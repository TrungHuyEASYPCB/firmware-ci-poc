#!/bin/bash
set -euo pipefail

IMAGE_NAME="${CI_DOCKER_IMAGE:-firmware-ci-poc-ci:latest}"
REPO_DIR="$(pwd -P)"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker command not found"
  exit 1
fi

echo "===================="
echo "DOCKER STATIC ANALYSIS SANDBOX"
echo "===================="
echo "Image: $IMAGE_NAME"
echo "Repo dir: $REPO_DIR"

echo ""
echo "Build Docker CI image"
docker build \
  -f docker/Dockerfile.ci \
  -t "$IMAGE_NAME" \
  .

echo ""
echo "Run static analysis inside Docker"
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$REPO_DIR:$REPO_DIR" \
  -w "$REPO_DIR" \
  "$IMAGE_NAME" \
  bash -lc '
    set -euo pipefail

    echo "Container user: $(id)"
    echo "Working dir: $(pwd)"
    echo "python3: $(python3 --version)"
    echo "shellcheck: $(shellcheck --version | head -n 1)"
    echo ""

    ./scripts/lint.sh
  '

echo ""
echo "Docker static analysis sandbox PASS"
