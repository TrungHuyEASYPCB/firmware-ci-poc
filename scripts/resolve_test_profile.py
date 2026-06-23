#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required.", file=sys.stderr)
    sys.exit(1)


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_yaml(path):
    p = Path(path)

    if not p.is_file():
        fail(f"Test matrix file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def shell_quote(value):
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def main():
    parser = argparse.ArgumentParser(description="Resolve HIL test profile configuration")
    parser.add_argument("--matrix", default="inventory/test_matrix.yaml")
    parser.add_argument("--profile", default=os.environ.get("TEST_PROFILE", "smoke"))
    parser.add_argument("--output", choices=["json", "shell", "pretty"], default="json")
    parser.add_argument("--github-output", default="")
    args = parser.parse_args()

    matrix = load_yaml(args.matrix)
    profiles = matrix.get("profiles", {})

    if args.profile not in profiles:
        fail(f"Unknown test profile: {args.profile}. Available profiles: {', '.join(sorted(profiles))}")

    profile = profiles[args.profile] or {}

    resolved = {
        "profile": args.profile,
        "description": str(profile.get("description", "")),
        "pytest_markers": str(profile.get("pytest_markers", "hil")),
        "uart_capture_seconds": int(profile.get("uart_capture_seconds", 5)),
        "retry_count": int(profile.get("retry_count", 0)),
        "expected_runtime": str(profile.get("expected_runtime", "")),
    }

    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as f:
            for key, value in resolved.items():
                f.write(f"{key}={value}\n")

    if args.output == "pretty":
        print(json.dumps(resolved, indent=2))
    elif args.output == "shell":
        print(f"export TEST_PROFILE={shell_quote(resolved['profile'])}")
        print(f"export PYTEST_MARKERS={shell_quote(resolved['pytest_markers'])}")
        print(f"export UART_CAPTURE_SECONDS={shell_quote(resolved['uart_capture_seconds'])}")
        print(f"export HIL_RETRY_COUNT={shell_quote(resolved['retry_count'])}")
        print(f"export TEST_PROFILE_DESCRIPTION={shell_quote(resolved['description'])}")
    else:
        print(json.dumps(resolved, separators=(",", ":")))


if __name__ == "__main__":
    main()
