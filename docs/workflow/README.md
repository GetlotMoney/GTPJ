# GTPJ 工作流

当前执行标准是 `SYS-WORKFLOW-V6`。日常读取顺序只有：

```text
AGENTS.md
-> START_HERE.md
-> WORKFLOW_KERNEL.md
-> 当前任务的一张 playbook
```

旧版状态机、命名线程、runtime gate 和多层收据说明统一保存在 `archive/specs/WORKFLOW_PRE_V6_ARCHIVE.md`，没有当前命令权。

## 当前文件

- `START_HERE.md`：五步工作流入口。
- `WORKFLOW_KERNEL.md`：科学、安全和两轮审核边界。
- `WORKFLOW_MANIFEST.yaml`：机器可读 V6 文件索引。
- `WORKFLOW_FILE_MAP.md`：人读文件地图。
- `playbooks/`：九张 V6 任务执行卡。
- `protocols/` 与 `reference/`：只在当前 playbook 明确点名时读取；与前三个入口冲突时，以前三个入口为准。

检查命令：

```powershell
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate
conda run -n dvsr_gpu python workflow/gtpj_workflow.py validate-workflow-consistency
```
