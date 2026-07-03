# Artifact Registration

本文件规定实验 raw artifacts 如何从本机文件变成可追踪证据。它补充
`artifact_policy.md`、`result_index_protocol.md` 和 `runbook.md`，重点回答：

```text
文件放哪里？
artifact id 怎么命名？
hash 和 size 怎么记录？
GitHub 里引用什么？
```

## 1. 基本原则

- raw logs、checkpoint、generated figures、feature cache、failure cases 不进 GitHub。
- GitHub 只记录 artifact identity、URI、hash、size、producer、required_for 和摘要结果。
- `GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml` 是外部 artifact 总登记表。
- `manifest.yaml` 是某个实验对 artifact 的复现引用。
- `result.yaml` 只引用关键证据 id，不复制完整 artifact 详情。

路径本身不是证据；hash 和 size 才能确认文件没有漂移。

## 2. 推荐命名

### run_id

```text
RUN-YYYYMMDD-HHMMSS-<kind>-<slug>
```

示例：

```text
RUN-20260626-153000-tune-topo008
```

### attempt_id

```text
attempt-001
attempt-002
```

失败重跑不要覆盖旧 attempt。

### logical URI

```text
warehouse://gtpj/runs/<base_version>/<kind>/<experiment_id>/<attempt_id>/<role>/<file>
```

示例：

```text
warehouse://gtpj/runs/v1/tune/TUNE-001/attempt-001/logs/train.log
```

### physical path

物理路径由 `.gtpj/local_paths.yaml` 决定。默认映射到：

```text
D:/backup/Documents/Myself/GTPJ_Warehouse/runs/<base_version>/<kind>/<experiment_id>/<attempt_id>/<role>/<file>
```

### artifact_id

```text
<role>:<base_version>:<kind>:<experiment_id>:<attempt_id>
```

示例：

```text
log:v1:tune:TUNE-001:attempt-001
checkpoint:v1:tune:TUNE-001:attempt-001
figure:v1:ablation:ABL-001:attempt-001
cache:v1:module_trial:TRIAL-001:attempt-001
```

## 3. Runner 写入规则

Runner 优先直接把 raw artifacts 写到 Warehouse run 目录：

```text
GTPJ_Warehouse/runs/<base_version>/<kind>/<experiment_id>/<attempt_id>/
  logs/
  checkpoints/
  figures/
  tables/
  failure_cases/
  receipts/
```

如果训练脚本临时写到了 repo 内的 `train_log/`，该路径只能作为临时产生位置。长期证据必须登记到
Warehouse；GitHub 里不能引用未登记的临时路径作为最终证据。

### Checkpoint retention

每次真实实验完成并完成日志解析、指标确认、hash/size 计算和 manifest/result 登记后，
Runner 或 Coordinator 必须清理模型 checkpoint：

- 每个 run、batch 或 attempt 最多保留 3 个模型 checkpoint；
- 默认保留按验证指标排序最高的 3 个，主指标是 GZSL-H；如果实验协议另有主指标，必须在
  manifest 或 quality_check 中写明；
- 如果有 owner 明确指定的 baseline/control checkpoint，它可以占用这 3 个名额之一；
- 删除范围只限模型权重文件，例如 `.pth`、`.pt`、`.ckpt`、`.safetensors`；
- 不得删除 raw log、config、manifest、result、quality_check、runner receipt、events、summary
  或 Warehouse registry；
- 被删除的 checkpoint 不再写入 manifest；如果已经登记过但后续被清理，必须把对应 artifact
  状态改成 `pruned`，并记录保留的 3 个 checkpoint artifact id。

这条规则是存储保留策略，不改变实验结论。若 promotion、baseline_grade 或论文复现实验需要更长
保留期，必须在对应 quality_check 中显式写出例外理由。

## 4. 登记步骤

### Step 1: 确定 artifact 身份

记录：

```yaml
artifact_id:
role:
uri:
local_path:
producer:
produced_by:
required_for:
status:
```

### Step 2: 计算 hash 和 size

PowerShell:

```powershell
(Get-FileHash -Algorithm SHA256 -Path "<artifact_path>").Hash.ToLower()
(Get-Item "<artifact_path>").Length
```

### Step 3: 更新 Warehouse registry

在外部文件中登记：

```text
D:/backup/Documents/Myself/GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml
```

推荐结构：

```yaml
artifacts:
  log:v1:tune:TUNE-001:attempt-001:
    role: raw_log
    uri: warehouse://gtpj/runs/v1/tune/TUNE-001/attempt-001/logs/train.log
    local_path: D:/backup/Documents/Myself/GTPJ_Warehouse/runs/v1/tune/TUNE-001/attempt-001/logs/train.log
    sha256:
    size_bytes:
    produced_by: runner
    required_for:
      - experiments/v1/tune/TUNE-001_topo008/result.yaml
    status: available
```

### Step 4: 更新实验 manifest

GitHub 里的 `manifest.yaml` 记录同一个 artifact id：

```yaml
artifacts:
  log:v1:tune:TUNE-001:attempt-001:
    role: raw_log
    uri: warehouse://gtpj/runs/v1/tune/TUNE-001/attempt-001/logs/train.log
    sha256:
    size_bytes:
```

### Step 5: 更新 result

`result.yaml` 只引用关键日志证据：

```yaml
evidence:
  log_artifact_id: log:v1:tune:TUNE-001:attempt-001
```

promotion 时通过 `result.evidence.log_artifact_id` 回到 `manifest.artifacts[...]`，再核对
URI、sha256 和 size。

### Step 6: 质量检查

每次登记后运行：

```bash
python workflow/gtpj_workflow.py audit-boundary
```

Quality Checker 还要确认：

- artifact 在 Warehouse 中可读；
- registry、manifest、result 三者 id 一致；
- sha256 和 size 一致；
- GitHub 没有 raw artifact；
- result 的指标来自这个 artifact。
- checkpoint retention 已执行：模型 checkpoint 最多保留 3 个，或 quality_check 写明例外。

## 5. Helper 使用边界

`record-result` 用于 version-level tune / ablation / confirmation。它可以从日志中解析指标，计算 sha256/size，并把轻量结果写回 GitHub 账本。它不提交、不 push、不删除分支。

`record-module-attempt` 用于 module trial 内部 attempt。它会从日志中解析指标，把 raw log / checkpoint / runner receipt 复制或生成到 Warehouse，并写回 attempt-local `manifest.yaml`、`result.yaml`、`result.md`、`quality_check.md`、`ATTEMPTS.md` 和 `GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml`。

推荐先运行：

```bash
python workflow/gtpj_workflow.py record-module-attempt ... --dry-run
```

确认指标和 Warehouse URI 后再正式执行。helper 不负责自动得出 trial-level 论文结论；如果某个 attempt 改变 root trial 决策，Coordinator 仍需 review 并同步 trial 根目录 README/result/quality_check/idea_tree。

如果 helper 和本文件冲突，优先遵守本文件的证据边界，再补 helper。

## 6. 阻断条件

以下情况不能把结果标记为 `keep` 或 `promote`：

- 只有本地路径，没有 artifact id；
- 只有 artifact id，没有 URI/hash/size；
- `result.yaml` 指向的 id 在 `manifest.yaml` 中无法解析；
- Warehouse 文件不存在或 hash 不一致；
- raw log/checkpoint/cache 被加入 Git；
- 指标无法追溯到对应 raw log；
- 实验完成后模型 checkpoint 未清理，且没有记录为什么需要超过 3 个。
