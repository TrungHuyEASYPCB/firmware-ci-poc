#!/bin/bash
set -euo pipefail

echo "===================="
echo "PYTEST HIL VALIDATION"
echo "===================="

export SERIAL="${SERIAL:-1050325823}"
export UART_PORT="${UART_PORT:-/dev/ttyACM0}"

echo "Serial: $SERIAL"
echo "UART port: $UART_PORT"

python3 -m pytest tests/hil -v -m hil
