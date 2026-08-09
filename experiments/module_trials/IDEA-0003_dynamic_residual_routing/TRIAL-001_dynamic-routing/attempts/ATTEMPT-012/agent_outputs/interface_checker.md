# Interface Checker

role_key: interface_checker
execution_mode: role_only
status: allow

检查结论：本轮只改动态路由配置参数，不改数据集划分、seen/unseen 标签映射、类别顺序、logits 形状或 GZSL 指标语义。`dynamic_pse_mode` 固定为 `fixed`，不启用之前不支持的 sample PSE。
