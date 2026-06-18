# HIL job summary publishing

## Purpose

HIL job summary publishing makes hardware-in-the-loop results visible directly in GitHub Actions.

Stage 21 stores reports as artifacts:

~~~text
hil-summary.json
hil-summary.md
~~~

Stage 22 publishes the Markdown report to:

~~~text
GitHub Actions Job Summary
~~~

This lets reviewers inspect HIL results without downloading artifacts.

## Workflows

The job summary is published from:

~~~text
.github/workflows/hil-matrix.yml
.github/workflows/nightly-hil.yml
~~~

## Behavior

The summary publishing step runs with:

~~~text
if: always()
~~~

This means a summary is still published when HIL validation fails.

## Input

The publisher reads:

~~~text
hil-results/hil-summary.md
~~~

If the file is missing, it writes a short fallback message instead of failing the workflow.

## Retention model

Stage 22 does not replace artifact retention.

The workflow keeps uploading:

~~~text
hil-results/**
~~~

The job summary is only an easier visibility layer.
