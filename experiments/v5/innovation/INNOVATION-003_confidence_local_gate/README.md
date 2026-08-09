# V5-INNOVATION-003：低全局置信度时增强局部

## 结论

这是一个尚未训练的最小创新草案。它不改 V5 母版，而是在母版输出之后加一个可学习、单调下降的 gate：全局分类越犹豫，局部分支得到的权重越大；全局分类越确定，局部分支权重不会变大。

## 固定实验身份

- 预留 `idea_id`：`IDEA-0005`。当前实验分支源自冻结母版，不能安全覆盖已经继续演进的主分支共享账本；主代理必须先在 main ledger-sync 工作树完成 `idea_tree` 与 V5 innovation 索引登记，再把登记结果安全同步回来。
- 母版：`MODEL-V5-TEMPLATE-V1` / `model/v5-template-v1`。
- 母版 commit：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 分支：`exp/v5/innovation/innovation-003-confidence-local-gate`。
- 评估仍是原来的 CUB xlsa17 `U/S/H/ZS`，类别编号、seen/unseen 划分和 200 类轴均不变。

## 最小运行方式

三份配置相同，只改变外部 `run-dir`：

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe experiments\v5\innovation\INNOVATION-003_confidence_local_gate\train.py `
  --config experiments\v5\innovation\INNOVATION-003_confidence_local_gate\configs\RUN-001.yaml `
  --data-root D:\path\to\data `
  --run-dir D:\path\to\warehouse\RUN-001 `
  --expected-run-commit <本次pre-run提交的40位commit>
```

入口会先检查 CUDA、Git 干净状态、准确 commit、输入文件和“输出目录尚不存在”。正式输出固定为 `training.log`、`metrics.json`、`model_best.pt`、`checkpoint_last.pt`，每次写入都先落临时文件再原子替换。

## 当前边界

- 本提交只准备代码、配置、参数表和测试，没有启动训练。
- 唯一正式开跑阻断是 `IDEA-0005` 尚未完成主分支共享登记；`EXPERIMENT.yaml` 明确记录 `formal_run_allowed: false`，登记同步并复核前禁止启动正式训练。参数表中的 `frozen` 只表示三份参数已经固定，不代表这个共享登记门已经通过。
- `beta=0.05` 固定，不能根据测试集成绩修改。
- `gate_bias` 与有效 slope 可学习；初始化分别为 `-1.0` 和 `1.0`。
- canonical `model/MyModel.py`、训练入口和正式配置不改。
