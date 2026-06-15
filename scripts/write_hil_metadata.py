#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(command):
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def main():
    output_dir = Path(os.environ.get("HIL_RESULTS_DIR", "hil-results"))
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device_id": os.environ.get("DEVICE_ID", "unknown"),
        "device_role": os.environ.get("DEVICE_ROLE", "unknown"),
        "board": os.environ.get("BOARD", "unknown"),
        "serial": os.environ.get("SERIAL", "unknown"),
        "uart_port": os.environ.get("UART_PORT", "unknown"),
        "hex_file": os.environ.get("HEX_FILE", "unknown"),
        "expected_version": os.environ.get("EXPECTED_VERSION", "unknown"),
        "expected_commit": os.environ.get("EXPECTED_COMMIT", "unknown"),
        "expected_board": os.environ.get("EXPECTED_BOARD", "unknown"),
        "git_commit": run(["git", "rev-parse", "--short", "HEAD"]),
        "git_ref": run(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "hostname": run(["hostname"]),
        "user": run(["whoami"]),
    }

    path = output_dir / "run_metadata.json"
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print(f"HIL metadata written to {path}")


if __name__ == "__main__":
    main()
