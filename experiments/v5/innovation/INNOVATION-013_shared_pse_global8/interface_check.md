# 接口检查

- 机器检查：4 个函数测试、CUDA logits/backward、9 个冻结输入哈希、实验与参数表校验均通过。
- 第 1 轮：`15c445694dd217d0e2792dcc304ad69e26199c73`，`pass`，阻断项 0。
- 第 2 轮：同一 reviewed code id，`pass`，阻断项 0。
- 边界：全局 8 句、共享类无关参数、真实交错 seen/unseen 映射；无 patch、无局部分支，测试只在恢复验证 checkpoint 后评估一次。
