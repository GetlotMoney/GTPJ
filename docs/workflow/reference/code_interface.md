# Code Interface Contract Alias

The canonical code interface contract is:

```text
docs/workflow/protocols/code_interface_contract.md
```

This file exists so external checklists, agents, or prompts that look for `docs/workflow/reference/code_interface.md` do not miss the interface gate.

Rules:

- Read `docs/workflow/protocols/code_interface_contract.md` before changing model code, forward paths, loss, data flow, scoring, or evaluation behavior.
- If the change comes from an idea, innovation, paper module, official code, or module trial, also read `docs/workflow/protocols/innovation_code_review_protocol.md`.
- If interface, label mapping, seen/unseen split, class order, logits shape, or metric semantics are unclear, the experiment is invalid evidence.
- Unclear interface evidence blocks Runner, `keep`, and `promote`.
