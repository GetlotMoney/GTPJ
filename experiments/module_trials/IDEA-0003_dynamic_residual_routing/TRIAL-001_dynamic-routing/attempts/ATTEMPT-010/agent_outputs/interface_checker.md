# Interface Checker Output

role: `interface_checker`
agent_instance_id: `019f3356-93a3-7c61-a29d-5edfda23d8a4`
workflow_display_name: `ATTEMPT-010 | Interface Checker`
thread_title: `ATTEMPT-010 | Interface Checker`
agent_instance_mode: `named_owner_thread`
decision: `allow`

## 结论

允许启动复现。四个候选的 same-seed min5 repeat 只复用已有动态路由配置，不改变 GZSL 评估语义。

## 检查点

- seed 全部固定为 `5`。
- `dynamic_direction_mode=sample`，`dynamic_gate_hidden=48`。
- `_dynamic_updates` 默认保持 `dynamic_local_mode=fixed`、`dynamic_icsa_mode=fixed`、`dynamic_pse_mode=fixed`。
- 不引入非法 `dynamic_pse_mode=sample`。
- 不改变 CUB xlsa17 数据、seen/unseen split、class order、label mapping、logits shape、U/S/H/ZS 计算。

## 边界

这是 Interface allow，不等于 promotion allow。结果必须报告 mean/min/max/range，不能只凭 best single 升版。

## 线程声明

未启动 Runner / 未改文件 / 未创建子 agents。
