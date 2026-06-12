#!/bin/bash

BOARD=$1

echo "===================="
echo "FLASH FRAMEWORK"
echo "===================="

echo "Board: $BOARD"

if grep -q "$BOARD:" boards/boards.yaml; then
    echo "Board found in registry"
else
    echo "Board not found"
    exit 1
fi