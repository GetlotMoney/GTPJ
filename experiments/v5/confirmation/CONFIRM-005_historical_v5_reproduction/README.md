# 老框架 V5 复现

- 问题：历史 V5 原始代码和原始配置能否把 H 恢复到约 74.40。
- 代码：使用审计包保存的历史源码，对应提交 4b259379d99c1a791442ea9e2fac0bb22b2411a9；该训练代码与正式 v5 Tag 的相关文件一致。
- 配置：原始 CONFIG_USED.yaml，seed=5，50 epoch，PSE outer ratio=0.65，local weight=0.2。
- 判断：任一独立运行 H>=74.40 才算恢复；最多 5 次，命中即停。
- 输出：5 次独立 Python 进程分别写入项目 .runtime/runs/v5/confirmation/V5-CONFIRM-005-old-framework/RUN-001..005，没有覆盖旧结果。
- 结果：5 次均未达到 74.40；最高 H=74.3230，均值 H=74.2326，属于接近但没有恢复。
- 代码差异：新旧框架的有效融合公式相同，最值得继续验证的是老代码多出的无效随机初始化是否改变了后续真实模块的初值和训练批次顺序，详见 code_difference.md。
