from pathlib import Path


def test_nightly_hil_workflow_exists():
    path = Path(".github/workflows/nightly-hil.yml")

    assert path.is_file()

    text = path.read_text(encoding="utf-8")

    assert "Nightly HIL Regression" in text
    assert "schedule:" in text
    assert "workflow_dispatch:" in text
    assert "scripts/generate_hil_matrix.py" in text
    assert "scripts/with_device_lock.sh" in text
    assert "max-parallel: 1" in text
