import json
import subprocess
from pathlib import Path


def test_generate_hil_matrix_preview_smoke():
    assert Path("scripts/generate_hil_matrix.py").is_file()
    assert Path("inventory/devices.yaml").is_file()

    result = subprocess.run(
        [
            "python3",
            "scripts/generate_hil_matrix.py",
            "--profile",
            "smoke",
            "--roles",
            "preview",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    matrix = json.loads(result.stdout)

    assert "include" in matrix
    assert matrix["include"]

    first = matrix["include"][0]

    assert first["profile"] == "smoke"
    assert first["serial"]
    assert first["board"]
    assert first["device_id"]
    assert first["uart_port"]
