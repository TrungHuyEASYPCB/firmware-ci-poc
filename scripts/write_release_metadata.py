#!/usr/bin/env python3
import argparse
import json
import os
import platform
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


def git_output(args):
    return run_command(["git", *args])


def docker_image_id(image_name):
    if not image_name:
        return ""

    return run_command([
        "docker",
        "image",
        "inspect",
        image_name,
        "--format",
        "{{.Id}}",
    ])


def docker_image_created(image_name):
    if not image_name:
        return ""

    return run_command([
        "docker",
        "image",
        "inspect",
        image_name,
        "--format",
        "{{.Created}}",
    ])


def read_file(path):
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return ""


def main():
    parser = argparse.ArgumentParser(description="Write firmware release provenance metadata")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--version", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--git-ref", required=True)
    parser.add_argument("--build-time", required=True)
    parser.add_argument("--hex-file", required=True)
    parser.add_argument("--archive", required=True)
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    ncs_version = os.environ.get("NCS_VERSION", "2.9.2")
    zephyr_sdk_version = os.environ.get("ZEPHYR_SDK_VERSION", "0.17.0")
    ncs_docker_image = os.environ.get("NCS_DOCKER_IMAGE", "firmware-ci-poc-ncs:2.9.2")
    ci_docker_image = os.environ.get("CI_DOCKER_IMAGE", "firmware-ci-poc-ci:latest")

    build_info = {
        "schema": "firmware-ci-poc.build-info.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": args.version,
        "board": args.board,
        "git": {
            "commit": args.git_commit,
            "ref": args.git_ref,
            "head": git_output(["rev-parse", "HEAD"]),
            "remote": git_output(["remote", "get-url", "origin"]),
        },
        "build": {
            "build_time": args.build_time,
            "host": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "runner": os.environ.get("DEVICE_RUNNER", ""),
            "test_profile": os.environ.get("TEST_PROFILE", ""),
        },
        "toolchain": {
            "ncs_version": ncs_version,
            "zephyr_sdk_version": zephyr_sdk_version,
            "zephyr_base": os.environ.get("ZEPHYR_BASE", ""),
            "ncs_docker_build": os.environ.get("NCS_DOCKER_BUILD", "0"),
        },
        "docker": {
            "ncs_image": ncs_docker_image,
            "ncs_image_id": docker_image_id(ncs_docker_image),
            "ncs_image_created": docker_image_created(ncs_docker_image),
            "ci_image": ci_docker_image,
            "ci_image_id": docker_image_id(ci_docker_image),
            "ci_image_created": docker_image_created(ci_docker_image),
        },
        "artifacts": {
            "firmware_hex": args.hex_file,
            "archive": args.archive,
            "manifest": "manifest.json",
            "package_env": "package.env",
            "release_notes": "release-notes.md",
            "checksums": "checksums.sha256",
            "build_info": "build-info.json",
            "sbom": "sbom.json",
        },
    }

    sbom = {
        "schema": "firmware-ci-poc.sbom.v1",
        "generated_at": build_info["generated_at"],
        "name": "firmware-ci-poc",
        "version": args.version,
        "board": args.board,
        "git_commit": args.git_commit,
        "components": [
            {
                "name": "firmware-ci-poc",
                "type": "application",
                "version": args.version,
                "source": git_output(["remote", "get-url", "origin"]),
                "commit": git_output(["rev-parse", "HEAD"]),
            },
            {
                "name": "nRF Connect SDK",
                "type": "sdk",
                "version": ncs_version,
                "source": "nrfconnect/sdk-nrf",
            },
            {
                "name": "Zephyr RTOS",
                "type": "rtos",
                "version": ncs_version,
                "source": "zephyrproject-rtos/zephyr via NCS manifest",
            },
            {
                "name": "Zephyr SDK",
                "type": "toolchain",
                "version": zephyr_sdk_version,
                "source": "zephyrproject-rtos/sdk-ng",
            },
            {
                "name": "nRF Util",
                "type": "programming-tool",
                "version": run_command(["nrfutil", "--version"]).splitlines()[0] if run_command(["nrfutil", "--version"]) else "",
                "source": "Nordic nRF Util",
            },
        ],
    }

    (release_dir / "build-info.json").write_text(
        json.dumps(build_info, indent=2) + "\n",
        encoding="utf-8",
    )

    (release_dir / "sbom.json").write_text(
        json.dumps(sbom, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Release metadata written:")
    print(f"  {release_dir / 'build-info.json'}")
    print(f"  {release_dir / 'sbom.json'}")


if __name__ == "__main__":
    main()
