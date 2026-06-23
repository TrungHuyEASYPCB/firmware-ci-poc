#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PASS_VALUES = {"pass", "passed", "success", "ok"}


def read_json(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Missing required file: {p}")

    return json.loads(p.read_text(encoding="utf-8"))


def find_first(data, keys):
    if not isinstance(data, dict):
        return ""

    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value)

    for value in data.values():
        if isinstance(value, dict):
            found = find_first(value, keys)
            if found:
                return found

    return ""


def normalize_version(value):
    value = str(value or "").strip()
    return value[1:] if value.startswith("v") else value


def add_check(checks, name, ok, detail):
    checks.append(
        {
            "name": name,
            "status": "passed" if ok else "failed",
            "detail": detail,
        }
    )


def write_markdown(report, path):
    icon = "✅" if report["status"] == "passed" else "❌"

    lines = [
        "# Release quality gate",
        "",
        f"Status: {icon} **{report['status']}**",
        "",
        "## Release",
        "",
        f"- Expected version: `{report.get('expected_version', '')}`",
        f"- Reported version: `{report.get('reported_version', '')}`",
        f"- HIL status: `{report.get('hil_status', '')}`",
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

    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Verify release quality gate from HIL reports")
    parser.add_argument("--results-dir", default="hil-results")
    parser.add_argument("--version", default="")
    parser.add_argument("--summary-file", default="")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    summary_path = Path(args.summary_file) if args.summary_file else results_dir / "hil-summary.json"

    checks = []
    summary = {}

    try:
        summary = read_json(summary_path)
        add_check(checks, "hil_summary_present", True, str(summary_path))
    except Exception as exc:
        add_check(checks, "hil_summary_present", False, str(exc))

    hil_status = find_first(summary, ["status", "result", "hil_status"])
    status_ok = hil_status.lower() in PASS_VALUES
    add_check(checks, "hil_status_passed", status_ok, hil_status or "missing status")

    expected_version = normalize_version(args.version)
    reported_version = normalize_version(
        find_first(
            summary,
            [
                "firmware_version",
                "release_version",
                "expected_version",
                "version",
                "reported_version",
            ],
        )
    )

    if expected_version:
        if reported_version:
            version_ok = expected_version == reported_version
            detail = f"expected={expected_version}, reported={reported_version}"
        else:
            version_ok = False
            detail = f"expected={expected_version}, reported version missing"
    else:
        version_ok = True
        detail = "version check skipped"

    add_check(checks, "release_version_matched", version_ok, detail)

    failed = [check for check in checks if check["status"] != "passed"]
    gate_status = "failed" if failed else "passed"

    report = {
        "schema": "firmware-ci-poc.release-gate.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": gate_status,
        "expected_version": expected_version,
        "reported_version": reported_version,
        "hil_status": hil_status,
        "summary_file": str(summary_path),
        "checks": checks,
    }

    results_dir.mkdir(parents=True, exist_ok=True)

    json_path = results_dir / "release-gate.json"
    md_path = results_dir / "release-gate.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)

    print(f"Release gate status: {gate_status}")
    print(f"Release gate JSON: {json_path}")
    print(f"Release gate Markdown: {md_path}")

    if gate_status != "passed":
        for check in failed:
            print(f"FAILED: {check['name']}: {check['detail']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
