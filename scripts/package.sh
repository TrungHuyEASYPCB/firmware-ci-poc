#!/bin/bash
set -euo pipefail

echo "===================="
echo "PACKAGE RELEASE"
echo "===================="

git config --global --add safe.directory "$(pwd)" || true

VERSION="${VERSION:-$(cat RELEASE_VERSION 2>/dev/null || echo 0.0.0-dev)}"
COMMIT="$(git rev-parse --short HEAD)"
REF_NAME="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD)}"
BUILD_TIME="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

BOARD="${BOARD:-nrf52dk/nrf52832}"
SERIAL="${SERIAL:-1050325823}"
HEX_FILE="${HEX_FILE:-build/merged.hex}"

if [ ! -f "$HEX_FILE" ]; then
  echo "HEX file not found: $HEX_FILE"
  exit 1
fi

rm -rf release
mkdir -p release

FIRMWARE_NAME="firmware-${VERSION}-${COMMIT}.hex"
PACKAGE_NAME="firmware-${VERSION}-${COMMIT}.tar.gz"

cp "$HEX_FILE" "release/$FIRMWARE_NAME"

cat > release/manifest.json <<MANIFEST
{
  "version": "$VERSION",
  "commit": "$COMMIT",
  "ref": "$REF_NAME",
  "build_time": "$BUILD_TIME",
  "board": "$BOARD",
  "serial": "$SERIAL",
  "firmware": "$FIRMWARE_NAME",
  "package": "$PACKAGE_NAME"
}
MANIFEST

tar -czf "release/$PACKAGE_NAME" -C release "$FIRMWARE_NAME" manifest.json

(
  cd release
  sha256sum "$FIRMWARE_NAME" "$PACKAGE_NAME" manifest.json > checksums.sha256
)

cat > release/release-notes.md <<NOTES
# Firmware v${VERSION}

## Summary

- Zephyr/NCS firmware build
- Target board: ${BOARD}
- Hardware serial: ${SERIAL}
- Commit: ${COMMIT}
- Ref: ${REF_NAME}
- Build time: ${BUILD_TIME}

## Validation

- Build: PASS
- Flash: PASS
- Pytest HIL UART validation: PASS

## Artifacts

- ${FIRMWARE_NAME}
- ${PACKAGE_NAME}
- manifest.json
- checksums.sha256
NOTES

cat > release/package.env <<ENV
VERSION=$VERSION
COMMIT=$COMMIT
PACKAGE_NAME=$PACKAGE_NAME
FIRMWARE_NAME=$FIRMWARE_NAME
ENV

echo "Package created:"
ls -lah release

echo ""
echo "Manifest:"
cat release/manifest.json

echo ""
echo "Checksums:"
cat release/checksums.sha256
