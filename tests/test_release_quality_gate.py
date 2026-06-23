import json
import subprocess
from pathlib import Path


def test_release_gate_passes_with_matching_hil_summary(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "firmware_version": "0.3.9",
                "device_id": "dut-01",
                "profile": "regression",
            }
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            "python3",
            "scripts/verify_release_gate.py",
            "--results-dir",
            str(results),
            "--version",
            "0.3.9",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    gate = json.loads((results / "release-gate.json").read_text(encoding="utf-8"))

    assert gate["status"] == "passed"
    assert (results / "release-gate.md").is_file()


def test_release_gate_fails_on_failed_hil_summary(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.json").write_text(
        json.dumps(
            {
                "status": "failed",
                "firmware_version": "0.3.9",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/verify_release_gate.py",
            "--results-dir",
            str(results),
            "--version",
            "0.3.9",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0
    assert "hil_status_passed" in result.stderr


def test_release_gate_fails_on_version_mismatch(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "firmware_version": "0.3.8",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/verify_release_gate.py",
            "--results-dir",
            str(results),
            "--version",
            "0.3.9",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0
    assert "release_version_matched" in result.stderr
