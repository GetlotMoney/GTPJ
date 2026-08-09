# V5 局部证据修复共享入口

这份入口只服务五组已预注册实验，不改变 V5 冻结母版。四个训练方案共用
`train.py`，方案 5 使用 `rerank.py`，通过严格配置拒绝临时改权重。

运行顺序：`FGVD-off → local CE → confusion contrast → crop distill → top-k rerank`。
所有训练均从 `MODEL-V5-TEMPLATE-V1@2f5fa5e` 开始，固定 50 epoch、同一数据、
同一 seed 5 初筛；输出目录必须不存在。

大文件身份检查会在第一次完整计算 SHA-256，后续路径、大小和修改时间未变时
复用清单，只对发生变化的文件重算。
