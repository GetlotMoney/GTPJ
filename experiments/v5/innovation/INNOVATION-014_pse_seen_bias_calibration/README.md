# V5-INNOVATION-014：PSE seen 偏置校准

固定 `V5-INNOVATION-013/RUN-002` 的共享 PSE，只加入一个可解释标量 `gamma`：从所有 seen 类 logits 中减去同一个值，直接修正 `S=74.99、U=63.23` 的不平衡。

按 owner 当前授权，`gamma` 直接在最终 `test_seen/test_unseen` 上搜索，以最快速度确定该方向的上限。

这是偏置校准模块，不作为 PSE 的新颖性声明。结果固定标记为 `test_score_search` 和 `not_confirmation_evidence: true`，只能用于路线选择，不能作为无偏泛化、confirmation 或 promotion 证据。`ΔH > 0` 才保留；否则删除该模块，转向语义漂移约束。
