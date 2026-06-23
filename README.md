# GTPJ

GTPJ 是面向广义零样本学习（generalized zero-shot learning）的
GeoTopoPatch-JEPA 实验仓库。

这个仓库用于维护第一个正式基线 `GTPJ-v1`。它只保留当前认可的框架：
冻结 CLIP、GPT 文本描述、patch bottleneck、几何感知局部编码、拓扑保持文本约束、
条件文本适配、视觉-文本双分支互蒸馏，以及 AG-JEPA 辅助训练。

## 当前版本

| 版本 | 代码 tag | 状态 | 主数据集 | 说明 |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | 已确认 | CUB GZSL | 新仓库第一版正式 baseline，seed=5，H=73.93。 |

当前只有一个权威代码基线：`GTPJ-v1 / tag v1 / H=73.93`。`main` 是唯一长期分支；
`v1` 是代码快照 tag，不是分支。如果本地或远端 `v1` tag 指向旧结果，
必须先修正为 `H=73.93` 对应快照再跑实验。

## 当前管理重点

当前阶段先管理 GitHub 项目本身：版本、tag、分支、目录、配置快照、创意树和实验证据。
OpenClaw / Codex 工作流之后再接入这个仓库；现有 `docs/workflow/` 和 `workflow/`
只作为未来工作流参考，不是当前必须执行的完整流程。

## 项目结构

```text
GTPJ/
|-- NEXT_ACTIONS.md         # 当前执行窗口
|-- model/                  # 模型代码
|-- tools/                  # 数据、特征、评估工具
|-- config/
|   `-- versions/v1.yaml    # 固定的 GTPJ-v1 配置
|-- docs/                   # GitHub 治理、项目状态和未来 workflow 参考
|-- workflow/               # 可选结构辅助；未来 workflow 接入口
|-- idea_tree/              # 总创意库和按版本生成的创意选择清单
`-- experiments/
    |-- module_trials/      # 模块 trial 证据；当前无已启动 trial
    `-- v1/                 # GTPJ-v1 baseline、调参、消融、确认记录
```

## GitHub 管理规则

一个版本就是一个 baseline：

```text
v1 = GTPJ-v1 = 一个代码快照 = 一个 Git tag = 一个版本实验目录 = 一个版本树节点
```

模块创意不会立刻变成 `v2`、`v3` 或 `v4`。它们必须先经过
`idea_tree/` 和 `experiments/module_trials/`。只有证据完整、质量检查通过、
并被明确接纳的 trial 才能提升为新的 baseline 版本。

版本不是默认串行继承。每个新版本都必须记录父节点：

```text
v1
|-- v2 = parent v1 + 模块A
`-- v3 = parent v1 + 模块B
```

`main` 保存当前主版本代码，同时保存所有历史版本账本。也就是说，
`experiments/v2/` 留在最新 `main` 中，不表示当前 `v3` 继承了 `v2` 的代码；
它只是 `v2` 的历史记录。

普通实验和模块 trial 的临时分支都从当前 `main` 开出，以继承最新账本。
分支名中的 `v1`、`v2` 只表示 `base_code_tag`，不是长期分支名。

全局版本树记录在：

```text
experiments/VERSION_TREE.md
```

如果从旧父节点产生新主版本，例如 `v4 = v1 + 新模块`，实现方式是：

```text
代码层来自 v1 和成功 trial
账本层来自提升时的当前 main
```

因此不能把旧 `dev/v1-...` 分支整体变成 `main`；必须从当前 `main`
开 `promote/...` 分支，保留最新账本，只移植代码层。

当前创意树已清空。新的创意必须从可靠来源重新登记，不能直接复用旧的来源不明候选。
`idea_tree/INDEX.md` 是总创意清单；`idea_tree/versions/v1.md` 是 v1 创意选择清单。
创新 trial 只读取对应 base version 的版本清单，不需要每次读完整总表。

## 未来工作流接入

OpenClaw 是未来实验运行的优先 runtime。Codex 需要兼容同一套仓库文件。
但在正式接入前，本仓库先保证 GitHub 治理干净：版本能回滚、实验能追溯、
创意有来源、代码快照和结果不混淆。

优先阅读：

- `NEXT_ACTIONS.md`
- `docs/GITHUB_GOVERNANCE.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/PROJECT_STATUS.md`
- `docs/workflow/README.md`（未来 workflow 参考）
- `workflow/README.md`（可选结构辅助）
- `experiments/v1/VERSION.md`
- `idea_tree/README.md`

## 可选结构辅助

需要检查仓库结构时，可以运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
```

`validate-remote` 检查远端 `main` 是否等于本地 `main`、远端 `v1` tag 是否等于本地
`v1` tag，并确认本地 `main` 包含 `v1` 历史；`main` 可以比 `v1` 多治理账本提交。

需要创建标准目录时，可以使用 helper；当前它不是强制工作流。
`new-experiment` 必须在 clean working tree 中运行，并且先从当前 `main` 切到 helper 建议的 `exp/...` 分支；helper 会拒绝不包含当前本地 `main` 历史的实验分支。
下面是模板命令，`IDEA-XXXX` 和 `<source>` 需要替换成真实值：

```bash
git switch main
git status --short
git switch -c exp/v1-confirm-001-v1-seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug v1_seed5

git switch main
git status --short
git switch -c exp/v1-tune-001-topo008
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008

python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
git switch main
git status --short
git switch -c dev/v1-idea-xxxx-trial-001-short-name
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
```

注意：`new-idea` 之后不能立刻无脑 `new-trial`。必须先补全
`version_scores.<base_version>.rationale`、`hypothesis`、`implementation_scope`、
`risk`，把 idea 状态改为 `selected`，并确认没有 blockers。
