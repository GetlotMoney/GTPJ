# 机器验证

```yaml
machine_gates_passed: true
candidate_commit: a9f8a83c2c0fa2c86cb5b53443579d8ddfd26f1d
```

- 服务器控制器状态：`completed`；`RUN-013…016` 均 `return_code=0`、`cleanup_complete=true`、`finish_receipt_state=verified`。
- 服务器证据：四张 R5 清单与二十个真实文件的路径、大小和 SHA-256 全部逐项通过；清单 SHA 分别为 `425d94bc…/6160ffa4…/0a70e516…/bfb1e045…`。
- `python -m unittest -v tests.test_gtpj_workflow`：254/254 通过。
- `python -m unittest -v tests.test_v5_ablation_server_runner`：51/51 通过。
- `python -m unittest -v tests.test_v5_global_only_ablation`：6 项通过，1 项 Windows 无 CUDA 按设计跳过；冻结候选此前服务器 CUDA 7/7 通过。
- `python -m unittest -v tests.test_v5_template_contract`：7/7 通过。
- 参数矩阵、实验起点、框架账本、工作流一致性、全项目 `validate` 与 `audit-boundary` 全部通过。
- `git diff --check` 通过。
- 服务器候选测试日志：57 项日志 SHA-256=`d04e533422fa9c331b7a2cf269d54183f64d24fe4ef00c7c412aa0a11c94d3be`；CUDA 7 项=`c813a56459b54b7d155f7e5dc1780f414c9b154eb8b6ac9d4aaa7489325867a3`；V5 32 项=`d89a22e3d53918e2e3843b6ed76953864d7da09520da31aa761e3723d8d34b1e`。
- 一次误写了不存在的测试模块名 `tests.test_v5_clean_template`，只产生 `ModuleNotFoundError`，随后按真实模块名 `tests.test_v5_template_contract` 重跑 7/7；这不是候选回归，已在此明确保留。
