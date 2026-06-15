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
echo "Check shell scripts"
mapfile -t SHELL_FILES < <(find scripts -type f -name "*.sh" | sort)

if [ "${#SHELL_FILES[@]}" -eq 0 ]; then
  echo "No shell scripts found."
else
  shellcheck "${SHELL_FILES[@]}"
fi

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
