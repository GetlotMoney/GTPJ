# 接口检查

role_key: interface_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow

files_reviewed:
- model/MyModel.py
- model/V5GlobalOnly.py
- train_GTPJ_CUB.py
- train_V5_ABLATION_001_CUB.py
- configs/RUN-001.yaml 至 configs/RUN-006.yaml
- tools/v5_cub_data.py
- tools/v5_evaluation.py

检查结论：两组使用相同 CUB/xlsa17 输入、类别顺序和 U/S/H/ZS 评估口径。FULL 使用冻结母版入口；GLOBAL_ONLY 使用专属全局模型，只移除 FGVD、BVSA、SGMP、局部融合和局部相关损失，保留 PSE、ICSA、全局余弦分数、CE 与 topology。三组随机种子按 5、17、29 一一配对。
