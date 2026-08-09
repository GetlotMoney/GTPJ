# 证据索引

## GitHub 内可直接查看

- `../result.md`：三个 seed 的指标与结论；
- `../PARAMETER_MATRIX.csv`：每次运行的机器可读记录；
- `../PARAMETER_MATRIX.md`：参数表阅读版；
- `../DATA_MANIFEST.json`：数据、split、类别顺序和评估输入身份；
- `../configs/`：每个 RUN 的冻结配置；
- `../quality_check.md`：本次账本完整性检查。

## GitHub 外的原始证据

原始日志、checkpoint、模型文件和运行目录保存在 Warehouse。对应位置、哈希和运行编号写在参数表中；它们不进入本仓库。

本实验的代码级历史分支不合并进 `main`，避免把实验专用控制器和临时代码污染正式模板。
