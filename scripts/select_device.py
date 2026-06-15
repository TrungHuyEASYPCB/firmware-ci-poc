#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Install with: sudo apt install -y python3-yaml")
    sys.exit(1)


INVENTORY_FILE = Path("inventory/devices.yaml")


def run_command(cmd):
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return completed.returncode, completed.stdout
    except FileNotFoundError:
        return 127, f"Command not found: {cmd[0]}"


def parse_nrfjprog_com(output):
    result = {}

    for line in output.splitlines():
        line = line.strip()
        match = re.search(r"(\d+)\s+(\S*/dev/\S+|\S+)\s+(VCOM\d+)", line)
        if not match:
            continue

        serial, port, vcom = match.groups()
        result.setdefault(serial, []).append(
            {
                "port": port,
                "vcom": vcom,
            }
        )

    return result


def load_inventory():
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(f"Missing inventory file: {INVENTORY_FILE}")

    with INVENTORY_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    devices = data.get("devices", {})
    if not devices:
        raise ValueError("No devices found in inventory/devices.yaml")

    return devices


def select_device(devices, role=None, device_id=None):
    if device_id:
        if device_id not in devices:
            raise ValueError(f"Device not found: {device_id}")
        return device_id, devices[device_id]

    candidates = []

    for current_id, device in devices.items():
        if str(device.get("status", "")) != "ready":
            continue

        if role and str(device.get("role", "")) != role:
            continue

        candidates.append((current_id, device))

    if not candidates:
        raise ValueError(f"No ready device found for role: {role}")

    if len(candidates) > 1:
        names = ", ".join(item[0] for item in candidates)
        raise ValueError(
            f"Multiple ready devices match role {role}: {names}. "
            f"Use --device-id to select one explicitly."
        )

    return candidates[0]


def resolve_uart(device):
    uart = str(device.get("uart", ""))

    if uart and uart != "auto":
        return uart

    serial = str(device.get("serial", ""))
    preferred_vcom = str(device.get("preferred_vcom", "VCOM0"))

    rc, output = run_command(["nrfjprog", "--com"])
    if rc != 0:
        raise RuntimeError(f"Failed to run nrfjprog --com:\n{output}")

    com_map = parse_nrfjprog_com(output)
    ports = com_map.get(serial, [])

    if not ports:
        raise RuntimeError(f"No UART port detected for serial {serial}")

    for item in ports:
        if item["vcom"] == preferred_vcom:
            return item["port"]

    return ports[0]["port"]


def csv(value):
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value or "")


def build_env(device_id, device):
    uart_port = resolve_uart(device)

    return {
        "DEVICE_ID": device_id,
        "DEVICE_ROLE": str(device.get("role", "")),
        "DEVICE_STATUS": str(device.get("status", "")),
        "DEVICE_VENDOR": str(device.get("vendor", "")),
        "DEVICE_PROBE": str(device.get("probe", "")),
        "DEVICE_TYPE": str(device.get("device_type", "")),
        "DEVICE_SOC": str(device.get("soc", "")),
        "DEVICE_RUNNER": str(device.get("runner", "")),
        "DEVICE_LOCATION": str(device.get("location", "")),
        "DEVICE_CAPABILITIES": csv(device.get("capabilities", [])),
        "DEVICE_TEST_PROFILES": csv(device.get("test_profiles", [])),
        "BOARD": str(device.get("board", "")),
        "SERIAL": str(device.get("serial", "")),
        "UART_PORT": uart_port,
    }


def print_display(env):
    print(f"Device id: {env['DEVICE_ID']}")
    print(f"Role: {env['DEVICE_ROLE']}")
    print(f"Status: {env['DEVICE_STATUS']}")
    print(f"Vendor: {env['DEVICE_VENDOR']}")
    print(f"Probe: {env['DEVICE_PROBE']}")
    print(f"Type: {env['DEVICE_TYPE']}")
    print(f"Board: {env['BOARD']}")
    print(f"SoC: {env['DEVICE_SOC']}")
    print(f"Serial: {env['SERIAL']}")
    print(f"UART: {env['UART_PORT']}")
    print(f"Runner: {env['DEVICE_RUNNER']}")
    print(f"Location: {env['DEVICE_LOCATION']}")
    print(f"Capabilities: {env['DEVICE_CAPABILITIES']}")
    print(f"Test profiles: {env['DEVICE_TEST_PROFILES']}")


def print_shell(env):
    for key, value in env.items():
        escaped = str(value).replace("'", "'\"'\"'")
        print(f"export {key}='{escaped}'")


def write_github_env(env, path):
    with open(path, "a", encoding="utf-8") as f:
        for key, value in env.items():
            f.write(f"{key}={value}\n")


def write_env_file(env, path):
    with open(path, "w", encoding="utf-8") as f:
        for key, value in env.items():
            f.write(f"{key}={value}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", help="Select ready device by role")
    parser.add_argument("--device-id", help="Select exact device id")
    parser.add_argument("--shell", action="store_true", help="Print shell exports")
    parser.add_argument("--github-env", help="Append environment variables to GitHub env file")
    parser.add_argument("--env-file", help="Write environment variables to file")
    args = parser.parse_args()

    try:
        devices = load_inventory()
        device_id, device = select_device(devices, role=args.role, device_id=args.device_id)
        env = build_env(device_id, device)
    except Exception as exc:
        print(f"Device selection failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.github_env:
        write_github_env(env, args.github_env)
    elif args.env_file:
        write_env_file(env, args.env_file)
    elif args.shell:
        print_shell(env)
    else:
        print_display(env)


if __name__ == "__main__":
    main()
