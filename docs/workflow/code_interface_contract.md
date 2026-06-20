# 代码接口契约（Code Interface Contract）

任何会修改模型代码、forward 路径、loss、数据流、打分或评估行为的模块 trial，
都必须遵守这份契约。

目标：

```text
新增模块可以测试一个假设，但不能静默改变 baseline 接口、tensor shape 或评估语义。
```

## Baseline-Off Equivalence（基线关闭等价）

每个新模块都必须有明确的 config switch。

当 switch 关闭时，选定 base version 的行为必须等价于原 baseline：

- forward 输入相同；
- forward 输出相同；
- logits shape 相同；
- class order 相同；
- 启用的 loss 和 loss weight 相同；
- evaluation 输入/输出格式相同；
- base version 的 config 默认值相同。

关闭路径不是“差不多接近”。它必须就是 base version 路径。

## Module Boundary（模块边界）

每个模块 trial 必须声明一个接入点：

- 文件；
- class 或 function；
- before/after 位置；
- 消耗的变量名；
- 产出的变量名。

不要让一个 trial 的改动散落在模型的无关位置。如果一个模块需要多个接入点，
必须说明原因，并按高风险处理。

## Input Contract（输入契约）

对每个被消耗的 tensor 或结构化输入，记录：

- 名称；
- shape；
- dtype；
- device；
- 语义含义；
- 是否期望梯度。

示例：

```text
visual_patch: [B, P, D], float32, cuda, CLIP patch tokens，启用梯度
text_attr: [C, A, D], float32, cuda, 类别属性文本特征，冻结
```

## Output Contract（输出契约）

对每个产出的 tensor 或结构化输出，记录：

- 名称；
- shape；
- dtype；
- device；
- 语义含义；
- 是否替换已有变量，还是只作为辅助输出。

如果模块改变维度，必须明确声明：

```text
D_in -> D_out
projection owner:
baseline path affected: yes/no
```

## Shape Invariants（形状不变量）

除非 trial 明确声明例外，否则必须保持这些不变量：

- batch 维 `B` 保持不变；
- class 维 `C` 保持不变；
- logits shape 保持 `[B, C]`；
- visual/text embedding 维度仍与 base scorer 兼容；
- seen/unseen class order 不变；
- score、loss 或 calibration 逻辑中不允许意外 broadcasting。

任何有意破坏不变量的改动都必须按高风险质量检查处理，并且没有 version bump
不能提升。

## Config Switch Contract（配置开关契约）

新的 trial switch 必须先是 trial-local。

提升前允许修改：

```text
experiments/module_trials/IDEA-xxxx_slug/TRIAL-xxx_slug/config.yaml
```

提升前不允许修改：

```text
config/versions/v1.yaml
experiments/v1/config.yaml
```

成功通过质量检查并提升后，switch 才能进入新的版本配置，例如 `config/versions/v2.yaml`。

默认值必须保持 baseline：

```text
use_new_module: false
lambda_new_loss: 0
mode: baseline-compatible default
```

## Loss Contract（Loss 契约）

新 loss 默认必须关闭。

必须满足：

```text
lambda_new_loss = 0 -> total loss is unchanged
lambda_new_loss > 0 -> 新 loss 只按该权重贡献到 total loss
```

新增 loss 不能静默改变已有 loss 的 normalization、reduction 或 weighting。

## Evaluation Contract（评估契约）

除非实验本身就是评估实验，否则模块 trial 不能改变 evaluation 语义。

受保护项目：

- class order；
- seen/unseen split；
- logits shape；
- calibration path；
- metric calculation；
- evaluation script 消耗的 output fields。

改变任何受保护项目都需要高风险质量检查，并且必须记录为高风险接口变更。

## Checkpoint Contract（Checkpoint 契约）

新模块应尽量保持 checkpoint 兼容。

如果新增参数，记录：

- 新的 state dict keys；
- 旧 checkpoint 是否可以用 `strict=False` 加载；
- missing/unexpected keys 是否符合预期；
- base version 是否仍能从 tag 恢复。

## Minimum Verification（最低验证）

模块 trial 开始训练前，必须记录或执行可用的最轻量检查：

- switch off forward pass；
- switch on forward pass；
- logits shape；
- loss scalar 和 backward pass；
- 预期 loss keys；
- evaluation 输出的 class count；
- base config files 没有意外变化。

如果完整训练成本太高，可以使用 dry run、小 batch 或 shape probe，
但必须记录为什么这些检查足以通过质量门。

## Promotion Rule（提升规则）

模块 trial 只有在满足以下条件时，才能提升为新的 baseline version：

- implementation 满足本契约；
- quality check decision 为 `ACCEPTED`；
- trial 已记录结果证据；
- baseline-off path 仍然有效；
- 新版本 config 与旧 base version config 分开创建。
