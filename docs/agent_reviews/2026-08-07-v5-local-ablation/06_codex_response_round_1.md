round: 1
reviewer: codex
addressed_claude_findings:
- 已把最终冻结文字统一改为目录文件描述符绑定，不再把运行时路线写成受控软链接。
- 正式启动后将先核对两个首项 RUN 是否进入真实模型入口，并观察 GPU 0/1 的显存和利用率后再对外报告已开跑。
- 保留 R1、R2 失败凭证，R3 仅在冻结提交和一次性清单全部通过后领取。
validation_rerun:
- 服务器精确候选 45 项控制器测试加 5 项 Linux 真实测试，共 50 项通过。
- 真实 bundle clone 的实验分支、全部管理引用、干净代码目录和 `validate-experiment-base` 均通过。
remaining_blocking_issues:

# 主任务回应

第一轮没有遗留阻断。最小训练探针不代替真实 CUB 训练，因此运行启动后的首项日志与双卡观察仍是必须步骤。
