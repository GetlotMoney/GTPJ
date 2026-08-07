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
import tempfile
import threading
import time

import yaml


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
LAUNCH_MANIFEST_SCHEMA = "gtpj.v5_ablation_001.launch.v2"
KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
REVIEW_PACK = Path("docs/agent_reviews/2026-08-07-v5-local-ablation")
TRUSTED_EVIDENCE_REFS = {
    "task_start_ref": EXPERIMENT_DIR / "TASK_START.yaml",
    "agent_runtime_ref": EXPERIMENT_DIR / "agent_runtime.yaml",
    "review_decision_ref": REVIEW_PACK / "10_final_decision.md",
    "parameter_matrix_ref": EXPERIMENT_DIR / "PARAMETER_MATRIX.csv",
    "experiment_binding_ref": EXPERIMENT_DIR / "EXPERIMENT.yaml",
}
LAUNCH_IDENTITY_VALUES = {
    "experiment_id": "V5-ABLATION-001",
    "workflow_mode": "server_frozen_runner",
    "experiment_branch": EXPERIMENT_BRANCH,
    "template_commit": TEMPLATE_COMMIT,
    "review_pack_ref": REVIEW_PACK.as_posix(),
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


def execution_id_for_commit(commit):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("冻结提交必须是 40 位小写 Git 提交号。")
    return f"V5-ABLATION-001-{commit[:12]}"


def ensure_supported_platform(
    *, platform_name=None, killpg_available=None, sigkill_available=None
):
    platform_name = os.name if platform_name is None else platform_name
    killpg_available = (
        hasattr(os, "killpg") if killpg_available is None else killpg_available
    )
    sigkill_available = (
        hasattr(signal, "SIGKILL")
        if sigkill_available is None
        else sigkill_available
    )
    if platform_name != "posix" or not killpg_available or not sigkill_available:
        raise RuntimeError(
            "正式服务器控制器只支持具备进程组与 SIGKILL 语义的 Linux。"
        )


def make_stop_signal_handler(stop_requested):
    def handle_stop(_signum, _frame):
        stop_requested.set()

    return handle_stop


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
    expected_values = {
        **LAUNCH_IDENTITY_VALUES,
        "execution_id": execution_id_for_commit(expected_commit),
        "pre_run_freeze_commit": expected_commit,
    }
    for field, expected in expected_values.items():
        if payload.get(field) != expected:
            raise ValueError(f"启动许可清单 {field} 不正确，拒绝正式训练。")
    for field, expected_path in TRUSTED_EVIDENCE_REFS.items():
        if payload.get(field) != expected_path.as_posix():
            raise ValueError(f"启动许可清单 {field} 不正确，拒绝正式训练。")
        digest_field = field.replace("_ref", "_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get(digest_field, ""))):
            raise ValueError(f"启动许可清单 {digest_field} 不是有效 SHA-256。")
    run_ids = payload.get("run_ids")
    expected_jobs = set(sum((list(items) for items in GROUP_JOBS.values()), []))
    if not isinstance(run_ids, dict) or set(run_ids) != expected_jobs:
        raise ValueError("启动许可清单 run_ids 必须与六个冻结 job_id 完全一致。")
    values = list(run_ids.values())
    if len(set(values)) != len(values) or any(
        not isinstance(item, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", item)
        for item in values
    ):
        raise ValueError("启动许可清单 run_ids 必须非空、唯一且只含安全字符。")
    return payload, hashlib.sha256(raw).hexdigest()


class RunGate:
    """把失败/停止标志与下一项任务的启动检查放在同一把锁里。"""

    def __init__(self):
        self.lock = threading.Lock()
        self.blocked = False

    def claim_start(self):
        with self.lock:
            return not self.blocked

    def launch_if_allowed(self, launch, *, should_block=None):
        with self.lock:
            if self.blocked or (should_block is not None and should_block()):
                return None
            return launch()

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


def finish_receipt_path(receipt):
    receipt = Path(receipt)
    return receipt.with_name(f"{receipt.stem}.finish.json")


def validate_finish_receipt(
    receipt, training_log, command, job_id, run_id, return_code
):
    receipt = Path(receipt)
    training_log = Path(training_log)
    finish = finish_receipt_path(receipt)
    if not receipt.is_file():
        raise RuntimeError("缺少 run start receipt。")
    if not training_log.is_file():
        raise RuntimeError("缺少训练日志，无法核对 run finish receipt。")
    if not finish.is_file():
        raise RuntimeError("缺少 run finish receipt。")
    try:
        payload = json.loads(finish.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("run finish receipt 不是有效 UTF-8 JSON。") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("run finish receipt 顶层必须是对象。")
    expected = {
        "schema_version": "gtpj-run-finish-receipt/v1",
        "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
        "job_id": job_id,
        "run_id": run_id,
        "run_start_receipt_sha256": _sha256_file(receipt),
        "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        "returncode": int(return_code),
        "log_sha256": _sha256_file(training_log),
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            raise RuntimeError(f"run finish receipt 的 {field} 与本次进程不一致。")
    if not isinstance(payload.get("pid"), int) or payload["pid"] <= 0:
        raise RuntimeError("run finish receipt 的 pid 无效。")
    for field in ("started_at", "finished_at"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise RuntimeError(f"run finish receipt 的 {field} 无效。")
    return payload


def cleanup_process_tree(*, helper_process, training_log, receipt):
    """无论上游哪一步异常，都尽力终止并回收训练/helper 进程。"""

    outcome = {
        "training_pid": None,
        "training_termination": None,
        "helper_termination": None,
        "cleanup_complete": True,
        "process_evidence_state": "helper_already_exited",
        "errors": [],
    }
    if helper_process is not None and helper_process.poll() is None:
        try:
            outcome["training_pid"] = training_pid_from_log(training_log)
        except Exception as exc:
            outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        if outcome["training_pid"] is not None:
            outcome["process_evidence_state"] = "training_pid_observed"
            try:
                outcome["training_termination"] = terminate_training_process(
                    training_pid=outcome["training_pid"],
                    helper_process=helper_process,
                )
            except Exception as exc:
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        else:
            outcome["process_evidence_state"] = "incomplete_before_training_pid"
        if helper_process.poll() is None:
            try:
                outcome["helper_termination"] = _terminate_helper_group(helper_process)
            except Exception as exc:
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        outcome["cleanup_complete"] = helper_process.poll() is not None
        if outcome["cleanup_complete"]:
            try:
                helper_process.wait(timeout=0)
            except (subprocess.TimeoutExpired, TypeError) as exc:
                outcome["cleanup_complete"] = False
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        if outcome["errors"]:
            outcome["process_evidence_state"] = "incomplete_cleanup_error"
        elif outcome["training_pid"] is not None and outcome["cleanup_complete"]:
            outcome["process_evidence_state"] = "process_tree_stopped"
    finish_receipt = finish_receipt_path(receipt)
    outcome["finish_receipt"] = str(finish_receipt)
    outcome["receipt_state"] = (
        "sealed" if finish_receipt.is_file() else "incomplete_missing_finish_receipt"
    )
    return outcome


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


def _sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_yaml_mapping(path, label):
    try:
        value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{label} 不是可读取的 UTF-8 YAML。") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} 顶层必须是对象。")
    return value


def _verify_task_start_gate(path):
    task_start = _read_yaml_mapping(path, "TASK_START.yaml")
    for field in ("formal_runner_allowed", "formal_evidence_allowed"):
        if task_start.get(field) is not True:
            raise ValueError(f"TASK_START.yaml 的 {field} 未通过。")
    expected_hard_gates = {
        "code_review": "strict-3 pass",
        "agent_runtime": "pass",
        "artifact_boundary": "pass",
        "pre_run_freeze_commit": "pass",
    }
    hard_gates = task_start.get("hard_gates")
    if not isinstance(hard_gates, dict):
        raise ValueError("TASK_START.yaml 缺少 hard_gates。")
    for field, expected in expected_hard_gates.items():
        if hard_gates.get(field) != expected:
            raise ValueError(f"TASK_START.yaml hard_gates.{field} 未通过。")


def _read_frozen_run_ids(matrix_path):
    with Path(matrix_path).open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected_jobs = set(sum((list(items) for items in GROUP_JOBS.values()), []))
    by_job = {row.get("job_id"): row for row in rows}
    if set(by_job) != expected_jobs or len(rows) != len(expected_jobs):
        raise ValueError("冻结参数矩阵必须恰好包含六个指定 job_id。")
    run_ids = {}
    for job_id in sorted(expected_jobs):
        row = by_job[job_id]
        run_id = row.get("run_id", "")
        if row.get("status") != "frozen" or not run_id:
            raise ValueError(f"冻结参数矩阵 {job_id} 尚未 ready/frozen。")
        run_ids[job_id] = run_id
    if len(set(run_ids.values())) != len(run_ids):
        raise ValueError("冻结参数矩阵 run_id 必须唯一。")
    return run_ids


def verify_frozen_launch_evidence(bundle, python, manifest, expected_commit):
    """从 Git bundle 自身重建受信证据，不相信外部清单里的通过布尔值。"""

    bundle = Path(bundle).resolve()
    python = Path(python).resolve()
    if not bundle.is_file():
        raise FileNotFoundError(f"Git bundle 不存在：{bundle}")
    if not python.is_file():
        raise FileNotFoundError(f"Python 不存在：{python}")
    with tempfile.TemporaryDirectory(prefix="gtpj-v5-abl001-verify-") as directory:
        root = Path(directory)
        bare_repo = root / "objects.git"
        checkout = root / "checkout"
        run_checked(["git", "init", "--bare", str(bare_repo)])
        run_checked(["git", "bundle", "verify", str(bundle)], cwd=bare_repo)
        heads = run_checked(
            ["git", "bundle", "list-heads", str(bundle)], cwd=bare_repo
        ).stdout.splitlines()
        refs = {}
        for line in heads:
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                refs[parts[1]] = parts[0]
        branch_ref = f"refs/heads/{EXPERIMENT_BRANCH}"
        if refs.get(branch_ref) != expected_commit:
            raise ValueError(
                "Git bundle 中实验分支没有准确指向 pre_run_freeze_commit。"
            )
        run_checked(["git", "bundle", "unbundle", str(bundle)], cwd=bare_repo)
        resolved = run_checked(
            ["git", "rev-parse", f"{expected_commit}^{{commit}}"], cwd=bare_repo
        ).stdout.strip()
        if resolved != expected_commit:
            raise ValueError("Git bundle 无法解析准确的 pre_run_freeze_commit。")
        run_checked(
            ["git", "cat-file", "-e", f"{TEMPLATE_COMMIT}^{{commit}}"],
            cwd=bare_repo,
        )
        checkout.mkdir()
        run_checked(
            [
                "git",
                f"--git-dir={bare_repo}",
                f"--work-tree={checkout}",
                "checkout",
                "--force",
                expected_commit,
                "--",
                ".",
            ]
        )

        for ref_field, relative_path in TRUSTED_EVIDENCE_REFS.items():
            evidence_path = checkout / relative_path
            digest_field = ref_field.replace("_ref", "_sha256")
            if not evidence_path.is_file():
                raise FileNotFoundError(f"冻结提交缺少受信证据：{relative_path.as_posix()}")
            actual_digest = _sha256_file(evidence_path)
            if manifest.get(digest_field) != actual_digest:
                raise ValueError(
                    f"启动许可清单 {digest_field} 与冻结提交中的文件不一致。"
                )

        _verify_task_start_gate(checkout / TRUSTED_EVIDENCE_REFS["task_start_ref"])
        matrix = checkout / TRUSTED_EVIDENCE_REFS["parameter_matrix_ref"]
        run_ids = _read_frozen_run_ids(matrix)
        if manifest.get("run_ids") != run_ids:
            raise ValueError("启动许可清单 run_ids 与冻结参数矩阵不一致。")

        workflow = checkout / "workflow/gtpj_workflow.py"
        commands = [
            [python, workflow, "validate-ai-cross-review", "--path", checkout / REVIEW_PACK],
            [python, workflow, "validate-agent-runtime", "--path", checkout / EXPERIMENT_DIR / "agent_runtime.yaml"],
            [python, workflow, "validate-parameter-matrix", "--path", matrix, "--expected-jobs", "6", "--require-ready"],
            [python, workflow, "validate-experiment-base", "--path", checkout / EXPERIMENT_DIR],
            [python, workflow, "validate"],
            [python, workflow, "validate-workflow-consistency"],
            [python, workflow, "validate-framework-ledgers"],
            [python, workflow, "audit-boundary"],
        ]
        for command in commands:
            run_checked(command, cwd=checkout)
        return {
            "commit": expected_commit,
            "branch": EXPERIMENT_BRANCH,
            "template_commit": TEMPLATE_COMMIT,
            "run_ids": run_ids,
            "validated_command_count": len(commands),
        }


def validate_fresh_execution_roots(runtime_root, warehouse_root, expected_commit):
    runtime_root = Path(runtime_root).resolve()
    warehouse_root = Path(warehouse_root).resolve()
    expected_name = execution_id_for_commit(expected_commit)
    if runtime_root.name != expected_name:
        raise ValueError(f"runtime-root 必须以准确 execution_id 命名：{expected_name}")
    if warehouse_root.name != expected_name:
        raise ValueError(f"warehouse-root 必须以准确 execution_id 命名：{expected_name}")
    if runtime_root == warehouse_root:
        raise ValueError("runtime-root 与 warehouse-root 不能是同一路径。")
    if runtime_root.exists():
        raise FileExistsError(f"runtime-root 已存在，拒绝复用：{runtime_root}")
    if warehouse_root.exists():
        raise FileExistsError(f"warehouse-root 已存在，拒绝复用：{warehouse_root}")
    return runtime_root, warehouse_root


def claim_execution_identity(
    claim_root,
    *,
    execution_id,
    commit,
    run_ids,
    runtime_root,
    warehouse_root,
):
    """在服务器持久目录中一次性领取 execution_id 和全部 run_id。"""

    if execution_id != execution_id_for_commit(commit):
        raise ValueError("execution_id 与冻结提交不一致。")
    if not isinstance(run_ids, dict) or not run_ids:
        raise ValueError("run_ids 必须是非空对象。")
    claim_root = Path(claim_root).resolve()
    claim_root.mkdir(parents=True, exist_ok=True)
    lock_path = claim_root / ".claims.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_stream:
        fcntl_module = None
        try:
            import fcntl as fcntl_module
        except ImportError:
            # 正式 main 已阻断非 Linux；此分支只方便本地只读单元测试。
            pass
        if fcntl_module is not None:
            fcntl_module.flock(lock_stream.fileno(), fcntl_module.LOCK_EX)
        try:
            used_run_ids = set()
            for path in claim_root.glob("*.json"):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"无法读取已有执行领取记录：{path}") from exc
                if payload.get("execution_id") == execution_id:
                    raise FileExistsError(f"execution_id 已领取：{execution_id}")
                existing = payload.get("run_ids", {})
                if isinstance(existing, dict):
                    used_run_ids.update(existing.values())
            duplicate_run_ids = sorted(set(run_ids.values()) & used_run_ids)
            if duplicate_run_ids:
                raise FileExistsError(
                    f"run_id 已领取，恢复必须新建身份：{duplicate_run_ids}"
                )
            claim_path = claim_root / f"{execution_id}.json"
            payload = {
                "schema_version": "gtpj.v5_ablation_001.execution_claim.v1",
                "execution_id": execution_id,
                "commit": commit,
                "run_ids": run_ids,
                "runtime_root": str(Path(runtime_root).resolve()),
                "warehouse_root": str(Path(warehouse_root).resolve()),
                "claimed_at_epoch": time.time(),
            }
            with claim_path.open("x", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            return claim_path
        finally:
            if fcntl_module is not None:
                fcntl_module.flock(lock_stream.fileno(), fcntl_module.LOCK_UN)


def verify_server_gpu_preflight():
    inventory = run_checked(
        ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader,nounits"]
    ).stdout.splitlines()
    indexes = {line.strip() for line in inventory if line.strip()}
    if not {"0", "1"}.issubset(indexes):
        raise RuntimeError("服务器必须能看到 GPU 0 和 GPU 1。")
    applications = run_checked(
        [
            "nvidia-smi",
            "--query-compute-apps=pid",
            "--format=csv,noheader,nounits",
        ]
    ).stdout.splitlines()
    active_pids = sorted({line.strip() for line in applications if line.strip().isdigit()})
    if active_pids:
        raise RuntimeError(
            f"服务器仍有 GPU 计算进程，拒绝抢占：{', '.join(active_pids)}"
        )
    return {"gpu_indexes": sorted(indexes), "active_compute_pids": []}


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

    runtime_root.mkdir(parents=True, exist_ok=False)
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
    if stop_file.exists() or stop_requested.is_set():
        status.update_job(job_id, status="not_started_after_stop_or_failure")
        return None
    job_dir = warehouse_root / job_id
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
    process = None
    return_code = None
    stopped_by_request = False
    caught = None
    cleanup = None

    def launch_helper():
        job_dir.mkdir(parents=True, exist_ok=False)
        with helper_log.open("xb") as stream:
            return subprocess.Popen(
                helper_args,
                cwd=str(ledger_root),
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

    try:
        process = run_gate.launch_if_allowed(
            launch_helper,
            should_block=lambda: stop_file.exists() or stop_requested.is_set(),
        )
        if process is None:
            status.update_job(job_id, status="not_started_after_stop_or_failure")
            return None
        status.update_job(
            job_id,
            status="running",
            helper_pid=process.pid,
            helper_process_group_id=process.pid,
        )
        while process.poll() is None:
            if stop_file.exists() or stop_requested.is_set():
                run_gate.request_stop()
                stop_requested.set()
                stop_file.touch(exist_ok=True)
                status.update_job(job_id, status="stopping")
                stopped_by_request = True
                cleanup = cleanup_process_tree(
                    helper_process=process,
                    training_log=training_log,
                    receipt=receipt,
                )
                break
            time.sleep(1)
        if process.poll() is None:
            raise RuntimeError("停止后 helper 进程仍存活。")
        return_code = process.wait()
    except BaseException as exc:
        caught = exc
        run_gate.mark_failure()
    finally:
        if process is not None and (cleanup is None or process.poll() is None):
            cleanup = cleanup_process_tree(
                helper_process=process,
                training_log=training_log,
                receipt=receipt,
            )
        if cleanup is not None:
            if process is not None and return_code is not None:
                try:
                    validate_finish_receipt(
                        receipt,
                        training_log,
                        command,
                        job_id,
                        frozen_run_id,
                        return_code,
                    )
                    cleanup["receipt_state"] = "verified"
                except RuntimeError as exc:
                    cleanup["receipt_state"] = "incomplete_invalid_finish_receipt"
                    cleanup.setdefault("errors", []).append(
                        f"{type(exc).__name__}: {exc}"
                    )
                    if not stopped_by_request and caught is None:
                        caught = exc
            cleanup_values = {
                "training_pid": cleanup.get("training_pid"),
                "training_termination": cleanup.get("training_termination"),
                "helper_termination": cleanup.get("helper_termination"),
                "cleanup_complete": cleanup.get("cleanup_complete"),
                "cleanup_errors": cleanup.get("errors", []),
                "finish_receipt": cleanup.get("finish_receipt"),
                "process_evidence_state": cleanup.get("process_evidence_state"),
                "finish_receipt_state": cleanup.get("receipt_state"),
            }
            try:
                status.update_job(job_id, **cleanup_values)
            except BaseException as exc:
                if caught is None:
                    caught = exc
            if not cleanup.get("cleanup_complete") and caught is None:
                caught = RuntimeError("helper 进程树清理不完整，正式证据阻断。")
            if (
                not stopped_by_request
                and return_code == 0
                and cleanup.get("receipt_state") != "verified"
                and caught is None
            ):
                caught = RuntimeError("训练返回成功但缺少 finish receipt，正式证据阻断。")
    if caught is not None:
        raise caught
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
    ensure_supported_platform()
    stop_requested = threading.Event()
    stop_handler = make_stop_signal_handler(stop_requested)
    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)
    launch_manifest, launch_manifest_sha256 = validate_launch_manifest(
        args.launch_manifest, args.commit
    )
    evidence_verification = verify_frozen_launch_evidence(
        args.bundle, args.python, launch_manifest, args.commit
    )
    if stop_requested.is_set():
        raise RuntimeError("收到停止信号，拒绝领取正式运行身份。")
    if not args.data_source.resolve().is_dir():
        raise FileNotFoundError(f"数据目录不存在：{args.data_source.resolve()}")
    gpu_preflight = verify_server_gpu_preflight()
    runtime_root, warehouse_root = validate_fresh_execution_roots(
        args.runtime_root, args.warehouse_root, args.commit
    )
    claim_path = claim_execution_identity(
        warehouse_root.parent / ".gtpj_execution_claims",
        execution_id=launch_manifest["execution_id"],
        commit=args.commit,
        run_ids=launch_manifest["run_ids"],
        runtime_root=runtime_root,
        warehouse_root=warehouse_root,
    )
    if stop_requested.is_set():
        raise RuntimeError("收到停止信号；运行身份已领取但不会创建训练副本。")
    runtime_root, warehouse_root, code_roots, code_commits, ledger_roots = prepare_layout(args)
    stop_file = runtime_root / "STOP"
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
        "evidence_verification": evidence_verification,
        "gpu_preflight": gpu_preflight,
        "execution_claim": str(claim_path),
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
    run_gate = RunGate()
    if stop_requested.is_set():
        run_gate.request_stop()
        stop_file.touch(exist_ok=True)
        status.set_controller(status="stopping", stop_requested_at_epoch=time.time())

    def worker(group):
        for job_id in GROUP_JOBS[group]:
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

    if stop_requested.is_set():
        stop_file.touch(exist_ok=True)
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
