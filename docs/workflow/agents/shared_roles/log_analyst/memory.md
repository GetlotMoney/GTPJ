# Log Analyst Memory

## Standing Lessons

- 日志解析只报告日志中真实存在的指标，不补造缺失字段。
- visible warning 不等于 root cause，除非和失败时间、堆栈或指标断点对齐。
- 需要同时记录 U/S/H/ZS、best_epoch、seed、config 和 log path。

## Recurrent Failure Modes

- 把成功 run 中也出现过的 warning 当成失败根因。
- 只摘 H，不记录 U/S 差距和 best epoch。
- 日志路径没有入 Warehouse 或没有 hash/size。

## Required Checks

- metrics parse
- best epoch
- seed/config
- log path
- failure traceback
- Warehouse artifact registration。

## Update Rules

日志解析、warning 归因或 artifact 登记错误重复出现时更新本文件。
