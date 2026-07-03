# Paper Intake / Idea Discovery

本模块专门处理“读论文、登记论文、提取创新点、同步到 GitHub idea_tree”。
它不跑实验，也不直接创建 module trial。

## 入口

Owner 可以把 PDF 放到：

```text
D:/Backup/Documents/Myself/GTPJ_Research/papers/_inbox/
```

然后说：

```text
按 GTPJ paper intake / idea discovery 工作流处理 _inbox。
基于 v2 提取可用创新，先不跑实验。
```

## 事实源

```text
GTPJ_Research/papers/PAPERS_INDEX.md
```

这是判断“哪些论文读过、读到什么阶段、有没有提取 idea”的本地论文登记表。
不要只靠 PDF 是否存在来判断阅读状态。

## 阅读状态

| status | 含义 | 是否能进 GitHub idea_tree |
|---|---|---|
| `new` | 已收集，未阅读 | 否 |
| `skimmed` | 已快速浏览 | 通常否 |
| `reading` | 正在精读 | 否 |
| `reviewed` | 已形成来源复核 | 可以进入 source index 或 candidate |
| `idea_extracted` | 已提取候选机制 | 可以进入 inbox 或 IDEA-xxxx |
| `synced_to_github` | 轻量事实已同步到 GitHub idea_tree | 可以排队 |
| `used_in_trial` | 已进入实验或作为实验依据 | 已有 linked trial |
| `archived` | 暂不使用 | 否 |

旧状态 `used` 等价于 `used_in_trial`，保留兼容。

## 标准流程

1. 扫描 `_inbox/`，为每篇论文分配 `paper_id`。
2. 在 `PAPERS_INDEX.md` 中登记标题、年份、方向、路径、状态和 next action。
3. 将论文整理到 `papers/PAPER-YYYY-short-name/`。
4. 创建或更新：

```text
paper_meta.yaml
reading_notes.md
source_review.md
code_review.md
extracted_ideas.md
code/
figures/
```

5. 如果论文、附录或项目页包含 GitHub 官方代码链接，必须把代码克隆到同一个论文目录：

```text
papers/PAPER-YYYY-short-name/code/<repo-name>/
```

只克隆参考实现代码，不主动下载数据集、checkpoint、预训练权重、日志、结果目录或大文件 artifact。
克隆时优先使用浅克隆、跳过 LFS smudge，并在 `paper_meta.yaml`、`code_review.md`
和 `PAPERS_INDEX.md` 中记录 `official_code_url`、`official_code_path`、clone commit
以及排除的数据/权重范围。
6. 如果没有可用机制，只保留 Research 记录并把状态设为 `reviewed` 或 `archived`。
7. 如果有粗糙想法，写入 GitHub `idea_tree/inbox.md`，状态保持 candidate。
8. 如果机制成熟，创建或更新 GitHub：

```text
idea_tree/sources/papers_index.md
idea_tree/ideas/IDEA-xxxx_slug/IDEA.md
idea_tree/idea_tree.json
idea_tree/versions/<base_version>.md
idea_tree/queues/01_selected_next.md 或 02_module_candidates.md
```

9. 收尾必须写 `sync_check`，确认 GitHub 轻量记录能反查 Research 长版材料和本地参考代码。

## 进入正式 IDEA 的条件

只有同时满足下面条件，才能从论文阅读升级成正式 `IDEA-xxxx`：

- `source_status` 是 `verified` 或 `local_heuristic`。
- 有明确 `source_ref`，能指向论文、官方代码或可复核观察。
- 如果来源声明有官方 GitHub，`source_ref` 必须能同时指向 `official_code_url` 和本地
  `official_code_path`；除非 clone 失败并已记录失败原因。
- 有 `hypothesis`、`implementation_scope` 和 `risk`。
- 有当前 base version 的 `version_scores.<vX>`。
- 接口影响能由 Interface Checker 检查。
- blockers 为空，或明确只能留在 inbox。

## 同步边界

```text
Research: 完整阅读、长推理、源码复核、候选 idea 草稿
GitHub: paper/source 轻量索引、正式 idea、版本评分、next_action
Warehouse: paper intake 通常不写；只有生成大型 OCR/图表/长报告时才登记
```

禁止只在聊天里确认“这篇论文有用”。凡是会影响后续实验选择的结论，必须写入
`PAPERS_INDEX.md`、Research 长版记录和 GitHub 轻量索引中的相应位置。
