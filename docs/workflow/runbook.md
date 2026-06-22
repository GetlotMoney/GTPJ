# Runbook

## 初始化 v1

本仓库中已经完成：

```text
GTPJ-v1 -> tag v1 -> experiments/v1/
```

## 运行 v1 确认实验

确认实验使用 `experiments/v1/confirmation/`，用于复验当前 baseline。

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug v1_seed5
git switch -c exp/v1-confirm-001-v1-seed5 v1
python train_GTPJ_CUB.py --config experiments/v1/confirmation/CONFIRM-001_v1_seed5/config.yaml
```

结果记录到：

```text
experiments/v1/confirmation/CONFIRM-001_v1_seed5/
```

## 运行 v1 调参实验

tuning run 属于 `experiments/v1/tune/`，不要放到 `confirmation/`。

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind tune --exp-id TUNE-001 --slug topo008
git switch -c exp/v1-tune-001-topo008 v1
python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml
```

## 启动新模块 Trial

下面是模板命令，`IDEA-XXXX`、`idea-xxxx` 和 `<source>` 需要替换成真实值。

```bash
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-XXXX --slug short_name --title "short name" --source-type paper --source-ref "<source>" --source-status verified --base-version v1 --global-score 50 --version-score 50 --applicability direct
python workflow/gtpj_workflow.py set-current-version --version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-XXXX --trial-id TRIAL-001 --slug short_name --base-version v1
git switch -c dev/v1-idea-xxxx-trial-001-short-name v1
```

实现后：

```bash
git tag trial/v1/idea-xxxx/trial-001
```

如果成功并提升：

不要把 `dev/v1-...` 整体直接合并到 `main`。它的账本来自旧 `v1` 时间点，
可能缺少当前 `main` 里的历史记录。

正确做法是从当前 `main` 开 promote 分支：

```bash
git switch main
git switch -c promote/v1-idea-xxxx-to-v2
```

然后在 promote 分支中：

```text
1. 保留当前 main 的 docs/、experiments/、idea_tree/、config/versions/。
2. 只把代码层移植为 parent tag + 成功 trial 的代码。
3. 新增 experiments/v2/。
4. 新增 config/versions/v2.yaml。
5. 更新 experiments/VERSION_TREE.md。
6. 更新 experiments/EXPERIMENT_REGISTRY.md、docs/PROJECT_STATUS.md、README.md。
7. 验证通过后合并 promote 分支到 main，并打 tag v2。
```

注意：`dev/v1-...` 里的 `v1` 是来源 baseline，不是最终版本号。
如果这个 trial 成功，最终可以提升为下一个正式 baseline，比如 `v2` 或 `v3`。
