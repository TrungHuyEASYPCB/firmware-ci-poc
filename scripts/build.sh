#!/bin/bash
set -euo pipefail

BOARD="${BOARD:-nrf52dk/nrf52832}"

if [ "${NCS_DOCKER_BUILD:-0}" = "1" ]; then
  NCS_ROOT="${NCS_ROOT:-/opt/ncs}"
  ZEPHYR_BASE="${ZEPHYR_BASE:-$NCS_ROOT/zephyr}"
  ZEPHYR_SDK_INSTALL_DIR="${ZEPHYR_SDK_INSTALL_DIR:-/opt/zephyr-sdk-0.17.0}"

  export ZEPHYR_BASE
  export ZEPHYR_SDK_INSTALL_DIR
  export ZEPHYR_TOOLCHAIN_VARIANT="${ZEPHYR_TOOLCHAIN_VARIANT:-zephyr}"
else
  NCS_ROOT="${NCS_ROOT:-$HOME/ncs}"
  TOOLCHAIN_ROOT="${TOOLCHAIN_ROOT:-$NCS_ROOT/toolchains/b77d8c1312}"
  ZEPHYR_BASE="${ZEPHYR_BASE:-$NCS_ROOT/v2.9.2/zephyr}"

  export PATH="$TOOLCHAIN_ROOT/usr/local/bin:$PATH"
  export LD_LIBRARY_PATH="$TOOLCHAIN_ROOT/usr/local/lib:${LD_LIBRARY_PATH:-}"
  export ZEPHYR_BASE
  export CMAKE_PREFIX_PATH="$TOOLCHAIN_ROOT/cmake:${CMAKE_PREFIX_PATH:-}"

  unset ZEPHYR_TOOLCHAIN_VARIANT
  unset ZEPHYR_SDK_INSTALL_DIR
  unset ZEPHYR_SDK_INSTALL_DIR_OVERRIDE
  unset ZEPHYR_SDK_INSTALL_DIR_OVERRIDE_DIR
fi

if [ -n "${FW_VERSION:-}" ]; then
  VERSION="$FW_VERSION"
elif [ -n "${RELEASE_VERSION:-}" ]; then
  VERSION="$RELEASE_VERSION"
elif [ -f RELEASE_VERSION ]; then
  VERSION="$(cat RELEASE_VERSION)"
else
  VERSION="0.0.0-dev"
fi

export FW_VERSION="$VERSION"
export FW_GIT_COMMIT="${FW_GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
export FW_GIT_REF="${FW_GIT_REF:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)}"
export FW_BOARD="$BOARD"

echo "===================="
echo "ZEPHYR BUILD"
echo "===================="
echo "Board: $BOARD"
echo "Firmware version: $FW_VERSION"
echo "Firmware git commit: $FW_GIT_COMMIT"
echo "Firmware git ref: $FW_GIT_REF"
echo "NCS_DOCKER_BUILD: ${NCS_DOCKER_BUILD:-0}"
echo "ZEPHYR_BASE: $ZEPHYR_BASE"
echo "ZEPHYR_TOOLCHAIN_VARIANT: ${ZEPHYR_TOOLCHAIN_VARIANT:-unset}"
echo "ZEPHYR_SDK_INSTALL_DIR: ${ZEPHYR_SDK_INSTALL_DIR:-unset}"
echo "CMAKE_PREFIX_PATH: ${CMAKE_PREFIX_PATH:-unset}"
echo "west: $(command -v west || true)"
echo "cmake: $(command -v cmake || true)"
echo "ninja: $(command -v ninja || true)"

if [ "${NCS_DOCKER_BUILD:-0}" = "1" ]; then
  WEST_COMMAND=(west -z "$ZEPHYR_BASE")
else
  WEST_COMMAND=(west)
fi

echo "WEST_COMMAND: ${WEST_COMMAND[*]}"
"${WEST_COMMAND[@]}" build -p always -b "$BOARD" .

if [ ! -f build/merged.hex ] && [ -f build/zephyr/zephyr.hex ]; then
  echo ""
  echo "Create compatibility firmware image: build/merged.hex"
  cp build/zephyr/zephyr.hex build/merged.hex
fi

echo ""
echo "Build completed"
echo "Generated firmware files:"
find build -type f \( -name "*.hex" -o -name "*.elf" -o -name "*.bin" \) | sort
