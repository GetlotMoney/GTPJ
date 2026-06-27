# 创意树

这个目录是 GitHub 仓库中的轻量 idea 事实索引。它不是完整论文笔记库，
也不是本地长版创意树。

完整论文阅读、长推理、创新草稿、失败路线和图示草稿放在本地：

```text
D:\Backup\Documents\Myself\GTPJ_Research
```

GitHub 这里只保存能让实验可追溯的最小证据：idea id、来源、版本评分、假设、
实现范围、风险、关联 trial、artifact/research URI 和下一步。

`inbox.md` 用来暂存粗糙想法。只有来源和版本适配记录清楚的想法，才移动成稳定的
`IDEA-xxxx` 节点。没有 idea 节点，就不能启动模块 trial。

## 必需结构

```text
idea_tree/
|-- INDEX.md                 # 给人读的总创意清单，不直接决定实验顺序
|-- idea_tree.json           # 机器可读的总创意注册表，唯一事实源
|-- ideas/
|   `-- IDEA-xxxx_slug/      # 单个 idea 的轻量说明，不放长笔记
|-- versions/
|   |-- v1.md                # v1 创意选择清单
|   `-- v2.md                # v2 创意选择清单
|-- queues/                  # 从总索引派生出的当前执行队列
`-- sources/                 # 论文/来源索引
```

## 轻量字段

GitHub idea 记录只写：

```text
idea_id
标题
来源 paper/code/user observation
source_status
global_score
version_scores.v1/v2/vX
hypothesis
implementation_scope
risk
linked_trials
evidence artifact id / research URI
next_action
```

不要在这里写完整论文笔记、长摘录、长推理或草稿。

## 排序规则

创意先进入总创意库，再按框架版本生成版本视图。

```text
global_score = 长期价值估计
version_scores.v1 = 这个创意对 GTPJ-v1 的适配记录
version_scores.v2 = 这个创意对 GTPJ-v2 的适配记录
```

`INDEX.md` 是总创意清单，只回答项目里有哪些创意。某个版本下一步适合试什么，
读取 `versions/<version>.md`，例如 `versions/v1.md`。

一个创意可以同时适用于多个版本，但每个版本可以有不同分数、阶段和实现说明。

例子：

```text
IDEA-0001 属性路由
  global_score: 80
  version_scores.v1.score: 40   # v1 接口不适合，成本高
  version_scores.v2.score: 85   # v2 已有属性分支，适合直接接入
```

这表示它长期价值高，但在 `v1` 下不一定优先。当前版本是 `v1` 时，
创新 trial 只读取 `versions/v1.md`；当前版本切到 `v2` 后，读取
`versions/v2.md`。

新建 `v2` 后，不能把 `v1` 分数直接复制过去。每个创意都要重新判断：

- v2 是否还保留它需要的输入输出接口；
- 它和 v2 新模块是互补、重复还是冲突；
- 旧实验结果是否仍然有参考意义；
- 需要直接接入、适配，还是标记为不适用。

`versions/vX.md` 是当前版本决策面板。每个 `ideas/IDEA-xxxx_slug/IDEA.md`
是该创意的轻量来源和理由记录。长版材料应指向 `research://` 或本地 `GTPJ_Research`。
只有检查过所选版本适配记录、来源状态、阻塞点和迁移说明后，
才能启动 trial。

来源不清楚时，先放在 `inbox.md`。只有 `source_status` 变成 `verified`
或 `local_heuristic`，并且当前版本评分补全后，才能启动 trial。
