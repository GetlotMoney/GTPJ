# V5 局部分支双卡消融执行计划

> **执行要求：** 实施时使用 `superpowers:executing-plans` 逐项完成；代码改动使用 `superpowers:test-driven-development`，先看到测试按预期失败，再写最小实现。

**目标：** 从冻结 V5 母版建立一个没有 FGVD、BVSA、SGMP 和局部损失的干净实验版本，并在服务器两张 RTX 4090 上对完整组与无局部组做种子 5、17、29 的公平配对训练。

**实现原则：** 冻结母版永远不改。本实验只在 `exp/v5/ablation/ablation-001-local-branch-effect` 分支新增专属模型和训练入口；母版的 `model/MyModel.py`、`train_GTPJ_CUB.py` 和四份正式 V5 配置逐字不变。无局部模型继续接受原来的 577-token 输入，但只读取 CLS，以保持数据与评估接口一致。

**环境：** Python 3.10、PyTorch、CUDA、CUB 缓存、CLIP ViT-L/14@336px 特征、GPT-5.5 文本原型；服务器 Python 为 `/data/lby/.conda/envs/dvsr_gpu/bin/python`。

---

## 任务 1：冻结当前事实和清理实验范围

**文件：**

- 修改：`experiments/v5/ablation/ABLATION-001_local_branch_effect/README.md`
- 修改：`experiments/v5/ablation/ABLATION-001_local_branch_effect/EXPERIMENT.yaml`
- 修改：`experiments/v5/ablation/INDEX.md`
- 修改：`experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv`
- 生成：`experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md`

- [ ] 保留旧 15 行计划的来源说明，但把 0.1/0.3 权重候选移出本次正式消融运行范围，标明它们应属于调参。
- [ ] 把第一批正式矩阵收敛为 6 行：完整 V5 与干净无局部，各用 seed 5、17、29。
- [ ] 把无局部定义修正为保留 PSE、ICSA、CE、topology，只删除 FGVD、BVSA、SGMP、局部融合和局部损失。
- [ ] 运行矩阵结构检查，确保没有伪造配置快照或结果字段。

验证：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe workflow/gtpj_workflow.py validate-parameter-matrix --path experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv
```

## 任务 2：先写无局部版本的失败测试

**文件：**

- 新增：`tests/test_v5_global_only_ablation.py`

- [ ] 测试模型不实例化 `bvsa_module`、`sgmp_predictor` 和 FGVD 参数。
- [ ] 测试固定 CLS、任意改变 576 个局部块后，训练与评估 logits 完全不变。
- [ ] 测试输出维度和 seen/unseen 类别顺序与 V5 保持一致。
- [ ] 测试总损失只等于 CE 加 topology，局部专属损失不存在或恒为 0。
- [ ] 测试配置文件不再接受任何局部模块参数。

运行 RED 阶段：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe -m unittest tests.test_v5_global_only_ablation -v
```

预期：测试因为当前仍实例化并调用局部分支而失败，且失败原因与消融目标一致。

## 任务 3：实现最小无局部模型

**文件：**

- 新增：`model/V5GlobalOnly.py`
- 新增：`train_V5_ABLATION_001_CUB.py`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/configs/RUN-004.yaml` 至 `RUN-006.yaml`

- [ ] 删除 FGVD、BVSA、SGMP 及其局部辅助函数和参数。
- [ ] 保留 PSE、ICSA、全局余弦打分、CE 和 topology。
- [ ] `forward` 继续验证 `[B, 577, D]`，只读取 CLS，返回与评估器兼容的 `clip_S_pp`。
- [ ] `compute_loss` 只计算 CE 和 topology，并保留清楚的日志字段。
- [ ] 训练入口写明实验身份和“局部块已忽略”，不增加功能开关。
- [ ] 三份无局部配置只保留实验真正读取的字段；四份正式 V5 配置逐字保持母版内容。

运行 GREEN 阶段：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe -m unittest tests.test_v5_global_only_ablation -v
```

## 任务 4：回归检查和真实最小样例

**文件：**

- 保持：`tests/test_v5_template_contract.py` 与 `tests/test_fae_memory_jepa.py` 的母版测试不跳过、不改验收含义。
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/interface_check.md`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/implementation.md`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/code.diff`

- [ ] 运行全部 V5 接口测试和现有 FAE/JEPA 回归测试。
- [ ] 用小张量真实前向和反向，确认梯度只流入 PSE、ICSA 和 logit scale。
- [ ] 记录参数量变化、输入输出形状、损失构成和补丁不敏感证据。
- [ ] 生成相对母版的 `code.diff`。

验证：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe -m unittest tests.test_v5_global_only_ablation tests.test_v5_template_contract tests.test_fae_memory_jepa -v
```

## 任务 5：完成严格代码审核和运行门

**文件：**

- 新增：`docs/agent_reviews/2026-08-07-v5-local-ablation/`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_runtime.yaml`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_outputs/*.md`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/agent_summary.md`
- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/quality_check.md`

- [ ] 按 `strict-3` 检查训练入口、评估语义和消融纯度；每轮只读审核都有明确结论。
- [ ] 修复阻断问题后重跑机器测试。
- [ ] 将服务器冻结运行写成 `role_only + server_detached_role_only`，不把顺序角色冒充多智能体。
- [ ] 依次通过 `validate-agent-runtime`、`multi-agent-preflight`、`agent-cleanup-plan`、`validate-ai-cross-review`。

### 任务 5.1：关闭第二轮审核发现的服务器控制器缺口

**文件：**

- 修改：`tests/test_v5_ablation_server_runner.py`
- 新增：`tests/test_v5_ablation_server_linux_integration.py`
- 修改：`tools/run_v5_ablation_001_server_controller.py`
- 修改：`experiments/v5/ablation/ABLATION-001_local_branch_effect/SERVER_RECOVERY.md`

- [ ] 先增加失败测试：许可清单必须绑定实验分支、母版提交、参数矩阵、`TASK_START.yaml`、`agent_runtime.yaml` 和 strict-3 最终决定的准确哈希。
- [ ] 先增加失败测试：服务器只允许 Linux 进程组语义，不能在 Windows 上把 `SIGTERM` 冒充 `SIGKILL`。
- [ ] 先增加失败测试：同一个冻结提交、同一个 `execution_id` 或已经领取过的 `run_id` 不得再次启动。
- [ ] 先增加失败测试：最终的“检查失败状态 + `Popen`”必须在同一把锁内，失败登记完成后不能再启动后续 RUN。
- [ ] 先增加失败测试：`Popen` 后任意异常都必须经过统一 `finally` 清理真实训练 PID 和 helper 进程组，并核对 `run_start_receipt.finish.json`。
- [ ] 使用 Git bundle 的临时隔离校验仓读取冻结提交，不依赖调用者填写的布尔值；校验通过前不得建立正式运行副本或训练进程。
- [ ] 使用服务器持久化身份领取记录阻止重复执行；中断后的恢复必须更换冻结提交、`job_id`、`run_id`，并填写 `repeat_of`。
- [ ] signal handler 只设置停止事件，文件和状态写入由普通控制流程完成，避免锁重入。
- [ ] bundle 内的 workflow 校验器必须与冻结母版 Git 对象一致；未验证来源的代码不得在预检阶段执行。
- [ ] runtime、Warehouse 和一次性领取记录绑定固定服务器父目录，不能通过换目录复用身份。
- [ ] finish receipt 或清理异常先锁住双队列，再继续写状态或抛错；用 barrier 测试固定该时序。
- [ ] 在 Linux 服务器用无训练 helper/子进程实际验证 TERM、回收和进程组语义。

RED 验证：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe -m unittest tests.test_v5_ablation_server_runner -v
```

预期：新增测试因上述接口或行为尚不存在而失败。

GREEN 验证：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe -m unittest tests.test_v5_ablation_server_runner tests.test_v5_global_only_ablation tests.test_v5_template_contract -v
```

## 任务 6：生成真实配置快照并创建运行前冻结提交

**文件：**

- 新增：`experiments/v5/ablation/ABLATION-001_local_branch_effect/configs/RUN-001.yaml` 至 `RUN-006.yaml`
- 修改：`PARAMETER_MATRIX.csv/.md`
- 新增：启动凭证文件

- [ ] RUN-001/002/003 为完整 V5，seed 5/17/29，代码引用母版提交。
- [ ] RUN-004/005/006 为无局部，seed 5/17/29，代码引用实验冻结提交。
- [ ] 每行绑定真实配置文件、配置哈希、代码引用和唯一 run id。
- [ ] 提交只包含运行前代码、配置和轻量计划，确认工作树 clean。

验证：

```powershell
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe workflow/gtpj_workflow.py validate-experiment-base --path experiments/v5/ablation/ABLATION-001_local_branch_effect
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe workflow/gtpj_workflow.py validate-parameter-matrix --path experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe workflow/gtpj_workflow.py validate
C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe workflow/gtpj_workflow.py audit-boundary
```

## 任务 7：上传冻结代码并双卡启动

**服务器位置：**

- 运行副本：`/data/lby/projects/cv_project/GTPJ/.runtime/ablation/V5-ABLATION-001-<冻结提交前12位>/`
- 结果仓库：`/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/ablation/V5-ABLATION-001-<冻结提交前12位>/`

- [ ] 再查两张 GPU、旧训练进程、磁盘空间和目标目录不存在或属于本实验。
- [ ] 在本地全部审核与运行时门通过后生成一次性 `launch_manifest.json`；上传后由控制器核对九项许可和准确冻结提交，任一不符都不得创建训练进程。
- [ ] 用冻结提交生成可验证代码包；控制器先在临时隔离校验仓中核对受信证据，再在 `.runtime/` 内建立两个独立干净运行副本。
- [ ] 在服务器持久化领取 `execution_id` 和六个 `run_id`；同一身份只能领取一次，停止或失败后也不能复用。
- [ ] GPU 0 启动完整组队列，GPU 1 启动无局部组队列；每队按 5、17、29 串行。
- [ ] 写 controller PID、每个子任务 PID、状态、停止文件路径、命令哈希和日志路径。
- [ ] STOP 或系统信号先停止真实训练 PID，超时后强制停止；失败时写 `recovery_handoff.json`，后续只能新建冻结 RUN，不能复用半截目录。
- [ ] 启动后等待至少一个真实训练 step，确认两张卡都有进程、日志持续增长且没有 NaN/路径错误。

服务器验证：

```bash
nvidia-smi --query-compute-apps=pid,gpu_uuid,used_memory --format=csv,noheader
cat /data/lby/projects/cv_project/GTPJ/.runtime/ablation/V5-ABLATION-001/status.json
```

## 任务 8：阶段交付

- [ ] 回报两张卡分别在跑什么、当前种子、PID、日志与停止位置。
- [ ] 明确当前只有启动证据，没有提前宣称精度结论。
- [ ] 结果完成后再做日志解析、配对统计、质量检查和 post-run result commit。
- [ ] owner 已于 2026-08-07 明确授权按本计划执行 Git 上传；仅在审核、机器验证和运行门全部通过后，推送当前独立实验分支并设置 upstream。
- [ ] 不删除历史文件、不改冻结 V5 母版、不把实验代码合并回母版；`main` 的 119 个本地提交另行审计，绝不与实验分支混推。
