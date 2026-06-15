import os
import pytest
import subprocess
import time


SERIAL = os.environ.get("SERIAL", "1050325823")
UART_PORT = os.environ.get("UART_PORT", "/dev/ttyACM0")
pytestmark = pytest.mark.hil


EXPECTED_TEXTS = [
    "BOOT OK",
    "Firmware CI PoC started",
    "Heartbeat",
]


def run_command(command, check=True):
    return subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=check,
    )


def test_uart_port_exists():
    assert os.path.exists(UART_PORT), f"UART port not found: {UART_PORT}"


def test_device_detected_by_nrfjprog():
    result = run_command(["nrfjprog", "--ids"], check=False)

    combined_output = result.stdout + result.stderr

    assert SERIAL in combined_output, (
        f"Device serial {SERIAL} not found in nrfjprog output:\n"
        f"{combined_output}"
    )


def test_firmware_uart_log_after_reset():
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
        ["timeout", "15", "cat", UART_PORT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    time.sleep(1)

    reset_result = run_command(
        ["nrfjprog", "--reset", "--snr", SERIAL],
        check=False,
    )

    stdout, stderr = cat_process.communicate(timeout=20)
    uart_log = stdout + stderr

    print("\n===== NRFJPROG RESET OUTPUT =====")
    print(reset_result.stdout)
    print(reset_result.stderr)

    print("\n===== UART LOG =====")
    print(uart_log)

    assert any(text in uart_log for text in EXPECTED_TEXTS), (
        "Expected firmware log was not found in UART output.\n"
        f"Expected one of: {EXPECTED_TEXTS}\n"
        f"UART log:\n{uart_log}"
    )
