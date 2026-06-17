#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ALLOWED_CHANNELS = {"dev", "rc", "stable"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def run_command(command, env=None):
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )

    if result.returncode != 0:
        fail(f"Command failed: {' '.join(command)}\n{result.stdout}")

    return result.stdout.strip()


def read_json(path, label):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid {label}: {exc}")


def verify_source_tag_on_main(source_tag):
    run_command(["git", "fetch", "origin", "main", "--tags", "--force"])

    tag_commit = run_command(["git", "rev-parse", f"{source_tag}^{{}}"])
    main_commit = run_command(["git", "rev-parse", "origin/main"])

    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", tag_commit, "origin/main"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if result.returncode != 0:
        fail(f"Source tag {source_tag} is not contained in origin/main")

    return tag_commit, main_commit


def main():
    parser = argparse.ArgumentParser(description="Promote an existing release artifact")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--output-dir", default="promotion")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--channel", required=True, choices=sorted(ALLOWED_CHANNELS))
    parser.add_argument("--require-signature", action="store_true")
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.source_tag.startswith("v"):
        fail("source tag must start with v")

    version = args.source_tag[1:]

    manifest_path = release_dir / "manifest.json"
    checksums_path = release_dir / "checksums.sha256"
    signature_path = release_dir / "signature.json"

    if not manifest_path.is_file():
        fail("manifest.json not found in release directory")

    if not checksums_path.is_file():
        fail("checksums.sha256 not found in release directory")

    if args.require_signature and not signature_path.is_file():
        fail("signature.json is required for promotion but missing")

    tag_commit, main_commit = verify_source_tag_on_main(args.source_tag)

    env = os.environ.copy()
    if args.require_signature:
        env["REQUIRE_FIRMWARE_SIGNATURE"] = "1"

    run_command(
        [
            "python3",
            "scripts/verify_release.py",
            "--release-dir",
            str(release_dir),
            "--version",
            version,
            "--skip-git-commit-check",
        ],
        env=env,
    )

    manifest = read_json(manifest_path, "manifest.json")
    signature = read_json(signature_path, "signature.json") if signature_path.is_file() else {}

    firmware_hex = manifest.get("firmware_hex", "")
    firmware_sha256 = signature.get("firmware_sha256", "")

    promotion = {
        "schema": "firmware-ci-poc.promotion.v1",
        "promoted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_tag": args.source_tag,
        "source_version": version,
        "channel": args.channel,
        "source_commit": manifest.get("git_commit", ""),
        "tag_commit": tag_commit,
        "origin_main": main_commit,
        "board": manifest.get("board", ""),
        "firmware_hex": firmware_hex,
        "firmware_sha256": firmware_sha256,
        "signature_required": args.require_signature,
        "signature_present": signature_path.is_file(),
        "signature_algorithm": signature.get("algorithm", ""),
        "key_id": signature.get("key_id", ""),
        "policy_document": "docs/artifact-promotion-policy.md",
        "rollback_policy": "docs/release-rollback-policy.md",
    }

    promotion_name = f"promotion-{args.channel}-{args.source_tag}.json"
    promotion_path = output_dir / promotion_name
    promotion_path.write_text(json.dumps(promotion, indent=2) + "\n", encoding="utf-8")

    print("Promotion metadata written:")
    print(f"  {promotion_path}")


if __name__ == "__main__":
    main()
