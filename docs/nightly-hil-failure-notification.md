# Nightly HIL failure notification

## Purpose

Nightly HIL failure notification creates a GitHub Issue when scheduled HIL validation fails.

The goal is to make nightly hardware failures visible without requiring operators to manually check GitHub Actions every morning.

## Behavior

The notification script reads:

~~~text
hil-results/hil-summary.json
hil-results/hil-summary.md
~~~

If the HIL status is:

~~~text
passed
~~~

No issue is created.

If the HIL status is:

~~~text
failed
error
unknown
~~~

The workflow creates or updates a GitHub Issue.

## Issue strategy

The issue title format is:

~~~text
[Nightly HIL] <status> on <device_id>/<profile>
~~~

If an open issue with the same title already exists, the workflow adds a new comment instead of creating a duplicate issue.

## Workflow integration

The notification is integrated into:

~~~text
.github/workflows/nightly-hil.yml
~~~

The step runs after HIL summary generation.

## Permissions

The workflow requires:

~~~yaml
permissions:
  contents: read
  issues: write
~~~

## Future improvements

Future stages may add:

- Slack notification
- Email notification
- Auto-close issue when nightly HIL recovers
- Failure trend tracking
