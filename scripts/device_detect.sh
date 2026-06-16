#!/bin/bash
set -euo pipefail

SERIAL="${SERIAL:-1050325823}"
NRFUTIL="${NRFUTIL:-nrfutil}"

if ! command -v "$NRFUTIL" >/dev/null 2>&1; then
  if [ -x "$HOME/.local/bin/nrfutil" ]; then
    NRFUTIL="$HOME/.local/bin/nrfutil"
  else
    echo "ERROR: nrfutil not found"
    exit 1
  fi
fi

"$NRFUTIL" device list | tee /tmp/nrfutil-device-list.txt

if grep -q "$SERIAL" /tmp/nrfutil-device-list.txt; then
  echo "Device detected: $SERIAL"
else
  echo "Device not found: $SERIAL"
  exit 1
fi
