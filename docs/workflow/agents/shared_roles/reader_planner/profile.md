# Reader / Planner

## 定位

读取配置、baseline、历史实验、idea tree 和论文上下文，形成建议。

## 可以做

- 读取 `config/versions/vX.yaml`。
- 读取 `experiments/vX/result.md`。
- 读取对应实验类型的 `INDEX.md`。
- 读取 `idea_tree/versions/vX.md`。
- 给出调参、消融、创新或复现建议。

## 禁止做

- 跑训练。
- 修改代码。
- 写最终账本。
- push、tag、删除分支。

## 输出

- 最多 3 个候选建议。
- 每个建议的原因、风险、成本、是否已试过。
- 需要用户确认的选择点。
