# 自动 Promotion 规范

Promotion 表示：一次实验的干净代码或配置状态，被正式接纳为新的 baseline 版本。

自动 promotion 表示：当实验账本已经明确记录 `promotion_decision: promote`，并且硬门证据全部通过时，
Coordinator 不再向用户二次确认，直接执行本地版本创建流程。

自动 promotion 不等于自动 push。`main` 和 tag 推送到 GitHub 仍然必须由用户明确要求。

## 触发条件

只有实验记录同时满足下面字段，才进入自动 promotion：

```text
promotion_decision: promote
promote_to: vX
```

并且 `promote_to` 对应的 tag 和版本目录尚不存在。

## 硬门

全部通过才允许 promotion：

- source experiment / trial 记录 `base_version`、`base_code_tag`、`code_branch`、`code_commit`。
- 记录 `run_config`、`run_command`、`run_log`。
- 结果包含 U、S、H、ZS、seed、best epoch 和日志路径。
- `quality_check.md` 没有 blocking issue。
- 改代码的实验必须有 `implementation.md` 和 `code.diff`。
- 消融和创新必须有 `interface_check.md`。
- class order、seen/unseen split、logits shape、metric calculation 没有未声明变化。
- 目标 config 可以冻结到 `config/versions/vX.yaml`。
- 当前 `main` clean。
- 新版本父节点和来源实验明确。

任一项缺失时，不创建新版本；记录或报告：

```text
promotion_decision: blocked
```

## 自动动作

硬门通过后，Coordinator 自动执行：

1. 从当前 `main` 开 promotion 分支。
2. 把被接纳的干净代码或配置状态整理到 promotion 分支。
3. 创建 `experiments/vX/`。
4. 创建 `config/versions/vX.yaml`。
5. 更新 `experiments/VERSION_TREE.md`。
6. 更新 `experiments/EXPERIMENT_REGISTRY.md`。
7. 更新 `docs/PROJECT_STATUS.md`。
8. 必要时更新 `README.md`。
9. 如果结构或目录类型变化，更新 `docs/PROJECT_STRUCTURE.md`。
10. 运行 `python workflow/gtpj_workflow.py validate`。
11. 验证通过后，创建本地 tag `vX`。
12. 不 push，除非用户明确说提交推送。

## 分支规则

promotion 分支必须从当前 `main` 开出：

```text
promote/<parent_version>-to-<target_version>-<slug>
```

不要把旧实验分支整体合并进 `main`。如果成功实验来自历史 tag 分支，只移植被接纳的干净代码或配置变化。

原因：

```text
代码来源 = parent tag + 成功实验变化
账本来源 = 当前 main
```

这样可以保留最新 `experiments/`、`idea_tree/`、docs 和 GitHub 规范。

## 版本记录

新版本必须记录：

```text
version:
parent_version:
parent_tag:
code_tag:
ledger_source:
ledger_source_commit:
source_experiment:
source_trial:
change_type:
config_snapshot:
baseline_result:
known_risks:
confirmation_requirement:
```

Promotion 创建正式 baseline。失败、阻塞或证据模糊的实验只保留为证据。
