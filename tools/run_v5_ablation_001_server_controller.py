"""V5-ABLATION-001 的服务器双 GPU 后台队列控制器。"""

import argparse
import atexit
import ctypes
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
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
BOUND_RUNTIME_WORKFLOW_BLOB = "d387f75ae987572ef0bb8a8c9f68859be2e55ecc"
LAUNCH_MANIFEST_SCHEMA = "gtpj.v5_ablation_001.launch.v3"
KILL_SIGNAL = getattr(signal, "SIGKILL", signal.SIGTERM)
SERVER_PYTHON = Path("/data/lby/.conda/envs/dvsr_gpu/bin/python")
SERVER_DATA_SOURCE = Path("/data/lby/projects/cv_project/GTPJ/data")
DATA_MANIFEST_SCHEMA = "gtpj.v5_ablation_001.data_manifest.v1"
BOUND_PYTHON_EXEC_ENV = "GTPJ_BOUND_PYTHON_EXEC"
BOUND_PYTHON_ARGV0_ENV = "GTPJ_BOUND_PYTHON_ARGV0"
V5_REQUIRED_DATA_FILES = {
    "xlsa17_res101": "xlsa17/data/CUB/res101.mat",
    "xlsa17_att_splits": "xlsa17/data/CUB/att_splits.mat",
    "train_cls": "cache/CUB_train_features.pt",
    "train_patches": "cache/CUB_train_patch_features.pt",
    "train_labels": "cache/CUB_train_labels.pt",
    "gpt55_sentences": "cache/CUB_gpt55_sentence_embeds.pt",
    "test_seen_cls": "cache/CUB_test_seen_features.pt",
    "test_seen_labels": "cache/CUB_test_seen_labels.pt",
    "test_seen_patches": "cache/CUB_test_seen_patch_features.pt",
    "test_unseen_cls": "cache/CUB_test_unseen_features.pt",
    "test_unseen_labels": "cache/CUB_test_unseen_labels.pt",
    "test_unseen_patches": "cache/CUB_test_unseen_patch_features.pt",
}
DATA_CONTRACT_VALUES = {
    "dataset": "CUB",
    "split_contract": "xlsa17_standard_trainval_test_seen_test_unseen",
    "label_contract": "zero_based_cache_labels_equal_xlsa17_labels",
    "class_order_contract": "sorted_seen_and_unseen_ids_from_xlsa17",
    "metric_contract": "GZSL_U_S_H_and_conventional_ZS",
}
SERVER_RUNTIME_BASE = Path("/data/lby/projects/cv_project/GTPJ/.runtime/ablation")
SERVER_WAREHOUSE_BASE = Path(
    "/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/ablation"
)
SERVER_CLAIM_ROOT = SERVER_WAREHOUSE_BASE / ".gtpj_execution_claims"
REVIEW_PACK = Path("docs/agent_reviews/2026-08-07-v5-local-ablation")
TRUSTED_EVIDENCE_REFS = {
    "task_start_ref": EXPERIMENT_DIR / "TASK_START.yaml",
    "agent_runtime_ref": EXPERIMENT_DIR / "agent_runtime.yaml",
    "review_decision_ref": REVIEW_PACK / "10_final_decision.md",
    "parameter_matrix_ref": EXPERIMENT_DIR / "PARAMETER_MATRIX.csv",
    "experiment_binding_ref": EXPERIMENT_DIR / "EXPERIMENT.yaml",
    "data_manifest_ref": EXPERIMENT_DIR / "DATA_MANIFEST.json",
}
LAUNCH_IDENTITY_VALUES = {
    "experiment_id": "V5-ABLATION-001",
    "workflow_mode": "server_frozen_runner",
    "experiment_branch": EXPERIMENT_BRANCH,
    "template_commit": TEMPLATE_COMMIT,
    "review_pack_ref": REVIEW_PACK.as_posix(),
}
VALIDATION_LOCAL_BRANCH_REFS = {
    "main": "refs/heads/main",
    "framework/v1": "refs/heads/framework/v1",
    "framework/v2": "refs/heads/framework/v2",
    "framework/v3": "refs/heads/framework/v3",
    "framework/v5": "refs/heads/framework/v5",
    "framework/v5-template-v1": "refs/heads/framework/v5-template-v1",
}
VALIDATION_REQUIRED_TAG_REFS = (
    "refs/tags/v1",
    "refs/tags/v2",
    "refs/tags/v3",
    "refs/tags/v4",
    "refs/tags/v5",
    "refs/tags/model/v5-template-v1",
)


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
    *,
    platform_name=None,
    killpg_available=None,
    sigkill_available=None,
    pidfd_open_available=None,
    pidfd_signal_available=None,
):
    platform_name = sys.platform if platform_name is None else platform_name
    killpg_available = (
        hasattr(os, "killpg") if killpg_available is None else killpg_available
    )
    sigkill_available = (
        hasattr(signal, "SIGKILL")
        if sigkill_available is None
        else sigkill_available
    )
    pidfd_open_available = (
        _probe_pidfd_support()
        if pidfd_open_available is None
        else pidfd_open_available
    )
    pidfd_signal_available = (
        pidfd_open_available
        if pidfd_signal_available is None
        else pidfd_signal_available
    )
    if (
        platform_name != "linux"
        or not killpg_available
        or not sigkill_available
        or not pidfd_open_available
        or not pidfd_signal_available
    ):
        raise RuntimeError(
            "正式服务器控制器只支持具备进程组、pidfd 与 SIGKILL 语义的 Linux。"
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
    if payload.get("python_ref") != SERVER_PYTHON.as_posix():
        raise ValueError("启动许可清单 python_ref 不是固定服务器 Python。")
    if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("python_sha256", ""))):
        raise ValueError("启动许可清单 python_sha256 不是有效 SHA-256。")
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


def verify_python_runtime(python, manifest, *, expected_identity=None):
    """固定正式 Python 的路径、内容和文件身份，拒绝运行期替换。"""

    python = Path(os.path.abspath(os.fspath(python)))
    if python != SERVER_PYTHON:
        raise ValueError(f"--python 必须是固定服务器路径：{SERVER_PYTHON}")
    if manifest.get("python_ref") != SERVER_PYTHON.as_posix():
        raise ValueError("启动许可清单 python_ref 与固定服务器路径不一致。")
    if not python.is_file():
        raise FileNotFoundError(f"固定服务器 Python 不存在：{python}")
    digest = _sha256_file(python)
    if manifest.get("python_sha256") != digest:
        raise ValueError("固定服务器 Python 的 SHA-256 与启动许可清单不一致。")
    stat_result = python.stat()
    identity = {
        "path": python.as_posix(),
        "resolved_path": python.resolve(strict=True).as_posix(),
        "sha256": digest,
        "device": int(stat_result.st_dev),
        "inode": int(stat_result.st_ino),
        "size": int(stat_result.st_size),
        "mtime_ns": int(stat_result.st_mtime_ns),
    }
    if expected_identity is not None and identity != expected_identity:
        raise ValueError("固定服务器 Python 的文件身份在运行期间发生变化。")
    return identity


def _sha256_fd(fd):
    digest = hashlib.sha256()
    with os.fdopen(os.dup(fd), "rb", closefd=True) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bind_python_runtime(python, manifest):
    """打开并保持正式 Python；后续 exec 只走该文件描述符。"""

    identity = verify_python_runtime(python, manifest)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(identity["resolved_path"], flags)
    try:
        stat_result = os.fstat(fd)
        bound = {
            **identity,
            "device": int(stat_result.st_dev),
            "inode": int(stat_result.st_ino),
            "size": int(stat_result.st_size),
            "mtime_ns": int(stat_result.st_mtime_ns),
            "sha256": _sha256_fd(fd),
        }
        if bound != identity:
            raise ValueError("固定服务器 Python 在打开绑定时发生变化。")
        return {
            "fd": fd,
            "exec_ref": f"/proc/{os.getpid()}/fd/{fd}",
            "argv0": identity["path"],
            "identity": identity,
        }
    except BaseException:
        os.close(fd)
        raise


def _open_pidfd(pid):
    opener = getattr(os, "pidfd_open", None)
    if opener is not None:
        return opener(int(pid), 0)
    if sys.platform != "linux":
        return None
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(ctypes.c_long(434), ctypes.c_int(int(pid)), ctypes.c_uint(0))
    if result < 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))
    return int(result)


def _signal_pidfd(pidfd, signal_number):
    sender = getattr(signal, "pidfd_send_signal", None)
    if sender is not None:
        sender(int(pidfd), signal_number, None, 0)
        return
    if sys.platform != "linux":
        raise RuntimeError("当前平台缺少 pidfd_send_signal。")
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(
        ctypes.c_long(424),
        ctypes.c_int(int(pidfd)),
        ctypes.c_int(int(signal_number)),
        ctypes.c_void_p(),
        ctypes.c_uint(0),
    )
    if result < 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _close_pidfd(identity):
    if not isinstance(identity, dict):
        return
    pidfd = identity.get("pidfd")
    if isinstance(pidfd, int) and pidfd >= 0:
        try:
            os.close(pidfd)
        except OSError:
            pass
        identity["pidfd"] = None


def _close_fd_quietly(fd):
    try:
        os.close(fd)
    except OSError:
        pass


def _probe_pidfd_support():
    if sys.platform != "linux":
        return False
    pidfd = None
    try:
        pidfd = _open_pidfd(os.getpid())
        _signal_pidfd(pidfd, 0)
    except OSError:
        return False
    finally:
        if pidfd is not None:
            _close_fd_quietly(pidfd)
    return True


def _signal_bound_identity(identity, signal_number):
    pidfd = identity.get("pidfd")
    if isinstance(pidfd, int) and pidfd >= 0:
        try:
            _signal_pidfd(pidfd, signal_number)
        except ProcessLookupError:
            return False
        return True
    if sys.platform == "linux":
        raise RuntimeError("正式 Linux 进程缺少 pidfd，拒绝按裸 PID 发送信号。")
    try:
        os.kill(identity["pid"], signal_number)
    except ProcessLookupError:
        return False
    return True


class RunGate:
    """把失败/停止标志与下一项任务的启动检查放在同一把锁里。"""

    def __init__(self):
        self.lock = threading.RLock()
        self.blocked = False

    def claim_start(self):
        with self.lock:
            return not self.blocked

    def launch_if_allowed(self, launch, *, should_block=None):
        with self.lock:
            if self.blocked or (should_block is not None and should_block()):
                return None
            try:
                return launch()
            except BaseException:
                self.blocked = True
                raise

    def write_status_or_block(self, write):
        """状态写入与失败关闸必须是同一个不可穿插的动作。"""

        with self.lock:
            try:
                return write()
            except BaseException:
                self.blocked = True
                raise

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


def read_linux_process_identity(pid):
    """读取 Linux /proc 身份；start_time_ticks 用来阻断 PID 复用误杀。"""

    pid = int(pid)
    try:
        raw = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    close = raw.rfind(")")
    if close < 0:
        raise RuntimeError(f"/proc/{pid}/stat 格式无效。")
    tail = raw[close + 2 :].split()
    if len(tail) < 20:
        raise RuntimeError(f"/proc/{pid}/stat 字段不足。")
    return {
        "pid": pid,
        "state": tail[0],
        "ppid": int(tail[1]),
        "pgid": int(tail[2]),
        "sid": int(tail[3]),
        "start_time_ticks": int(tail[19]),
    }


def capture_helper_identity(helper_process):
    pidfd = _open_pidfd(helper_process.pid)
    try:
        identity = read_linux_process_identity(helper_process.pid)
        if identity is None:
            raise RuntimeError("helper 启动后未能固定 /proc 进程身份。")
        if identity["pgid"] != helper_process.pid or identity["sid"] != helper_process.pid:
            raise RuntimeError("helper 没有建立预期的独立进程组与会话。")
        identity["pidfd"] = pidfd
        return identity
    except BaseException:
        if pidfd is not None:
            os.close(pidfd)
        raise


def capture_training_identity(training_pid, helper_identity):
    """先打开 pidfd，再核对 /proc；信号永远发给已打开的进程对象。"""

    try:
        pidfd = _open_pidfd(training_pid)
    except ProcessLookupError:
        return None
    try:
        identity = read_linux_process_identity(training_pid)
        if identity is None:
            return None
        if (
            identity["pgid"] != helper_identity["pgid"]
            or identity["sid"] != helper_identity["sid"]
        ):
            raise RuntimeError("日志中的训练 PID 不属于本次 helper 进程组与会话。")
        identity["pidfd"] = pidfd
        pidfd = None
        return identity
    finally:
        if pidfd is not None:
            os.close(pidfd)


def _same_process_identity(actual, expected):
    keys = ("pid", "pgid", "sid", "start_time_ticks")
    return actual is not None and all(actual.get(key) == expected.get(key) for key in keys)


def process_group_members(helper_identity):
    """列出仍能运行的本次会话成员；僵尸进程不再持有训练资源。"""

    members = []
    proc_root = Path("/proc")
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            identity = read_linux_process_identity(int(entry.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError, RuntimeError):
            continue
        if (
            identity is not None
            and identity["state"] != "Z"
            and identity["pgid"] == helper_identity["pgid"]
            and identity["sid"] == helper_identity["sid"]
        ):
            members.append(identity)
    return sorted(members, key=lambda item: item["pid"])


def _assert_helper_group_not_reused(helper_identity):
    current = read_linux_process_identity(helper_identity["pid"])
    if current is not None and not _same_process_identity(current, helper_identity):
        raise RuntimeError("helper PID 已被复用，拒绝向不明进程组发送信号。")


def _wait_for_process_group_empty(helper_identity, timeout_seconds, poll_interval_seconds):
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        _assert_helper_group_not_reused(helper_identity)
        if not process_group_members(helper_identity):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(max(0.0, float(poll_interval_seconds)))


def _signal_bound_helper_group(helper_identity, signal_number):
    members = process_group_members(helper_identity)
    signalled = False
    for member in members:
        bound = capture_training_identity(member["pid"], helper_identity)
        if bound is None:
            continue
        try:
            signalled = _signal_bound_identity(bound, signal_number) or signalled
        finally:
            _close_pidfd(bound)
    return signalled


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
    training_identity,
    helper_process,
    helper_identity,
    term_timeout_seconds=20,
    kill_timeout_seconds=5,
    poll_interval_seconds=0.2,
):
    """先停受信训练 PID，再按固定进程组兜底，避免孤儿与 PID 复用。"""

    if (
        training_identity["pgid"] != helper_identity["pgid"]
        or training_identity["sid"] != helper_identity["sid"]
    ):
        raise RuntimeError("训练 PID 不属于本次 helper 进程组与会话。")
    _signal_bound_identity(training_identity, signal.SIGTERM)
    if _wait_for_process_group_empty(
        helper_identity, term_timeout_seconds, poll_interval_seconds
    ):
        if helper_process.poll() is not None:
            helper_process.wait(timeout=0)
        return "terminated"
    _signal_bound_helper_group(helper_identity, KILL_SIGNAL)
    if _wait_for_process_group_empty(
        helper_identity, kill_timeout_seconds, poll_interval_seconds
    ):
        if helper_process.poll() is not None:
            helper_process.wait(timeout=0)
        return "group_killed"
    raise RuntimeError("训练/helper 进程组在 SIGKILL 后仍未收口。")


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


def _terminate_helper_group(
    helper_process,
    helper_identity,
    term_timeout_seconds=5,
    kill_timeout_seconds=5,
):
    """训练 PID 尚未写入日志时的最后兜底；此路径会标记证据不完整。"""

    _signal_bound_helper_group(helper_identity, signal.SIGTERM)
    if _wait_for_process_group_empty(helper_identity, term_timeout_seconds, 0.2):
        if helper_process.poll() is not None:
            helper_process.wait(timeout=0)
        return "helper_group_terminated"
    _signal_bound_helper_group(helper_identity, KILL_SIGNAL)
    if _wait_for_process_group_empty(helper_identity, kill_timeout_seconds, 0.2):
        if helper_process.poll() is not None:
            helper_process.wait(timeout=0)
        return "helper_group_killed"
    raise RuntimeError("helper 进程组在 SIGKILL 后仍未退出。")


def _terminate_uncaptured_helper(helper_process):
    """身份捕获前失败时，helper 尚未 wait，PID 不会复用，可安全杀整组。"""

    outcome = {
        "cleanup_complete": False,
        "process_evidence_state": "uncaptured_helper_forced_group_kill",
        "errors": [],
    }
    try:
        os.killpg(helper_process.pid, KILL_SIGNAL)
    except ProcessLookupError:
        pass
    except BaseException as exc:
        outcome["errors"].append(f"{type(exc).__name__}: {exc}")
    try:
        helper_process.wait(timeout=5)
    except BaseException as exc:
        outcome["errors"].append(f"{type(exc).__name__}: {exc}")
    outcome["cleanup_complete"] = not outcome["errors"]
    return outcome


def finish_receipt_path(receipt):
    receipt = Path(receipt)
    return receipt.with_name(f"{receipt.stem}.finish.json")


def sealed_training_pid_from_log(training_log, command, return_code):
    text = Path(training_log).read_text(encoding="utf-8", errors="replace")
    command_sha256 = hashlib.sha256(command.encode("utf-8")).hexdigest()
    starts = re.findall(
        rf"^GTPJ_TRAINING_PROCESS_STARTED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) started_at=\S+$",
        text,
        flags=re.MULTILINE,
    )
    finishes = re.findall(
        rf"^GTPJ_TRAINING_PROCESS_FINISHED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) returncode=(-?[0-9]+) finished_at=\S+$",
        text,
        flags=re.MULTILINE,
    )
    if len(starts) != 1 or len(finishes) != 1:
        raise RuntimeError("训练日志没有唯一的真实启动/结束 PID 标记。")
    finish_pid, logged_return_code = finishes[0]
    if starts[0] != finish_pid:
        raise RuntimeError("训练日志的启动与结束 pid 不一致。")
    if int(logged_return_code) != int(return_code):
        raise RuntimeError("训练日志的 returncode 与 helper 结果不一致。")
    return int(finish_pid)


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
    actual_training_pid = sealed_training_pid_from_log(
        training_log, command, return_code
    )
    if payload["pid"] != actual_training_pid:
        raise RuntimeError("run finish receipt 的 pid 与训练日志中的真实 PID 不一致。")
    for field in ("started_at", "finished_at"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise RuntimeError(f"run finish receipt 的 {field} 无效。")
    return payload


def cleanup_process_tree(*, helper_process, helper_identity, training_log, receipt):
    """无论上游哪一步异常，都尽力终止并回收训练/helper 进程。"""

    outcome = {
        "training_pid": None,
        "training_termination": None,
        "helper_termination": None,
        "helper_identity": helper_identity,
        "training_identity": None,
        "cleanup_complete": False,
        "process_evidence_state": "cleanup_not_verified",
        "errors": [],
    }
    if helper_process is None or helper_identity is None:
        outcome["errors"].append("缺少受信 helper 进程身份，无法安全清理。")
    else:
        try:
            outcome["training_pid"] = training_pid_from_log(training_log)
        except Exception as exc:
            outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        if outcome["training_pid"] is not None:
            outcome["process_evidence_state"] = "training_pid_observed"
            try:
                training_identity = capture_training_identity(
                    outcome["training_pid"], helper_identity
                )
                outcome["training_identity"] = training_identity
                if training_identity is not None:
                    try:
                        outcome["training_termination"] = terminate_training_process(
                            training_pid=outcome["training_pid"],
                            training_identity=training_identity,
                            helper_process=helper_process,
                            helper_identity=helper_identity,
                        )
                    finally:
                        _close_pidfd(training_identity)
            except Exception as exc:
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        else:
            outcome["process_evidence_state"] = "incomplete_before_training_pid"
        identity_error = any("不属于本次 helper" in item for item in outcome["errors"])
        if not identity_error and process_group_members(helper_identity):
            try:
                outcome["helper_termination"] = _terminate_helper_group(
                    helper_process, helper_identity
                )
            except Exception as exc:
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            group_empty = not process_group_members(helper_identity)
            helper_exited = helper_process.poll() is not None
            outcome["cleanup_complete"] = group_empty and helper_exited and not identity_error
        except Exception as exc:
            outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        if helper_process.poll() is not None:
            try:
                helper_process.wait(timeout=0)
            except (subprocess.TimeoutExpired, TypeError) as exc:
                outcome["cleanup_complete"] = False
                outcome["errors"].append(f"{type(exc).__name__}: {exc}")
        if outcome["errors"]:
            outcome["process_evidence_state"] = "incomplete_cleanup_error"
        elif outcome["cleanup_complete"]:
            outcome["process_evidence_state"] = "process_tree_stopped"
        _close_pidfd(helper_identity)
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
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_launch_failure_record(path, *, helper_pid, status_error, cleanup):
    """状态账本不可写时，在 RUN 目录保留不可覆盖的最小故障凭证。"""

    payload = {
        "schema_version": "gtpj.v5_ablation_001.launch_failure.v1",
        "helper_pid": int(helper_pid),
        "status_error": f"{type(status_error).__name__}: {status_error}",
        "cleanup": cleanup,
        "recorded_at_epoch": time.time(),
    }
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def persist_controller_failure(
    *,
    claim_path,
    runtime_root,
    warehouse_root,
    stage,
    error,
    status_data,
):
    """claim 一旦领取，任何后续失败都写入不可覆盖的恢复凭证。"""

    claim_path = Path(claim_path)
    runtime_root = Path(runtime_root)
    warehouse_root = Path(warehouse_root)
    recovery_path = runtime_root / "recovery_handoff.json"
    recovery_error = ""
    if runtime_root.is_dir() and not recovery_path.exists():
        try:
            write_recovery_handoff(recovery_path, status_data)
        except Exception as exc:
            recovery_error = f"{type(exc).__name__}: {exc}"
    failure_path = claim_path.with_name(f"{claim_path.stem}.failure.json")
    payload = {
        "schema_version": "gtpj.v5_ablation_001.controller_failure.v1",
        "execution_claim": str(claim_path.resolve()),
        "execution_claim_sha256": _sha256_file(claim_path),
        "failure_stage": str(stage),
        "error": f"{type(error).__name__}: {error}",
        "automatic_resume_allowed": False,
        "runtime_root": str(runtime_root.resolve()),
        "warehouse_root": str(warehouse_root.resolve()),
        "recovery_handoff": str(recovery_path.resolve()),
        "recovery_handoff_present": recovery_path.is_file(),
        "recovery_handoff_error": recovery_error,
        "recorded_at_epoch": time.time(),
    }
    with failure_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return failure_path


def run_checked(command, *, cwd=None):
    return subprocess.run(
        [str(item) for item in command],
        cwd=None if cwd is None else str(cwd),
        check=True,
        capture_output=True,
        text=True,
    )


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_mapping(path, label):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} 不是可读取的 UTF-8 JSON。") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} 顶层必须是对象。")
    return value


def _fixed_data_source_path(data_source):
    data_source = Path(os.path.abspath(os.fspath(data_source)))
    if data_source != SERVER_DATA_SOURCE:
        raise ValueError(f"--data-source 必须是固定服务器目录：{SERVER_DATA_SOURCE}")
    if not data_source.is_dir():
        raise FileNotFoundError(f"固定数据目录不存在：{data_source}")
    return data_source


def verify_data_source(data_source, data_manifest_path):
    """对冻结清单中的 12 个 CUB/xlsa17 输入做完整内容校验。"""

    data_source = _fixed_data_source_path(data_source)
    payload = _read_json_mapping(data_manifest_path, "DATA_MANIFEST.json")
    if payload.get("schema_version") != DATA_MANIFEST_SCHEMA:
        raise ValueError("DATA_MANIFEST.json schema_version 不正确。")
    if payload.get("data_source_ref") != SERVER_DATA_SOURCE.as_posix():
        raise ValueError("DATA_MANIFEST.json data_source_ref 不是固定服务器目录。")
    for field, expected in DATA_CONTRACT_VALUES.items():
        if payload.get(field) != expected:
            raise ValueError(f"DATA_MANIFEST.json {field} 与 V5 正式口径不一致。")
    files = payload.get("files")
    if not isinstance(files, dict) or set(files) != set(V5_REQUIRED_DATA_FILES):
        raise ValueError("DATA_MANIFEST.json 必须恰好冻结 12 个正式输入文件。")
    root_resolved = data_source.resolve(strict=True)
    records = {}
    for logical_name, expected_relative in V5_REQUIRED_DATA_FILES.items():
        declared = files.get(logical_name)
        if not isinstance(declared, dict):
            raise ValueError(f"数据文件 {logical_name} 缺少冻结记录。")
        if declared.get("relative_path") != expected_relative:
            raise ValueError(f"数据文件 {logical_name} 的相对路径不正确。")
        expected_sha256 = str(declared.get("sha256", ""))
        expected_size = declared.get("size_bytes")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise ValueError(f"数据文件 {logical_name} 的 SHA-256 无效。")
        if not isinstance(expected_size, int) or expected_size <= 0:
            raise ValueError(f"数据文件 {logical_name} 的大小无效。")
        path = data_source / expected_relative
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root_resolved) or not resolved.is_file():
            raise ValueError(f"数据文件 {logical_name} 逃逸固定数据目录。")
        stat_result = resolved.stat()
        actual_sha256 = _sha256_file(resolved)
        if stat_result.st_size != expected_size or actual_sha256 != expected_sha256:
            raise ValueError(f"数据文件 {logical_name} 与冻结大小或 SHA-256 不一致。")
        records[logical_name] = {
            "relative_path": expected_relative,
            "resolved_path": resolved.as_posix(),
            "sha256": actual_sha256,
            "size_bytes": int(stat_result.st_size),
            "device": int(stat_result.st_dev),
            "inode": int(stat_result.st_ino),
            "mtime_ns": int(stat_result.st_mtime_ns),
        }
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return {
        "data_source": data_source.as_posix(),
        "data_manifest_sha256": _sha256_file(data_manifest_path),
        "contracts": dict(DATA_CONTRACT_VALUES),
        "files": records,
        "combined_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def verify_data_source_identity(data_source, expected_identity):
    """每个任务启动前同时复核元数据和完整内容哈希。"""

    if expected_identity.get("snapshot_mode") == "private_copy_read_only":
        return verify_snapshot_data_identity(data_source, expected_identity)
    data_source = _fixed_data_source_path(data_source)
    if expected_identity.get("data_source") != data_source.as_posix():
        raise ValueError("运行期数据目录与预检身份不一致。")
    expected_files = expected_identity.get("files")
    if not isinstance(expected_files, dict) or set(expected_files) != set(
        V5_REQUIRED_DATA_FILES
    ):
        raise ValueError("运行期数据身份记录不完整。")
    for logical_name, expected_relative in V5_REQUIRED_DATA_FILES.items():
        expected = expected_files[logical_name]
        path = (data_source / expected_relative).resolve(strict=True)
        stat_result = path.stat()
        actual = {
            "resolved_path": path.as_posix(),
            "sha256": _sha256_file(path),
            "size_bytes": int(stat_result.st_size),
            "device": int(stat_result.st_dev),
            "inode": int(stat_result.st_ino),
            "mtime_ns": int(stat_result.st_mtime_ns),
        }
        for field, value in actual.items():
            if expected.get(field) != value:
                detail = "SHA-256" if field == "sha256" else "身份"
                raise ValueError(f"数据文件 {logical_name} 的运行期{detail}发生变化。")
    return True


def materialize_data_snapshot(data_source, snapshot_root, expected_identity):
    """把冻结输入复制到本次 execution 私有目录，并在复制时复算完整哈希。"""

    data_source = Path(os.path.abspath(os.fspath(data_source)))
    snapshot_root = Path(os.path.abspath(os.fspath(snapshot_root)))
    if snapshot_root.exists():
        raise FileExistsError(f"运行数据快照目录已存在，拒绝复用：{snapshot_root}")
    expected_files = expected_identity.get("files")
    if not isinstance(expected_files, dict) or set(expected_files) != set(
        V5_REQUIRED_DATA_FILES
    ):
        raise ValueError("源数据身份记录不完整，无法制作运行快照。")
    snapshot_root.mkdir(parents=True)
    records = {}
    for logical_name, relative_path in V5_REQUIRED_DATA_FILES.items():
        expected = expected_files[logical_name]
        source = (data_source / relative_path).resolve(strict=True)
        destination = snapshot_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size_bytes = 0
        with source.open("rb") as input_stream, destination.open("xb") as output_stream:
            for block in iter(lambda: input_stream.read(1024 * 1024), b""):
                digest.update(block)
                size_bytes += len(block)
                output_stream.write(block)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        actual_sha256 = digest.hexdigest()
        if (
            size_bytes != expected.get("size_bytes")
            or actual_sha256 != expected.get("sha256")
        ):
            raise ValueError(
                f"复制数据快照时 {logical_name} 与冻结大小或 SHA-256 不一致。"
            )
        destination.chmod(0o444)
        stat_result = destination.stat()
        records[logical_name] = {
            "relative_path": relative_path,
            "resolved_path": destination.resolve(strict=True).as_posix(),
            "sha256": actual_sha256,
            "size_bytes": int(stat_result.st_size),
            "device": int(stat_result.st_dev),
            "inode": int(stat_result.st_ino),
            "mtime_ns": int(stat_result.st_mtime_ns),
        }
    directories = sorted(
        (path for path in snapshot_root.rglob("*") if path.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    )
    for directory in directories:
        directory.chmod(0o555)
    snapshot_root.chmod(0o555)
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return {
        "data_source": snapshot_root.as_posix(),
        "source_data_source": data_source.as_posix(),
        "source_combined_sha256": expected_identity.get("combined_sha256"),
        "contracts": dict(expected_identity.get("contracts", {})),
        "files": records,
        "combined_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "snapshot_mode": "private_copy_read_only",
    }


def verify_snapshot_data_identity(snapshot_root, expected_identity):
    """每个 RUN 启动前重算私有只读快照，训练不再读取可变源目录。"""

    snapshot_root = Path(os.path.abspath(os.fspath(snapshot_root)))
    if expected_identity.get("data_source") != snapshot_root.as_posix():
        raise ValueError("运行数据快照路径与冻结身份不一致。")
    root_resolved = snapshot_root.resolve(strict=True)
    expected_files = expected_identity.get("files")
    if not isinstance(expected_files, dict) or set(expected_files) != set(
        V5_REQUIRED_DATA_FILES
    ):
        raise ValueError("运行数据快照身份记录不完整。")
    for logical_name, relative_path in V5_REQUIRED_DATA_FILES.items():
        expected = expected_files[logical_name]
        path = (snapshot_root / relative_path).resolve(strict=True)
        if not path.is_relative_to(root_resolved) or not path.is_file():
            raise ValueError(f"运行数据快照文件 {logical_name} 逃逸私有目录。")
        stat_result = path.stat()
        if stat_result.st_mode & 0o222:
            raise ValueError(f"运行数据快照文件 {logical_name} 仍可写。")
        actual = {
            "resolved_path": path.as_posix(),
            "sha256": _sha256_file(path),
            "size_bytes": int(stat_result.st_size),
            "device": int(stat_result.st_dev),
            "inode": int(stat_result.st_ino),
            "mtime_ns": int(stat_result.st_mtime_ns),
        }
        for field, value in actual.items():
            if expected.get(field) != value:
                detail = "SHA-256" if field == "sha256" else "身份"
                raise ValueError(
                    f"运行数据快照文件 {logical_name} 的{detail}发生变化。"
                )
    return True


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


def verify_frozen_launch_evidence(
    bundle,
    python,
    data_source,
    manifest,
    expected_commit,
    *,
    python_execution_ref=None,
):
    """从 Git bundle 自身重建受信证据，不相信外部清单里的通过布尔值。"""

    bundle = Path(bundle).resolve()
    python = Path(os.path.abspath(os.fspath(python)))
    if not bundle.is_file():
        raise FileNotFoundError(f"Git bundle 不存在：{bundle}")
    python_runtime_identity = verify_python_runtime(python, manifest)
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
        required_validation_refs = {
            *VALIDATION_LOCAL_BRANCH_REFS.values(),
            *VALIDATION_REQUIRED_TAG_REFS,
        }
        missing_validation_refs = sorted(required_validation_refs - refs.keys())
        if missing_validation_refs:
            raise ValueError(
                "Git bundle 缺少实验起点校验所需的管理引用："
                f"{missing_validation_refs}"
            )
        if (
            refs[VALIDATION_LOCAL_BRANCH_REFS["framework/v5-template-v1"]]
            != TEMPLATE_COMMIT
        ):
            raise ValueError("Git bundle 的 V5 母版分支没有指向冻结母版提交。")
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
        if manifest.get("template_commit") != TEMPLATE_COMMIT:
            raise ValueError("启动许可清单 template_commit 与控制器信任根不一致。")
        resolved_template_tag = run_checked(
            [
                "git",
                "rev-parse",
                f"{refs['refs/tags/model/v5-template-v1']}^{{commit}}",
            ],
            cwd=bare_repo,
        ).stdout.strip()
        if resolved_template_tag != TEMPLATE_COMMIT:
            raise ValueError("Git bundle 的 V5 母版 Tag 没有指向冻结母版提交。")
        validator_path = "workflow/gtpj_workflow.py"
        trusted_validator_blob = run_checked(
            ["git", "rev-parse", f"{TEMPLATE_COMMIT}:{validator_path}"],
            cwd=bare_repo,
        ).stdout.strip()
        candidate_validator_blob = run_checked(
            ["git", "rev-parse", f"{expected_commit}:{validator_path}"],
            cwd=bare_repo,
        ).stdout.strip()
        if candidate_validator_blob not in {
            trusted_validator_blob,
            BOUND_RUNTIME_WORKFLOW_BLOB,
        }:
            raise ValueError(
                "冻结提交的 workflow/gtpj_workflow.py 不是母版或已审核的绑定运行时版本。"
            )
        run_checked(["git", "clone", "--quiet", str(bundle), str(checkout)])
        run_checked(
            ["git", "checkout", "-B", EXPERIMENT_BRANCH, expected_commit],
            cwd=checkout,
        )
        if run_checked(["git", "rev-parse", "HEAD"], cwd=checkout).stdout.strip() != expected_commit:
            raise ValueError("隔离校验仓库 HEAD 未固定到 pre_run_freeze_commit。")
        if run_checked(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=checkout
        ).stdout.strip() != EXPERIMENT_BRANCH:
            raise ValueError("隔离校验仓库没有绑定正式实验分支。")
        for local_branch, bundle_ref in VALIDATION_LOCAL_BRANCH_REFS.items():
            run_checked(
                ["git", "branch", "-f", local_branch, refs[bundle_ref]],
                cwd=checkout,
            )
        if run_checked(["git", "status", "--porcelain"], cwd=checkout).stdout.strip():
            raise ValueError("隔离校验仓库不是干净工作树。")

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
        data_identity = verify_data_source(
            data_source, checkout / TRUSTED_EVIDENCE_REFS["data_manifest_ref"]
        )
        matrix = checkout / TRUSTED_EVIDENCE_REFS["parameter_matrix_ref"]
        run_ids = _read_frozen_run_ids(matrix)
        if manifest.get("run_ids") != run_ids:
            raise ValueError("启动许可清单 run_ids 与冻结参数矩阵不一致。")

        workflow = checkout / "workflow/gtpj_workflow.py"
        runtime_python = python_execution_ref or python
        commands = [
            [runtime_python, workflow, "validate-ai-cross-review", "--path", checkout / REVIEW_PACK],
            [runtime_python, workflow, "validate-agent-runtime", "--path", checkout / EXPERIMENT_DIR / "agent_runtime.yaml"],
            [runtime_python, workflow, "validate-parameter-matrix", "--path", matrix, "--expected-jobs", "6", "--require-ready"],
            [runtime_python, workflow, "validate-experiment-base", "--path", checkout / EXPERIMENT_DIR],
            [runtime_python, workflow, "validate"],
            [runtime_python, workflow, "validate-workflow-consistency"],
            [runtime_python, workflow, "validate-framework-ledgers"],
            [runtime_python, workflow, "audit-boundary"],
        ]
        for command in commands:
            run_checked(command, cwd=checkout)
        verify_python_runtime(
            python, manifest, expected_identity=python_runtime_identity
        )
        return {
            "commit": expected_commit,
            "branch": EXPERIMENT_BRANCH,
            "template_commit": TEMPLATE_COMMIT,
            "run_ids": run_ids,
            "validated_command_count": len(commands),
            "python_runtime": python_runtime_identity,
            "data_identity": data_identity,
        }


def validate_fresh_execution_roots(
    runtime_root,
    warehouse_root,
    expected_commit,
    *,
    runtime_base=SERVER_RUNTIME_BASE,
    warehouse_base=SERVER_WAREHOUSE_BASE,
):
    runtime_root = Path(runtime_root).resolve()
    warehouse_root = Path(warehouse_root).resolve()
    runtime_base = Path(runtime_base).resolve()
    warehouse_base = Path(warehouse_base).resolve()
    expected_name = execution_id_for_commit(expected_commit)
    if runtime_root.name != expected_name:
        raise ValueError(f"runtime-root 必须以准确 execution_id 命名：{expected_name}")
    if warehouse_root.name != expected_name:
        raise ValueError(f"warehouse-root 必须以准确 execution_id 命名：{expected_name}")
    if runtime_root.parent != runtime_base:
        raise ValueError(f"runtime-root 必须直接位于固定目录：{runtime_base}")
    if warehouse_root.parent != warehouse_base:
        raise ValueError(f"warehouse-root 必须直接位于固定目录：{warehouse_base}")
    if runtime_root == warehouse_root:
        raise ValueError("runtime-root 与 warehouse-root 不能是同一路径。")
    if runtime_root.exists():
        raise FileExistsError(f"runtime-root 已存在，拒绝复用：{runtime_root}")
    if warehouse_root.exists():
        raise FileExistsError(f"warehouse-root 已存在，拒绝复用：{warehouse_root}")
    return runtime_root, warehouse_root


def _atomic_create_json(path, payload):
    """先把完整 JSON 写入同目录临时文件，再用硬链接原子发布且禁止覆盖。"""

    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    published = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp_path, path)
        published = True
    except BaseException:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        if not published:
            raise
    return path


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
            return _atomic_create_json(claim_path, payload)
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
    heads = run_checked(
        ["git", "bundle", "list-heads", str(bundle)]
    ).stdout.splitlines()
    refs = {}
    for line in heads:
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2:
            refs[parts[1]] = parts[0]
    required_validation_refs = {
        *VALIDATION_LOCAL_BRANCH_REFS.values(),
        *VALIDATION_REQUIRED_TAG_REFS,
    }
    missing_validation_refs = sorted(required_validation_refs - refs.keys())
    if missing_validation_refs:
        raise ValueError(
            "Git bundle 缺少运行副本所需的管理引用："
            f"{missing_validation_refs}"
        )
    if (
        refs[VALIDATION_LOCAL_BRANCH_REFS["framework/v5-template-v1"]]
        != TEMPLATE_COMMIT
    ):
        raise ValueError("Git bundle 的 V5 母版分支没有指向冻结母版提交。")
    run_checked(["git", "clone", "--quiet", str(bundle), str(target)])
    run_checked(["git", "checkout", "--detach", commit], cwd=target)
    for local_branch, bundle_ref in VALIDATION_LOCAL_BRANCH_REFS.items():
        run_checked(
            ["git", "branch", "-f", local_branch, refs[bundle_ref]],
            cwd=target,
        )
    if bind_experiment_branch:
        run_checked(
            ["git", "checkout", "-B", EXPERIMENT_BRANCH, commit],
            cwd=target,
        )
    status = run_checked(["git", "status", "--porcelain"], cwd=target).stdout.strip()
    if status:
        raise RuntimeError(f"新建运行副本不干净：{target}")


def build_training_command(
    python,
    group,
    config,
    code_root,
    commit,
    *,
    data_root,
    train_log_root,
):
    data_identity = os.stat(data_root, follow_symlinks=False)
    train_log_identity = os.stat(train_log_root, follow_symlinks=False)
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
        "--data-root",
        str(data_root),
        "--train-log-root",
        str(train_log_root),
        "--data-device",
        str(data_identity.st_dev),
        "--data-inode",
        str(data_identity.st_ino),
        "--train-log-device",
        str(train_log_identity.st_dev),
        "--train-log-inode",
        str(train_log_identity.st_ino),
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
    data_source = Path(os.path.abspath(os.fspath(args.data_source)))
    python = Path(os.path.abspath(os.fspath(args.python)))
    for path, label in (
        (bundle, "Git bundle"),
        (data_source, "数据目录"),
        (python, "Python"),
    ):
        if not path.exists():
            raise FileNotFoundError(f"{label} 不存在：{path}")
    verify_python_runtime(
        python,
        args.launch_manifest_payload,
        expected_identity=args.python_runtime_identity,
    )
    verify_data_source_identity(data_source, args.data_runtime_identity)

    runtime_root.mkdir(parents=True, exist_ok=False)
    warehouse_root.mkdir(parents=True, exist_ok=False)
    args.source_data_runtime_identity = args.data_runtime_identity
    args.run_data_source = runtime_root / "data_snapshot"
    args.data_runtime_identity = materialize_data_snapshot(
        data_source,
        args.run_data_source,
        args.source_data_runtime_identity,
    )
    code_roots = {
        "FULL": runtime_root / "code_FULL",
        "GLOBAL_ONLY": runtime_root / "code_GLOBAL_ONLY",
    }
    code_commits = {"FULL": args.commit, "GLOBAL_ONLY": args.commit}
    for group, code_root in code_roots.items():
        clone_at(bundle, code_root, code_commits[group])
        group_warehouse = warehouse_root / group
        (group_warehouse / "train_log").mkdir(parents=True)

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
        run_gate.request_stop()
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
    code_commit = args.commit
    fixed_python = Path(os.path.abspath(os.fspath(args.python)))
    command = build_training_command(
        fixed_python,
        group,
        config,
        code_root,
        code_commit,
        data_root=getattr(args, "run_data_source", args.data_source),
        train_log_root=warehouse_root / group / "train_log",
    )
    helper_args = [
        str(fixed_python),
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
    try:
        run_gate.write_status_or_block(lambda: status.update_job(
            job_id,
            status="starting",
            group=group,
            ledger=str(ledger_root),
            code_root=str(code_root),
            receipt=str(receipt),
            training_log=str(training_log),
        ))
    except BaseException:
        run_gate.mark_failure()
        raise
    process = None
    helper_identity = None
    return_code = None
    stopped_by_request = False
    caught = None
    cleanup = None

    def launch_helper():
        nonlocal helper_identity
        verify_python_runtime(
            args.python,
            args.launch_manifest_payload,
            expected_identity=args.python_runtime_identity,
        )
        verify_data_source_identity(
            getattr(args, "run_data_source", args.data_source),
            args.data_runtime_identity,
        )
        if stop_file.exists() or stop_requested.is_set():
            run_gate.request_stop()
            return None
        job_dir.mkdir(parents=True, exist_ok=False)
        helper_environment = os.environ.copy()
        helper_environment[BOUND_PYTHON_EXEC_ENV] = getattr(
            args, "bound_python_exec_ref", str(fixed_python)
        )
        helper_environment[BOUND_PYTHON_ARGV0_ENV] = str(fixed_python)
        with helper_log.open("xb") as stream:
            def spawn_helper():
                return subprocess.Popen(
                    helper_args,
                    cwd=str(ledger_root),
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    executable=getattr(args, "bound_python_exec_ref", None),
                    env=helper_environment,
                )

            helper_process = run_gate.launch_if_allowed(
                spawn_helper,
                should_block=lambda: stop_file.exists() or stop_requested.is_set(),
            )
            if helper_process is None:
                run_gate.request_stop()
                return None
        try:
            helper_identity = capture_helper_identity(helper_process)
        except BaseException as identity_error:
            launch_cleanup = _terminate_uncaptured_helper(helper_process)
            try:
                write_launch_failure_record(
                    job_dir / "launch_failure.json",
                    helper_pid=helper_process.pid,
                    status_error=identity_error,
                    cleanup=launch_cleanup,
                )
            except BaseException as record_error:
                raise RuntimeError(
                    "helper 身份捕获失败，且 launch_failure.json 无法落盘；"
                    f"helper_pid={helper_process.pid}；"
                    f"cleanup_complete={launch_cleanup.get('cleanup_complete')}；"
                    f"record_error={type(record_error).__name__}: {record_error}"
                ) from identity_error
            if not launch_cleanup.get("cleanup_complete"):
                raise RuntimeError(
                    "helper 身份捕获失败且进程组清理不完整；"
                    f"helper_pid={helper_process.pid}；"
                    f"errors={launch_cleanup.get('errors', [])}"
                ) from identity_error
            raise
        try:
            run_gate.write_status_or_block(lambda: status.update_job(
                job_id,
                status="running",
                helper_pid=helper_process.pid,
                helper_process_group_id=helper_process.pid,
                helper_start_time_ticks=helper_identity["start_time_ticks"],
            ))
        except BaseException as status_error:
            try:
                launch_cleanup = cleanup_process_tree(
                    helper_process=helper_process,
                    helper_identity=helper_identity,
                    training_log=training_log,
                    receipt=receipt,
                )
            except BaseException as cleanup_error:
                launch_cleanup = {
                    "cleanup_complete": False,
                    "process_evidence_state": "incomplete_cleanup_exception",
                    "errors": [f"{type(cleanup_error).__name__}: {cleanup_error}"],
                }
            try:
                write_launch_failure_record(
                    job_dir / "launch_failure.json",
                    helper_pid=helper_process.pid,
                    status_error=status_error,
                    cleanup=launch_cleanup,
                )
            except BaseException as record_error:
                raise RuntimeError(
                    "running 状态写入失败，且 launch_failure.json 无法落盘；"
                    f"helper_pid={helper_process.pid}；"
                    f"cleanup_complete={launch_cleanup.get('cleanup_complete')}；"
                    f"record_error={type(record_error).__name__}: {record_error}"
                ) from status_error
            if not launch_cleanup.get("cleanup_complete"):
                raise RuntimeError(
                    "running 状态写入失败且 helper 进程树清理不完整；"
                    f"helper_pid={helper_process.pid}；"
                    f"errors={launch_cleanup.get('errors', [])}"
                ) from status_error
            raise
        return helper_process

    try:
        process = run_gate.launch_if_allowed(
            launch_helper,
            should_block=lambda: stop_file.exists() or stop_requested.is_set(),
        )
        if process is None:
            status.update_job(job_id, status="not_started_after_stop_or_failure")
            return None
        while process.poll() is None:
            if stop_file.exists() or stop_requested.is_set():
                run_gate.request_stop()
                stop_requested.set()
                stop_file.touch(exist_ok=True)
                status.update_job(job_id, status="stopping")
                stopped_by_request = True
                cleanup = cleanup_process_tree(
                    helper_process=process,
                    helper_identity=helper_identity,
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
                helper_identity=helper_identity,
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
                    run_gate.mark_failure()
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
            if not cleanup.get("cleanup_complete") and caught is None:
                caught = RuntimeError("helper 进程树清理不完整，正式证据阻断。")
            if (
                not stopped_by_request
                and return_code == 0
                and cleanup.get("receipt_state") != "verified"
                and caught is None
            ):
                caught = RuntimeError("训练返回成功但缺少 finish receipt，正式证据阻断。")
            if caught is not None or (return_code is not None and return_code != 0):
                # 必须先关闸，再做任何可能阻塞的状态写入，避免另一张卡领取下一项。
                run_gate.mark_failure()
            try:
                run_gate.write_status_or_block(
                    lambda: status.update_job(job_id, **cleanup_values)
                )
            except BaseException as exc:
                if caught is None:
                    caught = exc
                run_gate.mark_failure()
    if caught is not None:
        run_gate.mark_failure()
        raise caught
    if return_code != 0:
        run_gate.mark_failure()
    run_gate.write_status_or_block(
        lambda: status.update_job(
            job_id,
            status=(
                "stopped"
                if stopped_by_request
                else "completed" if return_code == 0 else "failed"
            ),
            return_code=return_code,
            finished_at_epoch=time.time(),
        )
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
    python_binding = bind_python_runtime(args.python, launch_manifest)
    args.bound_python_fd = python_binding["fd"]
    args.bound_python_exec_ref = python_binding["exec_ref"]
    atexit.register(_close_fd_quietly, args.bound_python_fd)
    evidence_verification = verify_frozen_launch_evidence(
        args.bundle,
        args.python,
        args.data_source,
        launch_manifest,
        args.commit,
        python_execution_ref=args.bound_python_exec_ref,
    )
    args.launch_manifest_payload = launch_manifest
    args.python_runtime_identity = evidence_verification["python_runtime"]
    args.data_runtime_identity = evidence_verification["data_identity"]
    if stop_requested.is_set():
        raise RuntimeError("收到停止信号，拒绝领取正式运行身份。")
    if not args.data_source.resolve().is_dir():
        raise FileNotFoundError(f"数据目录不存在：{args.data_source.resolve()}")
    gpu_preflight = verify_server_gpu_preflight()
    runtime_root, warehouse_root = validate_fresh_execution_roots(
        args.runtime_root, args.warehouse_root, args.commit
    )
    claim_path = claim_execution_identity(
        SERVER_CLAIM_ROOT,
        execution_id=launch_manifest["execution_id"],
        commit=args.commit,
        run_ids=launch_manifest["run_ids"],
        runtime_root=runtime_root,
        warehouse_root=warehouse_root,
    )
    status = None
    stage = "post_claim_pre_layout"
    final_status = "failed"
    try:
        if stop_requested.is_set():
            raise RuntimeError("收到停止信号；运行身份已领取但不会创建训练副本。")
        stage = "prepare_layout"
        (
            runtime_root,
            warehouse_root,
            code_roots,
            code_commits,
            ledger_roots,
        ) = prepare_layout(args)
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
            "python_runtime": args.python_runtime_identity,
            "data_runtime_snapshot": args.data_runtime_identity,
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
        stage = "status_initialization"
        status = StatusStore(runtime_root / "status.json", initial)
        run_gate = RunGate()
        if stop_requested.is_set():
            run_gate.request_stop()
            stop_file.touch(exist_ok=True)
            status.set_controller(
                status="stopping", stop_requested_at_epoch=time.time()
            )

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
                    run_gate.mark_failure()
                    try:
                        status.update_job(
                            job_id,
                            status="failed",
                            controller_error=f"{type(exc).__name__}: {exc}",
                        )
                    except BaseException:
                        return
                    code = 1
                if code not in {None, 0}:
                    run_gate.mark_failure()

        stage = "worker_execution"
        threads = [
            threading.Thread(target=worker, args=(group,)) for group in GROUP_JOBS
        ]
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
        stage = "final_status"
        status.set_controller(status=final_status, finished_at_epoch=time.time())
        if final_status != "completed":
            stage = "recovery_handoff"
            write_recovery_handoff(
                runtime_root / "recovery_handoff.json", status.data
            )
    except Exception as exc:
        failure_status = (
            status.data
            if status is not None
            else {
                "experiment_id": "V5-ABLATION-001",
                "status": "failed",
                "execution_claim": str(claim_path),
                "failure_stage": stage,
                "jobs": {
                    job_id: {"status": "not_started_after_stop_or_failure"}
                    for jobs in GROUP_JOBS.values()
                    for job_id in jobs
                },
            }
        )
        try:
            persist_controller_failure(
                claim_path=claim_path,
                runtime_root=runtime_root,
                warehouse_root=warehouse_root,
                stage=stage,
                error=exc,
                status_data=failure_status,
            )
        except Exception as evidence_error:
            raise RuntimeError(
                "控制器失败且恢复凭证写入失败；"
                f"original={type(exc).__name__}: {exc}；"
                f"evidence={type(evidence_error).__name__}: {evidence_error}"
            ) from exc
        raise
    raise SystemExit(0 if final_status == "completed" else 1)


if __name__ == "__main__":
    main()
