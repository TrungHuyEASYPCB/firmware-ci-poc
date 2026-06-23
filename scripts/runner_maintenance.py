#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_command(command):
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def resolve_command(name, extra_candidates=None):
    candidates = [shutil.which(name)]

    if extra_candidates:
        candidates.extend(extra_candidates)

    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate

    return ""


def add_check(checks, name, ok, detail):
    checks.append(
        {
            "name": name,
            "status": "passed" if ok else "failed",
            "detail": str(detail),
        }
    )


def scan_lock_dir(lock_dir, stale_minutes):
    lock_path = Path(lock_dir)
    now = datetime.now(timezone.utc).timestamp()

    entries = []

    if not lock_path.exists():
        return entries

    for path in sorted(lock_path.glob("*")):
        try:
            stat = path.stat()
        except OSError:
            continue

        age_seconds = max(0, int(now - stat.st_mtime))
        entries.append(
            {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "age_seconds": age_seconds,
                "stale": age_seconds >= stale_minutes * 60,
            }
        )

    return entries


def write_markdown(report, path):
    icon = "✅" if report["status"] == "passed" else "❌"

    lines = [
        "# Runner maintenance",
        "",
        f"Status: {icon} **{report['status']}**",
        "",
        "## Environment",
        "",
        f"- Hostname: `{report.get('hostname', '')}`",
        f"- Lock directory: `{report.get('lock_dir', '')}`",
        f"- Stale threshold minutes: `{report.get('stale_minutes', '')}`",
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

    lines.extend(["", "## Lock files", ""])

    if report["lock_files"]:
        lines.append("| File | Age seconds | Size | Stale |")
        lines.append("|---|---:|---:|---|")
        for item in report["lock_files"]:
            stale = "yes" if item["stale"] else "no"
            lines.append(
                f"| `{item['name']}` | {item['age_seconds']} | {item['size']} | {stale} |"
            )
    else:
        lines.append("No lock files found.")

    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Check self-hosted runner maintenance state")
    parser.add_argument("--results-dir", default="hil-results")
    parser.add_argument("--lock-dir", default="/tmp/firmware-ci-device-locks")
    parser.add_argument("--min-free-gb", type=float, default=2.0)
    parser.add_argument("--stale-minutes", type=int, default=120)
    parser.add_argument("--warn-on-stale-locks", action="store_true")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    checks = []

    hostname = os.uname().nodename if hasattr(os, "uname") else ""

    disk = shutil.disk_usage(".")
    free_gb = disk.free / (1024**3)
    add_check(
        checks,
        "disk_free_space",
        free_gb >= args.min_free_gb,
        f"{free_gb:.2f} GiB free, minimum {args.min_free_gb:.2f} GiB",
    )

    docker_path = resolve_command("docker")
    add_check(
        checks,
        "docker_command",
        bool(docker_path),
        docker_path or "docker not found in PATH",
    )

    if docker_path:
        docker_result = run_command([docker_path, "--version"])
        add_check(
            checks,
            "docker_version",
            docker_result.returncode == 0,
            docker_result.stdout.strip(),
        )

    nrfutil_path = resolve_command(
        "nrfutil",
        [
            str(Path.home() / ".local" / "bin" / "nrfutil"),
            "/home/rabbit/.local/bin/nrfutil",
            "/usr/local/bin/nrfutil",
            "/usr/bin/nrfutil",
        ],
    )
    add_check(
        checks,
        "nrfutil_command",
        bool(nrfutil_path),
        nrfutil_path or "nrfutil not found",
    )

    if nrfutil_path:
        nrfutil_result = run_command([nrfutil_path, "device", "list"])
        add_check(
            checks,
            "nrfutil_device_list",
            nrfutil_result.returncode == 0,
            nrfutil_result.stdout.strip()[:500],
        )

    lock_dir = Path(args.lock_dir)

    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
        writable = os.access(lock_dir, os.W_OK)
    except OSError as exc:
        writable = False
        lock_detail = str(exc)
    else:
        lock_detail = str(lock_dir)

    add_check(
        checks,
        "lock_dir_writable",
        writable,
        lock_detail,
    )

    lock_files = scan_lock_dir(lock_dir, args.stale_minutes)
    stale_count = sum(1 for item in lock_files if item["stale"])

    if args.warn_on_stale_locks:
        stale_ok = stale_count == 0
    else:
        stale_ok = True

    add_check(
        checks,
        "stale_lock_scan",
        stale_ok,
        f"{stale_count} stale lock file(s), {len(lock_files)} total lock file(s)",
    )

    failed = [check for check in checks if check["status"] != "passed"]
    status = "failed" if failed else "passed"

    report = {
        "schema": "firmware-ci-poc.runner-maintenance.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "hostname": hostname,
        "lock_dir": str(lock_dir),
        "stale_minutes": args.stale_minutes,
        "checks": checks,
        "lock_files": lock_files,
    }

    json_path = results_dir / "runner-maintenance.json"
    md_path = results_dir / "runner-maintenance.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)

    print(f"Runner maintenance status: {status}")
    print(f"Runner maintenance JSON: {json_path}")
    print(f"Runner maintenance Markdown: {md_path}")

    if status != "passed":
        for check in failed:
            print(f"FAILED: {check['name']}: {check['detail']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
