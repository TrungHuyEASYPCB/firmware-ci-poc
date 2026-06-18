# Multi-board HIL matrix

## Purpose

The HIL matrix allows firmware validation across multiple boards, roles, and test profiles.

Current project state:

- Runner host: ECT1250
- Current ready role: preview
- Current known device: nRF52 DK / nRF52832
- Current runner label: ect1250

The matrix design allows adding more boards later without rewriting the workflow.

## Device roles

| Role | Purpose |
|---|---|
| preview | Fast smoke validation on the primary preview device |
| regression | Longer validation on regression devices |
| nightly | Scheduled broader validation |
| release | Release-critical validation |

## Test profiles

| Profile | Purpose |
|---|---|
| smoke | Fast validation |
| regression | Deeper validation |
| release | Release validation |

## Inventory source

The HIL matrix is generated from:

~~~text
inventory/devices.yaml
inventory/test_matrix.yaml
~~~

## Matrix generation

Use:

~~~bash
python3 scripts/generate_hil_matrix.py --profile smoke --roles preview --output pretty
~~~

For GitHub Actions:

~~~bash
python3 scripts/generate_hil_matrix.py --profile smoke --roles preview --github-output "$GITHUB_OUTPUT"
~~~

## No direct hardware conflict

Every matrix item must run through:

~~~text
scripts/with_device_lock.sh
~~~

This prevents two jobs from flashing the same board at the same time.

## Current scaling model

Stage 19 introduces matrix support while keeping safe defaults:

- `max-parallel: 1`
- Uses self-hosted runner label `ect1250`
- Each matrix entry carries serial, board, role, profile, and UART port

Future runner farm stages can increase parallelism.
