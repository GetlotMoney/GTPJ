# 协作摘要

```text
experiment_id: V5-INNOVATION-008
base_version: v5
code_branch: exp/v5/innovation/innovation-008-pse-class-relation-calibration
activation_mode: implementation_with_bounded_read_only_support
formal_training_started: true
memory_used: false
verified_against_current_repo: true
final_decision: rejected_after_e1
```

## 主实现

- 责任：读取现有 V5 代码和项目规则，完成 E0–E4 的最小实现、配置、测试和账本。
- 写入范围：`model/MyModel.py`、`train_GTPJ_CUB.py`、`tools/v5_*`、实验目录、idea_tree 和必要项目文档。
- 当前结论：首次 CUDA 启动在首个 epoch 前发现类别编号设备错误；第二次完成 50 epoch 后发现最终评估索引设备错误。两处均有真实 CUDA 回归测试并经独立复核通过；随后 E0、E1 均完成正式成功 RUN。

## 只读方法核对

- 范围：训练期 self-calibration 与推理期 calibrated stacking 的原论文和作者代码。
- 发现：DAZLE 原式与本实验 seen-only CE 直接组合会产生持续抬高未见类概率的风险；因此采用达到固定下限后归零的有界版本，并在文档中明确写为 DAZLE-inspired。
- 推理结论：E4 使用 `seen logits -= gamma`，gamma 只从类不重叠验证划分确定。
- 文件写入：无。

## 独立代码审核

- 审核轮数：1 轮，原因是改动触及模型、loss 和 eval 语义，但范围只在一个实验分支。
- Reviewer：独立只读 Agent，只复核当前实现，不改文件。
- 审核结论：`PASS`。首轮发现续训可跨 RUN 混写；修复为 checkpoint 必须位于当前输出目录后复核通过，无剩余开跑阻断。
- 未覆盖：E2-E4 按预先停止条件主动跳过，不是待补证据。

## 真实运行与收口

- E0 `RUN-007`：`U=71.25`、`S=76.30`、`H=73.69`、`ZS=81.32`。
- E1 `RUN-002`：`U=78.75`、`S=58.17`、`H=66.92`、`ZS=81.28`。
- 决策：E1 的 `H` 下降 6.77，且 `S` 下降 18.13；按预先停止条件否决，E2-E4 跳过。
- 失败透明度：`RUN-001` 与 `RUN-006` 的日志原样保留，不计入效果比较。

## 第二版实现与审查

- owner 已批准本地运行 R0、R1、R2；不启用训练期或推理期校准。
- 主实现完成共享句子 PSE、安全类别关系适配器、类不重叠验证划分和三份配置。
- 独立只读 Reviewer 首轮仅阻断大缓存复制风险；主实现已改为训练和评估逐 batch 按位置取数，并用等价测试证明指标算法不变。
- 当前机器验证：专项 20 项、合计 35 项相关测试通过；项目校验、框架账本和仓库边界检查通过。
- 同一独立只读 Reviewer 已对最新内存修复给出 `PASS`：确认只长期保留一份大缓存，指标、标签、类别轴和 test 数据边界未改变。
- 未覆盖项只有进程级内存峰值实测；将在 RUN-008 运行时观察，不构成开跑阻断。

## 第二版运行与收口

- 三个本地 RUN 均从 clean commit `9698e68` 启动并正常退出；R0 首次加载时实测训练进程工作集约 7.2 GiB，没有发生旧实现的大缓存复制或 OOM。
- R0 `RUN-008`：`U=58.85`、`S=86.08`、`H=69.91`、`ZS=79.44`。
- R1 `RUN-009`：`U=46.49`、`S=89.83`、`H=61.27`、`ZS=74.81`。
- R2 `RUN-010`：`U=42.89`、`S=90.24`、`H=58.14`、`ZS=75.60`。
- R2 的限幅和旋转边界均生效，但 H 比 R0 低 11.76；按预设停止门否决，不读取正式测试集，不继续多 seed 或校准实验。
