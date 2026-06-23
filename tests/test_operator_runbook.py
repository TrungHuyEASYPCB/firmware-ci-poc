from pathlib import Path


def test_operator_runbook_exists():
    path = Path("docs/operator-runbook.md")

    assert path.is_file()

    text = path.read_text(encoding="utf-8")

    required_sections = [
        "Firmware CI/CD Operator Runbook",
        "Branch policy",
        "Release workflow",
        "GitHub Release approval",
        "Manual HIL Matrix test",
        "Manual Nightly HIL Regression test",
        "Stable promotion",
        "Common troubleshooting",
        "Stage completion checklist",
    ]

    for section in required_sections:
        assert section in text


def test_operator_runbook_mentions_critical_commands():
    text = Path("docs/operator-runbook.md").read_text(encoding="utf-8")

    required_commands = [
        "git fetch origin --tags --force",
        "python3 scripts/runner_maintenance.py",
        "python3 scripts/device_preflight.py",
        "python3 scripts/verify_release_gate.py",
        "./scripts/docker_ci.sh",
        "./scripts/docker_build.sh",
        "./scripts/package.sh",
        "source_tag: v<version>",
    ]

    for command in required_commands:
        assert command in text
