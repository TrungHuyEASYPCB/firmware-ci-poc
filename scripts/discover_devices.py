#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


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


def parse_nrfjprog_ids(output):
    serials = []
    for line in output.splitlines():
        line = line.strip()
        if re.fullmatch(r"\d+", line):
            serials.append(line)
    return serials


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
    if yaml is None or not INVENTORY_FILE.exists():
        return {}

    with INVENTORY_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    ids_rc, ids_output = run_command(["nrfjprog", "--ids"])
    com_rc, com_output = run_command(["nrfjprog", "--com"])

    connected_serials = parse_nrfjprog_ids(ids_output)
    com_map = parse_nrfjprog_com(com_output)

    inventory = load_inventory()
    devices = inventory.get("devices", {})

    discovered = []

    for serial in sorted(set(connected_serials) | set(com_map.keys())):
        inventory_match = None
        inventory_id = None

        for device_id, device in devices.items():
            if str(device.get("serial", "")) == str(serial):
                inventory_match = device
                inventory_id = device_id
                break

        discovered.append(
            {
                "serial": serial,
                "connected": serial in connected_serials or serial in com_map,
                "uarts": com_map.get(serial, []),
                "inventory_id": inventory_id,
                "role": inventory_match.get("role") if inventory_match else None,
                "board": inventory_match.get("board") if inventory_match else None,
                "soc": inventory_match.get("soc") if inventory_match else None,
                "vendor": inventory_match.get("vendor") if inventory_match else None,
                "probe": inventory_match.get("probe") if inventory_match else None,
                "status": inventory_match.get("status") if inventory_match else "unknown",
            }
        )

    payload = {
        "nrfjprog_ids_rc": ids_rc,
        "nrfjprog_com_rc": com_rc,
        "devices": discovered,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print("Discovered devices:")
    if not discovered:
        print("  No devices detected.")
        return

    for dev in discovered:
        print(f"  serial: {dev['serial']}")
        print(f"    inventory_id: {dev['inventory_id'] or 'unknown'}")
        print(f"    role: {dev['role'] or 'unknown'}")
        print(f"    board: {dev['board'] or 'unknown'}")
        print(f"    soc: {dev['soc'] or 'unknown'}")
        print(f"    vendor: {dev['vendor'] or 'unknown'}")
        print(f"    probe: {dev['probe'] or 'unknown'}")
        print(f"    status: {dev['status']}")
        if dev["uarts"]:
            for uart in dev["uarts"]:
                print(f"    uart: {uart['port']} ({uart['vcom']})")
        else:
            print("    uart: not detected")


if __name__ == "__main__":
    main()
