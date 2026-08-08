# V5-ABLATION-003 服务器启动计划

本文件只定义启动前的卡位和命令形状；当前没有启动任何训练。

## 固定分配

- 物理 GPU：`1`
- 进程可见卡：`CUDA_VISIBLE_DEVICES=1`
- 配置内设备：`cuda:0`（进程只看见这一张卡）
- 运行顺序：`RUN-001`（seed 5）→ `RUN-002`（seed 17）→ `RUN-003`（seed 29）

## 唯一正式入口

每个 RUN 必须在冻结提交后，从干净工作树通过 `prepare-run-start-receipt` 启动。把 `<FREEZE_COMMIT>` 替换成当次冻结提交，不能手工绕开该入口运行训练。

```powershell
$env:CUDA_VISIBLE_DEVICES = '1'
conda run -n dvsr_gpu python workflow/gtpj_workflow.py prepare-run-start-receipt `
  --path experiments/v5/ablation/ABLATION-003_icsa_effect/PARAMETER_MATRIX.csv `
  --config experiments/v5/ablation/ABLATION-003_icsa_effect/configs/RUN-001.yaml `
  --job-id RUN-001 --run-id V5-ABLATION-003-RUN-001 `
  --pre-run-freeze-commit <FREEZE_COMMIT> `
  --command "python train_GTPJ_CUB.py --config experiments/v5/ablation/ABLATION-003_icsa_effect/configs/RUN-001.yaml" `
  --receipt <warehouse-run-start-receipt> --log <warehouse-train-log>
```

`RUN-002` 和 `RUN-003` 只替换 `--config`、`--job-id`、`--run-id` 和外部日志路径；不改其它参数。
