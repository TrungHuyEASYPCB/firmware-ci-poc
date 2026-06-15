#!/bin/bash
set -euo pipefail

echo "===================="
echo "PYTEST HIL VALIDATION"
echo "===================="

export SERIAL="${SERIAL:-1050325823}"
export UART_PORT="${UART_PORT:-/dev/ttyACM0}"
export EXPECTED_VERSION="${EXPECTED_VERSION:-$(cat RELEASE_VERSION 2>/dev/null || echo 0.0.0-dev)}"
export EXPECTED_COMMIT="${EXPECTED_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
export EXPECTED_BOARD="${EXPECTED_BOARD:-${BOARD:-nrf52dk/nrf52832}}"

echo "Serial: $SERIAL"
echo "UART port: $UART_PORT"
echo "Expected version: $EXPECTED_VERSION"
echo "Expected commit: $EXPECTED_COMMIT"
echo "Expected board: $EXPECTED_BOARD"

python3 -m pytest tests/hil -v -m hil
