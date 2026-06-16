#!/bin/bash
set -euo pipefail

IMAGE_NAME="${NCS_DOCKER_IMAGE:-firmware-ci-poc-ncs:2.9.2}"
NCS_VERSION="${NCS_VERSION:-2.9.2}"
ZEPHYR_SDK_VERSION="${ZEPHYR_SDK_VERSION:-0.17.0}"
REPO_DIR="$(pwd -P)"
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found"
  exit 1
fi

echo "===================="
echo "DOCKER NCS BUILD"
echo "===================="
echo "Image: $IMAGE_NAME"
echo "NCS version: $NCS_VERSION"
echo "Zephyr SDK version: $ZEPHYR_SDK_VERSION"
echo "Repo dir: $REPO_DIR"
echo "Host UID: $HOST_UID"
echo "Host GID: $HOST_GID"
echo "Board: ${BOARD:-nrf52dk/nrf52832}"
echo "Release version: ${RELEASE_VERSION:-}"
echo "Firmware version: ${FW_VERSION:-}"

echo ""
echo "Build Docker NCS image"
docker build \
  -f docker/Dockerfile.ncs \
  --build-arg NCS_VERSION="$NCS_VERSION" \
  --build-arg ZEPHYR_SDK_VERSION="$ZEPHYR_SDK_VERSION" \
  -t "$IMAGE_NAME" \
  .

echo ""
echo "Run Zephyr build inside Docker NCS image"
docker run --rm \
  -e HOME=/tmp \
  -e HOST_UID="$HOST_UID" \
  -e HOST_GID="$HOST_GID" \
  -e NCS_DOCKER_BUILD=1 \
  -e NCS_ROOT=/opt/ncs \
  -e ZEPHYR_BASE=/opt/ncs/zephyr \
  -e ZEPHYR_SDK_INSTALL_DIR="/opt/zephyr-sdk-${ZEPHYR_SDK_VERSION}" \
  -e ZEPHYR_TOOLCHAIN_VARIANT=zephyr \
  -e BOARD="${BOARD:-}" \
  -e RELEASE_VERSION="${RELEASE_VERSION:-}" \
  -e FW_VERSION="${FW_VERSION:-}" \
  -e FW_GIT_COMMIT="${FW_GIT_COMMIT:-}" \
  -e FW_GIT_REF="${FW_GIT_REF:-}" \
  -v "$REPO_DIR:$REPO_DIR" \
  -w "$REPO_DIR" \
  "$IMAGE_NAME" \
  bash -lc '
    set -euo pipefail

    git config --global --add safe.directory "$PWD" || true

    echo "Container user: $(id)"
    echo "Working dir: $(pwd)"
    echo "west: $(west --version)"
    echo "cmake: $(cmake --version | head -n 1)"
    echo "ninja: $(ninja --version)"
    echo "ZEPHYR_BASE=$ZEPHYR_BASE"
    echo "ZEPHYR_TOOLCHAIN_VARIANT=$ZEPHYR_TOOLCHAIN_VARIANT"
    echo "ZEPHYR_SDK_INSTALL_DIR=$ZEPHYR_SDK_INSTALL_DIR"
    echo ""

    rm -rf build
    ./scripts/build.sh

    if [ -d build ]; then
      chown -R "$HOST_UID:$HOST_GID" build
    fi
  '

echo ""
echo "Docker NCS build completed"
find build -type f \( -name "*.hex" -o -name "*.elf" -o -name "*.bin" \) | sort
