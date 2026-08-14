# TE-PSE + VSC-Loss 实现合同

TE-PSE 模块和推理分数逐字复用 `V5-INNOVATION-015@b7f060af`，本实验只改变训练目标。

对 90% seen 训练子集中的归一化冻结图像特征，按 seen 类顺序计算：

```text
mu_c = normalize(mean_{i:y_i=c} normalize(x_i))
p_c  = b_c + alpha * e_c
M_cj = dot(mu_c, p_j) / T

L_v2s = CE(M, diag)
L_s2v = CE(M^T, diag)
L_vsc = 0.5 * (L_v2s + L_s2v)
L_total = L_image_ce + 0.1 * L_vsc
```

硬边界：

- `mu_c` 不得读取 10% validation 或 official seen/unseen tensor。
- `p_c` 必须是实际推理使用的未归一化有效类别向量，不能另造一套 prototype。
- `lambda_vsc=0.1` 固定且不搜索。
- checkpoint 仍只按 10% seen validation image CE 选择。
- official test 只在恢复最佳 checkpoint 后进行一个预注册评估阶段。
- 推理期不计算视觉中心或 VSC，不增加参数与分支。
