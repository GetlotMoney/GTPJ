# Runner Monitor Output

role: runner_monitor
agent_instance_id: 019f287c-a108-7031-ba5c-6e1ae6c1c91d
display_name: Pauli / shared Runner Monitor
decision: block

## Checked Scope

- local branch: `codex/dr035-exact-repeat-20260703`
- local base commit before DR035 pre-run edits: `fcbeeae3032a953b2be0e4a8c181dedb1a9fcdfb`
- attempt: `ATTEMPT-007`
- planned run id: `RUN-20260703-0002-dr035-exact-repeat-s5-min3-2gpu`
- server repo: `lab4090:/data/lby/projects/cv_project/GTPJ`
- server active branch: `codex/v5-strict-template-rebuild-confirmation`
- server active commit: `2ec0689496f674fb10a71edf91bf5fa09d3ce9d5`

## Findings

- ATTEMPT-007 Runner must remain blocked until v5 GPU cleanup completes.
- v5 strict-template batch is still running; V5T-003 is active on GPU0.
- GPU1 is idle, but the server branch/worktree must not be switched while v5 is active.
- No DR035 run dir or DR035 process exists on server.
- ATTEMPT-007 run id is executable after v5 completion, but not immediately startable.
- The local DR035 worktree is not yet frozen into a clean commit.
- `validate-agent-runtime` and `multi-agent-preflight` currently fail as expected because pre-run allow checks are not all pass.

## Required Before Runner

- Wait for the v5 strict-template run to finish and verify no v5 training/controller process remains.
- Confirm `nvidia-smi` shows both GPUs free enough for DR035 and no stale compute apps.
- Freeze ATTEMPT-007 files into a clean local commit.
- Sync lab4090 to that exact DR035 branch/commit.
- Refresh runner monitor and evidence-quality decisions to allow/pass.
- Rerun `validate-agent-runtime`, `multi-agent-preflight`, and `agent-cleanup-plan`.
- Generate the frozen batch only after the above gates pass.
