# 接口检查

- 句子 `[200,8,768]`，CLS `[N,768]`，patch `[N,576,768]`。
- candidate classes 为唯一全局类编号；输出分数 `[N,C]`，逐角色贡献 `[N,C,8]`。
- top-k 固定 8；删除最高范数或随机 patch 后，空间均值分母固定为 575。
- `lambda=0` 精确回到 Mean8；official cache 在选择状态保存后才加载。
