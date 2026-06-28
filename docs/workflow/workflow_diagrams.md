# Workflow Diagrams

本文规定 GTPJ 流程图放在哪里、必须画什么、什么时候更新。

## 当前结论

当前仓库在本规则落地前没有独立的流程图文件，也没有稳定的 Mermaid / draw.io 版本流程图。已有的是文字版版本树，例如：

```text
experiments/VERSION_TREE.md
docs/workflow/versioning.md
```

以后不要只靠文字描述版本和实验链路。每个正式版本、每个会改变代码语义的 module trial，都必须有轻量流程图。

## 存放规则

GitHub 中的权威流程图优先使用 Markdown + Mermaid，原因是：

- 可 diff。
- 可 review。
- 可和版本账本一起提交。
- 不依赖外部图片文件。

推荐位置：

```text
experiments/vX/VERSION.md
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/README.md
docs/workflow/workflow_diagrams.md
```

复杂图可以单独放：

```text
experiments/vX/flow.md
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/flow.md
```

生成出来的 PNG、HTML、临时截图默认不是权威证据。除非它是小型稳定文档资产，否则不要提交到 GitHub；大图、渲染图和临时可视化进入 `GTPJ_Warehouse`，GitHub 只记录引用。

## Owner 可视化交付

仓库中的权威流程图仍优先使用 Markdown + Mermaid，方便 diff、review 和随账本提交。

但给 owner 解释模型框架、代码路径、实验链路或流程差异时，默认再生成一个可本地打开的 HTML 视图，并在回复中给出 `file:///D:/.../xxx.html` 形式的绝对本地链接，例如：

```text
file:///D:/backup/Documents/xwechat_files/wxid_gv04544qttp922_8f75/msg/file/2026-06/FRAMEWORK_DIAGRAM_BASELINE(2).html
```

HTML 视图用于阅读和沟通，不自动成为实验事实源。若该 HTML 需要长期留档，优先放入 `GTPJ_Warehouse/diagrams/` 或对应外部 artifact 目录；GitHub 只记录轻量引用、哈希或说明。

## Framework Diagram

每个新的 innovation / module trial 必须在对应 trial 目录下保留框架图记录：

```text
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/framework_diagram.md
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/framework_diagram.html  # 可选，小型稳定 HTML
```

如果 HTML 太大、包含临时截图、或只是沟通视图，HTML 放入 `GTPJ_Warehouse/diagrams/`，
trial 目录中的 `framework_diagram.md` 只记录本地 `file:///D:/...` 链接、artifact id、哈希或说明。

框架图不能只写模块名。每张创新框架图必须解释清楚：

- 主 forward 链路：从原始输入到最终 logits，每个张量在哪一步产生、被谁消费。
- 辅助训练链路：每个 loss 的输入、target、teacher/source、权重、detach/梯度边界。
- 每条箭头的语义：数据流、监督信号、只读引用、还是配置/控制信号。
- 每个关键变量：变量名、来源、shape、dtype/device 如 relevant、含义、是否参与梯度、train/eval 差异。
- 每个方法/模块：代码位置、输入变量、输出变量、职责、开关条件、baseline-off 行为。
- 配置开关：默认值、trial 覆盖值、关闭后是否回到 base version。
- 类别与评估边界：class order、seen/unseen split、logits shape、metric calculation 是否改变。
- 与 intent 的差异：如果代码实际流程和 idea/设计图不同，必须用显式 “code vs intent” 标注。

视觉规范：

- 线不能覆盖文字或穿过节点主体；必要时转弯。
- 不同语义的线不能重合；如果必须靠近，使用不同路径和图例。
- loss 不要全部堆在末尾；应该嵌入它实际读取张量的位置。
- 同一模块内部的子方法要分层，不要把所有方法都塞进一个大框里。

## 必填图

每个正式版本 `experiments/vX/VERSION.md` 必须包含：

```text
## Version Flow
```

图里至少标出：

- `parent_version`
- `parent_tag`
- `based_on_trial`
- `source_attempt` 或 baseline source
- `code_tag`
- `evidence_level`
- `confirmation_status`
- 是否是当前 owner active mainline

每个新 module trial `README.md` 必须包含：

```text
## Trial Flow
## Framework Diagram
```

图里至少标出：

- idea/source
- Review 0
- Review 1
- implementation
- Review 2
- pre-run freeze commit
- Runner
- Warehouse artifact registration
- Review 3
- final decision

`## Framework Diagram` 至少必须包含：

- `framework_diagram.md` 的相对路径。
- 如果有 HTML 视图，记录 `file:///D:/...` 或 Warehouse artifact 引用。
- 变量词典：所有图中变量的来源、shape 和含义。
- 方法词典：所有图中方法/模块的代码位置、输入、输出和职责。
- loss 嵌入说明：每个 loss 在哪条链路读取哪些变量，不允许只在末尾列 loss 名。
- code vs intent 说明：代码实现与原始 idea/讨论图是否一致。

## 总流程框架

```mermaid
flowchart TD
  Owner["Owner request"] --> Router["WORKFLOW_ROUTER.md"]
  Router --> Card["TASK_START_CARD.md"]
  Card --> Type{"Task type"}

  Type --> ReadOnly["Read-only explanation / status"]
  Type --> VersionRun["Version-level tune / ablation / confirmation"]
  Type --> TrialRun["Innovation / module trial"]
  Type --> Promotion["Promotion"]

  VersionRun --> ExpDir["experiments/vX/<kind>/"]
  ExpDir --> Freeze["pre-run freeze commit"]
  Freeze --> Runner["Runner with GPU lock"]
  Runner --> Warehouse["GTPJ_Warehouse raw artifacts"]
  Warehouse --> Result["manifest / result / quality_check"]
  Result --> Decision["keep / revise / reject / confirm"]

  TrialRun --> Idea["idea_tree/IDEA-xxxx"]
  Idea --> Review0["Review 0: idea intent"]
  Review0 --> Review1["Review 1: interface design"]
  Review1 --> Impl["Implementer"]
  Impl --> Review2["Review 2: code diff pre-run"]
  Review2 --> TrialFreeze["pre-run freeze commit"]
  TrialFreeze --> TrialRunner["Runner with GPU lock"]
  TrialRunner --> TrialWarehouse["GTPJ_Warehouse raw artifacts"]
  TrialWarehouse --> Review3["Review 3: post-run evidence"]
  Review3 --> TrialDecision["revise / reject / promote"]

  Promotion --> Gate["promotion gate"]
  Gate --> Version["experiments/vY + config/versions/vY.yaml + tag vY"]
```

## 版本流程框架

```mermaid
flowchart TD
  Parent["parent version tag"] --> Trial["source trial tag"]
  Trial --> Attempt["decision-driving attempt"]
  Attempt --> Evidence["manifest / result / quality_check"]
  Evidence --> Promote{"promotion_decision"}
  Promote -->|promote| NewVersion["new version tag vY"]
  Promote -->|revise / reject| NoVersion["no new baseline"]
  NewVersion --> VersionRecord["experiments/vY/VERSION.md"]
  VersionRecord --> Active{"owner activate-version?"}
  Active -->|yes| MainCode["main active code changes"]
  Active -->|no| LedgerOnly["main keeps ledger only"]
```

## Module Trial 流程框架

```mermaid
flowchart TD
  Source["idea/source"] --> R0["Review 0"]
  R0 --> R1["Review 1"]
  R1 --> Code["implementation"]
  Code --> Tests["minimum code tests"]
  Tests --> R2["Review 2"]
  R2 --> Freeze["pre-run freeze commit"]
  Freeze --> Run["training run"]
  Run --> Artifacts["Warehouse artifacts"]
  Artifacts --> Attempt["attempt-local evidence"]
  Attempt --> Root["trial root summary"]
  Root --> R3["Review 3"]
  R3 --> Decision["final decision"]
```

## 更新规则

以下情况必须更新流程图：

- 新增正式版本 `vX`。
- 修改某个版本的 `parent_version`、`based_on_trial`、`code_tag` 或 confirmation 状态。
- 新 module trial 落成代码改动。
- trial 的决策从 `revise` / `reject` 变成 `promote`。
- promotion 创建新版本材料。

如果图和文字账本冲突，以 `result.yaml`、`manifest.yaml`、`experiments/VERSION_TREE.md` 和当前 Git tag 为事实源，先修正文字账本，再修正图。
