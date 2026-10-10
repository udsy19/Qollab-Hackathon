"""Offline integration tests: no network, real secret, POST, or actual trades."""
from __future__ import annotations

import json
import pytest
from qc_trade import alpaca_paper as m


class FakeResponse:
    ok = True
    def __init__(self, payload, status=200):
        self.status_code = status
        self.payload = payload
    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, statuses=None):
        self.headers = {}
        self.calls = []
        self.statuses = statuses or {}
    def get(self, url, params, timeout, allow_redirects):
        assert not allow_redirects
        assert timeout <= 30
        assert url.startswith((m.PAPER_HOST, m.DATA_HOST))
        self.calls.append((url, params))
        if url.endswith('/v2/account'):
            return FakeResponse({'status':'ACTIVE','equity':'XXXXX',
                 'account_number':'NEVER_PRINT','trading_blocked':False},
                self.statuses.get('account',200))
        if url.endswith('/v2/clock'):
            return FakeResponse({'is_open':False},self.statuses.get('clock',200))
        if url.endswith('/v2/stocks/bars'):
            assert params['symbols']=='SPY' and params['feed'] in {'sip','iex'}
            return FakeResponse({'bars':{'SPY':[{'t':'2025-09-10T13:30:00Z'}]}},
                self.statuses.get('data',200))
        raise AssertionError('Unexpected endpoint')


def test_read_only_paper_and_market_probe(monkeypatch):
    fake = FakeSession()
    monkeypatch.setattr(m,'_auth_session',lambda: fake)
    data = m.check_paper_and_data()
    assert data['market_data_authenticated']
    assert data['paper_account_authenticated']
    assert data['broker_orders_submitted']==0
    assert len(fake.calls)==3
    text = json.dumps(data)
    assert 'NEVER_PRINT' not in text
    assert 'XXXXX' not in text
    assert all('/v2/orders' not in x[0] for x in fake.calls)


def test_invalid_credentials_returns_sanitized_error(monkeypatch):
    fake = FakeSession({'account':401})
    monkeypatch.setattr(m,'_auth_session',lambda: fake)
    with pytest.raises(m.AlpacaConnectionError,match='401') as e:
        m.check_paper_and_data()
    assert 'NEVER_PRINT' not in str(e.value)
    assert len(fake.calls)==1


def test_forbidden_feed_returns_sanitized_error(monkeypatch):
    fake = FakeSession({'data':403})
    monkeypatch.setattr(m,'_auth_session',lambda: fake)
    with pytest.raises(m.AlpacaConnectionError,match='403'):
        m.check_paper_and_data(feed='sip')


def test_redirect_must_never_forward_credentials(monkeypatch):
    fake = FakeSession({'data':302})
    monkeypatch.setattr(m,'_auth_session',lambda: fake)
    with pytest.raises(m.AlpacaConnectionError,match='redirect'):
        m.check_paper_and_data()


def test_bad_feed_rejected_before_network(monkeypatch):
    monkeypatch.setattr(m,'_auth_session',lambda: (_ for _ in ()).throw(AssertionError('unexpected')))
    with pytest.raises(ValueError,match='Feed'):
        m.check_paper_and_data(feed='auto')


def test_no_environment_credentials(monkeypatch):
    monkeypatch.delenv('APCA_API_KEY_ID',raising=False)
    monkeypatch.delenv('APCA_API_SECRET_KEY',raising=False)
    with pytest.raises(m.AlpacaConnectionError,match='Missing'):
        m._auth_session()


def test_download_unauthorized_creates_no_complete_dataset(monkeypatch, tmp_path):
    from qc_trade import data as source
    class FakeDenied:
        status_code = 401
        def json(self):
            return {'message':'do not echo external errors'}
    class FakeSession:
        headers = {}
        def get(self,url,params,timeout,allow_redirects):
            assert 'data.alpaca.markets' in url
            assert not allow_redirects
            return FakeDenied()
    monkeypatch.setattr(source,'http_session',lambda: FakeSession())
    monkeypatch.setenv('APCA_API_KEY_ID','DUMMY_ID_NOT_REAL')
    monkeypatch.setenv('APCA_API_SECRET_KEY','DUMMY_SECRET_NOT_REAL')
    destination=tmp_path/'data.csv'
    with pytest.raises(RuntimeError,match='HTTP 401') as err:
        source.download_alpaca(['SPY','QQQ'],'2025-09-10','2025-09-11',out=destination)
    assert 'DUMMY_SECRET_NOT_REAL' not in str(err.value)
    assert not destination.exists()
    assert not destination.with_suffix('.provenance.json').exists()


def test_audit_refuses_synthetic_as_evidence(tmp_path):
    from qc_trade.audit import audit_results
    import shutil
    from pathlib import Path
    demo=Path(__file__).resolve().parents[1]/'outputs'/'demo'
    for filename in ['manifest.json','metrics_oos.csv','paired_bootstrap_vs_spy.csv',
                     'cost_stress_grid.csv','solver_benchmark_summary.csv']:
        shutil.copyfile(demo / filename, tmp_path / filename)
    r=audit_results(tmp_path)
    assert r['synthetic_data']
    assert not r['all_gates_passed']
    assert r['quantum_advantage_established'] is False
    assert r['paper_order_authorized'] is False
    assert (tmp_path/'RESEARCH_AUDIT.md').exists()
