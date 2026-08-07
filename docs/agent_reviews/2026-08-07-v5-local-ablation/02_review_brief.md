risk_level: high
review_tier: strict-3
claude_rounds_required: 3

# 审核说明

请以 `model/v5-template-v1...e9940e0aadd2017a1d95437338b6f4111d0f7787` 为范围，只读检查：

1. 两个实验组是否只差局部子系统；
2. 数据、类别顺序、指标和全局路线是否保持一致；
3. STOP/失败能否阻止另一队列继续启动；
4. Python、PID、数据与运行身份能否在检查后被替换或复用；
5. 文档是否把预检结果误写成正式精度结论。

每轮必须给出 `pass` 或可复现的阻断问题。三轮均使用不同的独立 Codex 只读任务；Claude Code 本轮不可用，因此按项目规范使用独立 Codex 作为后备审核者。
