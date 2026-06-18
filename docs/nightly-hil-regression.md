# Nightly HIL regression

## Purpose

Nightly HIL regression runs hardware-in-the-loop validation automatically on a schedule.

The workflow is designed to reuse the HIL matrix introduced in Stage 19.

## Current safe default

Because the current lab has one ready preview device, the scheduled workflow uses safe defaults:

| Field | Value |
|---|---|
| profile | smoke |
| roles | preview |
| max-parallel | 1 |

This keeps the nightly workflow safe while still proving the scheduled HIL path.

## Schedule

The workflow runs daily at:

~~~text
19:00 UTC
~~~

This is approximately:

~~~text
02:00 Vietnam time
~~~

## Manual run

The workflow can also be started manually from GitHub Actions:

~~~text
Actions → Nightly HIL Regression → Run workflow
~~~

Manual inputs:

| Input | Meaning |
|---|---|
| profile | smoke, regression, or release |
| roles | comma-separated roles, for example preview or preview,regression |

## Hardware locking

Every hardware job must use:

~~~text
scripts/with_device_lock.sh
~~~

This prevents concurrent jobs from flashing or validating the same device.

## Future scaling

When more devices are added to:

~~~text
inventory/devices.yaml
~~~

The workflow can be expanded by changing:

~~~text
roles
profile
max-parallel
~~~

No workflow rewrite should be required.
