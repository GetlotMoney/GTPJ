# V5-ABLATION-003 服务器启动计划

本文件只定义启动前的卡位和命令形状；当前没有启动任何训练。

## 固定分配

- 物理 GPU：`0`
- 进程可见卡：`CUDA_VISIBLE_DEVICES=0`
- 配置内设备：`cuda:0`（进程只看见这一张卡）
- 运行顺序：`RUN-001`（seed 5 第1次）→ `RUN-002`（seed 5 第2次）→ `RUN-003`（seed 17 第1次）→ `RUN-004`（seed 17 第2次）

## 启动方式

冻结提交完成且工作树干净后，在服务器对应工作树中直接使用现有训练入口。下面展示 `RUN-001` 的命令形状：

```powershell
$env:CUDA_VISIBLE_DEVICES = '0'
conda run -n dvsr_gpu python train_GTPJ_CUB.py `
  --config experiments/v5/ablation/ABLATION-003_icsa_effect/configs/RUN-001.yaml
```

`RUN-002`、`RUN-003` 和 `RUN-004` 只替换 `--config`。四个 RUN 必须各用一个独立 Warehouse 输出目录，并分别保存 `training.log`、最终指标和需要保留的最佳模型，不能覆盖前一次运行。
