# GTPJ-v5 Result

```text
version: v5
status: owner_activated_provisional
evidence_level: confirmation_grade
best_observed_H: 74.54
confirmed_H: 74.44
confirmation_status: owner_activated_provisional
promotion_decision: blocked
owner_activation_decision: owner_activate
active_main_update: activated
```

| Dataset | Source | U | S | H | ZS | best_epoch | Note |
|---|---|---:|---:|---:|---:|---:|---|
| CUB GZSL | `trial003-main100-069` | 71.90 | 77.16 | 74.43 | 81.62 | 34 | source config |
| CUB GZSL | `trial003-main100-091` | 71.80 | 77.40 | 74.49 | 81.68 | 45 | frozen repeat |
| CUB GZSL | `trial003-main100-092` | 71.90 | 77.14 | 74.43 | 81.52 | 34 | frozen repeat |
| CUB GZSL | `trial003-main100-093` | 71.63 | 77.29 | 74.35 | 81.48 | 34 | frozen repeat |
| CUB GZSL | `trial003-main100-094` | 72.53 | 76.40 | 74.41 | 81.45 | 33 | frozen repeat |
| CUB GZSL | `trial003-main100-095` | 72.13 | 77.11 | 74.54 | 81.65 | 34 | best observed frozen repeat |

Frozen repeat mean for jobs 091-095:

```text
U_mean: 72.00
S_mean: 77.07
H_mean: 74.44
ZS_mean: 81.56
```

`GTPJ-v5` is the owner-selected active mainline for the next tuning round. The strongest single observation is above `GTPJ-v4 confirmed_H=74.45`, but the 5-repeat mean is `74.44`, so v4 remains the stronger confirmed reference unless a later v5 confirmation/tune run changes that.
