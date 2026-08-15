# 正式框架晋级协议

晋级的意思是：一个创新候选已经通过确认、质量检查和代码瘦身，并由 owner 明确确认，可以把候选最终 commit 登记为新正式框架。
它会得到 `framework/vY` 与冻结 Tag `vY`，两者精确指向同一 commit；正式框架本身就是最简模板，`TEMPLATE.yaml` 只绑定这一个代码身份。它在 GitHub 分支列表中是直接入口，同时保留来源框架到 VY 的真实 Git 血缘。

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

## 2. 晋级不会移动 main 或自动激活代码

晋级只登记新正式框架和本地冻结 Tag，不会移动默认冻结的 `main`。切换当前运行配置属于另一项动作，只有用户明确要求执行 `activate-version vY` 时才能进行。
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
- owner 接纳已经写入 `OWNER_DECISION.yaml`，并由 `owner_decision_ref` 精确绑定目标框架、来源实验与候选最终 commit；
- 候选代码已删除新框架不使用的旧路径，并通过新旧行为对照；
- `framework/vY` 与 `vY` 指向同一个干净、最简、可运行的候选最终提交；
- 总管理提交中的 `TEMPLATE.yaml` 准确登记 `FRAMEWORK-VY`、`framework/vY`、`vY` 和该 commit；
- 若来源是已有框架，Git 必须证明来源框架 commit 是候选最终 commit 的祖先；若来源是 `main`，必须记录并验证实际 `derived_from_commit`；
- 创建 Tag 和任何经用户授权的推送之前，工作区必须干净。

任一检查失败时，不得创建正式框架，必须记录：

```text
promotion_decision: blocked
```

## 5. 检查通过后的本地动作

1. 确认来源创新已经通过，并由 owner 明确确认晋级。
2. 删除该框架不用的旧实现、旧开关和失效配置，用同一真实最小样例完成新旧行为对照；对照没通过就停止晋级。
3. 锁定瘦身后的候选最终 `commit:<sha>`，验证它与来源框架或 `main` 的真实 Git 祖先关系。
4. 分配一个未使用的新编号 `vY`，在该 commit 创建 `framework/vY` 与 `vY`；二者冻结后不得移动。
5. 在治理分支登记 `experiments/vY/OWNER_DECISION.yaml`，记录 `decision: accepted`、目标框架、来源实验、候选最终 commit 和 owner 明确接纳来源；
6. 登记 `experiments/vY/`，至少包含 `framework.yaml`、`TEMPLATE.yaml`、`VERSION.md`、`EXPERIMENTS.md` 和下面四类账本：

```text
experiments/vY/
├─ tune/INDEX.md
├─ ablation/INDEX.md
├─ innovation/INDEX.md
└─ confirmation/INDEX.md
```

7. `TEMPLATE.yaml` 写入 `template_id: FRAMEWORK-VY`、`template_status: canonical`、`framework/vY`、`vY` 和准确 commit；`framework.yaml` 写入 `owner_decision_ref`；治理登记提交与框架代码 commit 分开记录。
8. 把配置冻结到 `config/versions/vY.yaml`；如需保留首次正式成绩，可在 `experiments/vY/baseline/` 保存证据，但它不能替代四类账本。
9. 在来源框架的创新索引中，把 `promoted_framework` 回填为 `FRAMEWORK-VY`；完全独立框架则记录 owner 确认与 `main` 起点。原创新目录继续保留为来源证据。
10. 在新框架的 `framework.yaml` 写入 `registry_level: formal_peer`（表示可直接选择）、`derived_from_framework`、`promoted_from_experiment` 和准确 commit；该字段不抹除继承树。
11. 更新 `experiments/FRAMEWORK_TREE.md`、`experiments/VERSION_TREE.md`、总实验登记表和项目状态。
12. 运行框架模板、框架台账、工作流一致性、边界和测试检查。
13. 除非用户在验证后明确要求，否则不得推送分支或 Tag。
14. 除非用户明确要求，否则不得执行 `activate-version vY`。

## 6. 每个新正式框架必须记录

```text
framework_id:
framework_version:
registry_level: formal_peer
derived_from_framework:
derived_from_commit:  # 仅 main 直接来源必填
promoted_from_experiment:
framework_branch:
framework_tag:
framework_commit:
governance_source_commit:
owner_decision_ref:
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
