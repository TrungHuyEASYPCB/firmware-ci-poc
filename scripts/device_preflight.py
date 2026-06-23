#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required.", file=sys.stderr)
    sys.exit(1)


READY_STATES = {"ready", "available", "online", "enabled", "true", "yes"}


def load_yaml(path):
    p = Path(path)

    if not p.is_file():
        return {}

    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def as_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def normalize_devices(inventory):
    raw_devices = inventory.get("devices", inventory)

    if isinstance(raw_devices, list):
        return raw_devices

    if isinstance(raw_devices, dict):
        devices = []
        for key, value in raw_devices.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("id", key)
                devices.append(item)
        return devices

    return []


def device_roles(device):
    roles = []

    for key in ("roles", "role"):
        if key in device:
            roles.extend(as_list(device[key]))

    return [str(role) for role in roles if str(role)]


def is_ready(device):
    if device.get("enabled") is False:
        return False

    state = str(device.get("status", device.get("state", "ready"))).lower()
    return state in READY_STATES


def get_first(device, keys, default=""):
    for key in keys:
        if key in device and device[key] not in (None, ""):
            return device[key]

    return default


def select_device(inventory_path, role, device_id):
    inventory = load_yaml(inventory_path)
    devices = normalize_devices(inventory)

    for device in devices:
        if not isinstance(device, dict):
            continue

        if device_id and str(device.get("id", "")) != device_id:
            continue

        if not is_ready(device):
            continue

        roles = device_roles(device)

        if role and role not in roles:
            continue

        return device

    return {}


def run_command(command):
    return subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def check_status(name, ok, detail):
    return {
        "name": name,
        "status": "passed" if ok else "failed",
        "detail": detail,
    }


def write_markdown(report, path):
    status_icon = "✅" if report["status"] == "passed" else "❌"

    lines = [
        "# Device preflight",
        "",
        f"Status: {status_icon} **{report['status']}**",
        "",
        "## Device",
        "",
        f"- Device ID: `{report.get('device_id', '')}`",
        f"- Role: `{report.get('role', '')}`",
        f"- Serial: `{report.get('serial', '')}`",
        f"- Board: `{report.get('board', '')}`",
        f"- Family: `{report.get('family', '')}`",
        f"- UART: `{report.get('uart_port', '')}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]

    for check in report["checks"]:
        icon = "✅" if check["status"] == "passed" else "❌"
        detail = str(check.get("detail", "")).replace("\n", " ")
        lines.append(f"| `{check['name']}` | {icon} `{check['status']}` | {detail} |")

    lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Check device health before HIL")
    parser.add_argument("--inventory", default="inventory/devices.yaml")
    parser.add_argument("--role", default=os.environ.get("DEVICE_ROLE", "preview"))
    parser.add_argument("--device-id", default=os.environ.get("DEVICE_ID", ""))
    parser.add_argument("--serial", default=os.environ.get("SERIAL", ""))
    parser.add_argument("--board", default=os.environ.get("BOARD", ""))
    parser.add_argument("--family", default=os.environ.get("FAMILY", ""))
    parser.add_argument("--uart-port", default=os.environ.get("UART_PORT", ""))
    parser.add_argument("--results-dir", default="hil-results")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    device = select_device(args.inventory, args.role, args.device_id)

    device_id = args.device_id or str(get_first(device, ["id", "name", "device_id"], ""))
    serial = args.serial or str(get_first(device, ["serial", "serial_number", "device_serial"], ""))
    board = args.board or str(get_first(device, ["board", "target", "target_board"], "nrf52dk/nrf52832"))
    family = args.family or str(get_first(device, ["family", "soc_family"], "nrf52"))
    uart_port = args.uart_port or str(get_first(device, ["uart_port", "serial_port", "port", "vcom0", "tty"], ""))

    checks = []

    checks.append(
        check_status(
            "inventory_device",
            bool(device or (device_id and serial)),
            f"device_id={device_id}, role={args.role}",
        )
    )

    nrfutil_path = shutil.which("nrfutil")
    checks.append(
        check_status(
            "nrfutil_command",
            bool(nrfutil_path),
            nrfutil_path or "nrfutil not found in PATH",
        )
    )

    nrfutil_output = ""

    if nrfutil_path:
        result = run_command(["nrfutil", "device", "list"])
        nrfutil_output = result.stdout.strip()

        serial_found = bool(serial and serial in nrfutil_output)

        checks.append(
            check_status(
                "nrfutil_device_serial",
                serial_found,
                f"serial={serial}, nrfutil_exit={result.returncode}",
            )
        )
    else:
        checks.append(
            check_status(
                "nrfutil_device_serial",
                False,
                "Skipped because nrfutil command was not found",
            )
        )

    checks.append(
        check_status(
            "uart_port",
            bool(uart_port and Path(uart_port).exists()),
            uart_port or "UART port is empty",
        )
    )

    checks.append(
        check_status(
            "board_metadata",
            bool(board and family),
            f"board={board}, family={family}",
        )
    )

    lock_dir = Path("/tmp/firmware-ci-device-locks")
    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_ok = lock_dir.is_dir()
    except OSError as exc:
        lock_ok = False
        lock_detail = str(exc)
    else:
        lock_detail = str(lock_dir)

    checks.append(
        check_status(
            "device_lock_dir",
            lock_ok,
            lock_detail,
        )
    )

    failed = [check for check in checks if check["status"] != "passed"]
    status = "failed" if failed else "passed"

    report = {
        "schema": "firmware-ci-poc.device-preflight.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "device_id": device_id,
        "role": args.role,
        "serial": serial,
        "board": board,
        "family": family,
        "uart_port": uart_port,
        "checks": checks,
        "nrfutil_output": nrfutil_output,
    }

    json_path = results_dir / "device-preflight.json"
    md_path = results_dir / "device-preflight.md"

    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, md_path)

    print(f"Device preflight status: {status}")
    print(f"Device preflight JSON: {json_path}")
    print(f"Device preflight Markdown: {md_path}")

    if status != "passed":
        for check in failed:
            print(f"FAILED: {check['name']}: {check['detail']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
