# 机器验证

- `python -m unittest tests/test_v5_ablation_server_runner.py -v`：45 项通过。
- `python -m unittest discover -s tests -v`：总计 342 项，其中 337 项通过、5 项 Linux 专属测试在 Windows 按设计跳过。
- `lab4090` 精确候选 `28185a0f1f1c2bdc9b6239cbbc919165a84077df`：45 项控制器测试和 5 项真实 Linux 测试，共 50 项，全部通过。
- Linux 真实验证：错误目录 inode 拒绝；绑定后把原路径改名并放入错误目录，读取仍来自已绑定原目录；目录文件描述符跨 `execve` 后继续有效并把探针结果写入已绑定 Warehouse；新增的端到端用例真实走通包装器、固定 Python、`execve`、目录句柄和假训练入口。
- Windows 与 Linux 均验证：两个代码副本 Git 状态必须完全为空，额外未跟踪文件和 tracked 改动均拒绝。
- 真实临时 bundle clone：恢复 `main`、`framework/v1/v2/v3/v5`、`framework/v5-template-v1`，保留 `v1/v2/v3/v4/v5` 和 `model/v5-template-v1` Tag；RUN 账本当前分支为 `exp/v5/ablation/ablation-001-local-branch-effect`，并在 clone 中真实运行 `validate-experiment-base` 通过。
- `python -m py_compile tools/run_v5_ablation_001_server_controller.py tests/test_v5_ablation_server_runner.py`：通过。
- `python workflow/gtpj_workflow.py validate`：通过。
- `python workflow/gtpj_workflow.py validate-workflow-consistency`：通过。
- `python workflow/gtpj_workflow.py validate-framework-ledgers`：通过。
- `python workflow/gtpj_workflow.py audit-boundary`：通过。
- `python workflow/gtpj_workflow.py validate-agent-runtime --path experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_runtime.yaml`：通过。
- `python workflow/gtpj_workflow.py multi-agent-preflight --path experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_runtime.yaml`：通过。
- `python workflow/gtpj_workflow.py validate-parameter-matrix --path experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv --expected-jobs 6 --require-ready`：6 行就绪并通过。
- 在真实实验分支的干净工作区运行 `validate-experiment-base`：通过。
- `git diff --check`：通过。

本地没有安装 `pyflakes`，因此没有运行该可选检查；它不替代上述 Python 编译、单元测试和工作流校验。
