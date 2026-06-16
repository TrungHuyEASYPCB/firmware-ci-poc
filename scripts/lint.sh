#!/bin/bash
set -euo pipefail

echo "===================="
echo "STATIC ANALYSIS"
echo "===================="

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

need_command python3
need_command shellcheck

echo ""
echo "Check Python syntax without writing __pycache__"
python3 - <<'PY'
import ast
import sys
from pathlib import Path

failed = False

for root in [Path("scripts"), Path("tests")]:
    if not root.exists():
        continue

    for path in sorted(root.rglob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            print(f"Python OK: {path}")
        except SyntaxError as exc:
            failed = True
            print(f"Python FAIL: {path}")
            print(exc)

if failed:
    sys.exit(1)
PY

echo ""
echo "Check pytest collection"
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest --collect-only -q tests

echo ""
echo "Check deprecated Nordic CLI usage"
DEPRECATED_NORDIC_CLI_MATCHES="$(
  grep -RIn \
    --exclude="lint.sh" \
    --exclude-dir=".git" \
    --exclude-dir="build" \
    --exclude-dir="hil-results" \
    "nrfjprog" \
    scripts tests .github/workflows inventory README.md docs \
    2>/dev/null || true
)"

if [ -n "$DEPRECATED_NORDIC_CLI_MATCHES" ]; then
  echo "$DEPRECATED_NORDIC_CLI_MATCHES"
  echo "Deprecated Nordic CLI usage found. Use nrfutil device instead."
  exit 1
fi

echo ""
echo "Check shell scripts"
mapfile -t SHELL_FILES < <(find scripts -type f -name "*.sh" | sort)

if [ "${#SHELL_FILES[@]}" -eq 0 ]; then
  echo "No shell scripts found."
else
  shellcheck "${SHELL_FILES[@]}"
fi

echo ""
echo "Validate HIL inventory and test matrix"
python3 scripts/validate_inventory.py

echo ""
echo "Check YAML syntax"
python3 scripts/check_yaml.py \
  .github/workflows/*.yml \
  .github/workflows/*.yaml \
  inventory/*.yaml \
  inventory/*.yml

echo ""
echo "Check executable scripts"
for file in scripts/*.sh scripts/*.py; do
  [ -e "$file" ] || continue

  if [ ! -x "$file" ]; then
    echo "Script is not executable: $file"
    exit 1
  fi
done

echo ""
echo "Static analysis PASS"
