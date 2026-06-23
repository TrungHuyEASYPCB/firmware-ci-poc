import json
import os
import subprocess
import time
from pathlib import Path


def test_runner_maintenance_generates_report(tmp_path):
    results = tmp_path / "hil-results"
    lock_dir = tmp_path / "locks"

    subprocess.run(
        [
            "python3",
            "scripts/runner_maintenance.py",
            "--results-dir",
            str(results),
            "--lock-dir",
            str(lock_dir),
            "--min-free-gb",
            "0",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    report = json.loads((results / "runner-maintenance.json").read_text(encoding="utf-8"))

    assert report["status"] == "passed"
    assert (results / "runner-maintenance.md").is_file()
    assert lock_dir.is_dir()


def test_runner_maintenance_reports_stale_lock_when_enabled(tmp_path):
    results = tmp_path / "hil-results"
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()

    lock_file = lock_dir / "dut-01.lock"
    lock_file.write_text("", encoding="utf-8")

    old_time = time.time() - 3600
    os.utime(lock_file, (old_time, old_time))

    result = subprocess.run(
        [
            "python3",
            "scripts/runner_maintenance.py",
            "--results-dir",
            str(results),
            "--lock-dir",
            str(lock_dir),
            "--min-free-gb",
            "0",
            "--stale-minutes",
            "1",
            "--warn-on-stale-locks",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0

    report = json.loads((results / "runner-maintenance.json").read_text(encoding="utf-8"))

    assert report["status"] == "failed"
    assert report["lock_files"][0]["stale"] is True
