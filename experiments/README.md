# 实验记录

实验记录是轻量证据文件，不是原始训练存储区。

主要区域：

```text
VERSION_TREE.md          正式版本的父节点和代码来源账本
EXPERIMENT_REGISTRY.md   全局实验登记表
module_trials/           有代码实现证据的创新 trial
v1/                      GTPJ-v1 baseline、tune、ablation、confirmation 记录
v2/                      GTPJ-v2 baseline、tune、ablation、confirmation 记录
v3/                      GTPJ-v3 baseline、tune、ablation、confirmation 记录
v4/                      GTPJ-v4 confirmed reference baseline 记录
v5/                      GTPJ-v5 owner-activated active mainline 记录
```

当前 active mainline code 是 `GTPJ-v5 / tag v5`。`GTPJ-v5` 是 owner-activated provisional，`best_observed_H=74.54`，5 次 frozen repeat mean `confirmed_H=74.44`。

当前更强的 confirmed reference 仍是 `GTPJ-v4 / tag v4 / confirmed_H=74.45`。

旧的 `experiments/v1/` 到 `experiments/v4/` 不删除。`main` 保存全部版本账本，代码快照靠对应 tag 回滚。

不要在这里保存大型数据集、checkpoint、原始日志或 cache 文件。
