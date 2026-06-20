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

只有成功且通过质量检查的 trial 才能成为新的 baseline。

```text
GTPJ-v1 -> IDEA-xxxx -> TRIAL-001 -> promote -> GTPJ-v2
```

不要因为每个小尝试都创建一个新的 `vX`。

`vX` 不要求严格线性继承。`v3` 可以基于 `v1` 的新 trial 产生，
也可以基于 `v2` 的新 trial 产生。

```text
v1
|-- dev/v1-idea-0001-trial-001-a -> promote -> v2
`-- dev/v1-idea-0002-trial-001-b -> promote -> v3
```

规则：

- `main` 永远代表最新稳定项目，不要为了重新基于 `v1` 做实验而把 `main` 回退到 `v1`。
- 想从哪个 baseline 做新模块，就从哪个 tag 切 `dev/<base-version>-...` 分支。
- 分支名里的 `v1`、`v2` 是来源版本；提升后的 `vX` 是新的正式版本。
- 版本提升时，必须在新版本记录中写清楚 `base_version`。
