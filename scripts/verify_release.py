#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_expected_version():
    if os.environ.get("RELEASE_VERSION"):
        return os.environ["RELEASE_VERSION"].strip()

    version_file = Path("RELEASE_VERSION")
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()

    return ""


def git_short_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    return ""


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_checksums(path):
    entries = {}

    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split(None, 1)
        if len(parts) != 2:
            fail(f"Invalid checksum line {line_no}: {raw_line}")

        checksum, filename = parts
        filename = filename.strip().lstrip("*")

        if len(checksum) != 64:
            fail(f"Invalid sha256 length at line {line_no}: {checksum}")

        entries[filename] = checksum

    return entries


def verify_checksum_entries(release_dir, checksums):
    if not checksums:
        fail("checksums.sha256 has no entries")

    for filename, expected_hash in checksums.items():
        path = release_dir / filename

        if not path.exists():
            fail(f"Checksum entry points to missing file: {filename}")

        actual_hash = sha256_file(path)
        if actual_hash != expected_hash:
            fail(
                f"Checksum mismatch for {filename}: "
                f"expected {expected_hash}, got {actual_hash}"
            )

        print(f"Checksum OK: {filename}")


def main():
    parser = argparse.ArgumentParser(description="Verify release artifacts")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--version", default="")
    parser.add_argument("--board", default=os.environ.get("BOARD", "nrf52dk/nrf52832"))
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    if not release_dir.is_dir():
        fail(f"Release directory not found: {release_dir}")

    manifest_path = release_dir / "manifest.json"
    checksums_path = release_dir / "checksums.sha256"
    package_env_path = release_dir / "package.env"
    release_notes_path = release_dir / "release-notes.md"

    required_files = [
        manifest_path,
        checksums_path,
        package_env_path,
        release_notes_path,
    ]

    for path in required_files:
        if not path.is_file():
            fail(f"Required release file missing: {path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid manifest.json: {exc}")

    expected_version = args.version.strip() or read_expected_version()
    if not expected_version:
        fail("Expected version is empty. Set RELEASE_VERSION or pass --version")

    manifest_version = str(manifest.get("version", ""))
    if manifest_version != expected_version:
        fail(f"Manifest version mismatch: expected {expected_version}, got {manifest_version}")

    manifest_board = str(manifest.get("board", ""))
    if manifest_board != args.board:
        fail(f"Manifest board mismatch: expected {args.board}, got {manifest_board}")

    manifest_commit = str(manifest.get("git_commit", ""))
    if not manifest_commit:
        fail("manifest.json missing git_commit")

    current_commit = git_short_commit()
    if current_commit and manifest_commit != current_commit:
        fail(f"Manifest git_commit mismatch: expected {current_commit}, got {manifest_commit}")

    hex_files = sorted(release_dir.glob(f"firmware-{expected_version}-*.hex"))
    tar_files = sorted(release_dir.glob(f"firmware-{expected_version}-*.tar.gz"))

    if not hex_files:
        fail(f"No firmware hex artifact found for version {expected_version}")

    if not tar_files:
        fail(f"No firmware tar.gz artifact found for version {expected_version}")

    checksums = parse_checksums(checksums_path)
    verify_checksum_entries(release_dir, checksums)

    expected_assets = {
        hex_files[0].name,
        tar_files[0].name,
        "manifest.json",
        "package.env",
        "release-notes.md",
    }

    missing_checksum_entries = sorted(expected_assets - set(checksums.keys()))
    if missing_checksum_entries:
        fail(
            "Missing checksum entries for release assets: "
            + ", ".join(missing_checksum_entries)
        )

    print("")
    print("Release artifact verification PASS")
    print(f"Version: {expected_version}")
    print(f"Board: {manifest_board}")
    print(f"Commit: {manifest_commit}")
    print(f"HEX: {hex_files[0].name}")
    print(f"Archive: {tar_files[0].name}")


if __name__ == "__main__":
    main()
