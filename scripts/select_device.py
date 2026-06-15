#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


INVENTORY_PATH = Path("inventory/devices.yaml")


def clean_value(value: str) -> str:
    value = value.strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    return value


def parse_inventory(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Inventory file not found: {path}")

    devices = {}
    current_id = None
    in_devices = False

    for raw_line in path.read_text().splitlines():
        line = raw_line.rstrip()

        if not line.strip() or line.lstrip().startswith("#"):
            continue

        if line.strip() == "devices:":
            in_devices = True
            continue

        if not in_devices:
            continue

        if line.startswith("  ") and not line.startswith("    ") and line.strip().endswith(":"):
            current_id = line.strip()[:-1]
            devices[current_id] = {}
            continue

        if current_id and line.startswith("    ") and ":" in line:
            key, value = line.strip().split(":", 1)
            devices[current_id][key.strip()] = clean_value(value)

    return devices


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def select_device(devices, role=None, device_id=None):
    if device_id:
        if device_id not in devices:
            raise RuntimeError(f"Device id not found: {device_id}")
        device = devices[device_id]
        if device.get("status") != "ready":
            raise RuntimeError(f"Device {device_id} is not ready")
        return device_id, device

    role = role or "preview"

    for candidate_id, device in devices.items():
        if device.get("status") != "ready":
            continue
        if device.get("role") == role:
            return candidate_id, device

    raise RuntimeError(f"No ready device found for role: {role}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="preview")
    parser.add_argument("--device-id", default="")
    parser.add_argument("--github-env", default="")
    parser.add_argument("--env-file", default="")
    parser.add_argument("--shell", action="store_true")
    args = parser.parse_args()

    devices = parse_inventory(INVENTORY_PATH)
    device_id, device = select_device(
        devices,
        role=args.role,
        device_id=args.device_id or None,
    )

    env = {
        "DEVICE_ID": device_id,
        "DEVICE_ROLE": device.get("role", args.role),
        "BOARD": device["board"],
        "SERIAL": str(device["serial"]),
        "UART_PORT": device["uart"],
    }

    if args.github_env:
        with open(args.github_env, "a", encoding="utf-8") as f:
            for key, value in env.items():
                f.write(f"{key}={value}\n")

    if args.env_file:
        with open(args.env_file, "w", encoding="utf-8") as f:
            for key, value in env.items():
                f.write(f"export {key}={shell_quote(value)}\n")

    if args.shell:
        for key, value in env.items():
            print(f"export {key}={shell_quote(value)}")
        return

    print("Selected device:")
    for key, value in env.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
