# V5-ABLATION-008 服务器启动计划

## 固定分配

- 物理 GPU 1，由外层队列设置 `CUDA_VISIBLE_DEVICES=1`。
- 进程内设备继续使用配置中的逻辑 `cuda:0`。
- 顺序：先运行一条 `C-FROZEN` 和一条 `GL-FULL` 做路径检查，再按冻结映射完成其余任务；不得根据中途分数改变配置。

## 唯一正式启动者

只能由冻结后的 `CAMP-20260809-v5-ablation100` 统一控制器正式启动，禁止手工正式启动。每个 RUN 使用独立且不存在的外部输出目录，保存 `training.log`、`metrics.json`；训练路径另保存 `best_model.pth`，冻结路径不产生 checkpoint。

控制器启动每个 RUN 时必须同时传入本目录的 `DATA_MANIFEST.json` 和服务器实际数据根目录，并把启动时 clean 工作树的完整 HEAD 作为 `--expected-run-commit`。该 HEAD 是结果里的 `run_commit`；参数表中的 `code_ref` 固定为最后修改可执行代码的 E 提交 `8f71fa45839f8f2df8bc1bbb78be478246f24b71`，两者不得混写。
