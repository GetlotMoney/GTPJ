# ATTEMPT-008 Result

`ATTEMPT-008` 是 DR-035 的 same-seed min6 exact repeat，固定 seed=5、`direction_sample_h48_w0.525_a0.005`、batch size 64 和原评估口径。

| Job | U | S | H | ZS | Best epoch |
|---|---:|---:|---:|---:|---:|
| DR-001 | 72.23 | 77.07 | 74.57 | 81.75 | 48 |
| DR-002 | 72.09 | 77.27 | 74.59 | 81.48 | 48 |
| DR-003 | 72.29 | 76.86 | 74.51 | 81.84 | 48 |
| DR-004 | 73.17 | 76.43 | 74.76 | 82.02 | 37 |
| DR-005 | 72.32 | 76.77 | 74.47 | 81.51 | 48 |
| DR-006 | 72.56 | 76.44 | 74.45 | 81.85 | 47 |

```text
mean H: 74.56
min H: 74.45
max H: 74.76
range H: 0.31
best single: DR-004 / H=74.76
```

结论：`not_confirmed`。六次全部完成且稳定性 range 合格，但 mean H=74.56 低于预设 `mean_H>=74.60` 门槛，不能升级为 min6 confirmed。
