import json
import subprocess
from pathlib import Path


def test_write_hil_report_generates_json_and_markdown(tmp_path):
    results = tmp_path / "hil-results"
    results.mkdir()

    (results / "run_metadata.json").write_text(
        json.dumps(
            {
                "device_id": "dut-01",
                "device_role": "preview",
                "test_profile": "smoke",
                "serial": "1050325823",
                "uart_port": "/dev/ttyACM0",
                "expected_version": "0.3.2",
                "expected_commit": "abcdef0",
                "expected_board": "nrf52dk/nrf52832",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (results / "pytest-junit.xml").write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="2" time="1.23">
  <testcase classname="tests.hil.test_uart" name="test_uart_port_exists" time="0.10" />
  <testcase classname="tests.hil.test_uart" name="test_device_detected_by_nrfutil" time="0.20" />
</testsuite>
""",
        encoding="utf-8",
    )

    subprocess.run(
        [
            "python3",
            "scripts/write_hil_report.py",
            "--results-dir",
            str(results),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    summary_json = results / "hil-summary.json"
    summary_md = results / "hil-summary.md"

    assert summary_json.is_file()
    assert summary_md.is_file()

    data = json.loads(summary_json.read_text(encoding="utf-8"))

    assert data["schema"] == "firmware-ci-poc.hil-summary.v1"
    assert data["status"] == "passed"
    assert data["tests"] == 2
    assert data["failures"] == 0
    assert data["device_id"] == "dut-01"
    assert data["expected_version"] == "0.3.2"

    md = summary_md.read_text(encoding="utf-8")
    assert "# HIL summary" in md
    assert "dut-01" in md
    assert "0.3.2" in md
