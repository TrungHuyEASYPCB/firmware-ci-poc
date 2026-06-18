#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install python3-yaml.", file=sys.stderr)
    sys.exit(1)


READY_STATES = {"ready", "available", "online", "enabled", "true", "yes"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_yaml(path):
    p = Path(path)
    if not p.is_file():
        fail(f"YAML file not found: {p}")

    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return data


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_devices(inventory):
    raw_devices = inventory.get("devices", inventory)

    if isinstance(raw_devices, dict):
        devices = []
        for key, value in raw_devices.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("id", key)
                devices.append(item)
        return devices

    if isinstance(raw_devices, list):
        return raw_devices

    fail("inventory/devices.yaml must contain a devices list or mapping")


def get_first(device, keys, default=""):
    for key in keys:
        if key in device and device[key] not in (None, ""):
            return device[key]
    return default


def normalize_roles(device):
    roles = []

    for key in ("roles", "role"):
        if key in device:
            roles.extend(as_list(device[key]))

    return [str(role) for role in roles if str(role)]


def normalize_runner_labels(device):
    labels = []

    for key in ("runner_labels", "runner_label", "labels"):
        if key in device:
            labels.extend(as_list(device[key]))

    labels = [str(label) for label in labels if str(label)]

    if not labels:
        labels = ["self-hosted", "ect1250"]

    if "self-hosted" not in labels:
        labels.insert(0, "self-hosted")

    return labels


def normalize_uart_port(device):
    value = get_first(
        device,
        [
            "uart_port",
            "serial_port",
            "port",
            "vcom0",
            "vcom",
            "tty",
        ],
        "",
    )

    if isinstance(value, dict):
        for key in ("path", "device", "port", "vcom0"):
            if key in value:
                return str(value[key])

    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(get_first(first, ["path", "device", "port"], ""))
        return str(first)

    ports = device.get("ports")
    if isinstance(ports, list) and ports:
        for port in ports:
            if isinstance(port, dict):
                label = str(port.get("label", port.get("type", ""))).lower()
                if "vcom" in label or "uart" in label:
                    return str(get_first(port, ["path", "device", "port"], ""))
            elif isinstance(port, str):
                return port

    return str(value)


def is_ready(device):
    if device.get("enabled") is False:
        return False

    status = str(device.get("status", device.get("state", "ready"))).lower()

    return status in READY_STATES


def build_matrix(inventory_path, profile, roles):
    inventory = load_yaml(inventory_path)
    devices = normalize_devices(inventory)

    selected_roles = {role.strip() for role in roles.split(",") if role.strip()}

    if not selected_roles:
        fail("No roles selected")

    include = []

    for device in devices:
        if not isinstance(device, dict):
            continue

        if not is_ready(device):
            continue

        device_roles = normalize_roles(device)

        if not device_roles:
            continue

        if not selected_roles.intersection(device_roles):
            continue

        device_id = str(get_first(device, ["id", "name", "device_id"], "unknown-device"))
        serial = str(get_first(device, ["serial", "serial_number", "device_serial"], ""))
        board = str(get_first(device, ["board", "target", "target_board"], "nrf52dk/nrf52832"))
        family = str(get_first(device, ["family", "soc_family"], "nrf52"))
        uart_port = normalize_uart_port(device)
        runner_labels = normalize_runner_labels(device)

        if not serial:
            fail(f"Device {device_id} is missing serial")

        include.append(
            {
                "device_id": device_id,
                "role": device_roles[0],
                "profile": profile,
                "serial": serial,
                "board": board,
                "family": family,
                "uart_port": uart_port,
                "runner_labels": runner_labels,
                "lock_id": device_id,
            }
        )

    if not include:
        fail(f"No ready devices found for roles: {sorted(selected_roles)}")

    return {"include": include}


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub Actions HIL matrix")
    parser.add_argument("--inventory", default="inventory/devices.yaml")
    parser.add_argument("--test-matrix", default="inventory/test_matrix.yaml")
    parser.add_argument("--profile", default=os.environ.get("TEST_PROFILE", "smoke"))
    parser.add_argument("--roles", default="preview")
    parser.add_argument("--output", choices=["json", "pretty"], default="json")
    parser.add_argument("--github-output", default="")
    args = parser.parse_args()

    # Load test matrix for validation only. The script stays backward compatible
    # with existing inventory formats.
    if Path(args.test_matrix).exists():
        load_yaml(args.test_matrix)

    matrix = build_matrix(args.inventory, args.profile, args.roles)

    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as f:
            f.write(f"matrix={json.dumps(matrix, separators=(',', ':'))}\n")

    if args.output == "pretty":
        print(json.dumps(matrix, indent=2))
    else:
        print(json.dumps(matrix, separators=(",", ":")))


if __name__ == "__main__":
    main()
