#!/usr/bin/env bash
set -euo pipefail

ROOT="/data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches"
STATUS_FILE="$ROOT/ATTEMPT-011_SERVER_STATUS.json"
GLOBAL_STOP_FILE="$ROOT/ATTEMPT-011_STOP_REQUESTED"
RUN_IDS=(
  "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu"
  "RUN-20260706-0002-h76-mixed200-b02-search50-2gpu"
  "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu"
  "RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu"
)

write_status() {
  local current_batch="$1"
  local supervisor_state="$2"
  python3 - "$STATUS_FILE" "$ROOT" "$current_batch" "$supervisor_state" "${RUN_IDS[@]}" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_file = Path(sys.argv[1])
root = Path(sys.argv[2])
current_batch = sys.argv[3]
supervisor_state = sys.argv[4]
run_ids = sys.argv[5:]

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

aggregate = {"completed": 0, "failed": 0, "skipped": 0, "running": 0, "pending": 0, "total": 0}
batches = []
for run_id in run_ids:
    batch_path = root / run_id / "batch_status.json"
    payload = {"run_id": run_id, "exists": batch_path.exists(), "status": "missing", "summary": {}}
    if batch_path.exists():
        data = json.loads(batch_path.read_text(encoding="utf-8"))
        payload["status"] = data.get("status", "unknown")
        payload["summary"] = data.get("summary", {})
        for key in aggregate:
            aggregate[key] += int(payload["summary"].get(key, "0") or 0)
    batches.append(payload)

status_file.write_text(
    json.dumps(
        {
            "attempt_id": "ATTEMPT-011",
            "campaign_id": "ATTEMPT-011-H76-MIXED200",
            "supervisor_state": supervisor_state,
            "current_batch": current_batch,
            "aggregate": aggregate,
            "batches": batches,
            "updated_at": utc_now(),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY
}

batch_finished() {
  local run_id="$1"
  python3 - "$ROOT/$run_id/batch_status.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    raise SystemExit(1)
data = json.loads(path.read_text(encoding="utf-8"))
status = data.get("status", "")
raise SystemExit(0 if status in {"completed", "completed_with_failures", "completed_with_skips"} else 1)
PY
}

for run_id in "${RUN_IDS[@]}"; do
  if [[ -f "$GLOBAL_STOP_FILE" ]]; then
    write_status "$run_id" "stopped_before_start_next_batch"
    exit 0
  fi
  write_status "$run_id" "starting_batch"
  cd "$ROOT/$run_id"
  bash start_batch.sh
  write_status "$run_id" "running_batch"
  while ! batch_finished "$run_id"; do
    if [[ -f "$GLOBAL_STOP_FILE" && ! -f "$ROOT/$run_id/STOP_REQUESTED" ]]; then
      touch "$ROOT/$run_id/STOP_REQUESTED"
    fi
    write_status "$run_id" "running_batch"
    sleep 60
  done
  write_status "$run_id" "batch_finished"
done

write_status "none" "completed"
