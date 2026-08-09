# V5-INNOVATION-010 质量检查

```text
decision: reject
status: completed_not_keep
result_status: rejected
promotion_decision: rejected
evidence_level: valid_single_run
confirmation_status: not_applicable
single_seed: true
```

## 先说结论

`RUN-001` 是一次可追溯、成功结束的完整训练，但不是一个值得保留的模型结果。最佳 `H=58.917815`，比 V5 重复均值 `74.44` 低 `15.52` 个百分点，因此只登记为拒绝证据，不进入 keep、confirmation 或 promotion。

## 运行与证据检查

- [x] 训练使用独立 B 工作树，代码提交为 `79caa199df67f81a04372a47bd054536e75d1319`。
- [x] 配置指纹为 `5a14dc9e8db8ef72fd4bbf62a35ab49f08b0c0b09b238db12b1121ceb4a3b7a0`，seed=5，50 epoch。
- [x] 启动收据 SHA-256 为 `763e9fc227c85ea59bae9b2ff928974f408cb4b7a9eeb153db4b45396a754dd7`。
- [x] 结束收据记录 `returncode=0`，并与封口日志的命令、进程和结束时间一致。
- [x] 封口日志 SHA-256 为 `b6bd5fb3d6c90d4528212956b22885534ec310cb9fa537a3ee7d5bb2de29f13e`。
- [x] `final_metrics.json` 状态为 `completed`，完整记录 U/S/H/ZS、最佳 epoch、耗时、显存、模型大小和权重诊断。
- [x] 指标与诊断均为有限数；日志中没有非有限值停止或静默跳过评估。
- [x] 数据身份清单沿用共享只读文件 `/data/lby/projects/cv_project/GTPJ/.runtime/data_fingerprints/v5_8sent_inputs.json`，SHA-256 为 `6d71da3b580a6fabb29111d34b6d64d08f2aca93f8fe02ac8795972427ebb983`。
- [x] 8 句缓存形状为 `[200,8,768]`，SHA-256 为 `8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3`。
- [x] 原始日志、checkpoint 和大型诊断没有写入 Git。
- [ ] 服务器没有生成 `artifact_manifest.json`；因此不填写 `artifact_manifest_sha256`，也不把本结果升级为 promotion 证据。

缺少 manifest 不改变“这次运行失败还是成功”的判断，因为启动/结束收据、封口日志和最终指标已经互相对齐；但它阻止本结果被包装成更高等级的正式晋级证据。这里没有补造 manifest。

## 方法表现检查

- 最佳 epoch=1，`U/S/H/ZS=47.043979/78.809130/58.917815/75.780660`。
- 到第 50 轮，句子和区域选择更集中，但 `H` 降到 `48.44`，unseen 指标降到 `33.44`。
- 最佳轮 `global/local/final=5.243061/0.115244/5.266110`；局部分支经 0.2 融合后只增加约 `0.44%`。
- B 相比 A 更省训练时间和显存，但 `H` 仍低 `0.49` 个百分点；相比 V5 低 `15.52` 个百分点。
- 受控诊断可以追到句槽、region rank、patch 编号和坐标，但没有原图叠加，不能声称语义定位已经人工验证为合理。

## 稳定性边界

只有 seed=5 一次运行，不能估计均值、方差或“提升是否超过重复训练波动”。由于当前结果远低于 V5 且没有超过 A，本轮无需为了挽救该配置追加重复；若未来改变核心交互公式，应登记为新实验，而不是把新配置混入本次 `RUN-001`。

## 最终决定

`reject`。保留这次负结果证据，不保留为候选，不启动 confirmation，不 promotion。
