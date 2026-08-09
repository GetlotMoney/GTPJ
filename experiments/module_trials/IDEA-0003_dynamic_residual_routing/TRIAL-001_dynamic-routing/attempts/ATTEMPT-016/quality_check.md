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

## 服务器完成状态

- server runtime status: completed
- latest counts after sync: completed=10, running=0, pending=0, failed=0, skipped=0
- latest best: `DR-008` / `A015DR035` / H=74.85，低于 restore target H=75.00。
- `A015DR004` 完成 5/5，best H=74.84，低于 restore target H=75.04。
- `A015DR035` 完成 5/5，best H=74.85，低于 restore target H=75.00。

## 当前判断

两个 H>=75 来源候选均只有 near miss，没有 restored。由于每个候选已达到 5 次 hard cap，本轮不能继续追加 exact repeat；`confirmation_decision: not_restored`，`promotion_decision: blocked`。

本次只同步服务器已有运行结果并更新账本，不改变训练代码、配置、数据 split、label mapping、class order、logits shape 或 metric 语义。
