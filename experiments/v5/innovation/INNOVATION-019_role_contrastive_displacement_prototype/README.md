# V5-INNOVATION-019：角色对比位移原型（RCDP）

## 唯一问题

在纯 CLIP 全局图像特征和 GPT-5.5-derived 八句话上，使用“同角色跨类别 rival 差值”构造一个 seen/unseen 完全同式的文本原型模块，能否独立提高 GZSL H？

## 冻结公式

原始原型：

```text
p0[c] = normalize(mean_r(t[c,r]))
```

每个角色只在同一角色下寻找最相似的非自身类别：

```text
j*[c,r] = argmax_(j != c) cosine(t[c,r], t[j,r])
d[c,r]  = t[c,r] - t[j*,r]
```

八个角色固定等权，经角色独立低秩映射后形成有界位移：

```text
z[c,r] = Up[r](GELU(Down[r](d[c,r]))) / sqrt(rank)
bounded[c,r] = z[c,r] / max(1, ||z[c,r]||_2)
contrib[c,r] = gate * ||mean_r(t[c,r])||_2 / 8 * bounded[c,r]
p[c] = normalize(mean_r(t[c,r]) + sum_r(contrib[c,r]))
```

因此单角色贡献范数不超过 `gate*||原始均值||/8`，八项总位移不超过原始均值范数的 `gate<0.35`，不会因低秩权重变大而失控。`Up` 零初始化，初始状态精确回到纯 CLIP 八句均值。没有句间 attention、双专家、seen/unseen 两套公式、视觉 Adapter、局部分支或 gamma。

## 无 test 选参协议

1. 使用 xlsa17 `train_loc` 的 100 类；每类 20% 图像只用于 pseudo-seen S，剩余图像训练。
2. 使用 `val_loc` 的 50 个不重叠类别作为 pseudo-unseen U；100/50 的全部 150 类联合竞争，按 H 选择 epoch。
3. 选定 epoch 后，新建模型并在完整 `trainval_loc` 的 150 个正式 seen 类上从零重训。
4. checkpoint 保存后才加载 official test；纯 CLIP 基线和 RCDP 各评估一次，不再修改任何参数。

## 成功门

- 相对同次纯 CLIP 八句基线 `delta_H >= 0.50`：保留 RCDP，随后才允许验证第二模块 RPV。
- 否则记录 `stop_no_gain`，不叠加 RPV、gamma 或其他模块掩盖失败。

## 正式运行

```bash
python experiments/v5/innovation/INNOVATION-019_role_contrastive_displacement_prototype/train.py \
  --config experiments/v5/innovation/INNOVATION-019_role_contrastive_displacement_prototype/config.yaml \
  --run-dir <WAREHOUSE>/runs/v5/innovation/V5-INNOVATION-019/RUN-001 \
  --expected-commit <PRE_RUN_COMMIT> \
  --expected-config-sha256 4e9ee7b5b76f5e539724c8a92bea4970a1de607b922ca43711cb5370990e3f53
```
