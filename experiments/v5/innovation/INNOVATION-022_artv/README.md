# V5-INNOVATION-022：ARTV

本实验冻结 PSE-X2，用原始 CUB 测试图像的确定性 15-crop CLIP CLS 验证 X2
top-1/top-2。ARTV 没有训练参数；只有 7 票中至少 5 票支持第二名时才交换前两项。

- 实验问题与身份：`EXPERIMENT.yaml`
- 冻结参数：`config.yaml`、`PARAMETER_MATRIX.csv`
- 模块来源与边界：`module_source.md`
- 公式、张量与关闭路径：`implementation.md`
- 框架图：`framework_diagram.md`、`framework_diagram.html`
- 实现与入口：`artv.py`、`evaluate.py`

Owner 已指定直接读取 official test；本结果只标记为
`official-test-guided-development`，不作为 confirmation 证据。运行前不创建结果文件；
完成后再写入 U/S/H/ZS 和结论。
