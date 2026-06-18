# HIL report retention

## Purpose

HIL report retention creates readable summary reports for each hardware-in-the-loop validation run.

The goal is to avoid relying only on raw GitHub Actions logs.

## Generated reports

Each HIL run generates:

| File | Purpose |
|---|---|
| hil-summary.json | Machine-readable HIL result summary |
| hil-summary.md | Human-readable HIL result summary |

The reports are written to:

~~~text
hil-results/
~~~

## Input files

The report generator reads:

~~~text
hil-results/run_metadata.json
hil-results/pytest-junit.xml
~~~

If one of the files is missing, the report still gets generated with partial information.

## Report fields

The JSON report includes:

- HIL status
- Test counts
- Failure count
- Error count
- Skipped count
- Device ID
- Device role
- Board
- Serial
- UART port
- Expected firmware version
- Expected git commit
- Expected board
- GitHub workflow metadata when available

## Workflow integration

The report generator is used by:

~~~text
.github/workflows/hil-matrix.yml
.github/workflows/nightly-hil.yml
~~~

The report step runs with:

~~~text
if: always()
~~~

This means reports are generated even when HIL validation fails.

## Retention

Reports are uploaded as GitHub Actions artifacts together with raw HIL results.

Future stages can use these reports for dashboards, notifications, and release quality gates.
