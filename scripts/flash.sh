#!/bin/bash
set -euo pipefail

echo "===================="
echo "FLASH DEVICE"
echo "===================="

SERIAL="${SERIAL:-1050325823}"
HEX_FILE="${HEX_FILE:-build/merged.hex}"
HIL_RESULTS_DIR="${HIL_RESULTS_DIR:-hil-results}"

mkdir -p "$HIL_RESULTS_DIR"

if [ ! -f "$HEX_FILE" ]; then
  echo "HEX file not found: $HEX_FILE"
  exit 1
fi

echo "Serial: $SERIAL"
echo "HEX: $HEX_FILE"

{
  nrfjprog \
    --program "$HEX_FILE" \
    --sectorerase \
    --verify \
    --reset \
    --snr "$SERIAL"

  echo "Flash completed"
} 2>&1 | tee "$HIL_RESULTS_DIR/flash.log"
