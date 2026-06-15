#!/bin/bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <command> [args...]"
  exit 2
fi

LOCK_TIMEOUT="${LOCK_TIMEOUT:-600}"
DEVICE_ROLE="${DEVICE_ROLE:-preview}"

if [ -z "${DEVICE_ID:-}" ]; then
  ENV_FILE="$(mktemp)"
  python3 scripts/select_device.py --role "$DEVICE_ROLE" --env-file "$ENV_FILE"
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  rm -f "$ENV_FILE"
fi

LOCK_DIR="${DEVICE_LOCK_DIR:-/tmp/firmware-ci-device-locks}"
mkdir -p "$LOCK_DIR"

LOCK_FILE="$LOCK_DIR/${DEVICE_ID}.lock"

echo "===================="
echo "DEVICE LOCK"
echo "===================="
echo "Device id: $DEVICE_ID"
echo "Role: $DEVICE_ROLE"
echo "Board: $BOARD"
echo "Serial: $SERIAL"
echo "UART: $UART_PORT"
echo "Lock file: $LOCK_FILE"
echo "Timeout: ${LOCK_TIMEOUT}s"

exec 200>"$LOCK_FILE"

if ! flock -w "$LOCK_TIMEOUT" 200; then
  echo "Failed to acquire device lock: $LOCK_FILE"
  exit 1
fi

echo "Device lock acquired"

export DEVICE_ID
export DEVICE_ROLE
export BOARD
export SERIAL
export UART_PORT

"$@"
STATUS=$?

echo "Device lock released"

exit "$STATUS"
