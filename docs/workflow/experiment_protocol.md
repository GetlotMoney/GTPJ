# 实验协议

tune、ablation 和 confirmation 运行都属于某个 baseline 版本。

示例：

```text
experiments/v1/tune/TUNE-001_topo008/
experiments/v1/ablation/ABL-001_disable_jepa/
experiments/v1/confirmation/CONFIRM-043_cond008_seed5/
```

每个实验目录必须包含：

```text
README.md
config.yaml
quality_check.md
logs/
```

规则：

- tune 或 ablation 分支不要修改模型代码。
- 参数搜索只放在 `tune/` 下；不要把 tuning run 放到 `confirmation/`。
- 编辑前，先把版本配置复制到实验目录。
- 记录命令、seed、config、日志路径、U/S/H/ZS、best epoch 和结论。
- 失败运行也是证据，必须记录。
