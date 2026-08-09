# V5-INNOVATION-003：低全局置信度时增强局部

## 结论

三轮同配置、同种子独立运行已完成。固定的置信度 gate 平均 `H=73.4274`，比 global-only 平均低 `0.6844`，比完整 V5 平均低 `0.8009`。因此当前候选结论是 `reject`：不把这个固定 gate 保留为提升模块，也不进入 promotion。

## 固定实验身份

- `idea_id`：`IDEA-0005`；共享 `idea_tree` 与 V5 innovation 索引已由主分支提交 `6e42dfcff09a87c14aba807e4bb0fd7ab0d73350` 登记并同步。
- 母版：`MODEL-V5-TEMPLATE-V1` / `model/v5-template-v1`。
- 母版 commit：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 分支：`exp/v5/innovation/innovation-003-confidence-local-gate`。
- 评估仍是原来的 CUB xlsa17 `U/S/H/ZS`，类别编号、seen/unseen 划分和 200 类轴均不变。

## 已执行的运行方式

三份配置相同，只改变外部 `run-dir`：

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe experiments\v5\innovation\INNOVATION-003_confidence_local_gate\train.py `
  --config experiments\v5\innovation\INNOVATION-003_confidence_local_gate\configs\RUN-001.yaml `
  --data-root D:\path\to\data `
  --run-dir D:\path\to\warehouse\RUN-001 `
  --expected-run-commit <本次pre-run提交的40位commit>
```

入口会先检查 CUDA、Git 干净状态、准确 commit、输入文件和“输出目录尚不存在”。正式输出固定为 `training.log`、`metrics.json`、`model_best.pt`、`checkpoint_last.pt`，每次写入都先落临时文件再原子替换。

## 结果与当前边界

- 三轮正式训练都使用 commit `61734def74d13c15a110ad3e98e609a17c2115c6`、配置哈希 `cba09034a3b773b78d51cb3c28f35f0fee95ce7536f41be617b7bc04c98cf2ee`、种子 `5` 和原 CUB xlsa17 评估口径。
- 三轮 `H` 为 `73.2037 / 73.5050 / 73.5736`，范围差 `0.3699`；每轮最佳评估 gate 均值为 `0.3996 / 0.4005 / 0.4250`。
- 2026-08-09 的首次正式启动在第 1 个 epoch 前失败：类别划分被直接加载到 CUDA，而母版构造阶段会先与 CPU 连续类别轴比较。失败输出单独保留为 `RUN-000-startup-failure`，不计入三轮正式训练；入口现改为先在 CPU 加载类别划分，再随模型统一迁移设备，模型公式、损失和评估口径不变。
- `IDEA-0005` 共享登记和完整实验证据均已回填；参数表状态为 `completed`，详细结果见 `result.md`，文件哈希见 `evidence/ARTIFACTS.md`。
- `beta=0.05` 固定，不能根据测试集成绩修改。
- `gate_bias` 与有效 slope 可学习；初始化分别为 `-1.0` 和 `1.0`。
- canonical `model/MyModel.py`、训练入口和正式配置不改。
