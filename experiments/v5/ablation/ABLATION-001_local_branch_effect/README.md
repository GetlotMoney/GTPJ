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

两组都跑 seed 5、17、29，一共 6 次训练。两组的运行入口都来自本次冻结候选；完整组的模型和科学计算路径与冻结母版等价，无局部组使用本实验的专属瘦身模型。数据、类别顺序、评估函数、PSE、ICSA、训练轮数和学习率计划保持一致。

无局部版本删除 FGVD、BVSA、SGMP、局部融合，以及 consistency、BMDD、MPP、negative semantic 这些依赖局部路径的损失。PSE 和 ICSA 保留，因为它们会改变全局文本原型，删掉它们就不再是单纯测局部分支。

## 旧 15 行计划如何处理

旧计划把完整复跑、局部权重 0/0.1/0.3 和代码级移除混在一张表里，还把 ICSA 错算进局部子系统。研究设计已经收敛为 FULL 与 GLOBAL_ONLY 各三个 seed 的 6 个配对任务；当前正式矩阵共 12 行，因为 R3 的 6 行失败/取消证据必须永久保留，R4 使用新的 `RUN-007…012` 从头重跑。旧混合计划仍可从本分支历史提交 `83e4b5a` 回查。

局部权重 0.1/0.3 回答的是“权重取多少”，属于调参，不再混入本次主消融。只把融合权重设成 0 也不等于彻底去掉，因为局部模块和局部损失仍会参与训练。

## 当前完成情况

- [x] 绑定冻结母版与独立实验分支；
- [x] 参数表同表保留 R3、R4 历史；R4 的两项 seed 5 成功结果已从不可变日志恢复，其余四项标记为未启动；
- [x] 完成无局部代码瘦身；
- [x] 证明局部块改变不会影响输出，局部块梯度为 0；
- [x] 保留数据、评估、类别顺序和输出维度；
- [x] 冻结 12 个正式输入文件及 split、label、class order、metric 口径；
- [x] 本地机器测试通过；
- [x] `agent_runtime.yaml` 与三份开跑前角色检查通过；
- [x] 目录句柄修复后的 `strict-3` 代码审核通过；
- [x] R3 真实双卡启动进入两个模型入口，并在初始化时暴露类别编号的 CPU/CUDA 设备冲突；
- [x] R3 两个进程返回码为 1，收据与清理完整，其余四项未启动；
- [x] CUDA 类别编号修复后的 `strict-3` 审核通过；
- [x] 创建 R5 的 `RUN-013…016` 四个新身份，只补跑 R4 未启动的 seed 17、29；
- [x] R4 双卡训练成功完成 seed 5；记账程序的中文日志兼容问题已定位并修复；
- [ ] R5 通过新一轮审核和冻结后在服务器双卡启动；
- [ ] 剩余 4 次运行收口，并与已恢复的 seed 5 一起做三种子配对统计。

## 运行分配

| GPU | 队列 | 代码 |
|---:|---|---|
| 0 | 完整 V5：只补 seed 17 → 29 | `model/v5-template-v1` |
| 1 | 干净无局部：只补 seed 17 → 29 | 本实验运行前冻结提交 |

原始日志、checkpoint 和运行状态进入服务器 Warehouse；Git 只保存配置、凭证、哈希和轻量结果。

正式启动还必须提供一次性的 `launch_manifest.json`。清单只绑定冻结身份、被审核的代码候选、固定 Python 和证据哈希；控制器必须从被审核代码候选的干净 checkout 执行，再从最终 Git bundle 的准确提交中克隆真实实验分支，重新核对审核包、运行时门、参数表、数据清单、实验绑定和仓库边界，并确认审核后只补了审核记录与开跑门，不能靠手填“通过”、复用旧审核或篡改最终提交里的控制器绕过。runtime 与 Warehouse 使用冻结提交前 12 位命名，`execution_id` 和六个 `run_id` 在服务器只能领取一次。停止和失败后的处理见 [SERVER_RECOVERY.md](SERVER_RECOVERY.md)：半截运行不自动续跑，保留证据后必须用新的提交、job 和 run 从头执行。
