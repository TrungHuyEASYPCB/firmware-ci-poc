import os
import subprocess
from pathlib import Path


def test_publish_hil_summary_to_custom_step_summary(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "hil-summary.md").write_text(
        "# HIL summary\n\nStatus: ✅ **passed**\n\n- Device ID: `dut-01`\n",
        encoding="utf-8",
    )

    step_summary = tmp_path / "step-summary.md"

    env = os.environ.copy()
    env["GITHUB_STEP_SUMMARY"] = str(step_summary)

    subprocess.run(
        [
            "python3",
            "scripts/publish_hil_summary.py",
            "--results-dir",
            str(results),
            "--title",
            "Test HIL summary",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    text = step_summary.read_text(encoding="utf-8")

    assert "# Test HIL summary" in text
    assert "Status: ✅ **passed**" in text
    assert "dut-01" in text


def test_publish_hil_summary_fallback_when_missing(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    step_summary = tmp_path / "step-summary.md"

    env = os.environ.copy()
    env["GITHUB_STEP_SUMMARY"] = str(step_summary)

    subprocess.run(
        [
            "python3",
            "scripts/publish_hil_summary.py",
            "--results-dir",
            str(results),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    text = step_summary.read_text(encoding="utf-8")

    assert "HIL summary file was not found." in text
