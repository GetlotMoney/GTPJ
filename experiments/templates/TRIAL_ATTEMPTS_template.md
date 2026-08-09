# TRIAL ATTEMPTS（历史兼容模板）

> 状态：只读兼容。不得作为新实验入口，也不得新增 `formal_pending` 行。

本模板只用于解释和修复规范生效前已经存在的 `TRIAL / ATTEMPT` 账本。历史行保持 append-only（只追加、不覆盖），旧指标、哈希、提交号和证据路径不得删改。

今后新实验统一登记到所属框架的四类正式账本：

```text
experiments/vX/tune/INDEX.md
experiments/vX/ablation/INDEX.md
experiments/vX/innovation/INDEX.md
experiments/vX/confirmation/INDEX.md
```

旧 `ATTEMPT-xxx` 只能作为 `legacy_ref` 或 Runner 内部兼容号；其中可恢复的真实任务，要映射为正式实验参数表中的逐行 `RUN-xxx`。恢复不了的批次只能写进历史批次映射，并标明 `legacy_summary_only`，不能冒充一次真实运行。

旧 helper `record-module-attempt` 只负责把旧运行证据补回历史目录，不会把该目录升级为新的正式实验入口。
