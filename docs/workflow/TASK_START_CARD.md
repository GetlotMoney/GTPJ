# Task Start Card

本文件是每次 GTPJ 工作开始前由 Coordinator 自动生成的启动卡。它不替代
`WORKFLOW_ROUTER.md`，而是把 Router 的判断落成一张可检查的任务单，避免每次靠口述重新解释。

Owner 不需要说“开启动卡”，也不需要自己填表。Owner 只需要用自然语言说想基于哪个版本做什么；
Coordinator 负责判断任务类型、写入边界、agents、硬门和能不能开工。

启动卡可以先写在当前对话里。纯规划阶段不要为了启动卡提前创建空 run 目录。只有当 owner 明确同意开工，
或本轮请求已经明确包含“开始/你来操作/跑这个实验”时，才把启动卡转成正式文件、分支、实验目录或运行动作。

## 0. Owner 极简输入

Owner 最简单只需要说：

```text
我想基于 <version> 跑/做 <experiment or idea>。
```

常见说法：

```text
我想基于 v1 跑一个调参实验，调 conditional_text_ratio。
我想基于 v1 做一个新模块实验，把 CLIP-A-self 接进文本 adapter。
我想基于 v1 做一个消融，把 topo loss 关掉看看。
我想基于 v1 复现一下当前 baseline。
我想查一下为什么 CUB 日志结果不对。
```

如果 owner 只说：

```text
我想基于 v1 跑 CLIP-A-self。
```

Coordinator 也必须自动判断它更像 `innovation / module trial`，然后告诉 owner 是否能开工、缺什么。

Owner 不需要提前判断：

- 是否进入 `idea_tree`；
- 应该写 GitHub 还是本地 Research/Warehouse；
- 需要哪些 agents；
- 需要哪些 hard gates；
- 分支名、目录名、artifact id 怎么写。

这些都由 Coordinator 在启动卡里给出。

## 0.1 对话先行

每次正式开工前，Coordinator 先输出一个简短判断：

```text
能不能开工：
任务类型：
基于版本：
为什么这样归类：
当前缺口：
下一步最小动作：
```

如果能开工，Coordinator 再给启动卡摘要。
如果不能开工，Coordinator 只问最关键的 1 个问题，或给出最小补齐动作。

在下面情况出现前，不要改代码、跑实验、建实验目录或登记结果：

- owner 明确说“开始”“跑”“你来操作”“按这个做”；
- 或者 owner 本轮请求本身已经明确授权实际操作；
- 或者任务只是只读检查、解释或建议，不会写文件也不会跑训练。

## 1. 使用时机

每次出现下面任一动作前，都先填写启动卡：

- 读论文并准备产出 idea；
- 修改模型、forward、loss、eval 或数据流；
- 跑 tune、ablation、confirmation 或 debug/smoke；
- 登记实验结果、日志、checkpoint 或 generated figures；
- promotion、set-current-version 或 activate-version。

如果只是普通聊天解释，可以不写完整启动卡；但只要要改文件、跑实验或登记结果，Coordinator 就必须自动写。

## 2. 最小启动卡

```yaml
task_id:
date:
owner_request:

router:
  task_type:
  enters_idea_tree:
  github_writes:
  local_writes:
  required_protocols:

version:
  base_version:
  base_code_tag:
  current_branch:
  suggested_branch:

inputs:
  paper_or_source:
  idea_id:
  config:
  dataset:
  seed:

agents:
  serial:
  parallel:
  runner_required:
  gpu_lock_required:

hard_gates:
  interface_contract:
  source_status:
  artifact_boundary:
  metric_semantics:
  promotion_gate:

expected_outputs:
  github:
  research:
  warehouse:

stop_if:
```

## 3. 必填判断

`router.task_type` 只能从 Router 支持的任务类型中选择：

```text
paper intake / idea discovery
local heuristic idea
tune
ablation
confirmation
debug / smoke
innovation / module trial
promotion
set-current-version
activate-version
progress dashboard
```

`enters_idea_tree` 使用总判断规则：

```text
实验是为了调/查/验证已有东西 -> experiments，不进 idea_tree。
实验是为了证明一个新方法值得存在 -> idea_tree + module_trials。
```

## 4. 各任务补充字段

### Paper Intake / Idea Discovery

必须记录：

- paper id 或 source id；
- Research 写入位置；
- 是否只进 inbox；
- 是否已经 source review；
- 何时允许升级成正式 `IDEA-xxxx`。

### Tune

必须记录：

- base version；
- 调哪个参数；
- old value / new value；
- 预期成本；
- 是否已经试过；
- 为什么不改变模型结构、forward、loss 语义或 eval 语义。

### Ablation

必须记录：

- disabled module / disabled factor；
- switch key；
- baseline-off path；
- interface_check 是否阻塞；
- 一次只消融的主因素。

### Confirmation

必须记录：

- 要确认的 baseline tag；
- config；
- seed；
- 数据 split、class order、label mapping；
- 预期对齐的旧结果。

### Debug / Smoke

必须记录：

- debug 目标；
- 是否会产生长期证据；
- 如果要引用结果，转入哪个正式实验目录；
- debug 结果默认不能作为有效实验结论。

### Innovation / Module Trial

必须记录：

- 正式 `IDEA-xxxx`；
- `source_type`、`source_ref`、`source_status`；
- `version_scores.<base_version>`；
- source idea file；
- module insertion point；
- input/output contract；
- shape invariants；
- baseline-off switch；
- trial branch 和 trial tag 计划。

### Promotion

必须记录：

- parent version / parent tag；
- trial code tag；
- baseline H、trial H、delta H；
- U/S/ZS、seed、best epoch；
- complete manifest/result/quality/interface evidence；
- target version；
- 是否只是生成版本账本，还是 owner 明确要求 activate-version。

## 5. 启动卡阻断条件

遇到以下情况，先停止，不跑实验：

- 工作区 dirty 且未说明哪些改动属于当前任务；
- module trial 没有正式 idea；
- idea 来源是 `unknown` 或 `unverified` 却要开 trial；
- label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚；
- raw logs、checkpoint、generated figures 会写进 GitHub；
- Runner 需要 GPU，但 lock 状态未知；
- promotion 只看 H 提升，没有完整证据链。

## 6. 最小开工输出

每次任务启动时，Coordinator 至少输出：

```text
任务类型：
是否进入 idea_tree：
GitHub 写入：
本地写入：
必读协议：
启用 agents：
硬门：
当前阻塞：
```

这段输出就是后续 agent 的共同入口。
