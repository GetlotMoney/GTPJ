# Runbook

## 当前基线

本仓库当前 active baseline：

```text
GTPJ-v2
code tag: v2
baseline H: 74.29
长期分支: main
```

历史 baseline：

```text
GTPJ-v1
code tag: v1
baseline H: 73.93
```

`v1` 和 `v2` 是代码快照 tag，不是分支。`main` 是唯一长期分支，保存 owner 明确选择的
active code 和全部实验账本。

如果本地 baseline tag 和对应版本账本不一致，必须先修正 tag，不能继续跑正式实验。

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
对真实训练、confirmation、tune、ablation、module trial 的正式 run，再额外执行下面的冻结规则：

```text
1. 先写本次 run 需要的 config 副本、ATTEMPTS 计划行或启动卡
2. 提交 pre-run freeze commit
3. 再次检查 git status --short 为空
4. 记录 run_commit
5. 只从这个 clean worktree 启动 Runner
6. run 完成后再写 manifest/result/quality_check 和 artifact 注册，形成 post-run result commit
```

不要把“影响本次运行的配置改动”和“运行后的结果记账”混在同一次提交里。
如果只是本地离线复查，可以先跳过 `validate-remote`，但正式开实验前需要确认远端状态对齐。
`validate-remote` 允许 `main` 比历史 tag 多治理账本提交；它检查的是远端 `main` 对齐本地
`main`、远端 baseline tags 对齐本地 baseline tags，并确认本地 `main` 包含这些 baseline 历史。

Owner 只需要说明“想基于哪个版本跑/做什么”。检查通过后，Coordinator 自动按
`docs/workflow/TASK_START_CARD.md` 输出启动卡。只有启动卡说明任务类型、写入边界、agents、
hard gates 和当前阻断后，才进入具体实验命令。

第一次开跑完整工作流时，先读 `docs/workflow/FIRST_CLOSED_LOOP.md`，用 readiness check
和低风险任务验证通路，不要直接从复杂 module trial 开始。

## 实验后处理为什么会慢

结论先写清楚：后处理不应该每次都靠临场试错。慢的主要原因通常不是训练本身，而是证据链还没有完全脚本化，尤其是 module trial 内部 attempt 的结果登记。

常见耗时来源：

```text
1. 运行前需要 clean freeze commit，运行后又需要 post-run result commit。
2. raw log/checkpoint 必须留在 GTPJ_Warehouse，Git 里只能写 URI、sha256、size 和摘要。
3. manifest/result/quality_check/ATTEMPTS/README/INDEX/idea_tree 多个入口必须同步，否则以后会看到互相矛盾的状态。
4. 结果异常或 owner 质疑时，需要独立 Quality Checker 或多 agent 复核。
5. 如果某个步骤是第一次遇到，Coordinator 可能要边读规范边补证据字段，这会比训练本身更慢。
```

以后按下面规则沉淀经验：

```text
1. 同一个后处理动作重复出现 2 次：写进本 runbook。
2. 同一个后处理动作重复出现 3 次：优先加到 workflow/gtpj_workflow.py helper，而不是继续手工填。
3. version-level tune/ablation/confirmation 优先使用 record-result。
4. module trial attempt 如果 helper 尚不覆盖，至少沿用最近一次 attempt 的 manifest/result/quality_check 模板，并在本 runbook 记录缺口。
5. 任何“这次为什么慢”的原因，必须归类为：规范检查、artifact 注册、结果解释、多 agent 复核、脚本缺口或真实 bug。
```

项目内记忆分层：

```text
docs/workflow/runbook.md: 操作经验和反复踩坑的处理方法。
docs/workflow/issues/README.md: 具体实验执行问题索引，默认只读最近日期的问题文档。
docs/workflow/issues/YYYY-MM-DD-*.md: 按日期沉淀的问题、解决方案和预防规则。
docs/workflow/EXPERIMENT_ISSUES.md: 兼容入口，指向新的日期化问题库。
docs/workflow/*.md: 长期规范和硬门。
experiments/**/ATTEMPTS.md: 某个 trial 内部每次尝试的账本。
experiments/**/result.yaml / quality_check.md: 可引用的正式证据。
GTPJ_Warehouse: 原始日志、checkpoint 和 receipt。
```

聊天上下文和 Codex 全局 memory 只能帮助定位，不能当实验事实。能进入正式结论的内容，必须回到当前仓库文件、训练日志或 Warehouse artifact 里验证。

### 后处理最小闭环

真实训练完成后，除非只是 debug/smoke，否则按顺序做：

```text
1. 解析日志，记录 U/S/H/ZS、best_epoch、log path、checkpoint path。
2. 复制 raw log/checkpoint/receipt 到 GTPJ_Warehouse。
3. 计算 sha256 和 size。
4. 更新 attempt-local manifest.yaml、result.yaml、result.md、quality_check.md。
5. 更新 trial 或 version 的总账：ATTEMPTS.md、README.md、result.yaml/result.md、quality_check.md、INDEX、EXPERIMENT_REGISTRY。
6. 如果涉及 idea/module trial 状态，更新 idea_tree/idea_tree.json。
7. 跑 yaml/hash 校验、validate、audit-boundary、validate-remote、git diff --check。
8. 只提交轻量账本文件，不提交 train_log、.pth、.pt。
```

如果 4 到 6 步出现大量重复手工编辑，下一步不是继续试错，而是把该路径升级成 helper 命令。

### Module Trial Attempt 快速入账

module trial 内部 attempt 跑完后，优先用 helper，不要手填四五个账本文件：

```bash
python workflow/gtpj_workflow.py record-module-attempt \
  --trial-dir experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly \
  --attempt-id ATTEMPT-009 \
  --log train_log/CUB/<training_log>.txt \
  --best-checkpoint train_log/CUB/<best_model>.pth \
  --full-checkpoint train_log/CUB/<ckpt_full>.pth \
  --decision keep
```

建议先 dry-run：

```bash
python workflow/gtpj_workflow.py record-module-attempt ... --dry-run
```

该命令负责：

```text
1. 从训练日志解析 U/S/H/ZS 和 best_epoch。
2. 把 raw log、checkpoint、runner receipt 复制或生成到 GTPJ_Warehouse。
3. 计算 artifact sha256 和 size。
4. 写 attempt-local manifest.yaml、result.yaml、result.md、quality_check.md。
5. 更新 ATTEMPTS.md 中对应 attempt 行。
6. 更新 GTPJ_Warehouse/ARTIFACT_REGISTRY.yaml。
```

它不会自动判断 trial 根目录 README/result/quality_check/idea_tree 的最终结论。只有当本次 attempt 改变 trial-level 结论，例如 best、reject、promotion blocked 原因变化时，Coordinator 再做少量人工 review 和根账本同步。

## 运行 v2 确认实验

确认实验用于复验当前 baseline。当当前 `main` 代码就是 `v2` 时，临时分支从 `main` 开，
`base_code_tag: v2` 记录代码来源；如果未来当前 `main` 不是 `v2` 代码，则按
`docs/workflow/experiment_protocol.md` 的历史版本 confirmation 规则从 `v2` tag 开只运行分支。

```bash
git switch main
git switch -c exp/v2-confirm-001-v2-seed5
python workflow/gtpj_workflow.py new-experiment --version v2 --kind confirmation --exp-id CONFIRM-001 --slug v2_seed5
python train_GTPJ_CUB.py --config experiments/v2/confirmation/CONFIRM-001_v2_seed5/config.yaml
```

跑完后必须补：

```text
experiments/v2/confirmation/CONFIRM-001_v2_seed5/README.md
experiments/v2/confirmation/CONFIRM-001_v2_seed5/manifest.yaml
experiments/v2/confirmation/CONFIRM-001_v2_seed5/result.yaml
experiments/v2/confirmation/CONFIRM-001_v2_seed5/result.md
experiments/v2/confirmation/CONFIRM-001_v2_seed5/quality_check.md
experiments/EXPERIMENT_REGISTRY.md
experiments/v2/confirmation/INDEX.md
```

日志原始位置如果在 `train_log/`，必须登记或复制到外部 `GTPJ_Warehouse`，GitHub 只记录
`log_artifact_id`、`warehouse://` URI、sha256、size 和指标摘要。
具体 artifact id、Warehouse URI、hash、size、manifest/result 回填步骤见
`docs/workflow/ARTIFACT_REGISTRATION.md`。

确认实验记录完成后，当前版本实验可以把记录合并回 `main`，然后删除 `exp/...` 临时分支。
历史版本只运行分支不合并回 `main`，只回到当前 `main` 写账本。

## 运行 v2 版本级调参实验

version-level tune run 属于 `experiments/v2/tune/`，不要放到 `confirmation/`。
如果调参对象是某个 module trial 的 heads、ratio、dropout、seed 等 attempt 参数，应写入该 trial 的
`ATTEMPTS.md` 和 `attempts/ATTEMPT-xxx/`，不要写入 `experiments/v1/tune/`。

调参前先生成最多 3 个候选。这个命令只读配置和 tune 索引，不会改文件，也不会启动训练：

```bash
python workflow/gtpj_workflow.py tune-suggest --version v2
```

用户明确选择 1 个候选后，再开临时分支、创建实验目录、修改该实验目录里的配置副本：

```bash
git switch main
git switch -c exp/v2-tune-001-clipaself
python workflow/gtpj_workflow.py new-experiment --version v2 --kind tune --exp-id TUNE-001 --slug clipaself
```

Runner 开始前用本地文件锁占用 GPU，避免同一时间跑多个训练：

```bash
python workflow/gtpj_workflow.py runner-lock --run-id RUN-20260625-001 --experiment-id TUNE-001
python train_GTPJ_CUB.py --config experiments/v2/tune/TUNE-001_clipaself/config.yaml
```

跑完后必须补：

```text
README.md: 本次调了什么、old/new value、search space、结果和结论
quality_check.md: 证据是否完整、有没有改 eval 口径
manifest.yaml: config、command、seed、dataset、split、class order 和 artifact identity
result.yaml: U/S/H/ZS、best epoch、decision 和 evidence
result.md: 人类可读结果解释
experiments/v2/tune/INDEX.md: 实验索引
experiments/EXPERIMENT_REGISTRY.md: 全局登记
```

可以用 helper 解析训练日志并入账：

```bash
python workflow/gtpj_workflow.py record-result --version v2 --kind tune --exp-id TUNE-001 --slug clipaself --parameter clip_a_self_outer_ratio --old-value 0.15 --new-value 0.125 --seed 5 --log train_log/CUB/<log>.txt --command "python train_GTPJ_CUB.py --config experiments/v2/tune/TUNE-001_clipaself/config.yaml" --decision keep
python workflow/gtpj_workflow.py runner-unlock --run-id RUN-20260625-001
```

`record-result` 会读取外部日志、解析指标、计算 sha256/size，更新实验 README、`manifest.yaml`、
`result.yaml`、`result.md`、`experiments/v2/tune/INDEX.md` 和
`experiments/EXPERIMENT_REGISTRY.md`，并提示何时清理临时分支。
它不会把 raw log 复制到 GitHub。
它不提交、不 push、不删除分支。

tune 不会产生新的 `vX`。只有模块组合或模块替换通过 promotion gate 后，才会新增正式版本。

## 启动新模块 Trial

先登记创意来源。`IDEA-XXXX`、`short_name` 和 `<source>` 必须替换成真实值。

```bash
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v2 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v2
```

然后补全：

```text
idea_tree/idea_tree.json
idea_tree/ideas/IDEA-XXXX_short_name/IDEA.md
```

必须满足：

```text
status: selected
version_scores.v2.rationale: 非空
version_scores.v2.applicability: direct 或 needs_adaptation
version_scores.v2.blockers: []
hypothesis: 非空
implementation_scope: 非空
risk: 非空
```

最后创建 trial 记录并开临时开发分支：

```bash
git switch main
git switch -c dev/v2-idea-xxxx-trial-001-short-name
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v2
```

当前阶段 `main` 的代码就是 `v2`，所以不需要额外恢复代码层。未来如果 `main` 已经是 `v3`，但 trial 要基于旧 `v1` 或 `v2`，仍然从当前 `main` 开分支以保留最新账本，然后只把代码层恢复到目标 tag，不要恢复 `docs/`、`experiments/`、`idea_tree/` 和 `config/versions/`。

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
