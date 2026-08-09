# Runner Monitor Output

role: `runner_monitor`
agent_instance_id: `019f2cbc-2293-7902-83a1-8336abf43a72`
display_name: `CAMP-20260704-dr035-h76 | Runner Monitor`
system_nickname: `McClintock`
decision: allow_after_freeze

服务器资源层允许启动：`lab4090:/data/lby/projects/cv_project/GTPJ` 可访问，两张 RTX 4090 空闲，未发现旧 GTPJ 训练进程或 runner lock，`data`、`GTPJ_Warehouse` 和 `GTPJ_Research` 存在。

启动前必须冻结本地 commit，并让服务器切到同一个 commit。远端当前仍在 `codex/dr035-exact-repeat-20260703`，不能直接代表本轮 `dr035-min6-confirm` 和 `h76-existing-routing-100` profile。

runner 字段要求：

```yaml
server: lab4090
repo_path: /data/lby/projects/cv_project/GTPJ
gpu_state: idle
old_processes: none_found
runner_lock: none_found
data_root: /data/lby/projects/cv_project/GTPJ/data
warehouse_root: /data/lby/projects/cv_project/GTPJ_Warehouse
```
