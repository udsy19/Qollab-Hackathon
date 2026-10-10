"""Backtest integrity: causality, execution timing, holdings/cash accounting, costs.

Each test checks a PROPERTY that must hold for any correct engine, not the
engine's own bookkeeping: equity is re-derived here from the fill log and
market prices; causality is checked by perturbing the future and comparing
everything observable before the perturbation.
"""
from dataclasses import replace
import json
import numpy as np
import pandas as pd
import pytest
from qc_trade.data import BarPanel
from qc_trade.demo import synthetic_panel
from qc_trade.optimizer import OptConfig
from qc_trade import backtest as bt
from qc_trade.backtest import ExecutionConfig, run_backtest, METHODS
from qc_trade.audit import audit_results

ALL = list(METHODS)


@pytest.fixture(scope='module')
def panel():
    # The synthetic generator opens every bar at the previous close. Real bars gap,
    # and a fill at the wrong price is only visible when open != previous close.
    p = synthetic_panel(start='2026-09-01', end='2026-09-15', symbols=('SPY', 'QQQ', 'IWM', 'DIA'))
    gap = np.exp(np.random.default_rng(9).normal(0, 3e-4, p.open.shape))
    return BarPanel(p.open * gap, p.close, p.volume, p.days, p.diagnostics)


@pytest.fixture(scope='module')
def cfg():
    return ExecutionConfig(test_start='2026-09-09', history_bars=40, max_participation=1.)


@pytest.fixture(scope='module')
def opt():
    return OptConfig(k=2, anneal_steps=60, anneal_restarts=2)


@pytest.fixture(scope='module')
def result(panel, cfg, opt):
    return run_backtest(panel, cfg, opt, ALL)


def _perturb_from(panel: BarPanel, cut: pd.Timestamp, seed: int) -> BarPanel:
    """Independently rescale open, close and volume of every bar starting at/after cut."""
    rng = np.random.default_rng(seed)
    later = panel.close.index >= cut
    shape = (int(later.sum()), panel.close.shape[1])
    o, c, v = panel.open.copy(), panel.close.copy(), panel.volume.astype(float)
    o.loc[later] *= np.exp(rng.normal(0, .03, shape))
    c.loc[later] *= np.exp(rng.normal(0, .03, shape))
    v.loc[later] *= rng.uniform(.01, 5, shape)
    return BarPanel(o, c, v, panel.days, panel.diagnostics)


def _before(frame: pd.DataFrame, column: str, cut: pd.Timestamp) -> pd.DataFrame:
    return frame[pd.to_datetime(frame[column], utc=True) < cut].reset_index(drop=True)


# Owner's required test (spec section 6): "deliberately modify future prices and
# verify past trading decisions do not change".
@pytest.mark.parametrize('cut', ['2026-09-10T15:02:00Z',   # mid-session, between bar boundaries
                                 '2026-09-11T13:30:00Z',   # exactly a session open
                                 '2026-09-14T19:00:00Z'])  # late session, near forced flat
def test_future_price_perturbation_does_not_change_past(panel, cfg, opt, result, cut):
    cut = pd.Timestamp(cut)
    other = run_backtest(_perturb_from(panel, cut, seed=1), cfg, opt, ALL)
    # Decisions made on a signal bar that CLOSED by the cut must be identical,
    # even when their fill lands after the cut.
    a = _before(result.decisions, 'signal_time_utc', cut + pd.Timedelta(seconds=1))
    b = _before(other.decisions, 'signal_time_utc', cut + pd.Timedelta(seconds=1))
    assert len(a) > 0
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(_before(result.forecasts, 'time_utc', cut + pd.Timedelta(seconds=1)),
                                  _before(other.forecasts, 'time_utc', cut + pd.Timedelta(seconds=1)))
    pd.testing.assert_frame_equal(_before(result.fills, 'timestamp_utc', cut),
                                  _before(other.fills, 'timestamp_utc', cut))
    pd.testing.assert_frame_equal(_before(result.orders, 'timestamp', cut),
                                  _before(other.orders, 'timestamp', cut))
    pd.testing.assert_frame_equal(result.equity.loc[result.equity.index < cut],
                                  other.equity.loc[other.equity.index < cut])
    # And the perturbation is real: something after the cut did change.
    assert not result.equity.equals(other.equity)


def test_fill_at_a_bar_open_uses_nothing_from_that_bar_but_its_open(panel, cfg, opt, result):
    """At the instant a bar opens, only its open price is known: not its close, not its volume."""
    fill_bars = sorted(set(result.fills[~result.fills.forced].bar_index))
    t = fill_bars[len(fill_bars)//2]
    cut = panel.close.index[t]
    rng = np.random.default_rng(5)
    o, c, v = panel.open.copy(), panel.close.copy(), panel.volume.astype(float)
    at_or_after, after = panel.close.index >= cut, panel.close.index > cut
    o.loc[after] *= np.exp(rng.normal(0, .03, (int(after.sum()), o.shape[1])))
    c.loc[at_or_after] *= np.exp(rng.normal(0, .03, (int(at_or_after.sum()), c.shape[1])))
    v.loc[at_or_after] *= rng.uniform(.01, 5, (int(at_or_after.sum()), v.shape[1]))
    other = run_backtest(BarPanel(o, c, v, panel.days, panel.diagnostics), cfg, opt, ALL)
    upto = cut + pd.Timedelta(seconds=1)
    a, b = _before(result.fills, 'timestamp_utc', upto), _before(other.fills, 'timestamp_utc', upto)
    assert (pd.to_datetime(a.timestamp_utc, utc=True) == cut).any()
    pd.testing.assert_frame_equal(a, b)


def test_equity_is_cash_plus_holdings_rebuilt_from_fills(panel, result, cfg):
    """Re-derive NAV from the fill log and market closes, independently of the engine's NAV."""
    symbols = list(panel.close.columns)
    closes = panel.close.to_numpy(float)
    fills = result.fills
    assert len(fills) > 0
    for method in ALL:
        f = fills[fills.method == method]
        shares = np.zeros(len(symbols))
        cash = cfg.starting_capital
        by_bar = {k: g for k, g in f.groupby('bar_index')}
        nav = np.zeros(len(panel.close))
        for t in range(len(panel.close)):
            for _, row in by_bar.get(t, pd.DataFrame()).iterrows():
                j = symbols.index(row.symbol)
                signed = row.shares if row.side == 'buy' else -row.shares
                shares[j] += signed
                cash -= signed * row.fill_price + row.commission_usd
            assert cash >= -1e-6, f'{method}: negative cash (leverage) at bar {t}'
            assert (shares >= -1e-9).all(), f'{method}: short position at bar {t}'
            nav[t] = cash + shares @ closes[t]
        np.testing.assert_allclose(result.equity[method].to_numpy(), nav, rtol=1e-10, atol=1e-6,
                                   err_msg=f'{method}: engine equity is not cash + holdings')


def test_whole_shares_by_default(result):
    s = result.fills.shares.to_numpy(float)
    assert np.allclose(s, np.round(s)) and (s > 0).all()


def test_fills_are_at_a_later_bar_open_never_the_signal_bar(panel, result, cfg):
    """Recompute every fill price from the MARKET open and the cost model, not from the log."""
    opens = panel.open.to_numpy(float)
    symbols = list(panel.close.columns)
    fills = result.fills
    assert (~fills.forced).sum() > 0 and fills.forced.sum() > 0
    for _, row in fills.iterrows():
        j = symbols.index(row.symbol)
        if not row.forced:
            assert row.bar_index == row.signal_bar + cfg.execution_lag_bars > row.signal_bar
        concession = (cfg.spread_bps/2 + cfg.slippage_bps +
                      cfg.impact_bps_at_1pct*np.sqrt(row.participation/.01)) * 1e-4
        sign = 1 if row.side == 'buy' else -1
        expected = opens[row.bar_index, j] * (1 + sign*concession)
        assert np.isclose(row.fill_price, expected, rtol=1e-12, atol=0), (row.to_dict(), expected)
        assert np.isclose(row.commission_usd, cfg.commission_bps*1e-4*row.shares*row.fill_price, rtol=1e-12)


def test_flat_at_every_session_end_and_liquidation_is_costed(panel, result):
    days = panel.days.to_numpy()
    last = np.r_[days[1:] != days[:-1], True]
    symbols = list(panel.close.columns)
    for method in ALL:
        f = result.fills[result.fills.method == method]
        shares = np.zeros(len(symbols))
        for t in range(len(days)):
            for _, row in f[f.bar_index == t].iterrows():
                shares[symbols.index(row.symbol)] += row.shares if row.side == 'buy' else -row.shares
            if last[t]:
                assert np.allclose(shares, 0), f'{method} holds overnight after {days[t]}'
    forced = result.fills[result.fills.forced]
    assert len(forced) > 0 and (forced.side == 'sell').all()
    assert (forced.cost_usd > 0).all()
    assert forced.bar_index.isin(np.flatnonzero(last)).all()


def test_noncontiguous_panel_is_refused(panel, cfg, opt):
    keep = np.ones(len(panel.close), bool)
    keep[500] = False   # a missing mid-session 5m bar: a halt or a data hole
    holed = BarPanel(panel.open[keep], panel.close[keep], panel.volume[keep],
                     panel.days[keep], panel.diagnostics)
    with pytest.raises(ValueError, match='contiguous'):
        run_backtest(holed, cfg, opt, ['spy'])


def test_zero_extra_stress_equals_base_and_cost_is_additive(panel, cfg, opt):
    base = run_backtest(panel, cfg, opt, ['topk', 'spy'])
    grid = bt.cost_stress_grid(panel, cfg, opt, ['topk', 'spy'], [0.0, 5.0])
    zero = grid[grid.extra_slippage_bps_per_side == 0].set_index('method')
    for m in ['topk', 'spy']:
        assert zero.loc[m, 'oos_total_return'] == base.metrics.loc[m, 'oos_total_return']
        assert zero.loc[m, 'slippage_bps_total'] == cfg.slippage_bps
    five = grid[grid.extra_slippage_bps_per_side == 5].set_index('method')
    assert five.loc['spy', 'slippage_bps_total'] == cfg.slippage_bps + 5


def test_four_cost_scenarios_are_ordered(panel, cfg, opt):
    assert list(bt.COST_SCENARIOS) == ['optimistic', 'base', 'conservative', 'severe_stress']
    table = bt.run_cost_scenarios(panel, cfg, opt, ['spy', 'topk'])
    assert set(table.scenario) == set(bt.COST_SCENARIOS)
    assert (table.cost_assumption == 'MODELED from OHLCV, not observed quotes').all()
    for m in ['spy', 'topk']:
        r = table[table.method == m].set_index('scenario').loc[list(bt.COST_SCENARIOS)]
        # same decisions, harsher frictions => never more net return, never less cost
        assert (np.diff(r.oos_total_return.to_numpy(float)) <= 1e-12).all(), r
        assert (np.diff(r.oos_fees_usd.to_numpy(float)) >= -1e-9).all(), r
    # the "base" scenario is exactly the configuration it is given
    base = run_backtest(panel, replace(cfg, **bt.COST_SCENARIOS['base']), opt, ['spy'])
    got = table[(table.scenario == 'base') & (table.method == 'spy')].oos_total_return.iloc[0]
    assert got == base.metrics.loc['spy', 'oos_total_return']


def _audit_dir(tmp_path, scenario_returns: dict | None):
    (tmp_path / 'manifest.json').write_text(json.dumps({'synthetic_data': False, 'data_source': 'x.csv'}))
    pd.DataFrame([{'method': 'milp_qubo', 'oos_sessions': 120, 'oos_total_return': .05, 'oos_sharpe_rf0': 1.5,
                   'oos_max_drawdown': -.02, 'oos_fees_usd': 10.},
                  {'method': 'spy', 'oos_sessions': 120, 'oos_total_return': .01, 'oos_sharpe_rf0': .5,
                   'oos_max_drawdown': -.03, 'oos_fees_usd': 1.}]).to_csv(tmp_path / 'metrics_oos.csv', index=False)
    pd.DataFrame([{'method': 'milp_qubo', 'bootstrap_ci_low_bps': 1., 'bootstrap_ci_high_bps': 5.}]
                 ).to_csv(tmp_path / 'paired_bootstrap_vs_spy.csv', index=False)
    pd.DataFrame([{'extra_slippage_bps_per_side': 5., 'slippage_bps_per_side': 6.5, 'method': 'milp_qubo',
                   'oos_total_return': .01}]).to_csv(tmp_path / 'cost_stress_grid.csv', index=False)
    pd.DataFrame([{'n': 4, 'method': 'milp_qubo', 'median_seconds': .01}]
                 ).to_csv(tmp_path / 'solver_benchmark_summary.csv', index=False)
    if scenario_returns is not None:
        pd.DataFrame([{'scenario': s, 'method': 'milp_qubo', 'oos_total_return': r}
                      for s, r in scenario_returns.items()]).to_csv(tmp_path / 'cost_scenarios.csv', index=False)


def test_audit_never_validates_a_strategy_profitable_only_under_optimistic_costs(tmp_path):
    _audit_dir(tmp_path, {'optimistic': .05, 'base': .02, 'conservative': -.01, 'severe_stress': -.04})
    report = audit_results(tmp_path, method='milp_qubo')
    assert report['gates']['positive_oos_net_return_conservative_costs'] is False
    assert report['all_gates_passed'] is False


def test_audit_passes_cost_gate_only_when_conservative_is_positive(tmp_path):
    _audit_dir(tmp_path, {'optimistic': .05, 'base': .04, 'conservative': .01, 'severe_stress': -.04})
    report = audit_results(tmp_path, method='milp_qubo')
    assert report['gates']['positive_oos_net_return_conservative_costs'] is True
    assert report['severe_stress_oos_total_return'] == -.04


def test_audit_missing_cost_scenarios_is_a_failure_not_a_skip(tmp_path):
    _audit_dir(tmp_path, None)
    with pytest.raises(FileNotFoundError):
        audit_results(tmp_path, method='milp_qubo')


def test_synthetic_panel_supports_more_than_six_symbols():
    p = synthetic_panel(start='2026-09-01', end='2026-09-03', symbols=tuple('ABCDEFGH'))
    assert p.close.shape[1] == 8 and np.isfinite(p.close.to_numpy()).all()


def test_default_capital_is_spec_25k():
    assert ExecutionConfig().starting_capital == 25_000
