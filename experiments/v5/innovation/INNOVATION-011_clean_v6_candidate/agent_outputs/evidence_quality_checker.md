# Evidence Quality Checker 开跑检查

```text
role_key: evidence_quality_checker
decision: allow
```

- 实验绑定 `MODEL-V5-TEMPLATE-V2@fb4b29b`，模型与训练逻辑只保留在独立实验分支。
- 参数表固定 `RUN-001`、seed 5、配置快照及其 SHA-256；代码审核绑定最终冻结提交。
- 大文件身份使用新的 `v5_innovation_011_inputs.json`，不会覆盖 009/010 的旧清单。
- 结果只保存到新的 Warehouse 目录；GitHub 只回填路径、哈希和 U/S/H/ZS 摘要。
- 本次只跑 `RUN-001`，不会自动追加复现或创建正式 V6。
