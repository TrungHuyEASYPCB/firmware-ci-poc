#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def read_json(path):
    p = Path(path)

    if not p.is_file():
        return {}

    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON file {p}: {exc}")


def read_text(path):
    p = Path(path)

    if not p.is_file():
        return ""

    return p.read_text(encoding="utf-8")


def github_api(method, url, token, payload=None):
    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    if payload is not None:
        req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as response:
        raw = response.read().decode("utf-8")

    if not raw:
        return {}

    return json.loads(raw)


def github_run_url():
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    if repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"

    return ""


def issue_title(report):
    status = report.get("status", "unknown")
    device_id = report.get("device_id", "unknown-device")
    profile = report.get("test_profile", "unknown-profile")

    return f"[Nightly HIL] {status} on {device_id}/{profile}"


def issue_body(report, summary_md):
    run_url = github_run_url()

    lines = [
        "Nightly HIL validation did not pass.",
        "",
        "## Failure context",
        "",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Device ID: `{report.get('device_id', '')}`",
        f"- Role: `{report.get('device_role', '')}`",
        f"- Profile: `{report.get('test_profile', '')}`",
        f"- Board: `{report.get('board', '')}`",
        f"- Serial: `{report.get('serial', '')}`",
        f"- UART: `{report.get('uart_port', '')}`",
        f"- Expected version: `{report.get('expected_version', '')}`",
        f"- Expected commit: `{report.get('expected_commit', '')}`",
        "",
    ]

    if run_url:
        lines.extend(
            [
                "## GitHub Actions run",
                "",
                run_url,
                "",
            ]
        )

    lines.extend(
        [
            "## HIL summary",
            "",
            summary_md if summary_md else "No Markdown summary was available.",
            "",
        ]
    )

    return "\n".join(lines)


def find_existing_issue(repo, token, title):
    encoded_state = urllib.parse.urlencode({"state": "open", "per_page": "100"})
    url = f"https://api.github.com/repos/{repo}/issues?{encoded_state}"

    issues = github_api("GET", url, token)

    for issue in issues:
        if "pull_request" in issue:
            continue

        if issue.get("title") == title:
            return issue

    return None


def main():
    parser = argparse.ArgumentParser(description="Create or update GitHub Issue when HIL fails")
    parser.add_argument("--results-dir", default="hil-results")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    report = read_json(results_dir / "hil-summary.json")
    summary_md = read_text(results_dir / "hil-summary.md")

    status = report.get("status", "unknown")

    if status == "passed":
        print("HIL status passed. No issue notification needed.")
        return

    title = issue_title(report)
    body = issue_body(report, summary_md)

    if args.dry_run:
        print("DRY RUN: would notify GitHub Issue")
        print(f"Title: {title}")
        print("")
        print(body)
        return

    if not args.repo:
        fail("GitHub repository is required. Set GITHUB_REPOSITORY or pass --repo")

    if not args.token:
        fail("GitHub token is required. Set GITHUB_TOKEN or pass --token")

    existing = find_existing_issue(args.repo, args.token, title)

    if existing:
        number = existing["number"]
        comment_url = f"https://api.github.com/repos/{args.repo}/issues/{number}/comments"

        github_api(
            "POST",
            comment_url,
            args.token,
            {
                "body": body,
            },
        )

        print(f"Updated existing issue #{number}: {title}")
        return

    issue_url = f"https://api.github.com/repos/{args.repo}/issues"

    created = github_api(
        "POST",
        issue_url,
        args.token,
        {
            "title": title,
            "body": body,
        },
    )

    print(f"Created issue #{created.get('number')}: {title}")


if __name__ == "__main__":
    main()
