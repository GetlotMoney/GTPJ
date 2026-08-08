# Quality Check

```text
runtime: local_cpu_pre_run
quality_check_mode: STRICT
decision: PASS_CODE_CANDIDATE_FORMAL_RUN_BLOCKED
promotion_decision: not_applicable
evidence_level: quick_local
confirmation_status: pending
review_rounds: 3
review_reason: 核心初始化与训练轨迹发生变化
```

## 范围

本检查只放行代码候选，不放行正式 GPU。检查范围是：随机初始化位置、模型参数边界、前向与损失
不变性、参数矩阵和冻结模板边界。服务器真实训练尚未发生。

## 机器验证

- [x] 修复前专项测试真实失败，首个差异位于 SGMP/ICSA。
- [x] 修复后同一专项测试通过。
- [x] `python -m unittest discover -s tests -v`：`290/290 PASS`，包含 2 项真实尺寸 probe 测试。
- [x] 可复用零步 probe 在 `dim_com=512、dim_f=768、seed=5` 下：全部活跃 state mismatch=`0`。
- [x] 实际尺寸模型构造后 CPU RNG 完全相同，前三批 SHA 固定且一致。
- [x] probe 硬校验配置 SHA，并输出候选 HEAD、dirty、模型 SHA；正式模式额外要求准确提交和干净 Git blob。
- [x] 修复版参数量仍为 `13,976,981`，没有 `proj_visual/proj_text`。
- [x] `git diff --check`、`py_compile`、`code.diff --unidiff-zero` 反向应用检查通过。
- [x] `code.diff` SHA-256：`6c78e4d98f6160fde2a74afd7e8382bb3ee415886f70df5d3029ee198eb5d0af`。
- [x] `validate`、`validate-workflow-consistency`、`validate-framework-ledgers`、
  `validate-framework-templates`、`audit-boundary` 全部通过。
- [x] 参数矩阵普通校验通过：5 行、30 列、编号唯一、重复引用有效。
- [x] 服务器固定 Python/PyTorch/CUDA 下的 `512→768` 零步指纹通过；证据 SHA-256 为 `ca3cc6cdc4785f7b69e8dde76bd9abf0656c94fc531d3e4732462a086988c616`。
- [x] 五行参数矩阵已冻结；`changed_parameters={}` 与实际配置零差异一致。
- [x] 专用服务器运行器专项测试 `23/23 PASS`；模型修复与零步探针专项测试 `10/10 PASS`。

## 三路独立审核

1. 随机数与代码可靠性：`PASS`，确认精确位置、完整 state/RNG/批次对齐且无参数污染。
2. 科学语义：代码 `PASS`；初版单次 best-hit 规则被 `BLOCK`，现已改为五次完整分布报告。
3. 实验治理：分支和账本 `PASS`；正式启动因命令、环境、冻结提交尚未绑定而继续 `BLOCK`。

详细回应见 `agent_summary.md`。两路提出修改的审核均已完成增量复核并放行代码候选；
它们同时一致要求正式 GPU 等候选提交、服务器 probe 和运行冻结完成后再启动。

## 接口与证据边界

- [x] 代码快照和准确母版明确。
- [x] 配置副本保存在实验目录，SHA 为 `def1d44c...b9e`。
- [x] 没有改变 eval、class order、logits shape、loss 或数据划分。
- [x] `state_dict` 和 checkpoint 接口不变。
- [x] 没有把前一轮服务器结果冒充本实验结果。
- [x] Git 中没有新增 raw log、checkpoint、缓存或生成图片。
- [ ] 正式日志 artifact URI、SHA256、size：待训练后登记。

## 当前决定

最小修复具备形成独立候选提交的条件；正式训练仍被安全门挡住。下一步先做服务器零步指纹，
再绑定准确提交、命令与环境并冻结五个任务。GPU 结果出来前，不更新 V5 模板、不移动 Tag、
不声称 74.4 已恢复。
