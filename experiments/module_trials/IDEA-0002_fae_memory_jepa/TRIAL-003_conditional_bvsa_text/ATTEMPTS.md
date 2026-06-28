# TRIAL-003 Attempts

| Attempt ID | Type | Parameter / Change | Old | New | Seed | U | S | H | ZS | Best epoch | Log artifact | Decision | Directory |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| ATTEMPT-001 | planned | BVSA text input | `bvsa_text_mode=adapted`; BVSA uses `all_text [C,768]` | `bvsa_text_mode=conditional`; BVSA uses `all_text_cond [B,C,768]` | 5 | | | | | | | planned | `attempts/ATTEMPT-001/` |

## Notes

- This is a new implementation hypothesis relative to TRIAL-002 because BVSA now directly consumes sample-conditioned text.
- No Runner has started yet.
- `attempts/ATTEMPT-001/config.yaml` is frozen from the branch-local config alias and includes `bvsa_text_mode: conditional`.
