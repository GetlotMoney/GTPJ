# 模块 Trial 历史兼容协议

本页只用于维护迁移前已经存在的 Trial/Attempt 证据。新实验必须按
`docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md` 写入所属正式框架四类账本。

模块 trial 放在：

```text
experiments/module_trials/
```

权威 idea 记录放在：

```text
idea_tree/ideas/IDEA-xxxx_short_name/IDEA.md
```

模块代码改动必须遵守：

```text
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
docs/workflow/protocols/module_template_selection.md
```

旧分支和 tag 命名带 base version：

```text
code_branch: dev/v1-idea-0001-trial-001-short-name
code_tag: trial/v1/idea-0001/trial-001
```

`code_tag` 是 trial 级代码快照，不是 attempt 级结果标签。一个 `TRIAL-xxx`
最多使用一个 trial 级 `code_tag` 来标识这条实现线；`ATTEMPT-xxx` 不创建 git tag。

其中 `v1` 表示这个旧 trial 的代码来源是 `v1` baseline tag。不得照此新建 Trial；
新的创新必须读取所属框架的 `TEMPLATE.yaml`，从其中登记的冻结母版准确提交独立开
`exp/v1/innovation/...`，不能从历史 `framework/v1` 或另一个实验继续叠代码。
`SYS-WORKFLOW-V5` 下也不得再用 `prepare-dynamic-routing-matrix` 或正式
`plan-dynamic-routing-batch` 创建新 Trial/Attempt 批次；后者只保留 `--debug-smoke` 链路探针。
如果 trial 成功，它可以被提升为新的 `v2`、`v3` 或后续版本。

必需结构：

```text
experiments/module_trials/IDEA-xxxx_short_name/
|-- IDEA.md              # trial-local pointer to the source idea file
`-- TRIAL-001_short_name/
    |-- README.md
    |-- ATTEMPTS.md
    |-- module_source.md
    |-- framework_diagram.md
    |-- implementation.md
    |-- code.diff
    |-- idea_intent_check.md
    |-- interface_precheck.md
    |-- review_round_1.md
    |-- review_round_2.md
    `-- attempts/
        `-- ATTEMPT-001/
            |-- config.yaml
            |-- manifest.yaml
            |-- result.yaml
            |-- quality_check.md
            |-- result.md
```

每个 trial 必须记录：

- source idea file
- module source、paper/code source 和论文写作解释
- base version
- base code tag
- module template family
- version-specific idea score
- framework diagram path 和 glossary
- insertion point
- input contract
- output contract
- shape invariants
- config switch 和 baseline-off path
- 如果触碰 loss/evaluation，记录对应 contract
- 最低验证证据
- code branch
- code tag
- attempts table
- best attempt id
- changed files
- implementation summary
- framework diagram with every key variable and method explained
- template selection reason and standard GZSL boundary
- Review 0 idea/source intent check
- Review 1 design/interface precheck
- Review 2 code diff pre-run review
- Review 3 post-run evidence review
- quality check decision
- result
- `trial_decision`
- `promotion_decision`

框架记录只放在 trial/root 层，不在每个 attempt 里重复。`ATTEMPT-xxx` 只记录同一实现假设下的
参数、配置、运行、结果和质量证据。只要新增或改写 module、forward、loss、evaluation、
data view、input/output、tensor flow、接口语义或模块分支逻辑，就不是普通 attempt 变体，
必须新开或更新对应 innovation / module trial，并维护 trial/root 的框架与来源记录。

## Trial/Attempt 兼容区

本节只服务已有历史目录。同一个旧 module trial 可以包含多个 attempts，但这些 attempts 必须保持在同一个实现假设内。

`ATTEMPTS.md` 保留为历史参数调优、窄范围消融、confirmation/rerun 和 debug-fix rerun 的兼容索引。

它不再是新实验的 owner-facing `formal_pending` 正式待跑表。新运行必须先登记到所属正式框架四类 `INDEX.md` 和
`PARAMETER_MATRIX.csv`，旧表只保留映射行，便于回查：

```text
attempt_id / type / run_id 或计划目录 / formal_evidence / status / evidence_state / decision / directory
```

状态为 `planned`、`pending`、`pre_run`、`pre_run_gated` 或 `ready_to_run` 的正式行，表示
这个 trial 下仍有待跑实验。已经完成、失败、替代、拒绝或只作为 debug_smoke 的行，不算正式待跑。
`.gtpj_runtime/batches/<run_id>` 只能作为 runner 缓存核对；没有 `ATTEMPTS.md` 行的 runtime
目录必须标为 `orphan_runtime_plan`，不得自动续跑。

### 参数矩阵硬规则（2026-08-04 起）

历史 `ATTEMPTS.md` 只负责告诉人“旧的这一批 Attempt 是什么”。新运行的参数表放在所属正式框架的实验目录，旧 Attempt 目录只保留原证据和映射。表里一行对应一套参数和一次 `RUN-xxx`；开跑前冻结参数，跑完只回填结果。完整列定义见 `docs/workflow/protocols/parameter_matrix_protocol.md`。

旧 Trial 内的调参和消融仍是判断模块是否有效的历史证据，但新记录统一映射成所属正式框架四类实验，因为它们回答：

```text
在同一个模块实现假设下，这个模块怎样设置才公平？
这个模块内部哪些局部因素真的有贡献？
当前 best attempt 是否能 clean confirmation？
```

新的调参、消融和确认必须分别记录到 `experiments/vX/tune/`、`experiments/vX/ablation/`
或 `experiments/vX/confirmation/`；用 `legacy_ref` 关联旧 Trial/Attempt，不再向旧目录增加第二套主账本。

推荐表格：
```text
| Attempt ID | Type | Run ID | Formal | Status | Evidence state | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
```

推荐 `Type` 取值：
```text
param_tune / ablation / confirmation / rerun / anchor_followup / debug_fix
```

每个 `attempts/ATTEMPT-xxx/` 目录应该保留自己的：
- `config.yaml`
- `manifest.yaml`
- `result.yaml`
- `quality_check.md`
- `result.md`

任何来源于旧 Attempt 的新 run 启动前，也必须先在所属正式框架的正式调参表中完成两阶段证据冻结：

## Innovation code review gate

## Module source and template gate

每个新 module trial 必须先写：

```text
module_source.md
implementation.md
```

`module_source.md` 必须能回答之后写论文时最关键的问题：

```text
这个模块来自哪里？
论文/官方代码中的机制是什么？
我们复制了什么、改造了什么、自己新增了什么？
它为什么适合当前 base version 的 GTPJ？
它使用哪个模板族，接到哪个代码位置？
switch off 为什么等价于 base version？
```

模板族必须来自：

```text
feature_adapter
fusion_gate
auxiliary_loss
sampler_or_data_view
```

如果机制触碰 evaluation、split、label mapping、class order 或 metric 语义，不能作为普通
module trial 与 baseline 直接比较；必须单独标记为 high-risk evaluation/data protocol work。

如果 module trial 会把 idea、论文机制、官方代码或本地创新改成实际代码，必须先通过
`docs/workflow/protocols/innovation_code_review_protocol.md`：

```text
Review 0 -> idea_intent_check.md
Review 1 -> interface_precheck.md
Review 2 -> review_round_1.md + interface_check.md + quality_check.md
Review 3 -> review_round_2.md + agent_summary.md
AI 交叉审核 -> 重要代码/决策改动使用 docs/workflow/protocols/ai_cross_review_protocol.md
```

这些文件是轻量审查凭证，允许进入 GitHub。完整长报告、日志和大文件仍进入 Warehouse。

### Framework diagram gate

新 module trial 的框架图是实现说明的一部分，不是可选插图。

每个新 trial 必须在 `README.md` 的 `## Framework Diagram` 中引用对应目录下的
`framework_diagram.md`。如果同时生成 HTML 视图，稳定小型 HTML 可以放在 trial 目录；
临时或较大的 HTML 进入 `GTPJ_Warehouse/diagrams/`，`framework_diagram.md` 记录
`file:///D:/...` 链接、artifact id、哈希或说明。

如果创新代码新增或改写 module、forward、loss、evaluation、data view、输入输出、
张量流向、接口语义或模块分支逻辑，
`README.md` 还必须包含 `## Code Flow Diagram`。这张图优先服务 owner 快速读懂代码实际怎么走：

- 从输入张量开始，标出图像、文本、类别原型、配置开关等入口；
- 标出新增或修改的代码模块、关键分支、gate、loss 读取点；
- 标出每个关键节点的输出，至少写清 `[B（图片/样本数量）, C（类别数量）]` 这类含义；
- 标出最终 logits / loss / metric 的出口；
- 如果代码实际流程和论文/idea 意图不同，必须在图旁写 `code_vs_intent`。

`README.md` 中的 `Code Flow Diagram` 可以先简单，但必须可读；完整变量、方法、loss
和 baseline-off 细节继续写在 `framework_diagram.md`。

`framework_diagram.md` 必须解释：

- 每个图中变量的来源、shape、含义、是否参与梯度、train/eval 差异；
- 每个图中方法/模块的代码位置、输入、输出、职责和开关条件；
- 主 forward 链路、辅助 loss 链路、teacher/target/source、detach/梯度边界；
- 每个 loss 在流程中的读取位置，不能只把 loss 名集中列在末尾；
- 代码实际流程与 idea/设计图是否一致，不一致时必须显式标注 “code vs intent”。

硬规则：

- 没有 Review 0 和 Review 1，不得开始实现；
- 没有 Review 2 通过，不得启动正式 Runner；
- 代码修复后必须重做相关 review；
- 没有 Review 3，不得把结果标成 best、promote 或主线候选；
- 如果真实多 agents 工具不可用，本任务不得冒充 `real_multi_agent`，只能阻断或降级为 debug/smoke。

### `pre-run freeze commit`

Runner 启动前，先把以下内容冻结进 Git：

- 目标 `attempts/ATTEMPT-xxx/config.yaml`；
- `ATTEMPTS.md` 中的计划行；
- 任何解释本次 run 要做什么的 task-start card 或 attempt note。

硬规则：

- Runner 必须从该 commit 后的 clean worktree 启动；
- attempt 的 `run_commit` 必须指向这个 freeze commit；
- 这个 commit 不能预先填写本次 run 的 `manifest.yaml`、`result.yaml`、`result.md`、
  `quality_check.md`、metrics 或 artifact registration。

### `post-run result commit`

attempt 完成后，写入 attempt-local：

- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`

然后在单独的 result-bookkeeping 步骤中更新 trial root summary 和索引。

attempt 完成后、result bookkeeping 被认为完成前，必须执行 checkpoint retention：

- 每个 attempt、batch 或 run 最多保留 3 个模型 checkpoint；
- 默认按 attempt 主验证指标 GZSL-H 保留 Top-3；
- 只删除 `.pth`、`.pt`、`.ckpt` 或 `.safetensors` 等模型权重文件；
- 永远不要删除 raw logs、configs、manifests、results、quality checks、runner receipts、
  events、summaries 或 Warehouse registry entries；
- 如果因为 promotion、可复现诊断或 owner 要求审计而必须保留超过 3 个 checkpoint，
  必须在 attempt 的 `quality_check.md` 中记录例外。

规则：
- `TRIAL-001` 是一个 idea 的一条实现线，不是一次训练运行。
- `ATTEMPT-001`、`ATTEMPT-002` 及后续行，是同一 trial 内的重复运行或小范围受控变化。
- 只改变 ratio、lambda、temperature、dropout、seed 或 scheduler 的数值变化，保留在同一 trial 内，类型写为 `param_tune`。
- 只用于解释当前 trial 的窄范围诊断消融，可以保留在同一 trial 内，类型写为 `ablation`。
- 用于确认当前 best attempt 的 clean rerun，可以保留在同一 trial 内，类型写为 `confirmation`。
- 如果变化变成新的实现假设、新 forward 路径或新 loss 机制，必须打开 `TRIAL-002`，不能继续扩展 `TRIAL-001`。
- trial root 的 `README.md`、`result.yaml` 和 `quality_check.md` 应该指向当前驱动决策的
  `best_attempt_id`，不要试图内联每个 attempt 的全部细节。
- trial-internal attempts 不能创建 git tags。attempt 记录使用 `best_attempt_id`、
  `attempts/ATTEMPT-xxx/`、`run_commit`、`record_commit` 和 Warehouse artifact ids。
- 只有一个 root-level attempt 的历史 trial 可以保留为 legacy evidence；本规则之后新增的 attempt
  应写入 `ATTEMPTS.md`。
- 如果真实 attempt run 在 dirty worktree 下启动，或在 attempt config 与计划 `ATTEMPTS.md`
  行冻结进 Git 之前启动，则结果不能视为 promotion-ready evidence；最多记录为 debug 或 `revise`。
- 如果 same-config、same-seed confirmation attempts 在决策边界两侧不一致，记录为
  `mixed_confirmation`。下一次 attempt 必须先做可复现诊断或确定性 confirmation，不能直接开 10-run tune sweep。
  保持模型语义冻结；只能暴露或启用 `strict_determinism`、`use_dedicated_batch_rng`、
  `batch_sampling_seed` 等控制项，并确保训练日志打印这些 runtime states。
- trial-internal 复现必须写 `repeat_type: exact_repeat`、`original_seed`、`max_attempts: 5`、
  `max_attempts_hard_cap: true`、`early_stop_on_best_hit: true`、`restore_target_H`、`near_miss_tolerance_H` 和
  `near_miss_not_restored`；原始 config、seed、代码 commit、
  data/cache、epoch schedule、batch size 和评估口径都不能改。`seed_sweep`、`score_search` 和
  `multi_seed_stability` 必须写 `not_confirmation_evidence: true`，只能作为搜索或稳定性诊断。

`trial_decision`：

```text
reject / revise / combine / promote
```

`promotion_decision`：

```text
not_applicable / promote / blocked / rejected
```

只有 `trial_decision: promote` 且 `promotion_decision: promote` 时，trial 才会进入
`docs/workflow/protocols/promotion.md` 的自动 promotion gate。
`H` 提升但证据不完整时，必须写 `revise`、`blocked` 或 `rejected`，不能写 `promote`。
单次最高 attempt 必须记录为 `best_observed_H`；复现任务还必须显式记录
`best_hit` / `best_single_H`，用于回答“有没有复现到目标分数”。只有 clean exact repeat
达到 `restore_target_H` 时才是有效还原，并停止后续 pending repeat。落入
`near_miss_tolerance_H` 但未达到目标时只能写 `near_miss_not_restored`，表示有效果、还有希望。只有 clean confirmation
或质量门要求的多 run 稳定性通过后，才能写 `stable_confirm: true`，并升级为
`confirmed_H` 或 `baseline_grade`。
`max_attempts_hard_cap: true` 表示同一候选不管有没有还原成功最多 5 次；5 次未达到目标时必须停止复现并记录 not restored / near miss。
`mixed_confirmation` 状态下，`best_observed_H` 可以保留，但 `confirmed_H` 必须保持 `pending`。

Promotion 必填证据：

- 来源正式框架 / 来源 Tag；
- trial code tag；
- trial tag 指向 README 中记录的 code_commit；
- baseline H、trial H、delta H；
- `evidence_level: baseline_grade`；
- `best_observed_H`、`confirmed_H` 和 `confirmation_status`；
- U/S/ZS、best epoch、seed；
- config 副本路径；
- 外部日志 artifact id、URI、sha256、size 和保留位置；
- class order、seen/unseen split、logits shape、metric calculation 未改变的说明；
- switch-off 等价检查；
- `experiments/vX/VERSION.md`、`experiments/VERSION_TREE.md`、`docs/PROJECT_STRUCTURE.md`
  和 `idea_tree/idea_tree.json` 更新记录。
