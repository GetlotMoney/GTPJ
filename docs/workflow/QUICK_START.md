# GTPJ Workflow Quick Start

本文件是 owner 日常入口。它把完整 workflow 压成几句人话口令；底层
`WORKFLOW_ROUTER.md`、`TASK_START_CARD.md`、agent、artifact、quality 和 promotion
规则仍然有效，由 Coordinator 自动展开。

新框架和新实验的结构以 `FRAMEWORK_EXPERIMENT_STANDARD.md` 为准：新模块先建立
`Vx-INNOVATION-xxx` 候选，冻结候选后再做候选内部调参、消融和确认；旧 `module trial` 不再是新入口。
本发布中的旧 helper 若仍输出 `trial` 路径，只能当历史兼容提示，不能据此创建新实验。
当前发布版 helper 的 `new-experiment` 还带有“分支必须包含 main”的旧限制，不能正确创建从冻结模板或冻结候选开始的正式实验；在独立 helper 升级审核通过前，它只能用于历史兼容和只读检查。

只想预览某句口令会怎样展开时，可以运行只读 helper：

```bash
python workflow/gtpj_workflow.py start --phrase "开新模块"
python workflow/gtpj_workflow.py repro-status --version v3
```

这些命令只输出 mini 启动卡或复现状态，不写文件、不建分支、不跑训练。

## 1. 人话口令

| 你说 | 默认含义 |
|---|---|
| `查状态` | 只读检查仓库、当前分支、active baseline 复现状态、队列和阻塞项，不改文件。 |
| `复现` | 默认先判定当前 active baseline 是否已复现；未要求正式确认时走最快 `quick_local` 或准备路径。 |
| `调参` | 默认基于当前 active baseline 生成最多 3 个候选；执行前再确认具体参数和成本。 |
| `消融` | 默认判断是版本级消融还是某个冻结候选内部的窄消融，并先检查接口门。 |
| `开新模块` | 默认基于当前 active baseline，从该版本 selected ready idea 队列建立新的 `Vx-INNOVATION-xxx` 候选，不 push。 |
| `开下一个新模块` | 明确按当前版本 selected 队列继续推进下一个 ready idea。 |
| `试这个：<一句话想法>` | 把一句话想法路由为 local heuristic idea、idea inbox 或可开正式创新候选的想法。 |
| `继续上一个` | 不新开 idea，继续当前创新候选或实验；旧 trial/attempt 只读回查。 |
| `别问，给我三个候选` | 只读 `idea_tree` / Research，列 3 个可开候选，不改代码。 |
| `升版本` | 检查 promotion gate；只有证据完整且记录明确时才进入 promotion。 |
| `切版本` | 只在 owner 明确要求时执行 activate-version；set-current-version 只切 idea_tree 视图。 |

## 2. 可复现状态优先

任何状态检查、结果比较、promotion 或打 tag 前，Coordinator 必须先查 baseline 复现状态：

```bash
python workflow/gtpj_workflow.py repro-status --version <vX>
```

判定规则：

```text
confirmation_status: confirmed 且 confirmed_H 不是 pending -> 可以当 confirmed baseline。
只有 best_observed_H、confirmed_H=pending 或 status=owner_activated_unconfirmed -> 只能当未确认参考。
```

mini 启动卡的 `gates` 必须包含 `baseline_repro_status`。未确认版本可以作为 active code 和
实验起点，但不能被说成 confirmed baseline，也不能仅凭它阻断或通过 promotion/tag。

## 3. `开新模块` 的默认展开

当 owner 只说 `开新模块` 或 `开下一个新模块` 时，Coordinator 默认执行：

```text
1. 只读检查仓库状态、active baseline 和当前分支。
2. 读取当前 active baseline 的 idea 视图，例如 idea_tree/versions/v3.md。
3. 找 selected 且无 blocker 的最高优先级 idea。
4. 检查 idea_id、source/ref/status、version_scores、hypothesis、scope、risk 是否齐全。
5. 输出 mini 启动卡，说明能不能开工和下一步最小动作。
6. 如果能开工，从所属框架的冻结模板创建 `Vx-INNOVATION-xxx` 分支和实验记录，先实现并冻结完整候选提交。
7. 进入代码审查、候选内部调参/消融/确认、Warehouse artifact 和 GitHub 账本闭环；不允许创建 `dev/...` 或新的 trial 目录。
8. 不 push，除非 owner 明确说提交推送。
```

`开新模块` 默认基于 `docs/PROJECT_STATUS.md` 和所属框架 `TEMPLATE.yaml` 所登记的当前研究框架；不能从旧示例中的 `v3`、旧 `dev/...` 或旧 trial 直接继续。

## 4. Ready Idea 条件

可以被 `开新模块` 自动选择的 idea 必须同时满足：

```text
status 或队列状态: selected / ready
blockers: empty
source_type: paper / user / observation / cross_domain / hybrid
source_status: verified 或 local_heuristic
source_ref: not empty
version_scores.<active_version>: exists
hypothesis: not empty
implementation_scope: not empty
risk: not empty
```

如果没有 ready idea，Coordinator 只能问一个最小问题，例如：

```text
当前框架没有可直接开工的 selected idea。要我先列 3 个候选，还是把你的想法登记成 local heuristic idea？
```

## 5. Owner 不需要说的内部词

下面这些都是后台动作，不应该要求 owner 口头指定：

```text
基于 v3
允许改代码
创新候选
候选内部验证
real_multi_agent
Review 0-3
artifact boundary
pre-run freeze
branch name
artifact id
```

Coordinator 必须自动判断这些内容，并在 mini 启动卡里用简短语言说明。

## 6. 最快合规路径

默认选择最快但仍合规的路径：

- 只读、查状态、解释、候选建议：`role_only`。
- frozen config 单次复现或 debug/smoke：`role_only`，除非结果要进入正式 best/promotion。
- 新模块、forward/loss/eval/data 语义变化、promotion、争议结果：`real_multi_agent`。
- 需要 `real_multi_agent` 时，并行执行只读审查角色；Runner、Implementer、Coordinator 仍串行。
- 任何时候都不能把隐藏上下文或口头印象当正式证据。

## 7. 收口回答

每次完成后，Coordinator 用短格式汇报：

```text
做了什么：
写了哪里：
验证了什么：
没有做什么，为什么：
下一步：
```
