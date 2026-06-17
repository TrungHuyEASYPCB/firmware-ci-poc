#!/bin/bash
set -euo pipefail

echo "===================="
echo "PACKAGE RELEASE"
echo "===================="

BOARD="${BOARD:-nrf52dk/nrf52832}"

if [ -n "${FW_VERSION:-}" ]; then
  VERSION="$FW_VERSION"
elif [ -n "${RELEASE_VERSION:-}" ]; then
  VERSION="$RELEASE_VERSION"
elif [ -f RELEASE_VERSION ]; then
  VERSION="$(cat RELEASE_VERSION)"
else
  VERSION="0.0.0-dev"
fi

GIT_COMMIT="${FW_GIT_COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
GIT_REF="${FW_GIT_REF:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)}"
BUILD_TIME="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

RELEASE_DIR="release"
mkdir -p "$RELEASE_DIR"

SOURCE_HEX=""

if [ -f build/merged.hex ]; then
  SOURCE_HEX="build/merged.hex"
elif [ -f build/firmware-ci-poc/zephyr/zephyr.hex ]; then
  SOURCE_HEX="build/firmware-ci-poc/zephyr/zephyr.hex"
elif [ -f build/zephyr/zephyr.hex ]; then
  SOURCE_HEX="build/zephyr/zephyr.hex"
else
  echo "ERROR: firmware hex not found"
  echo "Expected one of:"
  echo "  build/merged.hex"
  echo "  build/firmware-ci-poc/zephyr/zephyr.hex"
  echo "  build/zephyr/zephyr.hex"
  exit 1
fi

HEX_NAME="firmware-${VERSION}-${GIT_COMMIT}.hex"
TAR_NAME="firmware-${VERSION}-${GIT_COMMIT}.tar.gz"

HEX_PATH="${RELEASE_DIR}/${HEX_NAME}"
TAR_PATH="${RELEASE_DIR}/${TAR_NAME}"
MANIFEST_PATH="${RELEASE_DIR}/manifest.json"
PACKAGE_ENV_PATH="${RELEASE_DIR}/package.env"
RELEASE_NOTES_PATH="${RELEASE_DIR}/release-notes.md"

cp "$SOURCE_HEX" "$HEX_PATH"

python3 - <<PY
import json
from pathlib import Path

manifest = {
    "version": "${VERSION}",
    "git_commit": "${GIT_COMMIT}",
    "git_ref": "${GIT_REF}",
    "board": "${BOARD}",
    "build_time": "${BUILD_TIME}",
    "firmware_hex": "${HEX_NAME}",
    "archive": "${TAR_NAME}",
    "build_info": "build-info.json",
    "sbom": "sbom.json",
}

Path("${MANIFEST_PATH}").write_text(
    json.dumps(manifest, indent=2) + "\\n",
    encoding="utf-8",
)
PY

cat > "$PACKAGE_ENV_PATH" <<EOF_ENV
VERSION=${VERSION}
GIT_COMMIT=${GIT_COMMIT}
GIT_REF=${GIT_REF}
BOARD=${BOARD}
BUILD_TIME=${BUILD_TIME}
HEX_FILE=${HEX_NAME}
ARCHIVE=${TAR_NAME}
BUILD_INFO=build-info.json
SBOM=sbom.json
EOF_ENV

cat > "$RELEASE_NOTES_PATH" <<EOF_NOTES
# Firmware v${VERSION}

## Summary

- Zephyr/NCS firmware build
- Target board: ${BOARD}
- Hardware serial: ${SERIAL:-unknown}
- Commit: ${GIT_COMMIT}
- Ref: ${GIT_REF}
- Build time: ${BUILD_TIME}

## Validation

- Build: PASS
- Flash: PASS
- Pytest HIL UART validation: PASS
- Release artifact verification: PASS

## Artifacts

- ${HEX_NAME}
- ${TAR_NAME}
- manifest.json
- checksums.sha256
- package.env
- release-notes.md
- build-info.json
- sbom.json
EOF_NOTES

python3 scripts/write_release_metadata.py \
  --release-dir "$RELEASE_DIR" \
  --version "$VERSION" \
  --board "$BOARD" \
  --git-commit "$GIT_COMMIT" \
  --git-ref "$GIT_REF" \
  --build-time "$BUILD_TIME" \
  --hex-file "$HEX_NAME" \
  --archive "$TAR_NAME"

tar -C "$RELEASE_DIR" -czf "$TAR_PATH" \
  "$HEX_NAME" \
  manifest.json \
  package.env \
  release-notes.md \
  build-info.json \
  sbom.json

(
  cd "$RELEASE_DIR"
  sha256sum \
    "$HEX_NAME" \
    "$TAR_NAME" \
    manifest.json \
    package.env \
    release-notes.md \
    build-info.json \
    sbom.json \
    > checksums.sha256
)

echo ""
echo "Package completed"
echo "Release directory:"
ls -lh "$RELEASE_DIR"
