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

## 5. Helper 使用边界

当前 `record-result` 可以从日志中解析指标，计算 sha256/size，并把轻量结果写回 GitHub 账本。
它不负责把 raw log 长期整理到 Warehouse，也不提交、不 push、不删除分支。

如果 helper 和本文件冲突，优先遵守本文件的证据边界，再补 helper。

## 6. 阻断条件

以下情况不能把结果标记为 `keep` 或 `promote`：

- 只有本地路径，没有 artifact id；
- 只有 artifact id，没有 URI/hash/size；
- `result.yaml` 指向的 id 在 `manifest.yaml` 中无法解析；
- Warehouse 文件不存在或 hash 不一致；
- raw log/checkpoint/cache 被加入 Git；
- 指标无法追溯到对应 raw log。
