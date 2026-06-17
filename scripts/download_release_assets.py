#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def api_request(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(url)
    req.add_header("Accept", accept)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")

    with urllib.request.urlopen(req) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description="Download all assets from a GitHub Release")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--tag", required=True, help="release tag, for example v0.2.9")
    parser.add_argument("--output-dir", default="release")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()

    if not args.token:
        fail("GitHub token is required. Set GITHUB_TOKEN or pass --token")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    release_url = f"https://api.github.com/repos/{args.repo}/releases/tags/{args.tag}"
    release_data = json.loads(api_request(release_url, args.token).decode("utf-8"))

    assets = release_data.get("assets", [])
    if not assets:
        fail(f"No assets found for release tag {args.tag}")

    print(f"Downloading assets from {args.repo} release {args.tag}")

    for asset in assets:
        name = asset["name"]
        asset_url = asset["url"]
        target = output_dir / name

        print(f"Download: {name}")
        data = api_request(asset_url, args.token, accept="application/octet-stream")
        target.write_bytes(data)

    print(f"Downloaded {len(assets)} assets to {output_dir}")


if __name__ == "__main__":
    main()
