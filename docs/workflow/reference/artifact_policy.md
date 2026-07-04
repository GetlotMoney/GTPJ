# Artifact Policy

本文定义 GTPJ 的 GitHub 边界和外部 artifact 边界。目标是让 GitHub 保持为轻量事实索引，
同时保留完整证据链。

## GitHub Boundary

GitHub 是可复现控制面、治理事实源和轻量事实索引。它必须能回答：

```text
How can this result be reproduced?
What is the result?
Why was it kept, rejected, rerun, or promoted?
Which code, config, command, seed, dataset split, label mapping, class order, and evaluation path were used?
Which external artifact is the raw evidence, where is it, and what is its hash?
```

GitHub 不保存 raw logs、checkpoints、生成的实验图、完整论文阅读材料、完整创意树推理、
长创新草稿或论文笔记库。

对于 idea 记录，GitHub 只保存复现和审计实验所需的稳定字段：

```text
idea_id, title, source reference, source_status, global_score,
core_summary, version_scores.vX, hypothesis, implementation_scope, risk,
linked_trials, and evidence artifact ids or research URIs.
```

全局 idea 记录只描述创意本身和可追溯证据，不保存局部下一步动作。执行动作应写入
queue、trial/attempt、task card 或 result/quality 文件。

## External Stores

外部目录保存完整材料和大型资产：

```text
GTPJ_Research
  Paper PDFs, reading notes, full idea trees, source reviews, long-form reasoning, and innovation drafts.

GTPJ_Warehouse
  Raw logs, checkpoints, experiment visualizations, experiment tables, failure cases, and run receipts.
```

## Checkpoint Retention

训练 checkpoint 默认不是永久证据。一次 experiment campaign 被解析，并且 logs/receipts/configs
已经注册后，Warehouse 在保留候选集合中只保留按 H 排名前三（Top-3）的 `model_best`/best-model
checkpoints。其它训练 checkpoints（`*.pth`、`*.pt`、`*.ckpt`）可以在 retention manifest
记录保留和删除内容后删除。

执行 checkpoint retention 时，不要删除 logs、receipts、configs、summaries、manifests
或 registry files。它们是审计轨迹。如果被删除的 checkpoint 已经注册为 artifact，
保留 artifact id，并把 artifact reference 标记为 `pruned`，不要删除证据行。

GitHub 通过 logical URIs 引用外部资产：

```text
warehouse://gtpj/runs/v1/tune/TUNE-001_topo008/attempt-001/logs/train.log
research://ideas/IDEA-0001.md
```

本地物理路径存放在被忽略的本地文件中：

```text
.gtpj/local_paths.yaml
```

## Artifact Identity

每个进入证据链的外部 artifact 必须有稳定身份，而不能只有路径：

```text
artifact_id
role
uri
sha256
size_bytes
created_at or recorded_at
producer / produced_by
required_for
status
```

路径只能说明文件在哪里；哈希和大小才能证明它到底是哪一个文件。

## Forbidden GitHub Artifacts

不要把以下内容提交到 GitHub：

- `train_log/`
- `experiments/**/logs/*`
- `experiments/**/checkpoints/*`
- `experiments/**/figures/*` 下生成的实验图
- `*.pt`, `*.pth`, `*.ckpt`, `*.onnx`
- `*.npy`, `*.npz`
- 原始 datasets、feature caches、tensor dumps
- paper PDFs、完整 OCR dumps、完整 reading libraries、完整 idea trees
- `.gtpj/local_paths.yaml`, `.gtpj/locks/`, `.gtpj_runtime/`

允许进入 GitHub 的 artifacts：

- code、config、schema、workflow helper
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- `agent_summary.md`
- version tree、experiment registry、轻量 idea index
- 小型手工维护的解释性图源文件；生成的实验图仍必须留在外部

## Boundary Audit

提交前运行：

```bash
python workflow/gtpj_workflow.py audit-boundary
```

`audit-boundary` 检查：

- `experiments/` 下 raw logs、checkpoints、generated figures 和 caches 没有被 track 或进入 commit candidate；
- 旧的 `copied_log` 证据模式没有继续作为新证据模型；
- result records 指向 manifests；
- manifests 指向外部 artifact identities；
- GitHub 不包含应该放在外部存储中的资产。

## Legacy Migration

历史 `GTPJ-v1 / tag v1 / H=73.93` baseline log 已迁移到本地 Warehouse：

```text
artifact_id: log:legacy:v1_baseline:GTPJ-v1_CUB_seed5_20260613-145232
artifact_uri: warehouse://logs/legacy/v1_baseline/GTPJ-v1_CUB_seed5_20260613-145232.txt
sha256: 850a01a5c1500f75fef3d9729b8e89b47c78aa40203792341b03515ddc5edfb9
size_bytes: 139148
```

仓库不应保留任何 Git-tracked raw log 例外。历史证据通过外部 artifact pointer、hash、
config snapshot、result record 和 quality record 保持可复现。
