# 实验记录

实验记录是轻量证据文件，不是原始训练存储区。

主要区域：

```text
VERSION_TREE.md          正式 baseline 的父节点和代码来源账本
EXPERIMENT_REGISTRY.md   全局实验登记表
module_trials/           有代码实现证据的创新 trial
v1/                      GTPJ-v1 baseline、tune、ablation、confirmation 记录
```

当前唯一权威基线是 `GTPJ-v1 / tag v1 / H=73.93`。

以后新增 `v2`、`v3` 时，旧的 `experiments/v1/` 不删除。`main` 保存全部版本账本，
代码快照靠对应 tag 回滚。

不要在这里保存大型数据集、checkpoint 或原始 cache 文件。
