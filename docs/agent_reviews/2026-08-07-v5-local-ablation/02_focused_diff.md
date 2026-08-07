# 重点差异

## 模型与训练

- `model/V5GlobalOnly.py`：只保留 PSE、ICSA 与全局分类路线。
- `train_V5_ABLATION_001_CUB.py`：只使用 CE 与 topology 损失，不接收局部 checkpoint 或局部控制参数。
- `tests/test_v5_global_only_ablation.py`：证明局部块不能改变输出、不能收到梯度，且局部模块没有被实例化。

## 正式服务器执行

- `tools/run_v5_ablation_001_server_controller.py`：绑定 Python 文件对象、pidfd、只读数据快照、一次性 claim、共享失败闸门与最终 STOP 检查。
- `tests/test_v5_ablation_server_runner.py`：覆盖停止、失败、状态写入、数据身份、Python 身份和一次性运行边界。
- `tests/test_v5_ablation_server_linux_integration.py`：在 Linux 真进程上覆盖 helper 与孤儿训练子进程清理。
- 冻结 bundle 必须包含 `main`、现行框架母版分支与来源 Tag、V5 干净母版分支与 Tag；控制器从 `list-heads` 精确对象号恢复隔离仓的本地管理分支后再运行全仓校验。
- `bind_experiment_branch=true` 的六个 RUN 账本不能只创建分支引用，必须用 `git checkout -B` 真正进入实验分支；回归测试同时检查当前分支名，并在真实 clone 中运行 `validate-experiment-base`。
- 两个代码副本仍保持 detached HEAD，只作为准确提交的只读代码源；只有需要生成正式账本收据的六个账本进入命名实验分支。
- 两个代码副本都 checkout 本次候选提交，Git 状态必须完全为空，不再创建 `data` 或 `train_log` 链接；FULL 的模型、配置、数据划分和保留工具仍与冻结母版逐项比对。
- 控制器把真实数据和结果目录的设备号、inode 写入唯一训练命令；包装器用 `O_NOFOLLOW` 打开并核对目录身份，把可继承文件描述符的 `/proc/self/fd/<编号>` 交给两个训练入口。
- `train_GTPJ_CUB.py` 与 `train_V5_ABLATION_001_CUB.py` 在导入本地模型或工具之前先检查工作树；缓存、xlsa17、评估和结果路径只从绑定目录构造。`tools/v5_evaluation.py` 与 `tools/v5_runtime.py` 不再把 `/proc/self/fd` 路径解析回可替换的普通路径。
- 参数矩阵把已领取并失败的 R2 六个执行身份替换为 R3；R2 runtime、Warehouse、claim、收据和日志原样保留。

## R3 真实启动与类别编号修复

- R3 已领取并进入两个真实模型入口，但两组都在初始化时因 CUDA 类别编号与 CPU 核对张量比较而失败；没有训练 step 或精度，两个结束收据与进程树清理完整。
- `train_GTPJ_CUB.py` 与 `train_V5_ABLATION_001_CUB.py` 只把 `load_v5_cub_split` 的类别编号初始设备改成 CPU；数据划分、模型、优化器、损失、评估和配置不变。
- 新 CUDA 测试对 FULL 与 GLOBAL_ONLY 都使用 CPU 类别编号和 CUDA 文本特征完成真实模型构造，再验证 `.to("cuda")` 后类别缓冲位于 GPU。
- R3 身份永不复用；参数矩阵同表保留 R3 的 `RUN-001…006`，R4 使用新 `RUN-007…012` 和六个新 `run_id`，逐行 `repeat_of`，配对 seed 仍为 5、17、29。
- 通用参数表校验新增“只选择本批冻结行”的模式；没有被选择的历史行必须已经结束。控制器据此只领取 R4 六行，并拒绝重复 job、缺失 R4、未结束历史行或任何复用的 `run_id`。
- 最终审核文件新增 `reviewed_candidate_commit`。正式启动时，审核校验器必须精确匹配该代码候选；最终冻结提交只能在其后补审核记录与开跑门，若又改训练代码、配置、参数矩阵或工作流，控制器直接拒绝。
- 启动入口还会核对自身 checkout：HEAD 必须就是 `reviewed_candidate_commit`，控制器文件必须与该提交的 Git 对象一致且工作树完全干净。最终证据提交里的控制器即使内容相同也不能作为正式入口，避免它自我删除审核后差异检查。

## 需要诚实保留的边界

FULL 会先创建局部模块，GLOBAL_ONLY 不会，因此即使 seed 相同，随机数消耗顺序也可能让后续 ICSA 的逐元素初始值不同。三组配对 seed 用于估计这种训练波动；若差值落在波动范围内，不能强行宣称局部分支有效或无效。

前三次失败执行都没有产生可用精度；R3 虽进入模型入口，但仍在第一个训练 step 前退出，因此三批失败证据都不能参与局部分支效果比较。
