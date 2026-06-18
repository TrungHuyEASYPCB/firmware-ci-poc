#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Publish HIL Markdown summary to GitHub Actions job summary")
    parser.add_argument("--results-dir", default="hil-results")
    parser.add_argument("--title", default="HIL summary")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    summary_md = results_dir / "hil-summary.md"

    github_step_summary = os.environ.get("GITHUB_STEP_SUMMARY")

    if github_step_summary:
        target = Path(github_step_summary)
    else:
        target = results_dir / "github-step-summary.md"

    target.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {args.title}",
        "",
    ]

    if summary_md.is_file():
        lines.append(summary_md.read_text(encoding="utf-8"))
    else:
        lines.extend(
            [
                "HIL summary file was not found.",
                "",
                f"Expected path: `{summary_md}`",
                "",
            ]
        )

    lines.append("")

    with target.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"HIL job summary published to: {target}")


if __name__ == "__main__":
    main()
