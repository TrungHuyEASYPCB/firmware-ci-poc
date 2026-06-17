# Artifact promotion policy

## Purpose

Artifact promotion separates firmware validation from firmware distribution.

A promoted firmware artifact must be an existing GitHub Release artifact that has already passed:

- Build
- Flash
- Pytest HIL validation
- Checksum verification
- Signature verification
- Release gate validation

Promotion must not rebuild firmware.

## Promotion channels

| Channel | Meaning |
|---|---|
| dev | Internal development candidate |
| rc | Release candidate |
| stable | Approved release for deployment |

## Promotion rule

Promotion is allowed only from an existing release tag:

~~~text
vX.Y.Z
~~~

The promotion workflow must:

1. Download assets from the source GitHub Release.
2. Verify `checksums.sha256`.
3. Verify `signature.json`.
4. Verify `manifest.json`.
5. Generate `promotion.json`.
6. Attach promotion metadata back to the source GitHub Release.

## No rebuild policy

Promotion must not execute:

~~~text
scripts/docker_build.sh
scripts/flash.sh
scripts/validate.sh
~~~

Promotion only verifies and labels already-built artifacts.

## Promotion metadata

Each promotion generates:

~~~text
promotion.json
~~~

The metadata records:

- Source tag
- Promotion channel
- Source commit
- Firmware artifact name
- Firmware SHA256
- Signature status
- Promotion timestamp
- Promotion policy document

## Stable promotion requirements

A release can be promoted to `stable` only when:

- Release workflow passed
- Firmware signature verification passed
- The source tag is contained in `main`
- Release environment approval was completed

## Rollback relationship

If a stable release is later deprecated or revoked, follow:

~~~text
docs/release-rollback-policy.md
~~~
