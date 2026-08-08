# runner_monitor 开跑检查

- reviewed_candidate_commit: `e612bd011d258163dd36074913c246883a4f4c44`
- reviewer: `/root/r5_recovery_audit`
- decision: **PASS**
- 结论：代码包必须包含三组提交，旧代码数据只读隔离真实可用；两张卡按波次推进，任一失败后不再派下一波；早期失败也能留下结果、收据和证据清单。
- 机器证据：专项测试 18/18 通过，Python 编译通过；服务器 bwrap 写入拒绝、正式数据无探针残留、GPU 0/1 空闲。

