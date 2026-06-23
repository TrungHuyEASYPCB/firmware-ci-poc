#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_RELEASE_FILES = [
    "manifest.json",
    "checksums.sha256",
    "signature.json",
    "release-status.json",
    "build-info.json",
]


def read_json(path):
    p = Path(path)
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def normalize_version(value):
    value = str(value or "").strip()
    return value[1:] if value.startswith("v") else value


def add_check(checks, name, ok, detail):
    checks.append(
        {
            "name": name,
            "status": "passed" if ok else "failed",
            "detail": str(detail),
        }
    )


def write_markdown(report, path):
    icon = "✅" if report["status"] == "passed" else "❌"

    lines = [
        "# Stable promotion",
        "",
        f"Status: {icon} **{report['status']}**",
        "",
        "## Promotion",
        "",
        f"- Source tag: `{report['source_tag']}`",
        f"- Version: `{report['version']}`",
        f"- Channel: `{report['channel']}`",
        f"- Commit: `{report.get('commit', '')}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]

    for check in report["checks"]:
        check_icon = "✅" if check["status"] == "passed" else "❌"
        detail = str(check.get("detail", "")).replace("\n", " ")
        lines.append(f"| `{check['name']}` | {check_icon} `{check['status']}` | {detail} |")

    lines.extend(["", "## Release assets", ""])

    for asset in report["assets"]:
        lines.append(f"- `{asset}`")

    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate stable promotion metadata")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--channel", default="stable")
    parser.add_argument("--release-dir", default="release")
    parser.add_argument("--output-dir", default="promotion")
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_tag = args.source_tag
    version = normalize_version(source_tag)

    checks = []

    add_check(checks, "source_tag_present", bool(source_tag), source_tag)

    add_check(
        checks,
        "release_dir_present",
        release_dir.is_dir(),
        str(release_dir),
    )

    assets = []
    if release_dir.is_dir():
        assets = sorted(path.name for path in release_dir.iterdir() if path.is_file())

    for required in REQUIRED_RELEASE_FILES:
        add_check(
            checks,
            f"required_asset_{required}",
            (release_dir / required).is_file(),
            str(release_dir / required),
        )

    hex_assets = [name for name in assets if name.endswith(".hex")]
    archive_assets = [name for name in assets if name.endswith(".tar.gz")]

    add_check(checks, "firmware_hex_present", bool(hex_assets), ", ".join(hex_assets) or "missing .hex")
    add_check(checks, "firmware_archive_present", bool(archive_assets), ", ".join(archive_assets) or "missing .tar.gz")

    manifest = read_json(release_dir / "manifest.json")
    build_info = read_json(release_dir / "build-info.json")
    release_status = read_json(release_dir / "release-status.json")
    signature = read_json(release_dir / "signature.json")

    manifest_text = json.dumps(manifest, sort_keys=True)
    build_text = json.dumps(build_info, sort_keys=True)
    status_text = json.dumps(release_status, sort_keys=True)

    version_found = version in manifest_text or version in build_text or version in status_text

    add_check(
        checks,
        "version_found_in_metadata",
        version_found,
        f"version={version}",
    )

    signature_text = json.dumps(signature, sort_keys=True)
    add_check(
        checks,
        "signature_metadata_present",
        bool(signature) and "signature" in signature_text.lower(),
        "signature.json contains signature metadata",
    )

    commit = (
        str(build_info.get("commit", ""))
        or str(build_info.get("git_commit", ""))
        or str(manifest.get("commit", ""))
        or str(manifest.get("git_commit", ""))
    )

    failed = [check for check in checks if check["status"] != "passed"]
    status = "failed" if failed else "passed"

    report = {
        "schema": "firmware-ci-poc.stable-promotion.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "channel": args.channel,
        "source_tag": source_tag,
        "version": version,
        "commit": commit,
        "release_dir": str(release_dir),
        "assets": assets,
        "checks": checks,
    }

    json_path = output_dir / "stable-promotion.json"
    md_path = output_dir / "stable-promotion.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)

    print(f"Stable promotion status: {status}")
    print(f"Stable promotion JSON: {json_path}")
    print(f"Stable promotion Markdown: {md_path}")

    if status != "passed":
        for check in failed:
            print(f"FAILED: {check['name']}: {check['detail']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
