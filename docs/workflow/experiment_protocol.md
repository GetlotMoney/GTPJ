# 实验协议

tune、ablation 和 confirmation 运行都属于某个 baseline 版本。

示例：

```text
experiments/v1/tune/TUNE-001_topo008/
experiments/v1/ablation/ABL-001_disable_jepa/
experiments/v1/confirmation/CONFIRM-001_v1_seed5/
```

每个实验目录必须包含：

```text
README.md
config.yaml
quality_check.md
logs/
```

每个普通实验 README 必须记录：

```text
experiment_id:
version:
base_code_tag:
run_commit:
dirty_state:
command:
seed:
config:
python_env:
torch_cuda:
dataset_split:
cache_fingerprint:
original_log:
copied_log:
artifact_manifest:
attempt_id:
failure_stage:
decision:
```

规则：

- `exp/...` 临时分支从当前 `main` 开出，保证继承最新账本。
- `base_code_tag` 记录本次实验使用的代码来源，例如 `v1`。
- 当前 `main` 代码不是目标 `base_code_tag` 时，只恢复代码层，不恢复账本层。
- tune 或 ablation 分支不要修改模型代码。
- 参数搜索只放在 `tune/` 下；不要把 tuning run 放到 `confirmation/`。
- 编辑前，先把版本配置复制到实验目录。
- 记录命令、seed、config、日志路径、U/S/H/ZS、best epoch 和结论。
- 失败运行也是证据，必须记录。

Tune 必填：

- `tuned_parameter`；
- `old_value`；
- `new_value`；
- `search_space`；
- `single_variable: yes/no`；
- `baseline_H`；
- `trial_H`；
- `delta_H`；
- `promotion_rule`。

Ablation 必填：

- `disabled_module`；
- `switch_key`；
- `baseline_off_path`；
- `expected_effect`；
- `affected_contracts`；
- `control_result`；
- `ablation_delta`。

失败运行必填：

- `failure_stage`：setup / data / forward / backward / eval / logging / unknown；
- 错误摘要；
- stderr 或 log 路径；
- 是否需要 retry；
- 本次失败是否改变下一步实验计划。
