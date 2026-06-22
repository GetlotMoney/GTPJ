# GTPJ 可选结构辅助

这个目录目前不是强制工作流，而是可选的结构辅助层。

当前主规范放在 `docs/GITHUB_GOVERNANCE.md`。`docs/workflow/` 是未来
OpenClaw/Codex 接入时的参考草案。`NEXT_ACTIONS.md` 是当前执行窗口。

## 常用命令

下面是模板命令，`IDEA-XXXX` 和 `<source>` 需要替换成真实值：

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug v1_seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
```

## 未来 Runtime 入口

- `openclaw/README.md`：OpenClaw 优先的执行规则。
- `codex/README.md`：Codex 兼容执行规则。

未来两个 runtime 必须使用同一套仓库文件、模板和 CLI 检查。
模块代码改动还必须满足 `docs/workflow/code_interface_contract.md`。
