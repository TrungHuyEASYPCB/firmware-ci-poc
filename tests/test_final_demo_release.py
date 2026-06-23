from pathlib import Path


def test_final_demo_release_doc_exists():
    path = Path("docs/final-demo-release.md")

    assert path.is_file()

    text = path.read_text(encoding="utf-8")

    required = [
        "Final Demo Release",
        "v1.0.0",
        "Completed capabilities",
        "Release quality gate",
        "Stable promotion workflow",
        "Operator runbook",
        "docs/operator-runbook.md",
    ]

    for item in required:
        assert item in text


def test_operator_runbook_still_exists_for_final_release():
    assert Path("docs/operator-runbook.md").is_file()
