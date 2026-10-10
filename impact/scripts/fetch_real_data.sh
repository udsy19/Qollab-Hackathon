#!/usr/bin/env bash
# READ-ONLY Alpaca historical-data download for QC-TRADE. NEVER places orders.
#
#   bash scripts/fetch_real_data.sh smoke|pilot|full [--feed sip|iex] [--adjustment raw|split|dividend|all] [--dry-run]
#
# SPY QQQ IWM DIA TLT GLD to the latest XNYS session Alpaca permits, from:
#   smoke: 28 calendar days before it (a few minutes; checks the whole path)
#   pilot: 2026-04-01 (what run_research.sh pilot backtests)
#   full:  2024-01-01
# Non-interactive when APCA_API_KEY_ID / APCA_API_SECRET_KEY are exported. The last line
# of a successful run starts with 'SUMMARY: OK'. Keys: exported APCA_API_KEY_ID / APCA_API_SECRET_KEY,
# or an echo-off prompt here. Keys live only in this process's environment; they are
# never written, logged or passed on a command line. --dry-run asks for no keys and
# makes no network call.
set -Eeuo pipefail
umask 077
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PYTHON_CMD="${PYTHON_CMD:-python3}"
if ! command -v "$PYTHON_CMD" >/dev/null; then
  echo "Python 3 not found: install Python 3.10+ and retry." >&2
  exit 2
fi
MODE="${1:-}"
case "$MODE" in
  smoke) START='-28d' ;;
  pilot) START='2026-04-01' ;;
  full)  START='2024-01-01' ;;
  *) echo "Usage: bash scripts/fetch_real_data.sh smoke|pilot|full [--feed sip|iex] [--adjustment raw|split|dividend|all] [--dry-run]" >&2
     exit 2 ;;
esac
shift

FEED='sip'; ADJ='raw'; DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --feed) FEED="${2:-}"; shift 2 ;;
    --adjustment) ADJ="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
[[ "$FEED" == sip || "$FEED" == iex ]] || { echo "--feed must be sip or iex" >&2; exit 2; }

"$PYTHON_CMD" -c 'import pyarrow, exchange_calendars, pandas, requests' 2>/dev/null || {
  echo "Missing dependencies. Run: $PYTHON_CMD -m pip install -r requirements.txt" >&2
  exit 2
}

CACHE="${QCT_CACHE_ROOT:-data}/alpaca_${MODE}_${FEED}_${ADJ}_1min"
ARGS=(--mode "$MODE" "--start=$START" --feed "$FEED" --adjustment "$ADJ" --cache-dir "$CACHE")

if [[ "$DRY" == 1 ]]; then
  exec "$PYTHON_CMD" -m qc_trade.fetch "${ARGS[@]}" --dry-run
fi

# Never paste API credentials into source, command-line arguments, chat, or files.
if [[ ( -z "${APCA_API_KEY_ID:-}" || -z "${APCA_API_SECRET_KEY:-}" ) && ! -t 0 ]]; then
  echo "No terminal to prompt on: export APCA_API_KEY_ID and APCA_API_SECRET_KEY (paper keys) first." >&2
  exit 2
fi
if [[ -z "${APCA_API_KEY_ID:-}" ]]; then
  read -r -s -p 'Rotated Alpaca PAPER API key ID: ' APCA_API_KEY_ID
  printf '\n'
fi
if [[ -z "${APCA_API_SECRET_KEY:-}" ]]; then
  read -r -s -p 'Rotated Alpaca PAPER API secret: ' APCA_API_SECRET_KEY
  printf '\n'
fi
export APCA_API_KEY_ID APCA_API_SECRET_KEY
trap 'unset APCA_API_KEY_ID APCA_API_SECRET_KEY' EXIT

printf 'Read-only download (%s, feed=%s, adjustment=%s). No orders will be sent.\n' "$MODE" "$FEED" "$ADJ"
set +e
"$PYTHON_CMD" -m qc_trade.fetch "${ARGS[@]}"
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  printf '\nDownload did NOT complete (exit %s). Nothing synthetic was substituted.\n' "$rc" >&2
  printf 'Rerun the same command to resume: verified partitions are reused.\n' >&2
fi
exit $rc
