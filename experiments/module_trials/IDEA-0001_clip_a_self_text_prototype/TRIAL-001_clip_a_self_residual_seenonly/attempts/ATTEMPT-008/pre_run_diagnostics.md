# ATTEMPT-008 Pre-Run Diagnostics

```text
purpose: repeat ATTEMPT-003/007 config to investigate whether ATTEMPT-007 drop is parameter pollution or run-to-run variance
attempt_type: confirmation / rerun
target_attempts: ATTEMPT-003, ATTEMPT-007
planned_run_env: conda:dvsr_gpu
planned_command: conda run --no-capture-output -n dvsr_gpu python train_GTPJ_CUB.py --config experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/attempts/ATTEMPT-008/config.yaml
```

## Config Identity

```text
ATTEMPT-003 config size: 1534
ATTEMPT-003 config sha256: 2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622
ATTEMPT-007 config size: 1534
ATTEMPT-007 config sha256: 2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622
ATTEMPT-008 config expected sha256: 2970fa444cdee33f5690198018f39bd10c801d53c74d03eec8886ecc8fe63622
```

## Environment Snapshot

```text
python: 3.10.20 packaged by Anaconda
torch: 2.11.0+cu128
torch_cuda: 12.8
cuda_available: True
cudnn: 91900
cudnn_benchmark: False
cudnn_deterministic: False
deterministic_algorithms: False
CUBLAS_WORKSPACE_CONFIG:
gpu: NVIDIA GeForce RTX 5070 Ti
driver: 595.79
```

## Cache Fingerprints

```text
data/cache/cub_gpt55_sentence_embeds.pt size=4302567 sha256=977fce2c525a9e758b62622cc81c88238cc01ea9c1aca4db8823db9fdd678462 mtime=2026-06-26 10:25:34
data/gpt4_data/cub_gpt55.pt size=196921 sha256=36cc24543cd3a521f1b554fdf0ec09baf689531f2b724492adbb4d858549dec4 mtime=2026-05-25 03:12:51
data/cache/CUB_train_patch_features.pt size=6243583333 sha256=244dbf96109362306555c55cf718590a6ffd2f3c5c403127463aff86311aacc2 mtime=2026-05-17 02:09:11
data/cache/CUB_train_labels.pt size=29449 sha256=b1cbf2c128a3a09979852ec5906161a737be58bf4517b18b4f7d16beec06b666 mtime=2026-05-18 04:48:05
data/cache/CUB_class_text_embeds.pt size=616075 sha256=80c28bd79351d8dcef30bf34479322f01bc333a2eac534e2a08ff25b9b3c2a3e mtime=2026-06-11 13:41:46
```

## Pre-Run Risk Notes

- No model or training-code edit is planned for ATTEMPT-008.
- `train_GTPJ_CUB.py` seeds `torch`, `torch.cuda`, and `numpy`, but does not enable deterministic algorithms.
- This run should be interpreted as variance / pollution evidence, not as a promotion run.
