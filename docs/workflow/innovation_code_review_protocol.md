# Innovation Code Review Protocol

本文定义 idea / 创新 / 模块代码改动进入实验前后的强制多 agents 审查流程。

核心规则：

```text
只要一个 idea、创新机制或 module trial 会改变代码路径，就必须使用 real_multi_agent，
并且必须经过多轮独立审查后才能进入正式训练、best 选择或 promotion。
```

本协议不替代 `idea_tree_protocol.md`、`module_trial_protocol.md` 或
`code_interface_contract.md`。它只补充一条更硬的闸门：从创意到代码实现之间必须有可审计的
多 agents 复核。

## 1. 强制触发条件

以下任一情况触发本协议：

- 新 `IDEA-xxxx` 将被实现成代码；
- 新 module trial、adapter、forward path、loss、eval、data flow 或 scoring 改动；
- 任何会影响 label mapping、seen/unseen split、class order、logits shape 或 metric semantics 的改动；
- 参考论文、补充材料、项目页或官方代码实现新机制；
- trial 内 attempt 超出原 implementation hypothesis，需要新开 trial；
- 实验结果将用于 best 选择、主线候选、promotion 或论文实验路线；
- owner 明确要求多 agents、多次审查或独立 review；
- 结果异常、掉点明显、解释存在争议，且需要回查代码是否符合创新用意。

如果当前环境没有真实 sub-agent / multi-agent 工具，不能把顺序执行冒充为
`real_multi_agent`。这类任务必须阻断正式 run、promotion 或 best 结论，除非 owner 明确接受
本次只作为 debug/smoke 降级。

正式创新审查默认使用 workflow-scoped `temporary_subagent`。如果某个角色需要跨多个 workflow 连续追踪，才启用 `persistent_thread`，并在 task-start card 和 `agent_summary.md` 写明 thread id 或可见 label。无论使用哪种活上下文，正式结论必须写入 review 文件、`agent_summary.md`、result、quality 或 artifact evidence。

## 2. 最小审查轮次

每个创新代码改动至少包含四轮审查：

```text
Review 0: idea/source-intent review
Review 1: design/interface review
Review 2: code diff pre-run review
Review 3: post-run evidence review
```

### Review 0: Idea / Source Intent

Reader/Planner 与 Coordinator 检查：

- `IDEA.md` 或 Research 长版 idea 是否存在；
- `source_type`、`source_ref`、`source_status` 是否明确；
- 如果来自论文或官方代码，是否记录 paper id、official code URL、clone commit 和排除的数据/权重范围；
- hypothesis、implementation_scope、risk 和 `version_scores.<base_version>` 是否足以启动 trial；
- 本次改动是一个可复用机制，还是普通参数尝试；
- expected module behavior 是否写清楚。

输出文件：

```text
idea_intent_check.md
```

结论只能是：

```text
allow / blocked / revise
```

### Review 1: Design / Interface

Interface Checker 在 Implementer 写代码前检查：

- module insertion point；
- input/output contract；
- shape invariants；
- config switch 和 baseline-off path；
- loss/eval/data flow 是否改变；
- label mapping、seen/unseen split、class order、logits shape、metric semantics 是否受影响；
- writable file set 是否明确；
- 最小 smoke / shape / backward / switch-off 验证计划。

输出文件：

```text
interface_precheck.md
```

如果本轮为 `blocked`，Implementer 不得开始代码改动。

### Review 2: Code Diff Pre-Run

代码完成后、正式训练前，至少由以下只读 reviewers 独立检查：

- Interface Checker：代码是否满足接口契约和 baseline-off 等价；
- Quality Checker：diff 是否越界、config 是否完整、最小验证是否可执行；
- Reviewer：实现是否符合 idea/source intent，是否有明显遗漏或污染风险。

输出文件：

```text
review_round_1.md
interface_check.md
quality_check.md
```

任一角色给出 blocking issue 时，Runner 不得启动正式训练。修复后必须重新记录一轮 review。

### Review 3: Post-Run Evidence

训练或验证结束后，至少由以下角色独立检查：

- Log Analyst：只解析日志事实，不补造指标；
- Quality Checker：检查 artifact、hash、size、manifest、result、quality evidence；
- Result Analyst：判断 keep / revise / reject / rerun / promote 是否被证据支持；
- Reviewer：检查结论是否过度声明，是否仍符合最初 idea intent。

输出文件：

```text
review_round_2.md
agent_summary.md
```

如果结果要进入 promotion，还必须转入 `promotion.md` 的 promotion gate。

## 3. 临时 agents 与长期 agents

长期 agent 由文件化角色身份和历史凭证构成：`profile.md`、`memory.md`、by-experiment 调用规则、review 文件、`agent_summary.md` 和 issues。`persistent_thread` 只是跨 workflow 的可选活上下文，不是正式证据源。

临时 sub-agent 是本轮 innovation workflow 的默认独立活上下文。Coordinator 启动临时 agent 时必须显式传入：

- 对应 `shared_roles/<role>/profile.md`；
- 对应 `shared_roles/<role>/memory.md`；
- `docs/workflow/agents/by_experiment/innovation/agents/README.md`；
- 如启用 persistent thread，则传入对应 thread id / thread label；否则写明本轮使用 workflow-scoped temporary context；
- 本次 task-start card；
- 本轮需要审查的具体文件列表；
- 期望输出文件与结论格式。

临时 agent 结束后，经验只在下列位置持久化：

```text
agent_summary.md
review_round_*.md
docs/workflow/issues/YYYY-MM-DD-*.md
shared_roles/<role>/memory.md
workflow/gtpj_workflow.py helper 或 sync check
```

临时 agent 的隐藏上下文不能作为实验证据。进入 `result.yaml`、`quality_check.md`、promotion evidence 或正式结论前，
必须回到当前 repo、Research、Warehouse artifact 或日志重新验证。

正式 best、promotion 或 owner 明确要求多 agent 时，不能只保留临时 agent 的对话结论；必须把结论收口到文件化 evidence。若启用了 persistent thread，也可以同步一份可见总结，但不能替代文件证据。

## 4. Writer / Reviewer 边界

Implementer 是同一代码路径的唯一 writer。

默认只读角色：

- Reader/Planner；
- Interface Checker；
- Quality Checker；
- Reviewer；
- Runner，除 Warehouse raw artifacts 和 runtime state 外；
- Log Analyst；
- Result Analyst。

Coordinator 是最终 GitHub 账本 writer，但不得绕过 reviewer 结论。

禁止事项：

- 多个 agents 同时改同一模型、loss、eval 或 dataset 文件；
- Reviewer 自己修代码再给自己通过；
- Runner 在 pre-run review 仍有 blocking issue 时启动正式训练；
- 代码修复后沿用旧 review 结论；
- 用单 agent 顺序检查冒充 `real_multi_agent`；
- 把未验证的 memory-derived fact 写入正式结果。

## 5. 正式 run 前硬阻断

任一条件不满足时，正式 run、best 选择和 promotion 均必须阻断：

- 没有正式 idea/source 记录；
- 没有 `idea_intent_check.md`；
- 没有 `interface_precheck.md`；
- task-start card 的 `agents.activation_mode` 不是 `real_multi_agent`；
- `required_real_agents` 没有列出必须独立执行的角色；
- Implementer diff 超出声明的 writable file set；
- baseline-off switch 或 switch-off 等价不清；
- seen/unseen、class order、label mapping、logits shape 或 metric semantics 不清；
- Review 2 存在 blocking issue；
- 修代码后没有重新 review；
- 没有 pre-run freeze commit；
- worktree 不干净却启动正式 run。

## 6. 推荐文件布局

module trial root 推荐保留：

```text
implementation.md
code.diff
idea_intent_check.md
interface_precheck.md
review_round_1.md
interface_check.md
quality_check.md
review_round_2.md
agent_summary.md
```

attempt-local 目录仍按 `module_trial_protocol.md` 保存：

```text
attempts/ATTEMPT-xxx/config.yaml
attempts/ATTEMPT-xxx/manifest.yaml
attempts/ATTEMPT-xxx/result.yaml
attempts/ATTEMPT-xxx/result.md
attempts/ATTEMPT-xxx/quality_check.md
```

长报告、完整日志、checkpoints 和大文件仍写入 Warehouse，只在 GitHub 记录 artifact id / URI / hash / size。

## 7. 结论格式

每轮 review 至少记录：

```text
review_round:
role:
agent_instance_mode:
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
inputs_checked:
independence_scope:
findings:
blocking_issues:
non_blocking_issues:
decision: allow / blocked / revise
evidence_refs:
memory_used:
memory_sources:
verified_against_current_repo:
```

`agent_summary.md` 必须汇总四轮 review 的结论，并说明是否有临时 agents、长期角色 thread 是否复用、长期角色记忆是否加载、
哪些文件被独立审查、哪些 blocking issue 已解决。

## 8. 与其他协议的关系

- `idea_tree_protocol.md` 决定 idea 是否足以启动 trial；
- `module_trial_protocol.md` 决定 trial / attempt 如何落账；
- `code_interface_contract.md` 决定代码接口是否有效；
- `agent_orchestration.md` 决定 agents 如何启用；
- `agent_report_policy.md` 决定 agent evidence 如何保存；
- 本协议决定 idea 到代码改动之间是否经过足够的独立审查。
