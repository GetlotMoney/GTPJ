# GTPJ 可执行工作流

这个目录包含 GTPJ 的可执行 workflow 层。

仓库级规则放在 `docs/workflow/`。本目录把这些规则转成可重复执行的命令，
以及 OpenClaw 和 Codex 的 runtime 入口。`NEXT_ACTIONS.md` 是当前执行窗口。

## 常用命令

```bash
python workflow/gtpj_workflow.py status
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug clean_seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-0001 --slug attribute_router --title "attribute router" --source-type user --source-status unknown --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-0001 --trial-id TRIAL-001 --slug basic_router --base-version v1
```

## Runtime 入口

- `openclaw/README.md`：OpenClaw 优先的执行规则。
- `codex/README.md`：Codex 兼容执行规则。

两个 runtime 必须使用同一套仓库文件、模板和 CLI 检查。
模块代码改动还必须满足 `docs/workflow/code_interface_contract.md`。
