"""V5 代码等价性与历史高分复跑的双 GPU 服务器控制器。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


SCHEMA_VERSION = "gtpj.v5_confirmation_001.run_plan.v1"
EXPERIMENT_ID = "V5-CONFIRM-001"
EXPERIMENT_BRANCH = "exp/v5/confirmation/confirm-001-v5-code-equivalence"
EXPERIMENT_DIR = Path("experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence")
SERVER_PYTHON = Path("/data/lby/.conda/envs/dvsr_gpu/bin/python")
SERVER_DATA_SOURCE = Path("/data/lby/projects/cv_project/GTPJ/data")
SERVER_RUNTIME_ROOT = Path("/data/lby/projects/cv_project/GTPJ/.runtime/confirmation")
SERVER_WAREHOUSE_ROOT = Path("/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/confirmation")
SERVER_CLAIM_ROOT = SERVER_WAREHOUSE_ROOT / ".gtpj_execution_claims"
SERVER_GPU_LOCK_ROOT = Path("/data/lby/projects/cv_project/GTPJ/.runtime/gpu_locks")
LEGACY_V5_COMMIT = "4b259379d99c1a791442ea9e2fac0bb22b2411a9"
DYNAMIC_7511_COMMIT = "d505e992492eb6fe7272edf0f0dc1d15a5932434"
V5_CONFIG_SHA256 = "a11706a51657bedec949f612aed2063dfe57807c5bc1a5c81219e4ce5b162aca"
CURRENT_V5_CONFIG_SHA256 = "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"
DR095_SOURCE_CONFIG_SHA256 = "aec5ed6aa4c9ec872cd39383af5796b8daefde93d109c387b12df9363ca6953e"
DR095_CONFIG_SHA256 = "f4d95017cc884adb9a2549df4d88ee666e29c1e2b21e5395f5c4804a5eb83218"
CURRENT_TRAINING_BLOBS = {
    "model/MyModel.py": "e382fc803fc23d7781a310d5db2da16a412c9992",
    "train_GTPJ_CUB.py": "c09bf8a7368fd1e065a0ec13f40dc1f5e2d24ff7",
    "tools/v5_evaluation.py": "df86444b76c7d2a5419252ef6d5495f682c69234",
    "tools/v5_runtime.py": "236068d169db887f654bc65d1a83f46587255337",
}
GROUP_SPECS = {
    "LEGACY_V5": {
        "code_commit": LEGACY_V5_COMMIT,
        "config_ref": "experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/configs/V5-069.yaml",
        "config_sha256": V5_CONFIG_SHA256,
        "restore_target_H": 74.44,
        "formal_evidence": False,
        "execution_mode": "legacy_relative_roots",
    },
    "CURRENT_TEMPLATE": {
        "code_commit": "launcher_commit",
        "config_ref": "experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/configs/CURRENT-V5.yaml",
        "config_sha256": CURRENT_V5_CONFIG_SHA256,
        "restore_target_H": 74.44,
        "formal_evidence": True,
        "execution_mode": "bound_root_arguments",
    },
    "DYNAMIC_7511": {
        "code_commit": DYNAMIC_7511_COMMIT,
        "config_ref": "experiments/v5/confirmation/CONFIRM-001_v5-code-equivalence/configs/DR-095.yaml",
        "config_sha256": DR095_CONFIG_SHA256,
        "accepted_checkout_sha256": [DR095_CONFIG_SHA256, DR095_SOURCE_CONFIG_SHA256],
        "restore_target_H": 75.11,
        "formal_evidence": False,
        "execution_mode": "legacy_relative_roots",
    },
}
EXPECTED_JOBS = {
    *(f"DIAG-V5-{index:03d}" for index in range(1, 6)),
    *(f"RUN-{index:03d}" for index in range(1, 6)),
    *(f"DIAG-DR-{index:03d}" for index in range(1, 6)),
}
REQUIRED_DATA_CONTRACT = {
    "dataset": "CUB",
    "split_contract": "xlsa17_standard_trainval_test_seen_test_unseen",
    "label_contract": "zero_based_cache_labels_equal_xlsa17_labels",
    "class_order_contract": "sorted_seen_and_unseen_ids_from_xlsa17",
    "metric_contract": "GZSL_U_S_H_and_conventional_ZS",
}
NUMBER = r"[0-9]+(?:\.[0-9]+)?"
CURRENT_SUMMARY_RE = re.compile(
    rf"最佳 epoch=(?P<epoch>[0-9]+)，U=(?P<U>{NUMBER})%，"
    rf"S=(?P<S>{NUMBER})%，H=(?P<H>{NUMBER})%，ZS=(?P<ZS>{NUMBER})%。"
)
LEGACY_SUMMARY_RE = re.compile(
    rf"Best Results @ Epoch (?P<epoch>[0-9]+).*?"
    rf"GZSL-U\s*:\s*(?P<U>{NUMBER})%.*?"
    rf"GZSL-S\s*:\s*(?P<S>{NUMBER})%.*?"
    rf"GZSL-H\s*:\s*(?P<H>{NUMBER})%.*?"
    rf"ZSL\s*:\s*(?P<ZS>{NUMBER})%",
    re.DOTALL,
)


class LaunchError(RuntimeError):
    """正式启动或证据校验失败。"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--warehouse-root", type=Path, required=True)
    parser.add_argument("--data-source", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--data-manifest", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def exclusive_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n", closefd=False) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def verify_server_gpu_preflight() -> dict[str, Any]:
    inventory = subprocess.run(
        ["nvidia-smi", "--query-gpu=index", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.splitlines()
    indexes = {line.strip() for line in inventory if line.strip()}
    if not {"0", "1"}.issubset(indexes):
        raise LaunchError("服务器必须能看到 GPU 0 和 GPU 1。")
    applications = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.splitlines()
    active = sorted({line.strip() for line in applications if line.strip().isdigit()})
    if active:
        raise LaunchError("两张 GPU 仍有计算进程，拒绝抢占：" + ", ".join(active))
    return {"gpu_indexes": sorted(indexes), "active_compute_pids": []}


def acquire_gpu_locks() -> list[Any]:
    import fcntl

    SERVER_GPU_LOCK_ROOT.mkdir(parents=True, exist_ok=True)
    handles: list[Any] = []
    try:
        for gpu in (0, 1):
            handle = (SERVER_GPU_LOCK_ROOT / f"gpu-{gpu}.lock").open("a+", encoding="utf-8")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                handle.close()
                raise
            handles.append(handle)
    except BaseException:
        release_gpu_locks(handles)
        raise LaunchError("GPU 0/1 已被另一项受控实验锁定。")
    return handles


def release_gpu_locks(handles: list[Any]) -> None:
    try:
        import fcntl
    except ImportError:
        fcntl = None
    for handle in reversed(handles):
        try:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def claim_execution_identity(execution_id: str, commit: str, run_ids: list[str]) -> Path:
    import fcntl

    SERVER_CLAIM_ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = SERVER_CLAIM_ROOT / ".claims.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            used_run_ids: set[str] = set()
            for path in SERVER_CLAIM_ROOT.glob("*.json"):
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload.get("execution_id") == execution_id:
                    raise LaunchError("本次 execution_id 已经领取，拒绝重复运行。")
                used_run_ids.update(str(value) for value in payload.get("run_ids", []))
            duplicates = sorted(set(run_ids) & used_run_ids)
            if duplicates:
                raise LaunchError("run_id 已经领取，拒绝重复运行：" + ", ".join(duplicates))
            path = SERVER_CLAIM_ROOT / f"{execution_id}.json"
            exclusive_json(
                path,
                {
                    "schema_version": "gtpj.v5_confirmation_001.execution_claim.v1",
                    "experiment_id": EXPERIMENT_ID,
                    "execution_id": execution_id,
                    "commit": commit,
                    "run_ids": run_ids,
                    "claimed_at_unix": time.time(),
                },
            )
            return path
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise LaunchError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def require_commit(value: str, label: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise LaunchError(f"{label} 必须是 40 位小写 Git 提交号。")
    return value


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise LaunchError(f"{label}不存在：{path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LaunchError(f"{label}不是有效 UTF-8 JSON。") from exc
    if not isinstance(payload, dict):
        raise LaunchError(f"{label}顶层必须是对象。")
    return payload


def validate_plan(path: Path) -> dict[str, Any]:
    payload = load_json_object(path, "运行计划")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise LaunchError("运行计划 schema_version 不正确。")
    if payload.get("experiment_id") != EXPERIMENT_ID:
        raise LaunchError("运行计划 experiment_id 不正确。")
    if payload.get("run_all_five_owner_override") is not True:
        raise LaunchError("运行计划必须明确记录五次全部执行的 owner 决定。")
    if payload.get("near_miss_tolerance_H") != 0.2:
        raise LaunchError("接近目标的 H 容差必须固定为 0.2。")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 15:
        raise LaunchError("运行计划必须正好包含 15 项任务。")
    seen: set[str] = set()
    group_counts = {group: 0 for group in GROUP_SPECS}
    gpu_counts = {group: {0: 0, 1: 0} for group in GROUP_SPECS}
    attempts = {group: set() for group in GROUP_SPECS}
    run_ids: set[str] = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise LaunchError("运行计划中的每项任务必须是对象。")
        job_id = str(job.get("job_id", ""))
        group = str(job.get("group", ""))
        gpu = job.get("gpu")
        attempt = job.get("attempt")
        run_id = str(job.get("run_id", ""))
        if job_id not in EXPECTED_JOBS or job_id in seen:
            raise LaunchError(f"任务编号缺失、重复或越界：{job_id}")
        if group not in GROUP_SPECS:
            raise LaunchError(f"未知实验组：{group}")
        if gpu not in (0, 1):
            raise LaunchError(f"{job_id} 只能使用 GPU 0 或 1。")
        if not isinstance(attempt, int) or not 1 <= attempt <= 5:
            raise LaunchError(f"{job_id} 的 attempt 必须在 1..5。")
        expected_group = (
            "LEGACY_V5"
            if job_id.startswith("DIAG-V5-")
            else "DYNAMIC_7511"
            if job_id.startswith("DIAG-DR-")
            else "CURRENT_TEMPLATE"
        )
        if group != expected_group:
            raise LaunchError(f"{job_id} 必须属于 {expected_group}。")
        if not re.fullmatch(r"V5CONF001-[A-Z0-9-]+", run_id) or run_id in run_ids:
            raise LaunchError(f"{job_id} 的 run_id 缺失、重复或不安全。")
        seen.add(job_id)
        run_ids.add(run_id)
        group_counts[group] += 1
        gpu_counts[group][gpu] += 1
        attempts[group].add(attempt)
    if seen != EXPECTED_JOBS or any(count != 5 for count in group_counts.values()):
        raise LaunchError("三组任务必须各有五次且编号完整。")
    for group, counts in gpu_counts.items():
        if sorted(counts.values()) != [2, 3]:
            raise LaunchError(f"{group} 必须按 2/3 次交叉分配到两张 GPU。")
        if attempts[group] != {1, 2, 3, 4, 5}:
            raise LaunchError(f"{group} 的 attempt 必须正好覆盖 1..5。")
    return payload


def validate_checkout(repo_root: Path, commit: str) -> None:
    if git(repo_root, "rev-parse", "HEAD") != commit:
        raise LaunchError("控制器工作树 HEAD 与 --commit 不一致。")
    if git(repo_root, "status", "--porcelain", "--untracked-files=no"):
        raise LaunchError("控制器工作树包含 tracked 修改。")
    for relative_path, expected_blob in CURRENT_TRAINING_BLOBS.items():
        actual_blob = git(repo_root, "rev-parse", f"HEAD:{relative_path}")
        if actual_blob != expected_blob:
            raise LaunchError(f"今天代码的训练文件已变化：{relative_path}")


def validate_bundle(bundle: Path, repo_root: Path, commit: str) -> None:
    if not bundle.is_file():
        raise LaunchError(f"Git bundle 不存在：{bundle}")
    result = subprocess.run(
        ["git", "bundle", "verify", str(bundle)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise LaunchError("Git bundle 校验失败：" + (result.stderr.strip() or result.stdout.strip()))
    heads = subprocess.run(
        ["git", "bundle", "list-heads", str(bundle)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.splitlines()
    expected = f"{commit} refs/heads/{EXPERIMENT_BRANCH}"
    if expected not in heads:
        raise LaunchError("bundle 中的确认实验分支没有精确指向冻结提交。")
    required_commits = {
        commit,
        *(
            commit if spec["code_commit"] == "launcher_commit" else str(spec["code_commit"])
            for spec in GROUP_SPECS.values()
        ),
    }
    with tempfile.TemporaryDirectory(prefix="gtpj-v5-confirm-bundle-") as temporary:
        git_dir = Path(temporary) / "probe.git"
        init = subprocess.run(
            ["git", "init", "--bare", "--quiet", str(git_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if init.returncode != 0:
            raise LaunchError(init.stderr.strip() or "无法建立 bundle 隔离检查目录。")
        unpack = subprocess.run(
            ["git", f"--git-dir={git_dir}", "bundle", "unbundle", str(bundle)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if unpack.returncode != 0:
            raise LaunchError(unpack.stderr.strip() or "无法在隔离目录解包 bundle。")
        for required_commit in sorted(required_commits):
            present = subprocess.run(
                ["git", f"--git-dir={git_dir}", "cat-file", "-e", f"{required_commit}^{{commit}}"],
                capture_output=True,
            )
            if present.returncode != 0:
                raise LaunchError(f"bundle 缺少任务代码提交：{required_commit}")


def validate_config(repo_root: Path, spec: dict[str, Any]) -> Path:
    path = (repo_root / str(spec["config_ref"])).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise LaunchError("配置路径逃离冻结代码目录。") from exc
    if not path.is_file() or path.is_symlink():
        raise LaunchError(f"冻结配置不存在或是软链接：{path}")
    accepted_hashes = set(spec.get("accepted_checkout_sha256", [spec["config_sha256"]]))
    if sha256_file(path) not in accepted_hashes:
        raise LaunchError(f"冻结配置哈希不匹配：{path}")
    return path


def validate_data_manifest(path: Path, data_source: Path) -> dict[str, Any]:
    manifest = load_json_object(path, "数据清单")
    if manifest.get("schema_version") != "gtpj.v5_confirmation_001.data_manifest.v1":
        raise LaunchError("数据清单 schema_version 不正确。")
    for key, expected in REQUIRED_DATA_CONTRACT.items():
        if manifest.get(key) != expected:
            raise LaunchError(f"数据清单 {key} 不符合固定口径。")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise LaunchError("数据清单缺少逐文件身份。")
    data_source = data_source.resolve(strict=True)
    for name, record in files.items():
        if not isinstance(record, dict):
            raise LaunchError(f"数据清单 {name} 不是对象。")
        candidate = (data_source / str(record.get("relative_path", ""))).resolve(strict=True)
        try:
            candidate.relative_to(data_source)
        except ValueError as exc:
            raise LaunchError(f"数据文件 {name} 逃离数据根目录。") from exc
        if not candidate.is_file() or candidate.is_symlink():
            raise LaunchError(f"数据文件 {name} 不存在或是软链接。")
        if candidate.stat().st_size != int(record.get("size_bytes", -1)):
            raise LaunchError(f"数据文件 {name} 大小不匹配。")
        if sha256_file(candidate) != record.get("sha256"):
            raise LaunchError(f"数据文件 {name} 哈希不匹配。")
    return manifest


def clone_code(bundle: Path, destination: Path, commit: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--no-checkout", "--quiet", str(bundle), str(destination)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise LaunchError(result.stderr.strip() or "无法从 bundle 创建代码副本。")
    git(destination, "checkout", "--detach", commit)
    if git(destination, "rev-parse", "HEAD") != commit:
        raise LaunchError("任务代码副本没有停在指定提交。")
    if git(destination, "status", "--porcelain", "--untracked-files=all"):
        raise LaunchError("刚创建的任务代码副本不是干净状态。")


def parse_metrics(text: str) -> dict[str, Any]:
    current_matches = list(CURRENT_SUMMARY_RE.finditer(text))
    if current_matches:
        match = current_matches[-1]
    else:
        legacy_matches = list(LEGACY_SUMMARY_RE.finditer(text))
        if not legacy_matches:
            raise LaunchError("训练日志中找不到完整最终 U/S/H/ZS 汇总。")
        match = legacy_matches[-1]
    return {
        "best_epoch": int(match.group("epoch")),
        "U": float(match.group("U")),
        "S": float(match.group("S")),
        "H": float(match.group("H")),
        "ZS": float(match.group("ZS")),
    }


def file_record(path: Path, root: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise LaunchError(f"证据文件逃离任务目录：{path}") from exc
    if path.is_symlink() or not resolved.is_file():
        raise LaunchError(f"证据文件不存在或是软链接：{path}")
    return {
        "relative_path": relative.as_posix(),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def write_manifest(job_root: Path, result: dict[str, Any]) -> Path:
    artifacts: dict[str, Any] = {}
    for role, paths in {
        "launch_receipt": [job_root / "receipts" / "start.json"],
        "finish_receipt": [job_root / "receipts" / "finish.json"],
        "sealed_stdout_log": [job_root / "logs" / "training.log"],
        "config": [job_root / "config.yaml"],
        "run_result": [job_root / "result.json"],
        "internal_training_log": sorted((job_root / "train_log").rglob("training_log*.txt")),
        "retained_best_model": sorted((job_root / "train_log").rglob("best_model*.pth")),
    }.items():
        records = [file_record(path, job_root) for path in paths if path.exists()]
        if records:
            artifacts[role] = records
    payload = {
        "schema_version": "gtpj.v5_confirmation_001.artifact_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "job_id": result["job_id"],
        "group": result["group"],
        "formal_evidence": result["formal_evidence"],
        "code_commit": result["code_commit"],
        "config_sha256": result["config_sha256"],
        "metrics": result.get("metrics"),
        "return_code": result["return_code"],
        "artifacts": artifacts,
    }
    path = job_root / "artifact_manifest.json"
    atomic_json(path, payload)
    return path


def remove_checkpoint(path: Path) -> None:
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file():
        raise LaunchError(f"拒绝删除非普通 checkpoint：{path}")
    if resolved.suffix.lower() not in {".pth", ".pt", ".ckpt", ".safetensors"}:
        raise LaunchError(f"拒绝删除非 checkpoint 文件：{path}")
    resolved.unlink()


def apply_checkpoint_retention(results: list[dict[str, Any]]) -> None:
    by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in GROUP_SPECS}
    for result in results:
        if result.get("return_code") == 0 and result.get("metrics"):
            by_group[result["group"]].append(result)
    for group, group_results in by_group.items():
        ranked = sorted(group_results, key=lambda item: (-item["metrics"]["H"], item["job_id"]))
        keep_jobs = {item["job_id"] for item in ranked[:3]}
        for result in group_results:
            job_root = Path(result["job_root"])
            for checkpoint in sorted((job_root / "train_log").rglob("ckpt_full*.pth")):
                remove_checkpoint(checkpoint)
            best_models = sorted((job_root / "train_log").rglob("best_model*.pth"))
            if not best_models:
                raise LaunchError(f"{result['job_id']} 成功结束但没有最佳模型文件。")
            retained_model = None
            if result["job_id"] in keep_jobs:
                def score(path: Path) -> tuple[int, int]:
                    match = re.search(r"_H([0-9]+)\.pth$", path.name)
                    return (int(match.group(1)) if match else -1, path.stat().st_mtime_ns)

                retained_model = max(best_models, key=score)
            for checkpoint in best_models:
                if checkpoint != retained_model:
                    remove_checkpoint(checkpoint)
            result["checkpoint_retention"] = {
                "group": group,
                "kept_top3_job": result["job_id"] in keep_jobs,
                "full_resume_checkpoint_removed": True,
                "retained_best_model": retained_model.as_posix() if retained_model else None,
            }


def command_for_job(
    *,
    python: Path,
    code_root: Path,
    config: Path,
    job_root: Path,
    data_source: Path,
    execution_mode: str,
) -> list[str]:
    command = [str(python), str(code_root / "train_GTPJ_CUB.py"), "--config", str(config)]
    if execution_mode == "bound_root_arguments":
        command.extend(
            [
                "--data-root",
                str(data_source),
                "--train-log-root",
                str(job_root / "train_log"),
            ]
        )
    elif execution_mode != "legacy_relative_roots":
        raise LaunchError(f"未知执行模式：{execution_mode}")
    return command


def wrap_legacy_command_read_only(
    command: list[str], *, code_root: Path, job_root: Path, data_source: Path
) -> list[str]:
    """让旧入口继续使用 ./data，同时把正式数据以只读方式放进隔离环境。"""
    return [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--ro-bind",
        "/",
        "/",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--ro-bind",
        str(data_source),
        str(code_root / "data"),
        "--bind",
        str(job_root / "train_log"),
        str(code_root / "train_log"),
        "--chdir",
        str(code_root),
        *command,
    ]


def validate_legacy_data_isolation(data_source: Path, runtime_root: Path) -> None:
    bwrap = Path("/usr/bin/bwrap")
    if not bwrap.is_file():
        raise LaunchError("旧代码只读隔离需要 /usr/bin/bwrap。")
    runtime_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".v5-confirm-bwrap-", dir=runtime_root) as temporary:
        root = Path(temporary)
        bound_data = root / "data"
        writable_log = root / "train_log"
        bound_data.mkdir()
        writable_log.mkdir()
        probe_name = f".gtpj-write-probe-{os.getpid()}"
        if (data_source / probe_name).exists():
            raise LaunchError("只读隔离探针名称已存在。")
        script = (
            "from pathlib import Path; "
            f"root=Path({str(bound_data)!r}); "
            "assert (root/'cache/CUB_train_labels.pt').is_file(); "
            f"target=root/{probe_name!r}; "
            "\ntry:\n target.write_text('forbidden', encoding='utf-8')\n"
            "except OSError:\n pass\n"
            "else:\n raise SystemExit('read-only data accepted a write')\n"
            f"Path({str(writable_log / 'ok')!r}).write_text('ok', encoding='utf-8')"
        )
        result = subprocess.run(
            [
                str(bwrap),
                "--die-with-parent",
                "--ro-bind",
                "/",
                "/",
                "--dev-bind",
                "/dev",
                "/dev",
                "--proc",
                "/proc",
                "--ro-bind",
                str(data_source),
                str(bound_data),
                "--bind",
                str(writable_log),
                str(writable_log),
                str(SERVER_PYTHON),
                "-c",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not (writable_log / "ok").is_file():
            raise LaunchError(result.stderr.strip() or result.stdout.strip() or "旧代码只读数据隔离失败。")
        if (data_source / probe_name).exists():
            raise LaunchError("只读隔离探针污染了正式数据源。")


def validate_launch_gate(repo_root: Path, commit: str) -> None:
    gate = repo_root / EXPERIMENT_DIR / "agent_runtime.yaml"
    task_start = repo_root / EXPERIMENT_DIR / "TASK_START.yaml"
    gate_text = gate.read_text(encoding="utf-8")
    task_text = task_start.read_text(encoding="utf-8")
    required_gate_lines = {
        "runner_start_allowed: true",
        "formal_runner_allowed: true",
        "formal_evidence_allowed: true",
    }
    missing = sorted(line for line in required_gate_lines if line not in gate_text)
    if missing:
        raise LaunchError("开跑门尚未通过：" + ", ".join(missing))
    if "review_decision: pass" not in task_text:
        raise LaunchError("TASK_START 尚未登记独立审核通过。")
    reviewed_match = re.search(r"(?m)^reviewed_candidate_commit: ([0-9a-f]{40})$", gate_text)
    if not reviewed_match:
        raise LaunchError("agent_runtime 没有绑定准确的审核候选提交。")
    reviewed_commit = reviewed_match.group(1)
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed_commit, commit],
        cwd=repo_root,
    )
    if ancestry.returncode != 0:
        raise LaunchError("审核候选不是开跑提交的祖先。")
    allowed_exact = {
        (EXPERIMENT_DIR / "agent_runtime.yaml").as_posix(),
        (EXPERIMENT_DIR / "TASK_START.yaml").as_posix(),
        (EXPERIMENT_DIR / "AGENT_ACTIVITY.md").as_posix(),
        (EXPERIMENT_DIR / "MONITOR_HANDOFF.md").as_posix(),
    }
    allowed_prefixes = {
        (EXPERIMENT_DIR / "agent_outputs").as_posix() + "/",
        (EXPERIMENT_DIR / "reviews").as_posix() + "/",
    }
    changed = git(repo_root, "diff", "--name-only", reviewed_commit, commit).splitlines()
    forbidden = sorted(
        path
        for path in changed
        if path not in allowed_exact and not any(path.startswith(prefix) for prefix in allowed_prefixes)
    )
    if forbidden:
        raise LaunchError("审核后出现不允许的代码或参数变化：" + ", ".join(forbidden))
    for filename in ("runner_monitor.md", "interface_checker.md", "evidence_quality_checker.md"):
        output = repo_root / EXPERIMENT_DIR / "agent_outputs" / filename
        text = output.read_text(encoding="utf-8")
        if reviewed_commit not in text or "PASS" not in text:
            raise LaunchError(f"独立审核输出没有准确绑定候选或通过结论：{filename}")
    for command in (
        ["validate-agent-runtime", "--path", str(gate)],
        ["multi-agent-preflight", "--path", str(gate)],
    ):
        result = subprocess.run(
            [str(SERVER_PYTHON), str(repo_root / "workflow/gtpj_workflow.py"), *command],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise LaunchError(result.stderr.strip() or result.stdout.strip() or "开跑门校验失败。")


class Controller:
    def __init__(self, args: argparse.Namespace, repo_root: Path, plan: dict[str, Any]):
        self.args = args
        self.repo_root = repo_root
        self.plan = plan
        self.commit = require_commit(args.commit, "--commit")
        self.execution_id = f"V5-CONFIRM-001-{self.commit[:12]}"
        self.runtime_root = args.runtime_root.resolve()
        self.warehouse_root = args.warehouse_root.resolve()
        self.execution_root = self.runtime_root / self.execution_id
        self.warehouse_execution = self.warehouse_root / self.execution_id
        self.status_path = self.execution_root / "status.json"
        self.stop_path = self.execution_root / "STOP"
        self.stop_requested = threading.Event()
        self.status_lock = threading.Lock()
        self.results: list[dict[str, Any]] = []
        self.running: dict[int, subprocess.Popen[Any]] = {}
        self.launch_lock = threading.Lock()
        self.claim_path: Path | None = None

    def status_payload(self, state: str) -> dict[str, Any]:
        return {
            "schema_version": "gtpj.v5_confirmation_001.status.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "status": state,
            "launcher_commit": self.commit,
            "updated_at_unix": time.time(),
            "stop_file": self.stop_path.as_posix(),
            "execution_claim": self.claim_path.as_posix() if self.claim_path else None,
            "results": sorted(self.results, key=lambda item: item["job_id"]),
        }

    def write_status(self, state: str) -> None:
        with self.status_lock:
            atomic_json(self.status_path, self.status_payload(state))

    def request_stop(self, _signum: int, _frame: Any) -> None:
        self.stop_requested.set()

    def should_stop(self) -> bool:
        return self.stop_requested.is_set() or self.stop_path.exists()

    def prepare(self) -> None:
        if self.execution_root.exists() or self.warehouse_execution.exists():
            raise LaunchError("本次 execution 目录已经存在，拒绝覆盖或复用。")
        self.execution_root.mkdir(parents=True)
        self.warehouse_execution.mkdir(parents=True)
        self.write_status("prepared")

    def run_one(self, job: dict[str, Any]) -> dict[str, Any]:
        job_id = str(job["job_id"])
        group = str(job["group"])
        gpu = int(job["gpu"])
        spec = dict(GROUP_SPECS[group])
        code_commit = self.commit if spec["code_commit"] == "launcher_commit" else spec["code_commit"]
        code_commit = require_commit(str(code_commit), f"{job_id} code_commit")
        job_root = self.warehouse_execution / job_id
        code_root = self.execution_root / "code" / job_id
        job_root.mkdir(parents=True)
        (job_root / "logs").mkdir()
        (job_root / "receipts").mkdir()
        (job_root / "train_log").mkdir()
        clone_code(self.args.bundle, code_root, code_commit)
        if group == "CURRENT_TEMPLATE":
            for relative_path, expected_blob in CURRENT_TRAINING_BLOBS.items():
                if git(code_root, "rev-parse", f"HEAD:{relative_path}") != expected_blob:
                    raise LaunchError(f"{job_id} 今天代码训练文件哈希不匹配：{relative_path}")
        source_config = validate_config(self.repo_root, spec)
        config_copy = job_root / "config.yaml"
        shutil.copyfile(source_config, config_copy)
        if sha256_file(config_copy) != spec["config_sha256"]:
            raise LaunchError(f"{job_id} 配置复制后哈希变化。")
        if spec["execution_mode"] == "legacy_relative_roots":
            (code_root / "data").mkdir()
            (code_root / "train_log").mkdir()
        training_command = command_for_job(
            python=self.args.python,
            code_root=code_root,
            config=config_copy,
            job_root=job_root,
            data_source=self.args.data_source.resolve(),
            execution_mode=str(spec["execution_mode"]),
        )
        command = training_command
        if spec["execution_mode"] == "legacy_relative_roots":
            command = wrap_legacy_command_read_only(
                training_command,
                code_root=code_root,
                job_root=job_root,
                data_source=self.args.data_source.resolve(),
            )
        command_sha = hashlib.sha256(
            json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        start_receipt = {
            "schema_version": "gtpj.v5_confirmation_001.start_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": job_id,
            "run_id": str(job["run_id"]),
            "group": group,
            "attempt": int(job["attempt"]),
            "gpu": gpu,
            "formal_evidence": bool(spec["formal_evidence"]),
            "launcher_commit": self.commit,
            "code_commit": code_commit,
            "config_sha256": spec["config_sha256"],
            "command": command,
            "training_command": training_command,
            "command_sha256": command_sha,
            "bundle_sha256": sha256_file(self.args.bundle),
            "data_manifest_sha256": sha256_file(self.args.data_manifest),
            "started_at_unix": time.time(),
        }
        atomic_json(job_root / "receipts" / "start.json", start_receipt)
        environment = os.environ.copy()
        environment["CUDA_VISIBLE_DEVICES"] = str(gpu)
        environment["PYTHONUNBUFFERED"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        log_path = job_root / "logs" / "training.log"
        with log_path.open("w", encoding="utf-8", newline="\n") as log_handle:
            log_handle.write("GTPJ_PROCESS_START " + json.dumps(start_receipt, ensure_ascii=False, sort_keys=True) + "\n")
            log_handle.flush()
            with self.launch_lock:
                if self.should_stop():
                    raise LaunchError(f"{job_id} 在进程启动前收到停止或硬失败信号。")
                process = subprocess.Popen(
                    command,
                    cwd=code_root,
                    env=environment,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                with self.status_lock:
                    self.running[gpu] = process
            while process.poll() is None:
                if self.should_stop():
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                time.sleep(1)
            return_code = int(process.returncode)
            log_handle.write(f"GTPJ_PROCESS_FINISH return_code={return_code}\n")
            log_handle.flush()
            os.fsync(log_handle.fileno())
        with self.status_lock:
            self.running.pop(gpu, None)
        log_sha = sha256_file(log_path)
        metrics = None
        parse_error = None
        if return_code == 0:
            try:
                metrics = parse_metrics(log_path.read_text(encoding="utf-8", errors="replace"))
            except LaunchError as exc:
                parse_error = str(exc)
        evidence_return_code = 0 if return_code == 0 and parse_error is None else (90 if parse_error else return_code)
        finish_receipt = {
            "schema_version": "gtpj.v5_confirmation_001.finish_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": job_id,
            "run_id": str(job["run_id"]),
            "group": group,
            "code_commit": code_commit,
            "config_sha256": spec["config_sha256"],
            "command_sha256": command_sha,
            "training_log_sha256": log_sha,
            "process_return_code": return_code,
            "evidence_return_code": evidence_return_code,
            "metrics": metrics,
            "parse_error": parse_error,
            "finished_at_unix": time.time(),
        }
        atomic_json(job_root / "receipts" / "finish.json", finish_receipt)
        result = {
            "job_id": job_id,
            "run_id": str(job["run_id"]),
            "group": group,
            "gpu": gpu,
            "attempt": int(job["attempt"]),
            "formal_evidence": bool(spec["formal_evidence"]),
            "code_commit": code_commit,
            "config_sha256": spec["config_sha256"],
            "restore_target_H": float(spec["restore_target_H"]),
            "near_miss_tolerance_H": 0.2,
            "process_return_code": return_code,
            "return_code": evidence_return_code,
            "metrics": metrics,
            "job_root": job_root.as_posix(),
            "training_log_sha256": log_sha,
        }
        if metrics:
            result["target_hit"] = metrics["H"] >= float(spec["restore_target_H"])
            result["near_miss"] = (
                not result["target_hit"]
                and metrics["H"] >= float(spec["restore_target_H"]) - 0.2
            )
        return result

    def persist_early_failure(self, job: dict[str, Any], error: BaseException) -> dict[str, Any]:
        job_id = str(job["job_id"])
        group = str(job["group"])
        job_root = self.warehouse_execution / job_id
        (job_root / "logs").mkdir(parents=True, exist_ok=True)
        (job_root / "receipts").mkdir(parents=True, exist_ok=True)
        (job_root / "train_log").mkdir(parents=True, exist_ok=True)
        error_text = f"{type(error).__name__}: {error}"
        failure_log = job_root / "logs" / "training.log"
        if not failure_log.exists():
            failure_log.write_text("GTPJ_PRELAUNCH_FAILURE " + error_text + "\n", encoding="utf-8")
        finish = {
            "schema_version": "gtpj.v5_confirmation_001.finish_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": job_id,
            "run_id": str(job["run_id"]),
            "group": group,
            "process_return_code": None,
            "evidence_return_code": 99,
            "error": error_text,
            "finished_at_unix": time.time(),
        }
        atomic_json(job_root / "receipts" / "finish.json", finish)
        return {
            "job_id": job_id,
            "run_id": str(job["run_id"]),
            "group": group,
            "gpu": int(job["gpu"]),
            "attempt": int(job["attempt"]),
            "formal_evidence": bool(GROUP_SPECS[group]["formal_evidence"]),
            "return_code": 99,
            "error": error_text,
            "job_root": job_root.as_posix(),
            "training_log_sha256": sha256_file(failure_log),
        }

    def worker(self, gpu: int, jobs: list[dict[str, Any]]) -> None:
        for job in jobs:
            if self.should_stop():
                break
            try:
                result = self.run_one(job)
            except BaseException as exc:
                result = self.persist_early_failure(job, exc)
            with self.status_lock:
                self.results.append(result)
            if int(result.get("return_code", 99)) != 0:
                with self.launch_lock:
                    self.stop_requested.set()
            self.write_status("running")

    def run(self) -> int:
        self.claim_path = claim_execution_identity(
            self.execution_id,
            self.commit,
            [str(job["run_id"]) for job in self.plan["jobs"]],
        )
        try:
            self.prepare()
        except BaseException as exc:
            exclusive_json(
                self.claim_path.with_suffix(".failure.json"),
                {
                    "schema_version": "gtpj.v5_confirmation_001.controller_failure.v1",
                    "execution_claim": self.claim_path.as_posix(),
                    "failure_stage": "prepare",
                    "error": f"{type(exc).__name__}: {exc}",
                    "failed_at_unix": time.time(),
                },
            )
            raise
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        jobs_by_gpu = {
            gpu: [job for job in self.plan["jobs"] if int(job["gpu"]) == gpu]
            for gpu in (0, 1)
        }
        self.write_status("running")
        threads = [
            threading.Thread(target=self.worker, args=(gpu, jobs_by_gpu[gpu]), daemon=False)
            for gpu in (0, 1)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        retention_failed = False
        try:
            apply_checkpoint_retention(self.results)
        except BaseException as exc:
            retention_failed = True
            with self.status_lock:
                self.results.append(
                    {
                        "job_id": "CONTROLLER",
                        "group": "RETENTION",
                        "return_code": 98,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
        for result in self.results:
            if result.get("job_root"):
                atomic_json(Path(result["job_root"]) / "result.json", result)
                manifest = write_manifest(Path(result["job_root"]), result)
                result["artifact_manifest"] = manifest.as_posix()
                result["artifact_manifest_sha256"] = sha256_file(manifest)
        completed = (
            not retention_failed
            and len(self.results) == 15
            and all(item.get("return_code") == 0 for item in self.results)
        )
        final_state = "completed" if completed else ("stopped" if self.should_stop() else "partial_failed")
        self.write_status(final_state)
        return 0 if completed else 1


def main() -> int:
    args = parse_args()
    if sys.platform != "linux" and not args.validate_only:
        raise LaunchError("真实训练控制器只允许在 Linux 服务器运行。")
    commit = require_commit(args.commit, "--commit")
    if args.python.resolve() != SERVER_PYTHON.resolve():
        raise LaunchError(f"--python 必须是固定环境：{SERVER_PYTHON}")
    if not args.python.is_file():
        raise LaunchError("固定服务器 Python 不存在。")
    if args.data_source.resolve() != SERVER_DATA_SOURCE.resolve():
        raise LaunchError(f"--data-source 必须是固定数据根：{SERVER_DATA_SOURCE}")
    if args.runtime_root.resolve() != SERVER_RUNTIME_ROOT.resolve():
        raise LaunchError(f"--runtime-root 必须是固定运行根：{SERVER_RUNTIME_ROOT}")
    if args.warehouse_root.resolve() != SERVER_WAREHOUSE_ROOT.resolve():
        raise LaunchError(f"--warehouse-root 必须是固定 Warehouse 根：{SERVER_WAREHOUSE_ROOT}")
    repo_root = Path.cwd().resolve()
    if args.plan.resolve() != (repo_root / EXPERIMENT_DIR / "RUN_PLAN.json").resolve():
        raise LaunchError("--plan 必须指向冻结提交中的正式运行计划。")
    if args.data_manifest.resolve() != (repo_root / EXPERIMENT_DIR / "DATA_MANIFEST.json").resolve():
        raise LaunchError("--data-manifest 必须指向冻结提交中的数据清单。")
    validate_checkout(repo_root, commit)
    validate_bundle(args.bundle.resolve(), repo_root, commit)
    validate_launch_gate(repo_root, commit)
    plan = validate_plan(args.plan.resolve())
    for spec in GROUP_SPECS.values():
        validate_config(repo_root, spec)
    validate_data_manifest(args.data_manifest.resolve(), args.data_source)
    validate_legacy_data_isolation(args.data_source.resolve(), args.runtime_root.resolve())
    gpu_preflight = verify_server_gpu_preflight()
    if args.validate_only:
        print("validate-only-ok " + json.dumps(gpu_preflight, ensure_ascii=False, sort_keys=True))
        return 0
    gpu_locks = acquire_gpu_locks()
    try:
        verify_server_gpu_preflight()
        return Controller(args, repo_root, plan).run()
    finally:
        release_gpu_locks(gpu_locks)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LaunchError, OSError, subprocess.SubprocessError) as exc:
        print(f"启动失败：{exc}", file=sys.stderr)
        raise SystemExit(2)
