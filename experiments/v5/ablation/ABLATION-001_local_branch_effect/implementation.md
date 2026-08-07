# 实现记录

## 母版和改动边界

- 母版：`MODEL-V5-TEMPLATE-V1`；
- 母版提交：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；
- 实验分支：`exp/v5/ablation/ablation-001-local-branch-effect`；
- 冻结母版工作区未修改；所有实验代码只存在于独立实验分支。

## 删除内容

新增的 `model/V5GlobalOnly.py` 不定义或实例化 FGVD、BVSA、SGMP；前向计算不生成局部分数，最终分数就是全局分数。它的 `compute_loss` 不计算 consistency、BMDD、MPP 和 negative semantic 损失。

新增的 `train_V5_ABLATION_001_CUB.py` 只导入这个专属模型。没有增加 `use_xxx` 开关，也没有让第二个实验继续修改第一个实验。母版的 `model/MyModel.py`、`train_GTPJ_CUB.py` 和四份正式 V5 配置与冻结 Tag 逐字一致。

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

- `launch_manifest.json` 不再用调用者填写的通过布尔值自我证明；它只绑定冻结提交、实验分支、母版提交、六个 `run_id` 和五份受信文件的 SHA-256；
- 控制器先从 Git bundle 建立临时隔离校验仓，重新运行 strict-3、agent runtime、参数表、实验绑定和仓库边界校验；通过前不创建正式运行副本和训练进程；
- 代码包里的 `workflow/gtpj_workflow.py` 只有与硬编码冻结母版中的 Git 对象完全相同才会被执行；恶意或误改的自校验器会提前被拒绝；
- runtime 与 Warehouse 使用 `V5-ABLATION-001-<冻结提交前12位>` 命名；服务器持久化领取 `execution_id` 和六个 `run_id`，停止后也不能重复使用；
- runtime、Warehouse 和身份领取目录都固定在服务器约定父目录，不能靠更换 `--warehouse-root` 父目录重新领取；
- STOP 或系统信号由普通控制流程处理；signal handler 只设置停止事件，不获取状态锁；
- 任意异常都进入统一 `finally`：先处理真实训练 PID，再兜底停止 helper 进程组，并确认进程已经回收；
- `run_start_receipt.finish.json` 会再次核对 job、run、启动收据哈希、退出码、PID 和日志哈希；只存在文件但内容不一致仍然阻断正式证据；
- 冻结证据校验调用 `validate-experiment-base` 时传入完整实验目录；测试中的最小工作流会检查该路径确实包含 `EXPERIMENT.yaml`，防止参数写错却被假校验放过；
- 最终的失败检查与 `Popen` 在同一把锁内；任一 RUN 失败登记完成后，两个队列都不能再启动后续 RUN；
- finish receipt 或清理异常会在写后续状态前立即登记共享失败，另一队列不能利用异常处理窗口启动后续 RUN；
- 正式控制器只接受 `sys.platform == linux` 且具备真实进程组和 `SIGKILL` 的环境，Windows、macOS 和 BSD 均不能正式运行；
- 本实验的无局部分支入口不提供续训参数，不读取外部 checkpoint；停止后的重跑必须新建冻结 RUN；
- 非正常结束会生成 `recovery_handoff.json`，具体规则见 `SERVER_RECOVERY.md`。

## 已知随机性边界

同一 seed 能锁定每个版本自己的初始化和采样，但删除大量模块后，PyTorch 随机数的消耗顺序必然变化，因此不能假设两组每一层初始权重逐元素相同。三个配对 seed 用来降低这种训练噪声；若最终差值很小，会把“差值低于随机波动”作为结论边界，而不是强行说局部分支有效或无效。

## 当前机器验证

- 服务器控制器专属测试：22 项通过；
- 真实 Linux 进程组收口测试已写入；Windows 本地按设计跳过，正式启动前必须在服务器实际通过；
- V5 相关模型、母版和旧数学路径测试：41 项通过；
- 仓库完整回归：311 项通过；
- `validate-experiment-base`、6 行冻结参数表、总工作流、规则一致性、框架账本和仓库边界检查均通过。
