# ATTEMPT-016 Quality Check

## 已检查

- 复现类型是 `exact_repeat`，不是 seed sweep，也不是 multi-seed stability。
- 两个候选都固定 seed=5；每个候选最多 5 次。
- 只有达到各自 `restore_target_H` 才算 restored。
- near miss 不算 restored，不触发 confirmation，不触发 promotion。
- 本轮不改变 GZSL 接口、数据 split、label mapping、class order、logits shape 或 metric 语义。
- 运行模式是 `server_frozen_runner`，没有创建命名 Codex 线程，也没有启动右侧 temporary subagents。
- `RUN-20260708-0004...` 是训练前环境失败，不作为方法证据。
- 有效运行是 `RUN-20260708-0005...`，固定 Python 为 `/data/lby/.conda/envs/dvsr_gpu/bin/python`。

## 当前服务器状态

- screen session: `GTPJ_ATTEMPT016_RESTORE10_R2`
- controller: GPU0/GPU1 各 1 个 `run_dynamic_routing_batch.py`
- trainer: GPU0/GPU1 各 1 个 `train_GTPJ_CUB.py`
- latest counts: completed=4, running=2, pending=4, failed=0, skipped=0
- latest best: `DR-003` / `A015DR004` / H=74.84，低于 restore target H=75.04。

## 当前判断

`A015DR004` 当前只有 near miss，没有 restored。Runner 继续 exact repeat，直到达到 restore target 或触发 5 次 hard cap。promotion_decision: blocked。
