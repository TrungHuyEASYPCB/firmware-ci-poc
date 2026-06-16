# Contributing to Korlinx

Internal development guidelines for the Korlinx team. Naming rules (issues, branches, labels, PR titles) live in [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md); this file covers workflow and enforcement.

---

## Rules (machine-checkable)

> Authoritative, deterministic rules. Sections below are reference detail. Commit/PR formats are defined in [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) (`N6`/`N7`) and enforced by [`.github/commitlint.config.js`](.github/commitlint.config.js).

| ID | Rule |
|----|------|
| `C1` | Never push directly to `main` or `develop` — all changes land via PR. |
| `C2` | Feature work branches off `develop`. Hotfixes branch off `main`. |
| `C3` | Commit header: `^(feat\|fix\|chore\|docs\|refactor\|test\|perf\|ci\|revert\|hotfix)(\([a-z0-9-]+\))?: .+$` |
| `C4` | Commit header ≤ 72 characters total (type + scope + subject). |
| `C5` | Subject: imperative mood, no trailing period, not Title/Sentence/UPPER-case. |
| `C6` | Pre-commit hooks must pass before pushing (`pre-commit run --all-files`). |
| `C7` | PR title must satisfy `C3`; PR body must link the issue (`Closes #<n>`). |
| `C8` | One concern per PR — split unrelated changes. |
| `C9` | ≥ 1 approval before merge; author does not merge their own PR (except hotfix). |
| `C10` | All review threads resolved before merge. |
| `C11` | Merge strategy: **Squash and Merge** for every PR. |

**DO**
- Run `pre-commit run --all-files` before pushing.
- Explain *why* in the commit body, not *what*.
- Prefix non-blocking review comments with `nit:` or `suggestion:`.

**DON'T**
- Commit with `--no-verify` to skip hooks.
- Disable a lint rule inline without a comment explaining why.
- Bundle multiple concerns into one PR.

---

## Branch Strategy

| Branch | Purpose | Merges from | Trigger |
|--------|---------|-------------|---------|
| `main` | Production — always deployable | PR from `develop` (1 approval) | Production flash + manual release tag |
| `develop` | Integration | PR from feature branches (1 approval) | Preview flash + auto `-dev` tag |

Branch naming patterns: see [NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md) (`N3`/`N4`).

---

## Commit Messages

[Conventional Commits](https://www.conventionalcommits.org/), enforced on the `commit-msg` hook.

```
<type>(<scope>): <short summary>

[optional body — explain why, not what]

[optional footer — Closes #X, Refs #Y]
```

- Allowed types (`C3`): `feat` `fix` `chore` `docs` `refactor` `test` `perf` `ci` `revert` `hotfix`
- Header ≤ 72 chars including the `type(scope): ` prefix (`C4`) — this leaves the summary itself shorter than 72.
- Scope is optional but encouraged: `feat(lcd):`, `fix(lte):`

**Examples** (all pass commitlint):
```
feat(lcd): add RGB state machine for idle screen
fix(lte): handle AT command timeout on network loss
chore: bump pre-commit hooks to v4.6.0
```

---

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

Run manually any time:
```bash
pre-commit run --all-files
```

Hooks (see [`.pre-commit-config.yaml`](.pre-commit-config.yaml)):
- Trailing whitespace, EOF newline, line endings (`--fix=lf`)
- YAML / JSON syntax validation
- Merge-conflict marker detection
- Conventional Commits enforcement on `commit-msg`

---

## Pull Requests

- Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) — loads automatically.
- One concern per PR (`C8`); link the issue with `Closes #X` (`C7`).
- PR title follows Conventional Commits (`C3`); pre-commit must pass (`C6`).
- **Squash and Merge** only (`C11`); author does not merge own PR (`C9`).

---

## Code Review

- Minimum **1 approval** before merge (`C9`).
- Reviewers respond within **2 business days**.
- Resolve all threads before merge (`C10`).
- Prefix non-blocking comments with `nit:` / `suggestion:`.

---

## Hotfix Process

Urgent fixes that can't wait for the full review cycle:

1. Branch from `main`: `hotfix/<description>` (`N4`)
2. Fix, commit, open PR with a `hotfix:` title (`C3`)
3. Author may self-merge into `main` after a quick peer check (Slack/call is fine)
4. **Also merge into `develop`** to avoid drift — second PR or cherry-pick
5. Tag the release after merge: `git tag -a v<x.y.z> -m "hotfix: <description>" && git push origin v<x.y.z>`

---

## Release Process (normal `develop → main`)

CI does **not** auto-tag `main` — a maintainer owns the semver bump:

1. Open a PR from `develop` to `main`; merge after approval (`C9`/`C11`).
2. The push to `main` runs the production flash job (no tag created by CI).
3. Tag the release manually:
   ```bash
   git tag -a v<x.y.z> -m "release: <summary>" && git push origin v<x.y.z>
   ```
   Bump rule: `feat` → minor, `fix`/`chore` → patch, breaking change → major.
