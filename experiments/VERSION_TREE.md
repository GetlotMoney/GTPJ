# 版本树

本文件是全局版本树账本。它只记录正式 baseline 版本之间的代码父子关系，
不记录普通 tune、ablation 或 confirmation 实验。

核心规则：

- 每个正式版本必须有一个明确 `parent_version`。
- `parent_version` 表示代码父节点，不表示实验账本父节点。
- `main` 保存 owner 明确选择的 active code，同时保存全部历史版本账本。
- 从旧父节点提升新版本时，代码层可以来自旧 tag，账本层必须来自提升时的当前 `main`。

## 当前版本树

```text
v1
`-- v2 = parent v1 + IDEA-0001/TRIAL-001 CLIP-A-self text prototype adapter
```

## 版本表

| 版本 | 父版本 | 代码 tag | 账本来源 | 变更类型 | Trial | 说明 |
|---|---|---|---|---|---|---|
| `v1` | none | `v1` | initial | initial_baseline | none | 第一版正式 baseline。 |
| `v2` | `v1` | `v2` | `dev/v1-idea-0001-trial-001-clip-a-self-residual-seenonly@f24a277` | add_module | `trial/v1/idea-0001/trial-001` | CLIP-A-self text prototype adapter 主线版；ATTEMPT-019 CUB seed=5 H=74.29。 |

## 记录模板

新增正式版本时，在表格中增加一行：

```text
| `vX` | `vParent` | `vX` | `main@<commit>` | add_module / replace_module / remove_module / combo | `trial/vParent/idea-xxxx/trial-xxx` | 简短说明 |
```

同时更新：

- `experiments/vX/VERSION.md`
- `experiments/EXPERIMENT_REGISTRY.md`
- `config/versions/vX.yaml`
- `docs/PROJECT_STATUS.md`
- `README.md`
