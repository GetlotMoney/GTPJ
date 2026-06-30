# Attempts

| Attempt | Server run | Status | Best single | Best dynamic | Repeat evidence | Decision |
|---|---|---|---|---|---|---|
| `ATTEMPT-001` | `RUN-20260630-0005-dynroute50-2gpu` | 50 completed / 0 failed | DR-001 static control H=74.40 | DR-008 local_class_h24 H=74.39 | DR-008 repeat mean H=74.23 | revise, no promotion |

## ATTEMPT-001 Notes

This attempt used the `balanced-aggressive` 50-job profile across two GPUs.

Main observations:

- Static v5 control remained the top single result at H=74.40.
- Best dynamic single was close but below references: DR-008 H=74.39.
- Best dynamic repeat mean was weaker: DR-008 repeat mean H=74.23.
- Direction gate had the most promising first-principles signal, especially DR-023 with H=74.38 and U=72.26.
- Dynamic ICSA and multi-gate combinations were unstable in this profile.
- Follow-up profile should freeze ICSA and explore direction/local/PSE gates with fewer coupled moving parts.

Attempt-local records:

- `attempts/ATTEMPT-001/config.yaml`
- `attempts/ATTEMPT-001/manifest.yaml`
- `attempts/ATTEMPT-001/result.yaml`
- `attempts/ATTEMPT-001/result.md`
- `attempts/ATTEMPT-001/quality_check.md`
