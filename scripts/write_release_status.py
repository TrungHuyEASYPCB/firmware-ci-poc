#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_command(command):
    try:
        result = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except FileNotFoundError:
        return ""


def discover_previous_release(current_version):
    tags = run_command(["git", "tag", "--list", "v[0-9]*", "--sort=-v:refname"])
    current_tag = f"v{current_version}"

    for tag in tags.splitlines():
        tag = tag.strip()
        if tag and tag != current_tag:
            return tag

    return ""


def main():
    parser = argparse.ArgumentParser(description="Write release rollback status metadata")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--version", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--lifecycle", default="active")
    parser.add_argument("--rollback-target", default="")
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    rollback_target = args.rollback_target.strip() or discover_previous_release(args.version)

    release_status = {
        "schema": "firmware-ci-poc.release-status.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": args.version,
        "tag": f"v{args.version}",
        "git_commit": args.git_commit,
        "board": args.board,
        "lifecycle": args.lifecycle,
        "rollback": {
            "supported": True,
            "preferred_target": rollback_target,
            "policy_document": "docs/release-rollback-policy.md",
            "required_validation": [
                "sha256 checksum verification",
                "flash validation",
                "pytest HIL smoke validation"
            ]
        },
        "hotfix": {
            "branch_pattern": "hotfix/*",
            "base_branch": "main",
            "merge_back_to_develop": True
        },
        "deprecation": {
            "method": "edit GitHub Release title and release-notes.md",
            "title_prefix": "[DEPRECATED]",
            "keep_artifacts_for_audit": True
        }
    }

    output_path = release_dir / "release-status.json"
    output_path.write_text(json.dumps(release_status, indent=2) + "\n", encoding="utf-8")

    print("Release status written:")
    print(f"  {output_path}")


if __name__ == "__main__":
    main()
