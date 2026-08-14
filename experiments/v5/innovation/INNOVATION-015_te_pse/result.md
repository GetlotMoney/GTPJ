# V5-INNOVATION-015 结果

```text
status: completed_stop_no_gain
decision: stop_no_gain
evidence_level: valid_single_run
not_confirmation_evidence: true
promotion_decision: rejected
```

## 结论

TE-PSE 没有提高当前 GPT-5.6 八句纯 CLIP 基线。相对同次 B0，U 略升 `0.213766`，
但 S 下降 `1.172471`，最终 H 下降 `0.462097`、ZS 下降 `0.473136`。因此按冻结规则停止，
不进入 seed 17、机制 control、confirmation 或 promotion。

唯一共享强度已经达到上限 `0.5` 的 `99.61%`，所以失败不能解释为“参数没学到”；当前角色
rival 证据方向本身没有形成 U/S 共同增益。本结论只有 seed 5 单次观察，不作稳定性声明。

## 完整结果

| 路径 | U | S | H | ZS | best epoch |
|---|---:|---:|---:|---:|---:|
| 同次 B0，`alpha=0` | 63.037896 | 65.331149 | 64.164039 | 80.301231 | - |
| TE-PSE | 63.251662 | 64.158678 | 63.701942 | 79.828095 | 99 |
| TE-PSE - B0 | +0.213766 | -1.172471 | -0.462097 | -0.473136 | - |

机制诊断：`best_validation_loss=2.493268013`，`evidence_strength=0.498062223`，
`coherence min/mean/max=0.133762/0.247409/0.377835`，最大加法分解误差
`2.384186e-7 <= 1e-6`。

## 身份与证据

- run commit：`b7f060afdd6d42baeee25b4d3068389085d88286`
- config SHA-256：`23d1a15060d09bbaab74df2294661d54172ff4c509c89e1ec24bc582a7deb91c`
- Warehouse：`warehouse://runs/v5/innovation/V5-INNOVATION-015/RUN-001`
- `training.log`：`0896ea96c7e8b9618651f869ce6a25a886183f4013e669c05710976e7eb8c10f`
- `metrics.json`：`c06b40c05231cf426031968b624a548f676da4462cf86f83cf81dadc3f72b32a`
- `result.yaml`：`8f84abe785828b39e36649d471e2345511a8c80d3d1c34483d3788a5c6b1f5d1`
- `model_best.pth`：`239f1590e920203bc103ff41c90260824ccf9e0cbcb3800661a34b96ba43e493`

服务器没有生成 `artifact_manifest.json`，因此参数矩阵的 manifest 哈希保持空白，不补造证据。
