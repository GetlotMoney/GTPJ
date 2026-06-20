# 创意树

这个目录是模块创新的事实来源。

`inbox.md` 用来暂存粗糙想法。只有被选中的想法才移动成稳定的
`IDEA-xxxx` 节点。

没有 idea 节点，就不能启动模块 trial。

## 必需结构

```text
idea_tree/
|-- INDEX.md                 # 给人读的总排名
|-- idea_tree.json           # 机器可读的创意注册表
|-- ideas/
|   `-- IDEA-0001_short_name/
|       `-- IDEA.md          # 来源、假设、版本评分、约束
|-- queues/                  # 从总索引派生出的当前执行队列
`-- sources/                 # 论文/来源索引
```

## 排序规则

创意按框架版本排序，不只按全局价值排序。

```text
global_score = 长期价值估计
version_scores.v1.score = 对 GTPJ-v1 的当前价值
version_scores.v2.score = 对 GTPJ-v2 的当前价值
```

当前激活的框架版本使用自己的分数列。一个创意可以同时适用于多个版本，
但每个版本可以有不同分数和不同实现说明。

`INDEX.md` 是当前决策面板。每个 `ideas/IDEA-xxxx_slug/IDEA.md`
是该创意的来源和理由记录。只有检查过所选版本分数、来源状态、阻塞点和迁移说明后，
才能启动 trial。
