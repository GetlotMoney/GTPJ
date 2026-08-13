# 执行卡：论文到实验闭环

用于把已核实的论文机制转成 GTPJ 中可验证的创新实验。

## 最短闭环

1. 完成 paper intake，形成来源、机制 claim、hypothesis 和风险。
2. 由 owner 指定 `base_code_tag`，选择最窄的 `module_template_selection.md` 模板并写 `module_source.md`。
3. 在所属框架创建 innovation 项，写实现契约、配置和 `PARAMETER_MATRIX`。
4. 机器测试后完成两轮依次进行的只读审核，从 clean 冻结提交启动首个独立 RUN。
5. 回填结果并反哺 Research 与 idea 记录；只有 confirmation 和 owner 接纳后才进入 promotion。

缺来源、基线、假设、接口边界或 owner 实验授权时，停在对应阶段，不默认训练。当前通用规则见 `START_HERE.md` 和 `WORKFLOW_KERNEL.md`。
