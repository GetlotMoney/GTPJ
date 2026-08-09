# V5-ABLATION-011：current global-only

结论先说：本目录只冻结“保留 PSE、ICSA、全局 logits 与文本拓扑损失，移除全部局部分支”的三次 seed=5 预运行草案；当前没有启动训练，也没有结果结论。

- 母版：`MODEL-V5-TEMPLATE-V1@2f5fa5e631ef82658d4bac587cdfd17f3534cb35`
- 分支：`exp/v5/ablation/ablation-011-current-global-only`
- 模型：`model/V5GlobalOnly.py`
- 入口：`train_V5_ABLATION_011_CUB.py`
- 输入：CUB CLS、标签、xlsa17 划分、gpt55 句子文本；不需要局部块缓存
- 输出：每个尚未创建的独立 run 目录内写 `training.log`、`metrics.json`、`model_best.pth`、`checkpoint_last.pth`

开跑时保持工作区 clean，不再回写本表；直接把本地预运行提交的完整 `HEAD` 传给入口，入口会把它写进运行输出：

```powershell
conda run -n dvsr_gpu python train_V5_ABLATION_011_CUB.py --config <RUN配置> --data-root <data目录> --run-dir <不存在的RUN目录> --expected-run-commit <完整HEAD>
```
