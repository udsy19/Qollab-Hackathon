"""Session-flat, next-executable-5min-open intraday research backtester.

All target forecasts are computed AFTER the signal bar closes. No forward-fill,
no crossing overnight returns in alpha/covariance. One full-bar fill delay by
DEFAULT (execution_lag_bars=2) after next boundary; no unrealizable close fills.

Accounting is an explicit share/cash ledger: every order becomes per-asset
fills (shares, fill price, commission); equity at every bar is
cash + sum(shares * close). Spread, slippage, impact and commission are
MODELED from OHLCV bars, never observed quotes or real fills.
"""
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import replace
from typing import Iterable
import numpy as np
import pandas as pd
import exchange_calendars as xcals
from .data import BarPanel
from .optimizer import OptConfig, choose, validate_config

METHODS = ('anneal','milp_qubo','exact_qubo','greedy','topk','minvar','spy','equal','cash')
COST_MODEL_LABEL = 'MODELED from OHLCV, not observed quotes'


@dataclass(frozen=True)
class ExecutionConfig:
    test_start: str = '2022-09-01'
    rebalance_minutes: int = 30
    signal_start_minutes: int = 30
    execution_lag_bars: int = 2
    history_bars: int = 156  # ~2 trading sessions; short for mechanics, not robust forecasts
    alpha_shrinkage: float = .30
    starting_capital: float = 25_000  # spec section 4: conservative initial capital
    whole_shares: bool = True         # integer share quantities; residual stays in cash
    spread_bps: float = 1.0           # FULL spread; charged half per executed side
    slippage_bps: float = 1.5
    commission_bps: float = .2        # commission + regulatory fees, per side, of fill notional
    impact_bps_at_1pct: float = 1.0
    max_participation: float = .02   # reject new target if any leg exceeds 2% previous 5m volume
    block_bootstrap_days: int = 5
    bootstrap_reps: int = 600
    seed: int = 77


# Four execution-cost scenarios (spec section 6). Every number is a MODELED
# assumption for liquid US ETFs, not a measurement: OHLCV bars carry no quotes.
# 'base' equals the ExecutionConfig defaults. Only frictions vary; timing,
# signals and optimizer settings are identical across scenarios.
COST_SCENARIOS: dict[str, dict[str, float]] = {
    'optimistic':    {'spread_bps': 0.5, 'slippage_bps': 0.5, 'commission_bps': 0.0, 'impact_bps_at_1pct': 0.5},
    'base':          {'spread_bps': 1.0, 'slippage_bps': 1.5, 'commission_bps': 0.2, 'impact_bps_at_1pct': 1.0},
    'conservative':  {'spread_bps': 2.0, 'slippage_bps': 3.0, 'commission_bps': 0.5, 'impact_bps_at_1pct': 2.0},
    'severe_stress': {'spread_bps': 5.0, 'slippage_bps': 10.0, 'commission_bps': 1.0, 'impact_bps_at_1pct': 5.0},
}


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


def validate_panel(panel: BarPanel) -> None:
    """Refuse a panel the timing logic cannot trust: missing input is a failure.

    Every session must hold exactly the XNYS 5-minute grid from the open to
    the last bucket before the close. A hole (halt, data gap) or a truncated
    session would silently shift the signal clock, the fill bar or the forced
    end-of-day liquidation.
    """
    idx = panel.close.index
    for frame in (panel.open, panel.volume):
        if not frame.index.equals(idx) or list(frame.columns) != list(panel.close.columns):
            raise ValueError('Panel open/close/volume must share one index and column order')
    if not panel.days.index.equals(idx):
        raise ValueError('Panel session labels must share the price index')
    if not idx.is_monotonic_increasing or idx.has_duplicates:
        raise ValueError('Panel bars must be strictly increasing in time')
    prices = np.r_[panel.open.to_numpy(float).ravel(), panel.close.to_numpy(float).ravel()]
    if not np.isfinite(prices).all() or (prices <= 0).any():
        raise ValueError('Panel prices must be finite and positive')
    vol = panel.volume.to_numpy(float)
    if not np.isfinite(vol).all() or (vol < 0).any():
        raise ValueError('Panel volume must be finite and non-negative')
    cal = xcals.get_calendar('XNYS')
    for day, stamps in pd.Series(idx, index=idx).groupby(panel.days.to_numpy()):
        session = pd.Timestamp(day)
        if not cal.is_session(session):
            raise ValueError(f'{day} is not an XNYS session')
        grid = pd.date_range(cal.session_open(session), cal.session_close(session)-pd.Timedelta(minutes=5),
                             freq='5min')
        if not pd.DatetimeIndex(stamps.to_numpy()).tz_localize(None).equals(grid.tz_localize(None)):
            raise ValueError(f'{day}: session bars are not contiguous on the XNYS 5-minute grid '
                             f'({len(stamps)} bars, expected {len(grid)}); refuse rather than trade through a gap')


def _execute(shares: np.ndarray, cash: float, target: np.ndarray, px: np.ndarray,
             prior_volume: np.ndarray, prior_close: np.ndarray, cfg: ExecutionConfig,
             *, forced: bool) -> dict:
    """Turn target weights into share fills at this bar's OPEN, sells before buys.

    Costs are price concessions (half spread + slippage + square-root impact)
    plus commission on fill notional. Buys are scaled down to the cash on hand,
    so cash never goes negative (no leverage). Participation is measured
    against the PREVIOUS completed bar's dollar volume.
    """
    nav_open = float(cash + shares @ px)
    wanted = target * nav_open / px
    if cfg.whole_shares:
        wanted = np.floor(wanted + 1e-9)
    delta = wanted - shares
    notional = np.abs(delta) * px
    out = {'nav_open': nav_open, 'turnover': float(notional.sum()/nav_open), 'peak': 0.0,
           'rejected': False, 'fills': [], 'shares': shares, 'cash': cash}
    if notional.sum() < 1e-9:
        return out
    participation = notional / np.maximum(prior_volume * prior_close, 1e-6)
    out['peak'] = float(participation.max())
    if not forced and out['peak'] > cfg.max_participation:
        out['rejected'] = True
        return out
    concession = (cfg.spread_bps/2 + cfg.slippage_bps +
                  cfg.impact_bps_at_1pct*np.sqrt(participation/.01)) * 1e-4
    commission = cfg.commission_bps * 1e-4
    shares = shares.copy()
    for j in np.flatnonzero(delta < 0):
        qty = -delta[j]
        price = px[j] * (1 - concession[j])
        fee = commission * qty * price
        cash += qty * price - fee
        shares[j] -= qty
        out['fills'].append((j, 'sell', qty, price, fee, participation[j]))
    buys = np.flatnonzero(delta > 0)
    prices = px[buys] * (1 + concession[buys])
    qty = delta[buys]
    need = float((qty * prices).sum() * (1 + commission))
    if need > cash:
        qty = qty * (cash / need) * (1 - 1e-12)
        if cfg.whole_shares:
            qty = np.floor(qty)
    for j, q, price in zip(buys, qty, prices):
        if q <= 0:
            continue
        fee = commission * q * price
        cash -= q * price + fee
        shares[j] += q
        out['fills'].append((j, 'buy', q, price, fee, participation[j]))
    if cash < -1e-6:
        raise RuntimeError('Ledger went negative: buys exceeded available cash')
    out['shares'], out['cash'] = shares, cash
    return out


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
    fills: pd.DataFrame       # one row per executed leg: shares, fill price, commission
    decisions: pd.DataFrame   # target weights chosen at each signal close, per method


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
    validate_panel(panel)
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
    cash = {s:float(e.starting_capital) for s in methods}
    shares = {s:np.zeros(n) for s in methods}
    queue: dict[str,dict[int,tuple[np.ndarray,int]]] = {s:{} for s in methods}
    histories = {s:np.zeros(len(times)) for s in methods}
    costs = {s:0.0 for s in methods}
    turn = {s:0.0 for s in methods}
    traded = {s:0 for s in methods}
    optimizer_secs = {s:[] for s in methods}
    trades, features, fills, decided = [], [], [], []
    first_test_pos = int(np.searchsorted(days, e.test_start))
    if first_test_pos >= len(times):
        raise ValueError('test_start must be no later than last available session')
    if len(np.unique(days[first_test_pos:])) < 2:
        raise ValueError('At least two out-of-sample complete sessions required')
    signal_id=0

    for t, current in enumerate(times):
        if first[t]:
            for method in methods:
                if np.abs(shares[method]).sum() > 1e-9:
                    raise AssertionError('Overnight holdings must be zero')
        for method in methods:
            active = queue[method].pop(t, None)
            if last[t]:
                # The exit is placed at the last 5m bucket START, not at its close.
                # It overrides any outstanding signal. Force liquidate even if
                # capacity threshold exceeded, but record the diagnostic.
                target, forced, order_signal_idx = np.zeros(n), True, -1
            elif active is not None:
                (target, order_signal_idx), forced = active, False
            else:
                target, forced, order_signal_idx = None, False, -1
            if target is not None:
                if first[t]:
                    raise AssertionError('Orders may not fill at first session bar')
                ex = _execute(shares[method], cash[method], target, A_open[t],
                              A_volume[t-1], A_close[t-1], e, forced=forced)
                signal_time = ((times[order_signal_idx]+pd.Timedelta(minutes=5)).isoformat()
                               if order_signal_idx >= 0 else '')
                cost_usd = 0.0
                for j, side, qty, price, fee, part in ex['fills']:
                    slip_usd = qty*abs(price-A_open[t, j])
                    cost_usd += slip_usd + fee
                    fills.append({'timestamp_utc':current.isoformat(), 'bar_index':t, 'NY_day':days[t],
                                  'method':method, 'symbol':symbols[j], 'side':side, 'shares':float(qty),
                                  'reference_price':float(A_open[t, j]), 'fill_price':float(price),
                                  'notional_usd':float(qty*price), 'commission_usd':float(fee),
                                  'cost_usd':float(slip_usd+fee), 'participation':float(part),
                                  'forced':forced, 'signal_bar':order_signal_idx, 'signal_time_utc':signal_time})
                shares[method], cash[method] = ex['shares'], ex['cash']
                if ex['fills'] and t >= first_test_pos:
                    costs[method] += cost_usd
                    turn[method] += ex['turnover']
                    traded[method] += 1
                if ex['fills'] or ex['rejected']:
                    held = shares[method]*A_open[t]/ex['nav_open']
                    trades.append({'timestamp':current.isoformat(), 'NY_day':days[t],
                      'method':method,'type':'forced_flat' if forced else 'rebalance',
                      'signal_time_utc':signal_time,
                      'rejected_capacity':ex['rejected'],'estimated_max_participation':ex['peak'],
                      'gross_L1_turnover':ex['turnover'] if ex['fills'] else 0.0,
                      'cost_fraction_nav':cost_usd/ex['nav_open'],
                      'cost_usd':cost_usd, 'cash_after':float(cash[method]),
                      'positions':';'.join(f'{s}:{v:.5f}' for s,v in zip(symbols,held) if v>1e-5)})
            histories[method][t] = cash[method] + shares[method] @ A_close[t]
            if histories[method][t] <= 0:
                raise RuntimeError('Nonpositive equity; inspect prices and the cost model')
        if t in decisions and cumulative[t] >= e.history_bars:
            pos = int(cumulative[t])
            R = cache[pos-e.history_bars:pos]
            mu, cov = forecast(R, horizon_bars=e.rebalance_minutes//5,
                               shrinkage=e.alpha_shrinkage)
            fill_pos = t+e.execution_lag_bars
            for method in methods:
                held = shares[method]*A_close[t]/histories[method][t]
                target, detail = choose(method,mu,cov,held,o,seed=o.seed+signal_id)
                optimizer_secs[method].append(detail['runtime_seconds']) if t>=first_test_pos else None
                queue[method][fill_pos] = target, t
                decided.append({'signal_time_utc':(current+pd.Timedelta(minutes=5)).isoformat(),
                                'signal_bar':t, 'fill_bar':fill_pos, 'method':method,
                                **{f'w_{s}':float(v) for s,v in zip(symbols,target)}})
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
            'accounting':'share/cash ledger; equity = cash + shares x close; '
                         + ('whole shares' if e.whole_shares else 'fractional shares'),
            'cost_model':COST_MODEL_LABEL,
            'data_quality':panel.diagnostics,
            'methods':methods,'signals_oos':sum(int(x['NY_day']>=e.test_start) for x in features)}
    return BacktestResult(pd.DataFrame(histories,index=times),daily_oos,metrics,
                          pd.DataFrame(trades),pd.DataFrame(features),diag,
                          pd.DataFrame(fills),pd.DataFrame(decided))


def cost_stress_grid(panel: BarPanel, e: ExecutionConfig, o: OptConfig, methods: Iterable[str],
                     extra_slippage_bps: Iterable[float]) -> pd.DataFrame:
    """Re-run the holdout with ADDITIONAL per-side slippage on top of the base config.

    Optimizer settings (including its own expected-cost prior) are not retuned.
    """
    rows = []
    for extra in extra_slippage_bps:
        if extra < 0:
            raise ValueError('Stress slippage cannot be negative')
        stressed = replace(e, slippage_bps=e.slippage_bps+extra)
        res = run_backtest(panel, stressed, o, methods)
        for method, row in res.metrics.iterrows():
            rows.append({'extra_slippage_bps_per_side':extra, 'slippage_bps_total':stressed.slippage_bps,
                         'method':method, 'oos_total_return':row['oos_total_return'],
                         'oos_sharpe_rf0':row['oos_sharpe_rf0'], 'oos_fees_usd':row['oos_fees_usd'],
                         'trades':row['oos_trades']})
    return pd.DataFrame(rows)


def run_cost_scenarios(panel: BarPanel, e: ExecutionConfig, o: OptConfig,
                       methods: Iterable[str]) -> pd.DataFrame:
    """The four named execution-cost scenarios on identical timing and settings."""
    rows = []
    for name, frictions in COST_SCENARIOS.items():
        res = run_backtest(panel, replace(e, **frictions), o, methods)
        for method, row in res.metrics.iterrows():
            rows.append({'scenario':name, 'method':method, **frictions,
                         'oos_total_return':row['oos_total_return'], 'oos_sharpe_rf0':row['oos_sharpe_rf0'],
                         'oos_max_drawdown':row['oos_max_drawdown'], 'oos_fees_usd':row['oos_fees_usd'],
                         'oos_trades':row['oos_trades'], 'cost_assumption':COST_MODEL_LABEL})
    return pd.DataFrame(rows)


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
