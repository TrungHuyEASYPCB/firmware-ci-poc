#!/bin/bash

set -e

VERSION=$(date +%Y%m%d-%H%M%S)

mkdir -p release

tar -czf release/firmware-${VERSION}.tar.gz build/

echo "===== PACKAGE DONE ====="

ls -lah release
