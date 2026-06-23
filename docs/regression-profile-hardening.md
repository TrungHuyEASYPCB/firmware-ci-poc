# Regression profile hardening

## Purpose

Regression profile hardening defines how different HIL test profiles should behave.

The project currently supports:

| Profile | Purpose |
|---|---|
| smoke | Fast validation for PR and release sanity checks |
| regression | Deeper validation for nightly or pre-release confidence |
| release | Release-critical validation before publishing firmware |

## Why this matters

Before Stage 25, workflows accepted a profile name, but profile behavior was not centralized.

Stage 25 introduces a single profile configuration file:

~~~text
inventory/test_matrix.yaml
~~~

This lets workflows and scripts resolve profile behavior consistently.

## Profile configuration

Each profile can define:

| Field | Meaning |
|---|---|
| description | Human-readable purpose |
| pytest_markers | Pytest marker expression |
| uart_capture_seconds | UART capture duration |
| retry_count | Retry count for future resilient validation |
| expected_runtime | Human-readable expected duration |

## Current safe defaults

Because the lab currently has one preview board, all profiles still run safely on `dut-01`.

Future stages can make `regression` and `release` stricter without changing workflow structure.

## Workflow integration

The following workflows resolve test profiles before HIL validation:

~~~text
.github/workflows/hil-matrix.yml
.github/workflows/nightly-hil.yml
~~~

## Validation

Invalid profiles fail early before build or flash.
