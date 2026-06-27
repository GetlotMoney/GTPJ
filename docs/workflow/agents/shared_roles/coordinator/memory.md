# Coordinator Memory

## Standing Lessons

- GitHub 是权威控制面；本地 skill 是执行副本，修改 workflow 后必须同步。
- 不要只靠聊天上下文判断状态；先检查 repo、branch、dirty state、tags 和远端差异。
- 不要在 owner 未明确要求时 push、发布、删除远端或重写历史。

## Recurrent Failure Modes

- 规范已改但本地 skill 未同步，后续 agent 会读到旧规则。
- 训练后手工同步 manifest/result/quality/registry 容易漂移，应优先使用 helper。
- 本地 `main` ahead remote 时，不能说 GitHub 已经有最新规则。

## Required Checks

- `git status --short --branch`
- `python workflow/gtpj_workflow.py validate`
- `python workflow/gtpj_workflow.py audit-boundary`
- 需要远端事实时运行 `validate-remote`
- 明确 GitHub、Research、Warehouse 哪些写了、哪些跳过。

## Update Rules

同类流程或同步问题重复两次后，更新本文件；重复三次后推动 helper 或 sync check。
