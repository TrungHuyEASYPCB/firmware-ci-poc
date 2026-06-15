#!/bin/bash
set -euo pipefail

echo "===================="
echo "ZEPHYR BUILD"
echo "===================="

TOOLCHAIN_ROOT="${TOOLCHAIN_ROOT:-$HOME/ncs/toolchains/b77d8c1312}"
ZEPHYR_BASE="${ZEPHYR_BASE:-$HOME/ncs/v2.9.2/zephyr}"
BOARD="${BOARD:-nrf52dk/nrf52832}"

export ZEPHYR_BASE
export PATH="$TOOLCHAIN_ROOT/usr/local/bin:$PATH"
export LD_LIBRARY_PATH="$TOOLCHAIN_ROOT/usr/local/lib:${LD_LIBRARY_PATH:-}"

# Use Nordic/NCS toolchain package.
export CMAKE_PREFIX_PATH="$TOOLCHAIN_ROOT/cmake:${CMAKE_PREFIX_PATH:-}"

# Do not force plain Zephyr SDK mode.
unset ZEPHYR_TOOLCHAIN_VARIANT
unset ZEPHYR_SDK_INSTALL_DIR

echo "Board: $BOARD"
echo "ZEPHYR_BASE: $ZEPHYR_BASE"
echo "TOOLCHAIN_ROOT: $TOOLCHAIN_ROOT"
echo "CMAKE_PREFIX_PATH: $CMAKE_PREFIX_PATH"

west build -p always \
  -b "$BOARD" \
  .

echo ""
echo "Generated HEX files:"
find build -name "*.hex" -print
