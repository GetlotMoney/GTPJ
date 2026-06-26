# Runbook

## 当前唯一基线

本仓库当前只有一个正式基线：

```text
GTPJ-v1
code tag: v1
baseline H: 73.93
长期分支: main
```

`v1` 是代码快照 tag，不是分支。`main` 是唯一长期分支，保存 owner 明确选择的 active code
和全部实验账本。

如果本地 `v1` tag 不是 `H=73.93` 对应的代码快照，必须先修正 tag，不能继续跑实验。

## 实验前统一检查

每次跑实验前先做：

```bash
git switch main
git status --short
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-remote
```

要求：

```text
working tree: clean
validate-ok
validate-remote-ok
```

如果工作区不干净，先提交或处理当前改动，不要直接开实验分支。
如果只是本地离线复查，可以先跳过 `validate-remote`，但正式开实验前需要确认远端状态对齐。
`validate-remote` 允许 `main` 比 `v1` 多治理账本提交；它检查的是远端 `main` 对齐本地
`main`、远端 `v1` 对齐本地 `v1` tag，并确认本地 `main` 包含 `v1` 历史。

检查通过后，先按 `docs/workflow/TASK_START_CARD.md` 输出启动卡。只有启动卡说明任务类型、
写入边界、agents、hard gates 和当前阻断后，才进入具体实验命令。

第一次开跑完整工作流时，先读 `docs/workflow/FIRST_CLOSED_LOOP.md`，用 readiness check
和低风险任务验证通路，不要直接从复杂 module trial 开始。

## 运行 v1 确认实验

确认实验用于复验当前 baseline。当当前 `main` 代码就是 `v1` 时，临时分支从 `main` 开，
`base_code_tag: v1` 记录代码来源；如果未来当前 `main` 不是 `v1` 代码，则按
`docs/workflow/experiment_protocol.md` 的历史版本 confirmation 规则从 `v1` tag 开只运行分支。

```bash
git switch main
git switch -c exp/v1-confirm-001-v1-seed5
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug v1_seed5
python train_GTPJ_CUB.py --config experiments/v1/confirmation/CONFIRM-001_v1_seed5/config.yaml
```

跑完后必须补：

```text
experiments/v1/confirmation/CONFIRM-001_v1_seed5/README.md
experiments/v1/confirmation/CONFIRM-001_v1_seed5/manifest.yaml
experiments/v1/confirmation/CONFIRM-001_v1_seed5/result.yaml
experiments/v1/confirmation/CONFIRM-001_v1_seed5/result.md
experiments/v1/confirmation/CONFIRM-001_v1_seed5/quality_check.md
experiments/EXPERIMENT_REGISTRY.md
experiments/v1/confirmation/INDEX.md
```

日志原始位置如果在 `train_log/`，必须登记或复制到外部 `GTPJ_Warehouse`，GitHub 只记录
`log_artifact_id`、`warehouse://` URI、sha256、size 和指标摘要。
具体 artifact id、Warehouse URI、hash、size、manifest/result 回填步骤见
`docs/workflow/ARTIFACT_REGISTRATION.md`。

确认实验记录完成后，当前版本实验可以把记录合并回 `main`，然后删除 `exp/...` 临时分支。
历史版本只运行分支不合并回 `main`，只回到当前 `main` 写账本。

## 运行 v1 调参实验

tune run 属于 `experiments/v1/tune/`，不要放到 `confirmation/`。

调参前先生成最多 3 个候选。这个命令只读配置和 tune 索引，不会改文件，也不会启动训练：

```bash
python workflow/gtpj_workflow.py tune-suggest --version v1
```

用户明确选择 1 个候选后，再开临时分支、创建实验目录、修改该实验目录里的配置副本：

```bash
git switch main
git switch -c exp/v1-tune-001-topo008
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
```

Runner 开始前用本地文件锁占用 GPU，避免同一时间跑多个训练：

```bash
python workflow/gtpj_workflow.py runner-lock --run-id RUN-20260625-001 --experiment-id TUNE-001
python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml
```

跑完后必须补：

```text
README.md: 本次调了什么、old/new value、search space、结果和结论
quality_check.md: 证据是否完整、有没有改 eval 口径
manifest.yaml: config、command、seed、dataset、split、class order 和 artifact identity
result.yaml: U/S/H/ZS、best epoch、decision 和 evidence
result.md: 人类可读结果解释
experiments/v1/tune/INDEX.md: 实验索引
experiments/EXPERIMENT_REGISTRY.md: 全局登记
```

可以用 helper 解析训练日志并入账：

```bash
python workflow/gtpj_workflow.py record-result --version v1 --kind tune --exp-id TUNE-001 --slug topo008 --parameter conditional_text_ratio --old-value 0.008 --new-value 0.006 --seed 5 --log train_log/CUB/<log>.txt --command "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml" --decision keep
python workflow/gtpj_workflow.py runner-unlock --run-id RUN-20260625-001
```

`record-result` 会读取外部日志、解析指标、计算 sha256/size，更新实验 README、`manifest.yaml`、
`result.yaml`、`result.md`、`experiments/v1/tune/INDEX.md` 和
`experiments/EXPERIMENT_REGISTRY.md`，并提示何时清理临时分支。
它不会把 raw log 复制到 GitHub。
它不提交、不 push、不删除分支。

tune 不会产生新的 `vX`。只有模块组合或模块替换通过 promotion gate 后，才会新增正式版本。

## 启动新模块 Trial

先登记创意来源。`IDEA-XXXX`、`short_name` 和 `<source>` 必须替换成真实值。

```bash
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
```

然后补全：

```text
idea_tree/idea_tree.json
idea_tree/ideas/IDEA-XXXX_short_name/IDEA.md
```

必须满足：

```text
status: selected
version_scores.v1.rationale: 非空
version_scores.v1.applicability: direct 或 needs_adaptation
version_scores.v1.blockers: []
hypothesis: 非空
implementation_scope: 非空
risk: 非空
```

最后创建 trial 记录并开临时开发分支：

```bash
git switch main
git switch -c dev/v1-idea-xxxx-trial-001-short-name
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
```

当前阶段 `main` 的代码就是 `v1`，所以不需要额外恢复代码层。未来如果 `main` 已经是 `v3`，但 trial 要基于旧 `v1`，仍然从当前 `main` 开分支以保留最新账本，然后只把代码层恢复到 `v1`，不要恢复 `docs/`、`experiments/`、`idea_tree/` 和 `config/versions/`。

## Trial 打快照 tag

实现、训练、证据记录全部完成后，先确认工作区干净：

```bash
git status --short
git rev-parse HEAD
```

然后显式把 tag 打到当前 commit：

```bash
git tag trial/v1/idea-xxxx/trial-001 <code_commit>
```

`<code_commit>` 必须写进 trial README 的 `code_commit` 字段。不要在 dirty working tree 上打 tag。

## 成功 Trial 提升为新版本

不要把 `dev/v1-...` 整体直接合并成 `main`。

正确做法：

```bash
git switch main
git switch -c promote/v1-idea-xxxx-to-v2
```

在 `promote/...` 分支中：

```text
1. 保留当前 main 的账本层：docs/、workflow/、experiments/、idea_tree/、config/versions/。
2. 把成功 trial 的证据目录合并回当前账本。
3. 只移植代码层：model/、tools/、train_*.py、当前运行别名 config/GTPJ_*.yaml。
4. 新增 experiments/v2/。
5. 新增 config/versions/v2.yaml。
6. 更新 experiments/VERSION_TREE.md。
7. 更新 experiments/EXPERIMENT_REGISTRY.md、docs/PROJECT_STATUS.md、docs/PROJECT_STRUCTURE.md、README.md。
8. 更新 idea_tree/idea_tree.json 的 current_version 和必要的 version_scores.v2。
9. 通过 validate 和 promotion quality gate 后，在 promote 分支的版本代码 commit 上打 tag v2。
10. 回到当前 main，只把 v2 账本层回流到 main；不要默认回流代码层。
11. main 当前代码是否切到 v2，必须由 owner 明确执行 activate-version v2。
```

新 `vX` tag 必须指向包含正式版本代码和版本材料的明确 commit。不能指向 dirty tree，
也不能指向只含 trial 证据但未完成版本账本的中间 commit。这个 commit 不必是当前 `main` commit。

## 分支删除规则

- `exp/...`：实验记录合并回 `main` 后可以删除。
- 失败 `dev/...`：先打 `trial/...` tag，再把失败证据记录回 `main`，然后可以删除。
- 成功 `dev/...`：先打 `trial/...` tag，再通过 `promote/...` 生成新 `vX`，最后可以删除。
- `promote/...`：新版本 tag 打好、版本账本回流到 `main` 后可以删除；代码层是否回流由
  owner 通过 `activate-version` 明确决定。
- 永远不要删除 `main`。
- 推送后的 `vX` 和 `trial/...` tag 默认不可移动。
