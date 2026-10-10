"""Command-line entry point: python -m qc_trade.cli --help."""
from __future__ import annotations
import argparse
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from .data import download_alpaca,download_public_sample,read_minute_csv,aggregate_5min,NY,file_sha256
from .alpaca_paper import check_paper_and_data, AlpacaConnectionError
from .audit import audit_results
from .demo import synthetic_panel
from .optimizer import OptConfig
from .backtest import (ExecutionConfig,run_backtest,block_bootstrap_paired_excess,METHODS,
                       cost_stress_grid,run_cost_scenarios)
from .benchmark import benchmark_solvers


def csv_list(value: str) -> list[str]:
    return [s.strip().upper() for s in value.split(',') if s.strip()]


def save_plot(equity: pd.DataFrame, test_start: str, out: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    daily = equity.groupby(equity.index.tz_convert(NY).strftime('%Y-%m-%d')).last()
    idx = int(np.searchsorted(daily.index.to_numpy(),test_start))
    previous = daily.iloc[idx-1] if idx else pd.Series(equity.iloc[0],index=equity.columns)
    curves = daily.iloc[idx:].div(previous)
    fig, ax = plt.subplots(figsize=(10.5,5.5))
    for mode in curves:
        ax.plot(pd.to_datetime(curves.index),curves[mode],label=mode,linewidth=1.6)
    ax.set_title('OUT-OF-SAMPLE net-of-cost equity | research, NOT a future return forecast')
    ax.set_ylabel('Growth of $1 at OOS start')
    ax.grid(alpha=.2)
    ax.legend(ncol=3,fontsize=8)
    fig.tight_layout()
    fig.savefig(out/'oos_equity.png',dpi=150)
    plt.close(fig)


def experiment(panel, exec_cfg, opt_cfg, args, *, data_path=None, synthetic=False) -> None:
    methods = [s.strip().lower() for s in args.methods.split(',') if s.strip()]
    valid = set(METHODS)|{'qaoa','qaoa_xy','full_exact'}
    if not methods or set(methods)-valid:
        raise ValueError(f'Unknown methods: {set(methods)-valid}')
    results = run_backtest(panel,exec_cfg,opt_cfg,methods)
    target = Path(args.out)
    target.mkdir(parents=True,exist_ok=True)
    results.equity.to_csv(target/'bar_equity.csv',index_label='timestamp_utc')
    results.daily_oos_returns.to_csv(target/'daily_oos_returns.csv',index_label='NY_day')
    results.metrics.to_csv(target/'metrics_oos.csv',index_label='method')
    results.orders.to_csv(target/'orders.csv',index=False)
    results.forecasts.to_csv(target/'forecasts.csv',index=False)
    results.fills.to_csv(target/'fills.csv',index=False)
    results.decisions.to_csv(target/'decisions.csv',index=False)
    uncertainty = (block_bootstrap_paired_excess(results.daily_oos_returns,
                   block_days=exec_cfg.block_bootstrap_days,repeats=exec_cfg.bootstrap_reps,
                   seed=exec_cfg.seed) if 'spy' in methods else pd.DataFrame())
    uncertainty.to_csv(target/'paired_bootstrap_vs_spy.csv',index=False)
    if args.benchmark:
        bench, summary = benchmark_solvers(panel,exec_cfg,opt_cfg,
                  max_snapshots=args.snapshots,restarts=args.benchmark_repeats,
                  include_qaoa=not args.skip_qaoa,
                  counts=[int(i.strip()) for i in args.sizes.split(',') if i.strip()] if args.sizes else None)
        bench.to_csv(target/'solver_benchmark_trials.csv',index=False)
        summary.to_csv(target/'solver_benchmark_summary.csv',index=False)
    if args.stress:
        cost_stress_grid(panel,exec_cfg,opt_cfg,methods,[float(v) for v in args.stress_bps.split(',')]
                         ).to_csv(target/'cost_stress_grid.csv',index=False)
        run_cost_scenarios(panel,exec_cfg,opt_cfg,methods).to_csv(target/'cost_scenarios.csv',index=False)
    save_plot(results.equity,exec_cfg.test_start,target)
    manifest = {'version':'QC-TRADE intraday research v2',
      'created_utc':datetime.now(timezone.utc).isoformat(),
      'synthetic_data':synthetic,'real_profitability_claim':False,
      'data_source': 'synthetic' if synthetic else str(data_path),
      'data_file_sha256':file_sha256(Path(data_path)) if data_path else None,
      'execution':asdict(exec_cfg),'optimization':asdict(opt_cfg),
      'diagnostics':results.diagnostics,
      'warning':'No historical positive P&L or quantum advantage is asserted by this program.'}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str))
    print('\n'+('SYNTHETIC TEST ONLY — NO MARKET-RETURN EVIDENCE' if synthetic else 'REAL HISTORICAL MARKET DATA — OOS RESEARCH, NOT LIVE TRADING'))
    print(results.metrics[['oos_sessions','oos_total_return','oos_sharpe_rf0','oos_max_drawdown',
                            'oos_trades','oos_fees_usd']].to_string(float_format=lambda x:f'{x:.4f}'))
    if args.benchmark:
        print('\nCOMPUTATIONAL SAME-INSTANCE BENCHMARK (QAOA = ideal statevector simulation)')
        print(summary[['n','method','trials','median_seconds','median_qubo_gap','median_refined_gap']].to_string(index=False,float_format=lambda x:f'{x:.7g}'))
    print('Saved:', target.resolve())


def main(argv=None):
    p = argparse.ArgumentParser(prog='qc_trade',description='Research-only intraday portfolio optimization. Does not submit broker orders.')
    cmds = p.add_subparsers(dest='command',required=True)
    u = cmds.add_parser('audit',help='Evaluate OOS evidence gates from prior backtest outputs')
    u.add_argument('--out',required=True)
    u.add_argument('--method',default='milp_qubo')
    c = cmds.add_parser('check-alpaca',help='Read-only credential, paper account and historical data health check; NO orders')
    c.add_argument('--feed',choices=['sip','iex'],default='sip')
    a = cmds.add_parser('fetch-alpaca',help='Use YOUR Alpaca keys for real 1Min OHLCV')
    a.add_argument('--symbols',default='SPY,QQQ,IWM,DIA,TLT,GLD')
    a.add_argument('--start',required=True,help='UTC date YYYY-MM-DD, inclusive')
    a.add_argument('--end',required=True,help='UTC end boundary YYYY-MM-DD (Alpaca uses inclusive endpoint)')
    a.add_argument('--feed',choices=['sip','iex'],default='sip')
    a.add_argument('--out',default='data/minute_bars.csv')
    f = cmds.add_parser('fetch-public-sample',help='Download FREE third-party 2022H2 real market 1m sample')
    f.add_argument('--out',default='data/public_sample_2022.csv')
    for name in ('backtest','demo'):
        b = cmds.add_parser(name,help='Run walk-forward historical strategy evaluation' if name=='backtest' else 'Run synthetic mechanics sanity test')
        if name=='backtest':
            b.add_argument('--data',required=True,help='CSV with timestamp,symbol,open,high,low,close,volume')
            b.add_argument('--symbols',default='SPY,QQQ,IWM,DIA,TLT,GLD')
            b.add_argument('--min-minute-bars',type=int,default=5)
            b.add_argument('--max-missing-fraction',type=float,default=.15)
            b.add_argument('--end-date',default=None,help='Optional NY-date cutoff, e.g. 2022-10-26 for delisted TWTR')
            b.add_argument('--test-start',required=True,help='UNTUNED OOS holdout start YYYY-MM-DD')
        else:
            b.add_argument('--test-start',default='2026-09-14')
        b.add_argument('--out',default='outputs/research')
        b.add_argument('--methods',default='anneal,milp_qubo,exact_qubo,greedy,topk,minvar,spy,equal,cash')
        b.add_argument('--k',type=int,default=2)
        b.add_argument('--rebalance-minutes',type=int,default=30)
        b.add_argument('--signal-start-minutes',type=int,default=30)
        b.add_argument('--execution-lag-bars',type=int,default=2)
        b.add_argument('--history-bars',type=int,default=312)
        b.add_argument('--alpha-shrinkage',type=float,default=.3)
        b.add_argument('--capital',type=float,default=25_000)
        b.add_argument('--fractional-shares',action='store_true',help='Allow fractional share fills (default: whole shares)')
        b.add_argument('--spread-bps',type=float,default=1.0)
        b.add_argument('--slippage-bps',type=float,default=1.5)
        b.add_argument('--commission-bps',type=float,default=.2)
        b.add_argument('--impact-bps',type=float,default=1.0)
        b.add_argument('--max-participation',type=float,default=.02)
        b.add_argument('--expected-cost-bps',type=float,default=4.0)
        b.add_argument('--risk-aversion',type=float,default=6.0)
        b.add_argument('--min-weight',type=float,default=.03)
        b.add_argument('--max-weight',type=float,default=.8)
        b.add_argument('--anneal-steps',type=int,default=300)
        b.add_argument('--anneal-restarts',type=int,default=4)
        b.add_argument('--qaoa-maxiter',type=int,default=80)
        b.add_argument('--qaoa-shots',type=int,default=1024)
        b.add_argument('--stress',action='store_true',help='Re-run holdout with EXTRA per-side slippage (--stress-bps) and the four named cost scenarios')
        b.add_argument('--stress-bps',default='0,1.5,5,10')
        b.add_argument('--benchmark',action='store_true')
        b.add_argument('--snapshots',type=int,default=6)
        b.add_argument('--benchmark-repeats',type=int,default=3)
        b.add_argument('--skip-qaoa',action='store_true',help='Benchmark classical approaches only')
        b.add_argument('--sizes',default='',help='Benchmark sub-universe sizes 4,6,8; blank=auto')
    args = p.parse_args(argv)
    if args.command=='audit':
        summary = audit_results(Path(args.out),method=args.method)
        print(json.dumps({'oos_sessions':summary['oos_sessions'],
                          'synthetic_data':summary['synthetic_data'],
                          'all_gates_passed':summary['all_gates_passed'],
                          'evidence_gates':summary['gates'],
                          'report':str(Path(args.out)/'RESEARCH_AUDIT.md')},indent=2))
        return
    if args.command=='check-alpaca':
        try:
            print(json.dumps(check_paper_and_data(feed=args.feed),indent=2))
        except AlpacaConnectionError as exc:
            raise SystemExit('Alpaca read-only check failed: '+str(exc)) from None
        return
    if args.command=='fetch-alpaca':
        print(json.dumps(download_alpaca(csv_list(args.symbols),args.start,args.end,feed=args.feed,out=Path(args.out)),indent=2))
        return
    if args.command=='fetch-public-sample':
        print(json.dumps(download_public_sample(Path(args.out)),indent=2))
        return
    e = ExecutionConfig(test_start=args.test_start,rebalance_minutes=args.rebalance_minutes,
        signal_start_minutes=args.signal_start_minutes,execution_lag_bars=args.execution_lag_bars,
        history_bars=args.history_bars,alpha_shrinkage=args.alpha_shrinkage,
        starting_capital=args.capital,whole_shares=not args.fractional_shares,spread_bps=args.spread_bps,slippage_bps=args.slippage_bps,
        commission_bps=args.commission_bps,impact_bps_at_1pct=args.impact_bps,
        max_participation=args.max_participation)
    o = OptConfig(k=args.k,risk_aversion=args.risk_aversion,min_weight=args.min_weight,
        max_weight=args.max_weight,expected_cost_bps=args.expected_cost_bps,
        anneal_steps=args.anneal_steps,anneal_restarts=args.anneal_restarts,
        qaoa_maxiter=args.qaoa_maxiter,qaoa_shots=args.qaoa_shots)
    if args.command=='demo':
        panel = synthetic_panel()
        experiment(panel,e,o,args,synthetic=True)
    else:
        minutes = read_minute_csv(Path(args.data))
        if args.end_date:
            days = minutes.timestamp.dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
            minutes = minutes.loc[days<=args.end_date]
        panel = aggregate_5min(minutes,csv_list(args.symbols),
            min_one_minute_bars=args.min_minute_bars,
            max_missing_session_fraction=args.max_missing_fraction)
        experiment(panel,e,o,args,data_path=args.data)

if __name__=='__main__':
    main()
