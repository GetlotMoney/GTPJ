# 机器验证

- `python -m unittest tests/test_v5_ablation_server_runner.py -q`：46 项通过。
- `python -m unittest discover -s tests -p "test_*.py" -q`：总计 346 项，其中 340 项通过、5 项 Linux 专属测试和 1 项 CUDA 专属测试在 Windows 按设计跳过。
- `lab4090` 精确候选 `1df6e9c0e05af9022b81c3133008d735d3db287b`：45 项控制器测试和 5 项真实 Linux 测试，共 50 项，全部通过。
- `lab4090` CUDA 模型测试：`tests.test_v5_global_only_ablation` 共 7 项全部通过；其中新增用例真实以 CPU 类别编号和 CUDA 文本特征构造 FULL 与 GLOBAL_ONLY，并确认 `.to("cuda")` 后两者的类别缓冲都在 GPU。
- `lab4090` V5 相关测试：规范数学路径、复现、母版合同和消融语义共 32 项全部通过，CUDA 专属用例没有跳过。
- Linux 真实验证：错误目录 inode 拒绝；绑定后把原路径改名并放入错误目录，读取仍来自已绑定原目录；目录文件描述符跨 `execve` 后继续有效并把探针结果写入已绑定 Warehouse；新增的端到端用例真实走通包装器、固定 Python、`execve`、目录句柄和假训练入口。
- Windows 与 Linux 均验证：两个代码副本 Git 状态必须完全为空，额外未跟踪文件和 tracked 改动均拒绝。
- 真实临时 bundle clone：14 项引用精确指向候选或既定管理对象；恢复 `main`、`framework/v1/v2/v3/v5`、`framework/v5-template-v1`，保留 `v1/v2/v3/v4/v5` 和 `model/v5-template-v1` Tag；审核仓当前分支为 `exp/v5/ablation/ablation-001-local-branch-effect`，HEAD 精确为 `1df6e9c` 且工作树为空。
- `python -m py_compile tools/run_v5_ablation_001_server_controller.py tests/test_v5_ablation_server_runner.py`：通过。
- `python workflow/gtpj_workflow.py validate`：通过。
- `python workflow/gtpj_workflow.py validate-workflow-consistency`：通过。
- `python workflow/gtpj_workflow.py validate-framework-ledgers`：通过。
- `python workflow/gtpj_workflow.py audit-boundary`：通过。
- `python workflow/gtpj_workflow.py validate-agent-runtime --path experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_runtime.yaml`：通过。
- `python workflow/gtpj_workflow.py multi-agent-preflight --path experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_runtime.yaml`：通过。
- `python workflow/gtpj_workflow.py validate-parameter-matrix --path .../PARAMETER_MATRIX.csv --require-ready --ready-job-id RUN-007 ... --ready-job-id RUN-012`：12 行全表结构通过，R3 六行均为终态，R4 六行冻结并可启动。
- 在真实实验分支的干净工作区运行 `validate-experiment-base`：通过。
- `git diff --check`：通过。

首个设备修复候选的服务器日志位于 `/data/lby/projects/cv_project/GTPJ/.runtime/reviews/1df6e9c-*.log`；最终候选的服务器复验日志将在精确提交生成后补写。本地没有安装 `pyflakes`，因此没有运行该可选检查；它不替代上述 Python 编译、单元测试和工作流校验。
