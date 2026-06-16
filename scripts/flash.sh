#!/bin/bash
set -euo pipefail

echo "===================="
echo "FLASH DEVICE"
echo "===================="

SERIAL="${SERIAL:-1050325823}"
DEVICE_FAMILY="${DEVICE_FAMILY:-nrf52}"
HEX_FILE="${HEX_FILE:-build/merged.hex}"
HIL_RESULTS_DIR="${HIL_RESULTS_DIR:-hil-results}"
NRFUTIL="${NRFUTIL:-nrfutil}"

if ! command -v "$NRFUTIL" >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/nrfutil" ]; then
    NRFUTIL="$HOME/.local/bin/nrfutil"
  else
    echo "ERROR: nrfutil not found. Install nRF Util or set NRFUTIL=/path/to/nrfutil"
    exit 1
  fi
fi

mkdir -p "$HIL_RESULTS_DIR"

if [ ! -f "$HEX_FILE" ]; then
  echo "HEX file not found: $HEX_FILE"
  exit 1
fi

echo "nrfutil: $NRFUTIL"
echo "Serial: $SERIAL"
echo "Family: $DEVICE_FAMILY"
echo "HEX: $HEX_FILE"

{
  "$NRFUTIL" device program \
    --firmware "$HEX_FILE" \
    --serial-number "$SERIAL" \
    --family "$DEVICE_FAMILY" \
    --options chip_erase_mode=ERASE_RANGES_TOUCHED_BY_FIRMWARE,verify=VERIFY_READ,reset=RESET_SYSTEM

  echo "Flash completed"
} 2>&1 | tee "$HIL_RESULTS_DIR/flash.log"
