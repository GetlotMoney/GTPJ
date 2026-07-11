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
v4/                      historical config-only tag record; formal reference is v3/CONFIRM-001
v5/                      GTPJ-v5 owner-activated active mainline 记录
```

当前 active mainline code 是 `GTPJ-v5 / tag v5`。`GTPJ-v5` 是 owner-activated provisional，`best_observed_H=74.54`，5 次 frozen repeat mean `confirmed_H=74.44`。

当前更强的 confirmed reference 是 `v3/CONFIRM-001 local-v3-054 / confirmed_H=74.47`。历史 `v4` tag 是 config-only 误分类，不作为正式框架版本。

当前研究最高单次来自 `IDEA-0003/TRIAL-001 ATTEMPT-017`，`H=75.11`；ATTEMPT-018 的 5 次 exact repeat 最好 `H=74.71`、均值 `H=74.58`，未还原，因此该结果仍是未晋级的研究单次，不能替代 confirmed reference。完整高分分布见该 trial 的 [README](module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/README.md) 和 [ATTEMPTS](module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/ATTEMPTS.md)。

旧的 `experiments/v1/` 到 `experiments/v4/` 不删除。`main` 保存全部版本账本，代码快照靠对应 tag 回滚。

## 正式表格地图

以后查询“现在有哪些待跑实验”，先看正式表格，不从 `.gtpj_runtime/` 目录反推。

| 问题 | 先看哪张表 | 说明 |
|---|---|---|
| 全局有哪些版本和已登记实验 | `EXPERIMENT_REGISTRY.md` | 全局索引，辅助定位，不替代各类型正式表格。 |
| 某个 baseline 的调参待跑 | `vX/tune/INDEX.md` | `Status` 为 `planned/pending/pre_run/pre_run_gated/ready_to_run` 的行是正式待跑。 |
| 某个 baseline 的消融待跑 | `vX/ablation/INDEX.md` | 同上。 |
| 某个 baseline 的复现/确认待跑 | `vX/confirmation/INDEX.md` | 同上。 |
| 某个新模块 trial 内部还有什么待跑 | `module_trials/.../TRIAL-xxx/ATTEMPTS.md` | trial 内部调参、窄消融、rerun、confirmation 都看这里。 |
| 混合 campaign 里任务如何分配 | `campaigns/.../WORK_ITEMS.md` / `RESULT_INDEX.md` | 只是 derived index；正式结果和正式待跑仍回到各自归属表格。 |

正式待跑统一叫 `formal_pending`。没有正式表格行、只有 `.gtpj_runtime/batches/<run_id>` 的目录，统一叫 `orphan_runtime_plan`；它只能作为历史参考或排障线索，不能自动续跑，也不能进入 keep / best / confirmation / promotion。

不要在这里保存大型数据集、checkpoint、原始日志或 cache 文件。
