#!/usr/bin/env python3
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed. Install with: sudo apt install -y python3-yaml")
    sys.exit(1)


DEVICES_FILE = Path("inventory/devices.yaml")
MATRIX_FILE = Path("inventory/test_matrix.yaml")

REQUIRED_DEVICE_FIELDS = {
    "role",
    "status",
    "vendor",
    "probe",
    "board",
    "soc",
    "serial",
    "uart",
}

VALID_DEVICE_STATUS = {
    "ready",
    "disabled",
}


def load_yaml(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_devices(devices):
    if not isinstance(devices, dict) or not devices:
        raise ValueError("inventory/devices.yaml must contain at least one device")

    ready_serials = {}
    ready_uarts = {}
    ready_roles = {}
    ready_profiles_by_role = {}

    for device_id, device in devices.items():
        if not isinstance(device, dict):
            raise ValueError(f"Device {device_id} must be a mapping")

        missing = REQUIRED_DEVICE_FIELDS - set(device)
        if missing:
            raise ValueError(f"Device {device_id} missing fields: {sorted(missing)}")

        status = str(device["status"])
        if status not in VALID_DEVICE_STATUS:
            raise ValueError(
                f"Device {device_id} has invalid status {status}. "
                f"Valid: {sorted(VALID_DEVICE_STATUS)}"
            )

        serial = str(device["serial"])
        uart = str(device["uart"])
        role = str(device["role"])

        if uart == "auto" and not device.get("preferred_vcom"):
            raise ValueError(f"Device {device_id} uses uart:auto but missing preferred_vcom")

        profiles = device.get("test_profiles", [])
        if profiles and not isinstance(profiles, list):
            raise ValueError(f"Device {device_id} test_profiles must be a list")

        if status == "ready":
            ready_roles.setdefault(role, []).append(device_id)
            ready_profiles_by_role.setdefault(role, set()).update(str(p) for p in profiles)

            if serial in ready_serials:
                raise ValueError(
                    f"Duplicate ready device serial {serial}: "
                    f"{ready_serials[serial]} and {device_id}"
                )

            if uart != "auto":
                if uart in ready_uarts:
                    raise ValueError(
                        f"Duplicate ready device UART {uart}: "
                        f"{ready_uarts[uart]} and {device_id}"
                    )
                ready_uarts[uart] = device_id

            ready_serials[serial] = device_id

    return ready_roles, ready_profiles_by_role


def validate_test_matrix(test_matrix, ready_roles, ready_profiles_by_role):
    if not isinstance(test_matrix, dict) or not test_matrix:
        raise ValueError("inventory/test_matrix.yaml must contain at least one matrix entry")

    enabled_count = 0

    for entry_id, entry in test_matrix.items():
        if not isinstance(entry, dict):
            raise ValueError(f"Matrix entry {entry_id} must be a mapping")

        enabled = bool(entry.get("enabled", False))
        device_role = str(entry.get("device_role", ""))
        test_profile = str(entry.get("test_profile", ""))

        if not device_role:
            raise ValueError(f"Matrix entry {entry_id} missing device_role")

        if not test_profile:
            raise ValueError(f"Matrix entry {entry_id} missing test_profile")

        if enabled:
            enabled_count += 1

            if device_role not in ready_roles:
                raise ValueError(
                    f"Matrix entry {entry_id} requires role {device_role}, "
                    f"but no ready device has that role"
                )

            supported_profiles = ready_profiles_by_role.get(device_role, set())
            if supported_profiles and test_profile not in supported_profiles:
                raise ValueError(
                    f"Matrix entry {entry_id} uses profile {test_profile}, "
                    f"but ready role {device_role} supports: {sorted(supported_profiles)}"
                )

    if enabled_count == 0:
        raise ValueError("At least one test matrix entry must be enabled")


def main():
    devices_doc = load_yaml(DEVICES_FILE)
    matrix_doc = load_yaml(MATRIX_FILE)

    devices = devices_doc.get("devices", {})
    test_matrix = matrix_doc.get("test_matrix", {})

    ready_roles, ready_profiles_by_role = validate_devices(devices)
    validate_test_matrix(test_matrix, ready_roles, ready_profiles_by_role)

    print("Inventory validation PASS")
    print(f"Ready roles: {', '.join(sorted(ready_roles))}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Inventory validation FAIL: {exc}")
        sys.exit(1)
