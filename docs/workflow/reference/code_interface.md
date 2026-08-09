# Code Interface Contract Alias

权威 code interface contract 是：

```text
docs/workflow/protocols/code_interface_contract.md
```

本文件用于兼容会查找 `docs/workflow/reference/code_interface.md` 的外部 checklist、agents
或 prompts，避免它们错过 interface gate。

规则：

- 修改 model code、forward paths、loss、data flow、scoring 或 evaluation behavior 前，先读 `docs/workflow/protocols/code_interface_contract.md`。
- 如果改动来自 idea、innovation、paper module、official code 或 module trial，也要读 `docs/workflow/protocols/innovation_code_review_protocol.md`。
- 如果 interface、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 不清楚，该实验就是 invalid evidence。
- interface evidence 不清楚时，Runner、`keep` 和 `promote` 全部阻断。
