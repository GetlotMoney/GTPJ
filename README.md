# GTPJ

GTPJ 是面向广义零样本学习（generalized zero-shot learning）的
GeoTopoPatch-JEPA 实验仓库。

这个仓库用于维护第一个正式基线 `GTPJ-v1`。它只保留当前认可的框架：
冻结 CLIP、GPT 文本描述、patch bottleneck、几何感知局部编码、拓扑保持文本约束、
条件文本适配、视觉-文本双分支互蒸馏，以及 AG-JEPA 辅助训练。

## 当前版本

| 版本 | 代码 tag | 状态 | 主数据集 | 说明 |
|---|---|---|---|---|
| `GTPJ-v1` | `v1` | 已确认 | CUB GZSL | `CONFIRM-001_clean_seed5` 已完成，seed=5 正式基准 H=73.79。 |

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
|-- idea_tree/              # 严格的创意来源和队列
`-- experiments/
    |-- module_trials/      # 有代码实现证据的模块 trial
    `-- v1/                 # GTPJ-v1 调参、消融、确认记录
```

## GitHub 管理规则

一个版本就是一个 baseline：

```text
v1 = GTPJ-v1 = 一个代码快照 = 一个 Git tag = 一个版本实验目录
```

模块创意不会立刻变成 `v2`、`v3` 或 `v4`。它们必须先经过
`idea_tree/` 和 `experiments/module_trials/`。只有证据完整、质量检查通过、
并被明确接纳的 trial 才能提升为新的 baseline 版本。

## 未来工作流接入

OpenClaw 是未来实验运行的优先 runtime。Codex 需要兼容同一套仓库文件。
但在正式接入前，本仓库先保证 GitHub 治理干净：版本能回滚、实验能追溯、
创意有来源、代码快照和结果不混淆。

优先阅读：

- `NEXT_ACTIONS.md`
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
```

需要创建标准目录时，可以使用 helper；当前它不是强制工作流：

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug clean_seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-0001 --slug attribute_router --title "attribute router" --source-type user --source-status unknown --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-0001 --trial-id TRIAL-001 --slug basic_router --base-version v1
```
