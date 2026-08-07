# 实现记录

## 母版和改动边界

- 母版：`MODEL-V5-TEMPLATE-V1`；
- 母版提交：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；
- 实验分支：`exp/v5/ablation/ablation-001-local-branch-effect`；
- 冻结母版工作区未修改；所有实验代码只存在于独立实验分支。

## 删除内容

新增的 `model/V5GlobalOnly.py` 不定义或实例化 FGVD、BVSA、SGMP；前向计算不生成局部分数，最终分数就是全局分数。它的 `compute_loss` 不计算 consistency、BMDD、MPP 和 negative semantic 损失。

新增的 `train_V5_ABLATION_001_CUB.py` 只导入这个专属模型。没有增加 `use_xxx` 开关，也没有让第二个实验继续修改第一个实验。母版的 `model/MyModel.py` 和四份正式 V5 配置与冻结 Tag 逐字一致。FULL 训练入口只增加服务器目录绑定，并把类别编号的初始加载设备改为 CPU；这是模型初始化所需的设备边界修复，不改变训练公式，模型构造完成后这些注册缓冲仍会随模型迁移到 GPU。

## 保留内容

- PSE 的实现、层数和参数量保持母版一致；
- ICSA 的实现和参数量保持母版一致；
- 全局 `logit_scale`、类别顺序、seen/unseen 映射和输出维度保持一致；
- CE 与 topology 损失保持一致；
- 训练仍加载同一份 CLS 和局部块缓存，无局部模型只读取 CLS，避免换数据入口带来干扰。

## 参数量

| 版本 | 总参数 | 可训练参数 | PSE | ICSA |
|---|---:|---:|---:|---:|
| 完整 V5 | 13,400,981 | 13,016,981 | 2,954,496 | 74,640 |
| 干净无局部 | 3,413,137 | 3,029,137 | 2,954,496 | 74,640 |

减少可训练参数 9,987,844，即 76.73%。减少量对应完整 V5 中 BVSA/FGVD 与 SGMP 的参数，不包含 PSE 和 ICSA。

## 服务器运行安全补强

- `launch_manifest.json` 不再用调用者填写的通过布尔值自我证明；它只绑定冻结提交、实验分支、母版提交、六个 `run_id`、六份受信文件和固定 Python 的 SHA-256；
- 控制器先从 Git bundle 克隆出带 `.git` 的临时隔离仓，并准确切到正式实验分支，再运行 strict-3、agent runtime、参数表、实验绑定和仓库边界校验；通过前不创建正式运行副本和训练进程；
- 代码包里的 `workflow/gtpj_workflow.py` 只允许冻结母版 Git 对象或控制器硬编码的已审核“绑定 Python”版本；其他自校验器会在执行前被拒绝；
- 正式 Python 固定为 `/data/lby/.conda/envs/dvsr_gpu/bin/python`；控制器核对清单哈希后打开文件描述符，helper、收据流程、训练包装器和最终训练入口都执行这个已打开文件，路径在检查后被替换也不会换掉实际解释器；
- `DATA_MANIFEST.json` 冻结 12 个 CUB/xlsa17 正式输入的路径、大小和 SHA-256，并同时固定 split、label、class order 与 metric 口径；控制器预检源目录后，把 12 个文件复制到本次 execution 私有快照，复制时再次核对完整哈希并改成只读；每个 RUN 只复核和读取这份快照，不再从可变源目录训练；
- runtime 与 Warehouse 使用 `V5-ABLATION-001-<冻结提交前12位>` 命名；服务器持久化领取 `execution_id` 和六个 `run_id`，停止后也不能重复使用；
- runtime、Warehouse 和身份领取目录都固定在服务器约定父目录，不能靠更换 `--warehouse-root` 父目录重新领取；
- STOP 或系统信号由普通控制流程处理；signal handler 只设置停止事件，不获取状态锁；
- 任意异常都进入统一 `finally`：先用 `/proc` 核对 PID、进程组、会话和启动时钟，再打开 Linux pidfd 绑定具体进程对象；正常停止信号只发给 pidfd，不按可能复用的裸 PID 发信号；即使 helper 先退出，也会继续清理仍存活的训练子进程；
- helper 创建后若连身份都没来得及固定，控制器会在该直接子进程被 `wait` 回收前强制停止它的独立进程组，并写 `launch_failure.json`；
- `run_start_receipt.finish.json` 会再次核对 job、run、启动收据哈希、退出码、PID 和日志哈希；只存在文件但内容不一致仍然阻断正式证据；
- 冻结证据校验调用 `validate-experiment-base` 时传入完整实验目录；测试中的最小工作流会检查该路径确实包含 `EXPERIMENT.yaml`，防止参数写错却被假校验放过；
- 正式 bundle 必须携带 `main`、现行 `framework/v1/v2/v3/v5` 与来源 Tag，以及 `framework/v5-template-v1` 和 `model/v5-template-v1`；Git clone 把非当前分支保存为远端引用后，控制器会在总校验副本、FULL/GLOBAL_ONLY 代码副本和六个 RUN 独立账本中，统一用 bundle 列表中已经验证的提交恢复本地管理分支，再执行全仓框架账本、母版起点或启动收据校验；
- 目录、环境变量和 helper 日志先准备完，再在共享锁内执行最后一次 STOP/失败检查；检查通过后的第一项动作就是 `Popen`，任一 RUN 失败登记完成后，两个队列都不能再启动后续 RUN；
- `Popen` 与首次 `running` 状态写入也在同一把锁内；如果状态无法落盘，会先清理刚创建的 helper 并锁住另一队列；
- 训练代码副本不再创建 `data` 或 `train_log` 软链接，Git 状态必须完全为空；FULL 与 GLOBAL_ONLY 都从本次冻结实验提交建立代码副本，FULL 的模型、配置、数据划分与保留模块仍逐项对照冻结母版；
- 包装器用设备号和 inode 核对本次私有数据快照与对应 Warehouse 目录，再打开 Linux 目录文件描述符跨进程交给两个训练入口；入口只通过 `/proc/self/fd/<编号>` 读写，因此同名路径在检查后被替换也不会改变实际目录；
- 上述启动期清理结果写入不可覆盖的 `launch_failure.json`；清理不完整时错误会携带 helper PID 和清理错误，不会丢失孤儿进程线索；
- execution claim 先完整写同目录临时文件、`fsync` 后用不可覆盖硬链接原子发布；正式 claim 一旦发布，即使临时文件清理失败也返回并保留有效领取凭证；领取后如果建目录、克隆或最终状态落盘失败，会额外写入不可覆盖的 `controller_failure.json` 同类凭证，并尽力生成 `recovery_handoff.json`；
- helper 启动前会在耗时的 Python 与数据复核结束后先准备目录、环境和日志，再紧邻 `Popen` 检查 STOP/停止事件；finish receipt、清理或任意状态写入异常都会在同一把共享锁内关闸，另一队列不能利用异常处理窗口启动后续 RUN；
- 正式控制器只接受 `sys.platform == linux` 且通过真实进程组、pidfd 和 `SIGKILL` 能力探测的环境；当前服务器 Python 未直接暴露 pidfd 时，控制器调用 Linux 内核接口；
- 本实验的无局部分支入口不提供续训参数，不读取外部 checkpoint；停止后的重跑必须新建冻结 RUN；
- 非正常结束会生成 `recovery_handoff.json`，具体规则见 `SERVER_RECOVERY.md`。

## 已知随机性边界

同一 seed 能锁定每个版本自己的初始化和采样，但删除大量模块后，PyTorch 随机数的消耗顺序必然变化，因此不能假设两组每一层初始权重逐元素相同。三个配对 seed 用来降低这种训练噪声；若最终差值很小，会把“差值低于随机波动”作为结论边界，而不是强行说局部分支有效或无效。

## 当前机器验证

- 服务器控制器专属测试：45 项通过；
- 精确候选 `28185a0f1f1c2bdc9b6239cbbc919165a84077df` 在 `lab4090` 完成 45 项控制器测试和 5 项真实 Linux 测试，共 50 项全部通过；上一候选 `d847266` 仍只保留为 FULL 实际入口和软链接换向阻断的审核证据；
- 冻结提交 `cca4e0e6419a462d36df5cad5177562cbf8fb31e` 的 R3 正式执行已进入两张 GPU 的真实模型入口，但 FULL 与 GLOBAL_ONLY 都因类别编号在 CUDA、初始化核对张量在 CPU 而退出；两项结束收据和进程树清理完整，其余四项没有启动，R3 仅作为失败证据保留；
- 当前修复让两个训练入口都以 CPU 类别编号构造模型，并新增“两个真实模型使用 CPU 类别编号和 CUDA 文本特征均可完成初始化”的服务器测试；本地静态与 CPU 行为测试已通过，精确修复候选的服务器 CUDA 验证和三路审核仍待完成；
- V5 相关模型、母版和旧数学路径测试：41 项通过；
- 当前修复的仓库完整回归共 344 项：338 项通过，另有 5 项 Linux 专属测试和 1 项 CUDA 专属测试在 Windows 按设计跳过；
- `validate-experiment-base`、6 行冻结参数表、总工作流、规则一致性、框架账本和仓库边界检查均通过。
