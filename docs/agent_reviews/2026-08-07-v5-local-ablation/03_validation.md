# 机器验证

- 精确代码候选：`0a2220fd8895115128d5d85b465afa2eeaaff3ea`。
- `python -m unittest discover -s tests -p "test_*.py" -q`：总计 351 项，其中 345 项通过、5 项 Linux 专属测试和 1 项 CUDA 专属测试在 Windows 按设计跳过。
- `lab4090` 控制器与真实 Linux 测试：55 项全部通过；包含正式控制器 checkout 身份、审核后差异白名单、目录句柄、固定 Python、`execve` 和假训练入口的端到端验证。
- `lab4090` CUDA 模型测试：7 项全部通过；真实以 CPU 类别编号和 CUDA 文本特征构造 FULL 与 GLOBAL_ONLY，并确认 `.to("cuda")` 后两者的类别缓冲都在 GPU。
- `lab4090` V5 相关测试：规范数学路径、复现、母版合同和消融语义共 32 项全部通过，CUDA 专属用例没有跳过。
- 服务器精确 checkout 为 `0a2220f`、实验分支正确、受控工作树为空；日志分别为 `/data/lby/projects/cv_project/GTPJ/.runtime/reviews/0a2220f-linux-55.log`、`0a2220f-cuda-7.log`、`0a2220f-v5-32.log`。
- 审核 bundle 的 SHA-256 为 `13ad7b77cf766d77e67211586bb177ecdf3fbf5c03dac65befb8ec1c1f96f0df`；14 项引用齐全，HEAD 与实验分支都指向 `0a2220f`，六条管理分支与六个 Tag 均通过对象号核对。
- 控制器 Git blob 为 `d771aa1da986508f41bf0f93931cc7fee2d21fe2`，文件 SHA-256 为 `a389be69fe3e1fcda6241f8afb595bc8b370b5cecc293ab42bd54f8523644982`；脏工作树、错误提交或后继提交自改控制器都会在绑定 Python 前拒绝。
- `python -m py_compile tools/run_v5_ablation_001_server_controller.py tests/test_v5_ablation_server_runner.py`：通过。
- `validate`、`validate-workflow-consistency`、`validate-framework-ledgers`、`audit-boundary`、`validate-agent-runtime`、`multi-agent-preflight` 和真实实验分支 `validate-experiment-base`：全部通过。
- `validate-parameter-matrix --require-ready --ready-job-id RUN-007 ... --ready-job-id RUN-012`：12 行全表结构通过，R3 六行均为终态，R4 六行冻结并可启动。
- 三路独立只读审核分别检查运行恢复、发布与引用完整性、科学语义，结论均为 `pass`。
- `git diff --check`：通过。

本地没有安装 `pyflakes`，因此没有运行这个可选检查；它不替代已经完成的 Python 编译、单元测试、真实 Linux/CUDA 测试和工作流校验。
