# 版本管理

## Baseline 版本

每个 baseline 命名为：

```text
GTPJ-v1
GTPJ-v2
GTPJ-v3
```

对应 Git tag：

```text
v1
v2
v3
```

每个版本拥有自己的记录目录：

```text
experiments/v1/
experiments/v2/
experiments/v3/
```

## 提升规则

只有成功且通过 review 的 trial 才能成为新的 baseline。

```text
IDEA-0001 -> TRIAL-001 -> promote -> GTPJ-v2
```

不要因为每个小尝试都创建一个新的 `vX`。
