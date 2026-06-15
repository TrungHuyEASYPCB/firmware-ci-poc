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

export FW_VERSION="${FW_VERSION:-$(cat RELEASE_VERSION 2>/dev/null || echo 0.0.0-dev)}"
export FW_GIT_COMMIT="${FW_GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
export FW_GIT_REF="${FW_GIT_REF:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)}"
export FW_BOARD="${FW_BOARD:-$BOARD}"

echo "Board: $BOARD"
echo "Firmware version: $FW_VERSION"
echo "Firmware git commit: $FW_GIT_COMMIT"
echo "Firmware git ref: $FW_GIT_REF"
echo "ZEPHYR_BASE: $ZEPHYR_BASE"
echo "TOOLCHAIN_ROOT: $TOOLCHAIN_ROOT"
echo "CMAKE_PREFIX_PATH: $CMAKE_PREFIX_PATH"

west build -p always \
  -b "$BOARD" \
  .

echo ""
echo "Generated HEX files:"
find build -name "*.hex" -print
