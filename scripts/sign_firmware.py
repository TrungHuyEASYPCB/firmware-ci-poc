#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def sha256_file(path):
    digest = hashlib.sha256()

    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def run_command(command):
    result = subprocess.run(
        command,
        check=False,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        fail(f"Command failed: {' '.join(command)}\n{stderr}")

    return result.stdout


def key_id_from_public_key(public_key_path):
    public_key = Path(public_key_path).read_bytes()
    return hashlib.sha256(public_key).hexdigest()[:16]


def main():
    parser = argparse.ArgumentParser(description="Sign firmware artifact")
    parser.add_argument("--firmware", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--public-key", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--git-commit", required=True)
    args = parser.parse_args()

    firmware_path = Path(args.firmware)
    private_key_path = Path(args.private_key)
    public_key_path = Path(args.public_key)

    if not firmware_path.is_file():
        fail(f"Firmware file not found: {firmware_path}")

    if not private_key_path.is_file():
        fail(f"Private key not found: {private_key_path}")

    if not public_key_path.is_file():
        fail(f"Public key not found: {public_key_path}")

    signature = run_command([
        "openssl",
        "dgst",
        "-sha256",
        "-sign",
        str(private_key_path),
        str(firmware_path),
    ])

    payload = {
        "schema": "firmware-ci-poc.signature.v1",
        "signed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "algorithm": "RSA-SHA256-PKCS1v15",
        "key_id": key_id_from_public_key(public_key_path),
        "version": args.version,
        "board": args.board,
        "git_commit": args.git_commit,
        "firmware_hex": firmware_path.name,
        "firmware_sha256": sha256_file(firmware_path),
        "signature_base64": base64.b64encode(signature).decode("ascii"),
        "public_key": str(public_key_path),
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("Firmware signature written:")
    print(f"  {output_path}")


if __name__ == "__main__":
    main()
