# V5-INNOVATION-003 质量检查

## 结论

三轮结果可用于拒绝当前固定 gate 候选：证据完整、身份一致，且三轮都未显示相对对照的改善。这不是 promotion 或论文模块提升证据。

## 已核对

- 三轮代码 commit 均为 `61734def74d13c15a110ad3e98e609a17c2115c6`，母版为 `MODEL-V5-TEMPLATE-V1` / `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 三份配置字节完全相同，每份 `1406` 字节，SHA256 均为 `cba09034a3b773b78d51cb3c28f35f0fee95ce7536f41be617b7bc04c98cf2ee`。
- 三轮种子都是 `5`，但分别由独立进程运行；没有根据中间或最终测试指标改变训练。
- 三轮训练日志均正常结束，`run_exit_code=0`；`metrics.json` 均记录 `status=completed`。
- 评估口径均为 `standard_gzsl_u_s_h_zs`，保留完整 `U/S/H/ZS`。
- 三轮输入指纹一致：CUB xlsa17 `res101.mat` SHA256 为 `9a97c71951f9ac9f5c3708e6e55386e53f3d433289ed5e87a18b4af2a1a0fca1`，`att_splits.mat` SHA256 为 `d7f5b4c2cb7853acdce43a9e87607ceed30bdf18c60344be3a266de29b6751e3`。
- 已现场重算每个本地输出文件的 SHA256 和字节数，明细见 `evidence/ARTIFACTS.md`。
- 修复前 `RUN-000-startup-failure` 已公开，不计入三轮均值，也没有占用 `RUN-001..003` 任何一行。

## 限制

- PyTorch 运行记录显示本次不是严格确定性运行；同种子三次的 `H` 范围差为 `0.36988309333463576`。
- 本次只回答锁定 gate 候选是否值得保留，不回答其他 gate 形式是否可能有效。
- 训练产物位于项目 `.runtime/`，不进 Git。本轮没有生成独立 manifest，因此参数表的 `artifact_manifest_sha256` 按真实状态留空，而不是伪造值。
