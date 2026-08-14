# V5-INNOVATION-015：TE-PSE 角色竞争证据校准

```text
experiment_id: V5-INNOVATION-015
status: completed_stop_no_gain
base_template: MODEL-V5-TEMPLATE-V2
base_commit: fb4b29b04087640890a532f105cb527d3a8c461b
formal_training_started: true
run_commit: b7f060afdd6d42baeee25b4d3068389085d88286
```

## 只回答一个问题

在冻结的 GPT-5.6 八句纯 CLIP 全局基线 `H=64.16403868322334` 上，只增加一个无 self-attention 的角色竞争证据项，是否能够提高 official GZSL H，同时保持 U 和 ZS 不发生不可接受的坍缩？

本轮不加入 visual adapter、seen-bias gamma、局部分支、ICSA、topology 或辅助损失。它们的收益不能混入 TE-PSE 的因果结论。

## 冻结结构

- 全局 anchor：八句话归一化后等权平均，再归一化。
- 证据角色：六个局部角色加 unique；overall 只参与全局 anchor。
- 每个类别、每个角色只选择同角色文本空间中最相似的其他类别作为 rival。
- 角色权重由 target/rival 文本区分度确定，不学习 attention 或 role MLP。
- seen/unseen 使用同一组 rival 规则、角色权重和同一个全局强度。
- 唯一训练参数：一个正值、有界、全局共享的 evidence strength。
- checkpoint：只按 seen 训练集内部 10% validation CE 选择。
- official test：冻结 checkpoint 后才计算一次，同时报告预先固定的 alpha=0 基线和 TE-PSE。

精确公式见 `implementation.md`，来源边界见 `module_source.md`。

## 冻结参数

| 项目 | 值 | 理由 |
|---|---:|---|
| text cache | GPT-5.6 8句 | 与当前干净 B0 对齐 |
| evidence roles | 7 | 6 local + unique；overall 保持全局职责 |
| temperature | 0.05 | 与 B0/SharedPSE 已有打分尺度一致 |
| evidence cap | 0.5 | 每类证据向量范数不超过 1，因此等价类别向量的偏移范数小于 0.5 |
| evidence init | 0.1 | 从靠近纯 CLIP 的小修正开始，不从强变换开始 |
| trainable parameters | 1 | 防止 seen-only 训练学习类别专属重写 |
| seed | 5 | 首个信号检查；有收益后才增加第二 seed |

这些数值在本轮不做 sweep。任何后续数值搜索必须登记为独立 tune，不能回写本次原始模块结果。

## 预先判定

- `keep_candidate`：raw、无 gamma 的 H 高于同次 B0，U/ZS 无不可接受坍缩，逐角色加法误差不超过 `1e-6`，再进入第二 seed 和机制 control。
- `stop_no_gain`：H 不升、强度收敛到接近 0，或收益只能依靠后加 gamma/adapter 才出现。
- 不论结果如何，都必须报告完整 `U/S/H/ZS`、evidence strength、角色权重、rival 类和分解误差。

## 稍后启动命令

本轮只冻结，不执行。正式启动时必须把占位符替换为最终审核等价提交，并把输出目录放在 Warehouse：

```powershell
conda run -n dvsr_gpu python experiments/v5/innovation/INNOVATION-015_te_pse/train.py `
  --config experiments/v5/innovation/INNOVATION-015_te_pse/config.yaml `
  --run-dir <WAREHOUSE>/runs/v5/innovation/V5-INNOVATION-015/RUN-001 `
  --expected-commit <FROZEN_COMMIT> `
  --run-id RUN-001
```

输出目录已存在时训练入口直接拒绝，禁止覆盖历史 RUN。
