#!/usr/bin/env python3
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def read_json(path):
    p = Path(path)
    if not p.is_file():
        return {}

    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_error": f"Invalid JSON: {p}"}


def parse_junit(path):
    p = Path(path)

    result = {
        "junit_present": p.is_file(),
        "tests": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "testcases": [],
    }

    if not p.is_file():
        result["status"] = "unknown"
        return result

    tree = ET.parse(p)
    root = tree.getroot()

    suites = []

    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = list(root.findall("testsuite"))

    for suite in suites:
        result["tests"] += int(suite.attrib.get("tests", 0))
        result["failures"] += int(suite.attrib.get("failures", 0))
        result["errors"] += int(suite.attrib.get("errors", 0))
        result["skipped"] += int(suite.attrib.get("skipped", 0))

        for case in suite.findall("testcase"):
            name = case.attrib.get("name", "")
            classname = case.attrib.get("classname", "")
            time_s = case.attrib.get("time", "")

            status = "passed"
            message = ""

            failure = case.find("failure")
            error = case.find("error")
            skipped = case.find("skipped")

            if failure is not None:
                status = "failed"
                message = failure.attrib.get("message", "")
            elif error is not None:
                status = "error"
                message = error.attrib.get("message", "")
            elif skipped is not None:
                status = "skipped"
                message = skipped.attrib.get("message", "")

            result["testcases"].append(
                {
                    "classname": classname,
                    "name": name,
                    "time": time_s,
                    "status": status,
                    "message": message,
                }
            )

    if result["tests"] == 0:
        result["status"] = "unknown"
    elif result["failures"] == 0 and result["errors"] == 0:
        result["status"] = "passed"
    else:
        result["status"] = "failed"

    return result


def env_metadata():
    keys = [
        "GITHUB_WORKFLOW",
        "GITHUB_RUN_ID",
        "GITHUB_RUN_NUMBER",
        "GITHUB_REF",
        "GITHUB_SHA",
        "GITHUB_ACTOR",
        "GITHUB_REPOSITORY",
        "DEVICE_ID",
        "DEVICE_ROLE",
        "TEST_PROFILE",
        "SERIAL",
        "BOARD",
        "FAMILY",
        "UART_PORT",
        "RELEASE_VERSION",
        "EXPECTED_VERSION",
        "EXPECTED_COMMIT",
        "EXPECTED_BOARD",
    ]

    return {key: os.environ.get(key, "") for key in keys if os.environ.get(key, "")}


def write_markdown(report, path):
    tests = report["tests"]
    status_icon = "✅" if report["status"] == "passed" else "❌" if report["status"] == "failed" else "⚠️"

    lines = [
        "# HIL summary",
        "",
        f"Status: {status_icon} **{report['status']}**",
        "",
        "## Device",
        "",
        f"- Device ID: `{report.get('device_id', '')}`",
        f"- Role: `{report.get('device_role', '')}`",
        f"- Profile: `{report.get('test_profile', '')}`",
        f"- Board: `{report.get('board', '')}`",
        f"- Serial: `{report.get('serial', '')}`",
        f"- UART: `{report.get('uart_port', '')}`",
        "",
        "## Firmware expectation",
        "",
        f"- Expected version: `{report.get('expected_version', '')}`",
        f"- Expected commit: `{report.get('expected_commit', '')}`",
        f"- Expected board: `{report.get('expected_board', '')}`",
        "",
        "## Test result",
        "",
        f"- Tests: `{tests}`",
        f"- Failures: `{report['failures']}`",
        f"- Errors: `{report['errors']}`",
        f"- Skipped: `{report['skipped']}`",
        "",
        "## Test cases",
        "",
        "| Status | Test | Time |",
        "|---|---|---|",
    ]

    for case in report.get("testcases", []):
        icon = {
            "passed": "✅",
            "failed": "❌",
            "error": "💥",
            "skipped": "⏭️",
        }.get(case.get("status"), "⚠️")

        test_name = f"{case.get('classname', '')}.{case.get('name', '')}".strip(".")
        lines.append(f"| {icon} {case.get('status')} | `{test_name}` | `{case.get('time', '')}` |")

    lines.extend(
        [
            "",
            "## GitHub Actions",
            "",
            f"- Workflow: `{report.get('github_workflow', '')}`",
            f"- Run ID: `{report.get('github_run_id', '')}`",
            f"- Run number: `{report.get('github_run_number', '')}`",
            f"- Ref: `{report.get('github_ref', '')}`",
            f"- SHA: `{report.get('github_sha', '')}`",
            "",
        ]
    )

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Write HIL JSON and Markdown summary reports")
    parser.add_argument("--results-dir", default="hil-results")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    metadata = read_json(results_dir / "run_metadata.json")
    junit = parse_junit(results_dir / "pytest-junit.xml")
    env = env_metadata()

    report = {
        "schema": "firmware-ci-poc.hil-summary.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": junit["status"],
        "tests": junit["tests"],
        "failures": junit["failures"],
        "errors": junit["errors"],
        "skipped": junit["skipped"],
        "junit_present": junit["junit_present"],
        "device_id": env.get("DEVICE_ID", metadata.get("device_id", "")),
        "device_role": env.get("DEVICE_ROLE", metadata.get("device_role", metadata.get("role", ""))),
        "test_profile": env.get("TEST_PROFILE", metadata.get("test_profile", metadata.get("profile", ""))),
        "serial": env.get("SERIAL", metadata.get("serial", "")),
        "board": env.get("BOARD", metadata.get("board", metadata.get("expected_board", ""))),
        "family": env.get("FAMILY", metadata.get("family", "")),
        "uart_port": env.get("UART_PORT", metadata.get("uart_port", "")),
        "expected_version": env.get("EXPECTED_VERSION", metadata.get("expected_version", "")),
        "expected_commit": env.get("EXPECTED_COMMIT", metadata.get("expected_commit", "")),
        "expected_board": env.get("EXPECTED_BOARD", metadata.get("expected_board", "")),
        "github_workflow": env.get("GITHUB_WORKFLOW", ""),
        "github_run_id": env.get("GITHUB_RUN_ID", ""),
        "github_run_number": env.get("GITHUB_RUN_NUMBER", ""),
        "github_ref": env.get("GITHUB_REF", ""),
        "github_sha": env.get("GITHUB_SHA", ""),
        "testcases": junit["testcases"],
        "metadata": metadata,
    }

    json_path = results_dir / "hil-summary.json"
    md_path = results_dir / "hil-summary.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)

    print(f"HIL JSON summary written: {json_path}")
    print(f"HIL Markdown summary written: {md_path}")
    print(f"HIL status: {report['status']}")

    if report["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
