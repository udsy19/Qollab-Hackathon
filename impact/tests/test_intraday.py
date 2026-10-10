"""Leakage, calendar, portfolio feasibility and solver parity tests."""
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
import exchange_calendars as xcals
from qc_trade.data import normalize_minutes, aggregate_5min
from qc_trade.demo import synthetic_panel
from qc_trade.optimizer import (OptConfig,qubo_matrix,exact_qubo,qubo_energy,
                                  milp_qubo,anneal_qubo,qaoa_statevector,qaoa_xy_statevector,choose,full_exact,
                                  portfolio_objective)
from qc_trade.backtest import (ExecutionConfig,run_backtest,closed_bar_returns,
                               forecast,signal_positions,block_bootstrap_paired_excess)
from qc_trade.benchmark import benchmark_solvers


@pytest.fixture(scope='module')
def panel():
    return synthetic_panel(start='2026-09-01',end='2026-09-15',symbols=('SPY','QQQ','IWM','DIA'))


def _minutes_2days():
    cal=xcals.get_calendar('XNYS')
    rows=[]
    for date in ('2026-10-07','2026-10-08'):
        ses=pd.Timestamp(date)
        for ts in pd.date_range(cal.session_open(ses),cal.session_close(ses)-pd.Timedelta(minutes=1),freq='min'):
            for symbol,base in (('SPY',100),('QQQ',200),('IWM',140)):
                rows.append({'timestamp':ts.isoformat(),'symbol':symbol,'open':base,'high':base+.1,
                             'low':base-.1,'close':base+.01,'volume':1000})
    return pd.DataFrame(rows)


def test_normalization_drops_nothing_and_uses_timezone():
    bars=_minutes_2days().iloc[:30].copy()
    d=normalize_minutes(bars)
    assert len(d)==30
    assert str(d.timestamp.dt.tz)=='UTC'


def test_raw_dst_aware_new_york():
    naive=pd.DataFrame([{'timestamp':'2026-07-15 09:30:00','symbol':'SPY','open':100,
      'high':101,'low':99,'close':100,'volume':10}])
    d=normalize_minutes(naive)
    assert d.timestamp.iloc[0]==pd.Timestamp('2026-07-15T13:30:00Z')


def test_duplicate_minute_is_error():
    a=_minutes_2days().iloc[:2]
    with pytest.raises(ValueError,match='Duplicate'):
        normalize_minutes(pd.concat([a,a]))


def test_unphysical_price_bar_is_error():
    x=_minutes_2days().iloc[:1].copy()
    x.loc[x.index[0],'high']=0.01
    with pytest.raises(ValueError,match='High'):
        normalize_minutes(x)


def test_incomplete_session_explicitly_rejected():
    source=_minutes_2days()
    ts=pd.Timestamp('2026-10-07T14:31:00Z')
    bad=source[~((source.symbol=='QQQ') & (pd.to_datetime(source.timestamp,utc=True)==ts))]
    p=aggregate_5min(bad,['SPY','QQQ','IWM'],max_missing_session_fraction=.6)
    assert p.diagnostics['kept_sessions']==1
    assert '2026-10-07' in p.diagnostics['rejected_sessions']
    assert len(p.close)==78


def test_one_session_valid_complete():
    d=_minutes_2days()
    p=aggregate_5min(d,['SPY','QQQ','IWM'])
    assert len(p.open)==156
    assert (p.open['SPY']==100).all()
    assert (p.volume['SPY']==5000).all()


def test_early_close_2026_black_friday():
    cal=xcals.get_calendar('XNYS')
    ses=pd.Timestamp('2026-11-27')
    assert (cal.session_close(ses)-cal.session_open(ses)).total_seconds()/3600 ==3.5
    intervals=pd.date_range(cal.session_open(ses),cal.session_close(ses)-pd.Timedelta(minutes=5),freq='5min')
    assert len(intervals)==42


def test_no_overnight_return_in_forecast(panel):
    returns=closed_bar_returns(panel)
    ix=panel.days.ne(panel.days.shift())
    assert returns.loc[ix].isna().all().all()
    assert returns.loc[~ix].notna().all().all()


def test_alpha_not_using_future_return(panel):
    r=closed_bar_returns(panel).dropna().to_numpy()
    idx=200
    a=forecast(r[:idx],horizon_bars=6,shrinkage=.3)
    future=r.copy()
    future[idx:]*=999
    b=forecast(future[:idx],horizon_bars=6,shrinkage=.3)
    np.testing.assert_array_equal(a[0],b[0])
    np.testing.assert_array_equal(a[1],b[1])


def test_exact_milp_match_random_qubo():
    rng=np.random.default_rng(10)
    for n,k in [(4,2),(9,3),(15,3)]:
        q=rng.normal(size=(n,n))
        q=(q+q.T)/2
        w,detail=milp_qubo(q,k)
        w_ref=exact_qubo(q,k)
        assert detail['milp_certified']
        assert len(w)==k
        assert np.isclose(qubo_energy(q,w),qubo_energy(q,w_ref),atol=1e-7)


def test_qubo_turnover_equals_equal_weight_exact():
    cfg=OptConfig(k=2)
    mu=np.array([.003,.001,.002,.005])
    cov=np.eye(4)*.0001
    prev=np.array([.6,.4,0,0])
    q=qubo_matrix(mu,cov,prev,cfg)
    for i in range(4):
        for j in range(i+1,4):
            y=np.zeros(4);y[[i,j]]=1
            eq=y/2
            actual = portfolio_objective(eq,mu,cov,prev,cfg)
            # Q discards ONLY constant transaction cost c||prev||_1
            assert np.isclose(qubo_energy(q,np.array([i,j]))+cfg.expected_cost_bps*1e-4*abs(prev).sum(), actual)


def test_continuous_full_opt_not_worse_than_equal_weight():
    cfg=OptConfig(k=2,min_weight=.02,max_weight=.80)
    mu=np.array([.0004,.002,.0002,.001])
    cov=np.eye(4)*.0004
    prev=np.zeros(4)
    full=full_exact(mu,cov,prev,cfg)
    assert np.isclose(full.sum(),1,atol=1e-5)
    assert np.count_nonzero(full>1e-5)==2
    for i in range(4):
        for j in range(i+1,4):
            w=np.zeros(4);w[[i,j]]=.5
            assert portfolio_objective(full,mu,cov,prev,cfg) <= portfolio_objective(w,mu,cov,prev,cfg)+1e-9


def test_annealer_and_qaoa_produce_valid_k():
    rng=np.random.default_rng(3)
    q=rng.normal(size=(4,4));q=(q+q.T)/2
    assert len(anneal_qubo(q,2,100,2,seed=8))==2
    cfg=OptConfig(k=2,qaoa_maxiter=30,qaoa_shots=256)
    y,details=qaoa_statevector(q,2,cfg,seed=8)
    assert len(y)==2
    assert 0<=details['qaoa_feasible_mass']<=1
    assert details['qaoa_evaluations']>0
    xy,xy_detail=qaoa_xy_statevector(q,2,cfg,seed=8)
    assert len(xy)==2
    assert np.isclose(xy_detail['qaoa_feasible_mass'],1,atol=1e-8)


def test_signal_lag_and_day_end(panel):
    cfg=ExecutionConfig(test_start='2026-09-10',history_bars=40,execution_lag_bars=2)
    signals=signal_positions(panel,cfg)
    assert len(signals)>0
    for t in signals:
        assert panel.days.iloc[t]==panel.days.iloc[t+2]
        assert panel.days.iloc[t]==panel.days.iloc[t+3]
        assert panel.close.index[t+2]-panel.close.index[t]==pd.Timedelta(minutes=10)


def test_zero_alpha_spy_benchmark_and_cost_sensitivity(panel):
    o=OptConfig(k=2)
    base=ExecutionConfig(test_start='2026-09-09',history_bars=40,
                         max_participation=1.0,slippage_bps=0,spread_bps=0,
                         commission_bps=0,impact_bps_at_1pct=0)
    expensive=replace(base,slippage_bps=10)
    a=run_backtest(panel,base,o,['spy'])
    b=run_backtest(panel,expensive,o,['spy'])
    assert b.metrics.loc['spy','oos_total_return'] < a.metrics.loc['spy','oos_total_return']
    assert len(a.orders[a.orders['type']=='forced_flat'])>0
    assert a.diagnostics['no_overnight_exposure']


def test_benchmark_consistent_same_instance(panel):
    o=OptConfig(k=2,anneal_steps=50,anneal_restarts=2,qaoa_maxiter=20,qaoa_shots=256)
    cfg=ExecutionConfig(test_start='2026-09-10',history_bars=40)
    detail,summary=benchmark_solvers(panel,cfg,o,counts=[4],max_snapshots=1,restarts=2,include_qaoa=True)
    ex=detail[detail.method=='exact_qubo']
    milp=detail[detail.method=='milp_qubo']
    assert ex.feasible.all()
    assert milp.feasible.all()
    assert np.allclose(ex.qubo_gap_to_exact,0,atol=1e-9)
    assert np.allclose(milp.qubo_gap_to_exact,0,atol=1e-9)
    full=detail[detail.method=='full_exact']
    assert np.allclose(full.portfolio_gap_to_full_exact,0,atol=1e-9)
    assert 'qaoa' in set(detail.method)
    assert 'qaoa_xy' in set(detail.method)


def test_bootstrap_requires_enough_days():
    small=pd.DataFrame({'spy':np.zeros(10),'x':np.full(10,.002)})
    res=block_bootstrap_paired_excess(small)
    assert np.isnan(res.loc[res.method=='x','bootstrap_ci_low_bps']).all()
    long=pd.DataFrame({'spy':np.zeros(60),'x':np.full(60,.002)})
    res2=block_bootstrap_paired_excess(long,repeats=100)
    assert np.isclose(res2.loc[res2.method=='x','bootstrap_ci_low_bps'].iloc[0],20)


def test_alpaca_paginated_download_mocked(monkeypatch, tmp_path):
    """Network-free contract test for real-data API ingestion and provenance."""
    from qc_trade import data as source
    class Reply:
        ok = True
        status_code = 200
        text = ''
        def __init__(self, payload): self.payload=payload
        def json(self): return self.payload
    class Sess:
        headers = {}
        def __init__(self): self.count=0
        def get(self,url,params,timeout,allow_redirects):
            assert allow_redirects is False
            assert 'data.alpaca.markets/v2/stocks/bars' in url
            self.count+=1
            if self.count==1:
                return Reply({'bars':{'SPY':[{'t':'2026-09-01T13:30:00Z','o':100,'h':101,
                    'l':99,'c':100.1,'v':1000}]}, 'next_page_token':'NEXT'})
            assert params['page_token']=='NEXT'
            return Reply({'bars':{'QQQ':[{'t':'2026-09-01T13:30:00Z','o':210,'h':211,
                    'l':209,'c':210.1,'v':2000}]}, 'next_page_token':None})
    monkeypatch.setattr(source,'http_session',Sess)
    monkeypatch.setenv('APCA_API_KEY_ID','DUMMY_KEY')
    monkeypatch.setenv('APCA_API_SECRET_KEY','DUMMY_SECRET')
    path=tmp_path/'bars.csv'
    meta=source.download_alpaca(['SPY','QQQ'],'2026-09-01','2026-09-02',out=path)
    assert meta['pages']==2 and meta['rows']==2
    assert set(source.read_minute_csv(path).symbol)=={'SPY','QQQ'}
    assert path.with_suffix('.provenance.json').exists()
    assert 'DUMMY_SECRET' not in path.read_text()


def test_public_archive_loader_mocked(monkeypatch, tmp_path):
    """Network-free fixed fixture matches the documented official ZIP layout."""
    import io
    import zipfile
    from qc_trade import data as source
    data = io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        for symbol in ['SPY','KO','TSLA','TWTR']:
            content='timestamp,open,high,low,close,volume,session\n2022-07-01 09:30:00,100,101,99,100.5,12345,reg\n'
            z.writestr(f'minute_by_symbol/{symbol}_minute.csv',content)
    class Reply:
        content=data.getvalue()
        def raise_for_status(self): pass
    class Session:
        def get(self,url,timeout):
            assert url == source.FREE_SAMPLE_URL
            return Reply()
    monkeypatch.setattr(source,'http_session',Session)
    path=tmp_path/'vendor.csv'
    meta=source.download_public_sample(path)
    assert meta['rows']==4
    assert set(source.read_minute_csv(path).symbol)=={'SPY','KO','TSLA','TWTR'}
