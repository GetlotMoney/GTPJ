#!/usr/bin/env bash
set -euo pipefail

# 用途：在 lab4090 上恢复 ATTEMPT-009 / h76-existing-routing-100。
# 行为：备份现有状态，只补跑未完成 job；如果发现真实训练进程正在跑，则直接退出。

REPO="${REPO:-/data/lby/projects/cv_project/GTPJ}"
RUN_ID="${RUN_ID:-RUN-20260704-0002-h76-existing-routing-100-2gpu}"
RUN_DIR="$REPO/.gtpj_runtime/batches/$RUN_ID"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

cd "$REPO"

if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR missing RUN_DIR: $RUN_DIR" >&2
  exit 1
fi

if pgrep -af "train_GTPJ|run_dynamic_routing_batch.py|start_batch.sh" >/tmp/gtpj_attempt009_processes.$$; then
  if grep -v "resume_attempt009_h76_server.sh" /tmp/gtpj_attempt009_processes.$$ | grep -q .; then
    echo "ERROR existing GTPJ runner/training processes found; refusing to launch." >&2
    cat /tmp/gtpj_attempt009_processes.$$
    rm -f /tmp/gtpj_attempt009_processes.$$
    exit 1
  fi
fi
rm -f /tmp/gtpj_attempt009_processes.$$

mkdir -p "$RUN_DIR/freeze_records" "$RUN_DIR/logs" "$RUN_DIR/pids"
cp "$RUN_DIR/batch_status.json" "$RUN_DIR/freeze_records/batch_status.before_resume.$STAMP.json"

python3 - <<PY
import json
import pathlib
import subprocess
from datetime import datetime, timezone

repo = pathlib.Path("$REPO")
run_dir = pathlib.Path("$RUN_DIR")
stamp = "$STAMP"

status_path = run_dir / "batch_status.json"
status = json.loads(status_path.read_text(encoding="utf-8"))
jobs = status.get("jobs", {})

completed = [jid for jid, job in jobs.items() if job.get("status") == "completed"]
failed = [jid for jid, job in jobs.items() if job.get("status") == "failed"]
skipped = [jid for jid, job in jobs.items() if job.get("status") == "skipped"]
stale_running = [jid for jid, job in jobs.items() if job.get("status") == "running"]
pending = [jid for jid, job in jobs.items() if job.get("status") == "pending"]

for jid in stale_running:
    job = jobs[jid]
    job["status"] = "pending"
    job["resume_reset_at"] = datetime.now(timezone.utc).isoformat()
    job["resume_reset_reason"] = "stale_running_no_gpu_process"
    job.pop("gpu", None)
    job.pop("pid", None)

status["status"] = "running"
status["updated_at"] = datetime.now(timezone.utc).isoformat()
status["resume_record"] = {
    "stamp": stamp,
    "reset_running_to_pending": stale_running,
    "completed_before_resume": len(completed),
    "failed_before_resume": len(failed),
    "skipped_before_resume": len(skipped),
    "pending_before_resume": len(pending),
}
status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

def sha16(path: pathlib.Path) -> str:
    import hashlib
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]

commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=repo, text=True).strip()
dirty = subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True)

record = {
    "stamp": stamp,
    "purpose": "resume ATTEMPT-009 h76-existing-routing-100 unfinished jobs",
    "run_id": "$RUN_ID",
    "run_dir": str(run_dir),
    "branch": branch,
    "commit": commit,
    "server_dirty_state": dirty.splitlines(),
    "plan_sha16": sha16(run_dir / "plan.json"),
    "batch_status_before_sha16": sha16(run_dir / "freeze_records" / f"batch_status.before_resume.{stamp}.json"),
    "run_script_sha16": sha16(run_dir / "run_dynamic_routing_batch.py"),
    "start_script_sha16": sha16(run_dir / "start_batch.sh"),
    "completed_before_resume": completed,
    "failed_before_resume": failed,
    "skipped_before_resume": skipped,
    "reset_stale_running_to_pending": stale_running,
}
(run_dir / "freeze_records" / f"resume_freeze.{stamp}.json").write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + "\\n",
    encoding="utf-8",
)

print("resume_freeze_record", run_dir / "freeze_records" / f"resume_freeze.{stamp}.json")
print("completed_before_resume", len(completed))
print("reset_stale_running_to_pending", ",".join(stale_running) if stale_running else "none")
print("remaining_to_run", len(pending) + len(stale_running))
PY

cd "$RUN_DIR"
nohup bash start_batch.sh > "logs/resume_launch.$STAMP.out" 2>&1 &
echo $! > "pids/resume_launcher.$STAMP.pid"

sleep 5
echo "resume_launcher_pid=$(cat "pids/resume_launcher.$STAMP.pid")"
echo "controller_pids:"
ls -1 pids/*.pid 2>/dev/null | xargs -r -I{} sh -c 'printf "%s " "{}"; cat "{}"; printf "\n"'
echo "gpu:"
nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader
echo "top_status:"
python3 "$REPO/workflow/gtpj_workflow.py" dynamic-routing-status --run-dir "$RUN_DIR"
