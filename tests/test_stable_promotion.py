import json
import subprocess
from pathlib import Path


def make_release_dir(path, version="0.4.0"):
    path.mkdir(parents=True)

    (path / "manifest.json").write_text(
        json.dumps({"version": version, "commit": "abc1234"}),
        encoding="utf-8",
    )
    (path / "checksums.sha256").write_text("dummy  manifest.json\n", encoding="utf-8")
    (path / "signature.json").write_text(
        json.dumps({"signature": "dummy-signature"}),
        encoding="utf-8",
    )
    (path / "release-status.json").write_text(
        json.dumps({"version": version, "status": "ready"}),
        encoding="utf-8",
    )
    (path / "build-info.json").write_text(
        json.dumps({"version": version, "commit": "abc1234"}),
        encoding="utf-8",
    )
    (path / f"firmware-{version}-abc1234.hex").write_text(":020000040000FA\n", encoding="utf-8")
    (path / f"firmware-{version}-abc1234.tar.gz").write_bytes(b"fake archive")


def test_stable_promotion_generates_metadata(tmp_path):
    release_dir = tmp_path / "release"
    output_dir = tmp_path / "promotion"
    make_release_dir(release_dir, "0.4.0")

    subprocess.run(
        [
            "python3",
            "scripts/write_stable_promotion.py",
            "--source-tag",
            "v0.4.0",
            "--release-dir",
            str(release_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    report = json.loads((output_dir / "stable-promotion.json").read_text(encoding="utf-8"))

    assert report["status"] == "passed"
    assert report["channel"] == "stable"
    assert report["version"] == "0.4.0"
    assert (output_dir / "stable-promotion.md").is_file()


def test_stable_promotion_fails_when_required_asset_missing(tmp_path):
    release_dir = tmp_path / "release"
    output_dir = tmp_path / "promotion"
    make_release_dir(release_dir, "0.4.0")

    (release_dir / "signature.json").unlink()

    result = subprocess.run(
        [
            "python3",
            "scripts/write_stable_promotion.py",
            "--source-tag",
            "v0.4.0",
            "--release-dir",
            str(release_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode != 0

    report = json.loads((output_dir / "stable-promotion.json").read_text(encoding="utf-8"))

    assert report["status"] == "failed"
