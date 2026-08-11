# V5-ABLATION-011 产物核对

本页记录 2026-08-09 在项目总目录现场读取到的文件大小与 SHA256。训练产物仍位于 `.runtime/runs/v5/local_complementarity/V5-ABLATION-011/`，本页只是轻量索引，不复制训练文件。

## RUN-001

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `training.log` | 16343 | `854f18ea3a5370ca4edaac27ec6082bcb43189866b92df2481c2f3eb22b69d94` |
| `metrics.json` | 7440 | `ae291efc484ed5ebac9c2efdad5bd132cb7e4f3127a946c86efe5244889c10ef` |
| `model_best.pth` | 15968213 | `8efc189956d30ddc687023f2f33e25111e11dba360472076e02f2ce1607d5b69` |
| `checkpoint_last.pth` | 40228660 | `b26a875cb2b4c2d4ef8e29643d24d432e2ebd8a142ccd3e175ab1b9979cfa248` |

## RUN-002

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `training.log` | 16343 | `723083c5e05c3078fb39137c834637008b2741d7ed0e3141474f4f17b8dd995e` |
| `metrics.json` | 7440 | `c937b4968bde0fd9c6978a2992e10e4d1430e8ee22f00765316fca1d00f77a77` |
| `model_best.pth` | 15968213 | `8efc189956d30ddc687023f2f33e25111e11dba360472076e02f2ce1607d5b69` |
| `checkpoint_last.pth` | 40228660 | `b26a875cb2b4c2d4ef8e29643d24d432e2ebd8a142ccd3e175ab1b9979cfa248` |

## RUN-003

| 文件 | 字节数 | SHA256 |
|---|---:|---|
| `training.log` | 16343 | `6e50d198606a6527bfef32e04345a80ddaad6a9a0e717dab7de7865051601dfc` |
| `metrics.json` | 7440 | `8907bf02c9ce0ceb1919d610f4260735fb716be250db48053a2cbc0552b663b6` |
| `model_best.pth` | 15968213 | `8efc189956d30ddc687023f2f33e25111e11dba360472076e02f2ce1607d5b69` |
| `checkpoint_last.pth` | 40228660 | `b26a875cb2b4c2d4ef8e29643d24d432e2ebd8a142ccd3e175ab1b9979cfa248` |

三个目录均只有上述四个文件，没有 `artifact_manifest`。因此参数表记录各 RUN 目录作为 `artifact_ref`，并把 `artifact_manifest_sha256` 留空。
