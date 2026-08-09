# Quality Check

```text
runtime: local_cuda
quality_check_mode: STRICT
decision: PASS_REJECT_RESULT
promotion_decision: not_applicable
evidence_level: single_seed_paired_rejection
confirmation_status: not_applicable
```

## 范围

检查 E0/E1 的代码提交、配置、数据身份、运行日志、最终指标、模型文件和评估口径；这是结果真实性检查，不是把失败方案晋级。

## 发现

- E0 与 E1 均从 clean commit `7295b07` 启动，seed 都是 5。
- 两组均完成 50 个 epoch 后只评估一次测试集。
- E1 相对 E0：`ΔU=+7.50`、`ΔS=-18.13`、`ΔH=-6.77`、`ΔZS=-0.04`。
- `RUN-001`、`RUN-006` 的失败日志保留，未混入正式指标。

## 质量检查

- [x] 代码快照或 base version 明确。
- [x] 配置副本保存在实验目录。
- [x] 外部日志 artifact URI、sha256、size 明确。
- [x] 结果口径明确。
- [x] 单 seed 否决证据没有冒充 confirmation 或 promotion。
- [x] eval 设备修复已声明且不改变指标算法、class order 或 logits shape。
- [x] seen/unseen split、label mapping、class order 和 metric calculation 未改变。
- [x] GitHub 目录中没有新增 raw log、checkpoint 或训练生成图。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] derived_from_framework / source_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] `evidence_level: baseline_grade` 或明确标成 owner_activated_unconfirmed / provisional。
- [ ] clean confirmation 或多 run 稳定性证据明确；单次最高 H 不直接 promotion。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 外部日志 artifact URI、sha256、size、保留位置明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到来源正式框架行为。
- [ ] VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] idea_tree current_version 和必要的 version_scores.vX 已更新。
- [ ] 新 baseline tag 准备打在包含正式版本代码和版本材料的明确 commit 上。
- [ ] main 当前代码只有 owner 明确执行 activate-version vX 时才切换；默认不切换。

## 决策

`PASS_REJECT_RESULT`：证据足以否决 E1；不支持继续 E2-E4，也不支持 promotion。

## 2026-08-10 第二版开跑前检查

```text
scope: R0/R1/R2 class-disjoint validation
decision: PASS_READY_TO_FREEZE
formal_test_cache_loaded: false
promotion_decision: not_applicable
```

- [x] 三组只改变声明的 PSE 路径，seed、训练轮数、学习率和 batch size 相同。
- [x] pseudo-seen 与 pseudo-unseen 类别零重叠，训练图与验证图零重叠。
- [x] 训练 CE 仍只使用 pseudo-seen 类。
- [x] R2 初始输出等于 R1，修正范数不超过 `0.1`，旋转不超过约 `5.75°`。
- [x] 验证运行不登记、读取或加载正式 test 缓存。
- [x] 训练与评估逐 batch 按位置取数，不生成三份大 patch 缓存副本。
- [x] 专项 20 项、合计 35 项相关测试、语法检查、项目校验、框架账本校验和边界检查通过。
- [x] 独立 Reviewer 对最新按位置取数修复给出 `PASS`，确认指标、标签、类别轴和 test 边界未改变。

以上检查通过并冻结 clean commit 后启动 RUN-008；这里的验证结果不能冒充正式测试或 promotion 证据。尚未做进程级内存峰值测量，R0 运行时继续观察；静态引用关系已确认只长期保留一份大缓存和当前 batch 的临时小副本。
