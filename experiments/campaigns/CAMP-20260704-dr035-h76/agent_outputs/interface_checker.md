# Interface Checker Output

role: `interface_checker`
agent_instance_id: `019f2cbb-a022-7d93-b9e5-fe223bc7d001`
display_name: `CAMP-20260704-dr035-h76 | Interface Checker`
system_nickname: `Schrodinger`
decision: allow

本轮只允许使用现有 GTPJ-v5 / IDEA-0003 dynamic routing 框架。DR-035 min6 和 100 个调参实验不得改变 CUB xlsa17、seen/unseen split、class order、label mapping、logits shape `[B（图片/样本数量）, C（类别数量）]`、U/S/H/ZS metric semantics。

必须冻结字段：

```text
base_version=v5
base_code_tag=v5
dataset=CUB
num_class=200
random_seed=5
batch_size=64
use_dynamic_routing=true
dynamic_direction_mode=sample
dynamic_gate_hidden=48
dynamic_gate_anchor_lambda=0.005
weight_s2v=0.525
```

DR-035 strict repeat 固定 seed=5；改变 seed 只能叫 seed_sweep，不能叫 exact repeat。
