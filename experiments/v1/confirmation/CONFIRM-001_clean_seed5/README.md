# CONFIRM-001_clean_seed5

```text
experiment_id: CONFIRM-001
version: v1
code_tag: v1
runtime: OpenClaw preferred / Codex compatible
review_mode: STRICT
run_commit: c2571b0
config: config.yaml
log: pending
status: running
```

## 问题

确认 `GTPJ-v1` 能在本仓库中用 `seed=5` 干净运行。

## 运行前检查

- [ ] 分支从 tag `v1` 切出。
- [ ] 配置复制自 `experiments/v1/config.yaml`。
- [ ] 只改变声明过的变量或开关。
- [ ] Review decision 为 `ACCEPTED`。

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## 结论

待记录。

## 运行计划

```text
branch: exp/v1-confirm-001-clean-seed5
command: F:\Anaconda\envs\dvsr_gpu\python.exe train_VGSR_CUB.py --config experiments/v1/confirmation/CONFIRM-001_clean_seed5/config.yaml
python: F:\Anaconda\envs\dvsr_gpu\python.exe
dataset: CUB GZSL
seed: 5
device: cuda:0
data_source: local data junction to C:\Users\Administrator\Desktop\cv-work\DVSR\data
metadata_source: local junction data/xlsa17/data -> C:\Users\Administrator\Desktop\cv-work\DVSR\xlsa17\xlsa17\data
```

训练策略由 `config.yaml` 锁定。`lr_stages` 存在时，训练脚本会用分阶段策略覆盖单独的 `epochs` 字段：

```text
stage 1: lr=0.001, epochs=20, eta_min=1e-5
stage 2: lr=0.0001, epochs=20, eta_min=1e-6, restart_from_best=False
stage 3: lr=0.00001, epochs=10, eta_min=1e-7, restart_from_best=False
total_epochs: 50
amp: disabled by default
```
