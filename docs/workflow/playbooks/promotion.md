# 执行卡：升版 Promotion

用于判断已确认的创新能否注册为新的正式框架和 Tag。

## 最短闭环

1. 确认候选来自 innovation，而不是纯调参或普通消融。
2. 核对准确 commit、配置、数据/划分、评估口径、全部 U/S/H/ZS、失败记录和 confirmation 证据。
3. 按 `docs/workflow/protocols/promotion.md` 比较 confirmed 指标、稳定性和当前 baseline。
4. 涉及代码或规则的最终版本必须已有机器测试和两轮只读审核通过。
5. 只形成 `promote` 或 `blocked/reject` 结论；创建 tag、push 或发布仍需 owner 当前明确授权。

不能用单次最高值代替稳定确认，也不能隐藏较弱 repeat。当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`。
