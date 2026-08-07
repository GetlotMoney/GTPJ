"""V5-ABLATION-001 的服务器双 GPU 后台队列控制器。"""

import argparse
import csv
import json
import os
from pathlib import Path
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


def parse_args():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--warehouse-root", type=Path, required=True)
    parser.add_argument("--data-source", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    return parser.parse_args()


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
    status,
):
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
        status.update_job(job_id, status="running", helper_pid=process.pid)
        while process.poll() is None:
            if stop_file.exists():
                os.killpg(process.pid, signal.SIGTERM)
                status.update_job(job_id, status="stopping")
                break
            time.sleep(5)
        return_code = process.wait()
    status.update_job(
        job_id,
        status="completed" if return_code == 0 else "failed",
        return_code=return_code,
        finished_at_epoch=time.time(),
    )
    return return_code


def main():
    args = parse_args()
    runtime_root, warehouse_root, code_roots, code_commits, ledger_roots = prepare_layout(args)
    stop_file = runtime_root / "STOP"
    controller_pid = runtime_root / "controller.pid"
    controller_pid.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    initial = {
        "schema_version": "gtpj.v5_ablation_001.server_status.v1",
        "experiment_id": "V5-ABLATION-001",
        "commit": args.commit,
        "code_commits": code_commits,
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
    abort_after_current = threading.Event()

    def worker(group):
        for job_id in GROUP_JOBS[group]:
            if stop_file.exists() or abort_after_current.is_set():
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
                    status=status,
                )
            except Exception as exc:
                status.update_job(
                    job_id,
                    status="failed",
                    controller_error=f"{type(exc).__name__}: {exc}",
                )
                code = 1
            if code != 0:
                abort_after_current.set()

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
    raise SystemExit(0 if final_status == "completed" else 1)


if __name__ == "__main__":
    main()
