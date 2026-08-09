# Campaign Plan

campaign_id: `CAMP-20260704-dr035-h76`

## 目标

目标是向稳定 `GZSL-H=76.00` 推进，但本轮仍只允许使用已有 GTPJ-v5 / IDEA-0003 dynamic routing 框架。不能引入新训练入口、新数据协议、新评价协议或未登记的新模块。

## 阶段

1. `ATTEMPT-008`: 跑 `dr035-min6-confirm`，把 DR-035 的同 seed exact repeat 从 min3 扩展到 min6。
2. `ATTEMPT-009`: 跑 `h76-existing-routing-100`，在已有动态路由框架内做 100 个 score search / tune。
3. 根据 ATTEMPT-009 的 top candidates，选择 `H>=74.75` 且 U/S 无塌陷的候选进入后续 min3；单次结果不直接 promotion。

## 硬边界

- CUB xlsa17 split、class order、label mapping、logits shape 和 U/S/H/ZS metric semantics 不变。
- `ATTEMPT-008` 固定 source seed=5。
- `ATTEMPT-009` 是 score search，不是 strict repeat。
- campaign 目录只做调度索引，正式结果回写到 ATTEMPT-008 / ATTEMPT-009。
- checkpoint 完成后按 Top-3 保留，logs、summary、events 和 receipts 不删除。
