#!/bin/bash

set -e

VERSION=$(date +%Y%m%d-%H%M%S)

mkdir -p release

PACKAGE_NAME="firmware-${VERSION}.tar.gz"

tar -czf release/${PACKAGE_NAME} build/

echo "PACKAGE_NAME=${PACKAGE_NAME}" > release/package.env

echo "===== PACKAGE DONE ====="

ls -lah release