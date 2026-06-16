#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

from nrfutil_device import list_devices


INVENTORY_FILE = Path("inventory/devices.yaml")


def load_inventory():
    if yaml is None or not INVENTORY_FILE.exists():
        return {}

    with INVENTORY_FILE.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    detected_devices, raw_output = list_devices()
    inventory = load_inventory()
    inventory_devices = inventory.get("devices", {})

    discovered = []

    for detected in detected_devices:
        serial = str(detected.get("serial", ""))
        inventory_match = None
        inventory_id = None

        for device_id, device in inventory_devices.items():
            if str(device.get("serial", "")) == serial:
                inventory_match = device
                inventory_id = device_id
                break

        discovered.append(
            {
                "serial": serial,
                "product": detected.get("product", ""),
                "board_version": detected.get("board_version", ""),
                "traits": detected.get("traits", []),
                "uarts": detected.get("uarts", []),
                "inventory_id": inventory_id,
                "role": inventory_match.get("role") if inventory_match else None,
                "board": inventory_match.get("board") if inventory_match else None,
                "soc": inventory_match.get("soc") if inventory_match else None,
                "family": inventory_match.get("family") if inventory_match else None,
                "vendor": inventory_match.get("vendor") if inventory_match else None,
                "probe": inventory_match.get("probe") if inventory_match else None,
                "status": inventory_match.get("status") if inventory_match else "unknown",
            }
        )

    if args.json:
        print(json.dumps({"devices": discovered}, indent=2))
        return

    print("Discovered Nordic devices via nrfutil:")
    if not discovered:
        print("  No devices detected.")
        print(raw_output)
        return

    for dev in discovered:
        print(f"  serial: {dev['serial']}")
        print(f"    inventory_id: {dev['inventory_id'] or 'unknown'}")
        print(f"    role: {dev['role'] or 'unknown'}")
        print(f"    board: {dev['board'] or 'unknown'}")
        print(f"    soc: {dev['soc'] or 'unknown'}")
        print(f"    family: {dev['family'] or 'unknown'}")
        print(f"    product: {dev['product'] or 'unknown'}")
        print(f"    board_version: {dev['board_version'] or 'unknown'}")
        print(f"    traits: {', '.join(dev['traits']) if dev['traits'] else 'unknown'}")
        if dev["uarts"]:
            for uart in dev["uarts"]:
                print(f"    uart: {uart['port']} ({uart['vcom']})")
        else:
            print("    uart: not detected")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Device discovery failed: {exc}", file=sys.stderr)
        sys.exit(1)
