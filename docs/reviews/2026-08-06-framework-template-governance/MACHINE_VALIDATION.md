# 机器验证

## 为什么使用三轮审核

本次同时改变框架母版身份、实验代码起点、参数表冻结和真实训练启动边界，属于会改变核心工作流含义的跨模块改动，因此按项目规则使用三轮独立只读审核。机器测试不能被审核替代，最终提交仍单独跑完全量测试和全部结构检查。

## 最终对象

```text
base: a663595f1ac3fca63780b936284752b170bdb64b
head: fd6921992b873a2d01db73010479340f67e59060
branch: codex/framework-ledger-redesign
```

## 最终干净运行

| 命令 | 结果 |
|---|---|
| `python -m pytest tests/test_gtpj_workflow.py -q` | `251 passed in 182.88s` |
| `python workflow/gtpj_workflow.py validate` | `validate-ok` |
| `python workflow/gtpj_workflow.py validate-framework-templates` | `validate-framework-templates-ok` |
| `python workflow/gtpj_workflow.py validate-framework-ledgers` | `validate-framework-ledgers-ok` |
| `python workflow/gtpj_workflow.py validate-workflow-consistency` | `validate-workflow-consistency-ok` |
| `python workflow/gtpj_workflow.py audit-boundary` | `audit-boundary-ok` |
| `python -m py_compile workflow/gtpj_workflow.py` | 退出码 0 |
| `git diff --check` | 退出码 0，无输出 |
| `git status --short` | 空，工作树干净 |

## 历史保护

```text
a663595 experiments/module_trials tree: 6e858397607f42c6c4b3ac870e24909e2aae14aa
fd69219 experiments/module_trials tree: 6e858397607f42c6c4b3ac870e24909e2aae14aa
file count: 471 -> 471
diff: none
```

没有运行模型训练、服务器任务、push、部署或发布。
