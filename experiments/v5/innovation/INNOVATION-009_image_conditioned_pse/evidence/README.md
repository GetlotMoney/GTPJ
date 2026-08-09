# 证据目录

这里只登记轻量运行凭证和结果引用。原始训练日志、checkpoint 与大文件继续放在 Warehouse 的独立运行目录，不进入 Git。

- `RUN-001`：首次评估设备错误，退出码 `1`；失败日志保留在 Warehouse 的独立目录。
- `RUN-002`：50 epoch 完成，退出码 `0`；封口日志 SHA-256 为 `bdcc73e182f2c4c0837221269c7075de1f86e303720f4ef27a2c48b08d9035de`。
- 结束收据 SHA-256：`0bab5ce215f9256d0907b1780680caf029e46f2973d649bcb614467ce202aba7`。
- 最终指标：`RUN-002/artifacts/final_metrics.json`，SHA-256 为 `6fd7aa5faf0e3c7527217c736738b7fa63b122b69ebbea4c00f5e512cf12c61e`，`U/S/H/ZS=47.921973/78.128189/59.405826/76.428151`。
- 最佳模型：`RUN-002/artifacts/model_best.pth`，SHA-256 为 `f49be7644e9195c6dfd3f9327b4bed2bdfd598fc2a0c91af0f5c2f1082f1d36f`。
- 决定：`reject`；不把单次筛选写成 confirmation 或 promotion 证据。
