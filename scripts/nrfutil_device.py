#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def nrfutil_executable():
    env_value = os.environ.get("NRFUTIL")
    if env_value:
        return env_value

    found = shutil.which("nrfutil")
    if found:
        return found

    local_bin = Path.home() / ".local" / "bin" / "nrfutil"
    if local_bin.exists() and os.access(local_bin, os.X_OK):
        return str(local_bin)

    raise FileNotFoundError(
        "nrfutil not found. Install nRF Util and ensure it is in PATH, "
        "or set NRFUTIL=/path/to/nrfutil"
    )


def run_nrfutil_device(args, check=False):
    exe = nrfutil_executable()
    command = [exe, "device", *args]

    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if check and completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"{completed.stdout}"
        )

    return completed.returncode, completed.stdout


def normalize_vcom(value):
    value = str(value).strip().upper()
    if value.startswith("VCOM"):
        return value
    return f"VCOM{value}"


def parse_device_list(output):
    devices = []
    current = None

    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            continue

        if re.fullmatch(r"\d+", stripped):
            current = {
                "serial": stripped,
                "product": "",
                "board_version": "",
                "traits": [],
                "uarts": [],
            }
            devices.append(current)
            continue

        if current is None:
            continue

        if stripped.startswith("Product"):
            current["product"] = stripped.replace("Product", "", 1).strip()
            continue

        if stripped.startswith("Board version"):
            current["board_version"] = stripped.replace("Board version", "", 1).strip()
            continue

        if stripped.startswith("Traits"):
            traits_text = stripped.replace("Traits", "", 1).strip()
            current["traits"] = [
                item.strip()
                for item in traits_text.split(",")
                if item.strip()
            ]
            continue

        port_match = re.search(r"(/dev/\S+),\s*vcom:\s*(\d+)", stripped)
        if port_match:
            port, vcom_index = port_match.groups()
            current["uarts"].append(
                {
                    "port": port,
                    "vcom": normalize_vcom(vcom_index),
                    "vcom_index": vcom_index,
                }
            )

    return devices


def list_devices():
    rc, output = run_nrfutil_device(["list"], check=False)
    if rc != 0:
        raise RuntimeError(f"nrfutil device list failed:\n{output}")
    return parse_device_list(output), output


def find_device(serial):
    devices, output = list_devices()
    for device in devices:
        if str(device.get("serial")) == str(serial):
            return device, output
    return None, output


def select_uart(serial, preferred_vcom="VCOM0"):
    preferred_vcom = normalize_vcom(preferred_vcom)
    device, output = find_device(serial)

    if not device:
        raise RuntimeError(
            f"Device serial {serial} not found in nrfutil device list:\n{output}"
        )

    uarts = device.get("uarts", [])
    if not uarts:
        raise RuntimeError(
            f"No UART ports found for serial {serial} in nrfutil device list:\n{output}"
        )

    for uart in uarts:
        if normalize_vcom(uart.get("vcom", "")) == preferred_vcom:
            return uart["port"]

    return uarts[0]["port"]


def main():
    devices, _ = list_devices()
    print(json.dumps(devices, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"nrfutil device helper failed: {exc}", file=sys.stderr)
        sys.exit(1)
