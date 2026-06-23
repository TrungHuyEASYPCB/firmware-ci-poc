import json
import os
import subprocess
from pathlib import Path


def write_fake_nrfutil(bin_dir, output):
    fake = bin_dir / "nrfutil"
    fake.write_text(f"#!/bin/sh\necho '{output}'\n", encoding="utf-8")
    fake.chmod(0o755)


def test_device_preflight_passes_with_fake_nrfutil(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_fake_nrfutil(bin_dir, "1050325823 nRF52 DK")

    uart = tmp_path / "ttyACM0"
    uart.write_text("", encoding="utf-8")

    inventory = tmp_path / "devices.yaml"
    inventory.write_text(
        """
devices:
  - id: dut-01
    role: preview
    status: ready
    serial: "1050325823"
    board: nrf52dk/nrf52832
    family: nrf52
    uart_port: "{uart}"
""".format(uart=uart),
        encoding="utf-8",
    )

    results = tmp_path / "hil-results"

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    subprocess.run(
        [
            "python3",
            "scripts/device_preflight.py",
            "--inventory",
            str(inventory),
            "--role",
            "preview",
            "--results-dir",
            str(results),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    report = json.loads((results / "device-preflight.json").read_text(encoding="utf-8"))

    assert report["status"] == "passed"
    assert report["device_id"] == "dut-01"
    assert report["serial"] == "1050325823"
    assert (results / "device-preflight.md").is_file()


def test_device_preflight_fails_when_serial_missing(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    write_fake_nrfutil(bin_dir, "no matching devices")

    uart = tmp_path / "ttyACM0"
    uart.write_text("", encoding="utf-8")

    inventory = tmp_path / "devices.yaml"
    inventory.write_text(
        """
devices:
  - id: dut-01
    role: preview
    status: ready
    serial: "1050325823"
    board: nrf52dk/nrf52832
    family: nrf52
    uart_port: "{uart}"
""".format(uart=uart),
        encoding="utf-8",
    )

    results = tmp_path / "hil-results"

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(
        [
            "python3",
            "scripts/device_preflight.py",
            "--inventory",
            str(inventory),
            "--role",
            "preview",
            "--results-dir",
            str(results),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    assert result.returncode != 0

    report = json.loads((results / "device-preflight.json").read_text(encoding="utf-8"))

    assert report["status"] == "failed"
