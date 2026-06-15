#!/bin/bash
set -e

echo "===================="
echo "FLASH DEVICE"
echo "===================="

SERIAL="${SERIAL:-1050325823}"
HEX_FILE="${HEX_FILE:-build/merged.hex}"

if [ ! -f "$HEX_FILE" ]; then
  echo "HEX file not found: $HEX_FILE"
  exit 1
fi

echo "Serial: $SERIAL"
echo "HEX: $HEX_FILE"

nrfjprog \
  --program "$HEX_FILE" \
  --sectorerase \
  --verify \
  --reset \
  --snr "$SERIAL"

echo "Flash completed"
