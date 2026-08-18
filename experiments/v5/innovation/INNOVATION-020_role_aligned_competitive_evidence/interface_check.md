# 接口检查

- 句子：`[200, 8, 768]`；图像 CLS：`[N, 768]`。
- candidate classes：一维、唯一、全局类编号 0..199。
- logits：`[N, C]`；逐角色贡献：`[N, C, 8]`。
- `lambda=0` 精确退回同次 Mean8 raw score。
- rival 始终从完整 200 类文本构造，不因 pseudo candidate 集合变化。
- official test 文件在选择状态保存后才可达。
