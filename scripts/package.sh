#!/bin/bash

set -e

VERSION=$(date +%Y%m%d-%H%M%S)

mkdir -p release

PACKAGE_NAME="firmware-${VERSION}.tar.gz"

tar -czf release/${PACKAGE_NAME} build/

echo "PACKAGE_NAME=${PACKAGE_NAME}" > release/package.env

echo "===== PACKAGE DONE ====="

ls -lah release

COMMIT=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VERSION=$(date +%Y%m%d-%H%M%S)