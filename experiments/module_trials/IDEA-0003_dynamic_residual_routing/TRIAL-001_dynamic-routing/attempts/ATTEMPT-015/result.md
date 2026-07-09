# ATTEMPT-015 Result

Current status: completed.

Final live monitor snapshot, 2026-07-08 23:36 +08:00:

- run_id: `RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu`
- server status: completed=100, running=0, pending=0, failed=0, skipped=0
- screen session: exited normally; GPU0/GPU1 idle in final read-only check
- top single: `DR-004 direction_sample_h48_w0.495_a0.003`
- metrics: H=75.04, U=73.30, S=76.85, ZS=82.05, best_epoch=37
- H>=75 singles: 2 (`DR-004`, `DR-035`)
- H>=76 singles: 0

Completed jobs reported by `monitor-workflow --report-new-completions`:

| job_id | name | H | U | S | ZS | best_epoch |
|---|---|---:|---:|---:|---:|---:|
| DR-001 | direction_sample_h48_w0.495_a0.0015 | 74.89 | 72.76 | 77.15 | 81.95 | 48 |
| DR-002 | direction_sample_h48_w0.495_a0.002 | 74.75 | 71.86 | 77.89 | 81.73 | 48 |
| DR-003 | direction_sample_h48_w0.495_a0.0025 | 74.34 | 72.29 | 76.51 | 81.34 | 37 |
| DR-004 | direction_sample_h48_w0.495_a0.003 | 75.04 | 73.30 | 76.85 | 82.05 | 37 |
| DR-005 | direction_sample_h48_w0.495_a0.0035 | 74.54 | 72.71 | 76.46 | 81.55 | 37 |
| DR-006 | direction_sample_h48_w0.5_a0.0015 | 74.72 | 73.06 | 76.45 | 81.64 | 40 |
| DR-007 | direction_sample_h48_w0.5_a0.002 | 74.66 | 72.60 | 76.84 | 81.69 | 37 |
| DR-008 | direction_sample_h48_w0.5_a0.0025 | 74.60 | 72.90 | 76.38 | 81.92 | 37 |
| DR-009 | direction_sample_h48_w0.5_a0.003 | 74.63 | 72.40 | 77.01 | 81.51 | 37 |
| DR-010 | direction_sample_h48_w0.5_a0.0035 | 74.88 | 73.17 | 76.68 | 81.96 | 37 |
| DR-011 | direction_sample_h48_w0.505_a0.0015 | 74.61 | 72.56 | 76.78 | 81.57 | 37 |
| DR-012 | direction_sample_h48_w0.505_a0.002 | 74.83 | 72.68 | 77.10 | 81.90 | 47 |
| DR-013 | direction_sample_h48_w0.505_a0.0025 | 74.81 | 72.60 | 77.16 | 81.89 | 37 |
| DR-014 | direction_sample_h48_w0.505_a0.003 | 74.63 | 72.76 | 76.61 | 81.58 | 48 |
| DR-015 | direction_sample_h48_w0.505_a0.0035 | 74.85 | 72.66 | 77.19 | 81.92 | 48 |
| DR-016 | direction_sample_h48_w0.51_a0.0015 | 74.57 | 72.21 | 77.10 | 81.63 | 48 |
| DR-017 | direction_sample_h48_w0.51_a0.002 | 74.64 | 72.90 | 76.47 | 81.79 | 37 |
| DR-018 | direction_sample_h48_w0.51_a0.0025 | 74.54 | 72.36 | 76.86 | 81.45 | 37 |
| DR-019 | direction_sample_h48_w0.51_a0.003 | 74.73 | 72.19 | 77.46 | 81.81 | 48 |
| DR-020 | direction_sample_h48_w0.51_a0.0035 | 74.74 | 72.60 | 77.02 | 81.79 | 48 |
| DR-021 | direction_sample_h48_w0.515_a0.0015 | 74.60 | 72.77 | 76.53 | 81.68 | 46 |
| DR-022 | direction_sample_h48_w0.515_a0.002 | 74.68 | 72.70 | 76.77 | 81.88 | 37 |
| DR-023 | direction_sample_h48_w0.515_a0.0025 | 74.92 | 73.03 | 76.91 | 82.16 | 50 |
| DR-024 | direction_sample_h48_w0.515_a0.003 | 74.73 | 72.62 | 76.97 | 81.50 | 48 |
| DR-025 | direction_sample_h48_w0.515_a0.0035 | 74.71 | 72.70 | 76.82 | 81.93 | 47 |
| DR-026 | direction_sample_h48_w0.52_a0.0015 | 74.71 | 72.43 | 77.15 | 81.61 | 48 |
| DR-027 | direction_sample_h48_w0.52_a0.002 | 74.76 | 72.90 | 76.72 | 81.88 | 37 |
| DR-028 | direction_sample_h48_w0.52_a0.0025 | 74.48 | 72.56 | 76.50 | 81.54 | 48 |
| DR-029 | direction_sample_h48_w0.52_a0.003 | 74.61 | 72.39 | 76.96 | 81.64 | 50 |
| DR-030 | direction_sample_h48_w0.52_a0.0035 | 74.46 | 71.92 | 77.18 | 81.28 | 48 |
| DR-031 | direction_sample_h48_w0.525_a0.0015 | 74.63 | 72.66 | 76.72 | 81.81 | 49 |
| DR-032 | direction_sample_h48_w0.525_a0.002 | 74.81 | 72.97 | 76.75 | 81.69 | 50 |
| DR-033 | direction_sample_h48_w0.525_a0.0025 | 74.53 | 72.56 | 76.61 | 81.54 | 37 |
| DR-034 | direction_sample_h48_w0.525_a0.003 | 74.80 | 72.53 | 77.21 | 81.72 | 48 |
| DR-035 | direction_sample_h48_w0.525_a0.0035 | 75.00 | 73.03 | 77.09 | 82.05 | 49 |
| DR-036 | direction_sample_h48_w0.53_a0.0015 | 74.91 | 72.26 | 77.76 | 81.82 | 48 |
| DR-037 | direction_sample_h48_w0.53_a0.002 | 74.79 | 72.90 | 76.78 | 81.92 | 37 |
| DR-038 | direction_sample_h48_w0.53_a0.0025 | 74.79 | 72.53 | 77.21 | 81.88 | 48 |
| DR-039 | direction_sample_h48_w0.53_a0.003 | 74.69 | 72.79 | 76.69 | 81.71 | 37 |
| DR-040 | direction_sample_h48_w0.53_a0.0035 | 74.49 | 72.72 | 76.34 | 81.78 | 37 |
| DR-041 | direction_sample_h48_w0.535_a0.0015 | 74.65 | 72.79 | 76.60 | 81.54 | 36 |
| DR-042 | direction_sample_h48_w0.535_a0.002 | 74.76 | 72.86 | 76.75 | 81.99 | 48 |
| DR-043 | direction_sample_h48_w0.535_a0.0025 | 74.77 | 72.45 | 77.23 | 81.91 | 50 |
| DR-044 | direction_sample_h48_w0.535_a0.003 | 74.66 | 72.63 | 76.82 | 81.89 | 50 |
| DR-045 | direction_sample_h48_w0.535_a0.0035 | 74.67 | 72.52 | 76.94 | 81.65 | 37 |
| DR-046 | direction_sample_h48_w0.54_a0.0015 | 74.34 | 72.29 | 76.50 | 81.25 | 45 |
| DR-047 | direction_sample_h48_w0.54_a0.002 | 74.57 | 72.94 | 76.28 | 81.72 | 37 |
| DR-048 | direction_sample_h48_w0.54_a0.0025 | 74.43 | 72.37 | 76.61 | 81.31 | 37 |
| DR-049 | direction_sample_h48_w0.54_a0.003 | 74.62 | 72.86 | 76.46 | 81.68 | 37 |
| DR-050 | direction_sample_h48_w0.54_a0.0035 | 74.47 | 72.90 | 76.10 | 81.54 | 37 |
| DR-051 | direction_sample_h48_w0.545_a0.0015 | 74.65 | 72.46 | 76.97 | 81.91 | 48 |
| DR-052 | direction_sample_h48_w0.545_a0.002 | 74.77 | 72.52 | 77.16 | 81.78 | 47 |
| DR-053 | direction_sample_h48_w0.545_a0.0025 | 74.81 | 72.73 | 77.01 | 82.12 | 50 |
| DR-054 | direction_sample_h48_w0.545_a0.003 | 74.30 | 73.06 | 75.59 | 81.38 | 34 |
| DR-055 | direction_sample_h48_w0.545_a0.0035 | 74.77 | 72.53 | 77.16 | 81.89 | 48 |
| DR-056 | direction_sample_h48_w0.55_a0.0015 | 74.44 | 72.26 | 76.77 | 81.54 | 48 |
| DR-057 | direction_sample_h48_w0.55_a0.002 | 74.66 | 72.26 | 77.23 | 81.75 | 50 |
| DR-058 | direction_sample_h48_w0.55_a0.0025 | 74.67 | 73.10 | 76.30 | 81.88 | 37 |
| DR-059 | direction_sample_h48_w0.55_a0.003 | 74.81 | 72.56 | 77.20 | 81.88 | 48 |
| DR-060 | direction_sample_h48_w0.55_a0.0035 | 74.73 | 72.90 | 76.65 | 81.98 | 37 |
| DR-061 | direction_sample_h48_w0.555_a0.0015 | 74.66 | 73.04 | 76.36 | 81.89 | 37 |
| DR-062 | direction_sample_h48_w0.555_a0.002 | 74.46 | 72.18 | 76.89 | 81.67 | 48 |
| DR-063 | direction_sample_h48_w0.555_a0.0025 | 74.58 | 72.66 | 76.60 | 81.58 | 48 |
| DR-064 | direction_sample_h48_w0.555_a0.003 | 74.59 | 72.73 | 76.55 | 81.85 | 37 |
| DR-065 | direction_sample_h48_w0.555_a0.0035 | 74.58 | 73.13 | 76.10 | 81.61 | 47 |
| DR-066 | direction_sample_h48_w0.4975_a0.00225 | 74.67 | 72.76 | 76.67 | 81.78 | 48 |
| DR-067 | direction_sample_h48_w0.4975_a0.00275 | 74.71 | 72.59 | 76.95 | 81.68 | 48 |
| DR-068 | direction_sample_h48_w0.4975_a0.00325 | 74.74 | 72.78 | 76.81 | 81.84 | 48 |
| DR-069 | direction_sample_h48_w0.4975_a0.00375 | 74.54 | 72.90 | 76.26 | 81.82 | 48 |
| DR-070 | direction_sample_h48_w0.5025_a0.00225 | 74.52 | 72.63 | 76.51 | 81.49 | 48 |
| DR-071 | direction_sample_h48_w0.5025_a0.00275 | 74.70 | 73.04 | 76.45 | 81.65 | 37 |
| DR-072 | direction_sample_h48_w0.5025_a0.00325 | 74.62 | 72.39 | 76.99 | 81.78 | 48 |
| DR-073 | direction_sample_h48_w0.5025_a0.00375 | 74.61 | 72.56 | 76.77 | 81.68 | 46 |
| DR-074 | direction_sample_h48_w0.5425_a0.00225 | 74.64 | 72.56 | 76.84 | 81.76 | 48 |
| DR-075 | direction_sample_h48_w0.5425_a0.00275 | 74.77 | 73.27 | 76.32 | 81.86 | 37 |
| DR-076 | direction_sample_h48_w0.5425_a0.00325 | 74.66 | 72.80 | 76.62 | 81.61 | 37 |
| DR-078 | direction_sample_h48_w0.5475_a0.00225 | 74.53 | 73.07 | 76.05 | 81.78 | 37 |
| DR-077 | direction_sample_h48_w0.5425_a0.00375 | 74.54 | 72.53 | 76.68 | 81.85 | 48 |
| DR-080 | direction_sample_h48_w0.5475_a0.00325 | 74.65 | 72.81 | 76.59 | 81.89 | 37 |
| DR-079 | direction_sample_h48_w0.5475_a0.00275 | 74.49 | 72.33 | 76.79 | 81.75 | 39 |
| DR-082 | direction_sample_h48_w0.5525_a0.00225 | 74.59 | 72.46 | 76.85 | 81.51 | 48 |
| DR-081 | direction_sample_h48_w0.5475_a0.00375 | 74.88 | 72.76 | 77.13 | 81.88 | 48 |
| DR-084 | direction_sample_h48_w0.5525_a0.00325 | 74.72 | 72.53 | 77.05 | 81.85 | 46 |
| DR-083 | direction_sample_h48_w0.5525_a0.00275 | 74.56 | 73.04 | 76.15 | 81.68 | 37 |
| DR-086 | direction_sample_h48_w0.525_a0.0005 | 74.69 | 72.88 | 76.59 | 81.50 | 48 |
| DR-085 | direction_sample_h48_w0.5525_a0.00375 | 74.42 | 72.32 | 76.66 | 81.44 | 37 |
| DR-088 | direction_sample_h48_w0.525_a0.00125 | 74.77 | 72.89 | 76.75 | 82.05 | 48 |
| DR-087 | direction_sample_h48_w0.525_a0.001 | 74.56 | 72.74 | 76.48 | 81.33 | 37 |
| DR-090 | direction_sample_h48_w0.53_a0.001 | 74.37 | 72.46 | 76.38 | 81.38 | 47 |
| DR-089 | direction_sample_h48_w0.53_a0.0005 | 74.66 | 72.16 | 77.33 | 81.51 | 48 |
| DR-092 | direction_sample_h48_w0.535_a0.0005 | 74.72 | 72.33 | 77.28 | 81.86 | 48 |
| DR-091 | direction_sample_h48_w0.53_a0.00125 | 74.56 | 72.49 | 76.76 | 81.85 | 48 |
| DR-094 | direction_sample_h48_w0.535_a0.00125 | 74.77 | 72.70 | 76.96 | 81.92 | 48 |
| DR-093 | direction_sample_h48_w0.535_a0.001 | 74.67 | 72.83 | 76.59 | 81.81 | 37 |
| DR-096 | direction_sample_h48_w0.54_a0.001 | 74.59 | 72.53 | 76.77 | 81.55 | 35 |
| DR-095 | direction_sample_h48_w0.54_a0.0005 | 74.40 | 72.30 | 76.62 | 81.32 | 37 |
| DR-098 | direction_sample_h48_w0.545_a0.0005 | 74.74 | 72.63 | 76.98 | 81.78 | 48 |
| DR-097 | direction_sample_h48_w0.54_a0.00125 | 74.57 | 72.29 | 77.00 | 81.65 | 49 |
| DR-100 | direction_sample_h48_w0.545_a0.00125 | 74.64 | 72.83 | 76.53 | 81.81 | 37 |
| DR-099 | direction_sample_h48_w0.545_a0.001 | 74.81 | 72.93 | 76.79 | 81.86 | 37 |

Final group summary:

| group | jobs | best job | best H | mean H | min H | max H |
|---|---:|---|---:|---:|---:|---:|
| h76_hotspot100_primary_grid | 65 | DR-004 | 75.04 | 74.670 | 74.30 | 75.04 |
| h76_hotspot100_micro_grid | 20 | DR-081 | 74.88 | 74.628 | 74.42 | 74.88 |
| h76_hotspot100_low_anchor_ridge | 15 | DR-099 | 74.81 | 74.635 | 74.37 | 74.81 |

Interpretation: `DR-004` and `DR-035` are tune_search single-run hits at or above 75. They are useful candidate evidence, but they are not reproduction, not confirmation evidence, and not promotion triggers. No H>=76 candidate appeared in this 100-job campaign. Follow-up requires exact-repeat same config and same seed under the reproduction rule.

Promotion is blocked. Confirmation is not started for this tune run.
