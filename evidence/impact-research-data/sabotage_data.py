"""research-data sabotage: copy impact/, apply one mutation, run pytest, report."""
import shutil
import subprocess
import sys
from pathlib import Path

SRC, SCR, PY = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
CASES = [
    ('S1 silent feed fallthrough', 'fetch.py', "if entitlement[a.feed] != 'allowed':", 'if False:'),
    ('S2 no status backoff', 'alpaca_paper.py', 'if status in RETRY_STATUSES and attempt < max_attempts - 1:', 'if False:'),
    ('S3 no sha verify on load', 'dataset.py', "if file_sha256(p) != e['sha256']:", 'if False:'),
    ('S4 secret in manifest', 'fetch.py', "'credentials_recorded': False,",
     "'credentials_recorded': False, 'k': __import__('os').environ['APCA_API_SECRET_KEY'],"),
    ('S5 fixed 390-minute session', 'dataset.py', 'expected = int((c - o) / pd.Timedelta(minutes=1))', 'expected = 390'),
    ('S6 incomplete bucket not rejected', 'dataset.py', 'elif incomplete:', 'elif False:'),
    ('S7 empty month cached', 'fetch.py', 'if frame.empty and len(sessions):', 'if False:'),
    ('S8 no overnight-gap flag', 'dataset.py',
     'if prev_close is not None and abs(first_open / prev_close - 1) > GAP_FLAG:', 'if False:'),
    ('S9 repeated page token accepted', 'alpaca_paper.py', 'if token in seen:', 'if False:'),
    ('S10 order path allowed', 'alpaca_paper.py', "PAPER_HOST: {'/v2/account', '/v2/clock'},",
     "PAPER_HOST: {'/v2/account', '/v2/clock', '/v2/orders'},"),
    ('S11 resume ignores verification', 'fetch.py',
     "if old and old['request'] == params and ds.verify_entry(a.cache_dir, old):", "if old and old['request'] == params:"),
    ('S12 daily volume not compared', 'dataset.py',
     'if ratio is not None and not VOLUME_RATIO_FLAG[0] <= ratio <= VOLUME_RATIO_FLAG[1]:', 'if False:'),
    ('S13 latest session ignores 16-min delay', 'dataset.py',
     'if cal.session_close(ses) + SIP_RECENCY_DELAY <= now:', 'if cal.session_close(ses) <= now:'),
    ('S14 follow redirects', 'alpaca_paper.py', 'allow_redirects=False)', 'allow_redirects=True)'),
    ('S15 5m consistency check removed', 'fetch.py', 'if kept != expected_kept:', 'if False:'),
    ('S16 dry-run touches network', 'fetch.py', '    man = ds.read_manifest(a.cache_dir) if a.cache_dir.exists() else None',
     '    ap.http_session()\n    man = ds.read_manifest(a.cache_dir) if a.cache_dir.exists() else None'),
    ('S17 dry-run writes cache dir', 'fetch.py', '    man = ds.read_manifest(a.cache_dir) if a.cache_dir.exists() else None',
     '    a.cache_dir.mkdir(parents=True, exist_ok=True)\n    man = ds.read_manifest(a.cache_dir) if a.cache_dir.exists() else None'),
    ('S18 secret printed to stdout', 'fetch.py', "    print(f'[1/5] paper account authenticated",
     "    print(__import__('os').environ['APCA_API_KEY_ID'])\n    print(f'[1/5] paper account authenticated"),
]
for name, f, old, new in CASES:
    shutil.rmtree(SCR, ignore_errors=True)
    shutil.copytree(SRC, SCR, ignore=shutil.ignore_patterns('data', '__pycache__', '.pytest_cache'))
    p = SCR / 'qc_trade' / f
    s = p.read_text()
    assert s.count(old) == 1, (name, s.count(old))
    p.write_text(s.replace(old, new))
    r = subprocess.run([PY, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests'], cwd=SCR,
                       capture_output=True, text=True)
    last = r.stdout.strip().splitlines()[-1]
    print(f"{'RED   ' if r.returncode else 'GREEN!'} {name:42s} exit={r.returncode}  {last}", flush=True)
