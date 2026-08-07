# 重点差异

## 模型与训练

- `models/FAE_Memory_JEPA_global_only.py`：只保留 PSE、ICSA 与全局分类路线。
- `tools/run_v5_ablation_001_global_only.py`：只使用 CE 与 topology 损失，不接收局部 checkpoint 或局部控制参数。
- `tests/test_v5_global_only_ablation.py`：证明局部块不能改变输出、不能收到梯度，且局部模块没有被实例化。

## 正式服务器执行

- `tools/run_v5_ablation_001_server_controller.py`：绑定 Python 文件对象、pidfd、只读数据快照、一次性 claim、共享失败闸门与最终 STOP 检查。
- `tests/test_v5_ablation_server_runner.py`：覆盖停止、失败、状态写入、数据身份、Python 身份和一次性运行边界。
- `tests/test_v5_ablation_server_linux_integration.py`：在 Linux 真进程上覆盖 helper 与孤儿训练子进程清理。
- 冻结 bundle 必须包含 `main`、现行框架母版分支与来源 Tag、V5 干净母版分支与 Tag；控制器从 `list-heads` 精确对象号恢复隔离仓的本地管理分支后再运行全仓校验。
- `bind_experiment_branch=true` 的六个 RUN 账本不能只创建分支引用，必须用 `git checkout -B` 真正进入实验分支；回归测试同时检查当前分支名，并在真实 clone 中运行 `validate-experiment-base`。
- 两个代码副本仍保持 detached HEAD，只作为准确提交的只读代码源；只有需要生成正式账本收据的六个账本进入命名实验分支。

## 需要诚实保留的边界

FULL 会先创建局部模块，GLOBAL_ONLY 不会，因此即使 seed 相同，随机数消耗顺序也可能让后续 ICSA 的逐元素初始值不同。三组配对 seed 用于估计这种训练波动；若差值落在波动范围内，不能强行宣称局部分支有效或无效。

首次失败执行没有生成训练 PID，也没有产生精度结果；它只能证明旧初始化失败，不能参与局部分支效果比较。
