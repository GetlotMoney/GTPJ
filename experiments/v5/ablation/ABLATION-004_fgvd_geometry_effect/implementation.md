# FGVD 几何编码关闭方式

- 关闭模块：只关闭 FGVD 几何关系计算和几何编码器前向计算。
- 入口：配置设置 `ablation_disable_fgvd_geometry=true`，本实验训练入口拒绝 false 或缺失字段。
- 保留选择：先照常运行 `fgvd_select_patches`，保持同一 top-K 索引和 `fgvd_select_k`。
- 保留投影：selected patches 仍经过 `embed_cv`；旁路只把投影结果 `vis` 直接作为 `fgvd_memory`。
- 保留训练：BVSA v2s/s2v、SGMP、局部融合、PSE、ICSA、CE、consistency、topology、BMDD、MPP 和 negative semantic 都保持母版行为。
- 验收：`tests/test_v5_fgvd_geometry_ablation.py` 检查禁用路径不调用几何函数和编码器、top-K 不变、memory 等于 patch_z、类别轴和剩余模块梯度有效。
