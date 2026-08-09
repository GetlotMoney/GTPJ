# 质量检查

- [x] 三个来源 checkpoint 的实验 ID、commit、配置 SHA 和 seen/unseen 划分匹配。
- [x] 三个 RUN 均 `status=completed`，固定使用 `k=5`、`residual_cap=0.25`。
- [x] top-k 外类别不能被改判，指标映射与 rescue/harm 语义通过测试和独立复核。
- [x] 输出目录独立且不覆盖；每个目录只有日志和指标。
- [ ] 三次 H 均未提高，因此不得作为有效创新或 promotion 候选。
