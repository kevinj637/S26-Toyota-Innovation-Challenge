#!/usr/bin/env bash
# One-command flash of the A2 demo firmware to a connected Arduino Uno R4.
# It streams current (for the web dashboard) AND runs the decision tree on-chip,
# lighting the onboard LED on a stall — so one flash gives both A1 and A2.
set -e
cd "$(dirname "$0")/.."

echo "[1/5] export trained tree -> model.h"
.venv/bin/python -m src.export_c --model model/tree.joblib --out model/model.h
cp model/model.h firmware_a2/stall_onboard/model.h

echo "[2/5] free the serial port (stop dashboard if running)"
pkill -f "web.app" 2>/dev/null || true
sleep 1

PORT=$(arduino-cli board list | awk '/usbmodem/{print $1; exit}')
[ -z "$PORT" ] && { echo "!! No Uno R4 found on a usbmodem port. Plug it in and retry."; exit 1; }
echo "[3/5] board on $PORT"

echo "[4/5] compile"
arduino-cli compile --fqbn arduino:renesas_uno:minima firmware_a2/stall_onboard

echo "[5/5] upload"
arduino-cli upload -p "$PORT" --fqbn arduino:renesas_uno:minima firmware_a2/stall_onboard

echo
echo "DONE. The onboard LED now lights on a stall (on-chip inference)."
echo "Open the dashboard too:  .venv/bin/python -m web.app --source serial --port $PORT"
