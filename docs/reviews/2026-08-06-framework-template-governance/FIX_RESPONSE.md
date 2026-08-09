# 修复回应

| 审核问题 | 最终处理 | 证明方式 |
|---|---|---|
| 历史代码未保留却登记宽泛目录 | 改为 `not_preserved + 具体证据` | 账本集成检查与负面测试 |
| 母版提交自指 | 分开记录母版代码 commit 与 `template_registry_commit` | registry 分离成功路径测试 |
| 任意祖先冒充母版 | 必须精确匹配 registry 的编号、Tag、commit | 祖先伪造负面测试 |
| 母版分支与 Tag 名称可错版 | 按框架版本和模板编号精确计算 | 错版本/错编号测试 |
| 非标准目录绕过冻结/启动 | V5 下非 canonical 路径明确拒绝 | freeze 与 receipt 负面测试 |
| 合法实验目录替另一套 Trial 放行 | 退役旧 `run-workflow --formal` | 正式旧 runner 负面测试 |
| 旧动态矩阵和 batch planner 仍可新建正式批次 | 创建入口退役，planner 仅保留 `--debug-smoke` | 两项入口负面测试 |
| 活跃说明仍教旧命令 | 改为标准四类实验参数表流程，并扩展扫描 | 文档一致性负面测试 |
| 扫描器误判多行 debug 命令 | 合并常见续行后再识别 `--debug-smoke` | 多行 debug 正面测试 |
| 旧已完成进程需要收口 | 允许已有 receipt+log 恢复封存，但不 gate、不 launch | 旧 receipt 恢复正面测试 |
