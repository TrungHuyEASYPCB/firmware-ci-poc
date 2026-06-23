# Release quality gate

## Purpose

Release quality gate verifies that firmware release publication is backed by a passing HIL report.

The gate reads:

~~~text
hil-results/hil-summary.json
~~~

If the HIL report is missing, failed, or mismatched with the release version, the release workflow must fail.

## Why this matters

A GitHub Release should not be published only because the build and package steps passed.

For this project, a valid release must also have:

| Requirement | Meaning |
|---|---|
| HIL status passed | Firmware was flashed and validated on hardware |
| Expected version matched | Device output matches the release version |
| HIL report present | Release decision is traceable |
| Gate report generated | Operator can audit why release passed or failed |

## Generated files

The gate writes:

~~~text
hil-results/release-gate.json
hil-results/release-gate.md
~~~

## Failure behavior

The release gate exits non-zero when release quality is not acceptable.

This prevents accidental release publication when HIL failed, was skipped, or produced incomplete evidence.
