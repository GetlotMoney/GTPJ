# 第二轮：母版身份、代码起点与运行绕过

```text
reviewer: model_math_review
decision: allow
final_head: fd6921992b873a2d01db73010479340f67e59060
```

## 审核发现

1. 母版代码提交不能同时包含一个预先写好的自身哈希，需要把代码提交和后续管理登记提交分开。
2. 只检查“记录的提交是祖先”会允许任意旧祖先冒充正式母版。
3. 非标准 Trial/Attempt 路径会跳过参数表冻结和启动收据的母版检查。
4. 旧 `run-workflow --formal` 虽检查一个实验目录，实际仍可计划另一套 Trial、版本和代码 Tag。
5. 活跃参数表说明仍教人使用已经退役的旧动态路由正式命令。

## 最终复核

- `template_registry_commit` 与母版代码 commit 分开记录；registry 必须属于本地 `main` 历史；
- 实验的母版编号、Tag、commit 必须与 registry 中的 `TEMPLATE.yaml` 完全一致；
- V5 新冻结和新启动只允许标准四类实验目录；
- 旧 receipt 与日志只允许恢复封存，不会重新启动训练；
- 旧动态路由正式 runner、正式 batch planner 和新旧式动态矩阵创建全部退役；`--debug-smoke` 保留；
- 多行 PowerShell/反斜杠调试命令不会被扫描器误判。

最终结论：B1、B2、B3、W1、W2 全部闭环，无阻断问题。
