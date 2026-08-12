# Interface Checker 开跑检查

```text
role_key: interface_checker
decision: allow
```

- 训练入口只接受 8 个本实验字段，旧模块字段会直接报错。
- 八句缓存固定为 `[200,8,768]`，模型输入固定为 CLS 加全部 576 个普通区域。
- 训练输出 seen 类 logits，评估输出 200 类全局顺序 logits；CPU/GPU 类别索引边界已有专项测试。
- 唯一损失是 seen 类交叉熵；旧 V5 checkpoint 因实验身份不符会被拒绝。
