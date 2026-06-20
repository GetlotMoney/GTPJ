# Runbook

## Initialize v1

Already done in this repository:

```text
GTPJ-v1 -> tag v1 -> experiments/v1/
```

## Run v1 Final Confirmation

`FINAL-001_clean_seed5` is already initialized in this repository. If it exists,
skip the creation command and continue from the branch command.

```bash
python workflow/gtpj_workflow.py new-experiment --version v1 --kind final --exp-id FINAL-001 --slug clean_seed5
git switch -c exp/v1-final-001-clean-seed5 v1
python train_VGSR_CUB.py --config experiments/v1/final/FINAL-001_clean_seed5/config.yaml
```

Record results under:

```text
experiments/v1/final/FINAL-001_clean_seed5/
```

## Start a New Module Trial

```bash
python workflow/gtpj_workflow.py new-idea --idea-id IDEA-0001 --slug short_name --title "short name" --source-type user --base-version v1
python workflow/gtpj_workflow.py new-trial --idea-id IDEA-0001 --trial-id TRIAL-001 --slug short_name
git switch -c dev/idea-0001-trial-001-short-name v1
```

After implementation:

```bash
git tag trial/idea-0001/trial-001
```

If successful and promoted:

```bash
git switch main
git merge dev/idea-0001-trial-001-short-name
git tag v2
```
