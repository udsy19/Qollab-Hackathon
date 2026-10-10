"""Offline gates for the historical-data pipeline (spec section 3).

No network: every HTTP call goes to FakeAlpaca, which serves calendar-correct
1-minute bars for the XNYS sessions in the requested window and paginates with
the request's own `limit`, like the real /v2/stocks/bars endpoint.
"""
from __future__ import annotations

import json
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import pytest

from qc_trade import alpaca_paper as ap
from qc_trade import dataset as ds
from qc_trade import fetch

KEY = 'PKDUMMYKEYNEVERWRITE'
SECRET = 'DUMMYSECRETNEVERWRITE'
CAL = xcals.get_calendar('XNYS')
BASE = {'SPY': 500.0, 'QQQ': 400.0, 'IWM': 200.0, 'DIA': 390.0, 'TLT': 90.0, 'GLD': 230.0}


class Reply:
    def __init__(self, status, payload=None, headers=None):
        self.status_code = status
        self.payload = payload if payload is not None else {}
        self.headers = headers or {}

    def json(self):
        return self.payload


class FakeAlpaca:
    """Stateful fake of the two official hosts. GET only; records every call."""

    def __init__(self, *, forbidden_feeds=(), drop=(), zero_volume=(), throttle=0,
                 daily_volume_scale=1.0, gap=None, empty_feeds=(), empty_symbols=()):
        self.headers = {}
        self.calls = []
        self.forbidden_feeds = set(forbidden_feeds)
        self.empty_feeds = set(empty_feeds)
        self.empty_symbols = set(empty_symbols)
        self.drop = {(s, pd.Timestamp(t)) for s, t in drop}
        self.zero_volume = {(s, pd.Timestamp(t)) for s, t in zero_volume}
        self.throttle = throttle
        self.daily_volume_scale = daily_volume_scale
        self.gap = gap  # (symbol, session) whose prices jump x2 from that session on

    # requests.Session surface used by the code under test
    def get(self, url, params=None, timeout=None, allow_redirects=True):
        assert allow_redirects is False, 'credentials must never follow a redirect'
        assert url.startswith((ap.PAPER_HOST, ap.DATA_HOST)), url
        self.calls.append((url, dict(params or {})))
        if self.throttle:
            self.throttle -= 1
            return Reply(429, headers={})
        if url == ap.PAPER_HOST + '/v2/account':
            return Reply(200, {'status': 'ACTIVE', 'account_number': 'NEVER_PRINT_ACCT',
                               'equity': '123456.78', 'trading_blocked': False})
        if url == ap.PAPER_HOST + '/v2/clock':
            return Reply(200, {'is_open': False})
        if url == ap.DATA_HOST + '/v2/stocks/bars':
            return self._bars(params)
        raise AssertionError(f'unexpected endpoint {url}')

    def post(self, *a, **k):  # pragma: no cover - must never be reached
        raise AssertionError('POST attempted')

    def _price(self, sym, ts):
        p = BASE[sym]
        if self.gap and sym == self.gap[0] and ts >= CAL.session_open(pd.Timestamp(self.gap[1])):
            p *= 2
        return p

    def _bars(self, params):
        feed = params['feed']
        if feed in self.forbidden_feeds:
            return Reply(403, {'message': 'subscription does not permit querying recent SIP data'})
        start = pd.Timestamp(params['start'])
        end = pd.Timestamp(params['end'])
        rows = []
        if feed not in self.empty_feeds:
            sessions = CAL.sessions_in_range(start.tz_convert('America/New_York').date(),
                                             end.tz_convert('America/New_York').date())
            for sym in params['symbols'].split(','):
                if sym in self.empty_symbols:
                    continue
                for ses in sessions:
                    o, c = CAL.session_open(ses), CAL.session_close(ses)
                    if params['timeframe'] == '1Day':
                        vol = 1000 * int((c - o) / pd.Timedelta(minutes=1))
                        t = pd.Timestamp(ses.date()).tz_localize('America/New_York').tz_convert('UTC')
                        if start <= t < end:
                            p = self._price(sym, o)
                            rows.append((sym, {'t': t.isoformat().replace('+00:00', 'Z'), 'o': p,
                                               'h': p + 1, 'l': p - 1, 'c': p,
                                               'v': vol * self.daily_volume_scale, 'n': 10, 'vw': p}))
                        continue
                    # one pre-market bar, every regular minute, one post-market bar
                    times = [o - pd.Timedelta(minutes=60)] + list(
                        pd.date_range(o, c - pd.Timedelta(minutes=1), freq='min')) + [c + pd.Timedelta(minutes=5)]
                    for t in times:
                        if not (start <= t < end) or (sym, t) in self.drop:
                            continue
                        p = self._price(sym, t)
                        v = 0 if (sym, t) in self.zero_volume else 1000
                        rows.append((sym, {'t': t.isoformat().replace('+00:00', 'Z'), 'o': p,
                                           'h': p + .05, 'l': p - .05, 'c': p + .01,
                                           'v': v, 'n': 3, 'vw': p}))
        offset = int(params.get('page_token') or 0)
        limit = int(params['limit'])
        page = rows[offset:offset + limit]
        bars = {}
        for sym, bar in page:
            bars.setdefault(sym, []).append(bar)
        token = str(offset + limit) if offset + limit < len(rows) else None
        return Reply(200, {'bars': bars, 'next_page_token': token})

    def bar_calls(self, timeframe='1Min'):
        return [p for u, p in self.calls if u.endswith('/v2/stocks/bars') and p.get('timeframe') == timeframe]


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv('APCA_API_KEY_ID', KEY)
    monkeypatch.setenv('APCA_API_SECRET_KEY', SECRET)


def _run(tmp_path, fake, monkeypatch, *extra, symbols='SPY,QQQ', start='2026-11-23',
         now='2026-12-01T12:00:00Z'):
    monkeypatch.setattr(ap, 'http_session', lambda: fake)
    sleeps = []
    argv = ['--symbols', symbols, f'--start={start}', '--cache-dir', str(tmp_path / 'cache'),
            '--now', now, '--page-limit', '700', *extra]
    rc = fetch.main(argv, sleep=sleeps.append)
    return rc, sleeps


def _all_bytes(root: Path) -> bytes:
    return b''.join(p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file())


# --------------------------------------------------------------------------- HTTP layer

def test_backoff_retries_429_then_succeeds(creds, monkeypatch):
    fake = FakeAlpaca(throttle=3)
    sleeps = []
    out = ap._get_json(fake, host=ap.PAPER_HOST, path='/v2/clock', sleep=sleeps.append)
    assert out == {'is_open': False}
    assert sleeps == [1.0, 2.0, 4.0]


def test_backoff_honours_retry_after_and_caps():
    class S(FakeAlpaca):
        def get(self, url, params=None, timeout=None, allow_redirects=True):
            self.calls.append(url)
            return Reply(503, headers={'Retry-After': '7'}) if len(self.calls) < 3 else Reply(200, {'ok': 1})
    sleeps = []
    assert ap._get_json(S(), host=ap.DATA_HOST, path='/v2/stocks/bars', sleep=sleeps.append) == {'ok': 1}
    assert sleeps == [7.0, 7.0]


def test_backoff_gives_up_loudly():
    fake = FakeAlpaca(throttle=100)
    sleeps = []
    with pytest.raises(ap.AlpacaConnectionError, match='HTTP 429') as e:
        ap._get_json(fake, host=ap.PAPER_HOST, path='/v2/clock', sleep=sleeps.append, max_attempts=4)
    assert e.value.status == 429
    assert len(fake.calls) == 4 and len(sleeps) == 3


def test_live_trading_host_and_order_paths_refused():
    fake = FakeAlpaca()
    with pytest.raises(ValueError):
        ap._get_json(fake, host='https://api.alpaca.markets', path='/v2/account')
    with pytest.raises(ValueError):
        ap._get_json(fake, host=ap.PAPER_HOST, path='/v2/orders')
    assert fake.calls == []


def test_pipeline_source_has_no_order_or_write_verbs():
    root = Path(ap.__file__).parent
    for name in ('alpaca_paper.py', 'dataset.py', 'fetch.py', 'data.py'):
        src = (root / name).read_text()
        for bad in ('.post(', '.put(', '.patch(', '.delete(', '/v2/orders', '/v2/positions'):
            assert bad not in src, (name, bad)


# --------------------------------------------------------------------------- calendar

@pytest.mark.parametrize('now,expected', [
    ('2026-10-09T20:10:00Z', '2026-10-08'),   # Fri 16:10 ET: close + 16 min not yet passed
    ('2026-10-09T20:20:00Z', '2026-10-09'),   # Fri 16:20 ET
    ('2026-10-10T21:00:00Z', '2026-10-09'),   # Saturday
    ('2026-11-26T18:00:00Z', '2026-11-25'),   # Thanksgiving holiday
    ('2026-11-27T18:30:00Z', '2026-11-27'),   # half day closed 13:00 ET
])
def test_latest_permitted_session(now, expected):
    assert str(ds.latest_permitted_session(pd.Timestamp(now)).date()) == expected


def test_month_partitions_use_new_york_midnight_across_dst():
    parts = ds.month_partitions(pd.Timestamp('2024-02-15'), pd.Timestamp('2024-04-02T04:00:00Z'))
    assert [p.month for p in parts] == ['2024-02', '2024-03', '2024-04']
    assert parts[0].start == pd.Timestamp('2024-02-15T05:00:00Z')      # EST
    assert parts[1].start == pd.Timestamp('2024-03-01T05:00:00Z')
    assert parts[1].end == pd.Timestamp('2024-04-01T04:00:00Z')        # EDT
    assert parts[2].end == pd.Timestamp('2024-04-02T04:00:00Z')


# --------------------------------------------------------------------------- end to end

def test_full_pipeline_writes_verified_cache_and_manifest(tmp_path, creds, monkeypatch, capsys):
    fake = FakeAlpaca()
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    cache = tmp_path / 'cache'
    man = json.loads((cache / 'manifest.json').read_text())
    # provenance
    assert man['feed'] == 'sip' and man['adjustment'] == 'raw' and man['timeframe'] == '1Min'
    assert man['symbols'] == ['SPY', 'QQQ']
    assert man['latest_permitted_session'] == '2026-11-30'
    assert man['entitlement']['sip'] == 'allowed' and man['entitlement']['iex'] == 'allowed'
    assert man['paper_account']['paper_only'] is True
    assert man['credentials_recorded'] is False
    files = man['files']
    assert {f['symbol'] for f in files} == {'SPY', 'QQQ'}
    for f in files:
        p = cache / f['path']
        assert p.suffix == '.parquet' and ds.file_sha256(p) == f['sha256']
        assert f['rows'] > 0 and f['pages'] >= 1 and f['downloaded_utc']
        assert 'page_token' not in f['request'] and f['request']['feed'] == 'sip'
    # pagination really happened (limit 700 < one month of bars)
    assert max(f['pages'] for f in files) > 1
    # no secret anywhere on disk or on stdout
    blob = _all_bytes(cache)
    out = capsys.readouterr().out
    for s in (KEY, SECRET, 'NEVER_PRINT_ACCT', '123456.78'):
        assert s.encode() not in blob and s not in out
    # GET only, never an order path
    assert all('/orders' not in u for u, _ in fake.calls)
    # calendar: Thanksgiving absent, Black Friday half day = 210 minutes, DST-correct open
    val = json.loads((cache / 'validation.json').read_text())
    sessions = {r['session']: r for r in val['sessions'] if r['symbol'] == 'SPY'}
    assert '2026-11-26' not in sessions
    assert sessions['2026-11-27']['expected_minutes'] == 210
    assert sessions['2026-11-24']['expected_minutes'] == 390
    assert sessions['2026-11-24']['extended_hours_bars'] == 2
    assert val['rejected_sessions'] == {}
    # 5-minute bars reconstructed only from complete minutes
    five = pd.read_parquet(cache / man['bars_5min']['path'])
    assert man['bars_5min']['sha256'] == ds.file_sha256(cache / man['bars_5min']['path'])
    per_day = five[five.symbol == 'SPY'].groupby('session').size().to_dict()
    assert per_day['2026-11-27'] == 42 and per_day['2026-11-24'] == 78


def test_feed_not_entitled_fails_loudly_and_never_switches(tmp_path, creds, monkeypatch, capsys):
    fake = FakeAlpaca(forbidden_feeds={'sip'})
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 3
    err = capsys.readouterr().err
    assert "'sip' is forbidden" in err and 'Not switching' in err and '--feed iex' in err
    # the probe asked about both feeds; refused BEFORE any download request on either feed
    probes = fake.bar_calls()
    assert sorted(p['feed'] for p in probes) == ['iex', 'sip'] and all(p['limit'] == 5 for p in probes)
    assert not (tmp_path / 'cache' / 'manifest.json').exists()
    assert not list((tmp_path / 'cache').rglob('*.parquet'))


def test_empty_feed_is_failure_not_skip(tmp_path, creds, monkeypatch):
    rc, _ = _run(tmp_path, FakeAlpaca(empty_feeds={'sip'}), monkeypatch)
    assert rc != 0
    assert not list((tmp_path / 'cache').rglob('*.parquet'))


def test_empty_month_in_download_is_failure_not_skip(tmp_path, creds, monkeypatch, capsys):
    rc, _ = _run(tmp_path, FakeAlpaca(empty_symbols={'QQQ'}), monkeypatch)
    assert rc == 1
    assert 'QQQ 2026-11: Alpaca returned zero bars' in capsys.readouterr().err
    assert not (tmp_path / 'cache' / 'minute' / 'QQQ').exists()
    man = json.loads((tmp_path / 'cache' / 'manifest.json').read_text())
    assert man['status'] == 'incomplete'


def test_repeated_page_token_is_an_error_not_a_loop():
    class Loop(FakeAlpaca):
        def get(self, url, params=None, timeout=None, allow_redirects=True):
            self.calls.append(url)
            if len(self.calls) > 5:
                raise AssertionError('pagination did not stop on a repeated token')
            return Reply(200, {'bars': {'SPY': []}, 'next_page_token': 'SAME'})
    with pytest.raises(ap.AlpacaConnectionError, match='repeated a pagination token'):
        list(ap.iter_bar_pages(Loop(), {'symbols': 'SPY'}))


def test_5min_and_report_must_agree(tmp_path, creds, monkeypatch, capsys):
    from dataclasses import replace
    real = fetch.aggregate_5min

    def drifted(minutes, symbols, **kw):   # a reconstruction that silently drops a session
        p = real(minutes, symbols, **kw)
        keep = p.days != p.days.iloc[-1]
        return replace(p, open=p.open[keep.values], close=p.close[keep.values],
                       volume=p.volume[keep.values], days=p.days[keep])
    monkeypatch.setattr(fetch, 'aggregate_5min', drifted)
    rc, _ = _run(tmp_path, FakeAlpaca(), monkeypatch)
    assert rc == 1 and 'disagree' in capsys.readouterr().err
    assert not (tmp_path / 'cache' / 'bars_5min.parquet').exists()


def test_missing_minute_rejects_session_in_report_and_5min(tmp_path, creds, monkeypatch):
    fake = FakeAlpaca(drop={('QQQ', '2026-11-24T15:02:00Z')})
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    cache = tmp_path / 'cache'
    val = json.loads((cache / 'validation.json').read_text())
    assert list(val['rejected_sessions']) == ['2026-11-24']
    assert 'QQQ' in val['rejected_sessions']['2026-11-24']
    row = [r for r in val['sessions'] if r['symbol'] == 'QQQ' and r['session'] == '2026-11-24'][0]
    assert row['missing_minutes'] == 1 and row['incomplete_5m_buckets'] == 1
    man = json.loads((cache / 'manifest.json').read_text())
    five = pd.read_parquet(cache / man['bars_5min']['path'])
    assert '2026-11-24' not in set(five.session)
    assert man['validation']['rejected_session_count'] == 1


def test_volume_and_corporate_action_flags(tmp_path, creds, monkeypatch):
    fake = FakeAlpaca(zero_volume={('SPY', '2026-11-25T15:00:00Z')}, daily_volume_scale=3.0,
                      gap=('QQQ', '2026-11-25'))
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    val = json.loads((tmp_path / 'cache' / 'validation.json').read_text())
    row = [r for r in val['sessions'] if r['symbol'] == 'SPY' and r['session'] == '2026-11-25'][0]
    assert row['zero_volume_minutes'] == 1
    assert any(f['flag'] == 'daily_volume_mismatch' for f in val['flags'])
    gaps = [f for f in val['flags'] if f['flag'] == 'overnight_gap']
    assert [(g['symbol'], g['session']) for g in gaps] == [('QQQ', '2026-11-25')]


def test_resume_skips_verified_partitions_and_redownloads_tampered(tmp_path, creds, monkeypatch):
    rc, _ = _run(tmp_path, FakeAlpaca(), monkeypatch)
    assert rc == 0
    second = FakeAlpaca()
    rc, _ = _run(tmp_path, second, monkeypatch)
    assert rc == 0
    assert [p for p in second.bar_calls() if p['limit'] != 5] == []
    man = json.loads((tmp_path / 'cache' / 'manifest.json').read_text())
    victim = tmp_path / 'cache' / man['files'][0]['path']
    victim.write_bytes(victim.read_bytes()[:-10] + b'0123456789')
    with pytest.raises(ds.DatasetIntegrityError, match='sha256'):
        ds.load_dataset(tmp_path / 'cache')
    third = FakeAlpaca()
    rc, _ = _run(tmp_path, third, monkeypatch)
    assert rc == 0
    assert len([p for p in third.bar_calls() if p['limit'] != 5]) >= 1
    assert len(ds.load_dataset(tmp_path / 'cache')) > 0


def test_retry_inside_download_backs_off(tmp_path, creds, monkeypatch):
    rc, sleeps = _run(tmp_path, FakeAlpaca(throttle=2), monkeypatch)
    assert rc == 0 and sleeps[:2] == [1.0, 2.0]


def test_dry_run_needs_no_credentials_and_no_network(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv('APCA_API_KEY_ID', raising=False)
    monkeypatch.delenv('APCA_API_SECRET_KEY', raising=False)
    monkeypatch.setattr(ap, 'http_session', lambda: (_ for _ in ()).throw(AssertionError('network')))
    rc = fetch.main(['--dry-run', '--symbols', 'SPY,QQQ,IWM,DIA,TLT,GLD', '--start', '2024-01-01',
                     '--cache-dir', str(tmp_path / 'c'), '--now', '2026-10-10T21:00:00Z'])
    assert rc == 0
    out = capsys.readouterr().out
    assert 'DRY RUN' in out and 'GET https://data.alpaca.markets/v2/stocks/bars' in out
    assert 'GET https://paper-api.alpaca.markets/v2/account' in out
    assert '2026-10-09' in out
    assert 'minute-bar partitions to download: 204' in out   # 6 symbols x 34 months
    assert not (tmp_path / 'c').exists()


def test_dry_run_shell_entry_point(tmp_path):
    import os
    import subprocess
    import sys
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'fetch_real_data.sh'
    env = {k: v for k, v in os.environ.items() if not k.startswith('APCA_')}
    env['PYTHON_CMD'] = sys.executable
    env['QCT_CACHE_ROOT'] = str(tmp_path)
    r = subprocess.run(['bash', str(script), 'pilot', '--dry-run'], env=env, capture_output=True,
                       text=True, stdin=subprocess.DEVNULL, timeout=120)
    assert r.returncode == 0, r.stderr
    assert 'DRY RUN' in r.stdout and 'Rotated Alpaca' not in r.stdout + r.stderr
    bad = subprocess.run(['bash', str(script), 'live'], env=env, capture_output=True, text=True,
                         stdin=subprocess.DEVNULL, timeout=60)
    assert bad.returncode == 2
    # no keys and no terminal: a clear failure, never a hang on a prompt
    nokeys = subprocess.run(['bash', str(script), 'smoke'], env=env, capture_output=True, text=True,
                            stdin=subprocess.DEVNULL, timeout=60)
    assert nokeys.returncode == 2 and 'APCA_API_KEY_ID' in nokeys.stderr


def test_shell_is_non_interactive_with_exported_keys(tmp_path):
    """With keys exported, the script must not prompt and must pass them only via the environment."""
    import os
    import subprocess
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'fetch_real_data.sh'
    stub = tmp_path / 'py'
    stub.write_text('#!/usr/bin/env bash\n[[ "$1" == -c ]] && exit 0\n'
                    'echo "ARGS $*"; echo "KEYSET ${APCA_API_KEY_ID:+yes}${APCA_API_SECRET_KEY:+yes}"\n')
    stub.chmod(0o755)
    env = dict(os.environ, PYTHON_CMD=str(stub), QCT_CACHE_ROOT=str(tmp_path),
               APCA_API_KEY_ID=KEY, APCA_API_SECRET_KEY=SECRET)
    for mode, start in (('smoke', '--start=-28d'), ('pilot', '--start=2026-04-01'), ('full', '--start=2024-01-01')):
        r = subprocess.run(['bash', str(script), mode], env=env, capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=60)
        assert r.returncode == 0, r.stderr
        assert 'Rotated Alpaca' not in r.stdout + r.stderr
        assert f'--mode {mode} {start}' in r.stdout and 'KEYSET yesyes' in r.stdout
        assert KEY not in r.stdout and SECRET not in r.stdout          # never on a command line


def test_relative_start_and_one_line_summary(tmp_path, creds, monkeypatch, capsys):
    rc, _ = _run(tmp_path, FakeAlpaca(), monkeypatch, start='-5d')
    assert rc == 0
    man = json.loads((tmp_path / 'cache' / 'manifest.json').read_text())
    assert man['requested_start'] == '2026-11-25'           # 5 calendar days before 2026-11-30
    last = capsys.readouterr().out.strip().splitlines()[-1]
    assert last.startswith('SUMMARY: OK ') and 'sessions=3' in last and 'rejected=0' in last
    assert 'sha256=' in last and str(tmp_path / 'cache' / 'manifest.json') in last


def test_backtest_reads_cache_directory(tmp_path, creds, monkeypatch):
    from qc_trade import data
    rc, _ = _run(tmp_path, FakeAlpaca(), monkeypatch)
    assert rc == 0
    cache = tmp_path / 'cache'
    minutes = data.read_minute_csv(cache)
    assert set(minutes.symbol) == {'SPY', 'QQQ'}
    assert data.file_sha256(cache) == data.file_sha256(cache / 'manifest.json')
    panel = data.aggregate_5min(minutes, ['SPY', 'QQQ'])
    assert panel.diagnostics['kept_sessions'] == 5


# --------------------------------------------------------------------------- audit findings O5-O7

def _row(ts, sym='SPY', p=100.0):
    return {'timestamp': ts, 'symbol': sym, 'open': p, 'high': p + .1, 'low': p - .1, 'close': p, 'volume': 10}


@pytest.mark.parametrize('stamps', [
    ['2026-07-15T13:30:00Z', '2026-07-15 09:31:00'],          # aware first, naive later
    ['2026-07-15 09:30:00', '2026-07-15T13:31:00+00:00'],     # naive first, aware later
    ['2026-07-15T13:30:00Z', '2026-07-15T09:31:00'],          # same layout, offset dropped
    [pd.Timestamp('2026-07-15T13:30:00Z'), pd.Timestamp('2026-07-15 09:31:00')],   # objects
])
def test_o5_mixed_naive_and_aware_timestamps_refused(stamps):
    from qc_trade.data import normalize_minutes
    with pytest.raises(ValueError, match='mixes timezone-aware and naive'):
        normalize_minutes(pd.DataFrame([_row(t) for t in stamps]))


def test_o5_every_row_parsed_with_its_own_offset_across_dst():
    from qc_trade.data import normalize_minutes
    d = normalize_minutes(pd.DataFrame([_row('2024-03-08T09:30:00-05:00'), _row('2024-03-11T09:30:00-04:00')]))
    assert list(d.timestamp) == [pd.Timestamp('2024-03-08T14:30:00Z'), pd.Timestamp('2024-03-11T13:30:00Z')]
    naive = normalize_minutes(pd.DataFrame([_row('2024-03-08 09:30:00'), _row('2024-03-11 09:30:00')]))
    assert list(naive.timestamp) == list(d.timestamp)
    with pytest.raises(Exception):   # 02:30 on 2024-03-10 does not exist in New York
        normalize_minutes(pd.DataFrame([_row('2024-03-10 02:30:00')]))


def test_o6_rejections_name_every_symbol_and_policy_is_explicit(tmp_path, creds, monkeypatch):
    from qc_trade.data import aggregate_5min
    fake = FakeAlpaca(drop={('QQQ', '2026-11-24T15:02:00Z'), ('SPY', '2026-11-24T16:00:00Z')})
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    minutes = ds.load_dataset(tmp_path / 'cache')
    p = aggregate_5min(minutes, ['SPY', 'QQQ'], max_missing_session_fraction=1.0)
    rej = p.diagnostics['rejected_sessions']['2026-11-24']
    assert set(rej) == {'SPY', 'QQQ'}                      # every failing symbol, not the first one
    assert p.diagnostics['rejection_policy'].startswith('drop the session for all symbols')
    comp = p.diagnostics['per_symbol_completeness']
    assert comp['SPY']['incomplete_sessions'] == 1 and comp['SPY']['complete_sessions'] == 4
    man = json.loads((tmp_path / 'cache' / 'manifest.json').read_text())
    assert man['validation']['min_one_minute_bars'] == 5
    assert man['validation']['per_symbol_rejected'] == {'SPY': 1, 'QQQ': 1}


def test_o6_min_minute_bars_is_configurable_and_recorded(tmp_path, creds, monkeypatch):
    fake = FakeAlpaca(drop={('QQQ', '2026-11-24T15:02:00Z')})
    rc, _ = _run(tmp_path, fake, monkeypatch, '--min-minute-bars', '4')
    assert rc == 0
    val = json.loads((tmp_path / 'cache' / 'validation.json').read_text())
    assert val['rejected_sessions'] == {} and val['min_one_minute_bars'] == 4
    man = json.loads((tmp_path / 'cache' / 'manifest.json').read_text())
    assert man['validation']['min_one_minute_bars'] == 4
    assert man['bars_5min']['sessions'] == 5


def test_o6_selection_bias_of_rejected_sessions_is_measured(tmp_path, creds, monkeypatch):
    fake = FakeAlpaca(drop={('QQQ', '2026-11-24T15:02:00Z')})
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    bias = json.loads((tmp_path / 'cache' / 'validation.json').read_text())['selection_bias']
    assert bias['rejected_sessions'] == 1 and bias['kept_sessions'] == 4
    assert set(bias['by_symbol']) == {'SPY', 'QQQ'}
    for b in bias['by_symbol'].values():
        assert {'kept_mean_range', 'rejected_mean_range', 'mannwhitney_p'} <= set(b)


def test_five_minute_panel_passes_backtest_contiguity_check(tmp_path, creds, monkeypatch):
    from qc_trade.backtest import validate_panel
    from qc_trade.data import aggregate_5min
    fake = FakeAlpaca(drop={('QQQ', '2026-11-24T15:02:00Z')})
    rc, _ = _run(tmp_path, fake, monkeypatch)
    assert rc == 0
    p = aggregate_5min(ds.load_dataset(tmp_path / 'cache'), ['SPY', 'QQQ'], max_missing_session_fraction=1.0)
    validate_panel(p)                                   # half day 2026-11-27 included, 11-24 rejected
    assert sorted(set(p.days)) == ['2026-11-23', '2026-11-25', '2026-11-27', '2026-11-30']


@pytest.mark.parametrize('status,needle', [(503, 'server error'), (500, 'server error'), (429, 'rate limit')])
def test_o7_retry_exhaustion_is_not_reported_as_connectivity(status, needle):
    class S(FakeAlpaca):
        def get(self, url, params=None, timeout=None, allow_redirects=True):
            self.calls.append(url)
            return Reply(status)
    with pytest.raises(ap.AlpacaConnectionError) as e:
        ap._get_json(S(), host=ap.PAPER_HOST, path='/v2/clock', sleep=lambda s: None)
    msg = str(e.value)
    assert needle in msg and 'after 6 attempts' in msg and 'Could not connect' not in msg
    assert e.value.status == status


def test_o7_connection_auth_and_entitlement_are_distinct():
    import requests

    class Down(FakeAlpaca):
        def get(self, *a, **k):
            raise requests.ConnectionError('dns')
    with pytest.raises(ap.AlpacaConnectionError, match='Could not connect') as e:
        ap._get_json(Down(), host=ap.PAPER_HOST, path='/v2/clock')
    assert e.value.status is None
    for status, needle in ((401, 'credentials'), (403, 'entitlement')):
        class S(FakeAlpaca):
            def get(self, *a, **k):
                return Reply(status)
        with pytest.raises(ap.AlpacaConnectionError, match=needle):
            ap._get_json(S(), host=ap.PAPER_HOST, path='/v2/clock', sleep=lambda s: None)
    # status retries are explicit; the adapter must never turn them into a RetryError
    retry = ap.http_session().get_adapter('https://x').max_retries
    assert retry.status == 0 and not retry.status_forcelist
