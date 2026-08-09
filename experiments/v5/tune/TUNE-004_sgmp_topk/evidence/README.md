# 证据入口

- 状态：`pre_run_gated`
- 实现审核：`review_pending / review-1`
- 运行方式：`server_detached_role_only`
- 当前只有冻结配置、参数表和服务器计划
- TUNE003 与 TUNE004 绝不合并
- `K16+topk16` 会被 `N-1` 上限截成 15，该组合不在本轮
- 训练结果、receipt、metrics、日志和 checkpoint：尚不存在
- 两种子双重复不是 confirmation
