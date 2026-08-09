# V5-ABLATION-011：current global-only

结论先说：三次 seed=5 独立进程运行均已完成，且逐项得到同一结果：`U=71.4106`、`S=77.0254`、`H=74.1118`、`ZS=81.2728`，最佳轮次均为 33。相对完整 V5 三轮均值，global-only 的 H 只低 `0.1165`，因此不能把当前局部分支写成“明显提升”；本实验只用于诊断，不是多 seed 稳定性证据。

- 母版：`MODEL-V5-TEMPLATE-V1@2f5fa5e631ef82658d4bac587cdfd17f3534cb35`
- 分支：`exp/v5/ablation/ablation-011-current-global-only`
- 模型：`model/V5GlobalOnly.py`
- 入口：`train_V5_ABLATION_011_CUB.py`
- 输入：CUB CLS、标签、xlsa17 划分、gpt55 句子文本；不需要局部块缓存
- 运行提交：`83bf7c090bdce18c6483a3ff58aeeb8313100664`
- 输出：项目总目录的 `.runtime/runs/v5/local_complementarity/V5-ABLATION-011/RUN-001..003`，每轮均保存 `training.log`、`metrics.json`、`model_best.pth`、`checkpoint_last.pth`
- 结论与边界：见 `result.md`、`quality_check.md` 与 `evidence/ARTIFACTS.md`

本次运行使用的命令形态如下，实际配置分别对应 `RUN-001..003`：

```powershell
conda run -n dvsr_gpu python train_V5_ABLATION_011_CUB.py --config <RUN配置> --data-root <data目录> --run-dir <不存在的RUN目录> --expected-run-commit <完整HEAD>
```
