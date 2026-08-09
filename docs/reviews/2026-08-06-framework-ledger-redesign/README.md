# 框架实验台账重构审核记录

## 最终结论

`PASS`。`SYS-WORKFLOW-V3`、`DATA-FRAMEWORK-LEDGER-V1` 和 `UI-FRAMEWORK-TREE-V1` 可以作为 GTPJ 当前正式规范使用。没有启动训练、没有 push、没有部署，模型代码和评估含义没有改变。

## 为什么使用三路独立复核

本次同时改变实验命名、创建入口、框架晋级条件和历史数据映射，属于会影响以后所有实验记录的核心工作流改动，因此采用三路复核：

1. 命名与晋级规则：检查四类实验、参数表和子框架门槛是否真的一致。
2. 旧入口兼容：检查旧 `Trial / Attempt` 是否只剩历史回查能力，不能绕过新账本。
3. 数据完整性：检查历史代码、配置指纹、动态路由任务和局部分支消融计划是否被误写。

审核基准提交为 `4c737891422335cbd3fef1d1dcf3d802e981bec4`。前置治理提交为 `2b92fc68961c22d4037381ed183343ae233a4361`，框架账本绑定提交为 `546e651ee6e065628858ccae5354be40063013eb`。

## 三路复核结果

### 1. 命名与晋级规则：PASS

初审发现旧 `record-module-attempt` 还能写新运行，且“未通过”可能被模糊文字匹配成“通过”。已改为：

- 新规范启用后，旧命令只能带 `legacy_summary_only` 和旧提交证明来补历史摘要；
- 历史摘要不能写成 `keep / best`，也不能用于晋级；
- 子框架必须精确满足 `promotion_decision=promote`、`confirmation_status=confirmed`、`confirmed_H` 是有限数值、质量决定明确通过。

复审的框架相关 14 项、旧 Attempt 相关 4 项和门禁定向 4 项测试均通过，四项工作流校验和差异空白检查通过。

### 2. 旧入口兼容：PASS

初审发现 `new-trial`、“开新模块”和创新规划仍会推荐旧目录。已改为：

- 新规范启用时拒绝 `new-trial`；
- “开新模块”进入 `experiments/vX/innovation/`；
- 创新规划使用 `new-experiment --kind innovation`；
- 没有启用新标准的旧测试夹具仍能读取旧流程，保证历史兼容。

复审定向测试 7 项通过，工作流主测试 216 项通过，四项工作流校验和差异空白检查通过。

### 3. 数据完整性：PASS

复审核对结果：

- ATTEMPT-019 的新旧参数表均为 15 行；配置哈希、参数、种子、复跑关系和配置快照引用差异均为 0；
- `module_trials` 与 `v4` 历史树均为 0 文件改写、0 文件删除，没有伪造 `framework/v4`；
- 动态路由仍是 2 个创新运行加 8 个调参运行，共 10 个可核实运行；其余 18 个 Attempt 只作为历史批次摘要；
- V1、V2、V3 的历史代码引用与配置指纹可以回查，没有用当前 V5 冒充旧证据；
- 未启动训练，ATTEMPT-019 仍全部为 `planned`。

## 主助手机器验证

```text
python -m unittest discover -s tests -p "test_*.py"
Ran 239 tests in 160.308s
OK

python workflow/gtpj_workflow.py validate-framework-ledgers
validate-framework-ledgers-ok

python workflow/gtpj_workflow.py validate
validate-ok

python workflow/gtpj_workflow.py validate-workflow-consistency
validate-workflow-consistency-ok

python workflow/gtpj_workflow.py audit-boundary
audit-boundary-ok

git diff --check
通过
```

## 最终决定与边界

- 正式入口只有 `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`。
- 历史 Trial/Attempt 文件不删除，因为它们是旧实验的原始证据；它们已退出新工作入口。
- 不完整的历史参数只写 `legacy_summary_only`，没有猜测或补造。
- 本次没有改变模型、训练配置或评估语义，没有启动服务器训练。
- 本次只完成本地分支和提交，没有执行 push、合并或发布。
