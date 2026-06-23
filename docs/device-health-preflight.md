# Device health preflight

## Purpose

Device health preflight checks whether the hardware lab is ready before running build, flash, or HIL validation.

This prevents unclear failures such as:

~~~text
Device serial 1050325823 not found in nrfutil device list
~~~

## Checks

The preflight script verifies:

| Check | Purpose |
|---|---|
| inventory device | Confirm selected role/device exists |
| nrfutil command | Confirm nrfutil is installed and available |
| nrfutil device list | Confirm the expected serial is connected |
| UART port | Confirm the expected UART path exists |
| board metadata | Confirm board/family fields are available |
| lock directory | Confirm device lock path can be prepared |

## Generated files

The script writes:

~~~text
hil-results/device-preflight.json
hil-results/device-preflight.md
~~~

## Workflows

Device preflight is used by:

~~~text
.github/workflows/hil-matrix.yml
.github/workflows/nightly-hil.yml
~~~

## Failure behavior

If preflight fails, the workflow stops before flashing.

This makes hardware issues visible early and avoids wasting build/HIL time.

## Current device

| Field | Value |
|---|---|
| Device ID | dut-01 |
| Role | preview |
| Serial | 1050325823 |
| Board | nrf52dk/nrf52832 |
| UART | /dev/ttyACM0 |
