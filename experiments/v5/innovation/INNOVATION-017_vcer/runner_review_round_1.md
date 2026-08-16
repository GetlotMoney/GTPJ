# VCER Runner 审核：第 1 轮

```text
round: 1
reviewer_id: /root/vcer_runner_review1
reviewed_code_id:
  vcer.py: 143dc00f92383012bfe0c797391dbf6a6e170057f4e3484765e2f8893a7dc720
  train.py: 3cfed93b1dfd77e55523dd4715af74156b571bd516b47fad3730ab1077985a34
  config.yaml: 0127650b913487db8d677e197ceb1ad803e6c4f979ade9854f079f1fab9bfa67
  tests/test_v5_vcer.py: 7b1ba15f8c78be14292c5186e73cec873ef921b4960d4359a8a9f3728f787d1b
  tests/test_v5_vcer_runner.py: 7ac3bb52254ddcefa87eb63b7574c07f262def327a3e43f432fb4b46a665b18b
machine_test_ref: py_compile pass; unittest 16/16 pass; git diff --check pass
unresolved_blockers: 0
decision: pass
```

## 审核闭环

- 初审发现配置缺少 `class_order_sha256`，正式入口会在训练前报错；已补入冻结值并由真实 `att_splits.mat` 测试。
- X2 重建改为逐元素核对并直接使用 checkpoint 的 sentence/adapted-class buffers，保持历史 Value/Output、LayerNorm 与 `base_part + role_part.sum` 顺序。
- loss、梯度和更新后参数均增加 NaN/Inf 硬停止。
- 已确认全局标签到 seen-local target、200 类 GZSL、50 类 ZS、先保存 checkpoint 后读取 official，以及输出不覆盖边界。

## 未覆盖

尚未执行真实 4090 allocator/吞吐探针，未加载大缓存或 official tensor，未启动训练。
