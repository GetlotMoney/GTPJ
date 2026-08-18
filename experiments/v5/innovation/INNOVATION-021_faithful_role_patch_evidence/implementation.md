# 实现说明

- `frpe_model.py`：一次 patch×角色文本匹配同时产生主条件和三个诊断，避免重复视觉前向。
- `train.py`：使用 mmap 读取大型 patch cache；100/50 验证只选择主条件强度；选择状态保存后才加载 official patch/CLS/labels。
- `lambda=0` 精确退回 Mean8；模块没有可训练参数，不做最终 refit。
