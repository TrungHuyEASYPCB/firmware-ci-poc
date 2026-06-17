# Release rollback and hotfix policy

## Purpose

This document defines the rollback and hotfix policy for the firmware-ci-poc release pipeline.

The project follows this release flow:

~~~text
feature/* or ci/* -> PR -> develop -> release/* -> PR -> main -> tag -> GitHub Release
~~~

Direct pushes to `develop` and `main` are not allowed.

## Release states

| State | Meaning |
|---|---|
| active | Current valid release |
| superseded | Replaced by a newer release |
| deprecated | Release should not be used for new deployments |
| revoked | Release is invalid and must not be deployed |

## Rollback decision

Use rollback when:

- A newly released firmware has a critical runtime issue.
- The previous release is known-good.
- The hardware can safely be flashed back to a previous firmware image.

Use hotfix when:

- The issue is understood and can be fixed quickly.
- A rollback would reintroduce another known issue.
- The release needs a small patch on top of `main`.

## Rollback target

The preferred rollback target is normally the previous stable GitHub Release tag.

Example:

~~~text
Current release: v0.2.7
Rollback target: v0.2.6
~~~

Before rollback, verify the target tag:

~~~bash
git fetch origin --tags --force

git show --no-patch --decorate --oneline v0.2.6
git rev-parse v0.2.6^{}
~~~

Download and verify release assets:

~~~bash
sha256sum -c checksums.sha256
~~~

## Manual rollback procedure

1. Open the previous known-good GitHub Release.
2. Download the firmware HEX and `checksums.sha256`.
3. Verify checksums.
4. Flash the rollback firmware to the target device.
5. Run HIL smoke validation.
6. Mark the bad release as deprecated in release notes.
7. Create a hotfix issue if a code fix is required.

## Hotfix branch procedure

Create a hotfix branch from `main`:

~~~bash
git fetch origin --tags

git switch main
git pull --ff-only origin main

git switch -c hotfix/<version-or-issue>
~~~

After fixing:

~~~text
hotfix/* -> PR -> main -> tag -> GitHub Release
~~~

If the hotfix also needs to be kept in future development, merge or cherry-pick the fix back to `develop`.

## Release deprecation procedure

When a release is bad but must remain visible for audit:

1. Edit the GitHub Release title.
2. Prefix with `[DEPRECATED]`.
3. Add a warning at the top of release notes.
4. Point users to the rollback target or fixed release.
5. Keep artifacts for traceability unless they are unsafe to distribute.

Example release note prefix:

~~~text
[DEPRECATED] Do not deploy this firmware.
Use v0.2.6 or newer instead.
Reason: failed HIL regression on UART validation.
~~~

## Audit requirements

Each release should include:

~~~text
manifest.json
checksums.sha256
package.env
release-notes.md
build-info.json
sbom.json
release-status.json
firmware-*.hex
firmware-*.tar.gz
~~~

`release-status.json` records the release lifecycle and rollback guidance.
