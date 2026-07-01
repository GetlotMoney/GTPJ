# 执行卡：论文读取 / Idea Discovery

当 owner 要求读论文、处理来源、提取创新点时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
paper_intake.md
idea_tree_protocol.md
```

## 角色

默认角色：`阅读/规划 (Reader/Planner)`、`来源复核 (Source Reviewer)`、`总控 (Coordinator)`。

如果输出会影响正式 idea 选择、module trial、baseline 表述或论文实验规划，使用 `real_multi_agent`。

## 输出

长证据写入 `GTPJ_Research`。

轻量 GitHub 记录写入：

```text
idea_tree/sources/
idea_tree/inbox.md
idea_tree/ideas/<IDEA-ID>/
idea_tree/idea_tree.json
idea_tree/versions/<vX>.md
```

## 阻断门

- 没有 verified source 或 owner 接受的 local heuristic。
- 缺少 hypothesis、implementation scope 或 risk。
- idea 没有关联 active version view。
- owner 只要求阅读，没有授权实验执行。
