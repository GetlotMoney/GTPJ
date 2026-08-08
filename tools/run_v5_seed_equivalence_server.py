"""CONFIRM-002 五次同 seed GPU 诊断的服务器控制器。"""

from __future__ import annotations

import csv
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


SCHEMA_VERSION = "gtpj.v5_confirmation_002.run_plan.v1"
EXPERIMENT_ID = "V5-CONFIRM-002"
EXPERIMENT_BRANCH = "exp/v5/confirmation/confirm-002-v5-seed-equivalence"
EXPERIMENT_DIR = Path("experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence")
POST_REVIEW_ALLOWED_EXACT = {
    (EXPERIMENT_DIR / name).as_posix()
    for name in (
        "TASK_START.yaml",
        "agent_runtime.yaml",
        "AGENT_ACTIVITY.md",
        "MONITOR_HANDOFF.md",
        "agent_summary.md",
        "quality_check.md",
        "manifest.yaml",
    )
}
POST_REVIEW_ALLOWED_PREFIXES = (
    (EXPERIMENT_DIR / "agent_outputs").as_posix() + "/",
    (EXPERIMENT_DIR / "reviews").as_posix() + "/",
)
EXPECTED_JOB_IDS = [f"RUN-{index:03d}" for index in range(1, 6)]
EXPECTED_RUN_IDS = [f"V5CONF002-R1-RUN-{index:03d}" for index in range(1, 6)]
EXPECTED_GPUS = [0, 1, 0, 1, 0]
CONFIG_SHA256 = "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"
TRAINING_CANDIDATE_COMMIT = "534f1d132ed2ec842db05ce884446bff3f6ab8f8"
TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
HISTORICAL_V5_COMMIT = "4b259379d99c1a791442ea9e2fac0bb22b2411a9"
SCIENTIFIC_PATHS = (
    "model/MyModel.py",
    "train_GTPJ_CUB.py",
    "tools/v5_evaluation.py",
    "tools/v5_cub_data.py",
    "tools/v5_runtime.py",
    "tools/reproducibility.py",
    (EXPERIMENT_DIR / "config.yaml").as_posix(),
    (EXPERIMENT_DIR / "verify_seed_equivalence.py").as_posix(),
)
CONTROLLER_RELATIVE = Path("tools/run_v5_seed_equivalence_server.py")
SERVER_PYTHON = Path("/data/lby/.conda/envs/dvsr_gpu/bin/python")
SERVER_DATA_SOURCE = Path("/data/lby/projects/cv_project/GTPJ/data")
SERVER_RUNTIME_ROOT = Path("/data/lby/projects/cv_project/GTPJ/.runtime/confirmation")
SERVER_WAREHOUSE_ROOT = Path("/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/confirmation")
SERVER_CLAIM_ROOT = SERVER_WAREHOUSE_ROOT / ".gtpj_execution_claims"
SERVER_GPU_LOCK_ROOT = Path("/data/lby/projects/cv_project/GTPJ/.runtime/gpu_locks")
REQUIRED_INPUT_IDS = {
    "xlsa17_res101",
    "xlsa17_att_splits",
    "train_cls",
    "train_patches",
    "train_labels",
    "gpt55_sentences",
    "test_seen_features",
    "test_seen_patch_features",
    "test_seen_labels",
    "test_unseen_features",
    "test_unseen_patch_features",
    "test_unseen_labels",
}


class LaunchError(RuntimeError):
    """服务器开跑前或运行期间的硬失败。"""


def parse_args() -> Any:
    import argparse

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--final-commit", required=True)
    parser.add_argument("--reviewed-controller-commit", required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--warehouse-root", type=Path, required=True)
    parser.add_argument("--claim-root", type=Path, required=True)
    parser.add_argument("--data-source", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--data-manifest", type=Path, required=True)
    parser.add_argument("--review-pack", type=Path, required=True)
    parser.add_argument("--probe-evidence", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def _git(cwd: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise LaunchError(result.stderr.strip() or "Git 命令失败。")
    return result.stdout.strip()


def require_commit(value: str, label: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise LaunchError(f"{label} 必须是 40 位小写 Git commit。")
    return value


def require_tracked_runtime_file(
    repo_root: Path, supplied_path: Path, relative_path: Path
) -> Path:
    """运行计划和数据清单只能取自最终冻结提交，不能由外部文件替换。"""

    expected = (repo_root / relative_path).resolve(strict=True)
    supplied = supplied_path.resolve(strict=True)
    if supplied != expected:
        raise LaunchError(f"运行身份文件必须来自最终 checkout：{relative_path.as_posix()}")
    relative = relative_path.as_posix()
    if _git(repo_root, "hash-object", relative) != _git(repo_root, "rev-parse", f"HEAD:{relative}"):
        raise LaunchError(f"运行身份文件与最终 Git blob 不一致：{relative}")
    return expected


def verify_post_review_boundary(repo_root: Path, reviewed_commit: str, final_commit: str) -> None:
    """最终冻结只能补审核/启动记录，不能重写已审核代码和实验身份。"""

    reviewed = require_commit(reviewed_commit, "reviewed_commit")
    final = require_commit(final_commit, "final_commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed, final],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if ancestor.returncode != 0:
        raise LaunchError("最终冻结提交不是已审核控制器提交的后代。")
    changed = _git(repo_root, "diff", "--name-only", f"{reviewed}..{final}").splitlines()
    forbidden = [
        path
        for path in changed
        if path not in POST_REVIEW_ALLOWED_EXACT
        and not any(path.startswith(prefix) for prefix in POST_REVIEW_ALLOWED_PREFIXES)
    ]
    if forbidden:
        raise LaunchError("审核后出现禁止改动：" + ", ".join(sorted(forbidden)))


def verify_reviewed_controller_checkout(
    controller_repo: Path, reviewed_commit: str, controller_relative: Path
) -> None:
    """控制器必须从已审核提交运行，不能让最终提交里的篡改版自我放行。"""

    reviewed = require_commit(reviewed_commit, "reviewed_commit")
    if _git(controller_repo, "rev-parse", "HEAD") != reviewed:
        raise LaunchError("控制器没有从已审核提交运行。")
    if _git(controller_repo, "status", "--porcelain", "--untracked-files=all"):
        raise LaunchError("控制器 checkout 不是干净状态。")
    relative = controller_relative.as_posix()
    disk_blob = _git(controller_repo, "hash-object", relative)
    reviewed_blob = _git(controller_repo, "rev-parse", f"{reviewed}:{relative}")
    if disk_blob != reviewed_blob:
        raise LaunchError("控制器磁盘内容与已审核 Git blob 不一致。")


def validate_final_checkout(
    repo_root: Path, final_commit: str, reviewed_controller_commit: str
) -> None:
    final = require_commit(final_commit, "final_commit")
    reviewed = require_commit(reviewed_controller_commit, "reviewed_controller_commit")
    if _git(repo_root, "rev-parse", "HEAD") != final:
        raise LaunchError("最终运行 checkout 的 HEAD 不匹配。")
    if _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD") != EXPERIMENT_BRANCH:
        raise LaunchError("最终运行 checkout 没有停在命名实验分支。")
    if _git(repo_root, "status", "--porcelain", "--untracked-files=all"):
        raise LaunchError("最终运行 checkout 不是干净状态。")
    verify_post_review_boundary(repo_root, reviewed, final)
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", TRAINING_CANDIDATE_COMMIT, final],
        cwd=repo_root,
        capture_output=True,
    )
    if ancestor.returncode != 0:
        raise LaunchError("最终运行提交不是训练修复候选的后代。")
    validate_scientific_identity(repo_root, TRAINING_CANDIDATE_COMMIT)
    if _git(repo_root, "rev-parse", f"{final}:{CONTROLLER_RELATIVE.as_posix()}") != _git(
        repo_root, "rev-parse", f"{reviewed}:{CONTROLLER_RELATIVE.as_posix()}"
    ):
        raise LaunchError("最终冻结提交修改了已审核控制器。")


def _run_gate(repo_root: Path, *arguments: str) -> None:
    result = subprocess.run(
        [str(SERVER_PYTHON), str(repo_root / "workflow/gtpj_workflow.py"), *arguments],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise LaunchError(result.stderr.strip() or result.stdout.strip() or "workflow 开跑门失败。")


def validate_launch_gate(repo_root: Path, review_pack: Path, reviewed_commit: str) -> None:
    binding_path = review_pack / "REVIEW_BINDING.json"
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaunchError("代码审核包缺少可读的 REVIEW_BINDING.json。") from exc
    if binding.get("reviewed_commit") != reviewed_commit:
        raise LaunchError("代码审核包没有绑定已审核控制器提交。")
    if binding.get("review_tier") != "strict-3" or binding.get("decisions") != ["pass", "pass", "pass"]:
        raise LaunchError("代码审核包没有完成三路 strict-3 通过。")
    agent_runtime = repo_root / EXPERIMENT_DIR / "agent_runtime.yaml"
    matrix = repo_root / EXPERIMENT_DIR / "PARAMETER_MATRIX.csv"
    _run_gate(repo_root, "validate-ai-cross-review", "--path", str(review_pack))
    _run_gate(repo_root, "validate-agent-runtime", "--path", str(agent_runtime))
    _run_gate(repo_root, "multi-agent-preflight", "--path", str(agent_runtime))
    _run_gate(repo_root, "validate-parameter-matrix", "--path", str(matrix), "--expected-jobs", "5", "--require-ready")
    _run_gate(repo_root, "validate-experiment-base", "--path", str(repo_root / EXPERIMENT_DIR))


def capture_environment(python: Path) -> dict[str, Any]:
    script = (
        "import json,platform,torch; "
        "print(json.dumps({'python':platform.python_version(),'python_executable':__import__('sys').executable,"
        "'torch':torch.__version__,'cuda':torch.version.cuda,'cudnn':torch.backends.cudnn.version(),"
        "'cuda_available':torch.cuda.is_available(),'cuda_device_count':torch.cuda.device_count(),"
        "'devices':[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],"
        "'strict_determinism':torch.are_deterministic_algorithms_enabled(),"
        "'cudnn_benchmark':torch.backends.cudnn.benchmark},sort_keys=True))"
    )
    result = subprocess.run(
        [str(python), "-B", "-c", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    if result.returncode != 0:
        raise LaunchError("固定 Python 环境信息读取失败。")
    payload = json.loads(result.stdout)
    if payload.get("cuda_available") is not True or int(payload.get("cuda_device_count", 0)) != 2:
        raise LaunchError("固定 Python 没有精确看到两张 CUDA GPU。")
    return payload


def validate_bwrap_isolation(python: Path, data_source: Path, runtime_root: Path) -> None:
    bwrap = Path("/usr/bin/bwrap")
    if not bwrap.is_file():
        raise LaunchError("服务器缺少 /usr/bin/bwrap。")
    runtime_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".confirm002-bwrap-", dir=runtime_root) as temporary:
        root = Path(temporary)
        data_mount = root / "data"
        log_mount = root / "train_log"
        data_mount.mkdir()
        log_mount.mkdir()
        probe_name = f".gtpj-confirm002-write-probe-{os.getpid()}"
        script = (
            "from pathlib import Path; "
            f"data=Path({str(data_mount)!r}); log=Path({str(log_mount)!r}); "
            "assert (data/'cache/CUB_train_labels.pt').is_file(); "
            f"target=data/{probe_name!r}; "
            "\ntry:\n target.write_text('forbidden',encoding='utf-8')\n"
            "except OSError:\n pass\n"
            "else:\n raise SystemExit('data write unexpectedly succeeded')\n"
            "(log/'ok').write_text('ok',encoding='utf-8')"
        )
        command = [
            str(bwrap), "--die-with-parent", "--ro-bind", "/", "/", "--dev-bind", "/dev", "/dev",
            "--proc", "/proc", "--tmpfs", "/tmp", "--ro-bind", str(data_source), str(data_mount),
            "--bind", str(log_mount), str(log_mount), str(python), "-B", "-c", script,
        ]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0 or not (log_mount / "ok").is_file() or (data_source / probe_name).exists():
            raise LaunchError(result.stderr.strip() or result.stdout.strip() or "bwrap 只读隔离失败。")


def validate_plan(path: Path) -> dict[str, Any]:
    """读取并锁死五次 same-seed 任务，防止临跑时改次数、seed 或 GPU。"""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaunchError(f"RUN_PLAN.json 无法读取：{exc}") from exc
    if not isinstance(payload, dict):
        raise LaunchError("RUN_PLAN.json 顶层必须是对象。")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise LaunchError("RUN_PLAN.json schema_version 不匹配。")
    if payload.get("experiment_id") != EXPERIMENT_ID:
        raise LaunchError("RUN_PLAN.json experiment_id 不匹配。")
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != 5:
        raise LaunchError("CONFIRM-002 必须且只能包含 5 个任务。")
    if [job.get("job_id") for job in jobs if isinstance(job, dict)] != EXPECTED_JOB_IDS:
        raise LaunchError("RUN_PLAN.json 必须按 RUN-001..RUN-005 排列。")
    if [job.get("run_id") for job in jobs] != EXPECTED_RUN_IDS:
        raise LaunchError("RUN_PLAN.json 的 5 个 run_id 必须唯一且使用 R1 身份。")
    if [job.get("attempt") for job in jobs] != list(range(1, 6)):
        raise LaunchError("RUN_PLAN.json attempt 必须为 1..5。")
    if [job.get("gpu") for job in jobs] != EXPECTED_GPUS:
        raise LaunchError("RUN_PLAN.json GPU 必须按 0,1,0,1,0 分成三波。")
    if {job.get("seed") for job in jobs} != {5}:
        raise LaunchError("CONFIRM-002 五次必须全部使用原始 seed=5。")
    return payload


def validate_matrix(
    path: Path, plan: dict[str, Any], config_sha256: str
) -> list[dict[str, str]]:
    """参数表必须与五次计划逐行一致，且代码修复不能冒充配置改动。"""

    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if len(rows) != 5:
        raise LaunchError("PARAMETER_MATRIX.csv 必须精确包含 5 行。")
    jobs = plan["jobs"]
    result_fields = (
        "run_start_receipt_ref",
        "run_start_receipt_sha256",
        "run_command_sha256",
        "run_log_sha256",
        "run_exit_code",
        "U",
        "S",
        "H",
        "ZS",
        "best_epoch",
        "decision",
        "artifact_ref",
        "artifact_manifest_sha256",
    )
    for index, (row, job) in enumerate(zip(rows, jobs, strict=True)):
        expected_repeat = "" if index == 0 else "RUN-001"
        expected = {
            "job_id": job["job_id"],
            "work_item_id": EXPERIMENT_ID,
            "job_kind": "confirmation",
            "status": "frozen",
            "group": "REPAIRED_CURRENT",
            "base_version": "v5",
            "base_config_sha256": config_sha256,
            "code_ref": "model/v5-template-v1",
            "config_snapshot_ref": "config.yaml",
            "seed": "5",
            "changed_parameters": "{}",
            "config_fingerprint": config_sha256,
            "repeat_of": expected_repeat,
            "run_id": job["run_id"],
        }
        mismatches = [key for key, value in expected.items() if row.get(key, "") != value]
        if mismatches:
            raise LaunchError(
                f"{job['job_id']} 参数矩阵与冻结计划不一致：" + ", ".join(mismatches)
            )
        try:
            changed = json.loads(row["changed_parameters"])
        except json.JSONDecodeError as exc:
            raise LaunchError(f"{job['job_id']} changed_parameters 不是 JSON。") from exc
        if changed != {}:
            raise LaunchError(f"{job['job_id']} 配置实际未变，changed_parameters 必须为 {{}}。")
        populated = [field for field in result_fields if row.get(field, "")]
        if populated:
            raise LaunchError(f"{job['job_id']} 开跑前不得提前填写结果字段：{populated}")
    return rows


def validate_bundle(
    bundle: Path,
    repo_root: Path,
    commit: str,
    *,
    required_commits: list[str],
    expected_sha256: str | None = None,
) -> None:
    """验证 bundle 的分支尖端和所有后续运行需要的提交对象。"""

    if not bundle.is_file():
        raise LaunchError(f"Git bundle 不存在：{bundle}")
    if expected_sha256 is not None and sha256_file(bundle) != expected_sha256:
        raise LaunchError("Git bundle SHA256 与冻结值不一致。")
    verified = subprocess.run(
        ["git", "bundle", "verify", str(bundle)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if verified.returncode != 0:
        raise LaunchError(f"Git bundle verify 失败：{verified.stderr.strip()}")
    heads = subprocess.run(
        ["git", "bundle", "list-heads", str(bundle)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    expected_ref = f"refs/heads/{EXPERIMENT_BRANCH}"
    refs = {
        parts[1]: parts[0]
        for line in heads
        if len(parts := line.split(maxsplit=1)) == 2
    }
    if refs.get(expected_ref) != commit:
        raise LaunchError("Git bundle 的实验分支没有精确指向开跑提交。")

    with tempfile.TemporaryDirectory(prefix="gtpj-confirm002-bundle-") as temporary:
        probe = Path(temporary) / "probe"
        cloned = subprocess.run(
            ["git", "clone", "--quiet", str(bundle), str(probe)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if cloned.returncode != 0:
            raise LaunchError(f"Git bundle 隔离克隆失败：{cloned.stderr.strip()}")
        for required in required_commits:
            exists = subprocess.run(
                ["git", "cat-file", "-e", f"{required}^{{commit}}"],
                cwd=probe,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if exists.returncode != 0:
                raise LaunchError(f"Git bundle 缺少任务代码提交：{required}")


def clone_clean_checkout(bundle: Path, destination: Path, commit: str) -> None:
    """为单个 RUN 新建不可复用的精确提交代码副本。"""

    if destination.exists():
        raise LaunchError(f"任务代码目录已经存在，拒绝复用：{destination}")
    cloned = subprocess.run(
        ["git", "clone", "--quiet", str(bundle), str(destination)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if cloned.returncode != 0:
        raise LaunchError(f"任务代码克隆失败：{cloned.stderr.strip()}")
    checked = subprocess.run(
        ["git", "checkout", "--detach", commit],
        cwd=destination,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if checked.returncode != 0:
        raise LaunchError(f"任务代码 checkout 失败：{checked.stderr.strip()}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    if head != commit or status:
        raise LaunchError("任务代码副本不是精确、干净的开跑提交。")


def validate_scientific_identity(
    repo_root: Path, reference_commit: str = TRAINING_CANDIDATE_COMMIT
) -> None:
    """最终冻结和每个任务副本都必须保留 534f1d1 的科学代码字节。"""

    for relative in SCIENTIFIC_PATHS:
        if _git(repo_root, "rev-parse", f"HEAD:{relative}") != _git(
            repo_root, "rev-parse", f"{reference_commit}:{relative}"
        ):
            raise LaunchError(f"科学代码或配置在审核后发生变化：{relative}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_data_manifest(path: Path, data_source: Path) -> dict[str, Any]:
    """逐文件核对数据内容，并对 Tensor 额外核对形状和类型。"""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LaunchError(f"DATA_MANIFEST.json 无法读取：{exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "gtpj.v5.data_manifest/v1":
        raise LaunchError("DATA_MANIFEST.json schema_version 不匹配。")
    if payload.get("dataset") != "CUB":
        raise LaunchError("CONFIRM-002 只允许 CUB 数据。")
    files = payload.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise LaunchError("DATA_MANIFEST.json files 必须是对象列表。")
    ids = [item.get("id") for item in files]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_INPUT_IDS:
        raise LaunchError("DATA_MANIFEST.json 必须精确列出 12 份冻结输入。")

    root = data_source.resolve(strict=True)
    tensor_items: list[tuple[Path, dict[str, Any]]] = []
    for item in files:
        relative = Path(str(item.get("relative_path", "")))
        if relative.is_absolute():
            raise LaunchError(f"数据清单只允许相对路径：{relative}")
        actual = (root / relative).resolve(strict=True)
        if not actual.is_relative_to(root) or not actual.is_file():
            raise LaunchError(f"数据文件逃出冻结根目录：{relative}")
        if actual.stat().st_size != int(item.get("size_bytes", -1)):
            raise LaunchError(f"数据文件大小不匹配：{relative}")
        if sha256_file(actual) != item.get("sha256"):
            raise LaunchError(f"数据文件 SHA256 不匹配：{relative}")
        if item.get("shape") is None and item.get("dtype") is None:
            continue
        tensor_items.append((actual, item))

    if tensor_items:
        import torch

        for actual, item in tensor_items:
            tensor = torch.load(actual, map_location="cpu", weights_only=True, mmap=True)
            if not isinstance(tensor, torch.Tensor):
                raise LaunchError(f"冻结 Tensor 文件内容类型错误：{item['relative_path']}")
            if list(tensor.shape) != item.get("shape"):
                raise LaunchError(f"冻结 Tensor 形状不匹配：{item['relative_path']}")
            if str(tensor.dtype) != item.get("dtype"):
                raise LaunchError(f"冻结 Tensor dtype 不匹配：{item['relative_path']}")
    return payload


def build_training_command(
    *,
    python: Path,
    code_root: Path,
    config: Path,
    job_root: Path,
    data_source: Path,
) -> list[str]:
    """把旧相对路径入口放进只读数据、独立输出的 bubblewrap 沙箱。"""

    return [
        "/usr/bin/bwrap",
        "--die-with-parent",
        "--new-session",
        "--unshare-net",
        "--ro-bind",
        "/",
        "/",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--ro-bind",
        str(data_source),
        str(code_root / "data"),
        "--bind",
        str(job_root / "train_log"),
        str(code_root / "train_log"),
        "--chdir",
        str(code_root),
        str(python),
        "-B",
        "-u",
        str(code_root / "train_GTPJ_CUB.py"),
        "--config",
        str(config),
    ]


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_launch_spec(
    *,
    python: Path,
    code_root: Path,
    config: Path,
    job_root: Path,
    data_source: Path,
    physical_gpu: int,
) -> dict[str, Any]:
    """生成命令和包含物理 GPU 映射的完整启动身份。"""

    if physical_gpu not in (0, 1):
        raise LaunchError("CONFIRM-002 只允许物理 GPU 0 或 1。")
    argv = build_training_command(
        python=python,
        code_root=code_root,
        config=config,
        job_root=job_root,
        data_source=data_source,
    )
    env_delta = {
        "CUDA_VISIBLE_DEVICES": str(physical_gpu),
        "PYTHONUNBUFFERED": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }
    return {
        "argv": argv,
        "cwd": str(code_root),
        "env_delta": env_delta,
        "command_sha256": _sha256_json(argv),
        "launch_identity_sha256": _sha256_json(
            {
                "argv": argv,
                "cwd": str(code_root),
                "env_delta": env_delta,
                "python": str(python),
                "config": str(config),
            }
        ),
    }


NUMBER = r"[0-9]+(?:\.[0-9]+)?"
SUMMARY_RE = re.compile(
    rf"最佳 epoch=(?P<epoch>[0-9]+)，U=(?P<U>{NUMBER})%，"
    rf"S=(?P<S>{NUMBER})%，H=(?P<H>{NUMBER})%，ZS=(?P<ZS>{NUMBER})%。"
)


def parse_metrics(text: str) -> dict[str, Any]:
    """只接受训练结束时的中文最佳指标行。"""

    matches = list(SUMMARY_RE.finditer(text))
    if not matches:
        raise LaunchError("训练日志缺少最终最佳 U/S/H/ZS 汇总。")
    match = matches[-1]
    return {
        "best_epoch": int(match.group("epoch")),
        "U": float(match.group("U")),
        "S": float(match.group("S")),
        "H": float(match.group("H")),
        "ZS": float(match.group("ZS")),
    }


def validate_formal_probe_payload(payload: dict[str, Any], commit: str) -> dict[str, Any]:
    """拒绝任何未绑定最终提交、无 CUDA 或未完成 RNG 对齐的 probe。"""

    required_true = [
        "formal_candidate_check_requested",
        "formal_candidate_identity_ok",
        "cuda_available",
        "post_model_cpu_rng_equal",
        "post_model_cuda_rng_equal",
        "first_three_batches_equal",
        "config_matches_expected_sha256",
        "candidate_model_matches_head",
    ]
    failures = [key for key in required_true if payload.get(key) is not True]
    if payload.get("status") != "PASS":
        failures.append("status")
    if payload.get("git_head") != commit:
        failures.append("git_head")
    if payload.get("git_branch") != EXPERIMENT_BRANCH:
        failures.append("git_branch")
    if payload.get("git_dirty") is not False:
        failures.append("git_dirty")
    if int(payload.get("cuda_device_count", 0)) < 2:
        failures.append("cuda_device_count")
    if payload.get("active_state_mismatches") != []:
        failures.append("active_state_mismatches")
    if payload.get("dead_parameter_names_present") is not False:
        failures.append("dead_parameter_names_present")
    if failures:
        raise LaunchError("正式零步探针未通过：" + ", ".join(sorted(set(failures))))
    return payload


def run_formal_probe(
    *,
    python: Path,
    repo_root: Path,
    commit: str,
    evidence_path: Path,
    probe_path: Path | None = None,
) -> dict[str, Any]:
    """在最终干净提交上执行真实 CUDA/RNG probe，并保存原始 JSON。"""

    probe = probe_path or (repo_root / EXPERIMENT_DIR / "verify_seed_equivalence.py")
    result = subprocess.run(
        [
            str(python),
            "-B",
            "-u",
            str(probe),
            "--repository-root",
            str(repo_root),
            "--formal-candidate-commit",
            commit,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
    )
    if result.returncode != 0:
        raise LaunchError(result.stderr.strip() or result.stdout.strip() or "正式零步 probe 失败。")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LaunchError("正式零步 probe 没有返回单一 JSON。") from exc
    if not isinstance(payload, dict):
        raise LaunchError("正式零步 probe 顶层不是对象。")
    validate_formal_probe_payload(payload, commit)
    atomic_json(evidence_path, payload)
    return payload


def run_waves(jobs: list[dict[str, Any]], run_one, should_stop) -> list[dict[str, Any]]:
    """每波最多一张卡一个任务；整波成功后才允许派发下一波。"""

    queues = {
        gpu: [job for job in jobs if job["gpu"] == gpu]
        for gpu in (0, 1)
    }
    results: list[dict[str, Any]] = []
    results_lock = threading.Lock()

    def worker(job: dict[str, Any]) -> None:
        try:
            result = run_one(job)
        except BaseException as exc:  # 控制器必须把启动异常也封存成失败结果。
            result = {
                "job_id": job.get("job_id", "unknown"),
                "return_code": 99,
                "error": f"{type(exc).__name__}: {exc}",
            }
        with results_lock:
            results.append(result)

    wave_count = max(len(queue) for queue in queues.values())
    for wave_index in range(wave_count):
        if should_stop():
            break
        wave = [
            queues[gpu][wave_index]
            for gpu in (0, 1)
            if wave_index < len(queues[gpu])
        ]
        before = len(results)
        threads = [threading.Thread(target=worker, args=(job,), daemon=False) for job in wave]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        wave_results = results[before:]
        if should_stop() or any(int(item.get("return_code", 99)) != 0 for item in wave_results):
            break
    return results


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def file_record(path: Path, root: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file() or not resolved.is_relative_to(root_resolved):
        raise LaunchError(f"证据文件不存在、是软链接或逃离任务目录：{path}")
    return {
        "relative_path": resolved.relative_to(root_resolved).as_posix(),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def write_artifact_manifest(job_root: Path, result: dict[str, Any]) -> Path:
    artifacts: dict[str, list[dict[str, Any]]] = {}
    candidates = {
        "launch_receipt": [job_root / "receipts" / "start.json"],
        "finish_receipt": [job_root / "receipts" / "finish.json"],
        "sealed_stdout_log": [job_root / "logs" / "training.log"],
        "config": [job_root / "config.yaml"],
        "run_result": [job_root / "result.json"],
        "internal_training_log": sorted((job_root / "train_log").rglob("training_log*.txt")),
        "best_model": sorted((job_root / "train_log").rglob("best_model*.pth")),
        "full_checkpoint": sorted((job_root / "train_log").rglob("ckpt_full*.pth")),
    }
    for role, paths in candidates.items():
        records = [file_record(path, job_root) for path in paths if path.exists()]
        if records:
            artifacts[role] = records
    payload = {
        "schema_version": "gtpj.v5_confirmation_002.artifact_manifest.v1",
        "experiment_id": EXPERIMENT_ID,
        "execution_id": result["execution_id"],
        "job_id": result["job_id"],
        "run_id": result["run_id"],
        "pre_run_freeze_commit": result["pre_run_freeze_commit"],
        "config_sha256": result["config_sha256"],
        "metrics": result.get("metrics"),
        "return_code": result["return_code"],
        "not_confirmation_evidence": True,
        "artifacts": artifacts,
    }
    path = job_root / "artifact_manifest.json"
    atomic_json(path, payload)
    return path


def acquire_gpu_locks(lock_root: Path, gpu_ids: tuple[int, ...]) -> list[Any]:
    """锁定 GPU；旧的空锁文件可以继续使用，真正的锁由内核 flock 决定。"""

    import fcntl

    lock_root.mkdir(parents=True, exist_ok=True)
    handles: list[Any] = []
    try:
        for gpu in gpu_ids:
            handle = (lock_root / f"gpu-{gpu}.lock").open("a+", encoding="utf-8")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                handle.close()
                raise
            handles.append(handle)
    except BaseException as exc:
        release_gpu_locks(handles)
        raise LaunchError("GPU 已被另一项受控实验锁定。") from exc
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


def claim_execution_identity(
    *,
    claim_root: Path,
    execution_id: str,
    commit: str,
    run_ids: list[str],
    bundle_sha256: str,
) -> Path:
    """一次性领取 execution_id 和全部 run_id，历史失败也不能覆盖重用。"""

    import fcntl

    claim_root.mkdir(parents=True, exist_ok=True)
    lock_path = claim_root / ".claims.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            used_run_ids: set[str] = set()
            for path in sorted(claim_root.glob("*.json")):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise LaunchError(f"已有运行 claim 无法读取：{path}") from exc
                if payload.get("execution_id") == execution_id:
                    raise LaunchError("execution_id 已被永久领取，拒绝覆盖。")
                used_run_ids.update(str(value) for value in payload.get("run_ids", []))
            duplicates = sorted(set(run_ids) & used_run_ids)
            if duplicates:
                raise LaunchError("run_id 已被永久领取：" + ", ".join(duplicates))
            claim = claim_root / f"{execution_id}.json"
            payload = {
                "schema_version": "gtpj.v5_confirmation_002.execution_claim.v1",
                "experiment_id": EXPERIMENT_ID,
                "execution_id": execution_id,
                "pre_run_freeze_commit": commit,
                "bundle_sha256": bundle_sha256,
                "run_ids": list(run_ids),
                "claimed_at_unix": time.time(),
            }
            try:
                with claim.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
                    stream.write("\n")
            except FileExistsError as exc:
                raise LaunchError("execution claim 已存在，拒绝覆盖。") from exc
            return claim
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def verify_server_gpu_preflight() -> dict[str, Any]:
    """确认两张指定 4090 都存在且当前没有计算进程。"""

    inventory = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,uuid,driver_version,memory.total,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if inventory.returncode != 0:
        raise LaunchError("nvidia-smi GPU 清单查询失败。")
    rows = [line.strip() for line in inventory.stdout.splitlines() if line.strip()]
    indexes: set[int] = set()
    for row in rows:
        parts = [part.strip() for part in row.split(",")]
        if len(parts) < 2:
            raise LaunchError("nvidia-smi GPU 清单格式异常。")
        indexes.add(int(parts[0]))
        if int(parts[0]) in (0, 1) and "4090" not in parts[1]:
            raise LaunchError(f"GPU {parts[0]} 不是冻结的 RTX 4090。")
    if indexes != {0, 1}:
        raise LaunchError("服务器必须精确可见 GPU 0 和 GPU 1。")

    processes = subprocess.run(
        [
            "nvidia-smi",
            "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if processes.returncode != 0:
        raise LaunchError("nvidia-smi 计算进程查询失败。")
    active = [line.strip() for line in processes.stdout.splitlines() if line.strip()]
    if active:
        raise LaunchError("GPU 上仍有计算进程，拒绝抢占：" + " | ".join(active))
    return {"gpu_inventory": rows, "active_compute_processes": []}


class Controller:
    def __init__(
        self,
        args: Any,
        repo_root: Path,
        plan: dict[str, Any],
        probe_path: Path,
        environment_evidence: dict[str, Any],
    ) -> None:
        self.args = args
        self.repo_root = repo_root.resolve()
        self.plan = plan
        self.commit = require_commit(str(args.final_commit), "--final-commit")
        self.reviewed_controller_commit = require_commit(
            str(args.reviewed_controller_commit), "--reviewed-controller-commit"
        )
        self.training_candidate_commit = TRAINING_CANDIDATE_COMMIT
        self.execution_id = f"V5-CONFIRM-002-{self.commit[:12]}"
        self.runtime_root = args.runtime_root.resolve()
        self.warehouse_root = args.warehouse_root.resolve()
        self.execution_root = self.runtime_root / self.execution_id
        self.warehouse_execution = self.warehouse_root / self.execution_id
        self.status_path = self.execution_root / "status.json"
        self.stop_path = self.execution_root / "STOP"
        self.config_sha256 = CONFIG_SHA256
        self.bundle_sha256 = sha256_file(args.bundle)
        self.data_manifest_sha256 = sha256_file(args.data_manifest)
        self.probe_sha256 = sha256_file(probe_path)
        self.environment_evidence = environment_evidence
        self.stop_requested = threading.Event()
        self.status_lock = threading.Lock()
        self.launch_lock = threading.Lock()
        self.results: list[dict[str, Any]] = []
        self.running: dict[int, subprocess.Popen[Any]] = {}
        self.claim_path: Path | None = None

    def status_payload(self, state: str) -> dict[str, Any]:
        completed_ids = {str(result.get("job_id")) for result in self.results}
        cancelled = [
            str(job["job_id"])
            for job in self.plan["jobs"]
            if str(job["job_id"]) not in completed_ids
        ]
        return {
            "schema_version": "gtpj.v5_confirmation_002.status.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "status": state,
            "pre_run_freeze_commit": self.commit,
            "reviewed_controller_commit": self.reviewed_controller_commit,
            "updated_at_unix": time.time(),
            "stop_file": self.stop_path.as_posix(),
            "execution_claim": self.claim_path.as_posix() if self.claim_path else None,
            "results": sorted(self.results, key=lambda item: str(item.get("job_id", ""))),
            "not_dispatched_or_cancelled_jobs": cancelled,
        }

    def write_status(self, state: str) -> None:
        with self.status_lock:
            atomic_json(self.status_path, self.status_payload(state))

    def request_stop(self, _signum: int, _frame: Any) -> None:
        self.stop_requested.set()
        with self.status_lock:
            running = list(self.running.values())
        for process in running:
            self._terminate_process(process)

    def prepare(self) -> None:
        if self.execution_root.exists() or self.warehouse_execution.exists():
            raise LaunchError("本次 execution 目录已经存在，拒绝覆盖或复用。")
        self.execution_root.mkdir(parents=True)
        self.warehouse_execution.mkdir(parents=True)
        self.write_status("prepared")

    def run(self) -> int:
        self.claim_path = claim_execution_identity(
            claim_root=self.args.claim_root,
            execution_id=self.execution_id,
            commit=self.commit,
            run_ids=[str(job["run_id"]) for job in self.plan["jobs"]],
            bundle_sha256=self.bundle_sha256,
        )
        self.prepare()
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self.request_stop)
            signal.signal(signal.SIGINT, self.request_stop)
        self.write_status("running")

        def run_and_record(job: dict[str, Any]) -> dict[str, Any]:
            result = self.run_one_safely(job)
            with self.status_lock:
                self.results.append(result)
            self.write_status("running")
            return result

        run_waves(self.plan["jobs"], run_and_record, self.should_stop)
        completed = len(self.results) == 5 and all(
            int(result.get("return_code", 99)) == 0 for result in self.results
        )
        final_state = "completed" if completed else ("stopped" if self.should_stop() else "partial_failed")
        self.write_status(final_state)
        return 0 if completed else 1

    def should_stop(self) -> bool:
        return self.stop_requested.is_set() or self.stop_path.exists()

    @staticmethod
    def _terminate_process(process: subprocess.Popen[Any]) -> None:
        if process.poll() is not None:
            return
        if os.name == "nt":
            process.terminate()
        else:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def execute_prepared_job(
        self,
        job: dict[str, Any],
        job_root: Path,
        code_root: Path,
        launch_spec: dict[str, Any],
    ) -> dict[str, Any]:
        """运行一个已准备好的任务，并在返回前封存收据、结果和制品清单。"""

        start_receipt = {
            "schema_version": "gtpj.v5_confirmation_002.start_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": str(job["job_id"]),
            "run_id": str(job["run_id"]),
            "attempt": int(job["attempt"]),
            "seed": int(job["seed"]),
            "physical_gpu": int(job["gpu"]),
            "not_confirmation_evidence": True,
            "pre_run_freeze_commit": self.commit,
            "reviewed_controller_commit": self.reviewed_controller_commit,
            "config_sha256": self.config_sha256,
            "bundle_sha256": self.bundle_sha256,
            "data_manifest_sha256": self.data_manifest_sha256,
            "formal_probe_sha256": self.probe_sha256,
            "argv": launch_spec["argv"],
            "cwd": launch_spec["cwd"],
            "env_delta": launch_spec["env_delta"],
            "command_sha256": launch_spec["command_sha256"],
            "launch_identity_sha256": launch_spec["launch_identity_sha256"],
            "environment": self.environment_evidence,
            "started_at_unix": time.time(),
        }
        start_path = job_root / "receipts" / "start.json"
        atomic_json(start_path, start_receipt)
        start_sha = sha256_file(start_path)
        log_path = job_root / "logs" / "training.log"
        environment = os.environ.copy()
        environment.update({str(key): str(value) for key, value in launch_spec["env_delta"].items()})
        environment["PYTHONIOENCODING"] = "utf-8"
        environment["PYTHONUTF8"] = "1"
        process: subprocess.Popen[Any] | None = None
        with log_path.open("w", encoding="utf-8", newline="\n") as log_handle:
            log_handle.write(f"GTPJ_PROCESS_START start_receipt_sha256={start_sha}\n")
            log_handle.flush()
            with self.launch_lock:
                if self.should_stop():
                    raise LaunchError(f"{job['job_id']} 在进程启动前收到停止信号。")
                process = subprocess.Popen(
                    launch_spec["argv"],
                    cwd=code_root,
                    env=environment,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                with self.status_lock:
                    self.running[int(job["gpu"])] = process
            while process.poll() is None:
                if self.should_stop():
                    self._terminate_process(process)
                time.sleep(0.2)
            process_return_code = int(process.returncode)
            if process_return_code != 0:
                self.stop_requested.set()
            log_handle.write(f"GTPJ_PROCESS_FINISH return_code={process_return_code}\n")
            log_handle.flush()
            os.fsync(log_handle.fileno())
        with self.status_lock:
            self.running.pop(int(job["gpu"]), None)

        metrics = None
        evidence_error = None
        if process_return_code == 0:
            try:
                metrics = parse_metrics(log_path.read_text(encoding="utf-8", errors="replace"))
                if not list((job_root / "train_log").rglob("training_log*.txt")):
                    raise LaunchError("训练成功返回但缺少内层训练日志。")
                if not list((job_root / "train_log").rglob("best_model*.pth")):
                    raise LaunchError("训练成功返回但缺少最佳模型。")
            except LaunchError as exc:
                evidence_error = str(exc)
        evidence_return_code = (
            0
            if process_return_code == 0 and evidence_error is None
            else (90 if process_return_code == 0 else process_return_code)
        )
        if evidence_return_code != 0:
            self.stop_requested.set()
        log_sha = sha256_file(log_path)
        finish = {
            "schema_version": "gtpj.v5_confirmation_002.finish_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": str(job["job_id"]),
            "run_id": str(job["run_id"]),
            "pre_run_freeze_commit": self.commit,
            "config_sha256": self.config_sha256,
            "start_receipt_sha256": start_sha,
            "command_sha256": launch_spec["command_sha256"],
            "launch_identity_sha256": launch_spec["launch_identity_sha256"],
            "training_log_sha256": log_sha,
            "process_pid": process.pid if process is not None else None,
            "process_return_code": process_return_code,
            "evidence_return_code": evidence_return_code,
            "metrics": metrics,
            "evidence_error": evidence_error,
            "finished_at_unix": time.time(),
        }
        atomic_json(job_root / "receipts" / "finish.json", finish)
        result = {
            "execution_id": self.execution_id,
            "job_id": str(job["job_id"]),
            "run_id": str(job["run_id"]),
            "gpu": int(job["gpu"]),
            "attempt": int(job["attempt"]),
            "seed": int(job["seed"]),
            "pre_run_freeze_commit": self.commit,
            "config_sha256": self.config_sha256,
            "process_return_code": process_return_code,
            "return_code": evidence_return_code,
            "metrics": metrics,
            "evidence_error": evidence_error,
            "job_root": job_root.as_posix(),
            "training_log_sha256": log_sha,
            "not_confirmation_evidence": True,
        }
        atomic_json(job_root / "result.json", result)
        manifest = write_artifact_manifest(job_root, result)
        result["artifact_manifest"] = manifest.as_posix()
        result["artifact_manifest_sha256"] = sha256_file(manifest)
        return result

    def run_one_safely(self, job: dict[str, Any]) -> dict[str, Any]:
        try:
            result = self.run_one(job)
            if int(result.get("return_code", 99)) != 0:
                with self.launch_lock:
                    self.stop_requested.set()
            return result
        except BaseException as exc:
            # 先在与 Popen 共用的锁内关总闸，再进行可能较慢的失败证据写入。
            with self.launch_lock:
                self.stop_requested.set()
            return self.persist_early_failure(job, exc)

    def run_one(self, job: dict[str, Any]) -> dict[str, Any]:
        """为一个 RUN 建立全新代码/输出目录，然后交给证据化进程执行。"""

        job_id = str(job["job_id"])
        job_root = self.warehouse_execution / job_id
        code_root = self.execution_root / "code" / job_id
        if job_root.exists() or code_root.exists():
            raise LaunchError(f"{job_id} 的代码或输出目录已存在，拒绝复用。")
        for relative in ("logs", "receipts", "train_log"):
            (job_root / relative).mkdir(parents=True, exist_ok=False)
        clone_clean_checkout(self.args.bundle, code_root, self.commit)
        validate_scientific_identity(code_root, self.training_candidate_commit)
        source_config = code_root / EXPERIMENT_DIR / "config.yaml"
        if sha256_file(source_config) != self.config_sha256:
            raise LaunchError(f"{job_id} 的冻结配置哈希不匹配。")
        config_copy = job_root / "config.yaml"
        shutil.copyfile(source_config, config_copy)
        if sha256_file(config_copy) != self.config_sha256:
            raise LaunchError(f"{job_id} 的证据配置复制后发生变化。")
        (code_root / "data").mkdir()
        (code_root / "train_log").mkdir()
        if _git(code_root, "status", "--porcelain", "--untracked-files=all"):
            raise LaunchError(f"{job_id} 建立挂载点后代码工作树不再干净。")
        launch_spec = build_launch_spec(
            python=self.args.python,
            code_root=code_root,
            config=source_config,
            job_root=job_root,
            data_source=self.args.data_source.resolve(),
            physical_gpu=int(job["gpu"]),
        )
        return self.execute_prepared_job(job, job_root, code_root, launch_spec)

    def persist_early_failure(
        self, job: dict[str, Any], error: BaseException
    ) -> dict[str, Any]:
        """即使进程尚未创建，也立即留下不可伪装成成功的完整证据。"""

        job_root = self.warehouse_execution / str(job["job_id"])
        for relative in ("logs", "receipts", "train_log"):
            (job_root / relative).mkdir(parents=True, exist_ok=True)
        error_text = f"{type(error).__name__}: {error}"
        log_path = job_root / "logs" / "training.log"
        if not log_path.exists():
            log_path.write_text("GTPJ_PRELAUNCH_FAILURE " + error_text + "\n", encoding="utf-8")
        finish = {
            "schema_version": "gtpj.v5_confirmation_002.finish_receipt.v1",
            "experiment_id": EXPERIMENT_ID,
            "execution_id": self.execution_id,
            "job_id": str(job["job_id"]),
            "run_id": str(job["run_id"]),
            "pre_run_freeze_commit": self.commit,
            "config_sha256": self.config_sha256,
            "process_return_code": None,
            "evidence_return_code": 99,
            "error": error_text,
            "finished_at_unix": time.time(),
        }
        atomic_json(job_root / "receipts" / "finish.json", finish)
        result = {
            "execution_id": self.execution_id,
            "job_id": str(job["job_id"]),
            "run_id": str(job["run_id"]),
            "gpu": int(job["gpu"]),
            "attempt": int(job["attempt"]),
            "seed": int(job["seed"]),
            "pre_run_freeze_commit": self.commit,
            "config_sha256": self.config_sha256,
            "process_return_code": None,
            "return_code": 99,
            "metrics": None,
            "error": error_text,
            "job_root": job_root.as_posix(),
            "training_log_sha256": sha256_file(log_path),
            "not_confirmation_evidence": True,
        }
        atomic_json(job_root / "result.json", result)
        manifest = write_artifact_manifest(job_root, result)
        returned = dict(result)
        returned["artifact_manifest"] = manifest.as_posix()
        returned["artifact_manifest_sha256"] = sha256_file(manifest)
        return returned


def main() -> int:
    args = parse_args()
    if sys.platform != "linux":
        raise LaunchError("CONFIRM-002 正式控制器只允许在 Linux 服务器运行。")
    fixed_paths = (
        (args.python, SERVER_PYTHON, "--python"),
        (args.data_source, SERVER_DATA_SOURCE, "--data-source"),
        (args.runtime_root, SERVER_RUNTIME_ROOT, "--runtime-root"),
        (args.warehouse_root, SERVER_WAREHOUSE_ROOT, "--warehouse-root"),
        (args.claim_root, SERVER_CLAIM_ROOT, "--claim-root"),
    )
    for actual, expected, label in fixed_paths:
        if actual.resolve() != expected.resolve():
            raise LaunchError(f"{label} 必须使用冻结服务器路径：{expected}")
    final_commit = require_commit(args.final_commit, "--final-commit")
    reviewed_commit = require_commit(args.reviewed_controller_commit, "--reviewed-controller-commit")
    repo_root = args.repo_root.resolve(strict=True)
    controller_repo = Path(__file__).resolve().parents[1]
    verify_reviewed_controller_checkout(controller_repo, reviewed_commit, CONTROLLER_RELATIVE)
    validate_final_checkout(repo_root, final_commit, reviewed_commit)
    plan_path = require_tracked_runtime_file(repo_root, args.plan, EXPERIMENT_DIR / "RUN_PLAN.json")
    data_manifest_path = require_tracked_runtime_file(
        repo_root,
        args.data_manifest,
        EXPERIMENT_DIR / "DATA_MANIFEST.json",
    )
    plan = validate_plan(plan_path)
    validate_matrix(repo_root / EXPERIMENT_DIR / "PARAMETER_MATRIX.csv", plan, CONFIG_SHA256)
    if sha256_file(repo_root / EXPERIMENT_DIR / "config.yaml") != CONFIG_SHA256:
        raise LaunchError("最终冻结配置哈希不匹配。")
    validate_bundle(
        args.bundle.resolve(strict=True),
        repo_root,
        final_commit,
        required_commits=[
            final_commit,
            reviewed_commit,
            TRAINING_CANDIDATE_COMMIT,
            TEMPLATE_COMMIT,
            HISTORICAL_V5_COMMIT,
        ],
        expected_sha256=args.bundle_sha256,
    )
    validate_data_manifest(data_manifest_path, args.data_source)
    validate_launch_gate(repo_root, args.review_pack.resolve(strict=True), reviewed_commit)
    verify_server_gpu_preflight()
    locks = acquire_gpu_locks(SERVER_GPU_LOCK_ROOT, (0, 1))
    try:
        gpu_evidence = verify_server_gpu_preflight()
        environment = capture_environment(args.python)
        validate_bwrap_isolation(args.python, args.data_source.resolve(), args.runtime_root.resolve())
        probe_payload = run_formal_probe(
            python=args.python,
            repo_root=repo_root,
            commit=final_commit,
            evidence_path=args.probe_evidence,
        )
        environment["gpu_preflight"] = gpu_evidence
        environment["formal_probe_status"] = probe_payload["status"]
        if args.validate_only:
            print(json.dumps({"status": "PASS", "final_commit": final_commit}, ensure_ascii=False))
            return 0
        controller = Controller(args, repo_root, plan, args.probe_evidence, environment)
        return controller.run()
    finally:
        release_gpu_locks(locks)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LaunchError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        raise SystemExit(1)
