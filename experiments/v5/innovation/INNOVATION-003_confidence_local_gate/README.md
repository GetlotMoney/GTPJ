# V5-INNOVATION-003：低全局置信度时增强局部

## 结论

这是一个尚未训练的最小创新草案。它不改 V5 母版，而是在母版输出之后加一个可学习、单调下降的 gate：全局分类越犹豫，局部分支得到的权重越大；全局分类越确定，局部分支权重不会变大。

## 固定实验身份

- `idea_id`：`IDEA-0005`；共享 `idea_tree` 与 V5 innovation 索引已由主分支提交 `6e42dfcff09a87c14aba807e4bb0fd7ab0d73350` 登记并同步。
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
- 2026-08-09 的首次正式启动在第 1 个 epoch 前失败：类别划分被直接加载到 CUDA，而母版构造阶段会先与 CPU 连续类别轴比较。失败输出单独保留为 `RUN-000-startup-failure`，不计入三轮正式训练；入口现改为先在 CPU 加载类别划分，再随模型统一迁移设备，模型公式、损失和评估口径不变。
- `IDEA-0005` 共享登记门已通过，`EXPERIMENT.yaml` 记录 `formal_run_allowed: true`；三份参数保持 `frozen`，仍须以本次干净 pre-run commit 作为实际 `--expected-run-commit`。
- 已知的非训练语义阻断：全局 `validate` / `validate-framework-ledgers` 要求所有索引实验预先存在 `result.md` 与 `evidence/`，但当前最高优先级短流程禁止在 pre-run commit 伪造未来结果文件。本次不创建这两项占位，只以母版、参数表、专项测试、语法和差异范围等 targeted gates 作为预跑放行证据。
- `beta=0.05` 固定，不能根据测试集成绩修改。
- `gate_bias` 与有效 slope 可学习；初始化分别为 `-1.0` 和 `1.0`。
- canonical `model/MyModel.py`、训练入口和正式配置不改。
