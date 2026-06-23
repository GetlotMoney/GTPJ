# GTPJ 可选结构辅助

这个目录目前不是强制工作流，而是可选的结构辅助层。

当前主规范放在 `docs/GITHUB_GOVERNANCE.md`。`docs/workflow/` 是未来
OpenClaw/Codex 接入时的参考草案。`NEXT_ACTIONS.md` 是当前执行窗口。

当前唯一权威基线是 `GTPJ-v1 / tag v1 / H=73.93`。`validate` 会检查本地
`v1` tag 是否指向这个基线记录；如果 tag 错位，先修正 tag，不要继续跑实验。

## 常用命令

下面是模板命令，`IDEA-XXXX` 和 `<source>` 需要替换成真实值：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote

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

`validate-remote` 核对远端 `main` 和 `v1` 是否分别对齐本地 `main` 和本地 `v1` tag，
并确认本地 `main` 包含 `v1` 历史。它不要求 `main` 永远等于 `v1`。

`new-experiment` 只允许在 clean working tree 和对应的 `exp/...` 分支上创建目录；
它会拒绝直接在 `main`、错误分支，或不包含当前本地 `main` 历史的分支上落账本。

`new-idea` 只创建候选节点。创建 trial 前必须人工补全 rationale、hypothesis、
implementation_scope、risk，确认 blockers 为空，并把 idea 状态改为 `selected`。

`set-current-version` 只切换创意树视图和排序，刷新 `idea_tree/INDEX.md` 与
`idea_tree/versions/vX.md`；它不会切换 `main` active code。`main` 代码只能由
owner 明确执行 `activate-version vX` 改变。

## 未来 Runtime 入口

- `openclaw/README.md`：OpenClaw 优先的执行规则。
- `codex/README.md`：Codex 兼容执行规则。

未来两个 runtime 必须使用同一套仓库文件、模板和 CLI 检查。
模块代码改动还必须满足 `docs/workflow/code_interface_contract.md`。
