# 机器验证

- `python -m unittest tests.test_v5_ablation_server_runner -v`：41 项通过。
- `python -m unittest discover -v`：总计 335 项，其中 333 项通过、2 项 Linux 专属测试在 Windows 按设计跳过。
- `lab4090`：41 项控制器测试和 2 项真实 Linux 进程测试，共 43 项通过。
- 真实临时 bundle clone：恢复 `main`、`framework/v1/v2/v3/v5`、`framework/v5-template-v1`，保留 `v1/v2/v3/v4/v5` 和 `model/v5-template-v1` Tag；全仓框架账本、母版与工作流校验通过。
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
