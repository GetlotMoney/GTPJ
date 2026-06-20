# Runbook

## 初始化 v1

本仓库中已经完成：

```text
GTPJ-v1 -> tag v1 -> experiments/v1/
```

## 运行 v1 确认实验

`CONFIRM-001_clean_seed5` 已经在本仓库中初始化。如果目录已经存在，
跳过创建命令，从切分支命令继续。

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind confirmation --exp-id CONFIRM-001 --slug clean_seed5
git switch -c exp/v1-confirm-001-clean-seed5 v1
python train_GTPJ_CUB.py --config experiments/v1/confirmation/CONFIRM-001_clean_seed5/config.yaml
```

结果记录到：

```text
experiments/v1/confirmation/CONFIRM-001_clean_seed5/
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
git switch -c dev/idea-xxxx-trial-001-short-name v1
```

实现后：

```bash
git tag trial/idea-xxxx/trial-001
```

如果成功并提升：

```bash
git switch main
git merge dev/idea-xxxx-trial-001-short-name
git tag v2
```
