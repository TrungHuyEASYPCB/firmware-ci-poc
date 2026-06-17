#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


TAG_RE = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)$")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def run_git(args, check=False):
    result = subprocess.run(
        ["git", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    output = result.stdout.strip()

    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed:\n{output}")

    return result.returncode, output


def read_version_file(path):
    version_path = Path(path)

    if not version_path.is_file():
        fail(f"Version file not found: {version_path}")

    version = version_path.read_text(encoding="utf-8").strip()

    if not version:
        fail(f"Version file is empty: {version_path}")

    return version


def main():
    parser = argparse.ArgumentParser(description="Verify release gate before publishing")
    parser.add_argument("--tag-name", default=os.environ.get("GITHUB_REF_NAME", ""))
    parser.add_argument("--version-file", default="RELEASE_VERSION")
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument(
        "--skip-current-ref-check",
        action="store_true",
        help="Only for local development checks outside a tag checkout",
    )
    parser.add_argument(
        "--skip-main-check",
        action="store_true",
        help="Only for local development checks when origin/main is unavailable",
    )
    args = parser.parse_args()

    tag_name = args.tag_name.strip()

    if not tag_name:
        fail("Tag name is empty. Pass --tag-name or set GITHUB_REF_NAME")

    match = TAG_RE.match(tag_name)

    if not match:
        fail(f"Invalid release tag format: {tag_name}. Expected vX.Y.Z")

    tag_version = match.group("version")
    file_version = read_version_file(args.version_file)

    if file_version != tag_version:
        fail(
            f"Release version mismatch: tag {tag_name} expects {tag_version}, "
            f"but {args.version_file} contains {file_version}"
        )

    _, head_commit = run_git(["rev-parse", "HEAD"], check=True)

    if not args.skip_current_ref_check:
        _, tag_commit = run_git(["rev-parse", f"{tag_name}^{{}}"], check=True)

        if tag_commit != head_commit:
            fail(
                f"Current HEAD does not match tag {tag_name}: "
                f"HEAD={head_commit}, tag={tag_commit}"
            )

    if not args.skip_main_check:
        code, _ = run_git(["rev-parse", "--verify", args.main_ref])

        if code != 0:
            fail(f"Main ref not found: {args.main_ref}. Fetch main before running gate")

        code, output = run_git(["merge-base", "--is-ancestor", "HEAD", args.main_ref])

        if code != 0:
            fail(
                f"Release commit is not contained in {args.main_ref}. "
                f"Do not publish releases from non-main commits.\n{output}"
            )

    print("Release gate verification PASS")
    print(f"Tag: {tag_name}")
    print(f"Version: {tag_version}")
    print(f"HEAD: {head_commit}")
    print(f"Main ref: {args.main_ref}")


if __name__ == "__main__":
    main()
