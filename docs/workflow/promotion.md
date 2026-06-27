# 自动 Promotion 规范

Promotion 表示：一次实验的干净代码或配置状态，被正式接纳为新的 baseline 版本。

自动 promotion 表示：当实验账本已经明确记录 `promotion_decision: promote`，并且硬门证据全部通过时，
Coordinator 不再向用户二次确认，直接执行本地版本创建流程。

自动 promotion 不等于自动 push。`main` 和 tag 推送到 GitHub 仍然必须由用户明确要求。
自动 promotion 也不等于自动切换 `main` 当前代码。`main` 当前代码由 owner 在实验完成后明确决定；
未明确执行 `activate-version` 时，`main` 代码保持原 active version。

## 触发条件

只有实验记录同时满足下面字段，才进入自动 promotion：

```text
promotion_decision: promote
promote_to: vX
evidence_level: baseline_grade
confirmation_status: confirmed
```

并且 `promote_to` 对应的 tag 和版本目录尚不存在。

## 硬门

全部通过才允许 promotion：

- source experiment / trial 记录父版本、代码来源、分支、commit、配置、命令和日志。
- source experiment / trial 不只是单次最高 H；必须有 clean confirmation 或多 run 稳定性证据。
- source experiment / trial 的 `evidence_level` 必须为 `baseline_grade`；`valid_single_run`
  只能登记 `best_observed_H`，不能自动 promotion。
- `dirty_state: clean` 且 `git_dirty: false`；如果运行前 dirty 或 `run_commit` 不能唯一映射到
  pre-run freeze commit，promotion 阻断。
- 普通实验按 `docs/workflow/experiment_protocol.md` 的 promotion 字段映射读取：
  `version -> base_version/parent_version`、`base_code_tag -> parent_tag`、
  `run_commit -> code_commit`、`config -> run_config`、`command -> run_command`、
  `log_artifact_id -> run_log_artifact`、`log_uri -> run_log_uri`。
- module trial 必须直接记录 `base_version`、`base_code_tag`、`code_branch`、`code_commit`、
  `run_config`、`run_command` 和 `run_log_artifact`。
- 结果包含 U、S、H、ZS、seed、best epoch、log artifact id、URI、sha256 和 size。
- `quality_check.md` 没有 blocking issue。
- 改代码的实验必须有 `implementation.md` 和 `code.diff`。
- 消融和创新必须有 `interface_check.md`。
- class order、seen/unseen split、label mapping、logits shape、metric calculation 没有未声明变化。
- GitHub 边界通过：raw logs、checkpoint、generated figures、feature cache 没有进入 GitHub。
- 目标 config 可以冻结到 `config/versions/vX.yaml`。
- 当前 `main` clean。
- 新版本父节点和来源实验明确。

任一项缺失时，不创建新版本；记录或报告：

```text
promotion_decision: blocked
```

Owner override 只能绕过“是否现在激活主线代码”的产品决策，不能把证据等级从
`valid_single_run` 改写成 `baseline_grade`。如果 owner 明确要求激活但 confirmation 缺失，
版本状态必须写成 `owner_activated_unconfirmed` 或 `provisional`，并保留
`confirmation_status: pending/failed`。

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
10. 在 promotion 分支运行 `python workflow/gtpj_workflow.py validate`。
11. 验证通过后，在 promotion 分支的版本代码 commit 上创建本地 tag `vX`；`vX` tag 不要求指向当前
    `main` commit。
12. 回到当前 `main`，只回流账本层：`docs/`、`workflow/`、`idea_tree/`、`experiments/`、
    `config/versions/`、`README.md`、`AGENTS.md`、`NEXT_ACTIONS.md` 中与版本记录相关的内容。
13. 不回流代码层：`model/`、`tools/`、`train_*.py`、当前运行别名 `config/GTPJ_*.yaml`，
    除非 owner 明确要求 `activate-version vX`。
14. 在账本回流后的当前 `main` 上运行 `python workflow/gtpj_workflow.py validate`。
15. 不 push，除非用户明确说提交推送。

## 分支规则

promotion 分支必须从当前 `main` 开出：

```text
promote/<parent_version>-to-<target_version>-<slug>
```

不要把旧实验分支整体合并进 `main`。不要默认把 promotion 分支整体合并进 `main`。
默认只把版本账本回流到 `main`；代码层是否进入 `main` 由 owner 单独决定。

原因：

```text
版本代码来源 = parent tag + 成功实验变化
账本来源 = 当前 main
main 当前代码 = owner 明确选择的 active version
```

这样可以保留最新 `experiments/`、`idea_tree/`、docs 和 GitHub 规范。

## Activate Version

`activate-version` 是独立动作，不属于默认 promotion。

只有 owner 明确说要把当前主线切到某个正式版本时，才允许执行：

```text
activate-version vX
```

动作含义：

1. 从当前 `main` 开临时 activation 分支。
2. 只把代码层切换到 `vX` tag 对应状态。
3. 保留当前 `main` 的全部账本层。
4. 同步当前运行别名 config，例如 `config/GTPJ_*.yaml`。
5. 更新 `docs/PROJECT_STATUS.md`、`README.md` 和必要的 current version 记录。
6. 验证通过后，合并 activation 分支回 `main`。

如果 owner 没有明确执行 `activate-version`，promotion 后 `main` 代码仍然停在原 active version，
可以继续基于该框架寻找其他创新。

## Artifact Resolution

Promotion must resolve raw evidence through `result.yaml` and `manifest.yaml` together:

```text
artifact_id = result.evidence.log_artifact_id
artifact    = manifest.artifacts[artifact_id]
uri         = artifact.uri
sha256      = artifact.sha256
size_bytes  = artifact.size_bytes
```

If `uri`, `sha256`, or `size_bytes` is missing, the promotion gate is blocked. GitHub must not use a copied raw log as promotion evidence.

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
evidence_level:
best_observed_H:
confirmed_H:
confirmation_status:
active_main_update: not_activated | activated_by_owner
```

Promotion 创建正式 baseline。失败、阻塞或证据模糊的实验只保留为证据。
