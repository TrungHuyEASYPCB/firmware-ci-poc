# Stable promotion automation

## Purpose

Stable promotion automation promotes an existing verified GitHub Release to the `stable` channel.

The promotion does not rebuild firmware. It validates an already published release and writes promotion metadata.

## Promotion source

A stable promotion uses an existing release tag, for example:

~~~text
v0.3.11
~~~

## Validation

Before promotion, the workflow verifies:

| Check | Purpose |
|---|---|
| source tag exists | Ensure the tag is valid |
| tag contained in main | Ensure release came from protected main flow |
| release assets downloaded | Ensure release artifacts are available |
| release artifact verification | Ensure checksums/signature/manifest are valid |
| promotion metadata generated | Ensure stable channel metadata is auditable |

## Generated files

~~~text
promotion/stable-promotion.json
promotion/stable-promotion.md
~~~

## GitHub Release assets

The workflow uploads promotion metadata back to the source GitHub Release.

This makes the promoted stable release traceable from the release page itself.

## Safety

Stable promotion is manual-only and should be run after:

1. GitHub Release workflow passed
2. HIL Matrix passed
3. Nightly HIL Regression passed
4. Operator decides the release is stable
