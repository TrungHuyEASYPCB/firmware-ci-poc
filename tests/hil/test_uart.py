import os
import subprocess
import time
from pathlib import Path

import pytest


pytestmark = pytest.mark.hil


SERIAL = os.environ.get("SERIAL", "1050325823")
UART_PORT = os.environ.get("UART_PORT", "/dev/ttyACM0")
EXPECTED_BOARD = os.environ.get("EXPECTED_BOARD", os.environ.get("BOARD", "nrf52dk/nrf52832"))
UART_LOG_FILE = Path(os.environ.get("UART_LOG_FILE", "hil-results/uart.log"))
RESET_LOG_FILE = Path(os.environ.get("RESET_LOG_FILE", "hil-results/reset.log"))


def run_command(command, check=True):
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=check,
    )


def get_expected_version():
    env_version = os.environ.get("EXPECTED_VERSION")
    if env_version:
        return env_version

    version_file = Path("RELEASE_VERSION")
    if version_file.exists():
        return version_file.read_text().strip()

    return "0.0.0-dev"


def get_expected_commit():
    env_commit = os.environ.get("EXPECTED_COMMIT")
    if env_commit:
        return env_commit

    result = run_command(["git", "rev-parse", "--short", "HEAD"], check=False)
    if result.returncode == 0:
        return result.stdout.strip()

    return "unknown"


def capture_uart_after_reset():
    UART_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESET_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    run_command([
        "stty",
        "-F",
        UART_PORT,
        "115200",
        "cs8",
        "-cstopb",
        "-parenb",
        "-ixon",
        "-ixoff",
        "-crtscts",
        "raw",
        "-echo",
    ])

    cat_process = subprocess.Popen(
        ["timeout", "20", "cat", UART_PORT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    time.sleep(1)

    reset_result = run_command(
        ["nrfjprog", "--reset", "--snr", SERIAL],
        check=False,
    )

    reset_output = reset_result.stdout + reset_result.stderr
    RESET_LOG_FILE.write_text(reset_output, encoding="utf-8")

    stdout, stderr = cat_process.communicate(timeout=25)
    uart_log = stdout + stderr
    UART_LOG_FILE.write_text(uart_log, encoding="utf-8")

    print("\n===== NRFJPROG RESET OUTPUT =====")
    print(reset_output)

    print("\n===== UART LOG =====")
    print(uart_log)

    return uart_log


def test_uart_port_exists():
    assert os.path.exists(UART_PORT), f"UART port not found: {UART_PORT}"


def test_device_detected_by_nrfjprog():
    result = run_command(["nrfjprog", "--ids"], check=False)
    combined_output = result.stdout + result.stderr

    assert SERIAL in combined_output, (
        f"Device serial {SERIAL} not found in nrfjprog output:\n"
        f"{combined_output}"
    )


def test_firmware_uart_provenance_after_reset():
    expected_version = get_expected_version()
    expected_commit = get_expected_commit()

    uart_log = capture_uart_after_reset()

    required_texts = [
        "BOOT OK",
        f"Firmware version: {expected_version}",
        f"Git commit: {expected_commit}",
        f"Board: {EXPECTED_BOARD}",
        "Firmware CI PoC started",
        "Heartbeat",
    ]

    missing = [text for text in required_texts if text not in uart_log]

    assert not missing, (
        "Missing expected firmware provenance text in UART log.\n"
        f"Missing: {missing}\n"
        f"UART log:\n{uart_log}"
    )
