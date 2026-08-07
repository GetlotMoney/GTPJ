"""V5-ABLATION-001 的服务器双 GPU 后台队列控制器。"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import threading
import time


EXPERIMENT_BRANCH = "exp/v5/ablation/ablation-001-local-branch-effect"
EXPERIMENT_DIR = Path(
    "experiments/v5/ablation/ABLATION-001_local_branch_effect"
)
GROUP_JOBS = {
    "FULL": ("RUN-001", "RUN-002", "RUN-003"),
    "GLOBAL_ONLY": ("RUN-004", "RUN-005", "RUN-006"),
}
WRAPPER = "tools/run_v5_ablation_001_training.py"
TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
LAUNCH_MANIFEST_SCHEMA = "gtpj.v5_ablation_001.launch.v1"
KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
LAUNCH_GATE_VALUES = {
    "experiment_id": "V5-ABLATION-001",
    "workflow_mode": "server_frozen_runner",
    "formal_runner_allowed": True,
    "codex_named_thread_pre_review": "pass",
    "codex_named_thread_archived": True,
    "ai_cross_review_validation": "pass",
    "machine_validation": "pass",
    "matrix_validation": "pass",
    "agent_runtime_validation": "pass",
    "server_preflight": "pass",
}


def parse_args():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--warehouse-root", type=Path, required=True)
    parser.add_argument("--data-source", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--launch-manifest", type=Path, required=True)
    return parser.parse_args()


def validate_launch_manifest(path, expected_commit):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"启动许可清单不存在：{path}")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise ValueError("--commit 必须是 40 位小写 Git 提交号。")
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("启动许可清单必须是 UTF-8 JSON 对象。") from exc
    if not isinstance(payload, dict):
        raise ValueError("启动许可清单顶层必须是对象。")
    if payload.get("schema_version") != LAUNCH_MANIFEST_SCHEMA:
        raise ValueError("启动许可清单 schema_version 不正确。")
    if payload.get("pre_run_freeze_commit") != expected_commit:
        raise ValueError("启动许可清单 pre_run_freeze_commit 与待运行提交不一致。")
    for field, expected in LAUNCH_GATE_VALUES.items():
        if payload.get(field) != expected:
            raise ValueError(f"启动许可清单 {field} 未通过，拒绝正式训练。")
    return payload, hashlib.sha256(raw).hexdigest()


class RunGate:
    """把失败/停止标志与下一项任务的启动检查放在同一把锁里。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.blocked = False

    def claim_start(self):
        with self.lock:
            return not self.blocked

    def mark_failure(self):
        with self.lock:
            self.blocked = True

    def request_stop(self):
        self.mark_failure()


def training_pid_from_log(log_path):
    log_path = Path(log_path)
    if not log_path.is_file():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(
        r"^GTPJ_TRAINING_PROCESS_STARTED .* pid=([1-9][0-9]*) started_at=\S+$",
        text,
        flags=re.MULTILINE,
    )
    unique = sorted(set(matches))
    if len(unique) > 1:
        raise RuntimeError("训练日志出现多个训练 PID，拒绝猜测应停止哪个进程。")
    return int(unique[0]) if unique else None


def _wait_for_helper(helper_process, timeout_seconds, poll_interval_seconds):
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        if helper_process.poll() is not None:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(max(0.0, float(poll_interval_seconds)))


def terminate_training_process(
    *,
    training_pid,
    helper_process,
    term_timeout_seconds=20,
    kill_timeout_seconds=5,
    poll_interval_seconds=0.2,
):
    """只先停止训练子进程，让账本 helper 有机会写完失败收据。"""

    try:
        os.kill(training_pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    if _wait_for_helper(helper_process, term_timeout_seconds, poll_interval_seconds):
        return "terminated"
    try:
        os.kill(training_pid, KILL_SIGNAL)
    except ProcessLookupError:
        pass
    if _wait_for_helper(helper_process, kill_timeout_seconds, poll_interval_seconds):
        return "killed"
    raise RuntimeError("训练进程在 SIGKILL 后仍未收口。")


def _wait_for_training_pid(log_path, helper_process, timeout_seconds=15):
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while helper_process.poll() is None:
        training_pid = training_pid_from_log(log_path)
        if training_pid is not None:
            return training_pid
        if time.monotonic() >= deadline:
            break
        time.sleep(0.2)
    return training_pid_from_log(log_path)


def _terminate_helper_group(helper_process, term_timeout_seconds=5, kill_timeout_seconds=5):
    """训练 PID 尚未写入日志时的最后兜底；此路径会标记证据不完整。"""

    try:
        os.killpg(helper_process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    if _wait_for_helper(helper_process, term_timeout_seconds, 0.2):
        return "helper_group_terminated"
    try:
        os.killpg(helper_process.pid, KILL_SIGNAL)
    except ProcessLookupError:
        pass
    if _wait_for_helper(helper_process, kill_timeout_seconds, 0.2):
        return "helper_group_killed"
    raise RuntimeError("helper 进程组在 SIGKILL 后仍未退出。")


def write_recovery_handoff(path, status_data):
    partial_states = {"starting", "running", "stopping", "stopped", "failed"}
    partial_jobs = sorted(
        job_id
        for job_id, values in status_data.get("jobs", {}).items()
        if values.get("status") in partial_states
    )
    payload = {
        "schema_version": "gtpj.v5_ablation_001.recovery_handoff.v1",
        "experiment_id": status_data.get("experiment_id", "V5-ABLATION-001"),
        "controller_status": status_data.get("status", "failed"),
        "automatic_resume_allowed": False,
        "partial_jobs": partial_jobs,
        "required_next_action": (
            "sync the stopped/failed receipts, then create a new frozen RUN row "
            "with repeat_of; never reuse this runtime or Warehouse directory"
        ),
        "jobs": status_data.get("jobs", {}),
    }
    path = Path(path)
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temp.replace(path)


def run_checked(command, *, cwd=None):
    return subprocess.run(
        [str(item) for item in command],
        cwd=None if cwd is None else str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


def clone_at(bundle, target, commit, *, bind_experiment_branch=False):
    if target.exists():
        raise FileExistsError(f"拒绝覆盖已有运行副本：{target}")
    run_checked(["git", "clone", "--quiet", str(bundle), str(target)])
    run_checked(["git", "checkout", "--detach", commit], cwd=target)
    if bind_experiment_branch:
        run_checked(["git", "branch", "-f", EXPERIMENT_BRANCH, commit], cwd=target)
    status = run_checked(["git", "status", "--porcelain"], cwd=target).stdout.strip()
    if status:
        raise RuntimeError(f"新建运行副本不干净：{target}")


def ensure_link(link, target):
    if link.exists() or link.is_symlink():
        raise FileExistsError(f"拒绝覆盖已有路径：{link}")
    link.symlink_to(target, target_is_directory=True)


def build_training_command(python, group, config, code_root, commit):
    tokens = [
        str(python),
        WRAPPER,
        "--config",
        str(config),
        "--code-root",
        str(code_root),
        "--commit",
        commit,
        "--group",
        group,
    ]
    return shlex.join(tokens)


class StatusStore:
    def __init__(self, path, initial):
        self.path = path
        self.data = initial
        self.lock = threading.Lock()
        self.write()

    def write(self):
        temp = self.path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp.replace(self.path)

    def update_job(self, job_id, **values):
        with self.lock:
            self.data["jobs"][job_id].update(values)
            self.data["updated_at_epoch"] = time.time()
            self.write()

    def set_controller(self, **values):
        with self.lock:
            self.data.update(values)
            self.data["updated_at_epoch"] = time.time()
            self.write()


def prepare_layout(args):
    runtime_root = args.runtime_root.resolve()
    warehouse_root = args.warehouse_root.resolve()
    bundle = args.bundle.resolve()
    data_source = args.data_source.resolve()
    python = args.python.resolve()
    for path, label in (
        (bundle, "Git bundle"),
        (data_source, "数据目录"),
        (python, "Python"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} 不存在：{path}")

    runtime_root.mkdir(parents=True, exist_ok=True)
    warehouse_root.mkdir(parents=True, exist_ok=False)
    code_roots = {
        "FULL": runtime_root / "code_FULL",
        "GLOBAL_ONLY": runtime_root / "code_GLOBAL_ONLY",
    }
    code_commits = {"FULL": TEMPLATE_COMMIT, "GLOBAL_ONLY": args.commit}
    for group, code_root in code_roots.items():
        clone_at(bundle, code_root, code_commits[group])
        group_warehouse = warehouse_root / group
        (group_warehouse / "train_log").mkdir(parents=True)
        ensure_link(code_root / "data", data_source)
        ensure_link(code_root / "train_log", group_warehouse / "train_log")

    ledger_roots = {}
    for job_id in sum((list(items) for items in GROUP_JOBS.values()), []):
        ledger = runtime_root / f"ledger_{job_id}"
        clone_at(bundle, ledger, args.commit, bind_experiment_branch=True)
        ledger_roots[job_id] = ledger
    return runtime_root, warehouse_root, code_roots, code_commits, ledger_roots


def run_job(
    *,
    args,
    group,
    job_id,
    code_root,
    ledger_root,
    warehouse_root,
    stop_file,
    stop_requested,
    run_gate,
    status,
):
    if stop_file.exists() or stop_requested.is_set() or not run_gate.claim_start():
        status.update_job(job_id, status="not_started_after_stop_or_failure")
        return None
    job_dir = warehouse_root / job_id
    job_dir.mkdir(parents=True, exist_ok=False)
    config = ledger_root / EXPERIMENT_DIR / "configs" / f"{job_id}.yaml"
    matrix = ledger_root / EXPERIMENT_DIR / "PARAMETER_MATRIX.csv"
    receipt = job_dir / "run_start_receipt.json"
    training_log = job_dir / "training.log"
    helper_log = job_dir / "helper.log"
    with matrix.open("r", encoding="utf-8", newline="") as stream:
        matches = [row for row in csv.DictReader(stream) if row["job_id"] == job_id]
    if len(matches) != 1 or not matches[0]["run_id"]:
        raise RuntimeError(f"{job_id} 没有唯一且非空的冻结 run_id。")
    frozen_run_id = matches[0]["run_id"]
    code_commit = TEMPLATE_COMMIT if group == "FULL" else args.commit
    command = build_training_command(
        args.python.resolve(), group, config, code_root, code_commit
    )
    helper_args = [
        str(args.python.resolve()),
        "workflow/gtpj_workflow.py",
        "prepare-run-start-receipt",
        "--path",
        str(matrix),
        "--config",
        str(config),
        "--job-id",
        job_id,
        "--run-id",
        frozen_run_id,
        "--pre-run-freeze-commit",
        args.commit,
        "--command",
        command,
        "--receipt",
        str(receipt),
        "--log",
        str(training_log),
    ]
    status.update_job(
        job_id,
        status="starting",
        group=group,
        ledger=str(ledger_root),
        code_root=str(code_root),
        receipt=str(receipt),
        training_log=str(training_log),
    )
    with helper_log.open("wb") as stream:
        process = subprocess.Popen(
            helper_args,
            cwd=str(ledger_root),
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        status.update_job(
            job_id,
            status="running",
            helper_pid=process.pid,
            helper_process_group_id=process.pid,
        )
        stopped_by_request = False
        while process.poll() is None:
            if stop_file.exists() or stop_requested.is_set():
                run_gate.request_stop()
                stop_requested.set()
                status.update_job(job_id, status="stopping")
                training_pid = _wait_for_training_pid(training_log, process)
                if training_pid is None:
                    termination = _terminate_helper_group(process)
                    evidence_state = "incomplete_before_training_pid"
                else:
                    status.update_job(job_id, training_pid=training_pid)
                    termination = terminate_training_process(
                        training_pid=training_pid,
                        helper_process=process,
                    )
                    evidence_state = "helper_sealed_after_training_stop"
                status.update_job(
                    job_id,
                    termination=termination,
                    stop_evidence_state=evidence_state,
                )
                stopped_by_request = True
                break
            time.sleep(1)
        return_code = process.wait()
    if return_code != 0:
        run_gate.mark_failure()
    status.update_job(
        job_id,
        status=(
            "stopped"
            if stopped_by_request
            else "completed" if return_code == 0 else "failed"
        ),
        return_code=return_code,
        finished_at_epoch=time.time(),
    )
    return return_code


def main():
    args = parse_args()
    launch_manifest, launch_manifest_sha256 = validate_launch_manifest(
        args.launch_manifest, args.commit
    )
    runtime_root, warehouse_root, code_roots, code_commits, ledger_roots = prepare_layout(args)
    stop_file = runtime_root / "STOP"
    if stop_file.exists():
        raise RuntimeError(f"运行目录已有 STOP 文件，拒绝启动：{stop_file}")
    controller_pid = runtime_root / "controller.pid"
    controller_pid.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    initial = {
        "schema_version": "gtpj.v5_ablation_001.server_status.v1",
        "experiment_id": "V5-ABLATION-001",
        "commit": args.commit,
        "code_commits": code_commits,
        "launch_manifest": str(args.launch_manifest.resolve()),
        "launch_manifest_sha256": launch_manifest_sha256,
        "launch_gate": launch_manifest,
        "controller_pid": os.getpid(),
        "status": "running",
        "stop_file": str(stop_file),
        "jobs": {
            job_id: {"status": "pending", "group": group}
            for group, jobs in GROUP_JOBS.items()
            for job_id in jobs
        },
    }
    status = StatusStore(runtime_root / "status.json", initial)
    stop_requested = threading.Event()
    run_gate = RunGate()

    def handle_stop(signum, _frame):
        run_gate.request_stop()
        stop_requested.set()
        stop_file.touch(exist_ok=True)
        status.set_controller(
            status="stopping",
            stop_signal=int(signum),
            stop_requested_at_epoch=time.time(),
        )

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    def worker(group):
        for job_id in GROUP_JOBS[group]:
            if stop_file.exists() or stop_requested.is_set() or not run_gate.claim_start():
                status.update_job(job_id, status="not_started_after_stop_or_failure")
                continue
            try:
                code = run_job(
                    args=args,
                    group=group,
                    job_id=job_id,
                    code_root=code_roots[group],
                    ledger_root=ledger_roots[job_id],
                    warehouse_root=warehouse_root,
                    stop_file=stop_file,
                    stop_requested=stop_requested,
                    run_gate=run_gate,
                    status=status,
                )
            except Exception as exc:
                status.update_job(
                    job_id,
                    status="failed",
                    controller_error=f"{type(exc).__name__}: {exc}",
                )
                code = 1
                run_gate.mark_failure()
            if code not in {None, 0}:
                run_gate.mark_failure()

    threads = [threading.Thread(target=worker, args=(group,)) for group in GROUP_JOBS]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_states = {item["status"] for item in status.data["jobs"].values()}
    if final_states == {"completed"}:
        final_status = "completed"
    elif stop_file.exists():
        final_status = "stopped"
    else:
        final_status = "failed"
    status.set_controller(status=final_status, finished_at_epoch=time.time())
    if final_status != "completed":
        write_recovery_handoff(
            runtime_root / "recovery_handoff.json", status.data
        )
    raise SystemExit(0 if final_status == "completed" else 1)


if __name__ == "__main__":
    main()
