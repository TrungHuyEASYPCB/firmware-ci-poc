#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Install with: sudo apt install -y python3-yaml")
    sys.exit(1)


def main():
    files = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.exists() and path.is_file():
            files.append(path)

    if not files:
        print("No YAML files found to check.")
        return

    failed = False

    for path in files:
        try:
            with path.open("r", encoding="utf-8") as f:
                yaml.safe_load(f)
            print(f"YAML OK: {path}")
        except Exception as exc:
            failed = True
            print(f"YAML FAIL: {path}")
            print(exc)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
