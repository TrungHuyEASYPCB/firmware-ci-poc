#!/bin/bash
set -e

echo "===================="
echo "UART VALIDATION"
echo "===================="

SERIAL="${SERIAL:-1050325823}"
UART_PORT="${UART_PORT:-/dev/ttyACM0}"
LOG_FILE="$(mktemp)"

echo "Serial: $SERIAL"
echo "UART port: $UART_PORT"
echo "Log file: $LOG_FILE"

if [ ! -e "$UART_PORT" ]; then
  echo "UART port not found: $UART_PORT"
  exit 1
fi

stty -F "$UART_PORT" 115200 cs8 -cstopb -parenb -ixon -ixoff -crtscts raw -echo

timeout 15 cat "$UART_PORT" > "$LOG_FILE" &
CAT_PID=$!

sleep 1

nrfjprog --reset --snr "$SERIAL" || true

wait "$CAT_PID" || true

echo ""
echo "Captured UART log:"
cat "$LOG_FILE"

echo ""
if grep -q "Heartbeat" "$LOG_FILE" || grep -q "BOOT OK" "$LOG_FILE"; then
  echo "UART validation PASS"
else
  echo "UART validation FAIL"
  exit 1
fi
