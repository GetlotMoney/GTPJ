# V5-INNOVATION-012：8 句话纯 CLIP 全局基线

```text
experiment_id: V5-INNOVATION-012
kind: innovation
status: pre_run
base_template_id: MODEL-V5-TEMPLATE-V2
base_template_commit: fb4b29b04087640890a532f105cb527d3a8c461b
implementation_branch: codex/v5-global8-baseline-pse
experiment_branch: exp/v5/innovation/innovation-012-global8-clip-baseline
planned_runs: 1
```

## 问题与基线

从零重新建立当前研究线：冻结 CLIP，只使用图像 CLS 全局特征和 8 句话组成的类别文本原型，能得到什么真实 U/S/H/ZS？

8 句话固定为 6 个局部部位、1 个全局外观和 1 个独特判别特征。每句话先独立 L2 归一化，再等权平均，最后再次归一化为一个类别原型。分类分数是 CLS 与类别原型的余弦相似度。配置在计算前强制核对 8 个输入文件 SHA-256 和 xlsa17 的 200 类顺序；输出 RUN 目录必须不存在，并由入口排他创建。

本基线没有训练参数，不包含 PSE、区域匹配、局部分支、ICSA、FGVD、BVSA、SGMP、辅助损失或推理校准。它只负责给后续单模块实验提供零号参照。入口要求 tracked worktree clean，并把运行时准确 Git commit 写入结果 JSON。

## 运行

```text
/data/lby/.conda/envs/dvsr_gpu/bin/python \
  experiments/v5/innovation/INNOVATION-012_global8_clip_baseline/evaluate.py \
  --config experiments/v5/innovation/INNOVATION-012_global8_clip_baseline/config.yaml \
  --output <独立 Warehouse RUN-001 目录>/metrics.json
```

结果完成后回填 `PARAMETER_MATRIX.csv` 和 `result.md`。
