import json
import subprocess
from pathlib import Path


def test_resolve_smoke_profile():
    assert Path("inventory/test_matrix.yaml").is_file()
    assert Path("scripts/resolve_test_profile.py").is_file()

    result = subprocess.run(
        [
            "python3",
            "scripts/resolve_test_profile.py",
            "--profile",
            "smoke",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    data = json.loads(result.stdout)

    assert data["profile"] == "smoke"
    assert data["pytest_markers"]
    assert data["uart_capture_seconds"] >= 1


def test_resolve_regression_profile_shell_output():
    result = subprocess.run(
        [
            "python3",
            "scripts/resolve_test_profile.py",
            "--profile",
            "regression",
            "--output",
            "shell",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "export TEST_PROFILE='regression'" in result.stdout
    assert "export PYTEST_MARKERS=" in result.stdout
    assert "export UART_CAPTURE_SECONDS=" in result.stdout


def test_unknown_profile_fails():
    result = subprocess.run(
        [
            "python3",
            "scripts/resolve_test_profile.py",
            "--profile",
            "unknown-profile",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0
    assert "Unknown test profile" in result.stderr
