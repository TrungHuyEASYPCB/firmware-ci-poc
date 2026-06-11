#!/bin/bash

set -e

echo "===== BUILD START ====="

mkdir -p build

gcc firmware/main.c -o build/firmware

echo "===== BUILD DONE ====="

ls -lah build
