# 04 — 训练代码详解 (`train_GTPJ_CUB.py`)

> 对照仓库根目录的 `train_GTPJ_CUB.py`（当前共 1017 行），逐段讲解训练全流程。

---

## 文件结构总览

```
行 1-24     导入
行 27-49    缓存路径定义
行 53-86    日志工具 + 配置加载
行 87-96    随机种子设置
行 99-131   训练参数打印
行 133-193  模块配置摘要打印
行 197-204  加载冻结 CLIP
行 208-309  加载数据集 + 图像特征缓存
行 313-479  编码文本特征（类名 CLIP 嵌入 + GPT 描述嵌入）
行 482-513  初始化 GTPJ 模型
行 519-520  优化器 + 学习率调度器
行 525-653  Resume 系统（断点续训）
行 657-692  多段训练系统
行 697-750  输出路径、混合精度和 clip_only 快车道
行 752-1017 训练、评估与 checkpoint 保存（核心）
```

---

## 第一部分：导入（行 1-25）

```python
import torch
import torch.optim as optim          # 优化器（Adam）
import numpy as np
import yaml                           # 读 YAML 配置文件
import clip                           # OpenAI CLIP 官方库
from types import SimpleNamespace     # 让配置项可以用 config.key 访问

from model.MyModel import GTPJ        # ★ 你的模型
from tools.dataset import CUBDataLoader
from tools.helper_func import eval_zs_gzsl, get_clip_spatial_features
from tools.reproducibility import configure_reproducibility, make_batch_generator
```

### 缓存路径（行 27-43）

```python
CACHE_DIR = './data/cache'
CACHE_TRAIN_FEAT   = './data/cache/CUB_train_features.pt'       # [N, 768] CLS 特征
CACHE_TRAIN_LABEL  = './data/cache/CUB_train_labels.pt'         # [N] 标签
CACHE_TRAIN_PATCH  = './data/cache/CUB_train_patch_features.pt' # [N, 576, 768] patch 特征
```

这些 `.pt` 文件是 `torch.save` 保存的张量。**离线预处理好的 CLIP 特征**，训练时直接加载到内存，不用每次重新跑 CLIP（太慢）。

---

## 第二部分：配置加载（行 62-96）

```python
parser = argparse.ArgumentParser()
parser.add_argument("--config", default="./config/GTPJ_cub_gzsl.yaml")
args = parser.parse_args()

# 读 YAML
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# YAML 格式: {key: {value: actual_value}} → {key: actual_value}
config = {k: v['value'] if isinstance(v, dict) and 'value' in v else v
          for k, v in config.items()}

# 转成 SimpleNamespace：config.batch_size 而不是 config['batch_size']
config = SimpleNamespace(**config)
```

### 随机种子（行 87-96）

```python
seed = 5  # 固定种子保证可复现

repro_state = configure_reproducibility(
    seed,
    strict_determinism=False,     # 不强制严格确定性（会大幅降低速度）
    deterministic_warn_only=True, # 不确定操作只警告不报错
)
```

`configure_reproducibility` 做了：
- `torch.manual_seed(seed)` — 固定 PyTorch 随机数
- `torch.cuda.manual_seed_all(seed)` — 固定 CUDA 随机数
- 设置 `cudnn.deterministic` 等 CUDA 相关选项

---

## 第三部分：加载 CLIP（行 197-204）

```python
clip_model, _ = clip.load("ViT-L/14@336px", device=config.device)
# 下载/加载预训练 CLIP ViT-L/14@336px 模型
# ViT-L = Vision Transformer Large
# 14 = patch size 14×14
# 336px = 输入分辨率 336×336

clip_model = clip_model.float()  # 确保 float32
clip_model.eval()                # 评估模式（关闭 Dropout 等）

for p in clip_model.parameters():
    p.requires_grad = False      # ★ 冻结所有参数
```

**冻结 CLIP 是 GTPJ 的核心设计选择**：CLIP 只做特征提取，不参与训练。所有可训练的参数都在 GTPJ 模型里。这样做的原因：
1. CLIP 是在 400M 图文对上训练的，它的知识应该保留
2. GZSL 训练数据只有几千张图，微调 CLIP 会破坏其泛化能力
3. 只训练 GTPJ 的轻量适配层，参数量小（~10M），训练快

---

## 第四部分：加载数据（行 208-309）

### CUBDataLoader（行 210）

```python
dataloader = CUBDataLoader('.', config.device, is_balance=False)
```

`is_balance=False` → 随机采样。`is_balance=True` → 均衡采样（每类取相同数量）。

### 特征缓存加载优先级（行 245-309）

```
优先级 1: 多视角增强缓存 (use_aug_cache=True, CUB_train_*_aug.pt)
优先级 2: 单视角 patch 缓存 (CUB_train_patch_features.pt)
优先级 3: 单视角 CLS 缓存 (CUB_train_features.pt)  [legacy]
优先级 4: 实时提取（慢，不建议）
```

当前 v5 默认用的是优先级 2：单视角 patch 缓存。

### 内存管理技术

```python
# 1. pin_memory — 把 CPU 张量"钉"在固定内存区域
train_patches = train_patches.pin_memory()
# 好处：CPU→GPU 传输时，DMA 可以直接访问这块内存，不需要先拷贝到中间缓冲区
# 配合 non_blocking=True 实现异步传输

# 2. 异步 CPU→GPU 传输
patch_batch = train_patches[idx].to(config.device, non_blocking=True)
# non_blocking=True：发起传输后立即返回，不等待传输完成
# GPU 下一步需要这个张量时自动等待（隐式同步）
# 效果：传输和计算重叠，快 ~10-20%
```

---

## 第五部分：编码文本特征（行 313-479）

### 类名模板文本（行 313-332）

```python
# 每个类别生成一个 prompt："a photo of a Indigo Bunting, a type of bird."
prompts = [f"a photo of a {c}, a type of bird." for c in class_names]
text_inputs = torch.cat([clip.tokenize(p) for p in prompts])
with torch.no_grad():
    class_text_embeds = clip_model.encode_text(text_inputs).float()
# 结果: [200, 768] — CUB 200 类的 CLIP 模板文本嵌入
```

缓存到 `CUB_class_text_embeds.pt`，下次启动跳过这一步。

### GPT 描述编码（行 337-479）

```python
text_source = 'gpt55'  # 可选: gpt4 / claude / gpt55 / merge / weighted
```

为每个类别提供 7 句丰富的文本描述（如："A small songbird with vibrant blue plumage..."），替代简单的模板 prompt。

**关键逻辑**：如果开启了 PSE 自注意力（`use_pse_self_attention=True`），不仅要编码成平均嵌入（`[200, 768]`），还要保留句子级嵌入（`[200, M, 768]`），因为自注意力需要在句子维度上操作：

```python
if use_pse_sentence_text:
    gpt_sentence_embeds, hit, n_cls = _encode_description_sentences(...)
    # 返回 [200, M, 768] — M=7 个句子，每句 768 维
    gpt_text_embeds = gpt_sentence_embeds.mean(dim=1)
    # 平均作为 baseline 文本原型
```

---

## 第六部分：初始化模型（行 482-513）

```python
model = GTPJ(
    config,
    dataloader.seenclasses,        # [150] — seen 类编号
    dataloader.unseenclasses,      # [50]  — unseen 类编号
    seen_text_embeds=seen_gpt_embeds,     # [150, 768] GPT 描述（seen）
    unseen_text_embeds=unseen_clip_embeds, # [50, 768]  GPT 描述（unseen）
    class_attr=dataloader.att,            # [200, 312] CUB 专家属性
    attr_text_embeds=dataloader.clip_att,  # [312, 768] 属性文本原型
    seen_sentence_embeds=seen_sentence_embeds,  # [150, 7, 768] 句子级
    unseen_sentence_embeds=unseen_sentence_embeds,
).to(config.device)

# 模型搬到 GPU 后，所有 register_buffer 和 nn.Parameter 都会自动搬
# 包括 seenclass, unseenclass, seen_text_embeds 等
```

---

## 第七部分：优化器 + 调度器（行 519-520）

```python
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
# Adam: 自适应学习率优化器
# lr=0.001: 初始学习率
# weight_decay=1e-4: L2 正则化系数（防止过拟合）

scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)
# CosineAnnealing: 学习率按余弦曲线从 lr 降到 eta_min（默认 0）
# T_max: 半个余弦周期的长度
# 效果: epoch 1 到 epoch 30（或 T_max），lr 从 0.001 平滑降到 ~0
```

---

## 第八部分：Resume 系统（行 525-653）

### 三种续训模式

| 模式 | resume_lr_schedule | 行为 |
|---|---|---|
| 继续训练 | `continue` | 恢复 optimizer + scheduler 状态，epoch 接着数 |
| 重启 LR | `restart` | 只载权重，LR 从 0.001 重新开始 cosine |
| 微调 | `finetune` | 只载权重，LR=1e-4（或 finetune_lr），epoch 从 1 开始 |

### Checkpoint 保存格式

```python
# 完整 checkpoint（用于 resume）
torch.save({
    'epoch': epoch,
    'best_H': best_H,
    'best_metrics': best_metrics,
    'model_state_dict': model.state_dict(),       # 模型参数
    'optimizer_state_dict': optimizer.state_dict(), # 优化器状态
    'scheduler_state_dict': scheduler.state_dict(), # 调度器状态
}, 'ckpt_full_CUB_2026-...pth')

# 精简 checkpoint（只存最佳模型的权重）
torch.save(model.state_dict(), 'best_model_CUB_2026-..._H7444.pth')
```

---

## 第九部分：多段训练系统（行 657-692）

这是 v5 引入的重要特性。不再用 `epochs=30` 的单一 lr schedule，而是分多个阶段：

```yaml
lr_stages:
  - lr: 0.001
    epochs: 20
    eta_min: 1e-5
  - lr: 0.0001
    epochs: 20
    eta_min: 1e-6
    restart_from_best: false
  - lr: 1.0e-05
    epochs: 10
    eta_min: 1e-7
    restart_from_best: false
```

**三段策略含义**：
1. 第 1-20 轮：高学习率 0.001，快速学习大方向
2. 第 21-40 轮：中学习率 0.0001，精细调整
3. 第 41-50 轮：微学习率 0.00001，最后收敛

**`restart_from_best` 选项**：
- 当为 `True` 时，阶段切换时把模型权重回滚到当前 run 的历史最佳 checkpoint
- 等价于"early stopping at best + finetune from best"
- GZSL 领域（TransZero/MSDN）的标准做法，可比严格连续训练高 ~0.8 H

### 阶段切换代码

```python
if lr_stages and epoch in stage_boundaries and epoch < total_epochs:
    next_stage = lr_stages[next_idx]

    if bool(next_stage.get('restart_from_best', False)):
        # 回滚到最佳 checkpoint
        _ckpt = torch.load(CKPT_FULL_PATH)
        model.load_state_dict(_ckpt['model_state_dict'])

    # 重置 optimizer lr 和 scheduler T_max
    for g in optimizer.param_groups:
        g['lr'] = new_lr
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=new_T)
```

---

## 第十部分：训练循环（行 752-1017）— 最重要

### 每个 epoch 的结构

```
for epoch in range(start_epoch, total_epochs + 1):

    # ═══ 训练阶段 ═══
    model.train()                    # 开启训练模式

    for step in range(iters_per_epoch):   # 每个 epoch 有多少个 batch
        optimizer.zero_grad()        # 清零梯度

        # 步骤 1: 采样数据
        idx = random_perm[:batch_size]        # 随机选 batch 个样本
        batch_label = train_labels[idx]       # [64]

        # 步骤 2: 组装 clip_features
        # 从缓存读取 → CPU to GPU → 拼接 CLS + patch
        cls_batch = train_cls[idx].to(device).unsqueeze(1)     # [64, 1, 768]
        patch_batch = train_patches[idx].to(device)              # [64, 576, 768]
        clip_features = torch.cat([cls_batch, patch_batch], dim=1)  # [64, 577, 768]
        # dim=1 表示在第 1 维拼接：CLS [64,1,768] + patch [64,576,768] → [64,577,768]

        # 步骤 3: 前向传播 + 计算损失
        out_package = model(clip_features, is_train=True)
        # out_package 包含 logits [64, 150]、s_global、s_local 等

        in_package = out_package.copy()
        in_package['batch_label'] = batch_label
        loss_pack = model.compute_loss(in_package)
        loss = loss_pack['loss']

        # 步骤 4: 反向传播
        loss.backward()              # 计算所有参数的梯度
        optimizer.step()             # 用梯度更新参数

    # ═══ 调度器更新 ═══
    scheduler.step()                 # 每个 epoch 结束后更新学习率

    # ═══ 评估阶段 ═══
    acc_seen, acc_novel, H, acc_zs = eval_zs_gzsl(
        dataloader, clip_model, model, config.device)
    # 返回四个指标：seen 准确率、unseen 准确率、H 调和平均、ZS 准确率

    if H > best_H:
        best_H = H
        torch.save(model.state_dict(), BEST_MODEL_PATH)  # 保存最佳模型
```

### `model(clip_features, is_train=True)` 的形状变化

```
输入:  clip_features          [64, 577, 768]
        拆成:
          cls_token            [64, 768]
          patches              [64, 576, 768]

文本: all_text                 [200, 768]
        + ICSA →
      all_text_cond            [64, 200, 768]

全局: cls_token · all_text_cond → s_global  [64, 200]

局部: patches → FGVD 选 32 → FAE → BVSA → s_local  [64, 200]

融合: s_final = s_global + 0.2 × s_local         [64, 200]

输出: logits = s_final[:, seen_idx]                [64, 150]
```

### 每 20 步打印的损失项

```python
print_log(f"Step [{step+1:3d}/{iters_per_epoch}] | "
          f"Loss: {loss.item():.4f} | Avg: {avg_loss:.4f} | "
          f"CE: {ce_v:.3f}  Cons: {cons_v:.3f}  "
          f"Topo: {topo_v:.4f}  BMDD: {bmdd_v:.4f}  "
          f"MPP: {mpp_v:.4f}  Neg: {neg_v:.4f}")
```

**正常训练的预期损失范围**（经验值）：
- CE: 1.5~3.5（主要下降项）
- Cons: 0.01~0.5（稳定时很小）
- Topo: 0.01~0.1
- BMDD: 0.01~0.1
- MPP: 0.5~1.0
- Neg: 0.01~0.1

---

## 第十一部分：评估函数 `eval_zs_gzsl`（在 helper_func.py 中）

```python
def eval_zs_gzsl(dataloader, clip_model, model, device):
    model.eval()

    # 优先用缓存评估（快），没有缓存则实时提取（慢）
    if use_cache:
        # 从缓存加载测试集特征
        acc_seen  = _eval_from_cache(seen_feat, seen_label, model, seenclasses, ...)
        acc_novel, acc_zs = _eval_unseen_from_cache(unseen_feat, unseen_label, model, unseenclasses, ...)
    else:
        # 实时：读图像 → CLIP 提取特征 → 模型推理
        acc_seen  = val_gzsl_online(test_seen_loader, ...)
        acc_novel, acc_zs = val_zs_gzsl_online(test_unseen_loader, ...)

    # 计算 H（调和平均）
    H = (2 * acc_seen * acc_novel) / (acc_seen + acc_novel)
    return acc_seen, acc_novel, H, acc_zs
```

### GZSL 四个指标的含义

| 指标 | 含义 | 计算 |
|---|---|---|
| **S** (Seen Acc) | 在 seen 测试集上的准确率 | 正确预测 seen 类的样本 / seen 测试集总数 |
| **U** (Unseen Acc) | 在 unseen 测试集上的准确率 | 正确预测 unseen 类的样本 / unseen 测试集总数 |
| **H** (Harmonic Mean) | S 和 U 的调和平均 | H = 2×S×U / (S+U) |
| **ZS** (Zero-Shot Acc) | 只在 unseen 类别内比较 | 预测在 unseen 内部的最大值（不跟 seen 竞争） |

**为什么用调和平均？** 如果模型全预测 seen 类（S=100%），U 会很低（~0%）→ H ≈ 0%。调和平均惩罚极端不平衡，只有 S 和 U 都高，H 才高。

---

## 第十二部分：`model_mode='clip_only'` 快车道（行 729-750）

```python
if model_mode == 'clip_only':
    # 跳过训练，直接用 CLIP 零样本评估
    acc_seen, acc_novel, H, acc_zs = eval_zs_gzsl(...)
    print_log(f"GZSL-H : {H*100:.2f}%")  # 应该 ~60%
    raise SystemExit(0)  # 直接退出
```

这是验证代码和评估管线是否正常的快速检查——如果 `clip_only` 的 H ≠ 预期值，说明评估代码有问题。

---

## 第十三部分：混合精度训练（可选）（行 713-724）

```python
USE_AMP = False  # v5 默认关闭（为了可复现性）

if USE_AMP:
    with autocast('cuda', dtype=torch.bfloat16):
        out_package = model(clip_features, is_train=True)
        loss_pack = model.compute_loss(in_package)
        loss = loss_pack['loss']
    loss.backward()  # BF16 不需要 GradScaler
```

**BF16（bfloat16）**：和 float32 有相同的指数范围（8 位指数），只是精度位少（7 位 vs 23 位）→ 数值范围比 float16 大得多，不容易溢出 → 不需要损失放大（GradScaler）。

GTPJ 默认关闭 AMP 是因为：
1. 训练规模不大（几百万参数），不需要精度压缩
2. 为了严格的可复现性（AMP 引入非确定性）
3. 在 RTX 5070 Ti 上 BF16 自动转换有奇怪的显存占用问题

---

## 你已经学会

- [ ] 完整的训练流程：配置加载 → 数据准备 → 模型初始化 → 训练循环 → 评估
- [ ] 特征缓存系统（多视角 / patch / CLS / 实时提取四种模式）
- [ ] GPT 文本描述编码（类平均 vs 句子级）
- [ ] `pin_memory` + `non_blocking` 的 GPU 传输优化
- [ ] 三阶段 lr_schedule 的设计意图（快速学习 → 精细调整 → 收敛）
- [ ] `restart_from_best` 的 warm-restart 策略
- [ ] 每个训练 step 的 `zero_grad → forward → compute_loss → backward → step`
- [ ] Resume 系统的三种模式（continue / restart / finetune）
- [ ] GZSL 四个指标（S, U, H, ZS）的含义和计算
- [ ] `clip_only` 模式的用途

准备好后 → 进入 [05 — 工具代码详解](05_tools_explained.md)
