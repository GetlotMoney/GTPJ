# V5-INNOVATION-003 本地证据索引

训练产物唯一根目录为 `.runtime/runs/v5/local_complementarity/V5-INNOVATION-003/`。下表的大小和 SHA256 由 2026-08-09 对现有文件现场重算得到；这些原始文件不进 Git。

## 有效三轮

| 运行 | 文件 | 字节数 | SHA256 |
|---|---|---:|---|
| `RUN-001` | `training.log` | 22544 | `93acf77faf69f457272f34397059c805822d7e660fb8eaf446f500091d2738a5` |
| `RUN-001` | `metrics.json` | 37353 | `fcfef95d3623b8d37ec1a506b72003b8d48008d597e9667423a0b8a6bd366bee` |
| `RUN-001` | `model_best.pt` | 98419066 | `3b526601a01421aa3c632b1abb3a8934cae2587cc0c64ba9fd73aa2f0e7b8d5d` |
| `RUN-001` | `checkpoint_last.pt` | 202655107 | `c6dc0a6307ab0084c9de7f1f4c96b944a7a2cc8b5ad9c0f85e67059d41ec4308` |
| `RUN-002` | `training.log` | 22544 | `ca6ca5fbeb695889fb0ab593528107a16771d55e72e0f2d27559b4bc1e2bf5c1` |
| `RUN-002` | `metrics.json` | 37352 | `021f3333e0dbbea5dd004e3627e33a4533a20752daf42174f1b75520ca8f40c3` |
| `RUN-002` | `model_best.pt` | 98419066 | `3d5be13c696e08668f4e1832a9f027a5d70056923d241162d4ed51a53c2a2c3b` |
| `RUN-002` | `checkpoint_last.pt` | 202655107 | `e07ac2784d2cca6ea1b3d2d3b2b7535cfde5861ffb59f7cd78d5c154b281289b` |
| `RUN-003` | `training.log` | 22544 | `1600e880f68cd8d5eda8712e70a8ebbfa0b599057ded60eb7cf99c8dec62e00e` |
| `RUN-003` | `metrics.json` | 37348 | `cc42a00c99573a7444a745bca050aaf32da204f1218f8eeed3cc7ea6b77c9a40` |
| `RUN-003` | `model_best.pt` | 98419066 | `572e1d955dd53d8f2d07d18ce7d3f29aeedec584d37040a595f972e130480f58` |
| `RUN-003` | `checkpoint_last.pt` | 202655107 | `7789132de767df9852983b9785435e1d7700847824e287c87d13699635aac8ab` |

三轮配置快照均为 `1406` 字节，SHA256 均为 `cba09034a3b773b78d51cb3c28f35f0fee95ce7536f41be617b7bc04c98cf2ee`。有效运行的代码 commit 均为 `61734def74d13c15a110ad3e98e609a17c2115c6`。

## 不计入三轮的启动失败

| 运行 | 文件 | 字节数 | SHA256 |
|---|---|---:|---|
| `RUN-000-startup-failure` | `training.log` | 3538 | `cfcb3281498bc68886ac45a77a9d9f43d0daf1c426d1779090bbaa93d60c4d3f` |
| `RUN-000-startup-failure` | `metrics.json` | 10561 | `6bf833bba8874bd82f17a67fff39e34a84341d25c7e01b7faa9ca20fdcb3c8a9` |

该失败来自修复前 commit `dfbabccad889b5be7a8fdb35d55d0faca2b259fc`，是在第 1 个 epoch 前发生的 CPU/CUDA 设备不一致；它被保留供回查，不影响 `RUN-001..003` 的结果统计。

## manifest 状态

本轮训练入口没有生成独立 artifact manifest。因此 `PARAMETER_MATRIX.csv` 的 `artifact_manifest_sha256` 留空；本文件是人工可读索引，不冒充训练时生成的 manifest。
