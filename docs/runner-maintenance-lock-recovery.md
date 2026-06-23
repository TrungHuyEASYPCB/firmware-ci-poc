# Runner maintenance and lock recovery

## Purpose

Runner maintenance checks whether the self-hosted runner is healthy before long HIL jobs.

This stage focuses on the local lab host:

~~~text
Host: ECT1250
Runner label: self-hosted, ect1250
Device lock directory: /tmp/firmware-ci-device-locks
~~~

## Checks

| Check | Purpose |
|---|---|
| disk space | Avoid build or artifact failures caused by full disk |
| docker command | Confirm Docker is available |
| nrfutil command | Confirm Nordic device CLI is available |
| nrfutil device list | Confirm device discovery command works |
| lock directory | Confirm device lock directory exists and is writable |
| stale lock scan | Report old lock files for operator review |

## Generated files

~~~text
hil-results/runner-maintenance.json
hil-results/runner-maintenance.md
~~~

## Safety

The default mode is read-only.

The script reports stale locks, but does not delete anything unless an explicit future maintenance mode is added.

## Recommended operator action

If stale lock files are reported and no HIL job is running, inspect:

~~~bash
ls -lah /tmp/firmware-ci-device-locks
ps aux | grep -Ei 'flash|pytest|west|nrfutil|with_device_lock' | grep -v grep
~~~

If needed, restart the runner service:

~~~bash
sudo systemctl restart actions.runner.TrungHuyEASYPCB-firmware-ci-poc.runner-lab-01.service
~~~
