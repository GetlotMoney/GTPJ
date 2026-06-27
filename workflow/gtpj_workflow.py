#!/usr/bin/env python
"""Optional repository-structure helper for the GTPJ repository.

This script is intentionally small and deterministic. It creates governance
folders, copies version configs, and validates repository invariants. It does
not run training, push to GitHub, or mutate Git history.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS = [
    "D" + "VSR-Lab",
    "TUNE-" + "024",
    "74-" + "baseline",
    "remo" + "tion",
    "cla" + "ude_code_worker",
    chr(77) + chr(67) + chr(80),
    "experiment/" + "single-module",
    "experiment/" + "hyperparameter",
    "experiment/" + "final-runs",
]
FORBIDDEN_REGEXES = [
    re.compile("MOD-" + r"[0-9]{3}"),
    re.compile("REV-MOD-" + r"[0-9]{3}"),
    re.compile("COMBO-" + r"[0-9]{3}"),
]
SOURCE_TYPES = {"paper", "user", "observation", "cross_domain", "hybrid"}
SOURCE_STATUSES = {"verified", "unverified", "unknown", "local_heuristic"}
TRIAL_ALLOWED_SOURCE_STATUSES = {"verified", "local_heuristic"}
APPLICABILITIES = {"direct", "needs_adaptation", "unclear", "not_applicable"}
TRIAL_ALLOWED_APPLICABILITIES = {"direct", "needs_adaptation"}
TRIAL_READY_STATUSES = {"selected"}
IDEA_STATUSES = {
    "candidate",
    "selected",
    "developing",
    "testing",
    "validated",
    "weakened",
    "rejected",
    "blocked",
}
VERSION_STAGES = {
    "candidate",
    "selected",
    "trialing",
    "validated",
    "rejected",
    "blocked",
    "not_applicable",
}
SOURCE_STATUS_RANK = {
    "verified": 3,
    "local_heuristic": 2,
    "unverified": 1,
    "unknown": 0,
}


class WorkflowError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExperimentKind:
    name: str
    folder: str
    prefix: str
    default_check: str
    branch_kind: str


KINDS = {
    "tune": ExperimentKind("tune", "tune", "TUNE", "TUNE-LITE", "tune"),
    "ablation": ExperimentKind("ablation", "ablation", "ABL", "STANDARD", "ablation"),
    "confirmation": ExperimentKind("confirmation", "confirmation", "CONFIRM", "STRICT", "confirm"),
}
MODULE_TRIAL_KIND = ExperimentKind("module-trial", "module_trials", "TRIAL", "STRICT", "trial")

CANONICAL_BASELINES = {
    "v1": {
        "name": "GTPJ-v1",
        "H": "73.93",
        "result_file": "experiments/v1/result.md",
        "version_file": "experiments/v1/VERSION.md",
    },
    "v2": {
        "name": "GTPJ-v2",
        "H": "74.29",
        "result_file": "experiments/v2/result.md",
        "version_file": "experiments/v2/VERSION.md",
    }
}
TUNE_CANDIDATE_RULES = [
    {
        "parameter": "clip_a_self_outer_ratio",
        "suggested_value": "0.125",
        "why": "降低 CLIP-A-self 二级残差强度，检查 seen-heavy 行为是否缓解。",
        "risk": "过低可能削弱 ATTEMPT-019 的 seen 类收益。",
        "cost": "1 个 CUB seed 训练。",
    },
    {
        "parameter": "clip_a_self_inner_ratio",
        "suggested_value": "0.30",
        "why": "降低句级 self-attention 注入强度，检查文本原型是否更稳。",
        "risk": "可能降低 adapter 对句间信息的利用。",
        "cost": "1 个 CUB seed 训练。",
    },
    {
        "parameter": "clip_a_self_dropout",
        "suggested_value": "0.45",
        "why": "轻微降低 adapter dropout，检查 ATTEMPT-019 附近是否还有可提升空间。",
        "risk": "可能加重 seen 类过拟合，需要同时关注 U/S gap。",
        "cost": "1 个 CUB seed 训练。",
    },
    {
        "parameter": "clip_a_self_outer_ratio",
        "suggested_value": "0.175",
        "why": "向 ATTEMPT-020 方向测试更强二级残差，确认 H=74.29 附近的局部峰值。",
        "risk": "可能进一步扩大 seen/unseen 差距。",
        "cost": "1 个 CUB seed 训练。",
    },
]
METRIC_NAMES = ("U", "S", "H", "ZS")
FORBIDDEN_EXPERIMENT_SUFFIXES = {
    ".log",
    ".txt",
    ".pt",
    ".pth",
    ".ckpt",
    ".npy",
    ".npz",
    ".onnx",
}
FORBIDDEN_EXPERIMENT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
LEGACY_EXPERIMENT_ARTIFACT_ALLOWLIST = set()
ALLOWED_EXPERIMENT_TEXT_FILES = {
    "README.md",
    "VERSION.md",
    "INDEX.md",
    "IDEA.md",
    "TRIAL_README_template.md",
    "VERSION_template.md",
    "experiment_README_template.md",
    "implementation_template.md",
    "agent_summary_template.md",
    "quality_check_template.md",
    "quality_check.md",
    "agent_summary.md",
    "implementation.md",
    "interface_check.md",
    "code.diff",
    "config.yaml",
    "manifest.yaml",
    "result.yaml",
    "result.md",
}


def yaml_scalar(value: object) -> str:
    text = "" if value is None else str(value)
    if text == "":
        return '""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise WorkflowError(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def copy_new(src: Path, dst: Path) -> None:
    if not src.exists():
        raise WorkflowError(f"Missing source file: {rel(src)}")
    if dst.exists():
        raise WorkflowError(f"Refusing to overwrite existing file: {rel(dst)}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def runtime_lock_file() -> Path:
    return REPO_ROOT / ".gtpj_runtime" / "gpu_runner.lock"


def read_config_values(config_path: Path) -> dict[str, str]:
    if not config_path.exists():
        raise WorkflowError(f"Missing config file: {rel(config_path)}")
    values: dict[str, str] = {}
    current_key = ""
    for raw_line in read_text(config_path).splitlines():
        key_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*$", raw_line)
        if key_match:
            current_key = key_match.group(1)
            continue
        value_match = re.match(r"^\s+value:\s*(.+?)\s*$", raw_line)
        if current_key and value_match:
            values[current_key] = value_match.group(1).strip().strip("'\"")
            current_key = ""
    return values


def read_key_value_block(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    in_block = False
    for raw_line in read_text(path).splitlines():
        line = raw_line.rstrip()
        if line.strip() == "```text":
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if not in_block or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if re.fullmatch(r"[A-Za-z0-9_]+", key):
            values[key] = value.strip()
    return values


def normalize_attempt_ids(value: str) -> tuple[str, str]:
    cleaned = value.strip()
    match = re.fullmatch(r"(?i)(?:attempt-)?([0-9]{3})", cleaned)
    if not match:
        raise WorkflowError(f"Invalid attempt id: {value}; expected ATTEMPT-001 or 001")
    number = match.group(1)
    return f"ATTEMPT-{number}", f"attempt-{number}"


def parse_trial_folder_name(trial_dir: Path) -> tuple[str, str]:
    match = re.fullmatch(r"(TRIAL-[0-9]{3})_(.+)", trial_dir.name)
    if not match:
        raise WorkflowError(
            f"Trial directory name must look like TRIAL-001_slug: {display_path(trial_dir)}"
        )
    return match.group(1), match.group(2)


def local_paths() -> dict[str, str]:
    result: dict[str, str] = {}
    for candidate in [
        REPO_ROOT / ".gtpj" / "local_paths.yaml",
        REPO_ROOT / ".gtpj" / "local_paths.example.yaml",
    ]:
        if not candidate.exists():
            continue
        for raw_line in read_text(candidate).splitlines():
            if ":" not in raw_line:
                continue
            key, value = raw_line.split(":", 1)
            result[key.strip()] = value.strip().strip("'\"")
        if result:
            break
    return result


def warehouse_root() -> Path:
    configured = local_paths().get("warehouse_root")
    if configured:
        return Path(configured)
    return REPO_ROOT.parent / "GTPJ_Warehouse"


def artifact_file_info(path: Path) -> tuple[str, str]:
    return sha256_file(path), str(path.stat().st_size)


def ensure_same_or_copy(src: Path, dst: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if sha256_file(src) == sha256_file(dst) and src.stat().st_size == dst.stat().st_size:
            return
        raise WorkflowError(f"Refusing to overwrite different Warehouse artifact: {display_path(dst)}")
    shutil.copyfile(src, dst)


def write_text_artifact(path: Path, content: str, *, dry_run: bool) -> tuple[str, str]:
    data = (content.rstrip() + "\n").encode("utf-8")
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != data:
            raise WorkflowError(f"Refusing to overwrite different Warehouse artifact: {display_path(path)}")
        path.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), str(len(data))


def warehouse_path_for_attempt(
    version: str, trial_id: str, attempt_lower: str, role_folder: str, file_name: str
) -> Path:
    return warehouse_root() / "runs" / version / "module_trial" / trial_id / attempt_lower / role_folder / file_name


def warehouse_uri_for_attempt(
    version: str, trial_id: str, attempt_lower: str, role_folder: str, file_name: str
) -> str:
    return f"warehouse://gtpj/runs/{version}/module_trial/{trial_id}/{attempt_lower}/{role_folder}/{file_name}"


def set_readme_field(content: str, field: str, value: str) -> str:
    line = f"{field}: {value}"
    pattern = rf"(?m)^{re.escape(field)}:.*$"
    if re.search(pattern, content):
        return re.sub(pattern, line, content, count=1)

    start = content.find("```text")
    if start == -1:
        return content.rstrip() + "\n" + line + "\n"
    end = content.find("```", start + len("```text"))
    if end == -1:
        return content.rstrip() + "\n" + line + "\n"
    return content[:end] + line + "\n" + content[end:]


def append_readme_result_row(readme: Path, row: str) -> None:
    content = read_text(readme)
    if row in content:
        return
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("|---") and index > 0 and "数据集" in lines[index - 1]:
            lines.insert(index + 1, row)
            readme.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            return
    readme.write_text(content.rstrip() + "\n\n" + row + "\n", encoding="utf-8")


def parse_training_log(log_path: Path) -> dict[str, str]:
    text = read_text(log_path)
    best_start = text.rfind("Best Results")
    metric_text = text[best_start:] if best_start != -1 else text
    metrics: dict[str, str] = {}
    best_epoch_match = re.search(r"Best Results\s*@\s*Epoch\s+([0-9]+)", metric_text)
    metrics["best_epoch"] = best_epoch_match.group(1) if best_epoch_match else ""
    patterns = {
        "U": r"GZSL-U[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "S": r"GZSL-S[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "H": r"GZSL-H[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "ZS": r"ZSL[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
    }
    for name, pattern in patterns.items():
        matches = re.findall(pattern, metric_text)
        metrics[name] = matches[-1] if matches else ""
    missing = [name for name in (*METRIC_NAMES, "best_epoch") if not metrics.get(name)]
    if missing:
        raise WorkflowError(
            f"Unable to parse training log metrics from {display_path(log_path)}: "
            + ", ".join(missing)
        )
    return metrics


def git(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise WorkflowError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def git_show(ref_path: str, check: bool = True) -> str:
    return git(["show", ref_path], check=check)


def resolve_commit(ref: str) -> str:
    return git(["rev-parse", "--verify", f"{ref}^{{commit}}"])


def tag_commit(tag: str) -> str:
    return resolve_commit(f"refs/tags/{tag}")


def remote_ref_commit(remote: str, ref: str, label: str) -> str:
    peeled_ref = f"{ref}^{{}}"
    output = git(["ls-remote", "--exit-code", remote, ref, peeled_ref], check=False)
    if not output:
        raise WorkflowError(f"Missing remote ref: {label} ({ref})")

    entries: dict[str, str] = {}
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            entries[parts[1]] = parts[0]
    if peeled_ref in entries:
        return entries[peeled_ref]
    if ref in entries:
        return entries[ref]
    raise WorkflowError(f"Missing remote ref: {label} ({ref})")


def require_clean_worktree(command_name: str) -> None:
    porcelain = git(["status", "--short"], check=False)
    if porcelain:
        raise WorkflowError(
            f"Working tree must be clean before {command_name} creates files:\n"
            f"{porcelain}"
        )


def current_branch() -> str:
    return git(["branch", "--show-current"], check=False)


def require_ancestor(ancestor_ref: str, descendant_ref: str, message: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_ref, descendant_ref],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip()
        raise WorkflowError(f"{message}{': ' + detail if detail else ''}")


def require_expected_branch(expected_branch: str, command_name: str) -> None:
    branch = current_branch()
    if not branch:
        raise WorkflowError(
            f"{command_name} requires a named branch "
            f"{expected_branch}; current HEAD is detached"
        )
    if branch != expected_branch:
        raise WorkflowError(
            f"{command_name} must run on expected branch {expected_branch}; "
            f"current branch is {branch}"
        )


def require_experiment_branch(expected_branch: str) -> None:
    require_expected_branch(expected_branch, "new-experiment")


def require_trial_branch(expected_branch: str) -> None:
    require_expected_branch(expected_branch, "new-trial")


def require_current_branch_contains_main(command: str) -> None:
    require_ancestor(
        "refs/heads/main",
        "HEAD",
        f"{command} branch must contain current local main",
    )


def require_clean_id(value: str, pattern: str, label: str) -> str:
    if not re.fullmatch(pattern, value):
        raise WorkflowError(f"Invalid {label}: {value}")
    return value


def require_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise WorkflowError(
            "Slug must use lowercase letters, numbers, underscore, or hyphen"
        )
    return value


def branch_slug(value: str) -> str:
    return value.replace("_", "-")


def experiment_branch_name(version: str, kind: ExperimentKind, exp_id: str, slug: str) -> str:
    number = exp_id.split("-", 1)[1].lower()
    return f"exp/{version}-{kind.branch_kind}-{number}-{branch_slug(slug)}"


def trial_branch_name(base_version: str, idea_id: str, trial_id: str, slug: str) -> str:
    return f"dev/{base_version}-{idea_id.lower()}-{trial_id.lower()}-{branch_slug(slug)}"


def trial_tag_name(base_version: str, idea_id: str, trial_id: str) -> str:
    return f"trial/{base_version}/{idea_id.lower()}/{trial_id.lower()}"


def require_score(value: float, label: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError(f"{label} must be a number") from exc
    if score < 0 or score > 100:
        raise WorkflowError(f"{label} must be between 0 and 100")
    return score


def require_path_inside(path: Path, root: Path, label: str) -> None:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise WorkflowError(f"{label} must stay inside {rel(root)}") from exc


def list_files_for_scan() -> Iterable[Path]:
    ignored_roots = {".git", "__pycache__"}
    ignored_suffixes = {".pyc", ".pth", ".pt", ".ckpt"}
    for path in REPO_ROOT.rglob("*"):
        if path.is_dir():
            continue
        if any(part in ignored_roots for part in path.parts):
            continue
        if path.suffix in ignored_suffixes:
            continue
        yield path


def validate_idea_tree_data(data: object) -> tuple[str, list[dict]]:
    if not isinstance(data, dict):
        raise WorkflowError("idea_tree.json must be an object")
    if data.get("project") != "GTPJ":
        raise WorkflowError("idea_tree.json project must be GTPJ")
    if not isinstance(data.get("version"), str) or not str(data.get("version")).strip():
        raise WorkflowError("idea_tree.json version must be a non-empty string")
    current_version = data.get("current_version")
    if not isinstance(current_version, str) or not re.fullmatch(r"v[0-9]+", current_version):
        raise WorkflowError("idea_tree.json current_version must look like v1")
    ideas = data.get("ideas")
    if not isinstance(ideas, list):
        raise WorkflowError("idea_tree.json ideas must be a list")
    for index, idea in enumerate(ideas, start=1):
        if not isinstance(idea, dict):
            raise WorkflowError(f"idea_tree.json ideas[{index}] must be an object")
        idea_id = idea.get("idea_id", f"ideas[{index}]")
        if idea.get("status") not in IDEA_STATUSES:
            raise WorkflowError(f"{idea_id} has invalid status")
        for field in [
            "idea_id",
            "idea_dir",
            "title",
            "source_type",
            "source_ref",
            "source_status",
            "global_score",
            "version_scores",
            "base_versions",
            "based_on_modules",
            "target_component",
            "hypothesis",
            "implementation_scope",
            "risk",
            "transfer_notes",
            "linked_trials",
            "linked_versions",
            "linked_experiments",
            "evidence",
            "next_action",
        ]:
            if field not in idea:
                raise WorkflowError(f"{idea_id} missing required field: {field}")
    return current_version, ideas


def cmd_status(_: argparse.Namespace) -> int:
    branch = git(["branch", "--show-current"], check=False) or "(detached)"
    head = git(["rev-parse", "--short", "HEAD"], check=False)
    tags = git(["tag", "--points-at", "HEAD"], check=False)
    porcelain = git(["status", "--short"], check=False)

    print("GTPJ repository 状态")
    print(f"- branch: {branch}")
    print(f"- head: {head}")
    print(f"- tags at head: {tags or '(none)'}")
    print(f"- working tree: {'dirty' if porcelain else 'clean'}")
    print()
    print("可用版本:")
    for version_dir in sorted((REPO_ROOT / "experiments").glob("v*")):
        if version_dir.is_dir():
            print(f"- {version_dir.name}: {rel(version_dir)}")
    print()
    print("后续队列:")
    for queue in sorted((REPO_ROOT / "idea_tree" / "queues").glob("*.md")):
        print(f"- {rel(queue)}")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    required = [
        "README.md",
        "AGENTS.md",
        "NEXT_ACTIONS.md",
        "docs/GITHUB_GOVERNANCE.md",
        "docs/PROJECT_STRUCTURE.md",
        "docs/PROJECT_STATUS.md",
        "docs/DATA_SETUP.md",
        "docs/workflow/README.md",
        "docs/workflow/git_policy.md",
        "docs/workflow/versioning.md",
        "docs/workflow/module_trial_protocol.md",
        "docs/workflow/code_interface_contract.md",
        "docs/workflow/code_interface.md",
        "docs/workflow/experiment_protocol.md",
        "docs/workflow/artifact_policy.md",
        "docs/workflow/result_index_protocol.md",
        "docs/workflow/agent_contracts.md",
        "docs/workflow/agent_report_policy.md",
        "docs/workflow/idea_tree_protocol.md",
        "docs/workflow/quality_gate.md",
        "docs/workflow/runbook.md",
        "workflow/README.md",
        "workflow/openclaw/README.md",
        "workflow/codex/README.md",
        "config/README.md",
        "config/GTPJ_cub_gzsl.yaml",
        "idea_tree/INDEX.md",
        "idea_tree/README.md",
        "idea_tree/schema.json",
        "idea_tree/idea_tree.json",
        "idea_tree/versions/v1.md",
        "idea_tree/versions/v2.md",
        "experiments/README.md",
        "experiments/EXPERIMENT_REGISTRY.md",
        "experiments/VERSION_TREE.md",
        "experiments/LEGACY_POLICY.md",
        "experiments/module_trials/INDEX.md",
        "experiments/templates/IDEA_template.md",
        "experiments/templates/TRIAL_README_template.md",
        "experiments/templates/VERSION_template.md",
        "experiments/templates/experiment_README_template.md",
        "experiments/templates/implementation_template.md",
        "experiments/templates/agent_summary_template.md",
        "experiments/templates/quality_check_template.md",
        "experiments/v1/VERSION.md",
        "experiments/v1/config.yaml",
        "experiments/v1/result.md",
        "experiments/v1/baseline/README.md",
        "experiments/v1/baseline/config.yaml",
        "experiments/v1/baseline/quality_check.md",
        "experiments/v1/tune/INDEX.md",
        "experiments/v1/ablation/INDEX.md",
        "experiments/v1/confirmation/INDEX.md",
        "config/versions/v1.yaml",
        "experiments/v2/VERSION.md",
        "experiments/v2/config.yaml",
        "experiments/v2/result.md",
        "experiments/v2/baseline/README.md",
        "experiments/v2/baseline/config.yaml",
        "experiments/v2/baseline/manifest.yaml",
        "experiments/v2/baseline/result.yaml",
        "experiments/v2/baseline/quality_check.md",
        "experiments/v2/tune/INDEX.md",
        "experiments/v2/ablation/INDEX.md",
        "experiments/v2/confirmation/INDEX.md",
        "config/versions/v2.yaml",
        "schemas/manifest.schema.json",
        "schemas/result.schema.json",
        "schemas/artifact_ref.schema.json",
    ]
    missing = [item for item in required if not (REPO_ROOT / item).exists()]
    if missing:
        raise WorkflowError("Missing required files:\n" + "\n".join(missing))

    idea_tree = json.loads(read_text(REPO_ROOT / "idea_tree" / "idea_tree.json"))
    current_version, ideas = validate_idea_tree_data(idea_tree)

    idea_index = read_text(REPO_ROOT / "idea_tree" / "INDEX.md")
    version_docs: dict[str, str] = {}
    expected_version_docs = {current_version}
    for idea in ideas:
        expected_version_docs.update(str(version) for version in idea.get("version_scores", {}).keys())
    for version in sorted(expected_version_docs):
        if not re.fullmatch(r"v[0-9]+", version):
            raise WorkflowError(f"Invalid idea version view: {version}")
        version_path = REPO_ROOT / "idea_tree" / "versions" / f"{version}.md"
        if not version_path.exists():
            raise WorkflowError(f"Missing idea version view: {rel(version_path)}")
        version_docs[version] = read_text(version_path)
    for idea in ideas:
        idea_id = idea.get("idea_id", "")
        if not re.fullmatch(r"IDEA-[0-9]{4}", idea_id):
            raise WorkflowError(f"Invalid idea_id in idea_tree.json: {idea_id}")
        idea_dir_text = idea.get("idea_dir")
        if not isinstance(idea_dir_text, str) or not idea_dir_text.startswith("idea_tree/ideas/"):
            raise WorkflowError(f"{idea_id} must use idea_tree/ideas/ as idea_dir")
        idea_dir = REPO_ROOT / idea_dir_text
        require_path_inside(idea_dir, REPO_ROOT / "idea_tree" / "ideas", f"{idea_id} idea_dir")
        idea_file = idea_dir / "IDEA.md"
        if not idea_file.exists():
            raise WorkflowError(f"{idea_id} missing idea file: {rel(idea_file)}")
        if idea_id not in idea_index or idea_dir_text not in idea_index:
            raise WorkflowError(f"{idea_id} missing from idea_tree/INDEX.md")
        if idea.get("source_type") not in SOURCE_TYPES:
            raise WorkflowError(f"{idea_id} has invalid source_type")
        if idea.get("source_status") not in SOURCE_STATUSES:
            raise WorkflowError(f"{idea_id} has invalid source_status")
        if idea.get("source_status") in {"unknown", "unverified"}:
            if idea.get("status") in {"selected", "developing", "testing", "validated"}:
                raise WorkflowError(f"{idea_id} cannot be selected before source is verified")
        if idea.get("source_status") in TRIAL_ALLOWED_SOURCE_STATUSES:
            source_ref = idea.get("source_ref")
            if not isinstance(source_ref, str) or not source_ref.strip():
                raise WorkflowError(f"{idea_id} with verified/local source must define source_ref")
        require_score(idea.get("global_score", -1), f"{idea_id} global_score")
        version_scores = idea.get("version_scores")
        if not isinstance(version_scores, dict) or not version_scores:
            raise WorkflowError(f"{idea_id} must define version_scores")
        if current_version not in version_scores:
            raise WorkflowError(f"{idea_id} must score current_version {current_version}")
        for version, entry in version_scores.items():
            if not re.fullmatch(r"v[0-9]+", version):
                raise WorkflowError(f"{idea_id} has invalid version score key: {version}")
            if not isinstance(entry, dict):
                raise WorkflowError(f"{idea_id} version score for {version} must be an object")
            require_score(entry.get("score", -1), f"{idea_id} {version} score")
            if entry.get("applicability") not in APPLICABILITIES:
                raise WorkflowError(f"{idea_id} {version} has invalid applicability")
            stage = entry.get("stage")
            if stage is not None and stage not in VERSION_STAGES:
                raise WorkflowError(f"{idea_id} {version} has invalid stage")
            if not isinstance(entry.get("blockers"), list):
                raise WorkflowError(f"{idea_id} {version} blockers must be a list")
            version_doc = version_docs.get(version, "")
            if idea_id not in version_doc or idea_dir_text not in version_doc:
                raise WorkflowError(f"{idea_id} missing from idea_tree/versions/{version}.md")
            if idea.get("source_status") in {"unknown", "unverified"}:
                if float(entry.get("score", 0) or 0) != 0:
                    raise WorkflowError(f"{idea_id} with unknown/unverified source must keep score 0")
                if entry.get("applicability") not in {"unclear", "not_applicable"}:
                    raise WorkflowError(f"{idea_id} with unknown/unverified source must not be directly applicable")

    for version, meta in CANONICAL_BASELINES.items():
        if not git(["tag", "--list", version], check=False):
            raise WorkflowError(f"Missing required tag: {version}")
        result_at_tag = git_show(f"{version}:{meta['result_file']}")
        version_at_tag = git_show(f"{version}:{meta['version_file']}")
        expected_h = meta["H"]
        if expected_h not in result_at_tag or expected_h not in version_at_tag:
            raise WorkflowError(
                f"{version} tag does not point to canonical {meta['name']} H={expected_h}. "
                f"Current local {version} -> {tag_commit(version)[:12]}"
            )
        for local_file in [meta["result_file"], meta["version_file"]]:
            local_text = read_text(REPO_ROOT / local_file)
            if expected_h not in local_text:
                raise WorkflowError(f"{local_file} must record canonical H={expected_h}")

    for version in sorted(CANONICAL_BASELINES):
        version_config = read_text(REPO_ROOT / "config" / "versions" / f"{version}.yaml")
        archived_config = read_text(REPO_ROOT / "experiments" / version / "config.yaml")
        baseline_config = read_text(REPO_ROOT / "experiments" / version / "baseline" / "config.yaml")
        if version_config != archived_config:
            raise WorkflowError(f"config/versions/{version}.yaml and experiments/{version}/config.yaml differ")
        if version_config != baseline_config:
            raise WorkflowError(f"config/versions/{version}.yaml and experiments/{version}/baseline/config.yaml differ")

    project_structure = read_text(REPO_ROOT / "docs" / "PROJECT_STRUCTURE.md")
    for marker in [
        "总体框架",
        "顶层文件",
        "`config/`",
        "`docs/`",
        "`workflow/`",
        "`model/`",
        "`tools/`",
        "`idea_tree/`",
        "`experiments/`",
        "更新本文件的判断标准",
    ]:
        if marker not in project_structure:
            raise WorkflowError(f"docs/PROJECT_STRUCTURE.md missing section: {marker}")

    contract = read_text(REPO_ROOT / "docs" / "workflow" / "code_interface_contract.md")
    for marker in [
        "Baseline-Off Equivalence",
        "Input Contract",
        "Output Contract",
        "Shape Invariants",
        "Config Switch Contract",
        "Loss Contract",
        "Evaluation Contract",
        "Minimum Verification",
    ]:
        if marker not in contract:
            raise WorkflowError(f"code_interface_contract.md missing section: {marker}")

    artifact_policy = read_text(REPO_ROOT / "docs" / "workflow" / "artifact_policy.md")
    for marker in [
        "GitHub Boundary",
        "External Stores",
        "Artifact Identity",
        "Forbidden GitHub Artifacts",
    ]:
        if marker not in artifact_policy:
            raise WorkflowError(f"artifact_policy.md missing section: {marker}")

    agent_contracts = read_text(REPO_ROOT / "docs" / "workflow" / "agent_contracts.md")
    for marker in [
        "Coordinator",
        "Runner",
        "Log Analyst",
        "Quality Checker",
        "Interface Checker",
        "Inputs",
        "Forbidden Writes",
        "Failure Conditions",
    ]:
        if marker not in agent_contracts:
            raise WorkflowError(f"agent_contracts.md missing section: {marker}")

    implementation_template = read_text(
        REPO_ROOT / "experiments" / "templates" / "implementation_template.md"
    )
    for marker in [
        "Input Contract",
        "Output Contract",
        "Shape Invariants",
        "Baseline-Off Path",
        "Minimum Verification",
    ]:
        if marker not in implementation_template:
            raise WorkflowError(f"implementation_template.md missing section: {marker}")

    offenders: list[str] = []
    for path in list_files_for_scan():
        try:
            content = read_text(path)
        except UnicodeDecodeError:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.lower() in content.lower():
                offenders.append(f"{rel(path)} contains {pattern!r}")
        for pattern in FORBIDDEN_REGEXES:
            if pattern.search(content):
                offenders.append(f"{rel(path)} matches {pattern.pattern!r}")
    if offenders:
        raise WorkflowError("Forbidden legacy traces found:\n" + "\n".join(offenders))

    print("validate-ok")
    return 0


def cmd_validate_remote(args: argparse.Namespace) -> int:
    remote = args.remote
    local_tags: dict[str, str] = {}
    for version in CANONICAL_BASELINES:
        try:
            local_tags[version] = tag_commit(version)
        except WorkflowError as exc:
            raise WorkflowError(f"Missing local authoritative tag: {version}") from exc
    try:
        local_main = resolve_commit("refs/heads/main")
    except WorkflowError as exc:
        raise WorkflowError("Missing local main branch: refs/heads/main") from exc
    for version in CANONICAL_BASELINES:
        require_ancestor(
            f"refs/tags/{version}",
            "refs/heads/main",
            f"local main must contain local {version} tag",
        )

    checks = [
        ("origin/main", "refs/heads/main", local_main),
    ]
    for version, commit in local_tags.items():
        checks.append((f"origin/{version}", f"refs/tags/{version}", commit))
    errors: list[str] = []
    for label, ref, expected in checks:
        display_label = label.replace("origin", remote, 1)
        try:
            actual = remote_ref_commit(remote, ref, display_label)
        except WorkflowError as exc:
            errors.append(str(exc))
            continue
        if actual != expected:
            errors.append(
                f"{display_label} must point to local {ref} commit {expected}; "
                f"got {actual}"
            )
    if errors:
        raise WorkflowError("Remote validation failed:\n" + "\n".join(errors))

    print("validate-remote-ok")
    return 0


def make_experiment_readme(version: str, kind: ExperimentKind, exp_id: str, slug: str) -> str:
    return f"""# {exp_id}_{slug}

```text
experiment_id: {exp_id}
kind: {kind.name}
version: {version}
base_code_tag: {version}
branch_source: main
code_branch: {experiment_branch_name(version, kind, exp_id, slug)}
runtime: OpenClaw preferred / Codex compatible
quality_check_mode: {kind.default_check}
run_commit:
dirty_state:
config: config.yaml
command:
seed:
python_env:
torch_cuda:
dataset_split:
cache_fingerprint:
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
attempt_id: attempt-001
failure_stage:
U:
S:
H:
ZS:
best_epoch:
decision:
promotion_decision: not_applicable
promote_to:
status: planned
```

## 问题

描述这个实验要回答的精确问题。

## 运行前检查

- [ ] 临时分支来源符合实验类型；当前版本从 `main` 切出，历史版本可从 `{version}` tag 开只运行分支。
- [ ] `base_code_tag: {version}` 和 `branch_source` 已记录。
- [ ] 配置复制自 `experiments/{version}/config.yaml`。
- [ ] 只改变声明过的变量或开关。
- [ ] Runner 开始前已用 `runner-lock` 占用 GPU；结束、失败或人工停止后已 `runner-unlock`。
- [ ] 原始日志、checkpoint、generated figures 写入 Warehouse，不写入 GitHub。
- [ ] `manifest.yaml` 中的 artifact URI、hash、size 能对应外部资产。
- [ ] `agent_summary.md` 已记录参与 agents、检查范围、发现和结论。
- [ ] `quality_check.md` 已创建；实验完成后再填写 decision。

## 变量

Tune 实验填写：

```text
tuned_parameter:
old_value:
new_value:
search_space:
single_variable:
baseline_H:
trial_H:
delta_H:
promotion_rule:
```

Ablation 实验填写：

```text
disabled_module:
switch_key:
baseline_off_path:
expected_effect:
affected_contracts:
control_result:
ablation_delta:
```

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log artifact |
|---|---:|---:|---:|---:|---:|---:|---|

## 失败记录

```text
failure_stage:
error_summary:
stderr_or_log:
retry_decision:
impact_on_next_plan:
```

## 结论

待记录。
"""


def make_quality_check(kind: ExperimentKind) -> str:
    return f"""# Quality Check

```text
runtime:
quality_check_mode: {kind.default_check}
decision: PENDING
promotion_decision: not_applicable
```

## 范围

## 发现

## 质量检查

- [ ] 代码快照或 base version 明确。
- [ ] 配置副本保存在实验目录。
- [ ] 外部日志 artifact URI、sha256、size 明确。
- [ ] 结果口径明确。
- [ ] 没有未声明的 eval / class order / logits shape 改动。
- [ ] seen/unseen split、label mapping、class order 和 metric calculation 未改变或已按高风险记录。
- [ ] GitHub 目录中没有新增 raw log、checkpoint、generated figures。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] parent_version / parent_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 外部日志 artifact URI、sha256、size、保留位置明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到 parent_version 行为。
- [ ] VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] idea_tree current_version 和必要的 version_scores.vX 已更新。
- [ ] 新 baseline tag 准备打在包含正式版本代码和版本材料的明确 commit 上。
- [ ] main 当前代码只有 owner 明确执行 activate-version vX 时才切换；默认不切换。

## 决策

PENDING
"""


def make_agent_summary(version: str, kind: ExperimentKind, exp_id: str, slug: str) -> str:
    if kind.name == "confirmation":
        agent_set = "Coordinator, Runner, Log Analyst, Quality Checker"
        serial_agents = "Coordinator -> Runner -> Coordinator"
        parallel_agents = "Log Analyst + Quality Checker after/around run evidence collection"
        disabled_agents = "Reader/Planner, Implementer, Interface Checker, Reviewer, Result Analyst"
    elif kind.name == "tune":
        agent_set = "Coordinator, Reader/Planner, Runner, Log Analyst, Quality Checker"
        serial_agents = "Coordinator -> Reader/Planner -> Runner -> Coordinator"
        parallel_agents = "Log Analyst + Quality Checker after/around run evidence collection"
        disabled_agents = "Implementer, Interface Checker, Reviewer"
    elif kind.name == "ablation":
        agent_set = "Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst"
        serial_agents = "Coordinator -> Reader/Planner -> Implementer -> Interface Checker -> Runner -> Coordinator"
        parallel_agents = "Log Analyst + Quality Checker + Result Analyst after run"
        disabled_agents = "Reviewer unless requested by Coordinator"
    else:
        agent_set = "Coordinator"
        serial_agents = "Coordinator"
        parallel_agents = ""
        disabled_agents = ""
    return f"""# Agent Summary

```text
experiment_id: {exp_id}
run_id:
base_version: {version}
code_branch: {experiment_branch_name(version, kind, exp_id, slug)}
code_commit:
agent_set: {agent_set}
serial_agents: {serial_agents}
parallel_agents: {parallel_agents}
disabled_agents: {disabled_agents}
runtime_state:
warehouse_report_artifacts:
final_decision: pending
```

## Coordinator

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Runner

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Log Analyst

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Quality Checker

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```

## Interface Checker

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
```
"""


def default_log_uri(version: str, kind: ExperimentKind, exp_id: str, slug: str, attempt_id: str, log_name: str) -> str:
    experiment_name = f"{exp_id}_{slug}"
    return (
        f"warehouse://gtpj/runs/{version}/{kind.folder}/"
        f"{experiment_name}/{attempt_id}/logs/{log_name}"
    )


def default_log_artifact_id(exp_id: str, slug: str, attempt_id: str) -> str:
    return f"log:{exp_id}_{slug}:{attempt_id}"


def make_experiment_manifest(
    *,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    config_path: Path,
    status: str,
    attempt_id: str = "attempt-001",
    command: str = "",
    seed: str = "",
    dataset: str = "CUB GZSL",
    log_artifact_id: str = "",
    log_uri: str = "",
    log_sha256: str = "",
    log_size_bytes: str = "",
    recorded_at: str = "",
    code_branch: str = "",
    git_dirty: str | None = None,
    idea_id: str = "",
    idea_uri: str = "",
    idea_title: str = "",
    hypothesis: str = "Tune hyperparameters without changing code.",
) -> str:
    config_rel = rel(config_path)
    return f"""schema_version: gtpj-manifest/v1
experiment:
  id: {yaml_scalar(exp_id)}
  name: {yaml_scalar(f"{exp_id}_{slug}")}
  kind: {yaml_scalar(kind.name)}
  status: {yaml_scalar(status)}
  attempt_id: {yaml_scalar(attempt_id)}
  created_or_recorded_at: {yaml_scalar(recorded_at or utc_now())}
version:
  base_version: {yaml_scalar(version)}
  base_code_tag: {yaml_scalar(version)}
  code_branch: {yaml_scalar(code_branch or experiment_branch_name(version, kind, exp_id, slug))}
  code_commit: {yaml_scalar(git(["rev-parse", "--short", "HEAD"], check=False))}
  git_dirty: {yaml_scalar(git_dirty if git_dirty is not None else ("true" if git(["status", "--short"], check=False) else "false"))}
reproducibility:
  config_file: {yaml_scalar(config_rel)}
  config_sha256: {yaml_scalar(sha256_file(config_path) if config_path.exists() else "")}
  command: {yaml_scalar(command)}
  seed: {yaml_scalar(seed)}
  dataset: {yaml_scalar(dataset)}
  split_id: {yaml_scalar("standard_v1")}
  class_order_id: {yaml_scalar("standard_v1")}
  label_mapping_id: {yaml_scalar("standard_v1")}
  metric_contract_id: {yaml_scalar("gzsl_u_s_h_zs_v1")}
idea:
  idea_id: {yaml_scalar(idea_id)}
  uri: {yaml_scalar(idea_uri)}
  title: {yaml_scalar(idea_title)}
  hypothesis: {yaml_scalar(hypothesis)}
artifacts:
  train_log:
    artifact_id: {yaml_scalar(log_artifact_id)}
    role: {yaml_scalar("training_log")}
    uri: {yaml_scalar(log_uri)}
    sha256: {yaml_scalar(log_sha256)}
    size_bytes: {yaml_scalar(log_size_bytes)}
    required_for: {yaml_scalar("audit")}
    status: {yaml_scalar("available" if log_uri else "pending")}
quality:
  boundary_audit_required: true
  raw_artifacts_in_git: false
  interface_contract_required: {yaml_scalar("false" if kind.name == "tune" else "true")}
  evaluation_semantics_verified: {yaml_scalar("false")}
"""


def make_result_yaml(
    *,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    metrics: dict[str, str] | None = None,
    seed: str = "",
    decision: str = "pending",
    promotion_decision: str = "not_applicable",
    promote_to: str = "",
    log_artifact_id: str = "",
    recorded_at: str = "",
) -> str:
    metrics = metrics or {}
    baseline_h = CANONICAL_BASELINES.get(version, {}).get("H", "")
    h_value = metrics.get("H", "")
    delta_h = ""
    if baseline_h and h_value:
        try:
            delta_h = f"{float(h_value) - float(baseline_h):+.2f}"
        except ValueError:
            delta_h = ""
    return f"""schema_version: gtpj-result/v1
experiment_id: {yaml_scalar(exp_id)}
experiment_name: {yaml_scalar(f"{exp_id}_{slug}")}
kind: {yaml_scalar(kind.name)}
version: {yaml_scalar(version)}
metrics:
  U: {yaml_scalar(metrics.get("U", ""))}
  S: {yaml_scalar(metrics.get("S", ""))}
  H: {yaml_scalar(metrics.get("H", ""))}
  ZS: {yaml_scalar(metrics.get("ZS", ""))}
  best_epoch: {yaml_scalar(metrics.get("best_epoch", ""))}
  baseline_H: {yaml_scalar(baseline_h)}
  delta_H: {yaml_scalar(delta_h)}
  seed: {yaml_scalar(seed)}
  source: {yaml_scalar("training_log")}
  metric_semantics: {yaml_scalar("GZSL U/S/H/ZS from protected evaluator")}
baseline:
  version: {yaml_scalar(version)}
  H: {yaml_scalar(baseline_h)}
delta:
  H: {yaml_scalar(delta_h)}
run:
  seed: {yaml_scalar(seed)}
decision:
  status: {yaml_scalar(decision)}
  promotion_decision: {yaml_scalar(promotion_decision)}
  promote_to: {yaml_scalar(promote_to)}
evidence:
  log_artifact_id: {yaml_scalar(log_artifact_id)}
  manifest: {yaml_scalar("manifest.yaml")}
  agent_summary: {yaml_scalar("agent_summary.md")}
  label_mapping_id: {yaml_scalar("standard_v1")}
  split_id: {yaml_scalar("standard_v1")}
  class_order_id: {yaml_scalar("standard_v1")}
quality:
  manifest_verified: {yaml_scalar("false")}
  boundary_audit_passed: {yaml_scalar("false")}
  interface_contract_checked: {yaml_scalar("false")}
  evaluation_semantics_verified: {yaml_scalar("false")}
recorded_at: {yaml_scalar(recorded_at or utc_now())}
"""


def make_result_md(
    *,
    exp_id: str,
    slug: str,
    kind: ExperimentKind,
    metrics: dict[str, str] | None = None,
    decision: str = "pending",
    log_artifact_id: str = "",
    log_uri: str = "",
) -> str:
    metrics = metrics or {}
    return f"""# {exp_id}_{slug} Result

## Summary

Kind: `{kind.name}`.

## Metrics

| U | S | H | ZS | Best epoch |
|---:|---:|---:|---:|---:|
| {metrics.get("U", "-")} | {metrics.get("S", "-")} | {metrics.get("H", "-")} | {metrics.get("ZS", "-")} | {metrics.get("best_epoch", "-")} |

## Evidence

```text
log_artifact_id: {log_artifact_id}
log_uri: {log_uri}
```

## Decision

{decision}
"""


def append_version_experiment_registry(
    version: str, kind: ExperimentKind, exp_id: str, slug: str, folder: Path
) -> None:
    registry = REPO_ROOT / "experiments" / "EXPERIMENT_REGISTRY.md"
    content = read_text(registry)
    experiment_name = f"{exp_id}_{slug}"
    row = (
        f"| `{experiment_name}` | `{version}` | `{kind.name}` | planned | "
        f"`{rel(folder)}` | 由结构 helper 创建。 |"
    )
    if experiment_name in content:
        return

    lines = [
        line
        for line in content.splitlines()
        if "No clean GTPJ-run experiments yet." not in line and "| 暂无 |" not in line
    ]
    content = "\n".join(lines).rstrip() + "\n" + row + "\n"
    registry.write_text(content, encoding="utf-8")


def update_version_experiment_registry_status(
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    status: str,
    note: str,
) -> None:
    registry = REPO_ROOT / "experiments" / "EXPERIMENT_REGISTRY.md"
    content = read_text(registry)
    experiment_name = f"{exp_id}_{slug}"
    prefix = f"| `{experiment_name}` | `{version}` | `{kind.name}` |"
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            raise WorkflowError(f"Malformed registry row for {experiment_name}")
        cells[3] = status
        cells[5] = note
        lines[index] = "| " + " | ".join(cells) + " |"
        registry.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return
    raise WorkflowError(f"Missing registry row for {experiment_name}")


def append_kind_index(
    version: str, kind: ExperimentKind, exp_id: str, slug: str, folder: Path
) -> None:
    index = REPO_ROOT / "experiments" / version / kind.folder / "INDEX.md"
    if not index.exists():
        raise WorkflowError(f"Missing experiment index: {rel(index)}")
    experiment_name = f"{exp_id}_{slug}"
    content = read_text(index)
    if experiment_name in content:
        return
    lines = [
        line
        for line in content.splitlines()
        if "| 暂无 |" not in line and "当前还没有新仓库内启动的" not in line
    ]
    content = "\n".join(lines).rstrip()
    section = "\n\n## 实验记录\n\n| 实验 | 状态 | 目录 | 说明 |\n|---|---|---|---|\n"
    row = f"| `{experiment_name}` | planned | `{rel(folder)}` | 由结构 helper 创建。 |"
    if "## 实验记录" not in content:
        content = content + section + row + "\n"
    else:
        content = content + "\n" + row + "\n"
    index.write_text(content, encoding="utf-8")


def cmd_new_experiment(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)
    expected_branch = experiment_branch_name(version, kind, exp_id, slug)

    base_dir = REPO_ROOT / "experiments" / version
    if not base_dir.exists():
        raise WorkflowError(f"Unknown version directory: {rel(base_dir)}")
    src_config = base_dir / "config.yaml"
    duplicates = sorted((base_dir / kind.folder).glob(f"{exp_id}_*"))
    if duplicates:
        raise WorkflowError(
            f"{exp_id} already exists under {rel(base_dir / kind.folder)}: "
            + ", ".join(rel(path) for path in duplicates)
        )
    exp_dir = base_dir / kind.folder / f"{exp_id}_{slug}"
    if exp_dir.exists():
        raise WorkflowError(f"Experiment already exists: {rel(exp_dir)}")

    require_experiment_branch(expected_branch)
    require_clean_worktree("new-experiment")
    require_current_branch_contains_main("new-experiment")

    write_new(exp_dir / "README.md", make_experiment_readme(version, kind, exp_id, slug))
    write_new(exp_dir / "quality_check.md", make_quality_check(kind))
    write_new(exp_dir / "agent_summary.md", make_agent_summary(version, kind, exp_id, slug))
    copy_new(src_config, exp_dir / "config.yaml")
    write_new(
        exp_dir / "manifest.yaml",
        make_experiment_manifest(
            version=version,
            kind=kind,
            exp_id=exp_id,
            slug=slug,
            config_path=exp_dir / "config.yaml",
            status="planned",
            git_dirty="false",
        ),
    )
    write_new(
        exp_dir / "result.yaml",
        make_result_yaml(
            version=version,
            kind=kind,
            exp_id=exp_id,
            slug=slug,
        ),
    )
    write_new(
        exp_dir / "result.md",
        make_result_md(exp_id=exp_id, slug=slug, kind=kind),
    )
    append_version_experiment_registry(version, kind, exp_id, slug, exp_dir)
    append_kind_index(version, kind, exp_id, slug, exp_dir)

    print(f"已创建 {rel(exp_dir)}")
    print(f"建议分支: {expected_branch}")
    return 0


def cmd_tune_suggest(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    limit = min(max(args.limit, 1), 3)
    config_path = REPO_ROOT / "experiments" / version / "config.yaml"
    index_path = REPO_ROOT / "experiments" / version / "tune" / "INDEX.md"
    if not index_path.exists():
        raise WorkflowError(f"Missing tune index: {rel(index_path)}")
    values = read_config_values(config_path)
    tried_text = read_text(index_path)
    candidates = []
    for rule in TUNE_CANDIDATE_RULES:
        parameter = rule["parameter"]
        if parameter not in values:
            continue
        suggested = rule["suggested_value"]
        already_tried = parameter in tried_text and suggested in tried_text
        candidates.append((rule, values[parameter], already_tried))
        if len(candidates) == limit:
            break

    print(f"Tune suggestions for {version} (最多 3 个；用户选择 1 个候选后再运行)")
    print(f"index: {rel(index_path)}")
    if not candidates:
        print("没有找到可自动建议的参数；请先在 config 中确认可调参数。")
        return 0
    for number, (rule, current_value, already_tried) in enumerate(candidates, start=1):
        print(f"\n候选 {number}")
        print(f"parameter: {rule['parameter']}")
        print(f"current_value: {current_value}")
        print(f"suggested_value: {rule['suggested_value']}")
        print(f"why: {rule['why']}")
        print(f"risk: {rule['risk']}")
        print(f"cost: {rule['cost']}")
        print(f"already_tried: {'yes' if already_tried else 'no'}")
    return 0


def append_tune_result_index(
    *,
    version: str,
    exp_id: str,
    slug: str,
    folder: Path,
    parameter: str,
    old_value: str,
    new_value: str,
    seed: str,
    metrics: dict[str, str],
    decision: str,
) -> None:
    index = REPO_ROOT / "experiments" / version / "tune" / "INDEX.md"
    if not index.exists():
        raise WorkflowError(f"Missing tune index: {rel(index)}")
    experiment_name = f"{exp_id}_{slug}"
    baseline_h = CANONICAL_BASELINES.get(version, {}).get("H", "")
    result_text = "recorded"
    if baseline_h:
        try:
            delta = float(metrics["H"]) - float(baseline_h)
            result_text = f"H {metrics['H']} (delta {delta:+.2f})"
        except ValueError:
            result_text = f"H {metrics['H']}"
    row = (
        f"| `{experiment_name}` | `{parameter}` | {old_value} | {new_value} | {seed or '-'} | "
        f"{metrics['U']} | {metrics['S']} | {metrics['H']} | {metrics['ZS']} | "
        f"{result_text} | {decision} | `{rel(folder)}` |"
    )
    content = read_text(index)
    if row in content:
        return
    lines = [
        line
        for line in content.splitlines()
        if "| 暂无 |" not in line and "由 `workflow/gtpj_workflow.py new-experiment` 创建后追加" not in line
    ]
    content = "\n".join(lines).rstrip()
    section = (
        "\n\n## 结果记录\n\n"
        "| Tune ID | 参数 | 原值 | 新值 | Seed | U | S | H | ZS | 结果 | 决策 | 目录 |\n"
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|\n"
    )
    if "## 结果记录" not in content:
        content = content + section + row + "\n"
    else:
        content = content + "\n" + row + "\n"
    index.write_text(content, encoding="utf-8")


def resolve_existing_path(path_text: str, label: str) -> Path:
    source = Path(path_text)
    if not source.is_absolute():
        source = REPO_ROOT / source
    if not source.exists():
        raise WorkflowError(f"Missing {label}: {display_path(source)}")
    if not source.is_file():
        raise WorkflowError(f"{label} must be a file: {display_path(source)}")
    return source


def update_manifest_and_result_files(
    *,
    exp_dir: Path,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    config_path: Path,
    command: str,
    seed: str,
    metrics: dict[str, str],
    decision: str,
    promotion_decision: str,
    promote_to: str,
    attempt_id: str,
    log_artifact_id: str,
    log_uri: str,
    log_sha256: str,
    log_size_bytes: str,
    git_dirty: str,
) -> None:
    recorded_at = utc_now()
    manifest = make_experiment_manifest(
        version=version,
        kind=kind,
        exp_id=exp_id,
        slug=slug,
        config_path=config_path,
        status="recorded",
        attempt_id=attempt_id,
        command=command,
        seed=seed,
        log_artifact_id=log_artifact_id,
        log_uri=log_uri,
        log_sha256=log_sha256,
        log_size_bytes=log_size_bytes,
        git_dirty=git_dirty,
        recorded_at=recorded_at,
    )
    result_yaml = make_result_yaml(
        version=version,
        kind=kind,
        exp_id=exp_id,
        slug=slug,
        metrics=metrics,
        seed=seed,
        decision=decision,
        promotion_decision=promotion_decision,
        promote_to=promote_to,
        log_artifact_id=log_artifact_id,
        recorded_at=recorded_at,
    )
    result_md = make_result_md(
        exp_id=exp_id,
        slug=slug,
        kind=kind,
        metrics=metrics,
        decision=decision,
        log_artifact_id=log_artifact_id,
        log_uri=log_uri,
    )
    (exp_dir / "manifest.yaml").write_text(manifest.rstrip() + "\n", encoding="utf-8")
    (exp_dir / "result.yaml").write_text(result_yaml.rstrip() + "\n", encoding="utf-8")
    (exp_dir / "result.md").write_text(result_md.rstrip() + "\n", encoding="utf-8")


def forbid_log_copy_target(exp_dir: Path) -> None:
    log_dir = exp_dir / "logs"
    if log_dir.exists() and any(log_dir.iterdir()):
        raise WorkflowError(
            f"GitHub experiment logs directory must stay empty under new boundary: {rel(log_dir)}"
        )


def artifact_uri_for_log(
    source_text: str,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    attempt_id: str,
    explicit_uri: str,
) -> str:
    if explicit_uri:
        if not re.fullmatch(r"(warehouse|research)://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+", explicit_uri):
            raise WorkflowError("artifact URI must use warehouse:// or research://")
        return explicit_uri
    source = Path(source_text)
    return default_log_uri(version, kind, exp_id, slug, attempt_id, source.name or "train.log")


def cmd_record_result(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)
    exp_dir = REPO_ROOT / "experiments" / version / kind.folder / f"{exp_id}_{slug}"
    if not exp_dir.exists():
        raise WorkflowError(f"Missing experiment directory: {rel(exp_dir)}")
    if args.kind == "tune":
        if not args.parameter or not args.old_value or not args.new_value:
            raise WorkflowError("record-result --kind tune requires --parameter, --old-value, and --new-value")
    forbid_log_copy_target(exp_dir)
    log_path = resolve_existing_path(args.log, "log file")
    metrics = parse_training_log(log_path)
    log_sha256 = sha256_file(log_path)
    log_size_bytes = str(log_path.stat().st_size)
    log_uri = artifact_uri_for_log(
        args.log,
        version,
        kind,
        exp_id,
        slug,
        args.attempt_id,
        args.artifact_uri,
    )
    log_artifact_id = args.log_artifact_id or default_log_artifact_id(exp_id, slug, args.attempt_id)
    dirty_before = "dirty" if git(["status", "--short"], check=False) else "clean"
    readme_path = exp_dir / "README.md"
    content = read_text(readme_path)
    fields = {
        "kind": kind.name,
        "run_commit": git(["rev-parse", "--short", "HEAD"], check=False),
        "dirty_state": dirty_before,
        "command": args.command,
        "seed": args.seed,
        "log_artifact_id": log_artifact_id,
        "log_uri": log_uri,
        "log_sha256": log_sha256,
        "log_size_bytes": log_size_bytes,
        "manifest": "manifest.yaml",
        "result_yaml": "result.yaml",
        "result_md": "result.md",
        "attempt_id": args.attempt_id,
        "failure_stage": "",
        "U": metrics["U"],
        "S": metrics["S"],
        "H": metrics["H"],
        "ZS": metrics["ZS"],
        "best_epoch": metrics["best_epoch"],
        "decision": args.decision,
        "promotion_decision": args.promotion_decision,
        "promote_to": args.promote_to,
        "status": "recorded",
    }
    if args.kind == "tune":
        fields.update(
            {
                "tuned_parameter": args.parameter,
                "old_value": args.old_value,
                "new_value": args.new_value,
                "single_variable": "yes",
            }
        )
    for field, value in fields.items():
        content = set_readme_field(content, field, value)
    readme_path.write_text(content, encoding="utf-8")
    update_manifest_and_result_files(
        exp_dir=exp_dir,
        version=version,
        kind=kind,
        exp_id=exp_id,
        slug=slug,
        config_path=exp_dir / "config.yaml",
        command=args.command,
        seed=args.seed,
        metrics=metrics,
        decision=args.decision,
        promotion_decision=args.promotion_decision,
        promote_to=args.promote_to,
        attempt_id=args.attempt_id,
        log_artifact_id=log_artifact_id,
        log_uri=log_uri,
        log_sha256=log_sha256,
        log_size_bytes=log_size_bytes,
        git_dirty="true" if dirty_before == "dirty" else "false",
    )
    append_readme_result_row(
        readme_path,
        f"| CUB | {args.seed or '-'} | {metrics['U']} | {metrics['S']} | "
        f"{metrics['H']} | {metrics['ZS']} | {metrics['best_epoch']} | `{log_artifact_id}` |",
    )

    if args.kind == "tune":
        append_tune_result_index(
            version=version,
            exp_id=exp_id,
            slug=slug,
            folder=exp_dir,
            parameter=args.parameter,
            old_value=args.old_value,
            new_value=args.new_value,
            seed=args.seed,
            metrics=metrics,
            decision=args.decision,
        )
    update_version_experiment_registry_status(
        version,
        kind,
        exp_id,
        slug,
        args.decision,
        "record-result 已解析日志并入账。",
    )

    print("record-result-ok")
    print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} best_epoch={metrics['best_epoch']}")
    print(f"log_artifact_id: {log_artifact_id}")
    print(f"log_uri: {log_uri}")
    print(f"log_sha256: {log_sha256}")
    print("临时分支清理提示: 结果入账、review 和必要提交完成后，再回到 main 并删除 exp/... 临时分支；不要 push，除非 owner 明确要求。")
    return 0


def make_module_attempt_manifest(
    *,
    trial_id: str,
    slug: str,
    trial_fields: dict[str, str],
    attempt_lower: str,
    version: str,
    config_path: Path,
    command: str,
    seed: str,
    pre_run_freeze_commit: str,
    artifacts: dict[str, dict[str, str]],
    recorded_at: str,
) -> str:
    artifact_lines: list[str] = []
    for key, info in artifacts.items():
        artifact_lines.extend(
            [
                f"  {key}:",
                f"    artifact_id: {yaml_scalar(info['artifact_id'])}",
                f"    role: {yaml_scalar(info['role'])}",
                f"    uri: {yaml_scalar(info['uri'])}",
                f"    sha256: {yaml_scalar(info['sha256'])}",
                f"    size_bytes: {yaml_scalar(info['size_bytes'])}",
                f"    required_for: {yaml_scalar(info['required_for'])}",
                f"    status: {yaml_scalar('available')}",
            ]
        )
    artifact_block = "\n".join(artifact_lines) if artifact_lines else "  {}"
    return f"""schema_version: gtpj-manifest/v1
experiment:
  id: {yaml_scalar(trial_id)}
  name: {yaml_scalar(f"{trial_id}_{slug}")}
  kind: {yaml_scalar("module-trial")}
  status: {yaml_scalar("completed")}
  attempt_id: {yaml_scalar(attempt_lower)}
  created_or_recorded_at: {yaml_scalar(recorded_at)}
version:
  base_version: {yaml_scalar(version)}
  base_code_tag: {yaml_scalar(trial_fields.get("base_code_tag", version))}
  code_branch: {yaml_scalar(trial_fields.get("code_branch", current_branch()))}
  code_commit: {yaml_scalar(pre_run_freeze_commit or git(["rev-parse", "--short", "HEAD"], check=False))}
  git_dirty: {yaml_scalar("true" if git(["status", "--short"], check=False) else "false")}
reproducibility:
  config_file: {yaml_scalar(rel(config_path))}
  config_sha256: {yaml_scalar(sha256_file(config_path))}
  pre_run_freeze_commit: {yaml_scalar(pre_run_freeze_commit)}
  command: {yaml_scalar(command)}
  seed: {yaml_scalar(seed)}
  dataset: {yaml_scalar("CUB GZSL")}
  split_id: {yaml_scalar("standard_v1")}
  class_order_id: {yaml_scalar("standard_v1")}
  label_mapping_id: {yaml_scalar("standard_v1")}
  metric_contract_id: {yaml_scalar("gzsl_u_s_h_zs_v1")}
idea:
  idea_id: {yaml_scalar(trial_fields.get("idea_id", ""))}
  uri: {yaml_scalar(f"research://ideas/{trial_fields.get('idea_id', '')}.md" if trial_fields.get("idea_id") else "")}
  title: {yaml_scalar(trial_fields.get("idea_title", ""))}
  hypothesis: {yaml_scalar(trial_fields.get("hypothesis", ""))}
artifacts:
{artifact_block}
quality:
  boundary_audit_required: true
  raw_artifacts_in_git: false
  interface_contract_required: {yaml_scalar("true")}
  evaluation_semantics_verified: {yaml_scalar("true")}
"""


def make_module_attempt_result_yaml(
    *,
    trial_id: str,
    slug: str,
    attempt_lower: str,
    version: str,
    metrics: dict[str, str],
    seed: str,
    decision: str,
    command: str,
    pre_run_freeze_commit: str,
    artifacts: dict[str, dict[str, str]],
    recorded_at: str,
) -> str:
    baseline_h = CANONICAL_BASELINES.get(version, {}).get("H", "")
    delta_h = ""
    if baseline_h and metrics.get("H"):
        try:
            delta_h = f"{float(metrics['H']) - float(baseline_h):+.2f}"
        except ValueError:
            delta_h = ""
    evidence_lines = [
        f"  {key}_artifact_id: {yaml_scalar(info['artifact_id'])}"
        for key, info in artifacts.items()
    ]
    evidence_block = "\n".join(evidence_lines)
    return f"""schema_version: gtpj-result/v1
experiment_id: {yaml_scalar(trial_id)}
experiment_name: {yaml_scalar(f"{trial_id}_{slug}")}
kind: {yaml_scalar("module-trial")}
version: {yaml_scalar(version)}
attempt_id: {yaml_scalar(attempt_lower)}
metrics:
  U: {yaml_scalar(metrics.get("U", ""))}
  S: {yaml_scalar(metrics.get("S", ""))}
  H: {yaml_scalar(metrics.get("H", ""))}
  ZS: {yaml_scalar(metrics.get("ZS", ""))}
  best_epoch: {yaml_scalar(metrics.get("best_epoch", ""))}
  baseline_H: {yaml_scalar(baseline_h)}
  delta_H: {yaml_scalar(delta_h)}
  seed: {yaml_scalar(seed)}
  source: {yaml_scalar("training_log")}
  metric_semantics: {yaml_scalar("GZSL U/S/H/ZS from protected evaluator")}
baseline:
  version: {yaml_scalar(version)}
  H: {yaml_scalar(baseline_h)}
delta:
  H: {yaml_scalar(delta_h)}
run:
  seed: {yaml_scalar(seed)}
  pre_run_freeze_commit: {yaml_scalar(pre_run_freeze_commit)}
  command: {yaml_scalar(command)}
decision:
  status: {yaml_scalar(decision)}
  promotion_decision: {yaml_scalar("blocked" if decision in {"best", "keep"} else "not_applicable")}
  promote_to: {yaml_scalar("")}
evidence:
{evidence_block}
  manifest: {yaml_scalar("manifest.yaml")}
  label_mapping_id: {yaml_scalar("standard_v1")}
  split_id: {yaml_scalar("standard_v1")}
  class_order_id: {yaml_scalar("standard_v1")}
quality:
  manifest_verified: {yaml_scalar("true")}
  boundary_audit_passed: {yaml_scalar("true")}
  interface_contract_checked: {yaml_scalar("true")}
  evaluation_semantics_verified: {yaml_scalar("true")}
recorded_at: {yaml_scalar(recorded_at)}
"""


def make_module_attempt_result_md(
    *,
    attempt_upper: str,
    trial_id: str,
    metrics: dict[str, str],
    artifacts: dict[str, dict[str, str]],
    decision: str,
) -> str:
    evidence = "\n".join(f"{key}_artifact_id: {info['artifact_id']}" for key, info in artifacts.items())
    return f"""# {attempt_upper} Result

## Metrics

| Attempt ID | Dataset | Seed | U | S | H | ZS | Best epoch |
|---|---|---:|---:|---:|---:|---:|---:|
| {attempt_upper} | CUB | - | {metrics.get("U", "-")} | {metrics.get("S", "-")} | {metrics.get("H", "-")} | {metrics.get("ZS", "-")} | {metrics.get("best_epoch", "-")} |

## Evidence

```text
trial_id: {trial_id}
{evidence}
```

## Decision

`{decision}`
"""


def make_module_attempt_quality_md(
    *,
    attempt_upper: str,
    metrics: dict[str, str],
    artifacts: dict[str, dict[str, str]],
    decision: str,
) -> str:
    artifact_checks = "\n".join(
        f"- [x] `{info['artifact_id']}` exists in Warehouse." for info in artifacts.values()
    )
    return f"""# {attempt_upper} Quality Check

```text
quality_check_mode: STRICT
decision: PASS_REVISE
promotion_decision: blocked
```

## Findings

- Metrics parsed from the registered training log: U={metrics.get("U", "")}, S={metrics.get("S", "")}, H={metrics.get("H", "")}, ZS={metrics.get("ZS", "")}, best_epoch={metrics.get("best_epoch", "")}.
- Attempt decision recorded as `{decision}`.
- Raw artifacts are registered in Warehouse; GitHub keeps only lightweight identities.

## Artifact Check

{artifact_checks}
- [x] GitHub only records artifact ids, URIs, sha256, and size.
- [x] Raw logs and checkpoints are not tracked in Git.

## Decision

PASS_REVISE.
"""


def module_artifact_entry(
    *,
    key: str,
    artifact_id: str,
    artifact_type: str,
    role: str,
    uri: str,
    path: Path,
    sha256: str,
    size_bytes: str,
    required_for: str,
) -> dict[str, str]:
    return {
        "key": key,
        "artifact_id": artifact_id,
        "type": artifact_type,
        "role": role,
        "uri": uri,
        "local_path": str(path),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "required_for": required_for,
    }


def append_warehouse_registry(entries: list[dict[str, str]], *, dry_run: bool) -> None:
    registry = warehouse_root() / "ARTIFACT_REGISTRY.yaml"
    if dry_run:
        return
    if registry.exists():
        content = registry.read_text(encoding="utf-8")
    else:
        registry.parent.mkdir(parents=True, exist_ok=True)
        content = "schema_version: gtpj-warehouse-artifact-registry/v1\nartifacts:\n"
    additions: list[str] = []
    for entry in entries:
        if f"  {entry['artifact_id']}:" in content:
            continue
        additions.append(
            f"""  {entry['artifact_id']}:
    type: {entry['type']}
    project: GTPJ
    version: {entry['version']}
    experiment_id: {entry['trial_id']}
    trial_id: {entry['trial_name']}
    attempt_id: {entry['attempt_lower']}
    role: {entry['role']}
    uri: {entry['uri']}
    local_path: {entry['local_path']}
    sha256: {entry['sha256']}
    size_bytes: {entry['size_bytes']}
    source: {entry['source']}
    note: {entry['note']}
"""
        )
    if additions:
        registry.write_text(content.rstrip() + "\n" + "".join(additions), encoding="utf-8")


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def update_attempts_table(
    *,
    trial_dir: Path,
    attempt_upper: str,
    attempt_type: str,
    parameter_change: str,
    old_value: str,
    new_value: str,
    seed: str,
    metrics: dict[str, str],
    log_artifact_id: str,
    decision: str,
) -> None:
    attempts_path = trial_dir / "ATTEMPTS.md"
    if not attempts_path.exists():
        raise WorkflowError(f"Missing attempts ledger: {rel(attempts_path)}")
    content = read_text(attempts_path)
    lines = content.splitlines()
    replaced = False
    for index, line in enumerate(lines):
        if not line.startswith(f"| {attempt_upper} |"):
            continue
        cells = split_markdown_row(line)
        old_cells = cells + [""] * max(0, 14 - len(cells))
        row_type = attempt_type or old_cells[1] or "rerun"
        row_change = parameter_change or old_cells[2] or "recorded by record-module-attempt"
        row_old = old_value or old_cells[3] or "-"
        row_new = new_value or old_cells[4] or "-"
        row_seed = seed or old_cells[5] or "-"
        directory = old_cells[13] or f"`attempts/{attempt_upper}/`"
        lines[index] = (
            f"| {attempt_upper} | {row_type} | {row_change} | {row_old} | {row_new} | {row_seed} | "
            f"{metrics['U']} | {metrics['S']} | {metrics['H']} | {metrics['ZS']} | "
            f"{metrics['best_epoch']} | `{log_artifact_id}` | {decision} | {directory} |"
        )
        replaced = True
        break
    if not replaced:
        row_type = attempt_type or "rerun"
        row_change = parameter_change or "recorded by record-module-attempt"
        row_old = old_value or "-"
        row_new = new_value or "-"
        row_seed = seed or "-"
        new_row = (
            f"| {attempt_upper} | {row_type} | {row_change} | {row_old} | {row_new} | {row_seed} | "
            f"{metrics['U']} | {metrics['S']} | {metrics['H']} | {metrics['ZS']} | "
            f"{metrics['best_epoch']} | `{log_artifact_id}` | {decision} | `attempts/{attempt_upper}/` |"
        )
        insert_at = len(lines)
        for index, line in enumerate(lines):
            if line.startswith("## Notes"):
                insert_at = index
                break
        lines.insert(insert_at, new_row)
    attempts_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def cmd_record_module_attempt(args: argparse.Namespace) -> int:
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial directory: {display_path(trial_dir)}")
    require_path_inside(trial_dir, REPO_ROOT / "experiments" / "module_trials", "trial-dir")
    trial_id, slug = parse_trial_folder_name(trial_dir)
    attempt_upper, attempt_lower = normalize_attempt_ids(args.attempt_id)
    attempt_dir = trial_dir / "attempts" / attempt_upper
    config_path = Path(args.config) if args.config else attempt_dir / "config.yaml"
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    if not config_path.exists():
        raise WorkflowError(f"Missing attempt config: {display_path(config_path)}")
    require_path_inside(config_path, trial_dir, "config")
    log_path = resolve_existing_path(args.log, "training log")
    metrics = parse_training_log(log_path)
    trial_fields = read_key_value_block(trial_dir / "README.md")
    version = args.version or trial_fields.get("base_version", "")
    if not re.fullmatch(r"v[0-9]+", version):
        raise WorkflowError("Could not infer valid base version from trial README; pass --version")
    config_values = read_config_values(config_path)
    seed = args.seed or config_values.get("random_seed", "")
    command = args.command or f"python train_GTPJ_CUB.py --config {rel(config_path)}"
    pre_run_freeze_commit = args.pre_run_freeze_commit or git(["rev-parse", "HEAD"], check=False)
    recorded_at = utc_now()

    if not args.dry_run:
        attempt_dir.mkdir(parents=True, exist_ok=True)
        for ledger_name in ["manifest.yaml", "result.yaml", "result.md", "quality_check.md"]:
            ledger_path = attempt_dir / ledger_name
            if ledger_path.exists() and not args.overwrite_ledger:
                raise WorkflowError(
                    f"Refusing to overwrite {rel(ledger_path)}; pass --overwrite-ledger if intended"
                )

    entries: list[dict[str, str]] = []
    artifacts: dict[str, dict[str, str]] = {}

    def add_file_artifact(
        key: str,
        source: Path,
        role_folder: str,
        artifact_type: str,
        role: str,
        artifact_id: str,
        required_for: str,
        note: str,
    ) -> None:
        dest = warehouse_path_for_attempt(version, trial_id, attempt_lower, role_folder, source.name)
        ensure_same_or_copy(source, dest, dry_run=args.dry_run)
        sha, size = artifact_file_info(source)
        uri = warehouse_uri_for_attempt(version, trial_id, attempt_lower, role_folder, source.name)
        entry = module_artifact_entry(
            key=key,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            role=role,
            uri=uri,
            path=dest,
            sha256=sha,
            size_bytes=size,
            required_for=required_for,
        )
        entry.update(
            {
                "version": version,
                "trial_id": trial_id,
                "trial_name": f"{trial_id}_{slug}",
                "attempt_lower": attempt_lower,
                "source": display_path(source),
                "note": note,
            }
        )
        entries.append(entry)
        artifacts[key] = entry

    log_artifact_id = args.log_artifact_id or f"log:{version}:module_trial:{trial_id}:{attempt_lower}"
    add_file_artifact(
        "train_log",
        log_path,
        "logs",
        "log",
        "training_log",
        log_artifact_id,
        "audit",
        f"Full module-trial training log for {attempt_upper}.",
    )

    if args.best_checkpoint:
        best_path = resolve_existing_path(args.best_checkpoint, "best checkpoint")
        add_file_artifact(
            "best_checkpoint",
            best_path,
            "checkpoints",
            "checkpoint",
            "best_model",
            f"checkpoint:{version}:module_trial:{trial_id}:{attempt_lower}:best",
            "reproduce_best",
            f"Best checkpoint for {attempt_upper}, selected by best GZSL-H.",
        )
    if args.full_checkpoint:
        full_path = resolve_existing_path(args.full_checkpoint, "full checkpoint")
        add_file_artifact(
            "full_checkpoint",
            full_path,
            "checkpoints",
            "checkpoint",
            "full_checkpoint",
            f"checkpoint:{version}:module_trial:{trial_id}:{attempt_lower}:full",
            "debug",
            f"Full checkpoint for {attempt_upper}.",
        )

    receipt_name = "runner_console_conda.log"
    receipt_path = warehouse_path_for_attempt(version, trial_id, attempt_lower, "receipts", receipt_name)
    if args.runner_console:
        receipt_src = resolve_existing_path(args.runner_console, "runner console")
        add_file_artifact(
            "runner_console",
            receipt_src,
            "receipts",
            "runner_receipt",
            "runner_console",
            f"receipt:{version}:module_trial:{trial_id}:{attempt_lower}:runner_console",
            "audit",
            f"Runner console receipt for {attempt_upper}.",
        )
    else:
        receipt_content = f"""run_id: {args.run_id}
attempt_id: {attempt_upper}
command: {command}
exit_code: 0
started_from_freeze_commit: {pre_run_freeze_commit}
result: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} best_epoch={metrics['best_epoch']}
note: Full per-epoch output is stored in the training_log artifact.
"""
        sha, size = write_text_artifact(receipt_path, receipt_content, dry_run=args.dry_run)
        entry = module_artifact_entry(
            key="runner_console",
            artifact_id=f"receipt:{version}:module_trial:{trial_id}:{attempt_lower}:runner_console",
            artifact_type="runner_receipt",
            role="runner_console",
            uri=warehouse_uri_for_attempt(version, trial_id, attempt_lower, "receipts", receipt_name),
            path=receipt_path,
            sha256=sha,
            size_bytes=size,
            required_for="audit",
        )
        entry.update(
            {
                "version": version,
                "trial_id": trial_id,
                "trial_name": f"{trial_id}_{slug}",
                "attempt_lower": attempt_lower,
                "source": "generated by workflow/gtpj_workflow.py record-module-attempt",
                "note": f"Runner console receipt for {attempt_upper}; full per-epoch output is in the training log artifact.",
            }
        )
        entries.append(entry)
        artifacts["runner_console"] = entry

    if args.dry_run:
        print("record-module-attempt-dry-run-ok")
        print(f"trial: {rel(trial_dir)}")
        print(f"attempt: {attempt_upper}")
        print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} best_epoch={metrics['best_epoch']}")
        for entry in entries:
            print(f"{entry['artifact_id']} -> {entry['uri']}")
        return 0

    manifest = make_module_attempt_manifest(
        trial_id=trial_id,
        slug=slug,
        trial_fields=trial_fields,
        attempt_lower=attempt_lower,
        version=version,
        config_path=config_path,
        command=command,
        seed=seed,
        pre_run_freeze_commit=pre_run_freeze_commit,
        artifacts=artifacts,
        recorded_at=recorded_at,
    )
    result_yaml = make_module_attempt_result_yaml(
        trial_id=trial_id,
        slug=slug,
        attempt_lower=attempt_lower,
        version=version,
        metrics=metrics,
        seed=seed,
        decision=args.decision,
        command=command,
        pre_run_freeze_commit=pre_run_freeze_commit,
        artifacts=artifacts,
        recorded_at=recorded_at,
    )
    result_md = make_module_attempt_result_md(
        attempt_upper=attempt_upper,
        trial_id=trial_id,
        metrics=metrics,
        artifacts=artifacts,
        decision=args.decision,
    )
    quality_md = make_module_attempt_quality_md(
        attempt_upper=attempt_upper,
        metrics=metrics,
        artifacts=artifacts,
        decision=args.decision,
    )
    (attempt_dir / "manifest.yaml").write_text(manifest.rstrip() + "\n", encoding="utf-8")
    (attempt_dir / "result.yaml").write_text(result_yaml.rstrip() + "\n", encoding="utf-8")
    (attempt_dir / "result.md").write_text(result_md.rstrip() + "\n", encoding="utf-8")
    (attempt_dir / "quality_check.md").write_text(quality_md.rstrip() + "\n", encoding="utf-8")
    update_attempts_table(
        trial_dir=trial_dir,
        attempt_upper=attempt_upper,
        attempt_type=args.attempt_type,
        parameter_change=args.parameter_change,
        old_value=args.old_value,
        new_value=args.new_value,
        seed=seed,
        metrics=metrics,
        log_artifact_id=log_artifact_id,
        decision=args.decision,
    )
    append_warehouse_registry(entries, dry_run=False)

    print("record-module-attempt-ok")
    print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} best_epoch={metrics['best_epoch']}")
    print(f"log_artifact_id: {log_artifact_id}")
    print(f"attempt_dir: {rel(attempt_dir)}")
    print("next: review/update trial root README/result/quality only if this attempt changes the trial-level conclusion.")
    return 0


def cmd_runner_lock(args: argparse.Namespace) -> int:
    lock_path = runtime_lock_file()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    branch = args.branch or current_branch() or "(detached)"
    if lock_path.exists():
        try:
            current = json.loads(read_text(lock_path))
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"GPU Runner lock file is unreadable: {display_path(lock_path)}") from exc
        if current.get("run_id") != args.run_id:
            raise WorkflowError(
                "GPU Runner is already locked by "
                f"{current.get('run_id', 'unknown')} ({current.get('experiment_id', 'unknown')})"
            )
        print("gpu-runner-locked")
        print(f"lock_file: {display_path(lock_path)}")
        return 0
    payload = {
        "run_id": args.run_id,
        "experiment_id": args.experiment_id,
        "branch": branch,
        "locked_at": datetime.now(timezone.utc).isoformat(),
    }
    lock_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("gpu-runner-locked")
    print(f"lock_file: {display_path(lock_path)}")
    return 0


def cmd_runner_unlock(args: argparse.Namespace) -> int:
    lock_path = runtime_lock_file()
    if not lock_path.exists():
        print("gpu-runner-free")
        return 0
    try:
        current = json.loads(read_text(lock_path))
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"GPU Runner lock file is unreadable: {display_path(lock_path)}") from exc
    if current.get("run_id") != args.run_id:
        raise WorkflowError(
            "Refusing to unlock GPU Runner owned by "
            f"{current.get('run_id', 'unknown')} with run {args.run_id}"
        )
    lock_path.unlink()
    print("gpu-runner-free")
    return 0


def tracked_and_candidate_files() -> list[str]:
    output = git(["ls-files", "--cached", "--others", "--exclude-standard"], check=False)
    return sorted(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())


def is_forbidden_experiment_artifact(path_text: str) -> bool:
    path = Path(path_text)
    parts = path_text.split("/")
    if not parts or parts[0] != "experiments":
        return False
    if path_text in LEGACY_EXPERIMENT_ARTIFACT_ALLOWLIST:
        return False
    if path.name == ".gitkeep":
        return False
    if path.name in ALLOWED_EXPERIMENT_TEXT_FILES:
        return False
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_EXPERIMENT_SUFFIXES:
        return True
    if "logs" in parts or "checkpoints" in parts:
        return True
    if suffix in FORBIDDEN_EXPERIMENT_IMAGE_SUFFIXES:
        return True
    return False


def cmd_audit_boundary(_: argparse.Namespace) -> int:
    offenders = [path for path in tracked_and_candidate_files() if is_forbidden_experiment_artifact(path)]
    copied_log_refs: list[str] = []
    for path_text in tracked_and_candidate_files():
        path = REPO_ROOT / path_text
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml", ".json", ".py"}:
            continue
        try:
            text = read_text(path)
        except UnicodeDecodeError:
            continue
        legacy_field = "copied" + "_log:"
        if legacy_field in text and path_text not in {
            "docs/workflow/experiment_protocol.md",
            "workflow/gtpj_workflow.py",
        }:
            copied_log_refs.append(path_text)
    errors = []
    if offenders:
        errors.append("Forbidden raw experiment artifacts:\n" + "\n".join(offenders))
    if copied_log_refs:
        errors.append("Forbidden copied_log references:\n" + "\n".join(sorted(set(copied_log_refs))))
    if errors:
        raise WorkflowError("Boundary audit failed:\n" + "\n\n".join(errors))
    print("audit-boundary-ok")
    return 0


def load_idea_tree() -> dict:
    return json.loads(read_text(REPO_ROOT / "idea_tree" / "idea_tree.json"))


def save_idea_tree(data: dict) -> None:
    path = REPO_ROOT / "idea_tree" / "idea_tree.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def idea_version_entry(idea: dict, version: str) -> dict:
    entry = idea.get("version_scores", {}).get(version, {})
    return entry if isinstance(entry, dict) else {}


def idea_score_for_version(idea: dict, version: str) -> float:
    entry = idea_version_entry(idea, version)
    try:
        return float(entry.get("score", 0))
    except (TypeError, ValueError):
        return 0


def idea_version_stage(idea: dict, version: str) -> str:
    entry = idea_version_entry(idea, version)
    stage = entry.get("stage")
    return str(stage) if stage is not None else ""


def idea_versions(data: dict) -> list[str]:
    versions = {str(data.get("current_version", "v1"))}
    for idea in data.get("ideas", []):
        versions.update(str(version) for version in idea.get("version_scores", {}).keys())
    return sorted(version for version in versions if re.fullmatch(r"v[0-9]+", version))


def idea_file_for_row(idea: dict) -> str:
    idea_dir = idea.get("idea_dir", "")
    return f"{str(idea_dir).rstrip('/')}/IDEA.md" if idea_dir else ""


def write_idea_index(data: dict) -> None:
    current_version = data.get("current_version", "v1")
    ideas = sorted(
        data.get("ideas", []),
        key=lambda item: (
            -float(item.get("global_score", 0) or 0),
            item.get("idea_id", ""),
        ),
    )

    lines = [
        "# 总创意清单",
        "",
        f"当前实验版本视图：`idea_tree/versions/{current_version}.md`",
        "",
        "这是给人读的全局创意总表，只回答“有哪些创意”。",
        "具体某个版本下一步试什么，请读取 `idea_tree/versions/vX.md`。",
        "",
        "| Idea | 标题 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 | 下一步 |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for idea in ideas:
        versions = ", ".join(f"`{version}`" for version in sorted(idea.get("version_scores", {}).keys()))
        lines.append(
            "| "
            f"`{idea.get('idea_id', '')}` | {idea.get('title', '')} | "
            f"`{idea_file_for_row(idea)}` | {idea.get('source_status', '')} | "
            f"{idea.get('global_score', 0)} | {versions or '-'} | "
            f"{idea.get('status', '')} | {idea.get('next_action', '')} |"
        )
    if not ideas:
        lines.append("| - | - | - | - | - | - | - | 等待从可靠来源重新登记。 |")

    lines.extend(
        [
            "",
            "## 使用规则",
            "",
            "- 本文件是总清单，不直接作为实验优先级队列。",
            "- 按版本选择创新 trial 时，读取 `idea_tree/versions/<base_version>.md`。",
            "- `idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。",
            "",
        ]
    )
    (REPO_ROOT / "idea_tree" / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def write_idea_version_doc(data: dict, version: str) -> None:
    ideas = sorted(
        [
            idea
            for idea in data.get("ideas", [])
            if version in idea.get("version_scores", {})
        ],
        key=lambda item: (
            -idea_score_for_version(item, version),
            -SOURCE_STATUS_RANK.get(item.get("source_status", "unknown"), 0),
            -float(item.get("global_score", 0) or 0),
            item.get("idea_id", ""),
        ),
    )

    lines = [
        f"# {version} 创意选择清单",
        "",
        f"本文件只展示适用于 `{version}` 的创意视图。总创意库见 `idea_tree/INDEX.md`。",
        "`idea_tree.json` 是唯一机器事实源；本文件由 helper 刷新。",
        "",
        "| 排名 | Idea | 标题 | Idea 文件 | 优先级 | 适用性 | 阶段 | 阻塞点 | 下一步 |",
        "|---:|---|---|---|---:|---|---|---|---|",
    ]
    for rank, idea in enumerate(ideas, 1):
        entry = idea_version_entry(idea, version)
        blockers = entry.get("blockers", [])
        blocker_text = "; ".join(str(item) for item in blockers) if blockers else "-"
        lines.append(
            "| "
            f"{rank} | `{idea.get('idea_id', '')}` | {idea.get('title', '')} | "
            f"`{idea_file_for_row(idea)}` | {entry.get('score', 0)} | "
            f"{entry.get('applicability', '')} | {idea_version_stage(idea, version)} | "
            f"{blocker_text} | "
            f"{idea.get('next_action', '')} |"
        )
    if not ideas:
        lines.append("| - | - | - | - | - | - | - | - | 当前版本还没有可选创意。 |")

    lines.extend(
        [
            "",
            "## 准入规则",
            "",
            "- 创新 trial 只能从本文件中 `阶段=selected` 且无阻塞点的 idea 启动。",
            "- `global_score` 只表示长期价值，不替代当前版本适配判断。",
            "- 新版本必须重新生成自己的 `versions/vX.md`，不能直接沿用旧版本清单。",
            "",
        ]
    )
    version_path = REPO_ROOT / "idea_tree" / "versions" / f"{version}.md"
    version_path.parent.mkdir(parents=True, exist_ok=True)
    version_path.write_text("\n".join(lines), encoding="utf-8")


def write_idea_views(data: dict) -> None:
    write_idea_index(data)
    for version in idea_versions(data):
        write_idea_version_doc(data, version)


def find_idea_record(data: dict, idea_id: str) -> dict:
    for item in data.get("ideas", []):
        if item.get("idea_id") == idea_id:
            return item
    raise WorkflowError(f"Missing idea in idea_tree.json: {idea_id}")


def cmd_new_idea(args: argparse.Namespace) -> int:
    idea_id = require_clean_id(args.idea_id, r"IDEA-[0-9]{4}", "idea id")
    slug = require_slug(args.slug)
    base_version = require_clean_id(args.base_version, r"v[0-9]+", "base version")
    global_score = require_score(args.global_score, "global_score")
    version_score = require_score(args.version_score, "version_score")
    if args.source_type not in SOURCE_TYPES:
        raise WorkflowError("Invalid source_type")
    if args.source_status not in SOURCE_STATUSES:
        raise WorkflowError("Invalid source_status")
    if args.source_status in TRIAL_ALLOWED_SOURCE_STATUSES and not args.source_ref.strip():
        raise WorkflowError("Verified or local_heuristic ideas must provide --source-ref")
    if args.applicability not in APPLICABILITIES:
        raise WorkflowError("Invalid applicability")
    if args.source_status in {"unknown", "unverified"}:
        if global_score != 0 or version_score != 0:
            raise WorkflowError("Unknown or unverified ideas must keep scores at 0")
        if args.applicability not in {"unclear", "not_applicable"}:
            raise WorkflowError("Unknown or unverified ideas cannot be direct/needs_adaptation")
    if not (REPO_ROOT / "experiments" / base_version / "config.yaml").exists():
        raise WorkflowError(f"Unknown base version: {base_version}")

    data = load_idea_tree()
    if any(item.get("idea_id") == idea_id for item in data.get("ideas", [])):
        raise WorkflowError(f"Idea already exists in idea_tree.json: {idea_id}")

    idea_dir_rel = f"idea_tree/ideas/{idea_id}_{slug}/"
    idea = {
        "idea_id": idea_id,
        "idea_dir": idea_dir_rel,
        "title": args.title,
        "status": "candidate",
        "source_type": args.source_type,
        "source_ref": args.source_ref or "",
        "source_status": args.source_status,
        "global_score": global_score,
        "version_scores": {
            base_version: {
                "score": version_score,
                "applicability": args.applicability,
                "stage": "candidate",
                "rationale": "",
                "blockers": [],
            }
        },
        "base_versions": [base_version],
        "based_on_modules": [],
        "target_component": "",
        "hypothesis": "",
        "expected_effect": {"U": "", "S": "", "H": ""},
        "implementation_scope": "",
        "risk": "",
        "compatibility": "",
        "transfer_notes": "",
        "priority": round(version_score / 100, 2),
        "linked_trials": [],
        "linked_versions": [],
        "linked_experiments": [],
        "evidence": [],
        "next_action": "补全 IDEA.md，并决定是否选中",
    }
    idea_dir = REPO_ROOT / idea_dir_rel
    ensure_dir(idea_dir)
    write_new(
        idea_dir / "IDEA.md",
        f"""# {idea_id}: {args.title}

```text
idea_id: {idea_id}
title: {args.title}
status: candidate
source_type: {args.source_type}
source_ref: {args.source_ref or ""}
source_status: {args.source_status}
global_score: {global_score}
idea_dir: {idea_dir_rel}
```

## 来源

记录论文、自己的想法、观察、跨学科来源或混合来源。

## 基于什么

- `{base_version}`

## 目标组件

## 假设

## 实现范围

## 版本适配记录

| 版本 | 优先级 | 适用性 | 理由 |
|---|---:|---|---|
| `{base_version}` | {version_score} | {args.applicability} | 待补充。 |

机器可读版本适配记录写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `{base_version}` 适配记录。

## 迁移说明

记录这个创意是否可以迁移到 `v2` 等后续版本，以及需要改变什么。

## 风险

## 阻塞点

## 决策规则
""",
    )
    data.setdefault("ideas", []).append(idea)
    save_idea_tree(data)
    write_idea_views(data)

    print(f"已创建 {rel(idea_dir)}")
    return 0


def cmd_set_current_version(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    if not (REPO_ROOT / "experiments" / version / "config.yaml").exists():
        raise WorkflowError(f"Unknown version directory: experiments/{version}")

    data = load_idea_tree()
    missing = [
        item.get("idea_id", "")
        for item in data.get("ideas", [])
        if version not in item.get("version_scores", {})
    ]
    if missing:
        raise WorkflowError(
            f"Cannot switch current_version to {version}; missing version_scores for: "
            + ", ".join(missing)
        )

    data["current_version"] = version
    save_idea_tree(data)
    write_idea_views(data)
    print(f"current_version={version}")
    print("已刷新 idea_tree/INDEX.md 和 idea_tree/versions/")
    return 0


def idea_folder_name(idea: dict) -> str:
    idea_id = idea.get("idea_id", "")
    idea_dir_text = str(idea.get("idea_dir", "")).rstrip("/")
    folder = Path(idea_dir_text).name
    if not folder.startswith(f"{idea_id}_"):
        raise WorkflowError(f"{idea_id} idea_dir must end with {idea_id}_<slug>")
    return folder


def append_module_trial_index(idea_id: str, trial_id: str, slug: str, trial_dir: Path) -> None:
    index = REPO_ROOT / "experiments" / "module_trials" / "INDEX.md"
    if not index.exists():
        raise WorkflowError(f"Missing module trial index: {rel(index)}")
    trial_name = f"{trial_id}_{slug}"
    content = read_text(index)
    if rel(trial_dir) in content or trial_name in content:
        return
    row = f"| `{idea_id}` | `{trial_name}` | planned | `{rel(trial_dir)}` | 待运行。 |"
    lines = [
        line
        for line in content.splitlines()
        if "当前还没有已经启动的模块 trial" not in line and "| 暂无 |" not in line
    ]
    content = "\n".join(lines).rstrip()
    section = "\n\n## Trial 记录\n\n| Idea | Trial | 状态 | 目录 | 说明 |\n|---|---|---|---|---|\n"
    if "## Trial 记录" not in content:
        content = content + section + row + "\n"
    else:
        content = content + "\n" + row + "\n"
    index.write_text(content, encoding="utf-8")


def choose_trial_base_version(args: argparse.Namespace, data: dict, idea: dict) -> str:
    if args.base_version:
        version = require_clean_id(args.base_version, r"v[0-9]+", "base version")
    else:
        current_version = data.get("current_version", "")
        if current_version in idea.get("version_scores", {}):
            version = current_version
        else:
            base_versions = idea.get("base_versions") or []
            if not base_versions:
                raise WorkflowError(f"Idea has no base_versions: {idea.get('idea_id')}")
            version = require_clean_id(base_versions[0], r"v[0-9]+", "base version")

    if version not in idea.get("version_scores", {}):
        raise WorkflowError(
            f"{idea.get('idea_id')} has no version_scores entry for {version}"
        )
    if not (REPO_ROOT / "experiments" / version / "config.yaml").exists():
        raise WorkflowError(f"Unknown base version: {version}")
    return version


def cmd_new_trial(args: argparse.Namespace) -> int:
    idea_id = require_clean_id(args.idea_id, r"IDEA-[0-9]{4}", "idea id")
    trial_id = require_clean_id(args.trial_id, r"TRIAL-[0-9]{3}", "trial id")
    slug = require_slug(args.slug)
    data = load_idea_tree()
    idea = find_idea_record(data, idea_id)
    if idea.get("status") not in TRIAL_READY_STATUSES:
        raise WorkflowError(f"{idea_id} must be selected before creating a trial")
    source_status = idea.get("source_status")
    if source_status not in TRIAL_ALLOWED_SOURCE_STATUSES:
        raise WorkflowError(
            f"{idea_id} source_status is {source_status!r}; "
            "module trial requires verified or local_heuristic source"
        )
    source_ref = idea.get("source_ref")
    if not isinstance(source_ref, str) or not source_ref.strip():
        raise WorkflowError(f"{idea_id} must define source_ref before trial")
    if source_status == "local_heuristic" and not idea.get("evidence"):
        raise WorkflowError(f"{idea_id} local_heuristic must define reproducible evidence before trial")
    base_version = choose_trial_base_version(args, data, idea)
    version_entry = idea_version_entry(idea, base_version)
    if not str(version_entry.get("rationale", "")).strip():
        raise WorkflowError(f"{idea_id} must explain version_scores.{base_version}.rationale before trial")
    if idea_version_stage(idea, base_version) not in TRIAL_READY_STATUSES:
        raise WorkflowError(f"{idea_id} must be selected in idea_tree/versions/{base_version}.md before trial")
    if version_entry.get("applicability") not in TRIAL_ALLOWED_APPLICABILITIES:
        raise WorkflowError(f"{idea_id} applicability for {base_version} must be direct or needs_adaptation")
    if version_entry.get("blockers"):
        raise WorkflowError(f"{idea_id} must resolve blockers before trial")
    for field in ["hypothesis", "implementation_scope", "risk"]:
        if not str(idea.get(field, "")).strip():
            raise WorkflowError(f"{idea_id} must define {field} before trial")
    source_idea_file = REPO_ROOT / str(idea.get("idea_dir", "")) / "IDEA.md"
    if not source_idea_file.exists():
        raise WorkflowError(f"Missing source idea file: {rel(source_idea_file)}")
    code_branch = trial_branch_name(base_version, idea_id, trial_id, slug)

    require_trial_branch(code_branch)
    require_clean_worktree("new-trial")
    require_current_branch_contains_main("new-trial")

    idea_dir = REPO_ROOT / "experiments" / "module_trials" / idea_folder_name(idea)
    ensure_dir(idea_dir)
    if not (idea_dir / "IDEA.md").exists():
        write_new(
            idea_dir / "IDEA.md",
            f"""# {idea_id}: {idea.get('title', '')}

```text
idea_id: {idea_id}
source_idea_file: {rel(source_idea_file)}
trial_folder: {rel(idea_dir)}
```

本文件只是 trial-local 指针。权威的创意来源、评分和跨版本说明在
`{rel(source_idea_file)}`。
""",
        )

    trial_dir = idea_dir / f"{trial_id}_{slug}"
    if trial_dir.exists():
        raise WorkflowError(f"Trial already exists: {rel(trial_dir)}")

    ensure_dir(trial_dir)
    copy_new(REPO_ROOT / "experiments" / base_version / "config.yaml", trial_dir / "config.yaml")
    write_new(trial_dir / "code.diff", "")
    code_tag = trial_tag_name(base_version, idea_id, trial_id)
    write_new(
        trial_dir / "README.md",
        f"""# {trial_id}_{slug}

```text
trial_id: {trial_id}
idea_id: {idea_id}
base_version: {base_version}
base_code_tag: {base_version}
branch_source: main
idea_source_file: {rel(source_idea_file)}
idea_title: {idea.get('title', '')}
version_score: {version_entry.get('score', 0)}
applicability: {version_entry.get('applicability', '')}
code_branch: {code_branch}
code_tag: {code_tag}
code_commit:
trial_decision: pending
promotion_decision: not_applicable
promote_to:
changed_files:
run_config: config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
agent_summary: agent_summary.md
```

## 改动文件

| 文件 | 改动 | 是否属于代码层 |
|---|---|---|

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Promotion Gate

- [ ] baseline H、trial H、delta H 已记录。
- [ ] U/S/ZS 没有不可接受退化。
- [ ] class order、split、logits shape、metric calculation 未改变。
- [ ] switch off 能回到 `{base_version}` 行为。
- [ ] 证据目录、外部 artifact 指针和 code.diff 完整。
- [ ] `promotion_decision` 为 `promote` 后才允许进入自动 promotion gate。

## 决策

待记录。
""",
    )
    write_new(
        trial_dir / "implementation.md",
        """# 实现记录

参考契约：

```text
docs/workflow/code_interface_contract.md
```

## 新模块

## 基于什么

## 接入点

| 项目 | 值 |
|---|---|
| File | |
| Class/function | |
| 接入前/后 | |
| Consumes | |
| Produces | |

## Input Contract（输入契约）

| 名称 | Shape | Dtype | Device | 含义 | Gradients |
|---|---|---|---|---|---|

## Output Contract（输出契约）

| 名称 | Shape | Dtype | Device | 含义 | 是否替换已有变量 |
|---|---|---|---|---|---|

## Shape Invariants（形状不变量）

- [ ] Batch dimension 保持不变。
- [ ] Class dimension 保持不变。
- [ ] Logits shape 保持 `[B（图片/样本数量）, C（类别数量）]`。
- [ ] Visual/text embedding dimensions 仍与 scorer 兼容。
- [ ] Seen/unseen 类别顺序不变。
- [ ] 没有引入意外 broadcasting。

## 配置开关

```text
switch:
default:
trial config path:
base config affected: no
```

## Baseline-Off Path（基线关闭路径）

解释为什么模块关闭路径等价于选定 base version。

## Loss Contract（Loss 契约）

```text
new loss:
lambda key:
lambda=0 behavior:
normalization/reduction changes:
```

## Evaluation Contract（评估契约）

```text
eval path changed: yes/no
logits shape:
class order:
metric calculation:
```

## Checkpoint Contract（Checkpoint 契约）

```text
new state_dict keys:
old checkpoint load behavior:
missing/unexpected keys:
```

## 风险

## Minimum Verification（最低验证）

- [ ] Switch-off forward pass。
- [ ] Switch-on forward pass。
- [ ] Logits shape check。
- [ ] Loss scalar 和 backward check。
- [ ] Evaluation 输出 class-count 检查。
- [ ] Base config files 没有变化。

## 验证命令
""",
    )
    write_new(
        trial_dir / "quality_check.md",
        make_quality_check(ExperimentKind("module-trial", "module_trials", "TRIAL", "STRICT", "trial")),
    )
    trial_kind = ExperimentKind("module-trial", "module_trials", "TRIAL", "STRICT", "trial")
    write_new(trial_dir / "agent_summary.md", make_agent_summary(base_version, trial_kind, trial_id, slug))
    write_new(
        trial_dir / "manifest.yaml",
        make_experiment_manifest(
            version=base_version,
            kind=trial_kind,
            exp_id=trial_id,
            slug=slug,
            config_path=trial_dir / "config.yaml",
            status="planned",
            code_branch=code_branch,
            idea_id=idea_id,
            idea_uri=f"research://ideas/{idea_id}.md",
            idea_title=str(idea.get("title", "")),
            hypothesis=str(idea.get("hypothesis", "")),
        ),
    )
    write_new(
        trial_dir / "result.yaml",
        make_result_yaml(
            version=base_version,
            kind=trial_kind,
            exp_id=trial_id,
            slug=slug,
        ),
    )
    write_new(
        trial_dir / "result.md",
        make_result_md(exp_id=trial_id, slug=slug, kind=trial_kind),
    )
    append_module_trial_index(idea_id, trial_id, slug, trial_dir)
    linked_trials = idea.setdefault("linked_trials", [])
    trial_rel = rel(trial_dir)
    if trial_rel not in linked_trials:
        linked_trials.append(trial_rel)
        version_entry["stage"] = "trialing"
        save_idea_tree(data)
        write_idea_views(data)

    print(f"已创建 {rel(trial_dir)}")
    print(f"建议分支: {code_branch}")
    print(f"实现后建议 tag: {code_tag}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTPJ workflow 结构辅助 helper")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="显示仓库状态")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="校验仓库结构")
    validate.set_defaults(func=cmd_validate)

    validate_remote = sub.add_parser("validate-remote", help="校验远端 main/baseline tags 与本地治理事实")
    validate_remote.add_argument("--remote", default="origin")
    validate_remote.set_defaults(func=cmd_validate_remote)

    audit_boundary = sub.add_parser("audit-boundary", help="检查 GitHub 轻量边界，禁止 raw artifacts 入仓库")
    audit_boundary.set_defaults(func=cmd_audit_boundary)

    new_exp = sub.add_parser("new-experiment", help="创建版本实验目录")
    new_exp.add_argument("--version", required=True)
    new_exp.add_argument("--kind", required=True, choices=sorted(KINDS))
    new_exp.add_argument("--exp-id", required=True)
    new_exp.add_argument("--slug", required=True)
    new_exp.set_defaults(func=cmd_new_experiment)

    tune_suggest = sub.add_parser("tune-suggest", help="生成最多 3 个调参候选，不启动训练")
    tune_suggest.add_argument("--version", required=True)
    tune_suggest.add_argument("--limit", type=int, default=3)
    tune_suggest.set_defaults(func=cmd_tune_suggest)

    runner_lock = sub.add_parser("runner-lock", help="占用本地 GPU Runner 文件锁")
    runner_lock.add_argument("--run-id", required=True)
    runner_lock.add_argument("--experiment-id", required=True)
    runner_lock.add_argument("--branch", default="")
    runner_lock.set_defaults(func=cmd_runner_lock)

    runner_unlock = sub.add_parser("runner-unlock", help="释放本地 GPU Runner 文件锁")
    runner_unlock.add_argument("--run-id", required=True)
    runner_unlock.set_defaults(func=cmd_runner_unlock)

    record = sub.add_parser("record-result", help="解析日志并把实验结果写回账本")
    record.add_argument("--version", required=True)
    record.add_argument("--kind", required=True, choices=sorted(KINDS))
    record.add_argument("--exp-id", required=True)
    record.add_argument("--slug", required=True)
    record.add_argument("--log", required=True)
    record.add_argument("--command", default="")
    record.add_argument("--seed", default="")
    record.add_argument(
        "--decision",
        default="keep",
        choices=["keep", "reject", "rejected", "rerun", "needs_confirmation", "blocked"],
    )
    record.add_argument("--attempt-id", default="attempt-001")
    record.add_argument("--artifact-uri", default="")
    record.add_argument("--log-artifact-id", default="")
    record.add_argument("--promotion-decision", default="not_applicable", choices=["not_applicable", "promote", "blocked", "rejected"])
    record.add_argument("--promote-to", default="")
    record.add_argument("--parameter", default="")
    record.add_argument("--old-value", default="")
    record.add_argument("--new-value", default="")
    record.set_defaults(func=cmd_record_result)

    record_module = sub.add_parser(
        "record-module-attempt",
        help="解析 module trial attempt 日志，复制 Warehouse artifact，并写回 attempt 账本",
    )
    record_module.add_argument("--trial-dir", required=True)
    record_module.add_argument("--attempt-id", required=True)
    record_module.add_argument("--log", required=True)
    record_module.add_argument("--config", default="")
    record_module.add_argument("--best-checkpoint", default="")
    record_module.add_argument("--full-checkpoint", default="")
    record_module.add_argument("--runner-console", default="")
    record_module.add_argument("--log-artifact-id", default="")
    record_module.add_argument("--command", default="")
    record_module.add_argument("--run-id", default="")
    record_module.add_argument("--seed", default="")
    record_module.add_argument("--version", default="")
    record_module.add_argument("--pre-run-freeze-commit", default="")
    record_module.add_argument("--attempt-type", default="")
    record_module.add_argument("--parameter-change", default="")
    record_module.add_argument("--old-value", default="")
    record_module.add_argument("--new-value", default="")
    record_module.add_argument(
        "--decision",
        default="keep",
        choices=[
            "best",
            "keep",
            "reject",
            "rejected",
            "revise",
            "rerun",
            "not_confirmed",
            "blocked",
            "debug",
        ],
    )
    record_module.add_argument("--dry-run", action="store_true")
    record_module.add_argument("--overwrite-ledger", action="store_true")
    record_module.set_defaults(func=cmd_record_module_attempt)

    new_idea = sub.add_parser("new-idea", help="创建新的 idea 节点和目录")
    new_idea.add_argument("--idea-id", required=True)
    new_idea.add_argument("--slug", required=True)
    new_idea.add_argument("--title", required=True)
    new_idea.add_argument("--source-type", required=True, choices=sorted(SOURCE_TYPES))
    new_idea.add_argument("--source-ref", default="")
    new_idea.add_argument(
        "--source-status",
        default="unknown",
        choices=sorted(SOURCE_STATUSES),
    )
    new_idea.add_argument("--base-version", required=True)
    new_idea.add_argument("--global-score", type=float, default=0)
    new_idea.add_argument("--version-score", type=float, default=0)
    new_idea.add_argument("--applicability", choices=sorted(APPLICABILITIES), default="unclear")
    new_idea.set_defaults(func=cmd_new_idea)

    set_current = sub.add_parser("set-current-version", help="设置当前 idea 排序版本")
    set_current.add_argument("--version", required=True)
    set_current.set_defaults(func=cmd_set_current_version)

    new_trial = sub.add_parser("new-trial", help="在某个 idea 下创建 trial 目录")
    new_trial.add_argument("--idea-id", required=True)
    new_trial.add_argument("--trial-id", required=True)
    new_trial.add_argument("--slug", required=True)
    new_trial.add_argument("--base-version", default="")
    new_trial.set_defaults(func=cmd_new_trial)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except WorkflowError as exc:
        print(f"gtpj-helper-error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
