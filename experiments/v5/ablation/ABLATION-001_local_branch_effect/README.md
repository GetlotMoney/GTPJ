# V5-ABLATION-001：局部分支真实贡献

```yaml
framework: FRAMEWORK-V5
status: pre_run_gated
base_template: MODEL-V5-TEMPLATE-V1
base_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
experiment_branch: exp/v5/ablation/ablation-001-local-branch-effect
legacy_ref: codex/attempt019-local-ablation#ATTEMPT-019@954851b0d2dfd2d23f1efca10ba1bf142b3a6d68
parameter_matrix: PARAMETER_MATRIX.md
workflow_mode: server_frozen_runner
review_tier: strict-3
```

## 这次到底比较什么

第一批正式实验只比较两组：

- 完整 V5；
- 干净无局部版本。

两组都跑 seed 5、17、29，一共 6 次训练。完整组使用冻结母版代码；无局部组使用本实验分支代码。数据、类别顺序、评估函数、PSE、ICSA、训练轮数和学习率计划保持一致。

无局部版本删除 FGVD、BVSA、SGMP、局部融合，以及 consistency、BMDD、MPP、negative semantic 这些依赖局部路径的损失。PSE 和 ICSA 保留，因为它们会改变全局文本原型，删掉它们就不再是单纯测局部分支。

## 旧 15 行计划如何处理

旧计划把完整复跑、局部权重 0/0.1/0.3 和代码级移除混在一张表里，还把 ICSA 错算进局部子系统。该计划没有产生真实训练结果，现已收敛为 6 行正式矩阵；旧内容仍可从本分支历史提交 `83e4b5a` 回查。

局部权重 0.1/0.3 回答的是“权重取多少”，属于调参，不再混入本次主消融。只把融合权重设成 0 也不等于彻底去掉，因为局部模块和局部损失仍会参与训练。

## 当前完成情况

- [x] 绑定冻结母版与独立实验分支；
- [x] 写出 6 行参数表和 6 份真实配置；
- [x] 完成无局部代码瘦身；
- [x] 证明局部块改变不会影响输出，局部块梯度为 0；
- [x] 保留数据、评估、类别顺序和输出维度；
- [x] 本地机器测试通过；
- [ ] `strict-3` 代码审核通过；
- [ ] 创建运行前冻结提交；
- [ ] 服务器双卡正式启动；
- [ ] 6 次运行全部收口并做配对统计。

## 运行分配

| GPU | 队列 | 代码 |
|---:|---|---|
| 0 | 完整 V5：seed 5 → 17 → 29 | `model/v5-template-v1` |
| 1 | 干净无局部：seed 5 → 17 → 29 | 本实验运行前冻结提交 |

原始日志、checkpoint 和运行状态进入服务器 Warehouse；Git 只保存配置、凭证、哈希和轻量结果。

正式启动还必须提供一次性的 `launch_manifest.json`，其中的审核、参数表、运行时和服务器预检必须全部通过，且冻结提交必须与实际运行提交一致。停止和失败后的处理见 [SERVER_RECOVERY.md](SERVER_RECOVERY.md)：半截运行不自动续跑，保留证据后新建 RUN 从头执行。
