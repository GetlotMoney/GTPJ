# 05 — 工具代码详解

> 对照 `tools/dataset.py` + `tools/helper_func.py`，讲数据怎么加载、特征怎么提取、评估怎么做。

---

## 第一部分：`tools/dataset.py` — 数据加载

### `ImgDataset`（行 10-88）

这是一个标准的 PyTorch `Dataset`，实现按需读取图片：

```python
class ImgDataset(Dataset):
    def __init__(self, image_files, labels, dataset_name, transform=None, root_dir=None):
        self.image_files = image_files   # 图片路径列表（来自 .mat 元数据）
        self.labels = labels             # 对应的标签
        self.transform = transform       # 预处理（torchvision transforms）

    def __len__(self):
        return len(self.image_files)     # 总共有多少张图

    def __getitem__(self, idx):
        # 1. 解析路径
        img_path_raw = self.image_files[idx]

        # 2. 根据数据集清洗路径
        # CUB: .../images/001.Black_footed_Albatross/xxx.jpg
        # 从 'images' 关键词后面截取，前面可能是不同机器的绝对路径

        # 3. 拼接完整路径
        full_path = os.path.join(self.root_dir, rel_path)
        # 例如: data/CUB/images/001.Black_footed_Albatross/xxx.jpg

        # 4. 读图 + 预处理
        image = Image.open(full_path).convert('RGB')  # PIL 读图
        if self.transform:
            image = self.transform(image)            # 预处理
        return image, label
```

**`__getitem__` 什么时候被调用？** 当 DataLoader 遍历 `train_dataset` 时，每次取一个 batch 都会调用 N 次 `__getitem__`。

### `CUBDataLoader`（行 90-226）

这不是 PyTorch 的 DataLoader，是一个封装类。它的核心工作：

#### 读取元数据（行 144-188）

```python
# 1. 读取图片路径和标签
res101 = sio.loadmat('data/xlsa17/data/CUB/res101.mat')
self.image_files = res101['image_files']   # [11788] 所有图片路径
self.labels = res101['labels'] - 1         # 从 MATLAB 1-indexed 变 Python 0-indexed

# 2. 读取训练/测试分割
att_splits = sio.loadmat('data/xlsa17/data/CUB/att_splits.mat')
self.trainval_loc = att_splits['trainval_loc'] - 1     # 训练+验证图片索引
self.test_seen_loc = att_splits['test_seen_loc'] - 1   # seen 测试集索引
self.test_unseen_loc = att_splits['test_unseen_loc'] - 1 # unseen 测试集索引

# 3. 从标签推导 seen/unseen 类别编号
self.seenclasses = unique(self.labels[trainval_loc])      # [150] 全局编号
self.unseenclasses = unique(self.labels[test_unseen_loc]) # [50] 全局编号

# 4. 读取专家属性
att = att_splits['att'].T   # [200, 312] — CUB 有 312 维专家标注属性
```

### 均衡采样 vs 随机采样（行 199-226）

```python
if self.is_balance:   # 均衡采样
    # 每个 seen 类取 bucket_size // 150 个样本
    # 好处：每步每个类都出现，梯度方向更均衡
    for i_c in sampled_classes:
        idxs = self.idxs_list[i_c]   # 该类所有样本的索引
        sampled_idx = np.random.choice(idxs, n_per_class)
else:                  # 随机采样（GTPJ 默认）
    # 从所有训练样本中随机选 batch_size 个
    batch_idxs_local = np.random.choice(total_train, batch_size, replace=False)
```

**GTPJ 用 `is_balance=False` 是因为**：GZSL 下只需要对 seen 类做分类，每个 seen 类样本数相近（~30-60 张），不需要额外平衡。

---

## 第二部分：`tools/helper_func.py` — 特征提取和评估

### `get_clip_spatial_features(clip_model, images)`（行 59-83）

这是最重要的辅助函数之一。它手动拆解了 CLIP ViT 的 forward 过程，**为了拿到中间层的 patch 特征**（而不仅仅是最后的 CLS token）。

```python
def get_clip_spatial_features(clip_model, images):
    # images: [B, 3, 336, 336]

    with torch.no_grad():  # 不需要梯度

        # 步骤 1: Patchify — 用卷积把图像切成 24×24=576 个 patch
        x = clip_model.visual.conv1(images)
        # 卷积核 14×14，步长 14，336/14 = 24
        # 输出 [B, 768, 24, 24]
        x = x.reshape(x.shape[0], x.shape[1], -1)  # [B, 768, 576]
        x = x.permute(0, 2, 1)                     # [B, 576, 768]

        # 步骤 2: 拼 CLS token（"火车头"）
        class_embedding = clip_model.visual.class_embedding  # [768]
        # 扩展成 [B, 1, 768]
        cls_token = class_embedding.unsqueeze(0).unsqueeze(0).expand(B, 1, -1)
        x = torch.cat([cls_token, x], dim=1)  # [B, 577, 768]

        # 步骤 3: 加位置编码
        x = x + clip_model.visual.positional_embedding  # [577, 768]

        # 步骤 4: LayerNorm 预处理
        x = clip_model.visual.ln_pre(x)

        # 步骤 5: Transformer（12 层 ViT）
        x = x.permute(1, 0, 2)              # [577, B, 768] — Transformer 格式
        x = clip_model.visual.transformer(x) # 全局交互
        x = x.permute(1, 0, 2)              # [B, 577, 768] — 恢复

        # 步骤 6: LayerNorm 后处理 + 最终投影
        x = clip_model.visual.ln_post(x)
        if clip_model.visual.proj is not None:
            x = x @ clip_model.visual.proj   # 投影到 768 维共享空间

    # 返回 [B, 577, 768]
    # x[:, 0, :]   → CLS token（全局特征）
    # x[:, 1:, :]  → patch tokens（576 个局部特征）
    return x
```

**为什么不直接用 `clip_model.encode_image()`？** 因为 `encode_image` 只返回最后的 CLS token `[B, 768]`，丢弃了 576 个 patch 特征。GTPJ 的 FGVD 需要这些 patch 来做频域选择。

### 评估函数调用链

```
eval_zs_gzsl(dataloader, clip_model, model, device)
  │
  ├─ _load_test_cache(device)     ← 尝试加载测试集缓存
  │   ├─ seen_feat [N_seen, 768]
  │   ├─ seen_patch [N_seen, 576, 768]
  │   ├─ unseen_feat [N_unseen, 768]
  │   └─ unseen_patch [N_unseen, 576, 768]
  │
  ├─ _eval_from_cache(seen_feat, seen_label, ...)
  │   └─ 遍历 seen 测试集 → model(clip_input, is_train=False) → 取 argmax 预测
  │       └─ compute_per_class_acc_gzsl()  → 每个类单独算准确率，最后取平均
  │
  └─ _eval_unseen_from_cache(unseen_feat, unseen_label, ...)
      └─ 遍历 unseen 测试集 → model(clip_input, is_train=False)
          ├─ GZSL: 全 200 类取 argmax
          └─ ZSL: 只在 unseen (50) 类内取 argmax
```

### `compute_per_class_acc_gzsl()`（行 440-450）

```python
def compute_per_class_acc_gzsl(test_label, predicted_label, target_classes, in_package):
    per_class_accuracies = torch.zeros(len(target_classes))

    for i in range(len(target_classes)):
        is_class = test_label == target_classes[i]  # 找出这个类的所有样本
        if is_class.sum() > 0:
            # 该类准确率 = 预测正确的样本 / 该类总样本
            correct = (predicted_label[is_class] == test_label[is_class]).sum()
            per_class_accuracies[i] = correct / is_class.sum()

    return per_class_accuracies.mean()  # 对所有类取平均
```

**为什么是按类平均而不是全局平均？** GZSL 的标准做法。如果 unseen 某个类有很多测试样本，全局平均会被它主导；按类平均每个类权重相同，更公平。

---

## 完整数据流总结（从磁盘到评估结果）

```
╔════════════════════════════════════════════════════════════════════════╗
║                         离线预处理（只做一次）                         ║
╠════════════════════════════════════════════════════════════════════════╣
║  1. GPT 生成 200 个类 × 7 句描述文本                                  ║
║  2. CLIP 文本编码器 → class_text_embeds [200, 768]                    ║
║  3. CLIP 文本编码器 → gpt_sentence_embeds [200, 7, 768]               ║
║  4. CLIP 图像编码器 → CUB_train_features.pt [N_train, 577, 768]       ║
║  5. CLIP 图像编码器 → CUB_test_*_features.pt                          ║
╚════════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔════════════════════════════════════════════════════════════════════════╗
║                         训练时（每个 epoch）                            ║
╠════════════════════════════════════════════════════════════════════════╣
║  1. 采样 batch: idx = random_perm[:64]                                 ║
║  2. 读缓存: cls_batch [64, 768], patch_batch [64, 576, 768]           ║
║  3. 拼特征: clip_features = [cls, patch] → [64, 577, 768]              ║
║  4. 模型前向: GTPJ(clip_features, is_train=True)                       ║
║     - PSE: all_text [200, 768]                                         ║
║     - ICSA: all_text_cond [64, 200, 768]                               ║
║     - Global: s_global [64, 200]                                       ║
║     - FGVD+BVSA: s_local [64, 200]                                     ║
║     - Fuse: s_final [64, 200] → logits [64, 150]                       ║
║  5. 计算损失: compute_loss(logits, labels)                              ║
║  6. 反向传播: loss.backward() → optimizer.step()                        ║
╚════════════════════════════════════════════════════════════════════════╝
                              │
                              ▼
╔════════════════════════════════════════════════════════════════════════╗
║                         评估时（每个 epoch 结束）                       ║
╠════════════════════════════════════════════════════════════════════════╣
║  1. 加载测试集缓存（seen + unseen）                                     ║
║  2. seen 测试: GTPJ(seen_feat, is_train=False)                         ║
║     → logits [B, 200] → argmax 预测 → seen 准确率                      ║
║  3. unseen 测试: GTPJ(unseen_feat, is_train=False)                      ║
║     → GZSL: argmax over 200 → unseen 准确率                            ║
║     → ZSL: argmax over unseen 50 → ZS 准确率                           ║
║  4. H = 2×S×U/(S+U)                                                    ║
║  5. 如果 H > best_H → 保存模型                                          ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 关键文件路径速查表

| 文件 | 内容 | 形状 |
|---|---|---|
| `data/CUB/cub.pt` | GPT-4 描述词典 | `{类名: [句子列表]}` |
| `data/cache/CUB_train_features.pt` | 训练集 CLS 特征 | `[N_train, 768]` |
| `data/cache/CUB_train_patch_features.pt` | 训练集 patch 特征 | `[N_train, 576, 768]` fp16 |
| `data/cache/CUB_train_labels.pt` | 训练集标签 | `[N_train]` |
| `data/cache/CUB_class_text_embeds.pt` | CLIP 模板文本嵌入 | `[200, 768]` |
| `data/cache/CUB_gpt55_text_embeds.pt` | GPT-5.5 描述嵌入 | `[200, 768]` |
| `data/cache/CUB_gpt55_sentence_embeds.pt` | GPT-5.5 句子级嵌入 | `[200, 7, 768]` |
| `data/cache/CUB_test_seen_*.pt` | seen 测试集缓存 | 同上 |
| `data/cache/CUB_test_unseen_*.pt` | unseen 测试集缓存 | 同上 |
| `train_log/CUB/best_model_*_H7444.pth` | 最佳模型权重 | — |
| `train_log/CUB/ckpt_full_*.pth` | 完整 checkpoint | — |
| `train_log/CUB/training_log_*.txt` | 训练日志 | — |

---

## 你已经学会

全部 5 篇教程到此结束。你应该已经掌握：

- [ ] PyTorch 所有代码中用到的核心概念
- [ ] GTPJ 的完整数据流和架构
- [ ] MyModel.py 的每个类和函数的细节
- [ ] 训练脚本的全流程
- [ ] 数据加载、特征缓存、评估函数
- [ ] 整个框架从磁盘数据到最终 GZSL 指标的端到端链路

回到 [教程目录](00_README.md)
