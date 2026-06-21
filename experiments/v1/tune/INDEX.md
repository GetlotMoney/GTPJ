# GTPJ-v1 Tune 索引

Tuning run 使用类似 `TUNE-001_topo008` 的 ID，并且只放在本目录：

```text
experiments/v1/tune/
```

创建命令：

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
```

## 已完成

| 实验 | 状态 | 关键变化 | U | S | H | ZS | 说明 |
|---|---|---|---:|---:|---:|---:|---|
| `TUNE-043_cond008` | done | `conditional_text_ratio=0.008` | 72.36 | 75.57 | 73.93 | 81.62 | 第一版正式 baseline |
