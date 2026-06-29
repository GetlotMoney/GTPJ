# GTPJ

## Current Confirmed Version

```text
name: GTPJ-v4
code_tag: v4
status: confirmed
confirmed_H: 74.45
best_observed_H: 74.47
source: local-v3-054 min3 server confirmation
active_main_update: not_activated
```

`GTPJ-v4` is the current confirmed formal version. It is a promotion from the
min3-confirmed `local-v3-054` tuned v3 configuration, not an automatic
`activate-version` code switch.

GTPJ 是面向广义零样本学习（generalized zero-shot learning）的
GeoTopoPatch-JEPA 实验仓库。

这个仓库用于维护 GTPJ 的正式版本、配置快照、实验账本和 workflow 规范。GitHub 只保存轻量证据；
原始日志、receipt、checkpoint 和生成物保留在 Warehouse，并通过 URI、hash 和 size 反查。

## 当前版本

| 版本 | 代码 tag | 状态 | 主数据集 | 说明 |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | 已确认 | CUB GZSL | 新仓库第一版正式 baseline，seed=5，H=73.93。 |
| `GTPJ-v2` | `v2` | owner-activated / needs confirmation | CUB GZSL | CLIP-A-self text prototype adapter，seed=5，best_observed_H=74.29。 |
| `GTPJ-v3` | `v3` | owner-accepted stochastic / needs confirmation | CUB GZSL | Strict conditional FAE-memory JEPA，seed=5，best_observed_H=74.27。 |
| `GTPJ-v4` | `v4` | confirmed formal version | CUB GZSL | min3-confirmed `local-v3-054` tuned v3 configuration，confirmed_H=74.45，best_observed_H=74.47。 |

当前正式确定版本是 `GTPJ-v4 / tag v4`。这表示它已经通过 min3 复现实验证据进入
baseline-grade confirmed 版本；不表示已经执行 `activate-version`，也不表示 active runtime alias
已自动切换。`main` 是唯一长期分支；`v1`、`v2`、`v3`、`v4` 都是正式版本 tag，不是长期分支。

## 当前管理重点

当前阶段已经强制执行 GTPJ 核心 workflow：版本、tag、分支、目录、配置快照、创意树、
实验证据、任务路由、启动卡、artifact 边界、结果账本、质量门、agent 凭证和 promotion gate。
OpenClaw / Codex 只是不同 runtime 入口，必须接入同一套 GitHub 事实源和 workflow 规范。

## 项目结构

```text
GTPJ/
|-- NEXT_ACTIONS.md         # 当前执行窗口
|-- model/                  # 模型代码
|-- tools/                  # 数据、特征、评估工具
|-- config/
|   |-- versions/v1.yaml    # 固定的 GTPJ-v1 配置
|   |-- versions/v2.yaml    # 固定的 GTPJ-v2 配置
|   |-- versions/v3.yaml    # 固定的 GTPJ-v3 配置
|   `-- versions/v4.yaml    # 固定的 GTPJ-v4 配置
|-- docs/                   # GitHub 治理、项目状态和 workflow 规范
|-- workflow/               # 结构辅助工具和 runtime 接入口
|-- idea_tree/              # 总创意库和按版本生成的创意选择清单
`-- experiments/
    |-- module_trials/      # 模块 trial 证据；trial 内部 attempts 可做调参、窄消融、确认
    |-- v1/                 # GTPJ-v1 baseline 和 version-level 调参、消融、确认记录
    |-- v2/                 # GTPJ-v2 baseline 和 version-level 调参、消融、确认记录
    |-- v3/                 # GTPJ-v3 baseline 和 version-level 调参、消融、确认记录
    `-- v4/                 # GTPJ-v4 baseline 和 version-level 调参、消融、确认记录
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
`-- v2 = parent v1 + CLIP-A-self / PSE
    `-- v3 = parent v2 + FAE-memory JEPA / SGMP
        `-- v4 = parent v3 + local-v3-054 min3-confirmed tuned config
```

`main` 保存当前 active code 和所有历史版本账本。也就是说，
`experiments/v2/` 留在最新 `main` 中，不表示当前正式版本一定继承或激活了 `v2` 的 runtime alias；
它只是 `v2` 的历史记录。promotion 只确定正式版本和 tag，不自动执行 `activate-version`。

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

## Workflow 入口

OpenClaw 是实验运行的优先 runtime。Codex 兼容同一套仓库文件和 workflow 规范。
GitHub 负责事实源和轻量账本：版本能回滚、实验能追溯、创意有来源、代码快照和结果不混淆。

## 默认实验环境

本机 GTPJ 实验默认使用 conda 环境 `dvsr_gpu`。运行训练、特征抽取或验证脚本前，
先激活该环境：

```bash
conda activate dvsr_gpu
```

或者直接使用：

```bash
conda run -n dvsr_gpu python train_GTPJ_CUB.py --config config/versions/v4.yaml
```

优先阅读：

- `NEXT_ACTIONS.md`
- `docs/GITHUB_GOVERNANCE.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/PROJECT_STATUS.md`
- `docs/workflow/README.md`（workflow 入口）
- `workflow/README.md`（结构辅助工具）
- `experiments/v4/VERSION.md`
- `experiments/v3/VERSION.md`
- `experiments/v2/VERSION.md`
- `experiments/v1/VERSION.md`
- `idea_tree/README.md`

## 结构辅助工具

需要检查仓库结构时，可以运行：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
```

`validate-remote` 检查远端 `main` 是否等于本地 `main`、正式版本 tag 是否同步，
并确认本地 `main` 包含版本 tag 历史；`main` 可以比历史 tag 多治理账本提交。

需要创建标准目录、登记结果或做边界检查时，优先使用 helper。它是结构辅助工具，
不是研究判断黑盒。
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
