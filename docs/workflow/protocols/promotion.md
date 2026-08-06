# 正式框架晋级协议

晋级的意思是：一个创新候选已经通过确认和质量检查，可以登记为新的同级正式框架。
它会得到独立的 `FRAMEWORK-VY`、长期分支 `framework/vY` 和冻结 Tag `vY`，但不会成为来源框架的子目录，也不会自动切换当前运行入口。

纯调参、纯消融、纯确认以及尚未确认的创新都不能晋级。它们只能继续留在所属正式框架的四类实验账本中。

## 1. 复现门槛

从 2026-06-29 起，候选要用于正式晋级，必须同时满足：

- 复现记录包含 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、`max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H` 和 `near_miss_not_restored`；
- 同一候选最多做 5 次精确复跑；5 次仍未达到 `restore_target_H` 时，必须收口为未还原或接近但未还原；
- 每次复跑都有有效的 U、S、H、ZS、随机种子和最佳轮次；
- 代码、配置、随机种子、数据、缓存、训练轮次、批大小和评估方式保持一致；
- 至少一次干净复跑达到 `restore_target_H`；接近但没有达到不能算还原；
- 类别顺序、已见/未见划分、标签映射、输出形状和指标计算没有改变，或已经单独审计并说明。

达到上述条件后可以记录 `best_hit`。如果正式结论还要求稳定性，必须额外报告同一配置的均值、最小值、最大值和波动范围。
`seed_sweep`、`score_search` 和 `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，不能冒充精确复跑。

## 2. 晋级不会自动激活代码

晋级只登记新的同级正式框架和本地冻结 Tag。切换当前运行配置属于另一项动作，只有用户明确要求执行 `activate-version vY` 时才能进行。
没有切换时必须记录：

```text
active_main_update: not_activated
```

## 3. 进入晋级检查的字段

来源创新的结果必须记录：

```text
promotion_decision: promote
promote_to: vY
evidence_level: baseline_grade
confirmation_status: confirmed
```

`promote_to` 必须和即将登记的 `framework_version` 完全一致。例如目标是 `FRAMEWORK-V6`，这里必须写 `v6`，不能写 `v7` 或留空。

如果用户在历史时期接纳了证据不完整的框架，只能保留为明确的历史状态，例如 `legacy_owner_accepted_unconfirmed`；一般实验激活但未确认时写 `owner_activated_unconfirmed`。两者都不能伪装成按本协议确认通过的新框架。

## 4. 必须全部通过的检查

- 来源创新明确记录 `derived_from_framework`、来源 Tag、分支、提交、配置、命令、指标和外部证据；
- 来源创新确实改变框架或代码语义，纯调参不能晋级；
- 结果不是只有一次偶然高点；
- 运行来自干净提交，`dirty_state: clean` 且 `git_dirty: false`；
- U、S、H、ZS、随机种子、最佳轮次和比较基准齐全；
- `best_observed_H`、`confirmed_H` 和 `confirmation_status` 分开记录；
- 外部产物的编号、路径、sha256 和大小齐全；
- `quality_check.md` 没有阻断问题；
- 目标配置可以冻结到 `config/versions/vY.yaml`；
- 新编号尚未被任何正式框架、分支或 Tag 占用；
- `promote_to`、`framework_version`、`framework_branch` 和 `framework_tag` 指向同一个 `vY`；
- 创建 Tag 和任何经用户授权的推送之前，工作区必须干净。

任一检查失败时，不得创建正式框架，必须记录：

```text
promotion_decision: blocked
```

## 5. 检查通过后的本地动作

1. 锁定已确认的候选代码提交，确认它确实来自所属正式框架的创新实验。
2. 分配一个未使用的新编号 `vY`。
3. 从已确认提交建立长期分支 `framework/vY`。
4. 在总管理分支登记 `experiments/vY/`，至少包含 `framework.yaml`、`VERSION.md`、`EXPERIMENTS.md` 和下面四类同级账本：

```text
experiments/vY/
├─ tune/INDEX.md
├─ ablation/INDEX.md
├─ innovation/INDEX.md
└─ confirmation/INDEX.md
```

5. 把配置冻结到 `config/versions/vY.yaml`；如需保留首次正式成绩，可在 `experiments/vY/baseline/` 保存证据，但它不能替代四类账本。
6. 在来源框架的创新索引中，把 `promoted_framework` 回填为 `FRAMEWORK-VY`；原创新目录继续保留为来源证据。
7. 在新框架的 `framework.yaml` 写入 `registry_level: formal_peer`、`derived_from_framework` 和 `promoted_from_experiment`。
8. 更新 `experiments/FRAMEWORK_TREE.md`、`experiments/VERSION_TREE.md`、总实验登记表和项目状态。
9. 运行框架台账、工作流一致性、边界和测试检查。
10. 提交治理材料，并在已冻结的正式代码提交上创建本地 Tag `vY`。
11. 除非用户在验证后明确要求，否则不得推送分支或 Tag。
12. 除非用户明确要求，否则不得执行 `activate-version vY`。

## 6. 每个新正式框架必须记录

```text
framework_id:
framework_version:
registry_level: formal_peer
derived_from_framework:
promoted_from_experiment:
framework_branch:
framework_tag:
framework_commit:
governance_source_commit:
source_legacy_ref:
origin_status:
change_type:
config_snapshot:
baseline_result:
known_risks:
confirmation_requirement:
evidence_level:
best_observed_H:
confirmed_H:
confirmation_status:
active_main_update: not_activated | activated_by_owner | owner_accepted_current_tag
```

## 7. GitHub 边界

本协议只允许在检查通过后创建本地文件、提交、长期分支和本地 Tag。只有用户在验证后明确要求（`explicitly asks`）才允许推送；否则硬规则是 `must not push`。即使用户批准推送，也仍然禁止强制推送、删除远端引用和改写历史。
