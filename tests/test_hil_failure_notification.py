import json
import subprocess
from pathlib import Path


def test_notify_hil_failure_dry_run_outputs_issue(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "device_id": "dut-01",
                "device_role": "preview",
                "test_profile": "smoke",
                "board": "nrf52dk/nrf52832",
                "serial": "1050325823",
                "uart_port": "/dev/ttyACM0",
                "expected_version": "0.3.4",
                "expected_commit": "abcdef0",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (results / "hil-summary.md").write_text(
        "# HIL summary\n\nStatus: ❌ **failed**\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/notify_hil_failure.py",
            "--results-dir",
            str(results),
            "--dry-run",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "DRY RUN" in result.stdout
    assert "[Nightly HIL] failed on dut-01/smoke" in result.stdout
    assert "Nightly HIL validation did not pass." in result.stdout


def test_notify_hil_failure_passed_noops(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "device_id": "dut-01",
                "test_profile": "smoke",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/notify_hil_failure.py",
            "--results-dir",
            str(results),
            "--dry-run",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "HIL status passed. No issue notification needed." in result.stdout
