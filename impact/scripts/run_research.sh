#!/usr/bin/env bash
# READ-ONLY Alpaca authentication + historical study. NEVER places broker orders.
set -Eeuo pipefail
umask 077
cd "$(dirname "${BASH_SOURCE[0]}")/.."
PYTHON_CMD="${PYTHON_CMD:-python3}"
if ! command -v "$PYTHON_CMD" >/dev/null; then
  echo "Python 3 not found: install Python 3.10+ and retry." >&2
  exit 2
fi
MODE="${1:-pilot}"
if [[ "$MODE" != "pilot" && "$MODE" != "full" ]]; then
  echo "Usage: bash scripts/run_research.sh [pilot|full]" >&2
  exit 2
fi

# Never paste API credentials into source, command-line arguments, chat, or files.
# Read without terminal echo; retain only in the environment for this process.
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

"$PYTHON_CMD" -m qc_trade.cli check-alpaca --feed sip
TODAY_UTC="$(date -u +%Y-%m-%d)"
SYMBOLS='SPY,QQQ,IWM,DIA,TLT,GLD'
if [[ "$MODE" == "pilot" ]]; then
  # PILOT: limited recent data, only checks that the real workflow functions.
  # Never infer stable alpha from this small selected-sample window.
  START='2026-04-01'
  TEST_START='2026-08-03'
  REPEATS=2
  SNAPSHOTS=3
  OUTPUT="outputs/real_pilot_${TODAY_UTC}"
else
  # LOCKED OOS after precommitting settings on 2024/2025.
  START='2024-01-01'
  TEST_START='2026-01-02'
  REPEATS=5
  SNAPSHOTS=12
  OUTPUT="outputs/real_full_${TODAY_UTC}"
fi

mkdir -p data "$OUTPUT"
DATA="data/alpaca_${MODE}_${START}_${TODAY_UTC}_1min.csv"
if [[ ! -f "$DATA" || ! -f "${DATA%.csv}.provenance.json" ]]; then
  printf '\nFetching old historical SIP data only, no order placement.\n'
  "$PYTHON_CMD" -m qc_trade.cli fetch-alpaca \
    --symbols "$SYMBOLS" \
    --start "$START" --end "$TODAY_UTC" \
    --feed sip --out "$DATA"
else
  printf '\nUsing previously completed data: %s\n' "$DATA"
fi

"$PYTHON_CMD" -m qc_trade.cli backtest \
  --data "$DATA" --symbols "$SYMBOLS" \
  --test-start "$TEST_START" \
  --k 2 --history-bars 312 \
  --execution-lag-bars 2 --rebalance-minutes 30 \
  --methods milp_qubo,exact_qubo,greedy,topk,minvar,spy,equal,cash \
  --benchmark --sizes 4,6 \
  --benchmark-repeats "$REPEATS" --snapshots "$SNAPSHOTS" \
  --stress --stress-bps 0,1.5,5,10 \
  --out "$OUTPUT"

"$PYTHON_CMD" -m qc_trade.cli audit --out "$OUTPUT" --method milp_qubo
printf '\nReal-data reports generated under: %s\n' "$OUTPUT"
printf 'No paper orders submitted. Never place orders based solely on retrospective results.\n'
