#!/bin/bash

set -e

echo "===================="
echo "DEVICE DETECTION"
echo "===================="

IDS=$(nrfjprog --ids 2>/dev/null)

if [ -z "$IDS" ]; then
    echo "No Nordic device detected"
    exit 1
fi

echo "Detected devices:"
echo "$IDS"

mkdir -p inventory

cat > inventory/devices.yaml <<EOF
devices:
  dut-01:
    board: nrf52840dk
    serial: $IDS
    status: ready
EOF

echo ""
echo "Generated inventory:"
cat inventory/devices.yaml
