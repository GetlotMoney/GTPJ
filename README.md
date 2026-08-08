# GTPJ

## 先看这里

`main` 是项目总账：记录正式框架、模板身份、实验参数和结果，不在这里直接改模型或启动训练。

正式代码与实验起点分开保存：

```text
正式框架历史代码：framework/v1、framework/v2、framework/v3、framework/v5
V5 冻结模板：framework/v5-template-v1
V5 冻结模板 Tag：model/v5-template-v1
新实验分支：exp/v5/<tune|ablation|innovation|confirmation>/<实验名>
```

新实验必须从冻结模板开始，而不是从 `main` 或另一项实验接着改：

```bash
git fetch --tags origin
git switch -c exp/v5/ablation/ABLATION-002_pse-effect model/v5-template-v1
```

## 当前正式框架

| 框架 | 历史来源 | 代码引用 | 状态 |
|---|---|---|---|
| `FRAMEWORK-V1` | 初始正式框架 | `framework/v1` / `v1` | 历史正式框架 |
| `FRAMEWORK-V2` | 从 V1 演变 | `framework/v2` / `v2` | 历史正式框架 |
| `FRAMEWORK-V3` | 从 V2 演变 | `framework/v3` / `v3` | 历史正式框架 |
| `FRAMEWORK-V5` | 从 V3 演变 | `framework/v5` / `v5` | 当前研究框架 |

`v4` 只是历史配置 Tag，不是独立正式框架。

## V5 当前事实

- 冻结模板：`MODEL-V5-TEMPLATE-V1`；
- 模板提交：`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`；
- 当前模板 Tag：`model/v5-template-v1`；
- V5 局部分支消融：完整 V5 的平均 H 为 `74.11`，去掉整套局部分支后为 `74.03`，平均差值 `+0.08`；不能把局部分支写成稳定的主性能增益。

详细入口：

- [正式框架关系](experiments/FRAMEWORK_TREE.md)
- [V5 身份与模板](experiments/v5/framework.yaml)
- [V5 实验总览](experiments/v5/EXPERIMENTS.md)
- [V5-ABLATION-001 结果](experiments/v5/ablation/ABLATION-001_local_branch_effect/result.md)

## GitHub 边界

GitHub 保存轻量、可追溯的内容：代码、配置、参数表、结果、数据身份和外部证据索引。

原始日志、checkpoint、特征缓存、数据集和服务器运行目录不进入 GitHub；它们只保留在 Warehouse，并由参数表中的路径、哈希和运行编号回查。
