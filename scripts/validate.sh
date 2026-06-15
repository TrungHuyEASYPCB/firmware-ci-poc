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
export HIL_RESULTS_DIR="${HIL_RESULTS_DIR:-hil-results}"
export UART_LOG_FILE="${UART_LOG_FILE:-$HIL_RESULTS_DIR/uart.log}"
export RESET_LOG_FILE="${RESET_LOG_FILE:-$HIL_RESULTS_DIR/reset.log}"

mkdir -p "$HIL_RESULTS_DIR"

echo "Serial: $SERIAL"
echo "UART port: $UART_PORT"
echo "Expected version: $EXPECTED_VERSION"
echo "Expected commit: $EXPECTED_COMMIT"
echo "Expected board: $EXPECTED_BOARD"
echo "HIL results dir: $HIL_RESULTS_DIR"

python3 scripts/write_hil_metadata.py

python3 -m pytest tests/hil -v -m hil \
  --junitxml="$HIL_RESULTS_DIR/pytest-junit.xml" \
  2>&1 | tee "$HIL_RESULTS_DIR/pytest.log"
