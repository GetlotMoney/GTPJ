# Agent Lifecycle

| Role | Agent id | Lifecycle | Scope | Output |
|---|---|---|---|---|
| Campaign Planner | 019f21fe-adc2-7932-bc69-58d8c384598a | campaign_scoped | candidate design | warning / allow planning |
| Runner Monitor | 019f21ad-89e5-72a1-b985-df3bf5ca8ca2 | campaign_scoped | server/GPU/batch readiness | block then re-check |
| Interface Checker | 019f21ff-27d7-7f60-b2aa-65a80fce0a48 | task_scoped | GZSL and dynamic config legality | block until gate exists |
| Evidence Quality Checker | 019f21ff-27d7-7f60-b2aa-65a80fce0a48 | task_scoped | evidence chain and runtime gate | block until gate validates |

The Coordinator remains the only GitHub ledger writer.
