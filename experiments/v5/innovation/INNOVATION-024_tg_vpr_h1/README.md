# V5-INNOVATION-024：TG-VPR-H1 独立模型

本目录只保留已经通过多 seed 验证的 H1 路径：三组语义、单一 768 维 Value 变换、双层残差、seen-only原型适配和余弦分类。

```text
六个局部描述 → 局部组 ┐
独特描述       → 独特组 ├→ 单Value路径 → seen原型 → CLIP余弦分类
整体描述       → 整体组 ┘
unseen描述     → Mean8 ────────────────────────┘
```

本目录不包含 X1/X2、head搜索、CR、BR、GA 或 CSVG 失败模块。

seed 7独立迁移RUN已通过：checkpoint全部13个模型张量、50轮history、三组权重和U/S/H/ZS均与来源RUN逐项一致。

```powershell
conda run -n dvsr_gpu python experiments/v5/innovation/INNOVATION-024_tg_vpr_h1/train.py `
  --config experiments/v5/innovation/INNOVATION-024_tg_vpr_h1/config.yaml `
  --output-dir D:/path/outside/repo/RUN-001 `
  --expected-commit <完整commit> `
  --run-id RUN-001
```
