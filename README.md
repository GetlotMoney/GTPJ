# GTPJ

GTPJ 是面向广义零样本学习（generalized zero-shot learning）的
GeoTopoPatch-JEPA 实验仓库。

这个仓库用于维护第一个正式基线 `GTPJ-v1`。它只保留当前认可的框架：
冻结 CLIP、GPT 文本描述、patch bottleneck、几何感知局部编码、拓扑保持文本约束、
条件文本适配、视觉-文本双分支互蒸馏，以及 AG-JEPA 辅助训练。

## 当前版本

| 版本 | 代码 tag | 状态 | 主数据集 | 说明 |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | 已初始化 | CUB GZSL | 需要在本仓库中干净重跑后，才能作为正式报告结果。 |

## 项目结构

```text
GTPJ/
|-- NEXT_ACTIONS.md         # 当前执行窗口
|-- model/                  # 模型代码
|-- tools/                  # 数据、特征、评估工具
|-- config/
|   `-- versions/v1.yaml    # 固定的 GTPJ-v1 配置
|-- docs/workflow/          # GitHub 与实验工作流规则
|-- workflow/               # 可执行 workflow 命令
|-- idea_tree/              # 严格的创意来源和队列
`-- experiments/
    |-- module_trials/      # 有代码实现证据的模块 trial
    `-- v1/                 # GTPJ-v1 调参、消融、确认记录
```

## 工作流规则

一个版本就是一个 baseline：

```text
v1 = GTPJ-v1 = 一个代码快照 = 一个 Git tag = 一个版本实验目录
```

模块创意不会立刻变成 `v2`、`v3` 或 `v4`。它们必须先经过
`idea_tree/` 和 `experiments/module_trials/`。只有成功并通过 review 的
trial 才能提升为新的 baseline 版本。

## 运行时偏好

OpenClaw 是实验运行的优先 runtime。Codex 必须遵循同一套仓库文件并产出同样的记录，
这样两个 runtime 才能在同一个 baseline 上工作，而不会各自发明规则。

优先阅读：

- `NEXT_ACTIONS.md`
- `docs/PROJECT_STATUS.md`
- `docs/workflow/README.md`
- `workflow/README.md`
- `experiments/v1/VERSION.md`
- `idea_tree/README.md`

## 可执行工作流

创建任何记录前，先检查仓库：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
```

通过 helper 创建记录，不要手工乱建目录：

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug clean_seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-0001 --slug attribute_router --title "attribute router" --source-type user --source-status unknown --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-0001 --trial-id TRIAL-001 --slug basic_router --base-version v1
```
