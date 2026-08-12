# 两轮对抗式代码审核记录模板

本模板只提供最小字段。审核记录可直接写进当前任务输出或现有实验质量记录，不要求复制成一套新文件。

```text
reviewed_code_id: commit:<40位SHA> | diff_sha256:<64位SHA>
reviewed_extra_files: [] | <排序后的 path=SHA256>
machine_test_ref:
frozen_run_commit:            # 正式训练必填
freeze_equivalence: pass      # 正式训练必填

round: 1
reviewer_id:
previous_round_ref: not_applicable
files_reviewed:
findings:
unresolved_blockers: 0
decision: pass | blocked
uncovered_scope:

round: 2
reviewer_id:
previous_round_ref:
files_reviewed:
findings:
unresolved_blockers: 0
decision: pass | blocked
uncovered_scope:
```

硬规则：

- 两个 `reviewer_id` 必须不同，Reviewer 只读；
- 第 2 轮必须晚于第 1 轮问题修复、重测和复核；
- 两轮必须检查同一个 `reviewed_code_id`；
- 两轮必须记录相同的 `reviewed_extra_files`，不得漏掉范围内 untracked 或仓库外文件；
- 第 2 轮若促成代码修改，原记录失效，仍由这两个 Reviewer 按顺序重来；
- 正式 Runner 只使用 `frozen_run_commit`；其内容必须与已审核身份等价，否则两轮重来；
- 两轮未全部 `pass` 或 `unresolved_blockers` 不为 0 时，禁止正式训练。

旧 `review_tier`、`review-1`、`strict-3` 和 `validate-ai-cross-review` 只用于历史审核包回查。
