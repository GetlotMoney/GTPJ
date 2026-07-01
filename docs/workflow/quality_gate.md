# 质量门

普通实验的 `quality_check.md` 是证据完整性检查；baseline promotion 的
`quality_check.md` 是强制门。自动 promotion 的完整规则见 `docs/workflow/promotion.md`。

换句话说：

- tune、ablation、confirmation：`quality_check.md` 帮助记录证据是否完整。
- module trial、ablation 或 tuned configuration 提升为正式 `vX`：必须通过 promotion quality gate。

全局硬门：接口、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 任一不清，实验结果无效。该结果只能标记为 `blocked`、`rerun` 或 `rejected`，不得标记为 `keep` 或 `promote`，也不得作为 baseline 可比证据。

证据等级硬门：任何结果必须先标明 `evidence_level`，再决定用途。

```text
debug_smoke          环境/流程排障；formal_evidence=false，不得进入 keep/best/promotion/confirmation。
quick_local          本地快速复线或趋势观察；不得 promotion。
valid_single_run     单次完整证据；可记录 best_observed_H，但仍需确认。
confirmation_grade   clean confirmation 证据；可确认目标结果。
baseline_grade       可作为稳定 baseline 的证据。
```

只有 `baseline_grade` 才允许写成稳定 baseline。只有 `valid_single_run` 时，可以登记
`best_observed_H` 和 owner 选择的当前主线，但必须同时写 `needs_confirmation`、
`owner_activated_unconfirmed` 或 `provisional`。不得把一次最高 H 结果直接表述为 confirmed baseline。

复现状态硬门：任何状态检查、结果比较、promotion 或 tag 前，先检查 `baseline_repro_status`
或运行 `python workflow/gtpj_workflow.py repro-status --version <vX>`。若输出
`verdict: needs_confirmation`，该版本只能作为 active code / unconfirmed reference，不能作为
baseline-grade 证据，也不能让 agent 靠记忆把 `best_observed_H` 写成 `confirmed_H`。

运行实验前：

1. 检查 Git status。
2. 确认临时分支来源符合实验类型，并记录正确的 `base_code_tag` 和 `branch_source`。
   当前版本实验从当前 `main` 切出；历史版本 tune、ablation、confirmation 可以从 `vX` tag
   开只运行代码的临时分支，跑完后回当前 `main` 入账，不把该运行分支合并进 `main`。
   module trial 和 promotion 分支仍从当前 `main` 切出，必要时只恢复代码层到目标 tag。
3. 确认 config 改动只作用于当前实验。
4. 确认模块改动由 off switch 控制。
5. 如果有模块代码改动，确认满足 `docs/workflow/code_interface_contract.md`。
6. 确认外部日志 artifact URI、hash、size 和结果路径已经准备好。
7. 确认 raw logs、checkpoint、generated figures 不会写入 GitHub。
8. 确认实验结束后的 checkpoint retention 计划：模型 checkpoint 最多保留 3 个；若需要例外，
   必须在 `quality_check.md` 写明原因。

模块接口检查：

- baseline-off path 能回到选定 base version 的行为；
- input 和 output 的 tensor shape 已记录；
- 除非明确记录为接口变更，否则 logits shape 和 class order 不变；
- 新 loss 默认关闭，并由 config 权重控制；
- 除非 trial 明确就是 evaluation 实验，否则 evaluation 语义不变；
- seen/unseen split、label mapping、class order、logits shape 和 metric calculation
  不允许静默改变；
- 训练前已记录最低验证证据。

如果上述任一项无法确认，Runner 必须拒跑；如果是在运行后发现，Result Analyst 必须把结果降级为 `blocked`、`rerun` 或 `rejected`。

## Promotion Quality Gate

任何实验想提升为正式 `vX`，必须先记录：

```text
promotion_decision: promote
promote_to: vX
```

随后自动执行 `docs/workflow/promotion.md` 的硬门。必须满足：

- [ ] 父版本明确：`parent_version`、`parent_tag`、`base_code_tag` 已记录；普通实验可按
  `docs/workflow/experiment_protocol.md` 的 promotion 字段映射读取。
- [ ] 来源 commit/tag 明确：module trial 的 trial tag 指向 README 中记录的 `code_commit`；
  普通实验或 tuned configuration 必须记录 `run_commit`，并可映射为 `code_commit`。
- [ ] 指标明确：父版本 H、实验或 trial H、delta H、U/S/ZS、best epoch 已记录。
- [ ] 证据等级明确：`evidence_level` 至少是 `confirmation_grade`；正式 baseline 必须是
  `baseline_grade`，或显式标成 owner provisional activation。
- [ ] 干净确认明确：结果来自 clean pre-run freeze commit，`dirty_state: clean` 且
  `git_dirty: false`；否则只能记为 best_observed/debug，不能 promotion。
- [ ] 结果字段明确：`best_observed_H`、`confirmed_H`、`confirmation_status` 已区分记录。
- [ ] 对照明确：同 seed 对照已记录；高风险改动已说明是否需要多 seed。
- [ ] 配置明确：trial config 和新版本 config 路径已记录。
- [ ] 日志明确：外部日志 artifact id、URI、sha256、size 和保留位置已记录。
- [ ] checkpoint 保留明确：模型 checkpoint 最多保留 3 个，或质量检查写明例外理由。
- [ ] 口径不变：class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] 接口不乱：input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] 标注不乱：label mapping、seen/unseen split 和 class order 与 baseline 可比。
- [ ] GitHub 边界通过：没有新增 raw logs、checkpoint、generated figures 或 cache。
- [ ] 关闭等价：switch off 能回到 `parent_version` 行为。
- [ ] 账本完整：VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] 创意树同步：`idea_tree/idea_tree.json.current_version` 和必要的 `version_scores.vX` 已更新。
- [ ] baseline tag 准备打在包含正式版本代码和版本材料的明确 commit 上；该 commit 不必是当前
  `main` commit。
- [ ] 最终决策：`promotion_decision: promote`，且硬门未发现 blocking issue。

只满足 `H` 提升，但上面任一关键项缺失时，不允许 promotion；应记录
`promotion_decision: blocked` 或 `promotion_decision: rejected`。

clean confirmation 失败时，不回滚或抹掉原 run；必须把原 run 降级为 `valid_single_run`
或 `needs_confirmation`，并把 promotion 阻断原因写入 `quality_check.md` 和结果索引。

未来工作流可以使用的决策值：

```text
not_applicable
promote
blocked
rejected
```

风险等级：

- `TUNE-LITE`：只改 config 的 tuning。
- `STANDARD`：ablation、dataset transfer 或低风险 switch。
- `STRICT`：新模块代码、新 loss、forward path、data flow 或 evaluation 变化。

OpenClaw 和 Codex 未来应写出兼容的 `quality_check.md` 文件。
