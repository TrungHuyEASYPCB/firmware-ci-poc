# Firmware CI/CD Operator Runbook

## Project

| Field | Value |
|---|---|
| Project | firmware-ci-poc |
| Host | ECT1250 |
| User | rabbit |
| Local repo | ~/Trung/firmware-ci-poc |
| Remote | TrungHuyEASYPCB/firmware-ci-poc |
| Runner | self-hosted, ect1250 |
| Device | dut-01 |
| Board | nrf52dk/nrf52832 |
| Serial | 1050325823 |
| UART | /dev/ttyACM0 |

## Branch policy

Do not push directly to `develop` or `main`.

Use this flow:

~~~text
feature/* or ci/*
  → Pull Request
  → develop
  → release/*
  → Pull Request
  → main
  → tag
  → GitHub Release
  → Stable Promotion
~~~

## Standard terminal setup

Run this before local validation:

~~~bash
cd ~/Trung/firmware-ci-poc

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/.local/bin
hash -r
~~~

## Normal development workflow

~~~bash
git fetch origin --tags --force

git switch develop
git pull --ff-only origin develop

git switch -c ci/<stage-name>
~~~

After changes:

~~~bash
./scripts/lint.sh
./scripts/docker_ci.sh

git add <changed-files>
git commit -m "ci: describe change"
git push -u origin ci/<stage-name>
~~~

Create PR:

~~~text
base: develop
compare: ci/<stage-name>
~~~

## Release workflow

After the feature PR is merged into `develop`:

~~~bash
git fetch origin --tags --force

git switch develop
git pull --ff-only origin develop

NEXT_VERSION="0.x.y"

git switch -c "release/${NEXT_VERSION}"
echo "$NEXT_VERSION" > RELEASE_VERSION

git add RELEASE_VERSION
git commit -m "release: prepare v${NEXT_VERSION}"
~~~

Run local validation:

~~~bash
rm -rf build release hil-results promotion .pytest_cache
find . -type d -name "__pycache__" -prune -exec rm -rf {} +

DEVICE_ENV="$(python3 scripts/select_device.py --role preview --shell)" || exit 1
eval "$DEVICE_ENV"

export TEST_PROFILE=regression
export RELEASE_VERSION="$NEXT_VERSION"
export FIRMWARE_VERSION="$NEXT_VERSION"
export EXPECTED_VERSION="$NEXT_VERSION"
export SIGNING_KEY_PATH=".secrets/firmware-signing-private.pem"
export REQUIRE_FIRMWARE_SIGNATURE=1

python3 scripts/runner_maintenance.py --results-dir hil-results && \
python3 scripts/validate_inventory.py && \
python3 scripts/resolve_test_profile.py --profile "$TEST_PROFILE" --output pretty && \
python3 scripts/device_preflight.py --results-dir hil-results && \
./scripts/docker_ci.sh && \
./scripts/docker_build.sh && \
./scripts/with_device_lock.sh bash -lc './scripts/flash.sh && ./scripts/validate.sh' && \
python3 scripts/write_hil_report.py --results-dir hil-results && \
python3 scripts/verify_release_gate.py --results-dir hil-results --version "$NEXT_VERSION" && \
python3 scripts/publish_hil_summary.py --results-dir hil-results --title "Local HIL summary" && \
python3 scripts/notify_hil_failure.py --results-dir hil-results --dry-run && \
./scripts/package.sh && \
python3 scripts/verify_release.py --version "$NEXT_VERSION"
~~~

Push release branch:

~~~bash
git push -u origin release/<version>
~~~

Create PR:

~~~text
base: main
compare: release/<version>
~~~

After PR passes and merges into `main`:

~~~bash
git fetch origin --tags --force

git switch main
git pull --ff-only origin main

cat RELEASE_VERSION

git tag -a v<version> -m "Release v<version>"
git push origin v<version>
~~~

Verify tag:

~~~bash
git show --no-patch --decorate --oneline v<version>
git show v<version>:RELEASE_VERSION

git merge-base --is-ancestor v<version>^{} origin/main && \
  echo "OK: tag is contained in origin/main" || \
  echo "ERROR: tag is NOT contained in origin/main"
~~~

## GitHub Release approval

Go to:

~~~text
Actions → GitHub Release → run for v<version>
~~~

Approve:

~~~text
Review deployments → Approve and deploy
~~~

Expected key steps:

~~~text
Validate release gate
Runner maintenance check
Device preflight
Build firmware
Flash and validate HIL
Generate HIL summary report
Verify release quality gate
Package release
Verify release assets
Publish GitHub Release
~~~

Expected final messages:

~~~text
Release gate status: passed
Signature OK: signature.json
Release artifact verification PASS
Version: <version>
~~~

## Manual HIL Matrix test

Go to:

~~~text
Actions → HIL Matrix → Run workflow
~~~

Use:

~~~text
Use workflow from: Tag v<version>
profile: regression
roles: preview
~~~

Expected steps:

~~~text
Runner maintenance check
Resolve test profile
Device preflight
Static analysis
Build firmware
Flash and validate HIL
Generate HIL summary report
Publish HIL job summary
Upload HIL results
~~~

## Manual Nightly HIL Regression test

Go to:

~~~text
Actions → Nightly HIL Regression → Run workflow
~~~

Use:

~~~text
Use workflow from: Tag v<version>
profile: regression
roles: preview
~~~

Expected notification behavior when HIL passes:

~~~text
HIL status passed. No issue notification needed.
~~~

## Stable promotion

After GitHub Release and HIL checks pass:

~~~text
Actions → Stable Promotion → Run workflow
~~~

Use:

~~~text
Use workflow from: main
source_tag: v<version>
channel: stable
~~~

Important: `source_tag` must include the `v` prefix.

Correct:

~~~text
v0.4.0
~~~

Incorrect:

~~~text
0.4.0
~~~

Expected steps:

~~~text
Validate source tag
Download release assets
Verify release assets
Generate stable promotion metadata
Upload promotion metadata to release
Upload promotion artifact
~~~

After pass, the GitHub Release should include:

~~~text
stable-promotion.json
stable-promotion.md
~~~

## Common troubleshooting

### nrfutil not found

Symptom:

~~~text
nrfutil not found in PATH
~~~

Check:

~~~bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$HOME/.local/bin
hash -r

which nrfutil
nrfutil device list
~~~

### Device serial not found

Symptom:

~~~text
Device serial 1050325823 not found
~~~

Check:

~~~bash
nrfutil device list
lsusb | grep -Ei "segger|nordic|1366|j-link" || true
ls -l /dev/ttyACM* 2>/dev/null || true
dmesg | tail -80
~~~

Restart runner if needed:

~~~bash
sudo systemctl restart actions.runner.TrungHuyEASYPCB-firmware-ci-poc.runner-lab-01.service
~~~

### Lock file issue

Check:

~~~bash
ls -lah /tmp/firmware-ci-device-locks
ps aux | grep -Ei 'flash|pytest|west|nrfutil|with_device_lock' | grep -v grep
~~~

### Wrong tag version

Check:

~~~bash
git show --no-patch --decorate --oneline v<version>
git show v<version>:RELEASE_VERSION
~~~

Delete wrong tag only if necessary:

~~~bash
git tag -d v<version>
git push origin --delete v<version>
~~~

### RELEASE_VERSION conflict

Keep the intended release version:

~~~bash
cat > RELEASE_VERSION <<'EOF_VERSION'
<version>
EOF_VERSION

git add RELEASE_VERSION
git commit -m "release: resolve v<version> version conflict"
git push origin release/<version>
~~~

## Generated reports

| File | Purpose |
|---|---|
| hil-results/runner-maintenance.json | Runner health check result |
| hil-results/device-preflight.json | Device readiness result |
| hil-results/run_metadata.json | HIL run metadata |
| hil-results/pytest-junit.xml | Pytest HIL result |
| hil-results/hil-summary.json | HIL summary |
| hil-results/release-gate.json | Release quality gate result |
| release/signature.json | Firmware signature |
| release/checksums.sha256 | Release checksums |
| promotion/stable-promotion.json | Stable promotion metadata |

## Stage completion checklist

A stage is complete only when:

~~~text
1. Feature PR merged into develop
2. Release PR merged into main
3. Tag created from main
4. GitHub Release workflow passed
5. HIL Matrix passed when required
6. Nightly HIL passed when required
7. Stable Promotion passed when required
8. Release assets verified
~~~
