# 实现

冻结 `V5-INNOVATION-013/RUN-002` 的共享 PSE checkpoint，只对最终 GZSL logits 做一项改动：所有 seen 类列统一减去标量 `gamma`。

`gamma` 在最终 test U/S/H 上网格搜索，因此输出固定为 `test_score_search`，不属于 confirmation evidence。
