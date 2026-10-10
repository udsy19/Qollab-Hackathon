"""Session-flat, next-executable-5min-open intraday research backtester.

All target forecasts are computed AFTER the signal bar closes. No forward-fill,
no crossing overnight returns in alpha/covariance. One full-bar fill delay by
DEFAULT (execution_lag_bars=2) after next boundary; no unrealizable close fills.
"""
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import replace
from typing import Iterable
import numpy as np
import pandas as pd
from .data import BarPanel
from .optimizer import OptConfig, choose, validate_config

METHODS = ('anneal','milp_qubo','exact_qubo','greedy','topk','minvar','spy','equal','cash')


@dataclass(frozen=True)
class ExecutionConfig:
    test_start: str = '2022-09-01'
    rebalance_minutes: int = 30
    signal_start_minutes: int = 30
    execution_lag_bars: int = 2
    history_bars: int = 156  # ~2 trading sessions; short for mechanics, not robust forecasts
    alpha_shrinkage: float = .30
    starting_capital: float = 100_000
    spread_bps: float = 1.0           # FULL spread; charged half per executed side
    slippage_bps: float = 1.5
    commission_bps: float = .2
    impact_bps_at_1pct: float = 1.0
    max_participation: float = .02   # reject new target if any leg exceeds 2% previous 5m volume
    block_bootstrap_days: int = 5
    bootstrap_reps: int = 600
    seed: int = 77


def validate_exec(cfg: ExecutionConfig) -> None:
    if cfg.rebalance_minutes <= 0 or cfg.rebalance_minutes % 5:
        raise ValueError('Rebalance interval must be positive multiple of 5min')
    if cfg.signal_start_minutes < 5 or cfg.execution_lag_bars < 1:
        raise ValueError('Signals require >=1 closed bar and lag >=1 bar')
    if cfg.history_bars < 30:
        raise ValueError('Need >=30 5min bars to estimate risk')
    if not 0 <= cfg.alpha_shrinkage <= 1:
        raise ValueError('Shrinkage must be 0..1')
    for field in ['starting_capital','spread_bps','slippage_bps',
                  'commission_bps','impact_bps_at_1pct','max_participation']:
        v = getattr(cfg, field)
        if (field == 'starting_capital' and v <= 0) or (field != 'starting_capital' and v < 0):
            raise ValueError(field+' is invalid')


def closed_bar_returns(panel: BarPanel) -> pd.DataFrame:
    """Close-to-close 5m returns WITHIN the same NY session, NaN at each open."""
    returns = panel.close.groupby(panel.days).pct_change(fill_method=None)
    assert returns.loc[panel.days.ne(panel.days.shift())].isna().all().all()
    return returns


def forecast(trailing_returns: np.ndarray, *, horizon_bars: int, shrinkage: float) -> tuple[np.ndarray,np.ndarray]:
    """A *weak*, precommitted intraday time-series momentum signal + covariance.

    Forecast available after close t; return TARGET over next rebalance horizon.
    Do not claim this predicts market prices or has positive net-of-cost alpha.
    """
    R = np.asarray(trailing_returns, float)
    if R.ndim != 2 or len(R) < 30 or not np.isfinite(R).all():
        raise ValueError('Need >=30 available training return observations (no intraday gaps)')
    fast = R[-6:].mean(axis=0)
    slow = R[-30:].mean(axis=0)
    mu_1bar = shrinkage * (0.60*fast+0.40*slow)
    C = np.atleast_2d(np.cov(R, rowvar=False))
    C = .75*C + .25*np.diag(np.diag(C))
    C += np.eye(R.shape[1])*1e-11
    # Estimate expected objective over typical 30-minute holding horizon.
    return mu_1bar * horizon_bars, C * horizon_bars


def signal_positions(panel: BarPanel, cfg: ExecutionConfig) -> list[int]:
    starts = panel.open.index
    days = panel.days.to_numpy()
    positions = []
    first_idx = np.maximum.accumulate(np.where(np.r_[True, days[1:] != days[:-1]], np.arange(len(starts)), 0))
    for t in range(len(starts)-1):
        if t+cfg.execution_lag_bars >= len(starts) or days[t] != days[t+cfg.execution_lag_bars]:
            continue
        # A 5m bar starting at 09:55 closes at 10:00; 10:00 decision.
        minute_of_session = int((starts[t] - starts[first_idx[t]]).total_seconds()/60)+5
        if minute_of_session >= cfg.signal_start_minutes and minute_of_session % cfg.rebalance_minutes == 0:
            # Do not schedule a new position to fill into the last bar; it's flat.
            if t+cfg.execution_lag_bars+1 < len(starts) and days[t+cfg.execution_lag_bars+1] == days[t]:
                positions.append(t)
    return positions


def _session_layout(panel: BarPanel):
    days = panel.days.to_numpy()
    first = np.r_[True, days[1:] != days[:-1]]
    last = np.r_[days[1:] != days[:-1], True]
    return first, last


def _fill_cost(old_weights: np.ndarray, target: np.ndarray, prior_volume: np.ndarray,
               prior_close: np.ndarray, nav: float, cfg: ExecutionConfig,
               *, forced: bool=False) -> tuple[float,float,float,bool]:
    delta = np.abs(target-old_weights)
    turnover = float(delta.sum())
    if turnover < 1e-12:
        return 0,0,0,False
    liquidity_usd = np.maximum(prior_volume * prior_close, 1e-6)
    p = (delta*nav)/liquidity_usd
    peak = float(p.max())
    if not forced and peak > cfg.max_participation:
        return 0,0,peak,True
    impact_bps = cfg.impact_bps_at_1pct*np.sqrt(np.maximum(p,0)/.01)
    per_asset_bps = cfg.spread_bps/2 + cfg.slippage_bps + cfg.commission_bps + impact_bps
    fee = float(np.dot(delta, per_asset_bps) * 1e-4)
    return fee, turnover, peak, False


def _drift(weights: np.ndarray, price_rel: np.ndarray) -> tuple[np.ndarray,float]:
    gain = float(1+weights@(price_rel-1))
    if not np.isfinite(gain) or gain <= 0:
        raise RuntimeError('Impossible nonpositive wealth from prices; inspect raw data')
    return weights*price_rel/gain, gain


def _metric_one(nav: pd.Series, test_start: str, num_trades: int, turn: float,
                cost_usd: float, secs: list[float]) -> dict:
    # Session end market values only; cash overnight is assumed non-interest-bearing.
    daily = nav.groupby(nav.index.tz_convert('America/New_York').strftime('%Y-%m-%d')).last()
    first = int(np.searchsorted(daily.index.to_numpy(), test_start))
    if first >= len(daily):
        raise ValueError('No trading sessions beginning at requested test_start')
    # Base on the last training session NAV: OOS morning starts FLAT.
    starting_nav = float(daily.iloc[first-1]) if first else 1.0
    test_daily = daily.iloc[first:]
    daily_return = test_daily / pd.concat([pd.Series([starting_nav]),test_daily.iloc[:-1]],ignore_index=True).to_numpy() - 1
    n = len(daily_return)
    stdev = float(daily_return.std(ddof=1)) if n>1 else np.nan
    drawdown = test_daily / np.maximum.accumulate(np.r_[starting_nav, test_daily.to_numpy()])[1:] - 1
    ret = float(test_daily.iloc[-1]/starting_nav - 1)
    return {
      'oos_sessions':n,
      'oos_total_return':ret,
      'oos_annualized_return':float((1+ret)**(252/n)-1) if n>0 and ret>-1 else np.nan,
      'oos_sharpe_rf0':float(daily_return.mean()/stdev*np.sqrt(252)) if stdev>0 else np.nan,
      'oos_max_drawdown':float(drawdown.min()),
      'oos_win_day_rate':float((daily_return>0).mean()),
      'oos_trades':num_trades,
      'oos_gross_turnover_l1':turn,
      'oos_fees_usd':cost_usd,
      'oos_mean_optimizer_sec':float(np.mean(secs)) if secs else np.nan,
      'oos_p95_optimizer_sec':float(np.percentile(secs,95)) if secs else np.nan,
    }


@dataclass
class BacktestResult:
    equity: pd.DataFrame
    daily_oos_returns: pd.DataFrame
    metrics: pd.DataFrame
    orders: pd.DataFrame
    forecasts: pd.DataFrame
    diagnostics: dict


def run_backtest(panel: BarPanel, e: ExecutionConfig, o: OptConfig,
                 methods: Iterable[str]=METHODS) -> BacktestResult:
    validate_exec(e)
    symbols = panel.close.columns.tolist()
    n = len(symbols)
    validate_config(o, n)
    methods = list(methods)
    if len(set(methods)) != len(methods):
        raise ValueError('Duplicate methods')
    if 'spy' in methods and symbols[0] != 'SPY':
        raise ValueError('SPY baseline requires SPY first in the supplied universe')
    if (set(methods) & {'qaoa','qaoa_xy'}) and n > 9:
        raise ValueError('QAOA demo supports <=9 assets')
    if 'full_exact' in methods and n > 8:
        raise ValueError('Full exact requires a small asset universe')
    times = panel.close.index
    days = panel.days.to_numpy()
    first, last = _session_layout(panel)
    barret = closed_bar_returns(panel)
    cache = barret.dropna().to_numpy(float)
    # Need enough information BEFORE every decision; map current bar index to
    # number of fully observed intra-session returns at its close.
    cumulative = (~barret.isna().any(axis=1)).cumsum().to_numpy()
    decisions = set(signal_positions(panel, e))
    A_open = panel.open.to_numpy(float)
    A_close = panel.close.to_numpy(float)
    A_volume = panel.volume.to_numpy(float)
    nav = {s:e.starting_capital for s in methods}
    weights = {s:np.zeros(n) for s in methods}
    queue: dict[str,dict[int,tuple[np.ndarray,int]]] = {s:{} for s in methods}
    histories = {s:np.zeros(len(times)) for s in methods}
    costs = {s:0.0 for s in methods}
    turn = {s:0.0 for s in methods}
    traded = {s:0 for s in methods}
    optimizer_secs = {s:[] for s in methods}
    trades, features = [], []
    first_test_pos = int(np.searchsorted(days, e.test_start))
    if first_test_pos >= len(times):
        raise ValueError('test_start must be no later than last available session')
    if len(np.unique(days[first_test_pos:])) < 2:
        raise ValueError('At least two out-of-sample complete sessions required')
    signal_id=0

    for t, current in enumerate(times):
        if first[t]:
            for method in methods:
                if np.abs(weights[method]).sum() > 1e-8:
                    raise AssertionError('Overnight holdings must be zero')
        for method in methods:
            w = weights[method]
            if not first[t]:
                gap_rel = A_open[t] / A_close[t-1]
                w, grow = _drift(w,gap_rel)
                nav[method] *= grow
            active = queue[method].pop(t, None)
            if last[t]:
                # The exit is placed at the last 5m bucket START, not at its close.
                # It overrides any outstanding signal. Force liquidate even if
                # capacity threshold exceeded, but record the diagnostic.
                target = np.zeros(n)
                forced = True
                order_signal_idx = -1
            elif active is not None:
                target, order_signal_idx = active
                forced = False
            else:
                target = None
                forced = False
                order_signal_idx = -1
            if target is not None:
                if first[t]:
                    raise AssertionError('Orders may not fill at first session bar')
                fee, trade_amt, peak_participation, rejected = _fill_cost(
                    w,target,A_volume[t-1],A_close[t-1],nav[method],e,forced=forced)
                if not rejected:
                    before = nav[method]
                    nav[method] *= (1-fee)
                    if nav[method] <= 0:
                        raise RuntimeError('Transaction-cost model spent entire NAV')
                    if t >= first_test_pos:
                        costs[method] += before*fee
                        turn[method] += trade_amt
                        if trade_amt > 1e-12: traded[method] += 1
                    w = target.copy()
                if trade_amt>1e-12 or rejected:
                    trades.append({'timestamp':current.isoformat(), 'NY_day':days[t],
                      'method':method,'type':'forced_flat' if forced else 'rebalance',
                      'signal_time_utc':(times[order_signal_idx]+pd.Timedelta(minutes=5)).isoformat() if order_signal_idx>=0 else '',
                      'rejected_capacity':rejected,'estimated_max_participation':peak_participation,
                      'gross_L1_turnover':trade_amt,'cost_fraction_nav':fee,
                      'cost_usd':float(before*fee) if not rejected else 0.0,
                      'positions':';'.join(f'{s}:{v:.5f}' for s,v in zip(symbols,w) if v>1e-5)})
            w, grow = _drift(w,A_close[t]/A_open[t])
            nav[method] *= grow
            weights[method] = w
            histories[method][t] = nav[method]
        if t in decisions and cumulative[t] >= e.history_bars:
            pos = int(cumulative[t])
            R = cache[pos-e.history_bars:pos]
            mu, cov = forecast(R, horizon_bars=e.rebalance_minutes//5,
                               shrinkage=e.alpha_shrinkage)
            fill_pos = t+e.execution_lag_bars
            for method in methods:
                target, detail = choose(method,mu,cov,weights[method],o,seed=o.seed+signal_id)
                optimizer_secs[method].append(detail['runtime_seconds']) if t>=first_test_pos else None
                queue[method][fill_pos] = target, t
            if t >= first_test_pos:
                features.append({'time_utc':(current+pd.Timedelta(minutes=5)).isoformat(), 'NY_day':days[t],
                                 'fill_time_utc':times[fill_pos].isoformat(),
                                 'observed_return_samples':len(R),'signal_id':signal_id,
                                 'momentum_mu':';'.join(f'{s}:{v:.8f}' for s,v in zip(symbols,mu)),
                                 'input_cov_trace':float(np.trace(cov))})
            signal_id += 1
    daily = pd.DataFrame(histories,index=times).groupby(days).last()
    first_day = int(np.searchsorted(daily.index.to_numpy(),e.test_start))
    anchor = daily.iloc[first_day-1] if first_day else pd.Series(e.starting_capital, index=methods)
    daily_test = daily.iloc[first_day:]
    previous = pd.concat([pd.DataFrame([anchor.to_numpy()],columns=methods),daily_test.iloc[:-1]],ignore_index=True)
    daily_oos = pd.DataFrame(daily_test.to_numpy()/previous.to_numpy()-1,index=daily_test.index,columns=methods)
    metrics = pd.DataFrame({s:_metric_one(pd.Series(histories[s],index=times),e.test_start,
                                          traded[s],turn[s],costs[s],optimizer_secs[s]) for s in methods}).T
    diag = {'symbols':symbols,'test_start':e.test_start,'oos_first_day':daily_test.index[0],
            'oos_last_day':daily_test.index[-1],'no_overnight_exposure':True,
            'daily_signal_lookback_excludes_overnight_gaps':True,
            'fill':'next + %d 5min bar open from signal close' % (e.execution_lag_bars-1),
            'data_quality':panel.diagnostics,
            'methods':methods,'signals_oos':sum(int(x['NY_day']>=e.test_start) for x in features)}
    return BacktestResult(pd.DataFrame(histories,index=times),daily_oos,metrics,
                          pd.DataFrame(trades),pd.DataFrame(features),diag)


def block_bootstrap_paired_excess(oos: pd.DataFrame, *, baseline: str='spy',
                                 block_days: int=5, repeats: int=1000, seed: int=11) -> pd.DataFrame:
    """Exploratory paired 5-day circular block bootstrap of mean daily EXCESS bps.

    No claim of IID daily returns, statistical significance or trading alpha;
    bootstrap intervals are descriptive and require large OOS windows.
    """
    rng = np.random.default_rng(seed)
    if baseline not in oos:
        raise ValueError('Baseline missing')
    n = len(oos)
    rows = []
    for method in oos:
        v = (oos[method]-oos[baseline]).to_numpy(float)*10_000
        if n < max(30,block_days*6):
            low = high = p_two = np.nan
        else:
            sims = np.zeros(repeats)
            blocks = int(np.ceil(n/block_days))
            for j in range(repeats):
                starts = rng.integers(0,n,size=blocks)
                positions = np.concatenate([(s+np.arange(block_days))%n for s in starts])[:n]
                sims[j] = v[positions].mean()
            low,high = np.quantile(sims,[.025,.975])
            # Centered bootstrap approximates probability of null-compatible
            # excess mean; report as exploratory only, not post-selection p-val.
            p_two = float(np.mean(np.abs(sims-v.mean())>=abs(v.mean())))
        rows.append({'method':method,'mean_excess_daily_bps':v.mean(),
                     'bootstrap_ci_low_bps':low,'bootstrap_ci_high_bps':high,
                     'exploratory_two_sided_p':p_two, 'oos_days':n})
    return pd.DataFrame(rows)
