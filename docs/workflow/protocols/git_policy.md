# Git 分支与发布规则

## 永久对象

- `main`：默认冻结的公共底座与治理分支。只有 owner 明确批准的公共修复才能移动。
- `framework/vX`：正式框架本身就是最简模板；分支固定在该框架的准确 commit。
- `vX`：与 `framework/vX` 指向同一 commit 的冻结 Tag。
- `experiments/vX/TEMPLATE.yaml`：框架身份绑定卡，不是第二份代码。

历史 `MODEL-VX-TEMPLATE-VN`、`framework/vX-template-vN` 与 `model/vX-template-vN` 原地只读兼容；只有 `canonical` 能启动新实验，历史 `frozen / legacy_frozen` 只用于回查。

## 临时工作分支

- `codex/<task>`：代码、规则或治理修改。
- `exp/vX/tune/...`
- `exp/vX/ablation/...`
- `exp/vX/innovation/...`
- `exp/vX/confirmation/...`

普通开发不直接写 `main` 或 `framework/vX`。每项新实验先创建 `EXPERIMENT.yaml` 并读取 `TEMPLATE.yaml`，再从准确框架提交独立分叉。实验代码不得并回正式框架，也不得从另一个实验继续叠代码。

## 框架继承与晋级

- 继承现有框架：候选从父 `framework/vX` commit 分叉，正式晋级时 Git 祖先关系必须真实成立。
- 完全独立：候选从 `main` 的准确 commit 分叉，并记录 `derived_from_commit`。
- 只有 confirmation、质量检查、代码瘦身和 owner 明确接纳全部通过后，才能在候选最终 commit 创建 `framework/vY` 与 `vY`。
- 晋级不复制代码、不重写历史、不移动 `main`，也不自动激活新框架。

## 合并

- 治理或公共修复：审核通过后可由 owner 决定是否合入 `main`。
- tune、ablation、confirmation：结果与轻量账本回到治理分支，实验代码不改正式框架。
- innovation：未晋级时只保留候选与证据；晋级时让新框架指向候选最终 commit，而不是把它合回父框架。

## 发布与删除

本地创建不等于发布。没有 owner 当前明确授权，不得 push、创建远端 Tag、删除本地或远端历史引用、强推或改写历史。旧分支和 Tag 的整理另开任务处理。

## 最小验证

```powershell
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate-framework-templates
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate-framework-ledgers
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate-workflow-consistency
```
