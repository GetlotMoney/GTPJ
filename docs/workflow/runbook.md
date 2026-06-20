# Runbook

## Initialize v1

Already done in this repository:

```text
GTPJ-v1 -> tag v1 -> experiments/v1/
```

## Run v1 Final Confirmation

```bash
git checkout -b exp/v1-final-001-clean-seed5 v1
python train_VGSR_CUB.py --config experiments/v1/final/FINAL-001_clean_seed5/config.yaml
```

Record results under:

```text
experiments/v1/final/FINAL-001_clean_seed5/
```

## Start a New Module Trial

```bash
git checkout main
git checkout -b dev/idea-0001-trial-001-short-name v1
```

After implementation:

```bash
git tag trial/idea-0001/trial-001
```

If successful and promoted:

```bash
git checkout main
git merge dev/idea-0001-trial-001-short-name
git tag v2
```
