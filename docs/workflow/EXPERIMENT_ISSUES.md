# Experiment Issue Memory

本文件记录 GTPJ 实验执行中反复出现、会拖慢后处理或影响证据可信度的问题。

记录原则：

- 只记录可复用经验，不复制长日志。
- 每个问题都要写清影响范围、处理方式和下次预防规则。
- 如果同类问题出现 2 次，同步补充到 `docs/workflow/runbook.md`。
- 如果同类问题出现 3 次，优先考虑沉淀到 `workflow/gtpj_workflow.py` helper。

## 2026-06-26 TRIAL-001/002 24-run sweep

Scope:

- 前 20 个实验：`TRIAL-001_clip_a_self_residual_seenonly` 内部参数调节，计划为 `ATTEMPT-009` 到 `ATTEMPT-028`。
- 后 4 个实验：新增 L2SP/text-anchor loss 机制，计划新开 `TRIAL-002`，只调 `lambda_l2sp` = `0.001 / 0.003 / 0.005 / 0.01`。
- 所有训练默认使用 `dvsr_gpu` 环境。
- raw log/checkpoint 只进 `GTPJ_Warehouse`，GitHub 只记录 lightweight evidence。

### ISSUE-20260626-001: PowerShell heredoc mismatch

Status: fixed in workflow habit.

What happened:

- 在 PowerShell 中误用了 Bash 风格的 `python - <<'PY'` heredoc。
- PowerShell 报错：`Missing file specification after redirection operator`。

Impact:

- 未改动仓库文件，未启动训练，只浪费一次命令。

Resolution:

- Windows/PowerShell 下改用 `python -c`、临时脚本文件或已有 workflow helper。

Prevention:

- GTPJ 命令默认按 PowerShell 语法写。
- 如果需要多行 Python，优先写成 helper；临时脚本只用于机械生成或一次性验证。

### ISSUE-20260626-002: L2SP belongs to a new trial, not TRIAL-001 tuning

Status: guarded before run.

What happened:

- 用户指定 20 轮参数调节后，再跑 L2SP/text-anchor 模块实验。
- 当前 `TRIAL-001` 的 `implementation.md` 已声明 `lambda_l2sp` 不是 TRIAL-001 变量，`model/MyModel.py` 也会拦截非零 `lambda_l2sp`。

Impact:

- 不能把 `lambda_l2sp` 直接写进 `TRIAL-001` attempts，否则会混淆“参数调节”和“新增 loss 机制”。

Resolution:

- `ATTEMPT-009` 到 `ATTEMPT-028` 只调 TRIAL-001 既有参数。
- L2SP/text-anchor 在 20 轮结束后新开 `TRIAL-002`，实现 loss contract 后再跑 4 个 lambda。

Prevention:

- 改变 forward/loss/eval 语义时必须开新 trial。
- 数值-only 参数调节才留在当前 trial 的 `ATTEMPTS.md`。

### ISSUE-20260626-003: Post-run overhead must be helper-first

Status: policy active.

What happened:

- 之前 module trial 结果登记耗时偏长，主要卡在 manifest/result/quality/ATTEMPTS/Warehouse registry 多处同步。

Impact:

- 训练本身可能较快，但后处理如果手填，容易慢且容易出账本漂移。

Resolution:

- 本轮批量实验跑完后，优先用 `record-module-attempt` helper 入账。
- 对同一批 run，不在每个 attempt 后立刻手工改账本；先完整跑完，再批量解析和登记。

Prevention:

- 运行前先 freeze config 和 planned rows。
- 运行后先 dry-run helper，确认日志、checkpoint、metrics、URI/hash/size，再正式入账。

### ISSUE-20260626-004: Multi-line `python -c` is fragile in PowerShell

Status: fixed in workflow habit.

What happened:

- 复核配置时把多行 Python 逻辑直接塞进 `python -c`，PowerShell 传参后触发 `SyntaxError: unexpected character after line continuation character`。

Impact:

- 未改动仓库文件，未影响实验配置，只导致一次只读复核命令失败。

Resolution:

- 多行 Python 复核改用临时脚本文件执行。

Prevention:

- `python -c` 只用于单行表达式。
- 多行检查优先沉淀为 workflow helper；临时检查也使用 `$env:TEMP` 下脚本，执行后删除。
