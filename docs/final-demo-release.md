# Final Demo Release

## Purpose

This document marks the final demo release for the Firmware CI/CD PoC.

The goal of this PoC is to prove a complete firmware delivery flow:

~~~text
feature branch
→ Pull Request
→ develop
→ CI validation
→ HIL validation
→ release branch
→ Pull Request
→ main
→ signed GitHub Release
→ stable promotion
~~~

## Final demo version

~~~text
v1.0.0
~~~

## Completed capabilities

| Area | Status |
|---|---|
| Git branch workflow | Complete |
| Self-hosted runner | Complete |
| Docker static analysis sandbox | Complete |
| Docker NCS firmware build | Complete |
| Firmware artifact packaging | Complete |
| Device lock handling | Complete |
| Flash to physical board | Complete |
| Pytest HIL validation | Complete |
| HIL matrix workflow | Complete |
| Nightly HIL regression | Complete |
| HIL report retention | Complete |
| GitHub Actions job summary | Complete |
| Nightly HIL failure notification | Complete |
| Device health preflight | Complete |
| Regression profile hardening | Complete |
| Release quality gate | Complete |
| Runner maintenance check | Complete |
| Stable promotion workflow | Complete |
| Operator runbook | Complete |

## Final release quality requirements

The final `v1.0.0` release is valid only when:

~~~text
1. Release branch is merged into main through PR
2. Tag v1.0.0 is created from main
3. GitHub Release workflow passes
4. Firmware artifact verification passes
5. Firmware signature verification passes
6. HIL Matrix passes with regression profile
7. Nightly HIL Regression passes with regression profile
8. Stable Promotion workflow passes for v1.0.0
~~~

## Final demo board

| Field | Value |
|---|---|
| Device ID | dut-01 |
| Board | nrf52dk/nrf52832 |
| Serial | 1050325823 |
| UART | /dev/ttyACM0 |
| Role | preview |

## Final operator reference

Use the main operator guide:

~~~text
docs/operator-runbook.md
~~~

