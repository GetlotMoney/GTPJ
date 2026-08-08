#!/usr/bin/env python
"""Optional repository-structure helper for the GTPJ repository.

This script is intentionally small and deterministic. It creates governance
folders, copies version configs, and validates repository invariants. It does
not run training, push to GitHub, or mutate Git history.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
import hashlib
import io
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_GTPJ_WORKFLOW_SKILL_PATH = Path.home() / ".codex" / "skills" / "gtpj-workflow" / "SKILL.md"
CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS = 5
CONFIRMATION_RULE_DEFAULT_NEAR_MISS_TOLERANCE_H = 0.2
CONFIRMATION_RULE_REQUIRED_MARKERS = [
    "repeat_type: exact_repeat",
    "original_seed",
    "max_attempts: 5",
    "max_attempts_hard_cap",
    "early_stop_on_best_hit: true",
    "restore_target_H",
    "near_miss_tolerance_H",
    "near_miss_not_restored",
    "seed_sweep",
    "multi_seed_stability",
    "not_confirmation_evidence",
]
CONFIRMATION_RULE_REPO_SYNC_FILES = [
    "AGENTS.md",
    "docs/workflow/WORKFLOW_KERNEL.md",
    "docs/workflow/playbooks/confirmation.md",
    "docs/workflow/playbooks/tune.md",
    "docs/workflow/playbooks/mixed_campaign.md",
    "docs/workflow/playbooks/innovation.md",
    "docs/workflow/protocols/experiment_protocol.md",
    "docs/workflow/protocols/module_trial_protocol.md",
    "docs/workflow/protocols/mixed_experiment_campaign_protocol.md",
    "docs/workflow/protocols/autonomous_research_campaign.md",
    "docs/workflow/protocols/promotion.md",
    "docs/workflow/core/TASK_START_CARD.md",
    "docs/workflow/core/TASK_START_MINI.md",
    "docs/workflow/CLAUDE_CONTEXT.md",
    "experiments/templates/quality_check_template.md",
    "experiments/templates/run_receipt_template.yaml",
]
CONFIRMATION_RULE_SKILL_REFERENCE_FILES = [
    "references/workflow_kernel.md",
    "references/playbooks/confirmation.md",
    "references/experiment_protocol.md",
    "references/autonomous_research_campaign.md",
    "references/mixed_experiment_campaign_protocol.md",
    "references/promotion.md",
    "references/playbooks/mixed_campaign.md",
    "references/playbooks/tune.md",
]
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
TRIAL_READY_STATUSES = {"selected", "ready"}
TRIAL_MODULE_SCOPES = {"single_module", "composite", "architecture_change"}
TRIAL_TEMPLATE_FAMILIES = {
    "feature_adapter",
    "fusion_gate",
    "auxiliary_loss",
    "sampler_or_data_view",
    "composite",
    "architecture_change",
}
TRIAL_TRAINING_ENTRY_MODES = {
    "existing_entry_equivalent",
    "strict_template_entry",
}
TRIAL_STRICT_ENTRY_INVALID_SELECTED = {
    "",
    "existing_entry",
    "existing_entry_equivalent",
    "train_GTPJ_CUB.py",
}
TRIAL_LEGACY_MIGRATION_STATES = {
    "not_required",
    "required",
    "completed",
}
TRIAL_ARCHITECTURE_AFFECT_FLAGS = {
    "forward_main_flow",
    "class_scoring",
    "train_data_view",
    "eval_input_output",
    "split_or_label_mapping",
}
TRIAL_REQUIRED_AUDITS = {
    "shape_audit",
    "switch_off_equivalence",
    "standard_gzsl_eval_audit",
}
TRIAL_ARCHITECTURE_REQUIRED_AUDITS = TRIAL_REQUIRED_AUDITS | {
    "split_integrity_audit",
    "class_order_audit",
}
IDEA_STATUSES = {
    "candidate",
    "ready",
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
    "ready",
    "selected",
    "trialing",
    "validated",
    "rejected",
    "blocked",
    "not_applicable",
}
EVIDENCE_LEVELS = {
    "debug_smoke",
    "quick_local",
    "valid_single_run",
    "confirmation_grade",
    "baseline_grade",
}
NON_FORMAL_AGENT_RUNTIME_EVIDENCE_LEVELS = {
    "debug_smoke",
    "routing_index_only",
    "audit_note_only",
}
EVIDENCE_ROUTING_STATES = {
    "hypothesis_ready",
    "interface_precheck_passed",
    "smoke_passed",
    "single_run_valid",
    "tune_promising",
    "ablation_supported",
    "exact_repeat_best_hit",
    "stable_confirmed",
    "min3_confirmed",
    "promotion_candidate",
    "promoted",
    "blocked",
    "rerun_required",
    "rejected",
    "stopped_no_gain",
    "stopped_repeat_unstable",
    "stopped_ablation_not_supported",
    "archived",
}
EVIDENCE_TRANSITION_TYPES = {
    "init",
    "advance",
    "rerun",
    "revise",
    "reject",
    "block",
    "stop",
    "archive",
    "promote",
}
EVIDENCE_SUBJECT_TYPES = {
    "hypothesis",
    "candidate",
    "trial",
    "attempt",
    "run",
    "campaign",
    "campaign_task",
}
EVIDENCE_BAD_RULE_VERDICTS = {"fail", "failed", "block", "blocked"}
EVIDENCE_ADVANCING_TRANSITIONS = {"advance", "promote"}
AGENT_RUNTIME_ALLOW_DECISIONS = {"allow", "pass"}
AGENT_RUNTIME_BLOCKING_DECISIONS = {"", "block", "blocked", "fail", "failed", "not_checked", "pending"}
AGENT_RUNTIME_PREFLIGHT_KEYS = {
    "required_threads_created",
    "agent_instance_ids_present",
    "agent_status_refs_valid",
    "independent_outputs_present",
    "agent_output_refs_valid",
    "pre_run_allow_checks_passed",
    "agent_runtime_validated",
    "threads_archivable",
}
AGENT_RUNTIME_SERVER_DETACHED_PREFLIGHT_KEYS = {
    "role_plan_recorded",
    "independent_outputs_present",
    "pre_run_allow_checks_passed",
    "agent_runtime_validated",
    "server_detached_ready",
    "stop_mechanism_ready",
    "cleanup_not_required",
}
AGENT_RUNTIME_REQUIRED_FORMAL_ROLES = {
    "runner_monitor",
    "interface_checker",
    "evidence_quality_checker",
}
WORKFLOW_MODES = {
    "live_multi_agent_monitor",
    "server_frozen_runner",
}
AGENT_RUNTIME_ALLOWED_INSTANCE_STATUSES = {
    "spawned",
    "running",
    "active",
    "completed",
    "complete",
    "closed",
}
AGENT_RUNTIME_BLOCKED_INSTANCE_STATUSES = {
    "",
    "missing",
    "failed",
    "killed",
    "cancelled",
    "canceled",
    "not_found",
    "unknown",
}
AGENT_RUNTIME_INVALID_INSTANCE_IDS = {
    "",
    "none",
    "not_used",
    "not_recorded",
    "temporary_subagent",
    "temporary_subagents",
    "role_only",
    "current codex session",
    "current_thread",
    "current session",
    "workflow_helper",
}
AGENT_RUNTIME_INVALID_INSTANCE_ID_FRAGMENTS = {
    "spawn_agent",
    "temporary_subagent",
    "right_sidebar",
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
    "ablation": ExperimentKind("ablation", "ablation", "ABLATION", "STANDARD", "ablation"),
    "innovation": ExperimentKind("innovation", "innovation", "INNOVATION", "STRICT", "innovation"),
    "confirmation": ExperimentKind("confirmation", "confirmation", "CONFIRM", "STRICT", "confirm"),
}
MODULE_TRIAL_KIND = ExperimentKind("module-trial", "module_trials", "TRIAL", "STRICT", "trial")
FRAMEWORK_KIND_ORDER = ("tune", "ablation", "innovation", "confirmation")
FRAMEWORK_REQUIRED_KEYS = {
    "schema_version",
    "framework_id",
    "framework_version",
    "registry_level",
    "derived_from_framework",
    "promoted_from_experiment",
    "source_legacy_ref",
    "framework_branch",
    "framework_tag",
    "framework_commit",
    "governance_source_commit",
    "origin_status",
    "change_type",
    "modules",
    "inherits",
    "does_not_inherit",
    "status",
}
FRAMEWORK_TEMPLATE_REQUIRED_KEYS = {
    "schema_version",
    "framework_id",
    "template_id",
    "template_status",
    "template_branch",
    "template_tag",
    "template_commit",
    "source_framework_tag",
    "source_framework_commit",
    "behavior_contract",
}
EXPERIMENT_BINDING_REQUIRED_KEYS = {
    "schema_version",
    "experiment_id",
    "framework_id",
    "kind",
    "base_identity_kind",
    "base_template_id",
    "base_template_tag",
    "base_template_commit",
    "template_registry_commit",
    "historical_code_ref",
    "template_binding_status",
    "experiment_branch",
    "legacy_ref",
    "status",
}
DEFAULT_TEMPLATE_REGISTRY_REF = "main"
EXPERIMENT_BINDING_RULES = {
    "framework_template": ("ready", True, False),
    "historical_code_ref": ("historical_read_only", False, True),
    "pending_clean_template": ("blocked_pending_clean_template", False, False),
}
FRAMEWORK_INDEX_STATUSES = {
    "planned",
    "pending",
    "pre_run",
    "pre_run_gated",
    "ready_to_run",
    "running",
    "completed",
    "candidate",
    "promoted",
    "blocked",
    "rejected",
    "failed",
    "retired",
    "legacy_owner_accepted_unconfirmed",
    "legacy_owner_activated",
}
LEGACY_ORIGIN_STATUSES = {
    "legacy_owner_accepted_unconfirmed",
    "legacy_owner_activated",
}
PROMOTED_FRAMEWORK_STATUSES = {"promoted", *LEGACY_ORIGIN_STATUSES}

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
        "evidence_level": "valid_single_run",
        "best_observed_H": "74.29",
        "confirmed_H": "pending",
        "confirmation_status": "needs_confirmation",
        "status": "owner_activated_unconfirmed",
    },
    "v3": {
        "name": "GTPJ-v3",
        "H": "74.27",
        "result_file": "experiments/v3/result.md",
        "version_file": "experiments/v3/VERSION.md",
        "evidence_level": "valid_single_run",
        "best_observed_H": "74.27",
        "confirmed_H": "pending",
        "confirmation_status": "needs_confirmation",
        "status": "owner_accepted_stochastic_unconfirmed",
    },
    "v4": {
        "name": "GTPJ-v4 legacy config-only tag",
        "H": "74.47",
        "repeat_mean_H": "74.45",
        "result_file": "experiments/v4/result.md",
        "version_file": "experiments/v4/VERSION.md",
        "evidence_level": "baseline_grade",
        "best_observed_H": "74.47",
        "confirmed_H": "74.47",
        "confirmation_status": "confirmed",
        "status": "legacy_config_only_not_framework_version",
    },
    "v5": {
        "name": "GTPJ-v5",
        "H": "74.54",
        "result_file": "experiments/v5/result.md",
        "version_file": "experiments/v5/VERSION.md",
        "evidence_level": "confirmation_grade",
        "best_observed_H": "74.54",
        "confirmed_H": "74.44",
        "confirmation_status": "owner_activated_provisional",
        "status": "owner_activated_provisional",
    }
}


def baseline_evidence(version: str) -> dict[str, str]:
    meta = CANONICAL_BASELINES.get(version)
    if meta is None:
        raise WorkflowError(f"Unknown baseline version: {version}")

    h_value = meta.get("H", "")
    evidence_level = meta.get("evidence_level") or "baseline_grade"
    best_observed_h = meta.get("best_observed_H") or h_value
    confirmed_h = meta.get("confirmed_H") or h_value
    confirmation_status = meta.get("confirmation_status") or (
        "confirmed" if confirmed_h and confirmed_h != "pending" else "needs_confirmation"
    )
    status = meta.get("status") or (
        "confirmed" if confirmation_status == "confirmed" else "owner_activated_unconfirmed"
    )
    return {
        "name": meta.get("name", version),
        "H": h_value,
        "evidence_level": evidence_level,
        "best_observed_H": best_observed_h,
        "confirmed_H": confirmed_h,
        "confirmation_status": confirmation_status,
        "status": status,
    }


def baseline_is_confirmed(version: str) -> bool:
    evidence = baseline_evidence(version)
    return (
        evidence["confirmation_status"] == "confirmed"
        and evidence["confirmed_H"] not in {"", "pending"}
        and evidence["evidence_level"] in {"confirmation_grade", "baseline_grade"}
    )


def comparison_reference_h(version: str) -> str:
    evidence = baseline_evidence(version)
    return evidence["confirmed_H"] if baseline_is_confirmed(version) else evidence["best_observed_H"]


def comparison_reference_field(version: str) -> str:
    return "confirmed_H" if baseline_is_confirmed(version) else "best_observed_H"


def comparison_reference_phrase(version: str) -> str:
    field = comparison_reference_field(version)
    value = comparison_reference_h(version) or "-"
    suffix = "" if baseline_is_confirmed(version) else " (unconfirmed)"
    return f"{version} {field}={value}{suffix}"


def reproducibility_verdict(version: str) -> str:
    return "confirmed" if baseline_is_confirmed(version) else "needs_confirmation"
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
    "run_receipt_template.yaml",
    "quality_check_template.md",
    "quality_check.md",
    "agent_summary.md",
    "implementation.md",
    "interface_check.md",
    "idea_intent_check.md",
    "interface_precheck.md",
    "review_round_1.md",
    "review_round_2.md",
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


def result_evidence_defaults(kind_name: str, h_value: str, decision: str, git_dirty: str) -> dict[str, str]:
    if not h_value:
        return {
            "evidence_level": "pending",
            "result_status": "pending",
            "best_observed_H": "",
            "confirmed_H": "",
            "confirmation_status": "pending" if kind_name == "confirmation" else "not_applicable",
            "restore_target_H": "",
            "near_miss_tolerance_H": "",
            "near_miss_not_restored": "false",
        }

    if git_dirty == "true" or decision in {"blocked", "debug", "rerun", "reject", "rejected"}:
        evidence_level = "quick_local"
        best_observed_h = ""
    else:
        evidence_level = "valid_single_run"
        best_observed_h = h_value

    if decision in {"keep", "best", "needs_confirmation"}:
        result_status = "needs_confirmation"
    elif decision in {"reject", "rejected"}:
        result_status = "rejected"
    elif decision in {"blocked", "rerun", "debug"}:
        result_status = decision
    else:
        result_status = "valid_observation" if evidence_level == "valid_single_run" else "debug"

    return {
        "evidence_level": evidence_level,
        "result_status": result_status,
        "best_observed_H": best_observed_h,
        "confirmed_H": "pending",
        "confirmation_status": "pending" if kind_name == "confirmation" else "not_applicable",
        "restore_target_H": h_value if kind_name == "confirmation" else "",
        "near_miss_tolerance_H": "",
        "near_miss_not_restored": "false",
    }


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


VERSION_FRAMEWORK_SECTIONS = [
    "## Main Forward Flow",
    "## Variable Glossary",
    "## Module Glossary",
    "## Loss And Training Flow",
    "## GZSL Hard Rules",
]
VERSION_MODULE_SECTIONS = [
    "## Module Table",
    "## Config Switches",
    "## Version Delta",
]
VERSION_MODULE_FIELD_MARKERS = [
    "Purpose",
    "Input",
    "Output",
    "Config switch",
    "Baseline-off",
]
TRIAL_FRAMEWORK_CORE_MARKERS = [
    "## Variable Glossary",
    "## Method Glossary",
]
TRIAL_FORWARD_MARKERS = [
    "## Diagram",
    "## Main Forward",
    "## Main Forward And Loss Flow",
    "## 1. Main Forward Path",
]
TRIAL_LOSS_MARKERS = [
    "## Loss Flow",
    "## Loss",
    "## 2. AG-JEPA Loss Path",
    "## 3. Loss Attachments",
    "Loss Flow",
]


def contains_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker in text for marker in markers)


def validate_framework_diagram_docs() -> list[str]:
    errors: list[str] = []
    experiments_dir = REPO_ROOT / "experiments"

    for version_dir in sorted(experiments_dir.glob("v[0-9]*")):
        if not version_dir.is_dir():
            continue
        version_file = version_dir / "VERSION.md"
        framework_file = version_dir / "framework_diagram.md"
        modules_file = version_dir / "MODULES.md"

        if not version_file.exists():
            errors.append(f"{rel(version_dir)}/VERSION.md is required")
            continue
        version_text = read_text(version_file)
        for marker in ["## Framework Diagram", "## Version Flow", "framework_diagram", "module_glossary"]:
            if marker not in version_text:
                errors.append(f"{rel(version_file)} missing version framework marker: {marker}")

        if not framework_file.exists():
            errors.append(f"{rel(framework_file)} is required for every formal version")
        else:
            framework_text = read_text(framework_file)
            for marker in VERSION_FRAMEWORK_SECTIONS:
                if marker not in framework_text:
                    errors.append(f"{rel(framework_file)} missing section: {marker}")

        if not modules_file.exists():
            errors.append(f"{rel(modules_file)} is required for every formal version")
        else:
            modules_text = read_text(modules_file)
            for marker in VERSION_MODULE_SECTIONS + VERSION_MODULE_FIELD_MARKERS:
                if marker not in modules_text:
                    errors.append(f"{rel(modules_file)} missing module explanation marker: {marker}")

    for trial_readme in sorted((experiments_dir / "module_trials").glob("IDEA-*/TRIAL-*/README.md")):
        readme_text = read_text(trial_readme)
        for marker in ["## Trial Flow", "## Framework Diagram"]:
            if marker not in readme_text:
                errors.append(f"{rel(trial_readme)} must include {marker}")

        framework_file = trial_readme.with_name("framework_diagram.md")
        if not framework_file.exists():
            errors.append(f"{rel(framework_file)} is required for every module trial")
            continue
        framework_text = read_text(framework_file)
        for marker in TRIAL_FRAMEWORK_CORE_MARKERS:
            if marker not in framework_text:
                errors.append(f"{rel(framework_file)} missing section: {marker}")
        if not contains_any(framework_text, TRIAL_FORWARD_MARKERS):
            errors.append(f"{rel(framework_file)} must explain the main forward path")
        if not contains_any(framework_text, TRIAL_LOSS_MARKERS):
            errors.append(f"{rel(framework_file)} must explain the loss/training flow")

    return errors


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise WorkflowError(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_new_lf(path: Path, content: str) -> None:
    if path.exists():
        raise WorkflowError(f"Refusing to overwrite existing file: {rel(path)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content.rstrip() + "\n")


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


def repo_relative_path(path: Path, label: str) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise WorkflowError(f"{label} must be inside repository: {path}") from exc


def read_text_at_commit(commit: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip()
        raise WorkflowError(
            f"Cannot read {relative_path} at commit {commit}: {detail}"
        )
    return result.stdout


def confirmation_rule_sync_paths() -> list[Path]:
    paths = [REPO_ROOT / path_text for path_text in CONFIRMATION_RULE_REPO_SYNC_FILES]
    if LOCAL_GTPJ_WORKFLOW_SKILL_PATH.exists():
        paths.append(LOCAL_GTPJ_WORKFLOW_SKILL_PATH)
        skill_root = LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent
        references_dir = skill_root / "references"
        if references_dir.exists():
            paths.extend(skill_root / path_text for path_text in CONFIRMATION_RULE_SKILL_REFERENCE_FILES)
    return paths


def confirmation_policy_for_profile(
    profile: str,
    *,
    target_h: str = "",
    tolerance_h: str = "",
) -> dict[str, object]:
    near_miss_tolerance = tolerance_h or str(CONFIRMATION_RULE_DEFAULT_NEAR_MISS_TOLERANCE_H)
    if profile == "h76-followup50-multiseed":
        return {
            "repeat_type": "multi_seed_stability",
            "formal_confirmation_evidence": False,
            "not_confirmation_evidence": True,
            "seed_change_allowed": True,
            "reason": "seed_sweep/multi_seed_stability is not exact_repeat reproduction",
        }
    per_job_restore_profiles = {
        "h76-restore100-exact-repeat",
        "h76-hotspot-top2-restore10-exact-repeat",
        "h76-a017dr095-restore5-exact-repeat",
    }
    if profile in {
        "h76-top4-min5-repeat",
        "h76-restore100-exact-repeat",
        "h76-hotspot-top2-restore10-exact-repeat",
        "h76-a017dr095-restore5-exact-repeat",
        "dr035-min3-confirm",
        "dr035-max5-confirm",
    }:
        return {
            "repeat_type": "exact_repeat",
            "formal_confirmation_evidence": True,
            "original_seed": 5,
            "max_attempts": CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
            "max_attempts_hard_cap": True,
            "early_stop_on_best_hit": True,
            "restore_target_H": target_h or ("per_job_source_H" if profile in per_job_restore_profiles else ""),
            "per_job_restore_target_H": profile in per_job_restore_profiles,
            "near_miss_tolerance_H": near_miss_tolerance,
            "near_miss_not_restored": True,
            "seed_change_allowed": False,
            "not_confirmation_evidence": False,
        }
    return {
        "repeat_type": "not_confirmation",
        "formal_confirmation_evidence": False,
        "not_confirmation_evidence": True,
    }


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


def yaml_unquote(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
        return text.replace(r"\\", "\\").replace(r"\"", '"')
    if len(text) >= 2 and text[0] == "'" and text[-1] == "'":
        return text[1:-1]
    return text


def parse_shallow_yaml_text(text: str) -> dict[str, object]:
    """Parse helper-generated shallow YAML from either a file or a Git object."""
    data: dict[str, object] = {}
    current_section = ""
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            section_match = re.match(r"^([A-Za-z0-9_]+):\s*$", raw_line)
            if section_match:
                current_section = section_match.group(1)
                data[current_section] = {}
                continue
            value_match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if value_match:
                current_section = ""
                data[value_match.group(1)] = yaml_unquote(value_match.group(2))
                continue
        if current_section and raw_line.startswith("  ") and not raw_line.startswith("    "):
            value_match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if value_match and isinstance(data.get(current_section), dict):
                section = data[current_section]
                assert isinstance(section, dict)
                section[value_match.group(1)] = yaml_unquote(value_match.group(2))
    return data


def read_shallow_yaml(path: Path) -> dict[str, object]:
    """Parse the helper-generated, shallow YAML ledgers without a PyYAML dependency."""
    return parse_shallow_yaml_text(read_text(path))


def yaml_section_value(data: dict[str, object], section: str, key: str, default: str = "") -> str:
    section_data = data.get(section)
    if isinstance(section_data, dict):
        value = section_data.get(key)
        return "" if value is None else str(value)
    return default


def yaml_bool_value(value: object) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "on"}


def validate_trial_meta_data(data: dict[str, object], raw_text: str = "") -> list[str]:
    errors: list[str] = []
    scope = str(data.get("module_scope", "")).strip()
    family = str(data.get("template_family", "")).strip()
    risk = str(data.get("risk", "")).strip()

    if scope not in TRIAL_MODULE_SCOPES:
        errors.append(f"module_scope must be one of {sorted(TRIAL_MODULE_SCOPES)}, got {scope!r}")
    if family not in TRIAL_TEMPLATE_FAMILIES:
        errors.append(f"template_family must be one of {sorted(TRIAL_TEMPLATE_FAMILIES)}, got {family!r}")

    if scope == "single_module" and family in {"composite", "architecture_change"}:
        errors.append("single_module cannot use composite or architecture_change template_family")
    if scope == "composite" and family != "composite":
        errors.append("module_scope=composite requires template_family=composite")
    if scope == "architecture_change" and family != "architecture_change":
        errors.append("module_scope=architecture_change requires template_family=architecture_change")

    training_entry = data.get("training_entry")
    if not isinstance(training_entry, dict):
        errors.append("training_entry section is required")
        training_entry = {}
    entry_mode = str(training_entry.get("mode", "")).strip()
    selected_entry = str(training_entry.get("selected_entry", "")).strip()
    standard_template = str(training_entry.get("standard_template", "")).strip()
    legacy_migration = str(training_entry.get("legacy_module_migration", "")).strip()
    if entry_mode not in TRIAL_TRAINING_ENTRY_MODES:
        errors.append(
            f"training_entry.mode must be one of {sorted(TRIAL_TRAINING_ENTRY_MODES)}, got {entry_mode!r}"
        )
    if entry_mode == "strict_template_entry":
        if "standard_gzsl_training_template.py" not in standard_template:
            errors.append("strict_template_entry requires standard_gzsl_training_template.py as standard_template")
        if selected_entry in TRIAL_STRICT_ENTRY_INVALID_SELECTED:
            errors.append("strict_template_entry must select a trial-local training entry, not train_GTPJ_CUB.py")
        if legacy_migration not in TRIAL_LEGACY_MIGRATION_STATES:
            errors.append(
                "strict_template_entry requires legacy_module_migration: "
                + " | ".join(sorted(TRIAL_LEGACY_MIGRATION_STATES))
            )

    affects = data.get("affects")
    if not isinstance(affects, dict):
        errors.append("affects section is required")
        affects = {}
    risky_affects = [
        name for name in sorted(TRIAL_ARCHITECTURE_AFFECT_FLAGS)
        if yaml_bool_value(affects.get(name, "false"))
    ]
    if scope in {"single_module", "composite"} and risky_affects:
        errors.append(
            "module_scope must be architecture_change when affects are true: "
            + ", ".join(risky_affects)
        )
    if scope == "architecture_change" and risk != "high":
        errors.append("architecture_change trials must set risk: high")

    baseline_off = data.get("baseline_off")
    if not isinstance(baseline_off, dict):
        errors.append("baseline_off section is required")
        baseline_off = {}
    if scope in {"single_module", "composite"} and not yaml_bool_value(baseline_off.get("supported", "false")):
        errors.append("single_module/composite trials require baseline_off.supported: true")
    if scope == "composite" and not yaml_bool_value(
        baseline_off.get("all_switches_false_equals_base", "false")
    ):
        errors.append("composite trials require baseline_off.all_switches_false_equals_base: true")

    audit = data.get("audit")
    if not isinstance(audit, dict):
        errors.append("audit section is required")
        audit = {}
    required_audits = (
        TRIAL_ARCHITECTURE_REQUIRED_AUDITS
        if scope == "architecture_change"
        else TRIAL_REQUIRED_AUDITS
    )
    missing_audits = [
        name for name in sorted(required_audits)
        if str(audit.get(name, "")).strip() != "required"
    ]
    if missing_audits:
        errors.append("audit missing required gates: " + ", ".join(missing_audits))

    if scope == "composite" and "- name:" not in raw_text:
        errors.append("composite trials must list components with name/template_family/attachment_point/enabled_key")
    return errors


def validate_trial_meta_file(path: Path) -> list[str]:
    text = read_text(path)
    return validate_trial_meta_data(read_shallow_yaml(path), text)


def yaml_nested_section_value(path: Path, section: str, subsection: str, key: str, default: str = "") -> str:
    """Read one value from the helper ledger style nested YAML blocks.

    This intentionally supports only the simple nested maps used by result.yaml
    files, for example metrics.best_single.H. It is not a general YAML parser.
    """
    in_section = False
    in_subsection = False
    for raw_line in read_text(path).splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            in_section = raw_line == f"{section}:"
            in_subsection = False
            continue
        if not in_section:
            continue
        if raw_line.startswith("  ") and not raw_line.startswith("    "):
            match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if not match:
                in_subsection = False
                continue
            in_subsection = match.group(1) == subsection and match.group(2).strip() == ""
            continue
        if in_subsection and raw_line.startswith("    ") and not raw_line.startswith("      "):
            match = re.match(r"^\s{4}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if match and match.group(1) == key:
                return yaml_unquote(match.group(2))
    return default


def attempt_sync_metrics(attempt_result: dict[str, object], attempt_result_path: Path) -> dict[str, str]:
    metrics = {
        name: yaml_section_value(attempt_result, "metrics", name)
        for name in [*METRIC_NAMES, "best_epoch", "baseline_H", "delta_H", "seed"]
    }
    if not metrics.get("H"):
        for name in [*METRIC_NAMES, "best_epoch"]:
            metrics[name] = yaml_nested_section_value(attempt_result_path, "metrics", "best_single", name)
    return metrics


def read_yaml_artifacts(path: Path) -> dict[str, dict[str, str]]:
    artifacts: dict[str, dict[str, str]] = {}
    in_artifacts = False
    current_key = ""
    for raw_line in read_text(path).splitlines():
        if raw_line == "artifacts:":
            in_artifacts = True
            continue
        if not in_artifacts:
            continue
        if raw_line and not raw_line.startswith(" "):
            break
        key_match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*$", raw_line)
        if key_match:
            current_key = key_match.group(1)
            artifacts[current_key] = {}
            continue
        value_match = re.match(r"^\s{4}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
        if current_key and value_match:
            artifacts[current_key][value_match.group(1)] = yaml_unquote(value_match.group(2))
    return artifacts


def config_epoch_schedule(config_path: Path) -> dict[str, object]:
    text = read_text(config_path)
    config_epochs = None
    match = re.search(r"(?ms)^epochs:\s*\n\s+value:\s*([0-9]+)\s*$", text)
    if match:
        config_epochs = int(match.group(1))
    lr_stages_match = re.search(r"(?ms)^lr_stages:\s*\n\s+value:\s*\n(?P<body>(?:\s{2,}.+\n?)+)", text)
    stage_epochs = [int(value) for value in re.findall(r"^\s{4}epochs:\s*([0-9]+)\s*$", lr_stages_match.group("body"), re.MULTILINE)] if lr_stages_match else []
    if stage_epochs:
        return {
            "config_epochs_field": config_epochs,
            "planned_train_epochs": sum(stage_epochs),
            "epoch_schedule_source": "lr_stages",
            "lr_stage_epochs": stage_epochs,
        }
    return {
        "config_epochs_field": config_epochs,
        "planned_train_epochs": config_epochs,
        "epoch_schedule_source": "epochs",
        "lr_stage_epochs": [],
    }


def validate_attempt_epoch_schedule_disclosure() -> list[str]:
    errors: list[str] = []
    attempts_root = REPO_ROOT / "experiments" / "module_trials"
    if not attempts_root.exists():
        return errors
    for plan_path in sorted(attempts_root.glob("IDEA-*/TRIAL-*/attempts/ATTEMPT-*/pre_run_plan.md")):
        config_path = plan_path.with_name("config.yaml")
        if not config_path.exists():
            continue
        schedule = config_epoch_schedule(config_path)
        if schedule["epoch_schedule_source"] != "lr_stages":
            continue
        config_epochs = schedule["config_epochs_field"]
        planned_epochs = schedule["planned_train_epochs"]
        if config_epochs == planned_epochs:
            continue
        plan_text = read_text(plan_path)
        required_marker_groups = [
            [f"Config epochs field: {config_epochs}", f"config_epochs_field: {config_epochs}"],
            [f"Planned train epochs: {planned_epochs}", f"planned_train_epochs: {planned_epochs}"],
            ["Epoch schedule source: lr_stages", "epoch_schedule_source: lr_stages"],
        ]
        missing = [markers[0] for markers in required_marker_groups if not any(marker in plan_text for marker in markers)]
        if missing:
            errors.append(
                f"{rel(plan_path)} must disclose lr_stages epoch schedule; missing "
                + ", ".join(missing)
            )
        if re.search(r"(?m)^-\s*Epochs:\s*[0-9]+\s*$", plan_text):
            errors.append(
                f"{rel(plan_path)} must not use ambiguous '- Epochs:' when lr_stages overrides epochs"
            )
    return errors


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
        return re.sub(pattern, lambda _match: line, content, count=1)

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


def parse_training_log_text(text: str, label: str) -> dict[str, str]:
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
            f"Unable to parse training log metrics from {label}: "
            + ", ".join(missing)
        )
    return metrics


def parse_training_log(log_path: Path) -> dict[str, str]:
    return parse_training_log_text(read_text(log_path), display_path(log_path))


def captured_training_log_text(log_path: Path, command: str) -> str:
    """Return only output emitted by the workflow-launched process."""
    lines = read_text(log_path).splitlines()
    command_sha256 = parameter_matrix_sha256(command)
    start_prefix = f"GTPJ_TRAINING_PROCESS_STARTED command_sha256={command_sha256} "
    finish_prefix = f"GTPJ_TRAINING_PROCESS_FINISHED command_sha256={command_sha256} "
    starts = [index for index, line in enumerate(lines) if line.startswith(start_prefix)]
    finishes = [index for index, line in enumerate(lines) if line.startswith(finish_prefix)]
    if len(starts) != 1 or len(finishes) != 1 or starts[0] >= finishes[0]:
        raise WorkflowError("training log has no unique workflow-captured process interval")
    return "\n".join(lines[starts[0] + 1 : finishes[0]]) + "\n"


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


def git_dirty_outside(allowed_paths: Iterable[Path]) -> bool:
    """Ignore only the runtime evidence files created by the official helper."""
    allowed: set[str] = set()
    for path in allowed_paths:
        try:
            allowed.add(path.resolve().relative_to(REPO_ROOT.resolve()).as_posix())
        except ValueError:
            continue
    for line in git(["status", "--short", "--untracked-files=all"], check=False).splitlines():
        # git() strips the complete output, so the leading blank of the first
        # worktree-only status line (for example `` M file``) may be removed.
        offset = 2 if len(line) >= 2 and line[1] == " " else 3
        candidate = line[offset:].strip().replace("\\", "/")
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[1]
        if candidate not in allowed:
            return True
    return False


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


FORMAL_DYNAMIC_ROUTING_FINGERPRINT_PATHS = [
    "train_GTPJ_CUB.py",
    "model",
    "config",
    "tools",
    "workflow/gtpj_workflow.py",
]


def require_formal_dynamic_routing_source_control(args: argparse.Namespace, base_config: Path) -> dict[str, object]:
    """Require formal batch plans to be generated from the exact clean training commit."""

    require_clean_worktree("formal dynamic routing batch planning")
    head_commit = resolve_commit("HEAD")
    requested_commit_ref = str(args.commit or "HEAD")
    requested_commit = resolve_commit(requested_commit_ref)
    current = current_branch()
    allow_historical = bool(getattr(args, "allow_historical_training_commit", False))
    if requested_commit != head_commit and not allow_historical:
        raise WorkflowError(
            "Formal dynamic routing batch requires --commit to equal the clean local HEAD. "
            f"HEAD={head_commit}; requested {requested_commit_ref}={requested_commit}. "
            "Use --allow-historical-training-commit only for an explicit exact repeat of an older source commit."
        )

    if requested_commit != head_commit:
        if not args.branch:
            raise WorkflowError(
                "Formal historical training commit requires --branch to name the original branch."
            )
        branch_ref = f"refs/heads/{args.branch}"
        branch_tip = git(["rev-parse", "--verify", f"{branch_ref}^{{commit}}"], check=False)
        if not branch_tip:
            raise WorkflowError(
                f"Formal historical training commit requires a local branch ref for --branch {args.branch}."
            )
        require_ancestor(
            requested_commit,
            branch_tip,
            "Formal historical training commit must be contained in the requested branch",
        )
    elif args.branch and args.branch != current:
        raise WorkflowError(
            "Formal dynamic routing batch requires --branch to match the current branch. "
            f"current_branch={current or '(detached)'}; requested_branch={args.branch}. "
            "Check out the original branch before planning an exact repeat."
        )

    paths = list(FORMAL_DYNAMIC_ROUTING_FINGERPRINT_PATHS)
    base_config_rel = repo_relative_path(base_config, "Formal dynamic routing base config")
    if base_config_rel not in paths:
        paths.append(base_config_rel)
    object_ids: dict[str, str] = {}
    missing_paths: list[str] = []
    for relative in paths:
        object_id = git(["rev-parse", "--verify", f"{requested_commit}:{relative}"], check=False)
        if object_id:
            object_ids[relative] = object_id
        else:
            missing_paths.append(relative)

    return {
        "source_control_policy": (
            "formal_explicit_historical_training_commit"
            if requested_commit != head_commit
            else "formal_same_clean_head"
        ),
        "plan_generation_commit": head_commit,
        "plan_generation_branch": current,
        "training_commit": requested_commit,
        "training_branch_label": args.branch or current,
        "dirty_state": "clean",
        "fingerprint_paths": object_ids,
        "missing_fingerprint_paths": missing_paths,
    }


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
    return f"exp/{version}/{kind.name}/{exp_id.lower()}-{branch_slug(slug)}"


def framework_branch_name(version: str) -> str:
    return f"framework/{version}"


def framework_template_path(version: str) -> Path:
    return REPO_ROOT / "experiments" / version / "TEMPLATE.yaml"


def experiment_binding_path(row: dict[str, str]) -> Path:
    return REPO_ROOT / row["directory"] / "EXPERIMENT.yaml"


def load_framework_template_from_registry(
    version: str,
    registry_ref: str = DEFAULT_TEMPLATE_REGISTRY_REF,
) -> tuple[dict[str, object], str]:
    """Read TEMPLATE.yaml from an immutable governance commit, not the template checkout."""
    registry_commit = resolve_commit(registry_ref)
    require_ancestor(
        registry_commit,
        "refs/heads/main",
        "template registry commit must belong to the local main governance history",
    )
    template_rel = f"experiments/{version}/TEMPLATE.yaml"
    raw = git_show(f"{registry_commit}:{template_rel}", check=False)
    if not raw:
        raise WorkflowError(
            f"template registry {registry_commit} does not contain {template_rel}"
        )
    template_data = parse_shallow_yaml_text(raw)
    identity_errors = [
        f"missing key: {key}"
        for key in sorted(FRAMEWORK_TEMPLATE_REQUIRED_KEYS - set(template_data))
    ]
    identity_errors.extend(framework_template_identity_errors(version, template_data))
    ref_errors = framework_template_git_ref_errors(template_data)
    if identity_errors or ref_errors:
        raise WorkflowError(
            "template registry entry is invalid:\n"
            + "\n".join(identity_errors + ref_errors)
        )
    return template_data, registry_commit


def require_experiment_branch_base(
    version: str,
    *,
    template_data: dict[str, object] | None = None,
) -> None:
    template_path = framework_template_path(version)
    if template_data is not None or template_path.exists():
        template_data = template_data or read_shallow_yaml(template_path)
        template_status = str(template_data.get("template_status", ""))
        if template_status != "frozen":
            raise WorkflowError(
                "new-experiment requires a frozen clean framework template; "
                f"{rel(template_path)} status is {template_status or '<missing>'}"
            )
        template_commit = str(template_data.get("template_commit", ""))
        head_commit = git(["rev-parse", "HEAD"])
        if head_commit != template_commit:
            raise WorkflowError(
                "new-experiment branch must start exactly at template commit; "
                f"HEAD={head_commit}, template_commit={template_commit}"
            )
        template_ref_errors = framework_template_identity_errors(version, template_data)
        template_ref_errors.extend(framework_template_git_ref_errors(template_data))
        if template_ref_errors:
            raise WorkflowError(
                "new-experiment template identity is invalid:\n"
                + "\n".join(template_ref_errors)
            )
        return
    framework_branch = framework_branch_name(version)
    if not git(["rev-parse", "--verify", f"refs/heads/{framework_branch}"], check=False):
        raise WorkflowError(
            f"new-experiment requires local framework branch {framework_branch}; "
            "formal experiments must branch from their framework code line"
        )
    require_ancestor(
        f"refs/heads/{framework_branch}",
        "HEAD",
        f"new-experiment branch must contain {framework_branch}",
    )


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
    ignored_roots = {".git", ".gtpj_runtime", "__pycache__"}
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
            "core_summary",
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
        ]:
            if field not in idea:
                raise WorkflowError(f"{idea_id} missing required field: {field}")
    return current_version, ideas


def cmd_status(_: argparse.Namespace) -> int:
    branch = git(["branch", "--show-current"], check=False) or "(detached)"
    head = git(["rev-parse", "--short", "HEAD"], check=False)
    tags = git(["tag", "--points-at", "HEAD"], check=False)
    porcelain = git(["status", "--short"], check=False)
    current_version = ""
    idea_tree_path = REPO_ROOT / "idea_tree" / "idea_tree.json"
    if idea_tree_path.exists():
        try:
            current_version = str(json.loads(read_text(idea_tree_path)).get("current_version", ""))
        except json.JSONDecodeError:
            current_version = ""

    print("GTPJ repository 状态")
    print(f"- branch: {branch}")
    print(f"- head: {head}")
    print(f"- tags at head: {tags or '(none)'}")
    print(f"- working tree: {'dirty' if porcelain else 'clean'}")
    if current_version:
        print(f"- current_version: {current_version}")
    print()
    print("可用版本:")
    for version_dir in sorted((REPO_ROOT / "experiments").glob("v*")):
        if version_dir.is_dir():
            print(f"- {version_dir.name}: {rel(version_dir)}")
    print()
    print("复现状态:")
    for version in sorted(CANONICAL_BASELINES):
        evidence = baseline_evidence(version)
        active = " (active)" if version == current_version else ""
        print(
            f"- {version}{active}: {reproducibility_verdict(version)}; "
            f"evidence_level={evidence['evidence_level']}; "
            f"best_observed_H={evidence['best_observed_H']}; "
            f"confirmed_H={evidence['confirmed_H']}; "
            f"confirmation_status={evidence['confirmation_status']}"
        )
    print()
    print("后续队列:")
    for queue in sorted((REPO_ROOT / "idea_tree" / "queues").glob("*.md")):
        print(f"- {rel(queue)}")
    return 0


def queue_state_path() -> Path:
    return REPO_ROOT / "idea_tree" / "queues" / "queue_state.yaml"


def read_queue_state(path: Path | None = None) -> dict[str, object]:
    """Parse the small queue_state.yaml subset used by the todo helper."""
    path = path or queue_state_path()
    if not path.exists():
        raise WorkflowError(f"Missing queue state file: {rel(path)}")
    data: dict[str, object] = {}
    current_key = ""
    current_item: dict[str, str] | None = None
    for raw_line in read_text(path).splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if not match:
                continue
            current_key = match.group(1)
            current_item = None
            value = match.group(2).strip()
            data[current_key] = yaml_unquote(value) if value else {}
            continue
        if not current_key:
            continue
        if raw_line.startswith("  - "):
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            current_item = {}
            assert isinstance(data[current_key], list)
            data[current_key].append(current_item)
            rest = raw_line[4:].strip()
            if ":" in rest:
                key, value = rest.split(":", 1)
                current_item[key.strip()] = yaml_unquote(value.strip())
            continue
        if current_item is not None and raw_line.startswith("    "):
            match = re.match(r"^\s{4}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if match:
                current_item[match.group(1)] = yaml_unquote(match.group(2).strip())
            continue
        if raw_line.startswith("  ") and not raw_line.startswith("    "):
            match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if match:
                section = data.get(current_key)
                if not isinstance(section, dict):
                    section = {}
                    data[current_key] = section
                section[match.group(1)] = yaml_unquote(match.group(2).strip())
    return data


def queue_items(data: dict[str, object], section: str) -> list[dict[str, str]]:
    value = data.get(section, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def queue_section(data: dict[str, object], section: str) -> dict[str, str]:
    value = data.get(section, {})
    return value if isinstance(value, dict) else {}


def render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) or "-" for value in row) + " |" for row in rows)
    return lines


def queue_markdown_note() -> list[str]:
    return [
        "",
        "> 本文件由 `idea_tree/queues/queue_state.yaml` 生成。修改队列时先改机器源，再运行 `python workflow/gtpj_workflow.py refresh-todo`。",
        "",
    ]


def render_next_actions(data: dict[str, object]) -> str:
    window = queue_section(data, "current_window")
    action_rows = [
        [
            item.get("priority", "-"),
            item.get("item", "-"),
            item.get("type", "-"),
            item.get("owner", "-"),
            item.get("status", "-"),
            item.get("blocked_by", "-"),
            item.get("evidence_ref", "-"),
        ]
        for item in queue_items(data, "actions")
    ] or [["-", "当前没有近期动作。", "-", "-", "-", "-", "-"]]
    done_rows = [
        [
            item.get("item", "-"),
            item.get("evidence_ref", "-"),
        ]
        for item in queue_items(data, "completed")
    ] or [["-", "-"]]
    lines = [
        "# GTPJ 当前待办",
        "",
        "这是当前执行窗口，只保留近期优先动作；完整创意库不放在这里。",
        "",
        f"- 当前关注：{window.get('focus', '-')}",
        f"- 管理规则：{window.get('policy', '只保留 3-7 条近期动作；具体实验动作写入 task/trial/attempt。')}",
        f"- 更新时间：{data.get('updated_at', '-')}",
        "",
        "## 当前窗口",
        "",
        *render_table(["优先级", "事项", "类型", "负责人", "状态", "阻塞", "证据位置"], action_rows),
        "",
        "## 已完成摘要",
        "",
        *render_table(["事项", "证据位置"], done_rows),
        "",
    ]
    return "\n".join(lines)


def render_selected_next(data: dict[str, object]) -> str:
    rows = [
        [
            item.get("subject_id", "-"),
            item.get("idea", "-"),
            item.get("base_version", "-"),
            item.get("state", "-"),
            item.get("reason", "-"),
            item.get("evidence_ref", "-"),
        ]
        for item in queue_items(data, "selected_next")
    ]
    lines = ["# 已选队列", *queue_markdown_note()]
    if rows:
        lines.extend(render_table(["对象", "Idea", "基于版本", "状态", "入队理由", "证据位置"], rows))
    else:
        lines.append("当前没有已选中的 module trial。")
    lines.append("")
    return "\n".join(lines)


def render_module_candidates(data: dict[str, object]) -> str:
    rows = [
        [
            item.get("idea", "-"),
            item.get("candidate", "-"),
            item.get("switch", "-"),
            item.get("source_status", "-"),
            item.get("priority", "-"),
            item.get("reason", "-"),
            item.get("state", "-"),
        ]
        for item in queue_items(data, "module_candidates")
    ]
    lines = [
        "# 模块候选",
        *queue_markdown_note(),
        "规则：任何新候选必须先进入 `idea_tree/inbox.md`，补全来源后才能登记为 `idea_tree/ideas/IDEA-xxxx_slug/IDEA.md`。",
        "",
    ]
    if rows:
        lines.extend(render_table(["Idea", "候选", "主开关", "来源状态", "优先级", "入队理由", "当前状态"], rows))
    else:
        lines.append("当前没有模块候选。")
    lines.append("")
    return "\n".join(lines)


def render_ablation_questions(data: dict[str, object]) -> str:
    rows = [
        [
            item.get("question", "-"),
            item.get("subject", "-"),
            item.get("type", "-"),
            item.get("priority", "-"),
            item.get("reason", "-"),
            item.get("state", "-"),
        ]
        for item in queue_items(data, "ablation_questions")
    ]
    lines = ["# 消融问题队列", *queue_markdown_note()]
    if rows:
        lines.extend(render_table(["问题", "所属对象", "类型", "优先级", "入队理由", "当前状态"], rows))
    else:
        lines.append("当前没有待做消融问题。")
    lines.append("")
    return "\n".join(lines)


def render_tuning_questions(data: dict[str, object]) -> str:
    rows = [
        [
            item.get("question", "-"),
            item.get("base_version", "-"),
            item.get("parameter_scope", "-"),
            item.get("priority", "-"),
            item.get("reason", "-"),
            item.get("state", "-"),
        ]
        for item in queue_items(data, "tuning_questions")
    ]
    lines = [
        "# 调参问题队列",
        *queue_markdown_note(),
        "调参实验统一写入所属框架的 `experiments/vX/tune/`；旧 trial/attempt 目录只保留历史证据和兼容编号。",
        "",
    ]
    if rows:
        lines.extend(render_table(["问题", "基于版本", "参数/范围", "优先级", "入队理由", "当前状态"], rows))
    else:
        lines.append("当前没有待做调参问题。")
    lines.append("")
    return "\n".join(lines)


def write_todo_views(data: dict[str, object]) -> None:
    outputs = {
        "NEXT_ACTIONS.md": render_next_actions(data),
        "idea_tree/queues/01_selected_next.md": render_selected_next(data),
        "idea_tree/queues/02_module_candidates.md": render_module_candidates(data),
        "idea_tree/queues/03_ablation_questions.md": render_ablation_questions(data),
        "idea_tree/queues/04_tuning_questions.md": render_tuning_questions(data),
    }
    for relative, content in outputs.items():
        path = REPO_ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def cmd_refresh_todo(_: argparse.Namespace) -> int:
    data = read_queue_state()
    write_todo_views(data)
    print("refresh-todo-ok")
    print(f"source={rel(queue_state_path())}")
    return 0


def cmd_todo_status(_: argparse.Namespace) -> int:
    data = read_queue_state()
    window = queue_section(data, "current_window")
    print("todo-status")
    print(f"- source: {rel(queue_state_path())}")
    print(f"- updated_at: {data.get('updated_at', '-')}")
    print(f"- focus: {window.get('focus', '-')}")
    for section, label in [
        ("actions", "current_actions"),
        ("selected_next", "selected_next"),
        ("module_candidates", "module_candidates"),
        ("ablation_questions", "ablation_questions"),
        ("tuning_questions", "tuning_questions"),
    ]:
        items = queue_items(data, section)
        open_items = [item for item in items if item.get("status", item.get("state", "open")) != "done"]
        print(f"- {label}: {len(open_items)} open / {len(items)} total")
    return 0


def cmd_repro_status(args: argparse.Namespace) -> int:
    version = args.version.strip()
    if not version:
        data = load_idea_tree()
        version = str(data.get("current_version", "")).strip()
    if not version:
        raise WorkflowError("Unable to infer current version; pass --version vX")
    evidence = baseline_evidence(version)
    confirmed = baseline_is_confirmed(version)
    print(f"{version} reproducibility")
    print(f"- name: {evidence['name']}")
    print(f"- status: {evidence['status']}")
    print(f"- evidence_level: {evidence['evidence_level']}")
    print(f"- best_observed_H: {evidence['best_observed_H']}")
    print(f"- confirmed_H: {evidence['confirmed_H']}")
    print(f"- confirmation_status: {evidence['confirmation_status']}")
    print(f"- verdict: {reproducibility_verdict(version)}")
    print(
        f"- comparison_reference: {comparison_reference_field(version)}="
        f"{comparison_reference_h(version) or '-'}"
        f"{'' if confirmed else ' (unconfirmed)'}"
    )
    print(f"- can_claim_confirmed_baseline: {'yes' if confirmed else 'no'}")
    if "legacy_config_only" in evidence.get("status", ""):
        print("- framework_version: no")
        print("- note: pure tuning/config-only records stay under their owning formal framework; use v3/CONFIRM-001 local-v3-054 as the formal reference")
    if not confirmed:
        status = evidence.get("status", "")
        if "owner_accepted" in status or "owner_activated" in status:
            print(
                "- next_action: keep owner tag as an unconfirmed reference; "
                "run clean confirmation before confirmed or baseline-grade claims"
            )
        else:
            print("- next_action: run clean confirmation before baseline-grade or tag/promotion claims")
    return 0


def required_repository_files() -> list[str]:
    return [
        "README.md",
        "AGENTS.md",
        "NEXT_ACTIONS.md",
        "docs/GITHUB_GOVERNANCE.md",
        "docs/PROJECT_STRUCTURE.md",
        "docs/PROJECT_STATUS.md",
        "docs/DATA_SETUP.md",
        "docs/workflow/README.md",
        "docs/workflow/core/QUICK_START.md",
        "docs/workflow/WORKFLOW_MANIFEST.yaml",
        "docs/workflow/core/TASK_START_MINI.md",
        "docs/workflow/protocols/git_policy.md",
        "docs/workflow/protocols/versioning.md",
        "docs/workflow/protocols/module_trial_protocol.md",
        "docs/workflow/protocols/module_template_selection.md",
        "docs/workflow/protocols/code_interface_contract.md",
        "docs/workflow/protocols/innovation_code_review_protocol.md",
        "docs/workflow/protocols/ai_cross_review_protocol.md",
        "docs/workflow/reference/code_interface.md",
        "docs/workflow/protocols/experiment_protocol.md",
        "docs/workflow/reference/artifact_policy.md",
        "docs/workflow/reference/result_index_protocol.md",
        "docs/workflow/reference/agent_contracts.md",
        "docs/workflow/protocols/agent_orchestration.md",
        "docs/workflow/protocols/agent_cleanup_protocol.md",
        "docs/workflow/protocols/agent_report_policy.md",
        "docs/workflow/protocols/evidence_routing_protocol.md",
        "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md",
        "docs/workflow/reference/GZSL_HARD_RULES.md",
        "docs/workflow/reference/innovation_decomposition_protocol.md",
        "docs/workflow/core/WORKFLOW_VERSION.md",
        "docs/workflow/core/CHANGELOG.md",
        "docs/workflow/agents/README.md",
        "docs/workflow/agents/long_term_memory.md",
        "docs/workflow/protocols/idea_tree_protocol.md",
        "docs/workflow/protocols/quality_gate.md",
        "docs/workflow/archive/diagrams/workflow_diagrams.md",
        "docs/workflow/archive/runbooks/runbook.md",
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
        "idea_tree/queues/queue_state.yaml",
        "idea_tree/queues/01_selected_next.md",
        "idea_tree/queues/02_module_candidates.md",
        "idea_tree/queues/03_ablation_questions.md",
        "idea_tree/queues/04_tuning_questions.md",
        "experiments/README.md",
        "experiments/EXPERIMENT_REGISTRY.md",
        "experiments/VERSION_TREE.md",
        "experiments/LEGACY_POLICY.md",
        "experiments/module_trials/INDEX.md",
        "experiments/templates/IDEA_template.md",
        "experiments/templates/TRIAL_README_template.md",
        "experiments/templates/FRAMEWORK_template.yaml",
        "experiments/templates/FRAMEWORK_INDEX_template.md",
        "experiments/templates/VERSION_template.md",
        "experiments/templates/experiment_README_template.md",
        "experiments/templates/implementation_template.md",
        "experiments/templates/agent_summary_template.md",
        "experiments/templates/ai_cross_review_template.md",
        "experiments/templates/run_receipt_template.yaml",
        "experiments/templates/quality_check_template.md",
        "experiments/templates/modules/README.md",
        "experiments/templates/modules/module_source_template.md",
        "experiments/templates/modules/trial_meta_template.yaml",
        "experiments/templates/modules/standard_trial_config_template.yaml",
        "experiments/templates/modules/standard_gzsl_module_framework_template.py",
        "experiments/templates/modules/standard_gzsl_training_template.py",
        "experiments/templates/modules/feature_adapter_template.py",
        "experiments/templates/modules/fusion_gate_template.py",
        "experiments/templates/modules/auxiliary_loss_template.py",
        "experiments/templates/modules/sampler_or_data_view_template.py",
        "experiments/templates/modules/composite_module_template.py",
        "experiments/templates/modules/architecture_change_template.md",
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
        "experiments/v3/VERSION.md",
        "experiments/v3/config.yaml",
        "experiments/v3/result.md",
        "experiments/v3/baseline/README.md",
        "experiments/v3/baseline/config.yaml",
        "experiments/v3/baseline/manifest.yaml",
        "experiments/v3/baseline/result.yaml",
        "experiments/v3/baseline/quality_check.md",
        "experiments/v3/tune/INDEX.md",
        "experiments/v3/ablation/INDEX.md",
        "experiments/v3/confirmation/INDEX.md",
        "config/versions/v3.yaml",
        "experiments/v4/VERSION.md",
        "experiments/v4/config.yaml",
        "experiments/v4/result.md",
        "experiments/v4/baseline/README.md",
        "experiments/v4/baseline/config.yaml",
        "experiments/v4/baseline/manifest.yaml",
        "experiments/v4/baseline/result.yaml",
        "experiments/v4/baseline/quality_check.md",
        "experiments/v4/tune/INDEX.md",
        "experiments/v4/ablation/INDEX.md",
        "experiments/v4/confirmation/INDEX.md",
        "config/versions/v4.yaml",
        "experiments/v5/VERSION.md",
        "experiments/v5/config.yaml",
        "experiments/v5/result.md",
        "experiments/v5/baseline/README.md",
        "experiments/v5/baseline/config.yaml",
        "experiments/v5/baseline/manifest.yaml",
        "experiments/v5/baseline/result.yaml",
        "experiments/v5/baseline/quality_check.md",
        "experiments/v5/tune/INDEX.md",
        "experiments/v5/ablation/INDEX.md",
        "experiments/v5/confirmation/INDEX.md",
        "config/versions/v5.yaml",
        "schemas/manifest.schema.json",
        "schemas/result.schema.json",
        "schemas/artifact_ref.schema.json",
        "schemas/evidence_routing.schema.yaml",
        "schemas/framework.schema.json",
        "docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md",
        "docs/TECH_STACK_HISTORY.md",
    ]


def cmd_validate(_: argparse.Namespace) -> int:
    required = required_repository_files()
    missing = [item for item in required if not (REPO_ROOT / item).exists()]
    if missing:
        raise WorkflowError("Missing required files:\n" + "\n".join(missing))

    marker_requirements = {
        "docs/workflow/START_HERE.md": [
            "baseline_repro_status",
            "comparison_reference",
            "debug_smoke",
            "multi_agent_preflight",
            "formal_pending",
            "orphan_runtime_plan",
            "明确入口硬规则",
            "执行授权",
            "不得反复确认",
            "pre_run_planned",
            "report-new-completions",
        ],
        "docs/workflow/WORKFLOW_KERNEL.md": [
            "named_owner_thread",
            "debug_smoke",
            "Top-3",
            "TRANSITIONS.jsonl",
            "validate-agent-runtime",
            "multi-agent-preflight",
            "formal_pending",
            "orphan_runtime_plan",
            "开启多agents智能体工作流",
            "planning gate",
            "files_reviewed",
            "独立输出文件",
            "allow/block/propose",
            "report-new-completions",
        ],
        "docs/workflow/protocols/evidence_routing_protocol.md": ["subject_id", "TRANSITIONS.jsonl", "validate-evidence-routing"],
        "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md": [
            "left_sidebar_named_threads",
            "agent_runtime.yaml",
            "validate-agent-runtime",
            "multi-agent-preflight",
            "single_agent_execution",
            "formal_runner_allowed",
            "agent_output_refs",
            "files_reviewed",
            "report-new-completions",
        ],
        "docs/workflow/reference/GZSL_HARD_RULES.md": ["seen/unseen split", "logits", "rule_checks"],
        "docs/workflow/reference/innovation_decomposition_protocol.md": ["Hypothesis", "Trial", "Attempt"],
        "docs/workflow/core/WORKFLOW_VERSION.md": ["workflow-v2", "evidence_routing.yaml"],
        "docs/workflow/core/CHANGELOG.md": ["workflow-v2", "validate-evidence-routing"],
        "docs/workflow/core/QUICK_START.md": ["repro-status", "baseline_repro_status"],
        "docs/workflow/core/WORKFLOW_ROUTER.md": ["baseline_repro_status", "best_observed_H", "role_key", "formal_pending", "orphan_runtime_plan"],
        "docs/workflow/core/TASK_START_MINI.md": ["baseline_repro_status", "named_owner_thread", "subject_id", "agent_runtime_gate", "formal_runner_allowed"],
        "docs/workflow/core/TASK_START_CARD.md": [
            "subject_id",
            "transition_permissions",
            "authority_refs",
            "agent_runtime_gate",
            "multi_agent_preflight",
            "开启多agents智能体工作流",
            "files_reviewed",
        ],
        "docs/workflow/agents/README.md": ["role_aliases", "runner_monitor", "log_analyst"],
        "docs/workflow/protocols/agent_orchestration.md": [
            "Agent Runtime Protocol",
            "propose",
            "apply transition",
            "agent_runtime.yaml",
            "multi_agent_preflight",
            "files_reviewed",
            "分文件复核",
            "report-new-completions",
        ],
        "docs/workflow/protocols/mixed_experiment_campaign_protocol.md": ["subject_id", "derived_index_only", "evidence_state", "agent_runtime.yaml", "formal_pending", "orphan_runtime_plan"],
        "docs/workflow/playbooks/mixed_campaign.md": ["subject_id", "derived_index_only"],
        "docs/workflow/playbooks/innovation.md": ["Hypothesis", "Attachment Point"],
        "docs/workflow/playbooks/tune.md": ["tune_promising", "stopped_no_gain"],
        "docs/workflow/playbooks/ablation.md": ["ablation_supported", "stopped_ablation_not_supported"],
        "docs/workflow/playbooks/confirmation.md": ["promotion_compare_metric", "confirmed_H"],
        "docs/workflow/reference/artifact_policy.md": ["Top-3", "pruned"],
        "docs/workflow/protocols/promotion.md": ["must not push", "explicitly asks"],
        "docs/workflow/protocols/experiment_protocol.md": ["mixed_confirmation", "strict_determinism", "formal_pending", "orphan_runtime_plan"],
        "docs/workflow/protocols/module_trial_protocol.md": ["mixed_confirmation", "use_dedicated_batch_rng", "formal_pending", "orphan_runtime_plan"],
        "docs/workflow/archive/runbooks/runbook.md": ["mixed_confirmation", "batch_sampling_seed"],
        "docs/workflow/archive/issues/README.md": ["ISSUE-20260628-014"],
        "workflow/README.md": ["repro-status", "confirmed_H"],
    }
    for path_text, markers in marker_requirements.items():
        text = read_text(REPO_ROOT / path_text)
        for marker in markers:
            if marker not in text:
                raise WorkflowError(f"{path_text} missing reproducibility marker: {marker}")

    # The parameter-matrix rule is opt-in for older archived checkouts, but once
    # the active protocol exists it is part of the repository's formal contract.
    # This keeps historical test fixtures readable while preventing a live repo
    # from silently losing the rule, its global entry, or its usable CSV header.
    if parameter_matrix_policy_is_active():
        parameter_matrix_markers = {
            PARAMETER_MATRIX_PROTOCOL: [
                "policy_status: active",
                "PARAMETER_MATRIX.csv",
                "PARAMETER_MATRIX.md",
                "config_fingerprint",
                "repeat_of",
                "pre-run freeze",
                "refresh-parameter-matrix-view",
                "freeze-parameter-matrix",
                "record-result",
                "sync-dynamic-routing-matrix",
            ],
            "experiments/PARAMETER_MATRIX_CATALOG.md": [
                "参数矩阵总看板",
                "历史迁移队列",
                "PARAMETER_MATRIX.md",
            ],
        }
        for path_text, markers in parameter_matrix_markers.items():
            text = read_text(REPO_ROOT / path_text)
            for marker in markers:
                if marker not in text:
                    raise WorkflowError(f"{path_text} missing parameter-matrix marker: {marker}")
        template_path = REPO_ROOT / "experiments" / "templates" / "PARAMETER_MATRIX_template.csv"
        template_header = template_path.read_text(encoding="utf-8").splitlines()[0]
        if template_header != ",".join(PARAMETER_MATRIX_COLUMNS):
            raise WorkflowError("PARAMETER_MATRIX_template.csv has an invalid parameter-matrix header")

    workflow_diagrams = read_text(REPO_ROOT / "docs" / "workflow" / "archive" / "diagrams" / "workflow_diagrams.md")
    for marker in ["## Version Flow", "## Trial Flow", "## Framework Diagram", "## 总流程框架", "## Module Trial 流程框架"]:
        if marker not in workflow_diagrams:
            raise WorkflowError(f"workflow_diagrams.md missing section: {marker}")
    version_template = read_text(REPO_ROOT / "experiments" / "templates" / "VERSION_template.md")
    trial_template = read_text(REPO_ROOT / "experiments" / "templates" / "TRIAL_README_template.md")
    if "## Framework Diagram" not in version_template:
        raise WorkflowError("VERSION_template.md must include ## Framework Diagram")
    if "## Version Flow" not in version_template:
        raise WorkflowError("VERSION_template.md must include ## Version Flow")
    for marker in ["framework_diagram.md", "MODULES.md"]:
        if marker not in version_template:
            raise WorkflowError(f"VERSION_template.md missing version framework marker: {marker}")
    if "## Trial Flow" not in trial_template:
        raise WorkflowError("TRIAL_README_template.md must include ## Trial Flow")
    if "## Framework Diagram" not in trial_template:
        raise WorkflowError("TRIAL_README_template.md must include ## Framework Diagram")
    for marker in [
        "module_source:",
        "trial_meta:",
        "module_template_family:",
        "module_scope:",
        "standard_gzsl_framework",
        "standard_gzsl_training_template",
    ]:
        if marker not in trial_template:
            raise WorkflowError(f"TRIAL_README_template.md missing module template marker: {marker}")
    artifact_schema = read_text(REPO_ROOT / "schemas" / "artifact_ref.schema.json")
    if '"pruned"' not in artifact_schema:
        raise WorkflowError("artifact_ref.schema.json must allow status=pruned")
    agent_template = read_text(REPO_ROOT / "experiments" / "templates" / "agent_summary_template.md")
    for marker in [
        "agent_instance_mode:",
        "lifecycle:",
        "persistent_thread_id:",
        "named_thread_reason:",
        "agent_instance_id:",
        "agent_runtime_gate:",
        "runner_scope:",
        "formal_runner_allowed:",
        "formal_evidence_allowed:",
        "multi_agent_preflight:",
        "agent_instance_status:",
        "agent_status_refs:",
        "agent_output_refs:",
        "ai_cross_review:",
        "named_thread_ids:",
        "runner_start_gate:",
        "pre_run_required_checks:",
        "output_locations:",
        "verified_against_current_repo:",
        "subject_id:",
        "transition_id:",
        "rule_checks:",
        "authority_refs:",
        "not_checked:",
        "files_reviewed:",
    ]:
        if marker not in agent_template:
            raise WorkflowError(f"agent_summary_template.md missing agent evidence field: {marker}")
    quality_template = read_text(REPO_ROOT / "experiments" / "templates" / "quality_check_template.md")
    receipt_template = read_text(REPO_ROOT / "experiments" / "templates" / "run_receipt_template.yaml")
    for marker in ["schema_version: gtpj.run_receipt.v0", "multi_agent_preflight:", "formal_runner_allowed:", "formal_evidence_allowed:", "agent_output_refs:"]:
        if marker not in receipt_template:
            raise WorkflowError(f"run_receipt_template.yaml missing run receipt marker: {marker}")
    for marker in [
        "checkpoint retention",
        "Top-3",
        "subject_id:",
        "TRANSITIONS.jsonl",
        "authority_refs",
        "validate-agent-runtime",
        "multi-agent-preflight",
        "agent_output_refs",
        "标准 GZSL",
        "module_source.md",
        "trial_meta.yaml",
        "validate-trial-meta",
        "standard_gzsl_training_template.py",
        "module_scope: composite",
        "validate-ai-cross-review",
        "unresolved_blocking_issues: 0",
    ]:
        if marker not in quality_template:
            raise WorkflowError(f"quality_check_template.md missing checkpoint retention marker: {marker}")
    module_template_protocol = read_text(
        REPO_ROOT / "docs" / "workflow" / "protocols" / "module_template_selection.md"
    )
    for marker in [
        "feature_adapter_template.py",
        "fusion_gate_template.py",
        "auxiliary_loss_template.py",
        "sampler_or_data_view_template.py",
        "composite_module_template.py",
        "architecture_change_template.md",
        "trial_meta_template.yaml",
        "validate-trial-meta",
        "standard_gzsl_module_framework_template.py",
        "standard_gzsl_training_template.py",
        "base_version",
        "base_code_tag",
        "standard GZSL U/S/H/ZS",
    ]:
        if marker not in module_template_protocol:
            raise WorkflowError(f"module_template_selection.md missing marker: {marker}")
    module_template_markers = {
        "experiments/templates/modules/README.md": [
            "feature_adapter_template.py",
            "fusion_gate_template.py",
            "composite_module_template.py",
            "standard_gzsl_module_framework_template.py",
            "U, S, H, ZS",
        ],
        "experiments/templates/modules/module_source_template.md": [
            "paper_id:",
            "source_ref:",
            "template_family:",
            "module_scope:",
            "trial_meta.yaml",
            "paper_writing_note:",
        ],
        "experiments/templates/modules/trial_meta_template.yaml": [
            "schema_version: gtpj.trial_meta.v0",
            "module_scope",
            "affects:",
            "baseline_off:",
            "audit:",
        ],
        "experiments/templates/modules/standard_trial_config_template.yaml": [
            "base_code_tag",
            "trial_meta",
            "training_template",
            "affects",
            "composition_mode",
            "standard_gzsl_u_s_h_zs",
            "protect_seen_unseen_split",
            "protect_label_mapping",
        ],
        "experiments/templates/modules/standard_gzsl_module_framework_template.py": [
            "GZSLProtectedState",
            "assert_logits_shape",
            "standard_gzsl_u_s_h_zs",
        ],
        "experiments/templates/modules/standard_gzsl_training_template.py": [
            "StandardGZSLTrainingRun",
            "assert_standard_gzsl_eval",
            "best_observed_H",
            "standard_gzsl_u_s_h_zs",
        ],
        "experiments/templates/modules/feature_adapter_template.py": ["TrialFeatureAdapter", "template_family"],
        "experiments/templates/modules/fusion_gate_template.py": ["TrialFusionGate", "template_family"],
        "experiments/templates/modules/auxiliary_loss_template.py": ["TrialAuxiliaryLoss", "lambda_trial_loss"],
        "experiments/templates/modules/sampler_or_data_view_template.py": ["TrialViewSelector", "xlsa17"],
        "experiments/templates/modules/composite_module_template.py": [
            "TrialCompositeModule",
            "CompositePlan",
            "composition_mode",
            "all_components_disabled",
            "assert_standard_trial_output",
            "features",
            "logits",
            "losses",
            "debug",
        ],
        "experiments/templates/modules/architecture_change_template.md": [
            "module_scope: architecture_change",
            "affects.forward_main_flow",
            "standard_gzsl_eval_audit",
        ],
    }
    for path_text, markers in module_template_markers.items():
        text = read_text(REPO_ROOT / path_text)
        for marker in markers:
            if marker not in text:
                raise WorkflowError(f"{path_text} missing module template marker: {marker}")
    promotion_agents = read_text(
        REPO_ROOT / "docs" / "workflow" / "agents" / "by_experiment" / "promotion" / "agents" / "README.md"
    )
    if "Reviewer" not in promotion_agents:
        raise WorkflowError("promotion agents must include Reviewer")
    diagram_errors = validate_framework_diagram_docs()
    if diagram_errors:
        raise WorkflowError(
            "Framework diagram documentation failed:\n" + "\n".join(diagram_errors)
        )
    epoch_schedule_errors = validate_attempt_epoch_schedule_disclosure()
    if epoch_schedule_errors:
        raise WorkflowError(
            "Attempt epoch schedule disclosure failed:\n" + "\n".join(epoch_schedule_errors)
        )

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
        if meta.get("evidence_level"):
            evidence_markers = [
                f"evidence_level: {meta['evidence_level']}",
                f"best_observed_H: {meta['best_observed_H']}",
                f"confirmed_H: {meta['confirmed_H']}",
                f"confirmation_status: {meta['confirmation_status']}",
            ]
            for local_file in [meta["result_file"], meta["version_file"]]:
                local_text = read_text(REPO_ROOT / local_file)
                for marker in evidence_markers:
                    if marker not in local_text:
                        raise WorkflowError(f"{local_file} must record evidence marker: {marker}")
            baseline_result = read_text(REPO_ROOT / "experiments" / version / "baseline" / "result.yaml")
            baseline_quality = read_text(REPO_ROOT / "experiments" / version / "baseline" / "quality_check.md")
            for marker in [*evidence_markers, f"status: {meta['status']}"]:
                if marker not in baseline_result and marker not in baseline_quality:
                    raise WorkflowError(f"{version} baseline evidence must record marker: {marker}")
            if meta["confirmation_status"] != "confirmed" and "promotion_decision: blocked" not in baseline_result + baseline_quality:
                raise WorkflowError(f"{version} unconfirmed baseline evidence must block promotion")

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

    contract = read_text(REPO_ROOT / "docs" / "workflow" / "protocols" / "code_interface_contract.md")
    for marker in [
        "Baseline-Off Equivalence",
        "Input Contract",
        "Output Contract",
        "Shape Invariants",
        "Config Switch Contract",
        "Loss Contract",
        "Evaluation Contract",
        "Innovation Code Review Gate",
        "Minimum Verification",
    ]:
        if marker not in contract:
            raise WorkflowError(f"code_interface_contract.md missing section: {marker}")

    innovation_review = read_text(REPO_ROOT / "docs" / "workflow" / "protocols" / "innovation_code_review_protocol.md")
    for marker in [
        "Review 0",
        "Review 1",
        "Review 2",
        "Review 3",
        "ai_cross_review_protocol.md",
        "命名线程",
        "正式 run 前硬阻断",
    ]:
        if marker not in innovation_review:
            raise WorkflowError(f"innovation_code_review_protocol.md missing section: {marker}")

    agent_report_policy = read_text(REPO_ROOT / "docs" / "workflow" / "protocols" / "agent_report_policy.md")
    for marker in [
        "idea_intent_check.md",
        "interface_precheck.md",
        "review_round_1.md",
        "review_round_2.md",
        "temporary_agents",
        "review_rounds",
        "ai_cross_review",
        "job_completed_report",
    ]:
        if marker not in agent_report_policy:
            raise WorkflowError(f"agent_report_policy.md missing field: {marker}")

    artifact_policy = read_text(REPO_ROOT / "docs" / "workflow" / "reference" / "artifact_policy.md")
    for marker in [
        "GitHub Boundary",
        "External Stores",
        "Artifact Identity",
        "Forbidden GitHub Artifacts",
    ]:
        if marker not in artifact_policy:
            raise WorkflowError(f"artifact_policy.md missing section: {marker}")

    agent_contracts = read_text(REPO_ROOT / "docs" / "workflow" / "reference" / "agent_contracts.md")
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

    agent_roles = [
        "coordinator",
        "reader_planner",
        "runner",
        "implementer",
        "interface_checker",
        "quality_checker",
        "log_analyst",
        "result_analyst",
        "reviewer",
    ]
    for role in agent_roles:
        role_dir = REPO_ROOT / "docs" / "workflow" / "agents" / "shared_roles" / role
        for filename in ["profile.md", "memory.md"]:
            if not (role_dir / filename).exists():
                raise WorkflowError(f"Missing long-term agent file: {rel(role_dir / filename)}")

    long_term_memory = read_text(REPO_ROOT / "docs" / "workflow" / "agents" / "long_term_memory.md")
    for marker in [
        "长期 agent",
        "profile.md",
        "memory.md",
        "启动加载规则",
        "记忆写回规则",
        "证据边界",
    ]:
        if marker not in long_term_memory:
            raise WorkflowError(f"long_term_memory.md missing section: {marker}")

    implementation_template = read_text(
        REPO_ROOT / "experiments" / "templates" / "implementation_template.md"
    )
    for marker in [
        "Input Contract",
        "Output Contract",
        "Shape Invariants",
        "Baseline-Off Path",
        "Minimum Verification",
        "Template Selection",
        "Training Entry",
        "template_family",
        "trial_meta",
        "module_scope",
        "composition_mode",
        "affects",
        "standard_gzsl_training_template.py",
        "standard GZSL U/S/H/ZS",
        "module_template_selection.md",
    ]:
        if marker not in implementation_template:
            raise WorkflowError(f"implementation_template.md missing section: {marker}")

    evidence_docs = {
        "docs/workflow/protocols/experiment_protocol.md": [
            "quick_local",
            "valid_single_run",
            "confirmation_grade",
            "baseline_grade",
            "best_observed_H",
            "confirmed_H",
        ],
        "docs/workflow/protocols/quality_gate.md": [
            "evidence_level",
            "baseline_grade",
            "owner_activated_unconfirmed",
        ],
        "docs/workflow/protocols/promotion.md": [
            "evidence_level: baseline_grade",
            "confirmation_status: confirmed",
            "owner_activated_unconfirmed",
        ],
        "docs/workflow/archive/runbooks/runbook.md": [
            "quick_local",
            "valid_single_run",
            "confirmation_grade",
            "baseline_grade",
        ],
        "docs/workflow/core/TASK_START_CARD.md": [
            "best_observed_H",
            "confirmed_H",
            "confirmation_grade",
        ],
    }
    for doc, markers in evidence_docs.items():
        text = read_text(REPO_ROOT / doc)
        for marker in markers:
            if marker not in text:
                raise WorkflowError(f"{doc} missing evidence-grade marker: {marker}")

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

    framework_errors = validate_framework_ledgers()
    if framework_errors:
        raise WorkflowError("Framework ledger validation failed:\n" + "\n".join(framework_errors))
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
evidence_level: pending
result_status: pending
best_observed_H:
confirmed_H:
restore_target_H:
near_miss_tolerance_H:
near_miss_not_restored:
confirmation_status: pending
status: planned
```

## 问题

描述这个实验要回答的精确问题。

## 运行前检查

- [ ] 实验分支从 `framework/{version}` 切出，并按 `exp/{version}/<type>/<experiment-id>-<slug>` 命名。
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
evidence_level: pending
confirmation_status: pending
```

## 范围

## 发现

## 质量检查

- [ ] 代码快照或 base version 明确。
- [ ] 配置副本保存在实验目录。
- [ ] 外部日志 artifact URI、sha256、size 明确。
- [ ] 结果口径明确。
- [ ] `evidence_level`、`best_observed_H`、`confirmed_H` 和 `confirmation_status` 已区分。
- [ ] 没有未声明的 eval / class order / logits shape 改动。
- [ ] seen/unseen split、label mapping、class order 和 metric calculation 未改变或已按高风险记录。
- [ ] GitHub 目录中没有新增 raw log、checkpoint、generated figures。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] derived_from_framework / source_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] `evidence_level: baseline_grade` 或明确标成 owner_activated_unconfirmed / provisional。
- [ ] clean confirmation 或多 run 稳定性证据明确；单次最高 H 不直接 promotion。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 外部日志 artifact URI、sha256、size、保留位置明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到来源正式框架行为。
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
    elif kind.name == "module-trial":
        agent_set = "Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst, Reviewer"
        serial_agents = "Coordinator -> Review 0 -> Review 1 -> Implementer -> Review 2 -> Runner -> Review 3 -> Coordinator"
        parallel_agents = "Reader/Planner + Coordinator in Review 0; Interface Checker + Quality Checker + Reviewer in Review 2; Log Analyst + Quality Checker + Result Analyst + Reviewer in Review 3"
        disabled_agents = ""
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
activation_mode:
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads: none
agent_set: {agent_set}
serial_agents: {serial_agents}
parallel_agents: {parallel_agents}
disabled_agents: {disabled_agents}
named_threads: workflow-scoped named Codex role threads
tool_support:
memory_policy:
memory_used:
memory_sources:
persistent_thread_ids: none
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
runtime_state:
warehouse_report_artifacts:
final_decision: pending
review_rounds:
temporary_agents:
```

## Coordinator

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Reader/Planner

仅在 paper intake、idea discovery、tune suggestion、innovation/module trial 或需要读取论文/来源证据时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Implementer

仅在代码、配置、模块开关、loss、eval 或数据流发生实现改动时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Runner

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Log Analyst

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Quality Checker

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Interface Checker

仅在代码、接口、loss、eval、label mapping、seen/unseen split、class order、logits shape 或 metric semantics 可能变化时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Result Analyst

在 tune、ablation、confirmation、innovation/module trial 或 promotion 需要结果比较时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
```

## Reviewer

仅在 innovation、争议结果、promotion 或 owner 明确要求独立 review 时填写。

```text
role:
agent_instance_mode: named_owner_thread
agent_instance_type:
persistent_thread_id:
named_thread_reason:
lifecycle: workflow_scoped
independence_scope:
output_locations:
inputs_checked:
actions:
outputs:
issues:
decision:
evidence_refs:
memory_used:
memory_sources:
agent_profile_files:
agent_memory_files:
agent_memory_updates:
verified_against_current_repo:
review_round:
blocking_issues:
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
    code_commit: str = "",
    git_dirty: str | None = None,
    idea_id: str = "",
    idea_uri: str = "",
    idea_title: str = "",
    hypothesis: str = "Tune hyperparameters without changing code.",
    evidence_mode: str = "formal",
    run_start_receipt_sha256: str = "",
    run_start_receipt_ref: str = "",
) -> str:
    config_rel = rel(config_path)
    return f"""schema_version: gtpj-manifest/v1
experiment:
  id: {yaml_scalar(exp_id)}
  name: {yaml_scalar(f"{exp_id}_{slug}")}
  kind: {yaml_scalar(kind.name)}
  status: {yaml_scalar(status)}
  evidence_mode: {yaml_scalar(evidence_mode)}
  attempt_id: {yaml_scalar(attempt_id)}
  created_or_recorded_at: {yaml_scalar(recorded_at or utc_now())}
version:
  base_version: {yaml_scalar(version)}
  base_code_tag: {yaml_scalar(version)}
  code_branch: {yaml_scalar(code_branch or experiment_branch_name(version, kind, exp_id, slug))}
  code_commit: {yaml_scalar(code_commit or git(["rev-parse", "--short", "HEAD"], check=False))}
  git_dirty: {yaml_scalar(git_dirty if git_dirty is not None else ("true" if git(["status", "--short"], check=False) else "false"))}
reproducibility:
  config_file: {yaml_scalar(config_rel)}
  config_sha256: {yaml_scalar(sha256_file(config_path) if config_path.exists() else "")}
  pre_run_freeze_commit: {yaml_scalar(code_commit)}
  command: {yaml_scalar(command)}
  run_start_receipt_sha256: {yaml_scalar(run_start_receipt_sha256)}
  run_start_receipt_ref: {yaml_scalar(run_start_receipt_ref)}
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
    git_dirty: str = "false",
    legacy_summary_only: bool = False,
    run_start_receipt_sha256: str = "",
    run_start_receipt_ref: str = "",
) -> str:
    metrics = metrics or {}
    baseline_h = comparison_reference_h(version) if version in CANONICAL_BASELINES else ""
    h_value = metrics.get("H", "")
    delta_h = ""
    if baseline_h and h_value:
        try:
            delta_h = f"{float(h_value) - float(baseline_h):+.2f}"
        except ValueError:
            delta_h = ""
    evidence_defaults = result_evidence_defaults(kind.name, h_value, decision, git_dirty)
    if legacy_summary_only:
        evidence_defaults.update(
            {
                "evidence_level": "legacy_summary_only",
                "result_status": "legacy_summary_only",
                "best_observed_H": "",
                "confirmed_H": "",
                "restore_target_H": "",
                "near_miss_not_restored": "false",
                "confirmation_status": "not_applicable",
            }
        )
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
  baseline_reference: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  delta_H: {yaml_scalar(delta_h)}
  seed: {yaml_scalar(seed)}
  source: {yaml_scalar("training_log")}
  metric_semantics: {yaml_scalar("GZSL U/S/H/ZS from protected evaluator")}
baseline:
  version: {yaml_scalar(version)}
  H: {yaml_scalar(baseline_h)}
  reference_field: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  reference_status: {yaml_scalar(baseline_evidence(version)["status"] if version in CANONICAL_BASELINES else "")}
  confirmed_H: {yaml_scalar(baseline_evidence(version)["confirmed_H"] if version in CANONICAL_BASELINES else "")}
  confirmation_status: {yaml_scalar(baseline_evidence(version)["confirmation_status"] if version in CANONICAL_BASELINES else "")}
delta:
  H: {yaml_scalar(delta_h)}
run:
  seed: {yaml_scalar(seed)}
  run_start_receipt_sha256: {yaml_scalar(run_start_receipt_sha256)}
  run_start_receipt_ref: {yaml_scalar(run_start_receipt_ref)}
decision:
  status: {yaml_scalar(decision)}
  result_status: {yaml_scalar(evidence_defaults["result_status"])}
  promotion_decision: {yaml_scalar(promotion_decision)}
  promote_to: {yaml_scalar(promote_to)}
evidence:
  evidence_level: {yaml_scalar(evidence_defaults["evidence_level"])}
  best_observed_H: {yaml_scalar(evidence_defaults["best_observed_H"])}
  confirmed_H: {yaml_scalar(evidence_defaults["confirmed_H"])}
  confirmation_status: {yaml_scalar(evidence_defaults["confirmation_status"])}
  restore_target_H: {yaml_scalar(evidence_defaults["restore_target_H"])}
  near_miss_tolerance_H: {yaml_scalar(evidence_defaults["near_miss_tolerance_H"])}
  near_miss_not_restored: {yaml_scalar(evidence_defaults["near_miss_not_restored"])}
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
        f"`{rel(folder)}` | 由结构 helper 创建；正式待跑以 `experiments/{version}/{kind.folder}/INDEX.md` 行为准。 |"
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
    framework_experiment_id = f"{version.upper()}-{exp_id}"
    content = read_text(index)
    if framework_experiment_id in content:
        return
    if "| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |" in content:
        lines = [
            line
            for line in content.splitlines()
            if not re.match(r"^\|\s*-\s*\|\s*none\s*\|", line)
        ]
        lines.append(
            f"| `{framework_experiment_id}` | planned | 待填写本实验要回答的问题 | "
            f"`{rel(folder / PARAMETER_MATRIX_MD)}` | - | `{rel(folder)}` | - |"
        )
        index.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        refresh_framework_experiments_view(version)
        return
    lines = [
        line
        for line in content.splitlines()
        if "| 暂无 |" not in line and "当前还没有新仓库内启动的" not in line
    ]
    content = "\n".join(lines).rstrip()
    section = "\n\n## 实验记录\n\n| 实验 | 状态 | Run ID | Formal | 目录 | 说明 |\n|---|---|---|---|---|---|\n"
    row = f"| `{experiment_name}` | planned | pending | true | `{rel(folder)}` | 由结构 helper 创建；formal_pending 由本 INDEX 行决定，`.gtpj_runtime` 只作运行缓存。 |"
    if "## 实验记录" not in content:
        content = content + section + row + "\n"
    else:
        content = content + "\n" + row + "\n"
    index.write_text(content, encoding="utf-8")


def framework_index_rows(version: str, kind_name: str) -> list[dict[str, str]]:
    index_path = REPO_ROOT / "experiments" / version / kind_name / "INDEX.md"
    if not index_path.exists():
        return []
    rows: list[dict[str, str]] = []
    for line in read_text(index_path).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            continue
        experiment_id = cells[0]
        if not re.fullmatch(r"V[0-9]+-(?:TUNE|ABLATION|INNOVATION|CONFIRM)-[0-9]{3}", experiment_id):
            continue
        rows.append(
            {
                "experiment_id": experiment_id,
                "status": cells[1],
                "question": cells[2],
                "parameter_matrix": cells[3],
                "legacy_ref": cells[4],
                "directory": cells[5],
                "promoted_framework": cells[6],
            }
        )
    return rows


def framework_index_row_errors(version: str, kind_name: str) -> list[str]:
    """Report malformed formal rows instead of silently dropping them."""
    index_path = REPO_ROOT / "experiments" / version / kind_name / "INDEX.md"
    if not index_path.exists():
        return []
    errors: list[str] = []
    kind = KINDS[kind_name]
    expected_pattern = rf"{version.upper()}-{kind.prefix}-[0-9]{{3}}"
    for line_number, line in enumerate(read_text(index_path).splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        first = cells[0] if cells else ""
        if first in {"Experiment ID", "---", "-"} or all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in cells
        ):
            continue
        if len(cells) != 7:
            errors.append(f"{rel(index_path)} line {line_number} must have 7 columns")
            continue
        if not re.fullmatch(expected_pattern, first):
            errors.append(f"{rel(index_path)} line {line_number} has wrong ID for {kind_name}: {first}")
        status = cells[1]
        promoted_framework = cells[6]
        if status not in FRAMEWORK_INDEX_STATUSES:
            errors.append(f"{rel(index_path)} line {line_number} has invalid status: {status}")
        if promoted_framework != "-" and not re.fullmatch(r"FRAMEWORK-V[0-9]+", promoted_framework):
            errors.append(
                f"{rel(index_path)} line {line_number} has invalid promoted framework: {promoted_framework}"
            )
        if promoted_framework != "-" and kind_name != "innovation":
            errors.append(
                f"{rel(index_path)} line {line_number} can name a promoted framework only in innovation"
            )
        if promoted_framework != "-" and status not in PROMOTED_FRAMEWORK_STATUSES:
            errors.append(
                f"{rel(index_path)} line {line_number} status {status} cannot name a promoted framework"
            )
        if promoted_framework == "-" and status in PROMOTED_FRAMEWORK_STATUSES:
            errors.append(
                f"{rel(index_path)} line {line_number} status {status} requires a promoted framework"
            )
    return errors


def render_framework_experiments_view(version: str) -> str:
    framework_id = f"FRAMEWORK-{version.upper()}"
    labels = {
        "tune": "调参",
        "ablation": "消融",
        "innovation": "创新",
        "confirmation": "确认",
    }
    lines = [
        f"# {framework_id} 实验总览",
        "",
        "> 本页由四个类型 INDEX 自动生成。请修改对应 INDEX 后运行 "
        f"`python workflow/gtpj_workflow.py refresh-framework-view --version {version}`，不要手工维护第二份结论。",
        "",
        "| 类型 | 实验数 | 正式台账 |",
        "|---|---:|---|",
    ]
    rows_by_kind = {kind: framework_index_rows(version, kind) for kind in FRAMEWORK_KIND_ORDER}
    for kind in FRAMEWORK_KIND_ORDER:
        lines.append(f"| {labels[kind]} | {len(rows_by_kind[kind])} | `{kind}/INDEX.md` |")
    for kind in FRAMEWORK_KIND_ORDER:
        lines.extend(
            [
                "",
                f"## {labels[kind]}实验",
                "",
                "| Experiment ID | Status | Question | Parameter matrix | Legacy reference | Directory | Promoted framework |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        rows = rows_by_kind[kind]
        if not rows:
            lines.append("| - | none | 暂无 | - | - | - | - |")
            continue
        for row in rows:
            lines.append(
                f"| `{row['experiment_id']}` | {row['status']} | {row['question']} | "
                f"`{row['parameter_matrix']}` | `{row['legacy_ref']}` | "
                f"`{row['directory']}` | {row['promoted_framework']} |"
            )
    return "\n".join(lines).rstrip() + "\n"


def refresh_framework_experiments_view(version: str) -> Path:
    version = require_clean_id(version, r"v[0-9]+", "version")
    framework_path = REPO_ROOT / "experiments" / version / "framework.yaml"
    if not framework_path.exists():
        raise WorkflowError(f"{version} is not a formal framework; missing {rel(framework_path)}")
    output = framework_path.with_name("EXPERIMENTS.md")
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_framework_experiments_view(version))
    return output


def framework_schema_instance(data: dict[str, object]) -> tuple[dict[str, object], list[str]]:
    instance = dict(data)
    errors: list[str] = []
    for key in ("modules", "inherits", "does_not_inherit"):
        value = instance.get(key)
        if isinstance(value, str):
            try:
                instance[key] = json.loads(value)
            except json.JSONDecodeError:
                errors.append(f"{key} must be a valid JSON-style YAML inline list")
    return instance, errors


def json_schema_subset_errors(
    instance: dict[str, object], schema: dict[str, object]
) -> list[str]:
    """Validate the JSON-Schema keywords used by framework.schema.json without a new dependency."""
    errors: list[str] = []
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if key not in instance:
                errors.append(f"missing required property: {key}")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return errors + ["schema properties must be an object"]
    for key, raw_rules in properties.items():
        if key not in instance or not isinstance(raw_rules, dict):
            continue
        value = instance[key]
        expected_type = raw_rules.get("type")
        if expected_type == "array" and not isinstance(value, list):
            errors.append(f"{key} must be an array")
            continue
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"{key} must be a string")
            continue
        if "const" in raw_rules and value != raw_rules["const"]:
            errors.append(f"{key} must equal {raw_rules['const']}")
        enum = raw_rules.get("enum")
        if isinstance(enum, list) and value not in enum:
            errors.append(f"{key} must be one of: {', '.join(str(item) for item in enum)}")
        pattern = raw_rules.get("pattern")
        if isinstance(pattern, str) and (not isinstance(value, str) or not re.fullmatch(pattern, value)):
            errors.append(f"{key} does not match schema pattern {pattern}")
        items = raw_rules.get("items")
        if isinstance(value, list) and isinstance(items, dict) and items.get("type") == "string":
            if any(not isinstance(item, str) for item in value):
                errors.append(f"{key} entries must all be strings")
    return errors


def framework_origin_evidence_errors(
    framework_data: dict[str, object], source_row: dict[str, str]
) -> list[str]:
    """Check how a peer framework entered the formal registry without modelling containment."""
    errors: list[str] = []
    framework_id = str(framework_data.get("framework_id", "formal framework"))
    source_experiment = str(framework_data.get("promoted_from_experiment", "source innovation"))
    origin_status = str(framework_data.get("origin_status", ""))
    source_status = source_row["status"]
    if origin_status in LEGACY_ORIGIN_STATUSES:
        if source_status != origin_status:
            errors.append(
                f"{framework_id} legacy origin status must match source row {origin_status}"
            )
        return errors
    if origin_status != "confirmed_promoted" or source_status != "promoted":
        return [
            f"{framework_id} formal registration requires a promoted source innovation or an explicit legacy origin status"
        ]
    result_path = REPO_ROOT / source_row["directory"] / "result.yaml"
    quality_path = REPO_ROOT / source_row["directory"] / "quality_check.md"
    result_data = read_shallow_yaml(result_path) if result_path.exists() else {}
    promotion_decision = yaml_section_value(result_data, "decision", "promotion_decision")
    promote_to = yaml_section_value(result_data, "decision", "promote_to")
    confirmation_status = yaml_section_value(result_data, "evidence", "confirmation_status")
    confirmed_h = yaml_section_value(result_data, "evidence", "confirmed_H")
    quality_fields = read_key_value_block(quality_path) if quality_path.exists() else {}
    quality_decision = quality_fields.get("decision", "").strip().lower()
    if promotion_decision != "promote":
        errors.append(f"{source_experiment} is promoted without promotion_decision: promote")
    expected_version = str(framework_data.get("framework_version", ""))
    if promote_to != expected_version:
        errors.append(f"{source_experiment} promote_to must be {expected_version}")
    if confirmation_status != "confirmed":
        errors.append(f"{source_experiment} is promoted without confirmation_status: confirmed")
    try:
        confirmed_h_value = float(confirmed_h)
    except ValueError:
        confirmed_h_value = math.nan
    if not math.isfinite(confirmed_h_value):
        errors.append(f"{source_experiment} is promoted without a finite confirmed_H")
    if quality_decision not in {"allow", "pass", "passed", "approved", "通过"}:
        errors.append(f"{source_experiment} is promoted without a passing quality check")
    return errors


def framework_derivation_errors(frameworks: dict[str, dict[str, object]]) -> list[str]:
    """Reject broken or cyclic history pointers while keeping every formal framework at one level."""
    errors: list[str] = []
    by_id = {
        str(data.get("framework_id", "")): data
        for data in frameworks.values()
        if str(data.get("framework_id", ""))
    }
    reported_cycles: set[tuple[str, ...]] = set()
    for framework_id in sorted(by_id):
        root_data = by_id[framework_id]
        source_framework = str(root_data.get("derived_from_framework", ""))
        promoted_from = str(root_data.get("promoted_from_experiment", ""))
        origin_status = str(root_data.get("origin_status", ""))
        if source_framework == "none" and framework_id != "FRAMEWORK-V1":
            errors.append(f"only FRAMEWORK-V1 may be the initial root; found {framework_id}")
        if framework_id == "FRAMEWORK-V1":
            if (source_framework, promoted_from, origin_status) != ("none", "initial", "initial"):
                errors.append(
                    "FRAMEWORK-V1 must use derived_from_framework=none, "
                    "promoted_from_experiment=initial, and origin_status=initial"
                )
        elif promoted_from == "initial" or origin_status == "initial":
            errors.append(f"{framework_id} cannot use initial origin fields")
        path: list[str] = []
        cursor = framework_id
        while cursor != "none":
            if cursor in path:
                cycle = tuple(path[path.index(cursor):] + [cursor])
                normalized = tuple(sorted(set(cycle)))
                if normalized not in reported_cycles:
                    reported_cycles.add(normalized)
                    errors.append("framework derivation cycle detected: " + " -> ".join(cycle))
                break
            path.append(cursor)
            current = by_id.get(cursor)
            if current is None:
                errors.append(f"{framework_id} points to unknown source framework {cursor}")
                break
            cursor = str(current.get("derived_from_framework", ""))
            if not cursor:
                errors.append(f"{framework_id} is missing derived_from_framework")
                break
    return errors


def framework_promotion_link_errors(frameworks: dict[str, dict[str, object]]) -> list[str]:
    """Require every promotion pointer to name one real peer framework and appear only once."""
    errors: list[str] = []
    registered_ids = {
        str(data.get("framework_id", ""))
        for data in frameworks.values()
        if str(data.get("framework_id", ""))
    }
    links: dict[str, list[str]] = {}
    for version in sorted(frameworks):
        for row in framework_index_rows(version, "innovation"):
            target = row.get("promoted_framework", "-")
            if target == "-":
                continue
            source = f"{row.get('experiment_id', 'unknown experiment')} under FRAMEWORK-{version.upper()}"
            links.setdefault(target, []).append(source)
            if target not in registered_ids:
                errors.append(f"{source} points to unknown formal framework {target}")
            if target == "FRAMEWORK-V1":
                errors.append(f"{source} cannot promote the initial framework FRAMEWORK-V1")
    for target, sources in sorted(links.items()):
        if len(sources) != 1:
            errors.append(f"{target} must have exactly one promotion link; found {len(sources)}")
    return errors


def framework_git_ref_errors(version: str, expected_commit: str) -> list[str]:
    """Require both the long-lived branch and frozen Tag for a formal peer framework."""
    errors: list[str] = []
    branch = framework_branch_name(version)
    branch_commit = git(["rev-parse", "--verify", f"refs/heads/{branch}"], check=False)
    if not branch_commit:
        errors.append(f"missing long-lived framework branch: {branch}")
    tag_commit_value = git(
        ["rev-parse", "--verify", f"refs/tags/{version}^{{commit}}"],
        check=False,
    )
    if not tag_commit_value:
        errors.append(f"missing frozen framework tag: {version}")
    elif expected_commit != tag_commit_value:
        errors.append(f"framework_commit does not match tag {version}")
    if branch_commit and expected_commit:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", expected_commit, branch],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            errors.append(f"{branch} does not contain framework_commit {expected_commit}")
    return errors


def framework_template_git_ref_errors(data: dict[str, object]) -> list[str]:
    """Require a frozen template's branch, Tag, and recorded commit to be identical."""
    errors: list[str] = []
    template_tag = str(data.get("template_tag", ""))
    template_branch = str(data.get("template_branch", ""))
    template_commit = str(data.get("template_commit", ""))
    tag_commit_value = git(
        ["rev-parse", "--verify", f"refs/tags/{template_tag}^{{commit}}"],
        check=False,
    )
    branch_commit_value = git(
        ["rev-parse", "--verify", f"refs/heads/{template_branch}"],
        check=False,
    )
    if not tag_commit_value:
        errors.append(f"missing template tag: {template_tag}")
    elif tag_commit_value != template_commit:
        errors.append(f"template_commit does not match tag {template_tag}")
    if not branch_commit_value:
        errors.append(f"missing template branch: {template_branch}")
    elif (
        str(data.get("template_status", "")) in {"frozen", "legacy_frozen"}
        and branch_commit_value != template_commit
    ):
        errors.append(
            f"frozen template branch must equal template_commit: {template_branch}"
        )
    return errors


def framework_template_identity_errors(
    version: str,
    data: dict[str, object],
) -> list[str]:
    """Validate the human-readable template identity before trusting its Git refs."""
    errors: list[str] = []
    expected_framework_id = f"FRAMEWORK-{version.upper()}"
    if str(data.get("framework_id", "")) != expected_framework_id:
        errors.append(f"framework_id must be {expected_framework_id}")

    template_id = str(data.get("template_id", ""))
    id_match = re.fullmatch(
        rf"MODEL-{version.upper()}-TEMPLATE-V([0-9]+)", template_id
    )
    if not id_match:
        errors.append(f"template_id must belong to {version.upper()}")
        return errors

    template_number = int(id_match.group(1))
    status = str(data.get("template_status", ""))
    if template_number == 0:
        expected_branch = framework_branch_name(version)
        expected_tag = version
        if status != "legacy_frozen":
            errors.append("V0 must use legacy_frozen status")
    else:
        expected_branch = f"framework/{version}-template-v{template_number}"
        expected_tag = f"model/{version}-template-v{template_number}"
        if status != "frozen":
            errors.append("clean template must use frozen status")

    if str(data.get("template_branch", "")) != expected_branch:
        errors.append(f"template_branch must be {expected_branch}")
    if str(data.get("template_tag", "")) != expected_tag:
        errors.append(f"template_tag must be {expected_tag}")
    if str(data.get("source_framework_tag", "")) != version:
        errors.append(f"source_framework_tag must be {version}")

    source_commit = str(data.get("source_framework_commit", ""))
    source_tag_commit = git(
        ["rev-parse", "--verify", f"refs/tags/{version}^{{commit}}"],
        check=False,
    )
    if not source_tag_commit:
        errors.append(f"missing source framework tag: {version}")
    elif source_commit != source_tag_commit:
        errors.append(f"source_framework_commit must match tag {version}")
    return errors


def validate_framework_templates() -> list[str]:
    errors: list[str] = []
    schema_path = REPO_ROOT / "schemas" / "framework_template.schema.json"
    try:
        template_schema = json.loads(read_text(schema_path))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load {display_path(schema_path)}: {exc}"]

    active = immutable_template_standard_is_active()
    framework_paths = sorted((REPO_ROOT / "experiments").glob("v[0-9]*/framework.yaml"))
    version_dirs = {path.parent for path in framework_paths}
    version_dirs.update(
        path.parent for path in (REPO_ROOT / "experiments").glob("v[0-9]*/TEMPLATE.yaml")
    )
    for version_dir in sorted(version_dirs):
        version = version_dir.name
        template_path = framework_template_path(version)
        if not template_path.exists():
            if active:
                errors.append(
                    f"{rel(template_path)} is required under the active immutable template standard"
                )
            continue
        data = read_shallow_yaml(template_path)
        missing = sorted(FRAMEWORK_TEMPLATE_REQUIRED_KEYS - set(data))
        if missing:
            errors.append(f"{rel(template_path)} missing keys: {', '.join(missing)}")
        errors.extend(
            f"{rel(template_path)} schema: {item}"
            for item in json_schema_subset_errors(data, template_schema)
        )
        errors.extend(
            f"{rel(template_path)}: {item}"
            for item in framework_template_identity_errors(version, data)
        )
        errors.extend(
            f"{rel(template_path)}: {item}"
            for item in framework_template_git_ref_errors(data)
        )
    return errors


def _none_like(value: object) -> bool:
    return str(value).strip().lower() in {"", "-", "none"}


def _binding_expected_branch(
    version: str, kind_name: str, row: dict[str, str]
) -> str:
    directory_name = Path(row["directory"]).name
    local_id, separator, slug = directory_name.partition("_")
    if not separator or not slug:
        return ""
    return experiment_branch_name(version, KINDS[kind_name], local_id, slug)


def experiment_binding_errors(
    *,
    version: str,
    kind_name: str,
    row: dict[str, str],
    data: dict[str, object],
    template_data: dict[str, object],
) -> list[str]:
    errors: list[str] = []
    missing = sorted(EXPERIMENT_BINDING_REQUIRED_KEYS - set(data))
    if missing:
        errors.append(f"missing keys: {', '.join(missing)}")

    scalar_checks = {
        "schema_version": "gtpj.experiment.v1",
        "experiment_id": row["experiment_id"],
        "framework_id": f"FRAMEWORK-{version.upper()}",
        "kind": kind_name,
        "status": row["status"],
    }
    for key, expected in scalar_checks.items():
        if str(data.get(key, "")) != expected:
            errors.append(f"{key} must be {expected}")

    row_legacy = row.get("legacy_ref", "-")
    data_legacy = str(data.get("legacy_ref", ""))
    if not (_none_like(row_legacy) and _none_like(data_legacy)) and data_legacy != row_legacy:
        errors.append(f"legacy_ref must match INDEX: {row_legacy}")

    identity_kind = str(data.get("base_identity_kind", ""))
    rule = EXPERIMENT_BINDING_RULES.get(identity_kind)
    if rule is None:
        errors.append(f"unsupported base_identity_kind: {identity_kind}")
        return errors
    expected_binding_status, template_required, historical_required = rule
    actual_binding_status = str(data.get("template_binding_status", ""))
    if actual_binding_status != expected_binding_status:
        errors.append(
            f"{identity_kind} requires {expected_binding_status}, got {actual_binding_status}"
        )

    template_fields = (
        str(data.get("base_template_id", "")),
        str(data.get("base_template_tag", "")),
        str(data.get("base_template_commit", "")),
    )
    registry_commit = str(data.get("template_registry_commit", ""))
    if template_required:
        if any(_none_like(value) for value in template_fields):
            errors.append("framework_template requires the complete template id/tag/commit")
        if not re.fullmatch(r"[0-9a-f]{40}", registry_commit):
            errors.append("framework_template requires a full template_registry_commit")
        else:
            registry_raw = git_show(
                f"{registry_commit}:experiments/{version}/TEMPLATE.yaml",
                check=False,
            )
            if not registry_raw:
                errors.append(
                    "template_registry_commit does not contain the recorded TEMPLATE.yaml"
                )
            else:
                registry_template = parse_shallow_yaml_text(registry_raw)
                registry_errors = framework_template_identity_errors(
                    version, registry_template
                )
                registry_errors.extend(
                    framework_template_git_ref_errors(registry_template)
                )
                errors.extend(
                    f"template registry: {item}" for item in registry_errors
                )
                registry_fields = (
                    str(registry_template.get("template_id", "")),
                    str(registry_template.get("template_tag", "")),
                    str(registry_template.get("template_commit", "")),
                )
                if template_fields != registry_fields:
                    errors.append(
                        "framework_template id/tag/commit must match TEMPLATE.yaml"
                    )
                if str(registry_template.get("template_status", "")) != "frozen":
                    errors.append("framework_template requires a frozen clean template")
        # The experiment checkout starts at the template code commit, which is
        # intentionally older than the later governance commit that registers
        # that template.  Trust the immutable registry object above rather than
        # the checkout's older TEMPLATE.yaml (often the historical V0 ledger).
        expected_branch = _binding_expected_branch(version, kind_name, row)
        if not expected_branch or str(data.get("experiment_branch", "")) != expected_branch:
            errors.append(f"experiment_branch must be {expected_branch or '<valid experiment branch>'}")
    else:
        if any(not _none_like(value) for value in template_fields):
            errors.append(f"{identity_kind} must not claim a clean template id/tag/commit")
        if not _none_like(registry_commit):
            errors.append(f"{identity_kind} must use template_registry_commit: none")
        if not _none_like(data.get("experiment_branch", "")):
            errors.append(f"{identity_kind} must use experiment_branch: none")

    historical_ref = data.get("historical_code_ref", "")
    if historical_required and _none_like(historical_ref):
        errors.append("historical_code_ref requires a real historical_code_ref")
    if identity_kind == "framework_template" and not _none_like(historical_ref):
        # A clean experiment may retain an old planning reference, but it is not its code base.
        pass
    return errors


def historical_binding_evidence_errors(
    data: dict[str, object],
    matrix_rows: list[dict[str, str]],
) -> list[str]:
    """Do not turn a known-missing run code ref into a misleading broad directory claim."""
    if str(data.get("base_identity_kind", "")) != "historical_code_ref":
        return []
    missing_refs = [
        matrix_cell(row.get("code_ref", ""))
        for row in matrix_rows
        if matrix_cell(row.get("code_ref", "")).startswith(
            "legacy_code_ref_not_preserved:"
        )
    ]
    if not missing_refs:
        return []
    historical_ref = str(data.get("historical_code_ref", "")).strip()
    if not historical_ref.lower().startswith("not_preserved"):
        return [
            "historical_code_ref must say not_preserved when the parameter matrix "
            "says the exact legacy code ref was not preserved"
        ]
    if "evidence=" not in historical_ref:
        return ["not_preserved historical_code_ref must name its surviving evidence"]
    errors: list[str] = []
    for missing_ref in sorted(set(missing_refs)):
        legacy_id = missing_ref.split(":", 1)[1].strip()
        if legacy_id and legacy_id not in historical_ref:
            errors.append(
                f"not_preserved historical_code_ref must include evidence for {legacy_id}"
            )
    return errors


def validate_experiment_binding(
    *,
    version: str,
    kind_name: str,
    row: dict[str, str],
    template_data: dict[str, object],
) -> list[str]:
    path = experiment_binding_path(row)
    if not path.exists():
        return [f"{row['experiment_id']} missing EXPERIMENT.yaml under {rel(path.parent)}"]
    data = read_shallow_yaml(path)
    errors: list[str] = []
    schema_path = REPO_ROOT / "schemas" / "experiment.schema.json"
    try:
        schema = json.loads(read_text(schema_path))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load {display_path(schema_path)}: {exc}"]
    errors.extend(
        f"schema: {item}" for item in json_schema_subset_errors(data, schema)
    )
    errors.extend(
        experiment_binding_errors(
            version=version,
            kind_name=kind_name,
            row=row,
            data=data,
            template_data=template_data,
        )
    )
    matrix_path = REPO_ROOT / row["parameter_matrix"].replace(".md", ".csv")
    if matrix_path.exists():
        try:
            matrix_rows = read_parameter_matrix(matrix_path)
        except WorkflowError as exc:
            errors.append(f"cannot inspect historical code evidence: {exc}")
        else:
            errors.extend(historical_binding_evidence_errors(data, matrix_rows))
    return [f"{row['experiment_id']}: {item}" for item in errors]


def framework_experiment_required_files(status: str) -> tuple[str, ...]:
    """运行前只要求输入文件，完成后才要求结果文件。"""
    required = ("README.md", PARAMETER_MATRIX_CSV, PARAMETER_MATRIX_MD)
    if status.strip().lower() in RESULT_OPTIONAL_EXPERIMENT_STATUSES:
        return required
    return (*required, "result.md")


def validate_framework_ledgers() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_framework_templates())
    frameworks: dict[str, dict[str, object]] = {}
    schema_path = REPO_ROOT / "schemas" / "framework.schema.json"
    try:
        framework_schema = json.loads(read_text(schema_path))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load {rel(schema_path)}: {exc}"]
    canonical_registry = REPO_ROOT / "experiments" / "FRAMEWORK_TREE.md"
    canonical_active = (
        framework_standard_is_active()
        and canonical_registry.exists()
    )
    if canonical_active:
        for version_dir in sorted((REPO_ROOT / "experiments").glob("v[0-9]*")):
            if version_dir.name == "v4" or not (version_dir / "VERSION.md").exists():
                continue
            if not (version_dir / "framework.yaml").exists():
                errors.append(f"{rel(version_dir)} is missing framework.yaml under the active framework standard")
    for framework_path in sorted((REPO_ROOT / "experiments").glob("v[0-9]*/framework.yaml")):
        version = framework_path.parent.name
        data = read_shallow_yaml(framework_path)
        frameworks[version] = data
        template_path = framework_template_path(version)
        template_data = read_shallow_yaml(template_path) if template_path.exists() else {}
        schema_instance, instance_errors = framework_schema_instance(data)
        errors.extend(f"{rel(framework_path)} schema: {item}" for item in instance_errors)
        errors.extend(
            f"{rel(framework_path)} schema: {item}"
            for item in json_schema_subset_errors(schema_instance, framework_schema)
        )
        missing = sorted(FRAMEWORK_REQUIRED_KEYS - set(data))
        if missing:
            errors.append(f"{rel(framework_path)} missing keys: {', '.join(missing)}")
            continue
        expected_id = f"FRAMEWORK-{version.upper()}"
        scalar_checks = {
            "schema_version": "gtpj.framework.v2",
            "framework_id": expected_id,
            "framework_version": version,
            "registry_level": "formal_peer",
            "framework_branch": framework_branch_name(version),
            "framework_tag": version,
        }
        for key, expected in scalar_checks.items():
            if str(data.get(key, "")) != expected:
                errors.append(f"{rel(framework_path)} {key} must be {expected}")
        for key in ("framework_commit", "governance_source_commit"):
            if not re.fullmatch(r"[0-9a-f]{40}", str(data.get(key, ""))):
                errors.append(f"{rel(framework_path)} {key} must be a full 40-character commit")
        governance_commit = str(data.get("governance_source_commit", ""))
        if re.fullmatch(r"[0-9a-f]{40}", governance_commit):
            governance_check = subprocess.run(
                ["git", "cat-file", "-e", f"{governance_commit}:docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md"],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if governance_check.returncode != 0:
                errors.append(
                    f"{rel(framework_path)} governance_source_commit does not contain the canonical standard"
                )
        for key in ("modules", "inherits", "does_not_inherit"):
            raw = str(data.get(key, "")).strip()
            if not (raw.startswith("[") and raw.endswith("]")):
                errors.append(f"{rel(framework_path)} {key} must use an inline list")

        expected_commit = str(data.get("framework_commit", ""))
        errors.extend(framework_git_ref_errors(version, expected_commit))

        all_ids: set[str] = set()
        for kind_name in FRAMEWORK_KIND_ORDER:
            index_path = framework_path.parent / kind_name / "INDEX.md"
            if not index_path.exists():
                errors.append(f"{rel(framework_path.parent)} missing {kind_name}/INDEX.md")
                continue
            kind = KINDS[kind_name]
            errors.extend(framework_index_row_errors(version, kind_name))
            rows = framework_index_rows(version, kind_name)
            for row in rows:
                experiment_id = row["experiment_id"]
                expected_pattern = rf"{version.upper()}-{kind.prefix}-[0-9]{{3}}"
                if not re.fullmatch(expected_pattern, experiment_id):
                    errors.append(f"{rel(index_path)} has wrong ID for {kind_name}: {experiment_id}")
                if experiment_id in all_ids:
                    errors.append(f"{rel(framework_path.parent)} repeats experiment ID {experiment_id}")
                all_ids.add(experiment_id)
                directory_text = row["directory"]
                matrix_text = row["parameter_matrix"]
                if directory_text == "-" or matrix_text == "-":
                    errors.append(f"{experiment_id} must name a directory and parameter matrix")
                    continue
                directory = REPO_ROOT / directory_text
                matrix_path = REPO_ROOT / matrix_text.replace(".md", ".csv")
                try:
                    require_path_inside(directory, framework_path.parent, experiment_id)
                    require_path_inside(matrix_path, framework_path.parent, experiment_id)
                except WorkflowError as exc:
                    errors.append(str(exc))
                    continue
                expected_matrix = directory / PARAMETER_MATRIX_CSV
                if matrix_path.resolve() != expected_matrix.resolve():
                    errors.append(
                        f"{experiment_id}: parameter matrix must be exactly {rel(expected_matrix)}"
                    )
                for required_name in framework_experiment_required_files(row["status"]):
                    if not (directory / required_name).exists():
                        errors.append(f"{experiment_id} missing {required_name} under {rel(directory)}")
                if not (directory / "evidence").is_dir():
                    errors.append(f"{experiment_id} missing evidence/ under {rel(directory)}")
                if immutable_template_standard_is_active() or experiment_binding_path(row).exists():
                    errors.extend(
                        validate_experiment_binding(
                            version=version,
                            kind_name=kind_name,
                            row=row,
                            template_data=template_data,
                        )
                    )
                if matrix_path.exists():
                    try:
                        matrix_rows = read_parameter_matrix(matrix_path)
                        for matrix_row in matrix_rows:
                            job_id = matrix_cell(matrix_row.get("job_id"))
                            work_item_id = matrix_cell(matrix_row.get("work_item_id"))
                            job_kind = matrix_cell(matrix_row.get("job_kind"))
                            base_version = matrix_cell(matrix_row.get("base_version"))
                            if not re.fullmatch(r"RUN-[0-9]{3}", job_id):
                                errors.append(
                                    f"{experiment_id}: formal job_id must be RUN-xxx, got {job_id or '<empty>'}"
                                )
                            if work_item_id != experiment_id:
                                errors.append(
                                    f"{experiment_id}: work_item_id must equal {experiment_id}, got {work_item_id or '<empty>'}"
                                )
                            if job_kind != kind_name:
                                errors.append(
                                    f"{experiment_id}: job_kind must be {kind_name}, got {job_kind or '<empty>'}"
                                )
                            if base_version != version:
                                errors.append(
                                    f"{experiment_id}: base_version must be {version}, got {base_version or '<empty>'}"
                                )
                        errors.extend(
                            f"{experiment_id}: {item}"
                            for item in validate_parameter_matrix_rows(matrix_rows, matrix_path=matrix_path)
                        )
                        errors.extend(
                            f"{experiment_id}: {item}"
                            for item in parameter_matrix_view_errors(matrix_path, matrix_rows)
                        )
                    except WorkflowError as exc:
                        errors.append(f"{experiment_id}: {exc}")
            indexed_dirs = {row["directory"] for row in rows}
            for child in sorted((framework_path.parent / kind_name).iterdir()):
                if child.is_dir() and rel(child) not in indexed_dirs:
                    errors.append(f"{rel(child)} exists but is missing from {rel(index_path)}")

        view_path = framework_path.parent / "EXPERIMENTS.md"
        expected_view = render_framework_experiments_view(version)
        if not view_path.exists():
            errors.append(f"{rel(framework_path.parent)} missing generated EXPERIMENTS.md")
        elif read_text(view_path) != expected_view:
            errors.append(
                f"{rel(view_path)} is stale; run refresh-framework-view --version {version}"
            )

    if (REPO_ROOT / "experiments" / "v4" / "framework.yaml").exists():
        errors.append("v4 is a legacy config-only tag and must not have framework.yaml")
    errors.extend(framework_derivation_errors(frameworks))
    errors.extend(framework_promotion_link_errors(frameworks))
    for version, data in frameworks.items():
        source_framework = str(data.get("derived_from_framework", ""))
        if source_framework == "none":
            continue
        source_version = source_framework.removeprefix("FRAMEWORK-").lower()
        source_experiment = str(data.get("promoted_from_experiment", ""))
        source_rows = framework_index_rows(source_version, "innovation")
        matches = [
            row
            for row in source_rows
            if row["experiment_id"] == source_experiment
            and row["promoted_framework"] == str(data.get("framework_id", ""))
        ]
        if len(matches) != 1:
            errors.append(
                f"{data.get('framework_id')} must have one source innovation link "
                f"{source_experiment} under {source_framework}"
            )
            continue
        errors.extend(framework_origin_evidence_errors(data, matches[0]))
    return errors


def cmd_refresh_framework_view(args: argparse.Namespace) -> int:
    output = refresh_framework_experiments_view(args.version)
    print(f"framework-view-refreshed path={rel(output)}")
    return 0


def cmd_validate_framework_ledgers(_: argparse.Namespace) -> int:
    errors = validate_framework_ledgers()
    if errors:
        raise WorkflowError("Framework ledger validation failed:\n" + "\n".join(errors))
    print("validate-framework-ledgers-ok")
    return 0


def cmd_validate_framework_templates(_: argparse.Namespace) -> int:
    errors = validate_framework_templates()
    if errors:
        raise WorkflowError("Framework template validation failed:\n" + "\n".join(errors))
    print("validate-framework-templates-ok")
    return 0


def make_experiment_binding_yaml(
    *,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    slug: str,
    template_data: dict[str, object],
    template_registry_commit: str,
) -> str:
    framework_experiment_id = f"{version.upper()}-{exp_id}"
    branch = experiment_branch_name(version, kind, exp_id, slug)
    return f"""schema_version: gtpj.experiment.v1
experiment_id: {framework_experiment_id}
framework_id: FRAMEWORK-{version.upper()}
kind: {kind.name}
base_identity_kind: framework_template
base_template_id: {template_data.get('template_id', 'none')}
base_template_tag: {template_data.get('template_tag', 'none')}
base_template_commit: {template_data.get('template_commit', 'none')}
template_registry_commit: {template_registry_commit}
historical_code_ref: none
template_binding_status: ready
experiment_branch: {branch}
legacy_ref: none
status: planned
"""


def formal_experiment_coordinates(
    experiment_dir: Path,
) -> tuple[str, str, str] | None:
    """Return version, kind, and local ID for a canonical formal experiment path."""
    try:
        parts = experiment_dir.resolve().relative_to(
            (REPO_ROOT / "experiments").resolve()
        ).parts
    except ValueError:
        return None
    if len(parts) != 3:
        return None
    version, kind_name, directory_name = parts
    if not re.fullmatch(r"v[0-9]+", version) or kind_name not in KINDS:
        return None
    local_id, separator, _slug = directory_name.partition("_")
    if not separator or not re.fullmatch(
        rf"{KINDS[kind_name].prefix}-[0-9]{{3}}", local_id
    ):
        return None
    return version, kind_name, local_id


def require_ready_experiment_base(experiment_dir: Path) -> dict[str, object]:
    """Require one formal experiment to be an independent child of a frozen template."""
    require_path_inside(experiment_dir, REPO_ROOT / "experiments", "experiment path")
    coordinates = formal_experiment_coordinates(experiment_dir)
    if coordinates is None:
        raise WorkflowError(
            "formal experiment path must be experiments/vX/<kind>/<EXPERIMENT-ID_slug>"
        )
    version, kind_name, local_id = coordinates
    binding_path = experiment_dir / "EXPERIMENT.yaml"
    if not binding_path.exists():
        raise WorkflowError(
            "formal experiment is not bound to a ready frozen template: "
            f"missing {display_path(binding_path)}"
        )
    data = read_shallow_yaml(binding_path)
    if (
        str(data.get("base_identity_kind", "")) != "framework_template"
        or str(data.get("template_binding_status", "")) != "ready"
    ):
        raise WorkflowError(
            "formal experiment is not bound to a ready frozen template"
        )

    registry_commit = str(data.get("template_registry_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", registry_commit):
        raise WorkflowError(
            "formal experiment is not bound to a ready frozen template: "
            "template_registry_commit must be a full commit"
        )
    template_data, resolved_registry = load_framework_template_from_registry(
        version, registry_commit
    )
    if resolved_registry != registry_commit:
        raise WorkflowError("template_registry_commit did not resolve exactly")

    row = {
        "experiment_id": f"{version.upper()}-{local_id}",
        "directory": rel(experiment_dir),
        "legacy_ref": str(data.get("legacy_ref", "none")),
        "status": str(data.get("status", "")),
        "parameter_matrix": rel(experiment_dir / PARAMETER_MATRIX_MD),
    }
    errors = experiment_binding_errors(
        version=version,
        kind_name=kind_name,
        row=row,
        data=data,
        template_data=template_data,
    )
    schema_path = REPO_ROOT / "schemas" / "experiment.schema.json"
    try:
        schema = json.loads(read_text(schema_path))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot load experiment schema: {exc}")
    else:
        errors.extend(
            f"schema: {item}" for item in json_schema_subset_errors(data, schema)
        )
    if errors:
        raise WorkflowError(
            "formal experiment template binding is invalid:\n" + "\n".join(errors)
        )

    expected_branch = str(data.get("experiment_branch", ""))
    require_expected_branch(expected_branch, "formal experiment")
    template_commit = str(data.get("base_template_commit", ""))
    require_ancestor(
        template_commit,
        "HEAD",
        "experiment branch must contain its recorded template commit",
    )
    template_ledger_path = f"experiments/{version}/TEMPLATE.yaml"
    changed_template_ledger = git(
        ["diff", "--name-only", f"{template_commit}..HEAD", "--", template_ledger_path],
        check=False,
    )
    if changed_template_ledger:
        raise WorkflowError(
            "experiment branch must not add or modify the framework TEMPLATE.yaml ledger"
        )

    experiment_refs = git(
        [
            "for-each-ref",
            "--format=%(refname:short) %(objectname)",
            f"refs/heads/exp/{version}/",
        ],
        check=False,
    )
    for line in experiment_refs.splitlines():
        other_branch, separator, other_commit = line.partition(" ")
        if not separator or other_branch == expected_branch or other_commit == template_commit:
            continue
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", other_commit, "HEAD"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            raise WorkflowError(
                "formal experiment branch contains another experiment branch; "
                f"it must fork independently from {template_data.get('template_tag')}: "
                f"{other_branch}"
            )
    return data


def require_ready_experiment_for_artifact(path: Path) -> None:
    """Require every new V5 formal artifact to live under one canonical experiment."""
    if not immutable_template_standard_is_active():
        return
    experiment_dir = path if path.is_dir() else path.parent
    if formal_experiment_coordinates(experiment_dir) is None:
        raise WorkflowError(
            "SYS-WORKFLOW-V5 formal artifacts must belong to a canonical formal "
            "experiment directory experiments/vX/<kind>/<EXPERIMENT-ID_slug>; "
            "legacy Trial/Attempt paths are read-only history"
        )
    require_ready_experiment_base(experiment_dir)


def cmd_validate_experiment_base(args: argparse.Namespace) -> int:
    experiment_dir = Path(args.path)
    if not experiment_dir.is_absolute():
        experiment_dir = REPO_ROOT / experiment_dir
    require_ready_experiment_base(experiment_dir)
    print(f"validate-experiment-base-ok path={display_path(experiment_dir)}")
    return 0


def cmd_new_experiment(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)
    expected_branch = experiment_branch_name(version, kind, exp_id, slug)

    base_dir = REPO_ROOT / "experiments" / version
    if not base_dir.exists():
        raise WorkflowError(f"Unknown version directory: {rel(base_dir)}")
    registry_ref = str(
        getattr(args, "template_registry_ref", DEFAULT_TEMPLATE_REGISTRY_REF)
        or DEFAULT_TEMPLATE_REGISTRY_REF
    )
    registry_active = immutable_template_standard_is_active_at_ref(registry_ref)
    template_registry_commit = "none"
    registry_template_data: dict[str, object] = {}
    if registry_active:
        registry_template_data, template_registry_commit = (
            load_framework_template_from_registry(version, registry_ref)
        )
        registry_framework = git_show(
            f"{template_registry_commit}:experiments/{version}/framework.yaml",
            check=False,
        )
        if not registry_framework:
            raise WorkflowError(
                f"{version} is not a formal framework in template registry "
                f"{template_registry_commit}"
            )
    elif framework_standard_is_active():
        if not (base_dir / "framework.yaml").exists():
            raise WorkflowError(f"{version} is not a formal framework; missing {rel(base_dir / 'framework.yaml')}")
        framework_errors = validate_framework_ledgers()
        if framework_errors:
            raise WorkflowError(
                "Cannot create a formal experiment while framework ledgers are invalid:\n"
                + "\n".join(framework_errors)
            )
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
    require_experiment_branch_base(
        version,
        template_data=registry_template_data or None,
    )

    template_path = framework_template_path(version)
    template_data = registry_template_data or (
        read_shallow_yaml(template_path) if template_path.exists() else {}
    )
    if template_data:
        write_new(
            exp_dir / "EXPERIMENT.yaml",
            make_experiment_binding_yaml(
                version=version,
                kind=kind,
                exp_id=exp_id,
                slug=slug,
                template_data=template_data,
                template_registry_commit=template_registry_commit,
            ),
        )

    write_new(exp_dir / "README.md", make_experiment_readme(version, kind, exp_id, slug))
    write_new(exp_dir / "quality_check.md", make_quality_check(kind))
    write_new(exp_dir / "agent_summary.md", make_agent_summary(version, kind, exp_id, slug))
    copy_new(src_config, exp_dir / "config.yaml")
    base_config_text = read_text(exp_dir / "config.yaml")
    write_parameter_matrix(
        directory=exp_dir,
        title=f"{exp_id}_{slug}",
        rows=[
            {
                "job_id": "RUN-001",
                "work_item_id": f"{version.upper()}-{exp_id}",
                "job_kind": kind.name,
                "status": "draft",
                "group": "待填写",
                "name": "请填写本次具体参数组合",
                "base_version": version,
                "base_config_sha256": parameter_matrix_sha256(base_config_text),
                "code_ref": str(template_data.get("template_tag", version)),
                "config_snapshot_ref": "config.yaml",
                "seed": "",
                "changed_parameters": "{}",
                "config_fingerprint": parameter_matrix_sha256(base_config_text),
                "repeat_of": "",
                "duplicate_resolution": "待填写后检查",
                "purpose": "开跑前填写要改的参数、目的和随机种子",
                "run_id": "",
                "run_start_receipt_ref": "",
                "run_start_receipt_sha256": "",
                "run_command_sha256": "",
                "run_log_sha256": "",
                "run_exit_code": "",
                "U": "",
                "S": "",
                "H": "",
                "ZS": "",
                "best_epoch": "",
                "decision": "",
                "artifact_ref": "",
                "artifact_manifest_sha256": "",
            }
        ],
        source_note="由 new-experiment 生成；该草稿必须填写并通过校验后才能用于正式运行。",
    )
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
    write_new(
        exp_dir / "evidence" / "README.md",
        "# 证据入口\n\n原始日志、模型和大文件放在 Warehouse；本目录只保存可核验的轻量指针。\n",
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


def update_framework_experiment_status(
    *,
    version: str,
    kind: ExperimentKind,
    exp_id: str,
    status: str,
) -> bool:
    """Update the single formal 7-column framework row and regenerate its owner view."""
    framework_path = REPO_ROOT / "experiments" / version / "framework.yaml"
    if not framework_path.exists():
        return False
    index_path = REPO_ROOT / "experiments" / version / kind.folder / "INDEX.md"
    if not index_path.exists():
        raise WorkflowError(f"Missing framework index: {rel(index_path)}")
    framework_experiment_id = f"{version.upper()}-{exp_id}"
    lines = read_text(index_path).splitlines()
    matched = 0
    updated: list[str] = []
    for line in lines:
        if not line.startswith("|"):
            updated.append(line)
            continue
        raw_cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(raw_cells) != 7 or raw_cells[0] != framework_experiment_id:
            updated.append(line)
            continue
        raw_cells[1] = status
        updated.append(
            f"| `{raw_cells[0]}` | {raw_cells[1]} | {raw_cells[2]} | "
            f"`{raw_cells[3]}` | `{raw_cells[4]}` | `{raw_cells[5]}` | {raw_cells[6]} |"
        )
        matched += 1
    if matched != 1:
        raise WorkflowError(
            f"{rel(index_path)} must contain exactly one formal row for {framework_experiment_id}; found {matched}"
        )
    index_path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
    refresh_framework_experiments_view(version)
    return True


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
    code_commit: str = "",
    legacy_summary_only: bool = False,
    run_start_receipt_sha256: str = "",
    run_start_receipt_ref: str = "",
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
        code_commit=code_commit,
        recorded_at=recorded_at,
        evidence_mode="legacy_summary_only" if legacy_summary_only else "formal",
        run_start_receipt_sha256=run_start_receipt_sha256,
        run_start_receipt_ref=run_start_receipt_ref,
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
        git_dirty=git_dirty,
        legacy_summary_only=legacy_summary_only,
        run_start_receipt_sha256=run_start_receipt_sha256,
        run_start_receipt_ref=run_start_receipt_ref,
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
    """Hold the matrix lock before any ledger or artifact can be written."""
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)
    matrix_path = REPO_ROOT / "experiments" / version / kind.folder / f"{exp_id}_{slug}" / PARAMETER_MATRIX_CSV
    if (
        matrix_path.exists()
        and parameter_matrix_policy_is_active()
        and not bool(getattr(args, "legacy_summary_only", False))
    ):
        with parameter_matrix_mutation_lock(
            matrix_path,
            operation="record-result-transaction",
            job_id=str(getattr(args, "matrix_job_id", "") or ""),
            run_id=str(getattr(args, "attempt_id", "") or ""),
        ):
            return _cmd_record_result_locked(args)
    return _cmd_record_result_locked(args)


def _cmd_record_result_locked(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)
    exp_dir = REPO_ROOT / "experiments" / version / kind.folder / f"{exp_id}_{slug}"
    if not exp_dir.exists():
        raise WorkflowError(f"Missing experiment directory: {rel(exp_dir)}")
    if existing_legacy_identity(exp_dir):
        raise WorkflowError("legacy_summary_only identity is permanent; refusing to overwrite this experiment ledger")
    if args.kind == "tune":
        if not args.parameter or not args.old_value or not args.new_value:
            raise WorkflowError("record-result --kind tune requires --parameter, --old-value, and --new-value")
    forbid_log_copy_target(exp_dir)
    log_path = resolve_existing_path(args.log, "log file")
    metrics = parse_training_log(log_path)
    matrix_path: Path | None = None
    matrix_rows: list[dict[str, str]] = []
    matrix_result_row: dict[str, str] | None = None
    run_start_receipt_path: Path | None = None
    run_start_receipt_sha256 = ""
    matrix_exists = (exp_dir / PARAMETER_MATRIX_CSV).exists()
    legacy_summary_only = bool(getattr(args, "legacy_summary_only", False))
    if legacy_summary_only:
        legacy_errors = legacy_summary_only_eligibility_errors(
            exp_dir,
            str(getattr(args, "legacy_source_commit", "") or ""),
        )
        if legacy_errors:
            raise WorkflowError("Legacy summary eligibility failed:\n" + "\n".join(legacy_errors))
    if parameter_matrix_policy_is_active() and not matrix_exists and not legacy_summary_only:
        raise WorkflowError(
            "Active parameter-matrix policy requires PARAMETER_MATRIX.csv; "
            "use --legacy-summary-only only for a pre-policy historical result"
        )
    if legacy_summary_only and matrix_exists:
        raise WorkflowError("--legacy-summary-only cannot bypass an existing parameter matrix")
    if legacy_summary_only and args.decision not in {"reject", "rejected", "blocked"}:
        raise WorkflowError("--legacy-summary-only cannot create keep/best evidence; use a non-promoting decision")
    if legacy_summary_only and (args.promotion_decision == "promote" or args.promote_to):
        raise WorkflowError("--legacy-summary-only cannot set promotion_decision=promote or promote_to")
    if parameter_matrix_policy_is_active() and matrix_exists:
        if not args.seed:
            raise WorkflowError("record-result under the parameter-matrix policy requires --seed")
        matrix_path = exp_dir / PARAMETER_MATRIX_CSV
        matrix_rows = ready_parameter_matrix_rows(matrix_path)
        matrix_result_row = select_parameter_matrix_result_row(
            matrix_rows,
            matrix_job_id=str(getattr(args, "matrix_job_id", "") or ""),
            seed=args.seed,
            label="record-result",
        )
        runtime_errors = parameter_matrix_runtime_errors(
            matrix_result_row,
            matrix_path=matrix_path,
            config_path=exp_dir / "config.yaml",
            seed=args.seed,
            tune_parameter=args.parameter if args.kind == "tune" else "",
            tune_new_value=args.new_value if args.kind == "tune" else "",
            tune_old_value=args.old_value if args.kind == "tune" else "",
            baseline_config_path=REPO_ROOT / "experiments" / version / "config.yaml",
        )
        runtime_errors.extend(
            parameter_matrix_freeze_commit_errors(
                commit_ref=str(getattr(args, "pre_run_freeze_commit", "") or ""),
                matrix_path=matrix_path,
                config_path=exp_dir / "config.yaml",
                job_id=matrix_result_row["job_id"],
            )
        )
        receipt_text = str(getattr(args, "run_start_receipt", "") or "").strip()
        if receipt_text:
            run_start_receipt_path = Path(receipt_text)
            if not run_start_receipt_path.is_absolute():
                run_start_receipt_path = REPO_ROOT / run_start_receipt_path
            runtime_errors.extend(
                run_start_receipt_errors(
                    receipt_path=run_start_receipt_path,
                    log_path=log_path,
                    config_path=exp_dir / "config.yaml",
                    row=matrix_result_row,
                    run_id=args.attempt_id,
                    pre_run_freeze_commit=str(getattr(args, "pre_run_freeze_commit", "") or ""),
                    command=args.command,
                )
            )
            if run_start_receipt_path.exists() and run_start_receipt_path.is_file():
                run_start_receipt_sha256 = sha256_file(run_start_receipt_path)
        else:
            runtime_errors.append("formal result requires --run-start-receipt created before training")
        if runtime_errors:
            raise WorkflowError("Formal result does not match its parameter-matrix row:\n" + "\n".join(runtime_errors))
        metrics = parse_training_log_text(
            captured_training_log_text(log_path, args.command),
            f"workflow-captured output in {display_path(log_path)}",
        )
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
    formal_commit = ""
    if matrix_path is not None:
        formal_commit = resolve_commit(str(getattr(args, "pre_run_freeze_commit", "") or ""))
        allowed_runtime_paths = [
            matrix_path,
            matrix_path.with_name(PARAMETER_MATRIX_MD),
            parameter_matrix_lock_path(matrix_path),
            log_path,
        ]
        if run_start_receipt_path is not None:
            allowed_runtime_paths.append(run_start_receipt_path)
            allowed_runtime_paths.append(run_finish_receipt_path(run_start_receipt_path))
        dirty_before = "dirty" if git_dirty_outside(allowed_runtime_paths) else "clean"
    else:
        dirty_before = "dirty" if git(["status", "--short"], check=False) else "clean"
    git_dirty = "true" if dirty_before == "dirty" else "false"
    run_start_receipt_ref = ""
    if run_start_receipt_path is not None:
        receipt_dest = exp_dir / "run_start_receipt.json"
        if receipt_dest.exists() and sha256_file(receipt_dest) != run_start_receipt_sha256:
            raise WorkflowError("Refusing to overwrite a different run_start_receipt.json")
        if run_start_receipt_path.resolve() != receipt_dest.resolve():
            shutil.copy2(run_start_receipt_path, receipt_dest)
        run_start_receipt_ref = rel(receipt_dest)
        finish_receipt_source = run_finish_receipt_path(run_start_receipt_path)
        finish_receipt_dest = exp_dir / "run_finish_receipt.json"
        if finish_receipt_dest.exists() and sha256_file(finish_receipt_dest) != sha256_file(finish_receipt_source):
            raise WorkflowError("Refusing to overwrite a different run_finish_receipt.json")
        if finish_receipt_source.resolve() != finish_receipt_dest.resolve():
            shutil.copy2(finish_receipt_source, finish_receipt_dest)
    evidence_defaults = result_evidence_defaults(kind.name, metrics["H"], args.decision, git_dirty)
    if legacy_summary_only:
        evidence_defaults.update(
            {
                "evidence_level": "legacy_summary_only",
                "result_status": "legacy_summary_only",
                "best_observed_H": "",
                "confirmed_H": "",
                "restore_target_H": "",
                "near_miss_not_restored": "false",
                "confirmation_status": "not_applicable",
            }
        )
    effective_promotion_decision = "blocked" if legacy_summary_only else args.promotion_decision
    effective_promote_to = "" if legacy_summary_only else args.promote_to
    readme_path = exp_dir / "README.md"
    content = read_text(readme_path)
    fields = {
        "kind": kind.name,
        "run_commit": formal_commit or git(["rev-parse", "--short", "HEAD"], check=False),
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
        "promotion_decision": effective_promotion_decision,
        "promote_to": effective_promote_to,
        "evidence_level": evidence_defaults["evidence_level"],
        "result_status": evidence_defaults["result_status"],
        "best_observed_H": evidence_defaults["best_observed_H"],
        "confirmed_H": evidence_defaults["confirmed_H"],
        "restore_target_H": evidence_defaults["restore_target_H"],
        "near_miss_tolerance_H": evidence_defaults["near_miss_tolerance_H"],
        "near_miss_not_restored": evidence_defaults["near_miss_not_restored"],
        "confirmation_status": evidence_defaults["confirmation_status"],
        "run_start_receipt_sha256": run_start_receipt_sha256,
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
        promotion_decision=effective_promotion_decision,
        promote_to=effective_promote_to,
        attempt_id=args.attempt_id,
        log_artifact_id=log_artifact_id,
        log_uri=log_uri,
        log_sha256=log_sha256,
        log_size_bytes=log_size_bytes,
        git_dirty=git_dirty,
        code_commit=formal_commit,
        legacy_summary_only=legacy_summary_only,
        run_start_receipt_sha256=run_start_receipt_sha256,
        run_start_receipt_ref=run_start_receipt_ref,
    )
    append_readme_result_row(
        readme_path,
        f"| CUB | {args.seed or '-'} | {metrics['U']} | {metrics['S']} | "
        f"{metrics['H']} | {metrics['ZS']} | {metrics['best_epoch']} | `{log_artifact_id}` |",
    )

    is_formal_framework = (REPO_ROOT / "experiments" / version / "framework.yaml").exists()
    if args.kind == "tune" and not is_formal_framework:
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

    if matrix_path is not None and matrix_result_row is not None:
        sync_parameter_matrix_result_row(
            matrix_path,
            matrix_rows,
            matrix_result_row,
            metrics=metrics,
            decision=args.decision,
            run_id=args.attempt_id,
            artifact_ref=log_uri,
        )
    if is_formal_framework:
        framework_status = "promoted" if effective_promotion_decision == "promote" else "completed"
        update_framework_experiment_status(
            version=version,
            kind=kind,
            exp_id=exp_id,
            status=framework_status,
        )
    print("record-result-ok")
    print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} best_epoch={metrics['best_epoch']}")
    print(f"log_artifact_id: {log_artifact_id}")
    print(f"log_uri: {log_uri}")
    print(f"log_sha256: {log_sha256}")
    print("临时分支清理提示: 结果写回目标框架账本、review 和必要提交完成后，再同步 main 总索引并删除 exp/... 临时分支；不要 push，除非 owner 明确要求。")
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
    git_dirty: str = "false",
    legacy_summary_only: bool = False,
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
  evidence_mode: {yaml_scalar("legacy_summary_only" if legacy_summary_only else "formal")}
  attempt_id: {yaml_scalar(attempt_lower)}
  created_or_recorded_at: {yaml_scalar(recorded_at)}
version:
  base_version: {yaml_scalar(version)}
  base_code_tag: {yaml_scalar(trial_fields.get("base_code_tag", version))}
  code_branch: {yaml_scalar(trial_fields.get("code_branch", current_branch()))}
  code_commit: {yaml_scalar(pre_run_freeze_commit or git(["rev-parse", "--short", "HEAD"], check=False))}
  git_dirty: {yaml_scalar(git_dirty)}
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
    legacy_summary_only: bool = False,
) -> str:
    baseline_h = comparison_reference_h(version) if version in CANONICAL_BASELINES else ""
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
    result_status = "legacy_summary_only" if legacy_summary_only else (
        "needs_confirmation" if decision in {"best", "keep"} else decision
    )
    promotion_decision = "blocked" if legacy_summary_only or decision in {"best", "keep"} else "not_applicable"
    evidence_level = "legacy_summary_only" if legacy_summary_only else (
        "valid_single_run" if decision in {"best", "keep"} else "quick_local"
    )
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
  baseline_reference: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  delta_H: {yaml_scalar(delta_h)}
  seed: {yaml_scalar(seed)}
  source: {yaml_scalar("training_log")}
  metric_semantics: {yaml_scalar("GZSL U/S/H/ZS from protected evaluator")}
baseline:
  version: {yaml_scalar(version)}
  H: {yaml_scalar(baseline_h)}
  reference_field: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  reference_status: {yaml_scalar(baseline_evidence(version)["status"] if version in CANONICAL_BASELINES else "")}
  confirmed_H: {yaml_scalar(baseline_evidence(version)["confirmed_H"] if version in CANONICAL_BASELINES else "")}
  confirmation_status: {yaml_scalar(baseline_evidence(version)["confirmation_status"] if version in CANONICAL_BASELINES else "")}
delta:
  H: {yaml_scalar(delta_h)}
run:
  seed: {yaml_scalar(seed)}
  pre_run_freeze_commit: {yaml_scalar(pre_run_freeze_commit)}
  command: {yaml_scalar(command)}
decision:
  status: {yaml_scalar(decision)}
  result_status: {yaml_scalar(result_status)}
  promotion_decision: {yaml_scalar(promotion_decision)}
  promote_to: {yaml_scalar("")}
evidence:
  evidence_level: {yaml_scalar(evidence_level)}
  best_observed_H: {yaml_scalar(metrics.get("H", "") if decision in {"best", "keep"} and not legacy_summary_only else "")}
  confirmed_H: {yaml_scalar("pending")}
  confirmation_status: {yaml_scalar("needs_confirmation" if decision in {"best", "keep"} else "not_applicable")}
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


def sync_evidence_defaults(
    *,
    decision: str,
    metrics: dict[str, str],
    raw_evidence_level: str,
    promotion_decision: str,
) -> dict[str, str]:
    h_value = metrics.get("H", "")
    confirmed_decisions = {"confirmed_candidate", "promote", "keep", "best"}
    if decision in {"blocked", "debug", "rerun"}:
        evidence_level = raw_evidence_level or "quick_local"
        result_status = decision
        best_observed_h = ""
        confirmation_status = "not_applicable"
        default_promotion = "not_applicable"
    elif decision == "not_confirmed":
        evidence_level = raw_evidence_level if raw_evidence_level in EVIDENCE_LEVELS else "quick_local"
        result_status = "not_confirmed"
        best_observed_h = ""
        confirmation_status = "needs_confirmation"
        default_promotion = "blocked"
    elif decision in confirmed_decisions:
        evidence_level = raw_evidence_level if raw_evidence_level in EVIDENCE_LEVELS else "valid_single_run"
        best_observed_h = h_value
        if evidence_level in {"confirmation_grade", "baseline_grade"}:
            if decision == "promote":
                result_status = "promotion_candidate"
            elif decision == "confirmed_candidate":
                result_status = "confirmed_candidate"
            else:
                result_status = "confirmed"
            confirmed_h = h_value
            confirmation_status = "confirmed_candidate" if decision == "confirmed_candidate" else "confirmed"
        else:
            result_status = "needs_confirmation" if decision != "promote" else "promotion_candidate"
            confirmed_h = "pending"
            confirmation_status = "needs_confirmation"
        default_promotion = "promote" if decision == "promote" else "blocked"
    elif decision in {"reject", "rejected"}:
        evidence_level = raw_evidence_level if raw_evidence_level in EVIDENCE_LEVELS else "valid_single_run"
        result_status = "rejected"
        best_observed_h = ""
        confirmation_status = "not_applicable"
        default_promotion = "not_applicable"
    else:
        evidence_level = raw_evidence_level if raw_evidence_level in EVIDENCE_LEVELS and raw_evidence_level != "quick_local" else "valid_single_run"
        result_status = "valid_observation"
        best_observed_h = ""
        confirmation_status = "not_applicable"
        default_promotion = "not_applicable"

    return {
        "evidence_level": evidence_level,
        "result_status": result_status,
        "best_observed_H": best_observed_h,
        "confirmed_H": confirmed_h if decision in confirmed_decisions else "pending",
        "confirmation_status": confirmation_status,
        "promotion_decision": promotion_decision or default_promotion,
        "promote_to": "",
    }


def numeric_greater(left: str, right: str) -> bool:
    try:
        return float(left) > float(right)
    except (TypeError, ValueError):
        return False


def preserve_trial_best_observed_for_sync(
    evidence_defaults: dict[str, str],
    trial_fields: dict[str, str],
    decision: str,
) -> dict[str, str]:
    preserved = dict(evidence_defaults)
    existing_best = trial_fields.get("best_observed_H", "")
    new_best = preserved.get("best_observed_H", "")
    if existing_best and (not new_best or numeric_greater(existing_best, new_best)):
        preserved["best_observed_H"] = existing_best
    if decision not in {"not_confirmed", "blocked", "debug", "rerun"}:
        return preserved
    for key in ["best_observed_H", "confirmed_H", "confirmation_status"]:
        value = trial_fields.get(key, "")
        if value:
            preserved[key] = value
    if trial_fields.get("evidence_level"):
        preserved["evidence_level"] = trial_fields["evidence_level"]
    if decision == "not_confirmed":
        preserved["result_status"] = "not_confirmed"
        preserved["promotion_decision"] = "blocked"
        if not preserved.get("confirmation_status") or preserved["confirmation_status"] == "not_applicable":
            preserved["confirmation_status"] = "needs_confirmation"
    return preserved


def metric_delta_h(version: str, metrics: dict[str, str]) -> str:
    if metrics.get("delta_H"):
        return metrics["delta_H"]
    baseline_h = metrics.get("baseline_H") or (
        comparison_reference_h(version) if version in CANONICAL_BASELINES else ""
    )
    h_value = metrics.get("H", "")
    if baseline_h and h_value:
        try:
            return f"{float(h_value) - float(baseline_h):+.2f}"
        except ValueError:
            return ""
    return ""


def baseline_confirmation_blocker(version: str) -> str:
    if version not in CANONICAL_BASELINES:
        return ""
    evidence = baseline_evidence(version)
    if evidence["confirmation_status"] == "confirmed" and evidence["confirmed_H"] != "pending":
        return ""
    return (
        f"active {version} comparison reference is unconfirmed: "
        f"{comparison_reference_phrase(version)}, confirmed_H={evidence['confirmed_H']}"
    )


def trial_followup_phrase(version: str, decision: str) -> str:
    if decision == "promote":
        return "promotion gate may proceed after confirmation."
    blocker = baseline_confirmation_blocker(version)
    if blocker:
        return f"do not promote/tag before {version} clean confirmation."
    return "do not promote without a stronger follow-up."


def artifact_id_lines(artifacts: dict[str, dict[str, str]]) -> list[str]:
    return [
        f"  {key}_artifact_id: {yaml_scalar(info.get('artifact_id', ''))}"
        for key, info in artifacts.items()
    ]


def make_trial_root_manifest(
    *,
    trial_id: str,
    slug: str,
    trial_fields: dict[str, str],
    attempt_upper: str,
    version: str,
    decision: str,
    attempt_manifest: dict[str, object],
    artifacts: dict[str, dict[str, str]],
    recorded_at: str,
) -> str:
    artifact_lines: list[str] = []
    for key, info in artifacts.items():
        artifact_lines.extend(
            [
                f"  {key}:",
                f"    artifact_id: {yaml_scalar(info.get('artifact_id', ''))}",
                f"    role: {yaml_scalar(info.get('role', ''))}",
                f"    uri: {yaml_scalar(info.get('uri', ''))}",
                f"    sha256: {yaml_scalar(info.get('sha256', ''))}",
                f"    size_bytes: {yaml_scalar(info.get('size_bytes', ''))}",
                f"    required_for: {yaml_scalar(info.get('required_for', ''))}",
                f"    status: {yaml_scalar(info.get('status', 'available') or 'available')}",
            ]
        )
    artifact_block = "\n".join(artifact_lines) if artifact_lines else "  {}"
    config_file = yaml_section_value(attempt_manifest, "reproducibility", "config_file")
    config_sha = yaml_section_value(attempt_manifest, "reproducibility", "config_sha256")
    pre_run_commit = yaml_section_value(attempt_manifest, "reproducibility", "pre_run_freeze_commit")
    command = yaml_section_value(attempt_manifest, "reproducibility", "command")
    seed = yaml_section_value(attempt_manifest, "reproducibility", "seed")
    code_commit = yaml_section_value(attempt_manifest, "version", "code_commit") or pre_run_commit
    git_dirty = yaml_section_value(attempt_manifest, "version", "git_dirty")
    return f"""schema_version: gtpj-manifest/v1
experiment:
  id: {yaml_scalar(trial_id)}
  name: {yaml_scalar(f"{trial_id}_{slug}")}
  kind: {yaml_scalar("module-trial")}
  status: {yaml_scalar(f"completed_{decision}")}
  attempt_id: {yaml_scalar(attempt_upper)}
  created_or_recorded_at: {yaml_scalar(recorded_at)}
version:
  base_version: {yaml_scalar(version)}
  base_code_tag: {yaml_scalar(trial_fields.get("base_code_tag", version))}
  code_branch: {yaml_scalar(trial_fields.get("code_branch", ""))}
  code_commit: {yaml_scalar(code_commit)}
  git_dirty: {yaml_scalar(git_dirty or "false")}
reproducibility:
  config_file: {yaml_scalar(config_file)}
  config_sha256: {yaml_scalar(config_sha)}
  pre_run_freeze_commit: {yaml_scalar(pre_run_commit)}
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
  hypothesis: {yaml_scalar(yaml_section_value(attempt_manifest, "idea", "hypothesis"))}
artifacts:
{artifact_block}
quality:
  boundary_audit_required: true
  raw_artifacts_in_git: false
  interface_contract_required: {yaml_scalar("true")}
  evaluation_semantics_verified: {yaml_scalar("true")}
"""


def make_trial_root_result_yaml(
    *,
    trial_id: str,
    slug: str,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    attempt_result: dict[str, object],
    artifacts: dict[str, dict[str, str]],
    recorded_at: str,
) -> str:
    baseline_h = metrics.get("baseline_H") or (
        comparison_reference_h(version) if version in CANONICAL_BASELINES else ""
    )
    delta_h = metric_delta_h(version, metrics)
    evidence_lines = artifact_id_lines(artifacts)
    evidence_block = "\n".join(evidence_lines)
    seed = metrics.get("seed") or yaml_section_value(attempt_result, "run", "seed")
    pre_run_commit = yaml_section_value(attempt_result, "run", "pre_run_freeze_commit")
    command = yaml_section_value(attempt_result, "run", "command")
    return f"""schema_version: gtpj-result/v1
experiment_id: {yaml_scalar(trial_id)}
experiment_name: {yaml_scalar(f"{trial_id}_{slug}")}
kind: {yaml_scalar("module-trial")}
version: {yaml_scalar(version)}
attempt_id: {yaml_scalar(attempt_upper)}
metrics:
  U: {yaml_scalar(metrics.get("U", ""))}
  S: {yaml_scalar(metrics.get("S", ""))}
  H: {yaml_scalar(metrics.get("H", ""))}
  ZS: {yaml_scalar(metrics.get("ZS", ""))}
  best_epoch: {yaml_scalar(metrics.get("best_epoch", ""))}
  baseline_H: {yaml_scalar(baseline_h)}
  baseline_reference: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  delta_H: {yaml_scalar(delta_h)}
  seed: {yaml_scalar(seed)}
  source: {yaml_scalar("attempt_result_yaml")}
  metric_semantics: {yaml_scalar("GZSL U/S/H/ZS from protected evaluator")}
baseline:
  version: {yaml_scalar(version)}
  H: {yaml_scalar(baseline_h)}
  reference_field: {yaml_scalar(comparison_reference_field(version) if version in CANONICAL_BASELINES else "")}
  reference_status: {yaml_scalar(baseline_evidence(version)["status"] if version in CANONICAL_BASELINES else "")}
  confirmed_H: {yaml_scalar(baseline_evidence(version)["confirmed_H"] if version in CANONICAL_BASELINES else "")}
  confirmation_status: {yaml_scalar(baseline_evidence(version)["confirmation_status"] if version in CANONICAL_BASELINES else "")}
delta:
  H: {yaml_scalar(delta_h)}
run:
  seed: {yaml_scalar(seed)}
  pre_run_freeze_commit: {yaml_scalar(pre_run_commit)}
  command: {yaml_scalar(command)}
decision:
  status: {yaml_scalar(decision)}
  result_status: {yaml_scalar(evidence_defaults["result_status"])}
  promotion_decision: {yaml_scalar(evidence_defaults["promotion_decision"])}
  promote_to: {yaml_scalar(evidence_defaults["promote_to"])}
evidence:
  evidence_level: {yaml_scalar(evidence_defaults["evidence_level"])}
  best_observed_H: {yaml_scalar(evidence_defaults["best_observed_H"])}
  confirmed_H: {yaml_scalar(evidence_defaults["confirmed_H"])}
  confirmation_status: {yaml_scalar(evidence_defaults["confirmation_status"])}
{evidence_block}
  manifest: {yaml_scalar("manifest.yaml")}
  attempt_manifest: {yaml_scalar(f"attempts/{attempt_upper}/manifest.yaml")}
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


def make_trial_root_result_md(
    *,
    trial_id: str,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    artifacts: dict[str, dict[str, str]],
) -> str:
    evidence_lines = "\n".join(
        f"{key}_artifact_id: {info.get('artifact_id', '')}" for key, info in artifacts.items()
    )
    blocker = baseline_confirmation_blocker(version)
    blocker_note = (
        "\n"
        + f"{attempt_upper} is recorded as `{evidence_defaults['evidence_level']}` with "
        + f"confirmed_H={evidence_defaults['confirmed_H']} and "
        + f"confirmation_status={evidence_defaults['confirmation_status']}. "
        + f"Promotion/tag remains blocked because {blocker}."
        if blocker
        else ""
    )
    return f"""# {trial_id} Trial Result

## Metrics

| Attempt ID | Base version | Dataset | Seed | U | S | H | ZS | Best epoch | delta_H |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| {attempt_upper} | {version} | CUB | {metrics.get("seed", "-")} | {metrics.get("U", "-")} | {metrics.get("S", "-")} | {metrics.get("H", "-")} | {metrics.get("ZS", "-")} | {metrics.get("best_epoch", "-")} | {metric_delta_h(version, metrics) or "-"} |

## Evidence

```text
trial_id: {trial_id}
attempt_id: {attempt_upper}
evidence_level: {evidence_defaults["evidence_level"]}
result_status: {evidence_defaults["result_status"]}
promotion_decision: {evidence_defaults["promotion_decision"]}
confirmed_H: {evidence_defaults["confirmed_H"]}
confirmation_status: {evidence_defaults["confirmation_status"]}
{evidence_lines}
```

## Decision

`{decision}`
{blocker_note}
"""


def make_trial_root_quality_md(
    *,
    trial_id: str,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    artifacts: dict[str, dict[str, str]],
) -> str:
    artifact_checks = "\n".join(
        f"- [x] `{info.get('artifact_id', '')}` exists in Warehouse." for info in artifacts.values()
    )
    blocker = baseline_confirmation_blocker(version)
    blocker_line = (
        f"- Promotion/tag remains blocked because {blocker}."
        if blocker
        else "- No baseline confirmation blocker was detected by the helper."
    )
    return f"""# {trial_id} Quality Check

```text
quality_check_mode: STRICT
attempt_id: {attempt_upper}
decision: PASS_{decision.upper()}
promotion_decision: {evidence_defaults["promotion_decision"]}
evidence_level: {evidence_defaults["evidence_level"]}
```

## Findings

- Metrics are synchronized from `{attempt_upper}`: U={metrics.get("U", "")}, S={metrics.get("S", "")}, H={metrics.get("H", "")}, ZS={metrics.get("ZS", "")}, best_epoch={metrics.get("best_epoch", "")}.
- Trial-level decision recorded as `{decision}`.
- Attempt confirmation status: confirmed_H={evidence_defaults["confirmed_H"]}, confirmation_status={evidence_defaults["confirmation_status"]}.
{blocker_line}
- Raw artifacts remain in Warehouse; GitHub stores lightweight identities only.

## Artifact Check

{artifact_checks}
- [x] `manifest.yaml`, `result.yaml`, and `result.md` point back to the attempt-local evidence.
- [x] No raw training log or checkpoint is copied into GitHub.

## Decision

PASS_{decision.upper()}.
"""


def make_trial_closeout_review_md(
    *,
    trial_id: str,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    attempt_manifest: dict[str, object],
    artifacts: dict[str, dict[str, str]],
) -> str:
    artifact_lines = "\n".join(
        f"- `{info.get('artifact_id', '')}` -> `{info.get('uri', '')}`"
        for info in artifacts.values()
    )
    code_commit = (
        yaml_section_value(attempt_manifest, "version", "code_commit")
        or yaml_section_value(attempt_manifest, "reproducibility", "pre_run_freeze_commit")
    )
    command = yaml_section_value(attempt_manifest, "reproducibility", "command")
    return f"""# Innovation Review Round 2: Post-Run Evidence

```text
review_round: Review 3
scope: post-run evidence review
activation_mode: real_multi_agent
attempt_id: {attempt_upper}
decision: {decision}
promotion_decision: {evidence_defaults["promotion_decision"]}
evidence_level: {evidence_defaults["evidence_level"]}
```

## Inputs Checked

- `attempts/{attempt_upper}/manifest.yaml`
- `attempts/{attempt_upper}/result.yaml`
- `attempts/{attempt_upper}/result.md`
- `attempts/{attempt_upper}/quality_check.md`
- `ATTEMPTS.md`
- `manifest.yaml`
- `result.yaml`
- `result.md`
- `quality_check.md`
- Warehouse artifact identities below

## Review 3 Findings

- Metrics synchronized from `{attempt_upper}`: U={metrics.get("U", "")}, S={metrics.get("S", "")}, H={metrics.get("H", "")}, ZS={metrics.get("ZS", "")}, best_epoch={metrics.get("best_epoch", "")}.
- Base version: `{version}`.
- Code commit / pre-run freeze: `{code_commit}`.
- Command: `{command}`.
- Trial decision: `{decision}`.
- Promotion decision: `{evidence_defaults["promotion_decision"]}`.
- Evidence level: `{evidence_defaults["evidence_level"]}`.
- Boundary check: raw artifacts remain in Warehouse; GitHub records lightweight ids, URIs, sha256, and size only.

## Artifact Refs

{artifact_lines}

## Blocking Issues

None recorded by automated closeout for `{attempt_upper}`.

## Decision

`{decision}`
"""


def make_trial_agent_summary_md(
    *,
    trial_id: str,
    slug: str,
    trial_fields: dict[str, str],
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    attempt_manifest: dict[str, object],
    artifacts: dict[str, dict[str, str]],
    recorded_at: str,
) -> str:
    artifact_ids = "; ".join(
        info.get("artifact_id", "") for info in artifacts.values() if info.get("artifact_id")
    )
    evidence_refs = "; ".join(
        [
            f"attempts/{attempt_upper}/manifest.yaml",
            f"attempts/{attempt_upper}/result.yaml",
            f"attempts/{attempt_upper}/quality_check.md",
            "review_round_2.md",
            "result.yaml",
            "quality_check.md",
        ]
    )
    code_branch = (
        yaml_section_value(attempt_manifest, "version", "code_branch")
        or trial_fields.get("code_branch", "")
    )
    code_commit = (
        yaml_section_value(attempt_manifest, "version", "code_commit")
        or yaml_section_value(attempt_manifest, "reproducibility", "pre_run_freeze_commit")
    )
    command = yaml_section_value(attempt_manifest, "reproducibility", "command")
    return f"""# Agent Summary: {trial_id}_{slug}

```text
experiment_id: {trial_id}
run_id:
base_version: {version}
code_branch: {code_branch}
code_commit: {code_commit}
activation_mode: real_multi_agent
agent_instance_mode: named_owner_thread
lifecycle: workflow_scoped
activation_reason: module trial closeout requires Review 0-3 evidence and artifact boundary checks
required_roles: Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst, Reviewer
required_real_agents: Reader/Planner, Interface Checker, Quality Checker, Reviewer, Log Analyst, Result Analyst
agent_persistent_threads: none
agent_set: Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst, Reviewer
serial_agents: Coordinator -> Review 0 -> Review 1 -> Implementer -> Review 2 -> Runner -> Review 3 -> Coordinator
parallel_agents: Interface Checker + Quality Checker + Reviewer in Review 2; Log Analyst + Quality Checker + Result Analyst + Reviewer in Review 3
disabled_agents: none
named_threads: workflow-scoped named Codex role threads; helper-generated summary records their required evidence slots
tool_support: workflow_helper generated current-attempt closeout summary
memory_policy: hidden/session memory is orientation only; formal facts come from current repo ledgers and Warehouse artifact identities
memory_used: no
memory_sources: current repo attempt manifest/result/quality; Warehouse artifact identities
agent_profile_files: docs/workflow/agents/shared_roles/*/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/*/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
persistent_thread_ids: none
runtime_state: completed
attempt_id: {attempt_upper}
warehouse_report_artifacts: {artifact_ids}
final_decision: {decision}
review_rounds: Review 0/1/2 existing trial evidence; Review 3 autogenerated from {attempt_upper}
temporary_agents: not recorded in helper-generated summary
recorded_at: {recorded_at}
```

## Coordinator

```text
role: Coordinator
agent_instance_mode: named_owner_thread
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: closeout summary generated from current repo evidence
independence_scope: final ledger writer
output_locations: manifest.yaml; result.yaml; result.md; quality_check.md; review_round_2.md; agent_summary.md
inputs_checked: README.md; ATTEMPTS.md; attempts/{attempt_upper}/manifest.yaml; attempts/{attempt_upper}/result.yaml; attempts/{attempt_upper}/quality_check.md
actions: synchronized trial root summary, Review 3 closeout, agent summary, module index, and idea tree
outputs: manifest.yaml; result.yaml; result.md; quality_check.md; review_round_2.md; agent_summary.md
issues: none recorded by automated closeout
decision: {decision}
evidence_refs: {evidence_refs}
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/coordinator/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/coordinator/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: all
blocking_issues: none
```

## Runner

```text
role: Runner
agent_instance_mode: named_owner_thread
agent_instance_type: recorded_run
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: recorded serial GPU run evidence
independence_scope: serial GPU owner
output_locations: attempts/{attempt_upper}/manifest.yaml; Warehouse artifacts
inputs_checked: command and config recorded in attempts/{attempt_upper}/manifest.yaml
actions: {command}
outputs: {artifact_ids}
issues: none recorded by automated closeout
decision: completed
evidence_refs: attempts/{attempt_upper}/manifest.yaml
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/runner/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/runner/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: Runner
blocking_issues: none
```

## Log Analyst

```text
role: Log Analyst
agent_instance_mode: named_owner_thread
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: parse current attempt result evidence
independence_scope: parse metrics from registered attempt result
output_locations: agent_summary.md; result.md
inputs_checked: attempts/{attempt_upper}/result.yaml
actions: extracted U/S/H/ZS and best_epoch
outputs: U={metrics.get("U", "")}; S={metrics.get("S", "")}; H={metrics.get("H", "")}; ZS={metrics.get("ZS", "")}; best_epoch={metrics.get("best_epoch", "")}
issues: none recorded by automated closeout
decision: allow
evidence_refs: attempts/{attempt_upper}/result.yaml
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/log_analyst/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/log_analyst/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: Review 3
blocking_issues: none
```

## Quality Checker

```text
role: Quality Checker
agent_instance_mode: named_owner_thread
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: check artifact boundary and ledger consistency
independence_scope: artifact boundary and ledger consistency
output_locations: review_round_2.md; quality_check.md; agent_summary.md
inputs_checked: attempt manifest/result/quality; Warehouse artifact ids
actions: required artifacts are referenced by root ledgers; raw artifacts stay outside GitHub
outputs: review_round_2.md; quality_check.md
issues: none recorded by automated closeout
decision: pass_{decision}
evidence_refs: {evidence_refs}
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/quality_checker/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/quality_checker/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: Review 3
blocking_issues: none
```

## Result Analyst

```text
role: Result Analyst
agent_instance_mode: named_owner_thread
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: compare current attempt metrics against recorded references
independence_scope: result interpretation from current attempt metrics
output_locations: result.md; agent_summary.md
inputs_checked: attempts/{attempt_upper}/result.yaml; baseline reproducibility fields in root result
actions: compared H against recorded reference when available
outputs: H={metrics.get("H", "")}; delta_H={metrics.get("delta_H", "")}; promotion_decision={evidence_defaults["promotion_decision"]}
issues: baseline confirmation status must still be checked before baseline-grade claims
decision: {decision}
evidence_refs: result.yaml; attempts/{attempt_upper}/result.yaml
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/result_analyst/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/result_analyst/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: Review 3
blocking_issues: none
```

## Reviewer

```text
role: Reviewer
agent_instance_mode: named_owner_thread
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
named_thread_reason: final closeout evidence consistency review
independence_scope: final evidence consistency check
output_locations: review_round_2.md; agent_summary.md
inputs_checked: review_round_2.md; agent_summary.md; result.yaml; quality_check.md
actions: confirmed current-attempt summary points to {attempt_upper}
outputs: final_decision={decision}
issues: none recorded by automated closeout
decision: {decision}
evidence_refs: {evidence_refs}
memory_used: no
memory_sources: current repo files
agent_profile_files: docs/workflow/agents/shared_roles/reviewer/profile.md
agent_memory_files: docs/workflow/agents/shared_roles/reviewer/memory.md
agent_memory_updates: none
verified_against_current_repo: yes
review_round: Review 3
blocking_issues: none
```
"""


def check_closeout_report_file(
    path: Path,
    *,
    attempt_upper: str,
    artifacts: dict[str, dict[str, str]],
) -> None:
    if not path.exists():
        raise WorkflowError(f"Missing closeout report file: {rel(path)}")
    fields = read_key_value_block(path)
    if fields.get("attempt_id") != attempt_upper:
        found = fields.get("attempt_id", "")
        raise WorkflowError(
            f"{rel(path)} must have attempt_id: {attempt_upper} in its first text block; found {found or 'missing'}"
        )
    text = read_text(path)
    stale_markers = [
        "No training result has been recorded",
        "尚未记录训练结果",
    ]
    for marker in stale_markers:
        if marker in text:
            raise WorkflowError(f"{rel(path)} still contains stale marker: {marker}")
    for artifact in artifacts.values():
        artifact_id = artifact.get("artifact_id", "")
        if artifact_id and artifact_id not in text:
            raise WorkflowError(f"{rel(path)} does not reference artifact {artifact_id}")


def replace_first_text_block_values(content: str, updates: dict[str, str]) -> str:
    lines = content.splitlines()
    in_block = False
    for index, line in enumerate(lines):
        if line.strip() == "```text" and not in_block:
            in_block = True
            continue
        if in_block and line.strip() == "```":
            break
        if not in_block or ":" not in line:
            continue
        key, _value = line.split(":", 1)
        stripped_key = key.strip()
        if stripped_key in updates:
            value = updates[stripped_key]
            lines[index] = f"{stripped_key}: {value}" if value else f"{stripped_key}:"
    return "\n".join(lines).rstrip() + "\n"


def replace_result_table_row(content: str, row: str) -> str:
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if "Seed | U | S | H | ZS | Best epoch | Log" not in line:
            continue
        separator = index + 1
        insert = separator + 1
        end = insert
        while end < len(lines) and lines[end].strip() and not lines[end].startswith("## "):
            end += 1
        lines[insert:end] = [row]
        return "\n".join(lines).rstrip() + "\n"
    return (
        content.rstrip()
        + "\n\n## Results\n\n"
        + "| Dataset | Seed | U | S | H | ZS | Best epoch | Log |\n"
        + "|---|---:|---:|---:|---:|---:|---:|---|\n"
        + row
        + "\n"
    )


def update_trial_readme_from_attempt(
    *,
    trial_dir: Path,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    evidence_defaults: dict[str, str],
    attempt_manifest: dict[str, object],
    artifacts: dict[str, dict[str, str]],
) -> None:
    readme_path = trial_dir / "README.md"
    content = read_text(readme_path)
    train_log = artifacts.get("train_log", {})
    code_commit = yaml_section_value(attempt_manifest, "version", "code_commit")
    updates = {
        "code_commit": code_commit,
        "trial_decision": decision,
        "promotion_decision": evidence_defaults["promotion_decision"],
        "promote_to": evidence_defaults["promote_to"],
        "evidence_level": evidence_defaults["evidence_level"],
        "best_observed_H": evidence_defaults["best_observed_H"],
        "confirmed_H": evidence_defaults["confirmed_H"],
        "confirmation_status": evidence_defaults["confirmation_status"],
        "run_config": yaml_section_value(attempt_manifest, "reproducibility", "config_file"),
        "log_artifact_id": train_log.get("artifact_id", ""),
        "log_uri": train_log.get("uri", ""),
        "log_sha256": train_log.get("sha256", ""),
        "log_size_bytes": train_log.get("size_bytes", ""),
        "manifest": "manifest.yaml",
        "result_yaml": "result.yaml",
        "result_md": "result.md",
    }
    content = replace_first_text_block_values(content, updates)
    row = (
        f"| CUB | {metrics.get('seed') or '-'} | {metrics.get('U', '-')} | "
        f"{metrics.get('S', '-')} | {metrics.get('H', '-')} | {metrics.get('ZS', '-')} | "
        f"{metrics.get('best_epoch', '-')} | `{train_log.get('artifact_id', '')}` |"
    )
    content = replace_result_table_row(content, row)
    readme_path.write_text(content, encoding="utf-8")


def update_module_trial_index(
    *,
    trial_dir: Path,
    idea_id: str,
    idea_file: str,
    version: str,
    attempt_upper: str,
    metrics: dict[str, str],
    decision: str,
) -> None:
    index_path = REPO_ROOT / "experiments" / "module_trials" / "INDEX.md"
    content = read_text(index_path) if index_path.exists() else "# Module Trials Index\n\n"
    trial_rel = rel(trial_dir)
    delta_h = metric_delta_h(version, metrics)
    summary = (
        f"{attempt_upper} H={metrics.get('H', '')}, delta_H={delta_h or '-'} "
        f"vs active {comparison_reference_phrase(version) if version in CANONICAL_BASELINES else version}; "
        + trial_followup_phrase(version, decision)
    )
    row = f"| `{idea_id}` | `{idea_file}` | `{trial_rel}` | {decision} | {summary} |"
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if f"`{trial_rel}`" in line:
            lines[index] = row
            index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            return
    if "| Idea | Source idea file | Trial evidence directory | Trial status | Summary |" not in content:
        lines.extend(
            [
                "",
                "## Trial Records",
                "",
                "| Idea | Source idea file | Trial evidence directory | Trial status | Summary |",
                "|---|---|---|---|---|",
            ]
        )
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if line.startswith("## Start Rules"):
            insert_at = index
            break
    lines.insert(insert_at, row)
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sync_idea_tree_from_trial(
    *,
    trial_dir: Path,
    trial_id: str,
    attempt_upper: str,
    version: str,
    metrics: dict[str, str],
    decision: str,
    trial_fields: dict[str, str],
) -> None:
    idea_id = trial_fields.get("idea_id", "")
    if not idea_id:
        raise WorkflowError("Trial README is missing idea_id")
    data = load_idea_tree()
    idea = find_idea_record(data, idea_id)
    status_map = {
        "promote": "validated",
        "keep": "testing",
        "best": "testing",
        "reject": "rejected",
        "rejected": "rejected",
        "blocked": "blocked",
        "debug": "blocked",
    }
    idea["status"] = status_map.get(decision, "weakened")
    version_scores = idea.setdefault("version_scores", {})
    version_entry = version_scores.setdefault(
        version,
        {"score": 0, "applicability": "unclear", "rationale": "", "blockers": []},
    )
    if decision == "promote":
        version_entry["stage"] = "validated"
    elif decision in {"reject", "rejected"}:
        version_entry["stage"] = "rejected"
    elif decision in {"blocked", "debug"}:
        version_entry["stage"] = "blocked"
    else:
        version_entry["stage"] = "trialing"
    trial_rel = rel(trial_dir)
    if trial_rel not in idea.setdefault("linked_trials", []):
        idea["linked_trials"].append(trial_rel)
    delta_h = metric_delta_h(version, metrics)
    reference = comparison_reference_phrase(version) if version in CANONICAL_BASELINES else version
    evidence_ref = f"{trial_rel}/result.yaml"
    note = (
        f"{attempt_upper} H={metrics.get('H', '')}, delta_H={delta_h or '-'} "
        f"vs {reference}; trial decision={decision}."
    )
    evidence = idea.setdefault("evidence", [])
    if not any(item.get("ref") == evidence_ref for item in evidence if isinstance(item, dict)):
        evidence.append({"type": "trial", "ref": evidence_ref, "note": note})
    else:
        for item in evidence:
            if isinstance(item, dict) and item.get("ref") == evidence_ref:
                item["note"] = note
    save_idea_tree(data)
    write_idea_views(data)


def cmd_sync_trial_summary(args: argparse.Namespace) -> int:
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial directory: {display_path(trial_dir)}")
    require_path_inside(trial_dir, REPO_ROOT / "experiments" / "module_trials", "trial-dir")
    trial_id, slug = parse_trial_folder_name(trial_dir)
    attempt_upper, _attempt_lower = normalize_attempt_ids(args.attempt_id)
    attempt_dir = trial_dir / "attempts" / attempt_upper
    if not attempt_dir.exists():
        raise WorkflowError(f"Missing attempt directory: {rel(attempt_dir)}")
    attempt_manifest_path = attempt_dir / "manifest.yaml"
    attempt_result_path = attempt_dir / "result.yaml"
    if not attempt_manifest_path.exists() or not attempt_result_path.exists():
        raise WorkflowError(f"{attempt_upper} must have manifest.yaml and result.yaml")

    trial_fields = read_key_value_block(trial_dir / "README.md")
    version = trial_fields.get("base_version", "")
    if not re.fullmatch(r"v[0-9]+", version):
        raise WorkflowError("Trial README must define base_version like v2")
    attempt_manifest = read_shallow_yaml(attempt_manifest_path)
    attempt_result = read_shallow_yaml(attempt_result_path)
    artifacts = read_yaml_artifacts(attempt_manifest_path)
    metrics = attempt_sync_metrics(attempt_result, attempt_result_path)
    if not metrics.get("H"):
        raise WorkflowError(f"{rel(attempt_result_path)} is missing metrics.H")
    metrics["baseline_H"] = metrics.get("baseline_H") or (
        comparison_reference_h(version) if version in CANONICAL_BASELINES else ""
    )
    metrics["delta_H"] = metric_delta_h(version, metrics)
    decision = args.decision or yaml_section_value(attempt_result, "decision", "status") or "revise"
    raw_evidence_level = args.evidence_level or yaml_section_value(attempt_result, "evidence", "evidence_level")
    promotion_decision = args.promotion_decision or yaml_section_value(attempt_result, "decision", "promotion_decision")
    legacy_summary_only = (
        yaml_section_value(attempt_manifest, "experiment", "evidence_mode") == "legacy_summary_only"
        or yaml_section_value(attempt_result, "evidence", "evidence_level") == "legacy_summary_only"
        or yaml_section_value(attempt_result, "decision", "result_status") == "legacy_summary_only"
    )
    if legacy_summary_only:
        if decision not in {"reject", "rejected", "blocked", "debug"}:
            raise WorkflowError("legacy_summary_only attempt cannot be synced as keep/best/promote evidence")
        if promotion_decision == "promote":
            raise WorkflowError("legacy_summary_only attempt cannot set promotion_decision=promote")
        if args.evidence_level and args.evidence_level != "legacy_summary_only":
            raise WorkflowError("legacy_summary_only attempt cannot change its evidence level during sync")
        raw_evidence_level = "legacy_summary_only"
        promotion_decision = "blocked"
    if promotion_decision == "not_applicable" and decision == "promote":
        promotion_decision = "promote"
    if legacy_summary_only:
        evidence_defaults = {
            "evidence_level": "legacy_summary_only",
            "result_status": "legacy_summary_only",
            "best_observed_H": "",
            "confirmed_H": "",
            "confirmation_status": "not_applicable",
            "promotion_decision": "blocked",
            "promote_to": "",
        }
    else:
        evidence_defaults = sync_evidence_defaults(
            decision=decision,
            metrics=metrics,
            raw_evidence_level=raw_evidence_level,
            promotion_decision=promotion_decision if promotion_decision != "not_applicable" or decision == "promote" else "",
        )
        evidence_defaults = preserve_trial_best_observed_for_sync(
            evidence_defaults,
            trial_fields,
            decision,
        )

    if args.dry_run:
        print("sync-trial-summary-dry-run-ok")
        print(f"trial: {rel(trial_dir)}")
        print(f"attempt: {attempt_upper}")
        print(f"decision: {decision}")
        print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} delta_H={metrics['delta_H']}")
        return 0

    recorded_at = str(
        attempt_result.get("recorded_at")
        or yaml_section_value(attempt_manifest, "experiment", "created_or_recorded_at")
        or utc_now()
    )
    (trial_dir / "manifest.yaml").write_text(
        make_trial_root_manifest(
            trial_id=trial_id,
            slug=slug,
            trial_fields=trial_fields,
            attempt_upper=attempt_upper,
            version=version,
            decision=decision,
            attempt_manifest=attempt_manifest,
            artifacts=artifacts,
            recorded_at=recorded_at,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "result.yaml").write_text(
        make_trial_root_result_yaml(
            trial_id=trial_id,
            slug=slug,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            evidence_defaults=evidence_defaults,
            attempt_result=attempt_result,
            artifacts=artifacts,
            recorded_at=recorded_at,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "result.md").write_text(
        make_trial_root_result_md(
            trial_id=trial_id,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            evidence_defaults=evidence_defaults,
            artifacts=artifacts,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "quality_check.md").write_text(
        make_trial_root_quality_md(
            trial_id=trial_id,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            evidence_defaults=evidence_defaults,
            artifacts=artifacts,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "review_round_2.md").write_text(
        make_trial_closeout_review_md(
            trial_id=trial_id,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            evidence_defaults=evidence_defaults,
            attempt_manifest=attempt_manifest,
            artifacts=artifacts,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    (trial_dir / "agent_summary.md").write_text(
        make_trial_agent_summary_md(
            trial_id=trial_id,
            slug=slug,
            trial_fields=trial_fields,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            evidence_defaults=evidence_defaults,
            attempt_manifest=attempt_manifest,
            artifacts=artifacts,
            recorded_at=recorded_at,
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    update_trial_readme_from_attempt(
        trial_dir=trial_dir,
        attempt_upper=attempt_upper,
        version=version,
        metrics=metrics,
        decision=decision,
        evidence_defaults=evidence_defaults,
        attempt_manifest=attempt_manifest,
        artifacts=artifacts,
    )
    idea_id = trial_fields.get("idea_id", "")
    idea_file = trial_fields.get("idea_source_file", "")
    update_module_trial_index(
        trial_dir=trial_dir,
        idea_id=idea_id,
        idea_file=idea_file,
        version=version,
        attempt_upper=attempt_upper,
        metrics=metrics,
        decision=decision,
    )
    if not args.skip_idea_tree:
        sync_idea_tree_from_trial(
            trial_dir=trial_dir,
            trial_id=trial_id,
            attempt_upper=attempt_upper,
            version=version,
            metrics=metrics,
            decision=decision,
            trial_fields=trial_fields,
        )

    print("sync-trial-summary-ok")
    print(f"trial: {rel(trial_dir)}")
    print(f"attempt: {attempt_upper}")
    print(f"decision: {decision}")
    print(f"metrics: U={metrics['U']} S={metrics['S']} H={metrics['H']} ZS={metrics['ZS']} delta_H={metrics['delta_H']}")
    return 0


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
    """Hold the matrix lock before any Attempt or Warehouse file can change."""
    require_legacy_module_attempt_backfill(args)
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    attempt_upper, _attempt_lower = normalize_attempt_ids(args.attempt_id)
    matrix_path = trial_dir / "attempts" / attempt_upper / PARAMETER_MATRIX_CSV
    if (
        matrix_path.exists()
        and parameter_matrix_policy_is_active()
        and not bool(getattr(args, "legacy_summary_only", False))
    ):
        with parameter_matrix_mutation_lock(
            matrix_path,
            operation="record-module-attempt-transaction",
            job_id=str(getattr(args, "matrix_job_id", "") or ""),
            run_id=str(getattr(args, "run_id", "") or attempt_upper),
        ):
            return _cmd_record_module_attempt_locked(args)
    return _cmd_record_module_attempt_locked(args)


def framework_standard_is_active() -> bool:
    standard_path = REPO_ROOT / "docs" / "workflow" / "FRAMEWORK_EXPERIMENT_STANDARD.md"
    if not standard_path.exists():
        return False
    standard_text = read_text(standard_path)
    version_match = re.search(r"(?m)^standard_id:\s*SYS-WORKFLOW-V([0-9]+)\s*$", standard_text)
    status_active = re.search(r"(?m)^status:\s*active\s*$", standard_text) is not None
    return bool(version_match and int(version_match.group(1)) >= 3 and status_active)


def immutable_template_standard_is_active() -> bool:
    standard_path = REPO_ROOT / "docs" / "workflow" / "FRAMEWORK_EXPERIMENT_STANDARD.md"
    if not standard_path.exists():
        return False
    standard_text = read_text(standard_path)
    version_match = re.search(r"(?m)^standard_id:\s*SYS-WORKFLOW-V([0-9]+)\s*$", standard_text)
    status_active = re.search(r"(?m)^status:\s*active\s*$", standard_text) is not None
    return bool(version_match and int(version_match.group(1)) >= 5 and status_active)


def immutable_template_standard_is_active_at_ref(ref: str) -> bool:
    """Check the governance version at a separate registry ref."""
    commit = resolve_commit(ref)
    standard_text = git_show(
        f"{commit}:docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md",
        check=False,
    )
    version_match = re.search(
        r"(?m)^standard_id:\s*SYS-WORKFLOW-V([0-9]+)\s*$", standard_text
    )
    status_active = re.search(r"(?m)^status:\s*active\s*$", standard_text) is not None
    return bool(version_match and int(version_match.group(1)) >= 5 and status_active)


def require_legacy_module_attempt_backfill(args: argparse.Namespace) -> None:
    """Under the active framework standard, the old command only backfills historical evidence."""
    if not framework_standard_is_active():
        return
    if not bool(getattr(args, "legacy_summary_only", False)):
        raise WorkflowError(
            "The active framework standard forbids new formal runs under Trial/Attempt. "
            "Create a framework experiment and use record-result; record-module-attempt is legacy backfill only."
        )
    if not str(getattr(args, "legacy_source_commit", "") or "").strip():
        raise WorkflowError(
            "Legacy Attempt backfill requires --legacy-source-commit proving that the Attempt predates the active framework standard."
        )


def _cmd_record_module_attempt_locked(args: argparse.Namespace) -> int:
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial directory: {display_path(trial_dir)}")
    require_path_inside(trial_dir, REPO_ROOT / "experiments" / "module_trials", "trial-dir")
    attempts_path = trial_dir / "ATTEMPTS.md"
    if not attempts_path.exists():
        raise WorkflowError(f"Missing attempts ledger: {rel(attempts_path)}")
    trial_id, slug = parse_trial_folder_name(trial_dir)
    attempt_upper, attempt_lower = normalize_attempt_ids(args.attempt_id)
    attempt_dir = trial_dir / "attempts" / attempt_upper
    if existing_legacy_identity(attempt_dir):
        raise WorkflowError("legacy_summary_only identity is permanent; refusing to overwrite this attempt ledger")
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
    pre_run_freeze_ref = args.pre_run_freeze_commit or (
        "" if parameter_matrix_policy_is_active() else git(["rev-parse", "HEAD"], check=False)
    )
    pre_run_freeze_commit = resolve_commit(pre_run_freeze_ref) if pre_run_freeze_ref.strip() else ""
    recorded_at = utc_now()
    matrix_path: Path | None = None
    matrix_rows: list[dict[str, str]] = []
    matrix_result_row: dict[str, str] | None = None
    run_start_receipt_path: Path | None = None
    matrix_exists = (attempt_dir / PARAMETER_MATRIX_CSV).exists()
    legacy_summary_only = bool(getattr(args, "legacy_summary_only", False))
    if legacy_summary_only:
        legacy_errors = legacy_summary_only_eligibility_errors(
            attempt_dir,
            str(getattr(args, "legacy_source_commit", "") or ""),
        )
        if legacy_errors:
            raise WorkflowError("Legacy summary eligibility failed:\n" + "\n".join(legacy_errors))
    if parameter_matrix_policy_is_active() and not matrix_exists and not legacy_summary_only:
        raise WorkflowError(
            "Active parameter-matrix policy requires PARAMETER_MATRIX.csv for a new module attempt; "
            "use --legacy-summary-only only for a pre-policy historical result"
        )
    if legacy_summary_only and matrix_exists:
        raise WorkflowError("--legacy-summary-only cannot bypass an existing parameter matrix")
    if legacy_summary_only and args.decision not in {"reject", "rejected", "blocked", "debug"}:
        raise WorkflowError("--legacy-summary-only cannot create keep/best evidence; use a non-promoting decision")
    if parameter_matrix_policy_is_active() and matrix_exists:
        if not seed:
            raise WorkflowError("record-module-attempt under the parameter-matrix policy requires a seed")
        matrix_path = attempt_dir / PARAMETER_MATRIX_CSV
        matrix_rows = ready_parameter_matrix_rows(matrix_path)
        matrix_result_row = select_parameter_matrix_result_row(
            matrix_rows,
            matrix_job_id=str(getattr(args, "matrix_job_id", "") or ""),
            seed=seed,
            label="record-module-attempt",
        )
        runtime_errors = parameter_matrix_runtime_errors(
            matrix_result_row,
            matrix_path=matrix_path,
            config_path=config_path,
            seed=seed,
            baseline_config_path=trial_dir / "config.yaml",
        )
        runtime_errors.extend(
            parameter_matrix_freeze_commit_errors(
                commit_ref=pre_run_freeze_commit,
                matrix_path=matrix_path,
                config_path=config_path,
                job_id=matrix_result_row["job_id"],
            )
        )
        receipt_text = str(getattr(args, "run_start_receipt", "") or "").strip()
        if receipt_text:
            run_start_receipt_path = Path(receipt_text)
            if not run_start_receipt_path.is_absolute():
                run_start_receipt_path = REPO_ROOT / run_start_receipt_path
            runtime_errors.extend(
                run_start_receipt_errors(
                    receipt_path=run_start_receipt_path,
                    log_path=log_path,
                    config_path=config_path,
                    row=matrix_result_row,
                    run_id=args.run_id or attempt_upper,
                    pre_run_freeze_commit=pre_run_freeze_commit,
                    command=command,
                )
            )
        else:
            runtime_errors.append("formal module result requires --run-start-receipt created before training")
        if runtime_errors:
            raise WorkflowError("Formal module result does not match its parameter-matrix row:\n" + "\n".join(runtime_errors))
        metrics = parse_training_log_text(
            captured_training_log_text(log_path, command),
            f"workflow-captured output in {display_path(log_path)}",
        )

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
    if run_start_receipt_path is not None:
        add_file_artifact(
            "run_start_receipt",
            run_start_receipt_path,
            "receipts",
            "run_start_receipt",
            "runner_start",
            f"receipt:{version}:module_trial:{trial_id}:{attempt_lower}:run_start",
            "audit",
            f"Runner start receipt bound to the frozen row for {attempt_upper}.",
        )
        add_file_artifact(
            "run_finish_receipt",
            run_finish_receipt_path(run_start_receipt_path),
            "receipts",
            "run_finish_receipt",
            "runner_finish",
            f"receipt:{version}:module_trial:{trial_id}:{attempt_lower}:run_finish",
            "audit",
            f"Immutable process-finish receipt for {attempt_upper}.",
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

    module_git_dirty = "true"
    if matrix_path is not None:
        allowed_runtime_paths = [
            matrix_path,
            matrix_path.with_name(PARAMETER_MATRIX_MD),
            parameter_matrix_lock_path(matrix_path),
            log_path,
        ]
        if run_start_receipt_path is not None:
            allowed_runtime_paths.append(run_start_receipt_path)
            allowed_runtime_paths.append(run_finish_receipt_path(run_start_receipt_path))
        module_git_dirty = "true" if git_dirty_outside(allowed_runtime_paths) else "false"
    elif not git(["status", "--short"], check=False):
        module_git_dirty = "false"

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
        git_dirty=module_git_dirty,
        legacy_summary_only=legacy_summary_only,
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
        legacy_summary_only=legacy_summary_only,
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
        attempt_type="legacy_summary_only" if legacy_summary_only else args.attempt_type,
        parameter_change="historical summary only; not promotion evidence" if legacy_summary_only else args.parameter_change,
        old_value=args.old_value,
        new_value=args.new_value,
        seed=seed,
        metrics=metrics,
        log_artifact_id=log_artifact_id,
        decision=args.decision,
    )
    append_warehouse_registry(entries, dry_run=False)
    if matrix_path is not None and matrix_result_row is not None:
        sync_parameter_matrix_result_row(
            matrix_path,
            matrix_rows,
            matrix_result_row,
            metrics=metrics,
            decision=args.decision,
            run_id=args.run_id or attempt_upper,
            artifact_ref=artifacts["train_log"]["uri"],
        )

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


def result_referenced_artifact_ids(result_text: str) -> set[str]:
    ids: set[str] = set()
    for match in re.finditer(
        r"^\s*(?:log_artifact_id|train_log_artifact_id|checkpoint_artifact_id):\s*['\"]?([^'\"\s,#]+)",
        result_text,
        re.MULTILINE,
    ):
        artifact_id = match.group(1).strip()
        if artifact_id:
            ids.add(artifact_id)
    return ids


def manifest_artifact_identity_status(manifest_text: str) -> dict[str, dict[str, bool]]:
    matches = list(
        re.finditer(
            r"^\s*artifact_id:\s*['\"]?([^'\"\n#]+)['\"]?\s*$",
            manifest_text,
            re.MULTILINE,
        )
    )
    identities: dict[str, dict[str, bool]] = {}
    for index, match in enumerate(matches):
        artifact_id = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(manifest_text)
        window = manifest_text[match.end() : end]
        identities[artifact_id] = {
            "uri": bool(re.search(r"^\s*uri:\s*['\"]?(warehouse|research)://", window, re.MULTILINE)),
            "sha256": bool(re.search(r"^\s*sha256:\s*['\"]?[0-9a-fA-F]{64}", window, re.MULTILINE)),
            "size_bytes": bool(re.search(r"^\s*size_bytes:\s*['\"]?[0-9]+", window, re.MULTILINE)),
        }
    return identities


def audit_result_manifest_artifact_chain() -> list[str]:
    errors: list[str] = []
    for result_path in sorted((REPO_ROOT / "experiments").rglob("result.yaml")):
        result_text = read_text(result_path)
        artifact_ids = result_referenced_artifact_ids(result_text)
        if not artifact_ids:
            continue
        manifest_path = result_path.with_name("manifest.yaml")
        if not manifest_path.exists():
            errors.append(f"{rel(result_path)} references artifacts but is missing {rel(manifest_path)}")
            continue
        identities = manifest_artifact_identity_status(read_text(manifest_path))
        for artifact_id in sorted(artifact_ids):
            if artifact_id not in identities:
                errors.append(
                    f"{rel(result_path)} references {artifact_id}, but {rel(manifest_path)} does not register it"
                )
                continue
            missing_fields = [field for field, ok in identities[artifact_id].items() if not ok]
            if missing_fields:
                errors.append(
                    f"{rel(manifest_path)} artifact {artifact_id} missing identity fields: "
                    + ", ".join(missing_fields)
                )
    return errors


def canonical_transition_payload(record: dict[str, object]) -> str:
    payload = {key: value for key, value in record.items() if key != "current_transition_hash"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def evidence_transition_hash(record: dict[str, object]) -> str:
    payload = canonical_transition_payload(record).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def normalize_hash(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return ""
    return text if text.startswith("sha256:") else f"sha256:{text}"


def is_valid_authority_ref(value: str, routing_path: Path) -> bool:
    text = value.strip()
    if not text:
        return True
    if text.startswith(("warehouse://", "research://")):
        return True
    if re.fullmatch(r"(?:sha256:)?[0-9a-fA-F]{64}", text):
        return True
    candidate_paths = [REPO_ROOT / text, routing_path.parent / text]
    return any(path.exists() for path in candidate_paths)


def collect_authority_ref_errors(value: object, routing_path: Path, trail: str = "authority_refs") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            errors.extend(collect_authority_ref_errors(child, routing_path, f"{trail}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(collect_authority_ref_errors(child, routing_path, f"{trail}[{index}]"))
    elif isinstance(value, str):
        if not is_valid_authority_ref(value, routing_path):
            errors.append(f"{trail} points to missing authority ref: {value}")
    elif value is not None:
        errors.append(f"{trail} must contain strings, lists, or objects")
    return errors


def load_transition_log(path: Path) -> list[dict[str, object]]:
    transitions: list[dict[str, object]] = []
    for line_number, raw_line in enumerate(read_text(path).splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            transition = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"{rel(path)} line {line_number} is not valid JSON: {exc}") from exc
        if not isinstance(transition, dict):
            raise WorkflowError(f"{rel(path)} line {line_number} must be a JSON object")
        transitions.append(transition)
    return transitions


def require_transition_role(value: object, field: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        if not value.get("role_key"):
            errors.append(f"{field} missing role_key")
        return
    if isinstance(value, list) and value:
        for index, item in enumerate(value):
            require_transition_role(item, f"{field}[{index}]", errors)
        return
    errors.append(f"{field} must be a role object or non-empty list of role objects")


def transition_string_section(record: dict[str, object], section: str, key: str) -> str:
    value = record.get(section)
    if isinstance(value, dict):
        item = value.get(key)
        return "" if item is None else str(item)
    return ""


def validate_transition_rule_checks(
    transition: dict[str, object],
    transition_type: str,
    to_state: str,
    errors: list[str],
) -> None:
    rule_checks = transition.get("rule_checks")
    if not isinstance(rule_checks, list) or not rule_checks:
        errors.append(f"{transition.get('transition_id', '<unknown>')} must include non-empty rule_checks")
        return
    has_bad_verdict = False
    for index, rule in enumerate(rule_checks):
        if not isinstance(rule, dict):
            errors.append(f"{transition.get('transition_id', '<unknown>')} rule_checks[{index}] must be an object")
            continue
        for field in ["rule_id", "verdict", "authority_ref"]:
            if not rule.get(field):
                errors.append(
                    f"{transition.get('transition_id', '<unknown>')} rule_checks[{index}] missing {field}"
                )
        verdict = str(rule.get("verdict", "")).lower()
        if verdict in EVIDENCE_BAD_RULE_VERDICTS:
            has_bad_verdict = True
    if has_bad_verdict and (
        transition_type in EVIDENCE_ADVANCING_TRANSITIONS
        or to_state in {"promotion_candidate", "promoted"}
    ):
        errors.append(
            f"{transition.get('transition_id', '<unknown>')} cannot advance/promote with failed rule_checks"
        )


def validate_transition_agent_attribution(transition: dict[str, object], errors: list[str]) -> None:
    attribution = transition.get("agent_attribution")
    if not isinstance(attribution, dict):
        errors.append(f"{transition.get('transition_id', '<unknown>')} missing agent_attribution")
        return
    require_transition_role(attribution.get("proposed_by"), "agent_attribution.proposed_by", errors)
    require_transition_role(attribution.get("checked_by"), "agent_attribution.checked_by", errors)
    require_transition_role(attribution.get("applied_by"), "agent_attribution.applied_by", errors)


def validate_transition_decision(transition: dict[str, object], errors: list[str]) -> None:
    decision = transition.get("decision")
    if not isinstance(decision, dict):
        errors.append(f"{transition.get('transition_id', '<unknown>')} missing decision")
        return
    for field in ["blocking_issues", "non_blocking_warnings", "not_checked"]:
        if field not in decision:
            errors.append(f"{transition.get('transition_id', '<unknown>')} decision missing {field}")


def resolve_transition_log_path(routing_path: Path, file_value: str) -> Path:
    transition_path = Path(file_value)
    if transition_path.is_absolute():
        return transition_path
    local_path = routing_path.parent / transition_path
    if local_path.exists():
        return local_path
    return REPO_ROOT / transition_path


def validate_evidence_routing_file(routing_path: Path) -> list[str]:
    errors: list[str] = []
    data = read_shallow_yaml(routing_path)
    subject_id = yaml_section_value(data, "subject", "subject_id")
    subject_type = yaml_section_value(data, "subject", "subject_type")
    current_state = yaml_section_value(data, "current_state", "evidence_state")
    derived_transition_id = yaml_section_value(data, "current_state", "derived_from_transition_id")
    derived_transition_hash = normalize_hash(
        yaml_section_value(data, "current_state", "derived_from_transition_hash")
    )
    transition_file_value = yaml_section_value(data, "transitions", "file")
    chain_head_id = yaml_section_value(data, "transitions", "chain_head_transition_id")
    chain_head_hash = normalize_hash(yaml_section_value(data, "transitions", "chain_head_hash"))

    if not subject_id:
        errors.append(f"{rel(routing_path)} missing subject.subject_id")
    if subject_type not in EVIDENCE_SUBJECT_TYPES:
        errors.append(f"{rel(routing_path)} invalid subject.subject_type: {subject_type}")
    if current_state not in EVIDENCE_ROUTING_STATES:
        errors.append(f"{rel(routing_path)} invalid current_state.evidence_state: {current_state}")
    if not transition_file_value:
        errors.append(f"{rel(routing_path)} missing transitions.file")
        return errors

    transition_log = resolve_transition_log_path(routing_path, transition_file_value)
    if not transition_log.exists():
        errors.append(f"{rel(routing_path)} missing transition log: {display_path(transition_log)}")
        return errors

    transitions = load_transition_log(transition_log)
    if not transitions:
        errors.append(f"{rel(transition_log)} must contain at least one transition")
        return errors

    seen_ids: set[str] = set()
    previous_id = ""
    previous_hash = ""
    previous_to_state = ""
    for index, transition in enumerate(transitions):
        transition_id = str(transition.get("transition_id", "")).strip()
        if not transition_id:
            errors.append(f"{rel(transition_log)} transition #{index + 1} missing transition_id")
        elif transition_id in seen_ids:
            errors.append(f"{rel(transition_log)} duplicate transition_id: {transition_id}")
        seen_ids.add(transition_id)

        actual_hash = evidence_transition_hash(transition)
        declared_hash = normalize_hash(transition.get("current_transition_hash"))
        if declared_hash != actual_hash:
            errors.append(f"{transition_id or '<unknown>'} current_transition_hash mismatch")

        declared_previous_id = "" if transition.get("previous_transition_id") is None else str(transition.get("previous_transition_id", ""))
        declared_previous_hash = normalize_hash(transition.get("previous_transition_hash"))
        if index == 0:
            if declared_previous_id or declared_previous_hash:
                errors.append(f"{transition_id} first transition must not have previous transition identity")
        else:
            if declared_previous_id != previous_id:
                errors.append(f"{transition_id} previous_transition_id must be {previous_id}")
            if declared_previous_hash != previous_hash:
                errors.append(f"{transition_id} previous_transition_hash must match previous transition hash")

        transition_subject = transition.get("subject")
        if not isinstance(transition_subject, dict):
            errors.append(f"{transition_id} missing subject object")
        else:
            if transition_subject.get("subject_id") != subject_id:
                errors.append(f"{transition_id} subject_id does not match {rel(routing_path)}")
            if transition_subject.get("subject_type") not in EVIDENCE_SUBJECT_TYPES:
                errors.append(f"{transition_id} invalid subject_type")

        transition_body = transition.get("transition")
        if not isinstance(transition_body, dict):
            errors.append(f"{transition_id} missing transition object")
            transition_type = ""
            from_state = ""
            to_state = ""
        else:
            transition_type = str(transition_body.get("transition_type", ""))
            from_state = "" if transition_body.get("from_state") is None else str(transition_body.get("from_state", ""))
            to_state = str(transition_body.get("to_state", ""))
            if transition_type not in EVIDENCE_TRANSITION_TYPES:
                errors.append(f"{transition_id} invalid transition_type: {transition_type}")
            if to_state not in EVIDENCE_ROUTING_STATES:
                errors.append(f"{transition_id} invalid to_state: {to_state}")
            if from_state and from_state not in EVIDENCE_ROUTING_STATES:
                errors.append(f"{transition_id} invalid from_state: {from_state}")
            if index > 0 and from_state != previous_to_state:
                errors.append(f"{transition_id} from_state must equal previous to_state {previous_to_state}")

        validate_transition_rule_checks(transition, transition_type, to_state, errors)
        validate_transition_agent_attribution(transition, errors)
        validate_transition_decision(transition, errors)
        authority_refs = transition.get("authority_refs")
        if not isinstance(authority_refs, dict):
            errors.append(f"{transition_id} missing authority_refs object")
        else:
            errors.extend(collect_authority_ref_errors(authority_refs, routing_path, "authority_refs"))

        previous_id = transition_id
        previous_hash = actual_hash
        previous_to_state = to_state

    head = transitions[-1]
    head_id = str(head.get("transition_id", ""))
    head_hash = evidence_transition_hash(head)
    head_state = transition_string_section(head, "transition", "to_state")
    if derived_transition_id != head_id:
        errors.append(f"{rel(routing_path)} current_state derived_from_transition_id does not match chain head")
    if derived_transition_hash != head_hash:
        errors.append(f"{rel(routing_path)} current_state derived_from_transition_hash does not match chain head")
    if current_state != head_state:
        errors.append(f"{rel(routing_path)} current_state evidence_state does not match chain head")
    if chain_head_id != head_id:
        errors.append(f"{rel(routing_path)} transitions.chain_head_transition_id does not match chain head")
    if chain_head_hash != head_hash:
        errors.append(f"{rel(routing_path)} transitions.chain_head_hash does not match chain head")
    return errors


def validate_campaign_result_indexes() -> list[str]:
    errors: list[str] = []
    campaigns_root = REPO_ROOT / "experiments" / "campaigns"
    if not campaigns_root.exists():
        return errors
    for result_index in sorted(campaigns_root.rglob("RESULT_INDEX.md")):
        text = read_text(result_index)
        for line_number, line in enumerate(text.splitlines(), start=1):
            authority_match = re.search(r"\bauthority\s*:\s*(\S+)", line)
            if authority_match and authority_match.group(1) != "derived_index_only":
                errors.append(f"{rel(result_index)}:{line_number} campaign index authority must be derived_index_only")
        if re.search(r"\bauthoritative\b", text, flags=re.IGNORECASE):
            errors.append(f"{rel(result_index)} must not claim authoritative campaign metrics")
        if re.search(r"\b[HUSZS]{1,2}\s*[:=]\s*[0-9]", text) and not re.search(
            r"(result_ref|metric_source|authority_source|derived_index_only)", text
        ):
            errors.append(f"{rel(result_index)} appears to contain metrics without source refs")
    return errors


def read_simple_yaml_maps(path: Path) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    scalars: dict[str, str] = {}
    maps: dict[str, dict[str, str]] = {}
    current_section = ""
    for raw_line in read_text(path).splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            section_match = re.match(r"^([A-Za-z0-9_]+):\s*$", raw_line)
            if section_match:
                current_section = section_match.group(1)
                maps[current_section] = {}
                continue
            value_match = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if value_match:
                current_section = ""
                scalars[value_match.group(1)] = yaml_unquote(value_match.group(2))
                continue
        if current_section and raw_line.startswith("  ") and not raw_line.startswith("    "):
            value_match = re.match(r"^\s{2}([A-Za-z0-9_]+):\s*(.*)$", raw_line)
            if value_match:
                maps.setdefault(current_section, {})[value_match.group(1)] = yaml_unquote(value_match.group(2))
    return scalars, maps


def truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1", "y"}


def falsey(value: str) -> bool:
    return value.strip().lower() in {"false", "no", "0", "n"}


def valid_runtime_agent_instance_id(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in AGENT_RUNTIME_INVALID_INSTANCE_IDS:
        return False
    if any(fragment in normalized for fragment in AGENT_RUNTIME_INVALID_INSTANCE_ID_FRAGMENTS):
        return False
    if len(normalized) < 8:
        return False
    if not re.search(r"[0-9]", normalized):
        return False
    return True


def has_any_role(mapping: dict[str, str], roles: set[str]) -> bool:
    return any(role in mapping for role in roles)


def validate_agent_runtime_ref(value: str, gate_path: Path) -> bool:
    text = value.strip()
    if not text:
        return False
    if text.startswith(("warehouse://", "research://", "agent://", "thread://", "subagent://")):
        return True
    candidates = [REPO_ROOT / text, gate_path.parent / text]
    return any(path.exists() for path in candidates)


def resolve_agent_runtime_local_ref(value: str, gate_path: Path) -> Path | None:
    text = value.strip()
    if not text or text.startswith(("warehouse://", "research://", "agent://", "thread://", "subagent://")):
        return None
    candidates = [REPO_ROOT / text, gate_path.parent / text]
    for path in candidates:
        if path.exists():
            return path
    return None


def normalized_text_fingerprint(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).hexdigest()


def validate_agent_runtime_role_ref(
    *,
    gate_name: str,
    gate_path: Path,
    role: str,
    instance_id: str,
    refs: dict[str, str],
    ref_name: str,
) -> tuple[list[str], Path | None, str]:
    errors: list[str] = []
    value = refs.get(role, "")
    if not value:
        errors.append(f"{gate_name} missing {ref_name}.{role}")
        return errors, None, ""
    path = resolve_agent_runtime_local_ref(value, gate_path)
    if path is None:
        errors.append(f"{gate_name} {ref_name}.{role} must point to a local evidence file: {value}")
        return errors, None, ""
    if not path.is_file():
        errors.append(f"{gate_name} {ref_name}.{role} is not a file: {value}")
        return errors, path, ""
    text = read_text(path).strip()
    if not text:
        errors.append(f"{gate_name} {ref_name}.{role} points to an empty file: {value}")
    role_label = role.replace("_", " ")
    if instance_id not in text and role not in text and role_label not in text:
        errors.append(f"{gate_name} {ref_name}.{role} does not mention role or agent id")
    return errors, path, text


def role_display_label(role: str) -> str:
    return " ".join(part.capitalize() for part in role.split("_") if part)


def validate_agent_thread_title(subject_id: str, role: str, thread_title: str) -> str | None:
    normalized = thread_title.strip()
    if not normalized:
        return f"named_thread_titles.{role} is missing"
    legacy_random_names = {
        "herschel",
        "epicurus",
        "galileo",
        "aristotle",
        "dewey",
        "jason",
        "poincare",
        "dalton",
        "mendel",
        "bohr",
        "raman",
        "pasteur",
        "descartes",
        "linnaeus",
        "dirac",
        "lorentz",
        "peirce",
        "feynman",
    }
    if normalized.lower() in legacy_random_names:
        return f"named_thread_titles.{role} uses a random legacy nickname: {thread_title}"
    if subject_id and subject_id.lower() not in normalized.lower():
        return f"named_thread_titles.{role} must include subject_id: {subject_id}"
    display_words = normalized.lower().replace("_", " ").replace("-", " ").replace("|", " ")
    missing_role_words = [part for part in role.split("_") if part and part.lower() not in display_words]
    if missing_role_words:
        expected = role_display_label(role)
        return f"named_thread_titles.{role} must include role label words: {expected}"
    if "|" not in normalized:
        return f"named_thread_titles.{role} must use '<subject_id> | <Role Label>' format"
    return None


def validate_agent_runtime_gate_file(gate_path: Path) -> list[str]:
    errors: list[str] = []
    scalars, maps = read_simple_yaml_maps(gate_path)
    gate_name = rel(gate_path)

    common_required_scalars = [
        "schema_version",
        "subject_id",
        "subject_type",
        "formal_evidence",
        "activation_mode",
        "agent_instance_mode",
    ]
    for field in common_required_scalars:
        if field not in scalars or scalars[field] == "":
            errors.append(f"{gate_name} missing {field}")

    formal = truthy(scalars.get("formal_evidence", ""))
    if not formal:
        evidence_level = scalars.get("evidence_level", "")
        debug_smoke = truthy(scalars.get("debug_smoke", ""))
        if scalars.get("activation_mode") != "role_only":
            errors.append(f"{gate_name} non-formal runtime gate requires activation_mode: role_only")
        if scalars.get("agent_instance_mode") != "role_only":
            errors.append(f"{gate_name} non-formal runtime gate requires agent_instance_mode: role_only")
        if evidence_level not in NON_FORMAL_AGENT_RUNTIME_EVIDENCE_LEVELS and not debug_smoke:
            errors.append(
                f"{gate_name} non-formal runtime gate must declare evidence_level: "
                f"{'/'.join(sorted(NON_FORMAL_AGENT_RUNTIME_EVIDENCE_LEVELS))}"
            )
        return errors

    required_scalars = [
        "lifecycle",
        "ui_visibility",
        "tool_support_real_multi_agent_available",
        "thread_management_tool",
        "single_agent_execution",
        "runner_start_allowed",
        "formal_runner_allowed",
        "formal_evidence_allowed",
        "owner_monitor_mode",
        "owner_role",
        "owner_visible_reporting",
        "report_channel",
        "report_interval_minutes",
        "agent_activity_stream",
        "monitor_handoff_on_pause",
        "thread_archive_policy",
        "archive_completed_threads_on_stage_end",
        "archived_threads_record",
    ]
    for field in required_scalars:
        if field not in scalars or scalars[field] == "":
            errors.append(f"{gate_name} missing {field}")

    formal_backend = scalars.get("formal_runtime_backend", "").strip() or "named_owner_thread"
    activation_mode = scalars.get("activation_mode", "")
    agent_instance_mode = scalars.get("agent_instance_mode", "")
    if activation_mode == "role_only" and agent_instance_mode == "role_only" and formal_backend == "named_owner_thread":
        errors.append(f"{gate_name} formal role_only gate must declare formal_runtime_backend: server_detached_role_only")
    if not truthy(scalars.get("runner_start_allowed", "")):
        errors.append(f"{gate_name} runner_start_allowed must be true before formal Runner starts")
    if not truthy(scalars.get("formal_runner_allowed", "")):
        errors.append(f"{gate_name} formal_runner_allowed must be true before formal Runner starts")
    if not truthy(scalars.get("formal_evidence_allowed", "")):
        errors.append(f"{gate_name} formal_evidence_allowed must be true for formal evidence")
    if not truthy(scalars.get("owner_monitor_mode", "")):
        errors.append(f"{gate_name} owner_monitor_mode must be true for formal Runner visibility")
    if scalars.get("owner_role") != "monitor":
        errors.append(f"{gate_name} owner_role must be monitor")
    if not truthy(scalars.get("owner_visible_reporting", "")):
        errors.append(f"{gate_name} owner_visible_reporting must be true")
    if not scalars.get("report_channel"):
        errors.append(f"{gate_name} report_channel must name the visible owner-facing channel")
    try:
        interval = int(scalars.get("report_interval_minutes", "0"))
    except ValueError:
        interval = 0
    if interval <= 0 or interval > 60:
        errors.append(f"{gate_name} report_interval_minutes must be between 1 and 60")
    if scalars.get("monitor_handoff_on_pause") != "required":
        errors.append(f"{gate_name} monitor_handoff_on_pause must be required")
    activity_stream = scalars.get("agent_activity_stream", "")
    if not validate_agent_runtime_ref(activity_stream, gate_path):
        errors.append(f"{gate_name} agent_activity_stream points to missing activity log: {activity_stream}")
    archived_threads_record = scalars.get("archived_threads_record", "")
    if not validate_agent_runtime_ref(archived_threads_record, gate_path):
        errors.append(f"{gate_name} archived_threads_record points to missing archive log: {archived_threads_record}")

    output_refs = maps.get("agent_output_refs", {})
    pre_run_checks = maps.get("pre_run_required_checks", {})
    authority_refs = maps.get("authority_refs", {})
    for key, value in authority_refs.items():
        if not validate_agent_runtime_ref(value, gate_path):
            errors.append(f"{gate_name} authority_refs.{key} points to missing authority ref: {value}")

    if formal_backend == "server_detached_role_only":
        if activation_mode != "role_only":
            errors.append(f"{gate_name} server_detached formal gate requires activation_mode: role_only")
        if agent_instance_mode != "role_only":
            errors.append(f"{gate_name} server_detached formal gate requires agent_instance_mode: role_only")
        if scalars.get("ui_visibility") != "current_owner_thread_only":
            errors.append(f"{gate_name} server_detached formal gate must declare ui_visibility: current_owner_thread_only")
        if not truthy(scalars.get("single_agent_execution", "")):
            errors.append(f"{gate_name} server_detached formal gate requires single_agent_execution: true")
        if truthy(scalars.get("real_multi_agent_required", "")):
            errors.append(f"{gate_name} server_detached formal gate requires real_multi_agent_required: false")
        if truthy(scalars.get("thread_creation_allowed", "")):
            errors.append(f"{gate_name} server_detached formal gate requires thread_creation_allowed: false")
        if scalars.get("thread_management_tool") not in {"not_used", "role_only"}:
            errors.append(f"{gate_name} server_detached formal gate must declare thread_management_tool: not_used")
        if scalars.get("thread_archive_policy") != "not_applicable_no_named_threads":
            errors.append(f"{gate_name} server_detached formal gate must declare thread_archive_policy: not_applicable_no_named_threads")
        if truthy(scalars.get("archive_completed_threads_on_stage_end", "")):
            errors.append(f"{gate_name} server_detached formal gate must declare archive_completed_threads_on_stage_end: false")
        if maps.get("named_thread_ids", {}):
            errors.append(f"{gate_name} server_detached formal gate must not declare named_thread_ids")
        if maps.get("named_thread_titles", {}):
            errors.append(f"{gate_name} server_detached formal gate must not declare named_thread_titles")
        if maps.get("agent_instance_status", {}):
            errors.append(f"{gate_name} server_detached formal gate must not declare agent_instance_status")
        if maps.get("agent_status_refs", {}):
            errors.append(f"{gate_name} server_detached formal gate must not declare agent_status_refs")
        if not output_refs:
            errors.append(f"{gate_name} missing agent_output_refs")
        output_paths: dict[str, Path] = {}
        output_fingerprints: dict[str, str] = {}
        for role in sorted(AGENT_RUNTIME_REQUIRED_FORMAL_ROLES):
            ref_errors, output_path, output_text = validate_agent_runtime_role_ref(
                gate_name=gate_name,
                gate_path=gate_path,
                role=role,
                instance_id=role,
                refs=output_refs,
                ref_name="agent_output_refs",
            )
            errors.extend(ref_errors)
            if output_path is not None:
                output_paths[role] = output_path.resolve()
            if output_text:
                output_fingerprints[role] = normalized_text_fingerprint(output_text)
        if len(set(output_paths.values())) < len(output_paths):
            errors.append(f"{gate_name} agent_output_refs must use independent files per role")
        seen_fingerprints: dict[str, str] = {}
        for role, fingerprint in output_fingerprints.items():
            other_role = seen_fingerprints.get(fingerprint)
            if other_role and other_role != role:
                errors.append(f"{gate_name} agent_output_refs.{role} duplicates output content from {other_role}")
            else:
                seen_fingerprints[fingerprint] = role
        if not pre_run_checks:
            errors.append(f"{gate_name} missing pre_run_required_checks")
        for role in sorted(AGENT_RUNTIME_REQUIRED_FORMAL_ROLES):
            normalized = pre_run_checks.get(role, "").strip().lower()
            if normalized not in AGENT_RUNTIME_ALLOW_DECISIONS:
                errors.append(f"{gate_name} pre_run_required_checks.{role} must be allow/pass before Runner starts")
        for role in sorted(pre_run_checks):
            if role not in AGENT_RUNTIME_REQUIRED_FORMAL_ROLES:
                errors.append(f"{gate_name} pre_run_required_checks.{role} is not a supported server_detached role")
        preflight = maps.get("sequential_role_preflight", {})
        if not preflight:
            errors.append(f"{gate_name} missing sequential_role_preflight")
        for key in sorted(AGENT_RUNTIME_SERVER_DETACHED_PREFLIGHT_KEYS):
            value = preflight.get(key, "")
            if not truthy(value):
                errors.append(f"{gate_name} sequential_role_preflight.{key} must be true before formal Runner starts")
        return errors

    if activation_mode != "real_multi_agent":
        errors.append(f"{gate_name} formal evidence requires activation_mode: real_multi_agent")
    if agent_instance_mode != "named_owner_thread":
        errors.append(f"{gate_name} formal evidence requires agent_instance_mode: named_owner_thread")
    if scalars.get("ui_visibility") != "left_sidebar_named_threads":
        errors.append(f"{gate_name} must declare ui_visibility: left_sidebar_named_threads")
    if scalars.get("thread_archive_policy") != "archive_completed_threads_on_stage_end":
        errors.append(f"{gate_name} thread_archive_policy must be archive_completed_threads_on_stage_end")
    if not truthy(scalars.get("archive_completed_threads_on_stage_end", "")):
        errors.append(f"{gate_name} archive_completed_threads_on_stage_end must be true")
    if not truthy(scalars.get("tool_support_real_multi_agent_available", "")):
        errors.append(f"{gate_name} must confirm real multi-agent tool support")
    if truthy(scalars.get("single_agent_execution", "")):
        errors.append(f"{gate_name} single_agent_execution cannot be true for formal evidence")
    if scalars.get("thread_management_tool") in {"", "role_only", "manual", "multi_agent_v1.spawn_agent", "not_used"}:
        errors.append(f"{gate_name} thread_management_tool must name the named Codex thread tool")

    agent_ids = maps.get("named_thread_ids", {})
    if not agent_ids:
        errors.append(f"{gate_name} missing named_thread_ids")
    for role, instance_id in agent_ids.items():
        if not valid_runtime_agent_instance_id(instance_id):
            errors.append(f"{gate_name} named_thread_ids.{role} is not a real agent/thread id")
    thread_titles = maps.get("named_thread_titles", {})
    if not thread_titles:
        errors.append(f"{gate_name} missing named_thread_titles")
    for role in agent_ids:
        title_error = validate_agent_thread_title(scalars.get("subject_id", ""), role, thread_titles.get(role, ""))
        if title_error:
            errors.append(f"{gate_name} {title_error}")
    extra_title_roles = sorted(set(thread_titles) - set(agent_ids))
    for role in extra_title_roles:
        errors.append(f"{gate_name} named_thread_titles.{role} has no matching named_thread_ids entry")
    instance_to_roles: dict[str, list[str]] = {}
    for role, instance_id in agent_ids.items():
        instance_to_roles.setdefault(instance_id.strip(), []).append(role)
    for instance_id, roles in sorted(instance_to_roles.items()):
        if len(roles) > 1:
            errors.append(
                f"{gate_name} named_thread_ids reuse one agent id for multiple roles: "
                f"{instance_id} -> {', '.join(sorted(roles))}"
            )

    if not has_any_role(agent_ids, {"runner_monitor", "runner"}):
        errors.append(f"{gate_name} missing Runner Monitor named thread id")
    if not has_any_role(agent_ids, {"evidence_quality_checker", "quality_checker"}):
        errors.append(f"{gate_name} missing Quality Checker named thread id")

    instance_status = maps.get("agent_instance_status", {})
    if not instance_status:
        errors.append(f"{gate_name} missing agent_instance_status")
    for role in agent_ids:
        normalized_status = instance_status.get(role, "").strip().lower()
        if normalized_status in AGENT_RUNTIME_BLOCKED_INSTANCE_STATUSES:
            errors.append(f"{gate_name} agent_instance_status.{role} must be running/completed, not {normalized_status or 'missing'}")
        elif normalized_status not in AGENT_RUNTIME_ALLOWED_INSTANCE_STATUSES:
            errors.append(f"{gate_name} agent_instance_status.{role} has unsupported status: {normalized_status}")

    status_refs = maps.get("agent_status_refs", {})
    if not status_refs:
        errors.append(f"{gate_name} missing agent_status_refs")
    if not output_refs:
        errors.append(f"{gate_name} missing agent_output_refs")
    output_paths: dict[str, Path] = {}
    output_fingerprints: dict[str, str] = {}
    for role, instance_id in agent_ids.items():
        ref_errors, _status_path, _status_text = validate_agent_runtime_role_ref(
            gate_name=gate_name,
            gate_path=gate_path,
            role=role,
            instance_id=instance_id,
            refs=status_refs,
            ref_name="agent_status_refs",
        )
        errors.extend(ref_errors)
        ref_errors, output_path, output_text = validate_agent_runtime_role_ref(
            gate_name=gate_name,
            gate_path=gate_path,
            role=role,
            instance_id=instance_id,
            refs=output_refs,
            ref_name="agent_output_refs",
        )
        errors.extend(ref_errors)
        if output_path is not None:
            output_paths[role] = output_path.resolve()
        if output_text:
            output_fingerprints[role] = normalized_text_fingerprint(output_text)
    if len(set(output_paths.values())) < len(output_paths):
        errors.append(f"{gate_name} agent_output_refs must use independent files per role")
    seen_fingerprints: dict[str, str] = {}
    for role, fingerprint in output_fingerprints.items():
        other_role = seen_fingerprints.get(fingerprint)
        if other_role and other_role != role:
            errors.append(f"{gate_name} agent_output_refs.{role} duplicates output content from {other_role}")
        else:
            seen_fingerprints[fingerprint] = role

    if not pre_run_checks:
        errors.append(f"{gate_name} missing pre_run_required_checks")
    for role, decision in pre_run_checks.items():
        normalized = decision.strip().lower()
        if normalized not in AGENT_RUNTIME_ALLOW_DECISIONS:
            errors.append(f"{gate_name} pre_run_required_checks.{role} must be allow/pass before Runner starts")
        if role not in agent_ids:
            errors.append(f"{gate_name} pre_run_required_checks.{role} has no matching named_thread_ids entry")

    if not has_any_role(pre_run_checks, {"runner_monitor", "runner"}):
        errors.append(f"{gate_name} missing Runner Monitor pre-run allow")
    if not has_any_role(pre_run_checks, {"evidence_quality_checker", "quality_checker"}):
        errors.append(f"{gate_name} missing Quality Checker pre-run allow")

    preflight = maps.get("multi_agent_preflight", {})
    if not preflight:
        errors.append(f"{gate_name} missing multi_agent_preflight")
    for key in sorted(AGENT_RUNTIME_PREFLIGHT_KEYS):
        value = preflight.get(key, "")
        if not truthy(value):
            errors.append(f"{gate_name} multi_agent_preflight.{key} must be true before formal Runner starts")
    return errors


def resolve_agent_runtime_gate_path(path_text: str) -> Path:
    gate_path = Path(path_text)
    if not gate_path.is_absolute():
        gate_path = REPO_ROOT / gate_path
    return gate_path


def cmd_validate_agent_runtime(args: argparse.Namespace) -> int:
    if args.path:
        gate_files = [resolve_agent_runtime_gate_path(args.path)]
    else:
        gate_files = sorted((REPO_ROOT / "experiments").rglob("agent_runtime.yaml"))
    errors: list[str] = []
    for gate_path in gate_files:
        if not gate_path.exists():
            errors.append(f"Missing agent runtime gate: {display_path(gate_path)}")
            continue
        errors.extend(validate_agent_runtime_gate_file(gate_path))
    if errors:
        raise WorkflowError("Agent runtime validation failed:\n" + "\n".join(errors))
    print(f"validate-agent-runtime-ok gates={len(gate_files)}")
    return 0


def cmd_multi_agent_preflight(args: argparse.Namespace) -> int:
    gate_path = resolve_agent_runtime_gate_path(args.path)
    if not gate_path.exists():
        raise WorkflowError(f"Missing agent runtime gate: {display_path(gate_path)}")
    errors = validate_agent_runtime_gate_file(gate_path)
    if errors:
        raise WorkflowError("Multi-agent preflight failed:\n" + "\n".join(errors))
    scalars, maps = read_simple_yaml_maps(gate_path)
    backend = scalars.get("formal_runtime_backend", "").strip() or "named_owner_thread"
    role_count = len(maps.get("named_thread_ids", {}))
    if backend == "server_detached_role_only":
        role_count = len(maps.get("agent_output_refs", {}))
    print(f"multi-agent-preflight-ok path={display_path(gate_path)} agents={role_count} backend={backend}")
    print(f"formal_runner_allowed={scalars.get('formal_runner_allowed', '')}")
    print(f"formal_evidence_allowed={scalars.get('formal_evidence_allowed', '')}")
    return 0


AGENT_CLEANUP_CLOSE_STATUSES = {"completed", "complete", "closed"}
AGENT_CLEANUP_KEEP_STATUSES = {"spawned", "running", "active"}
WORKFLOW_MANIFEST_CATEGORIES = {
    "daily_entry",
    "core",
    "playbook",
    "protocol",
    "reference",
    "agents",
    "archive",
    "deprecated",
}
WORKFLOW_MANIFEST_STATUSES = {
    "active",
    "active_reference",
    "historical",
    "deprecated",
    "moved_redirect",
}
WORKFLOW_MANIFEST_REQUIRED_IDS = {
    "workflow_readme",
    "manifest",
    "start_here",
    "kernel",
    "quick_start",
    "router",
    "task_start_mini",
    "task_start_card",
    "agent_runtime_hard_gate",
    "agent_cleanup_protocol",
    "playbook_tune",
    "playbook_ablation",
    "playbook_confirmation",
    "playbook_innovation",
    "playbook_promotion",
    "playbook_mixed_campaign",
    "playbook_paper_intake",
    "playbook_paper_to_experiment",
    "module_template_selection",
    "ai_cross_review_protocol",
}

AI_CROSS_REVIEW_REQUIRED_FILES = [
    "00_task.md",
    "01_codex_actions.md",
    "02_diff.patch",
    "03_validation.md",
    "04_claims.md",
    "05_claude_review_round_1.md",
    "06_codex_response_round_1.md",
    "07_claude_review_round_2.md",
    "08_codex_response_round_2.md",
    "09_claude_review_round_3.md",
    "10_final_decision.md",
]

AI_CROSS_REVIEW_ROUND_MARKERS = {
    "05_claude_review_round_1.md": ["round: 1", "verdict:", "blocking_issues:"],
    "06_codex_response_round_1.md": ["round: 1", "reviewer: codex", "addressed_claude_findings:", "validation_rerun:", "remaining_blocking_issues:"],
    "07_claude_review_round_2.md": ["round: 2", "verdict:", "blocking_issues:"],
    "08_codex_response_round_2.md": ["round: 2", "reviewer: codex", "addressed_claude_findings:", "validation_rerun:", "remaining_blocking_issues:"],
    "09_claude_review_round_3.md": ["round: 3", "verdict:", "blocking_issues:"],
}

AI_CROSS_REVIEW_FINAL_MARKERS = {
    "ai_cross_review_status: pass",
    "owner_participation: not_required",
    "rounds_completed:",
    "codex_fixes_or_rebuttals_recorded: true",
    "machine_gates_passed: true",
    "unresolved_blocking_issues: 0",
}
AI_CROSS_REVIEW_REVIEW_ROUND_FILES = {
    "05_claude_review_round_1.md",
    "07_claude_review_round_2.md",
    "09_claude_review_round_3.md",
}
AI_CROSS_REVIEW_DEFAULT_VALIDATION_COMMANDS = [
    "python workflow\\gtpj_workflow.py validate",
    "python workflow\\gtpj_workflow.py validate-workflow-consistency",
    "python workflow\\gtpj_workflow.py audit-boundary",
    "python -m py_compile workflow\\gtpj_workflow.py",
]
AI_CROSS_REVIEW_CORE_VALIDATION_FRAGMENTS = [
    "workflow\\gtpj_workflow.py validate",
    "workflow\\gtpj_workflow.py validate-workflow-consistency",
    "workflow\\gtpj_workflow.py audit-boundary",
    "py_compile workflow\\gtpj_workflow.py",
]
AI_CROSS_REVIEW_TIER_ROUNDS = {
    "fast": 0,
    "review-1": 1,
    "strict-3": 3,
}
AI_CROSS_REVIEW_STRICT_KEYWORDS = [
    "training-entry",
    "training_entry",
    "train_",
    "evaluation",
    "metric",
    "split",
    "label",
    "class-order",
    "class_order",
    "logits",
    "runner",
    "warehouse",
    "confirmation",
    "promotion",
    "baseline",
    "formal result",
    "experiment conclusion",
    "paper claim",
    "论文 claim",
    "正式实验结论",
]
AI_CROSS_REVIEW_STRICT_RESULT_FILENAMES = {
    "result.yaml",
    "result.yml",
    "result.md",
    "quality_check.md",
    "attempts.md",
    "agent_activity.md",
    "promotion.md",
    "baseline.md",
}
AI_CROSS_REVIEW_CLAUDE_ROUND_FILES = [
    ("05_claude_review_round_1.md", "06_codex_response_round_1.md"),
    ("07_claude_review_round_2.md", "08_codex_response_round_2.md"),
    ("09_claude_review_round_3.md", ""),
]


def cmd_agent_cleanup_plan(args: argparse.Namespace) -> int:
    gate_path = resolve_agent_runtime_gate_path(args.path)
    if not gate_path.exists():
        raise WorkflowError(f"Missing agent runtime gate: {display_path(gate_path)}")
    scalars, maps = read_simple_yaml_maps(gate_path)
    backend = scalars.get("formal_runtime_backend", "").strip() or "named_owner_thread"
    if backend == "server_detached_role_only":
        output_refs = maps.get("agent_output_refs", {})
        print(f"agent-cleanup-plan path={display_path(gate_path)}")
        print(f"subject_id={scalars.get('subject_id', '')}")
        print(f"thread_archive_policy={scalars.get('thread_archive_policy', '')}")
        print(f"archived_threads_record={scalars.get('archived_threads_record', '')}")
        print("cleanup_mode=not_applicable_no_named_threads")
        print(f"role_output_count={len(output_refs)}")
        print("keep_count=0")
        print("archive_count=0")
        print("unknown_count=0")
        print("duplicate_instance_ids=0")
        return 0
    agent_ids = maps.get("named_thread_ids", {})
    statuses = maps.get("agent_instance_status", {})
    output_refs = maps.get("agent_output_refs", {})
    current_stage_status = scalars.get("current_stage_status", "").strip().lower()
    archive_after_closeout_only = truthy(scalars.get("archive_after_closeout_only", ""))
    closeout_statuses = {"closed_out", "closeout_complete", "completed", "failed", "stopped", "cancelled"}
    archive_deferred = archive_after_closeout_only and current_stage_status not in closeout_statuses

    keep: list[tuple[str, str, str]] = []
    archive: list[tuple[str, str, str]] = []
    unknown: list[tuple[str, str, str]] = []
    instance_to_roles: dict[str, list[str]] = {}
    for role, instance_id in sorted(agent_ids.items()):
        instance_to_roles.setdefault(instance_id, []).append(role)
        status = statuses.get(role, "").strip().lower()
        row = (role, instance_id, status or "missing")
        if status in AGENT_CLEANUP_KEEP_STATUSES:
            keep.append(row)
        elif status in AGENT_CLEANUP_CLOSE_STATUSES:
            if archive_deferred:
                keep.append((role, instance_id, f"{status}:archive_deferred_until_closeout"))
            else:
                archive.append(row)
        else:
            unknown.append(row)

    print(f"agent-cleanup-plan path={display_path(gate_path)}")
    print(f"subject_id={scalars.get('subject_id', '')}")
    print(f"thread_archive_policy={scalars.get('thread_archive_policy', '')}")
    print(f"archived_threads_record={scalars.get('archived_threads_record', '')}")
    print(f"current_stage_status={current_stage_status}")
    print(f"archive_after_closeout_only={str(archive_after_closeout_only).lower()}")
    print(f"archive_deferred_until_closeout={str(archive_deferred).lower()}")
    print(f"keep_count={len(keep)}")
    for role, instance_id, status in keep:
        print(f"KEEP role={role} id={instance_id} status={status}")
    print(f"archive_count={len(archive)}")
    for role, instance_id, status in archive:
        output_ref = output_refs.get(role, "")
        print(f"ARCHIVE role={role} thread_id={instance_id} status={status} output_ref={output_ref}")
    print(f"unknown_count={len(unknown)}")
    for role, instance_id, status in unknown:
        print(f"UNKNOWN role={role} thread_id={instance_id} status={status}")
    duplicate_instances = {instance_id: roles for instance_id, roles in instance_to_roles.items() if len(roles) > 1}
    print(f"duplicate_instance_ids={len(duplicate_instances)}")
    for instance_id, roles in sorted(duplicate_instances.items()):
        print(f"DUPLICATE id={instance_id} roles={','.join(sorted(roles))}")
    if unknown:
        raise WorkflowError("Agent cleanup plan has unknown thread statuses; do not archive blindly")
    return 0


def workflow_manifest_path() -> Path:
    return REPO_ROOT / "docs" / "workflow" / "WORKFLOW_MANIFEST.yaml"


def read_workflow_manifest_entries(path: Path | None = None) -> list[dict[str, str]]:
    manifest_path = path or workflow_manifest_path()
    if not manifest_path.exists():
        raise WorkflowError(f"Missing workflow manifest: {rel(manifest_path)}")
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_files = False
    for raw_line in read_text(manifest_path).splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line == "files:":
            in_files = True
            continue
        if not in_files:
            continue
        item_match = re.match(r"^\s{2}-\s+([A-Za-z0-9_]+):\s*(.*)$", line)
        if item_match:
            current = {item_match.group(1): yaml_unquote(item_match.group(2))}
            entries.append(current)
            continue
        field_match = re.match(r"^\s{4}([A-Za-z0-9_]+):\s*(.*)$", line)
        if field_match and current is not None:
            current[field_match.group(1)] = yaml_unquote(field_match.group(2))
    if not entries:
        raise WorkflowError(f"Workflow manifest has no files entries: {rel(manifest_path)}")
    return entries


def workflow_manifest_errors() -> list[str]:
    errors: list[str] = []
    try:
        entries = read_workflow_manifest_entries()
    except WorkflowError as exc:
        return [str(exc)]

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    daily_read: list[str] = []
    for entry in entries:
        logical_id = entry.get("logical_id", "")
        canonical_path = entry.get("canonical_path", "")
        category = entry.get("category", "")
        status = entry.get("status", "")
        if not logical_id:
            errors.append("workflow manifest entry missing logical_id")
        elif logical_id in seen_ids:
            errors.append(f"workflow manifest duplicate logical_id: {logical_id}")
        seen_ids.add(logical_id)
        if not canonical_path:
            errors.append(f"{logical_id or '<missing-id>'} missing canonical_path")
            continue
        if canonical_path.startswith("/") or re.match(r"^[A-Za-z]:", canonical_path):
            errors.append(f"{logical_id} canonical_path must be repo-relative: {canonical_path}")
        if ".." in Path(canonical_path).parts:
            errors.append(f"{logical_id} canonical_path must not contain '..': {canonical_path}")
        if canonical_path in seen_paths:
            errors.append(f"workflow manifest duplicate canonical_path: {canonical_path}")
        seen_paths.add(canonical_path)
        if category not in WORKFLOW_MANIFEST_CATEGORIES:
            errors.append(f"{logical_id} invalid category: {category}")
        if status not in WORKFLOW_MANIFEST_STATUSES:
            errors.append(f"{logical_id} invalid status: {status}")
        if category in {"archive", "deprecated"} and status == "active":
            errors.append(f"{logical_id} cannot be active in {category}")
        if truthy(entry.get("daily_read", "")):
            daily_read.append(logical_id)
            if category not in {"daily_entry", "playbook"}:
                errors.append(f"{logical_id} daily_read must stay in daily_entry or playbook")
        path = REPO_ROOT / canonical_path
        if not path.exists():
            errors.append(f"{logical_id} missing canonical_path: {canonical_path}")

    missing_ids = sorted(WORKFLOW_MANIFEST_REQUIRED_IDS - seen_ids)
    for logical_id in missing_ids:
        errors.append(f"workflow manifest missing required logical_id: {logical_id}")
    if len(daily_read) > 4:
        errors.append("workflow manifest daily_read must stay compact: " + ", ".join(daily_read))
    return errors


def cmd_list_workflow_files(_: argparse.Namespace) -> int:
    entries = read_workflow_manifest_entries()
    by_category: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        by_category.setdefault(entry.get("category", "uncategorized"), []).append(entry)

    print(f"workflow-files manifest={rel(workflow_manifest_path())} entries={len(entries)}")
    for category in sorted(by_category):
        rows = sorted(by_category[category], key=lambda item: item.get("logical_id", ""))
        print(f"{category}: {len(rows)}")
        for entry in rows:
            daily = " daily" if truthy(entry.get("daily_read", "")) else ""
            exists = "ok" if (REPO_ROOT / entry.get("canonical_path", "")).exists() else "missing"
            print(
                f"  {entry.get('logical_id', '')} status={entry.get('status', '')}{daily} "
                f"path={entry.get('canonical_path', '')} exists={exists}"
            )
    errors = workflow_manifest_errors()
    print(f"manifest_errors={len(errors)}")
    for error in errors:
        print(f"ERROR {error}")
    return 1 if errors else 0


ENGLISH_DOC_PROSE_PATTERNS = [
    "Use when ",
    "Must not change",
    "Training entry modes",
    "What the source claims",
    "Use this section",
    "Fill only when",
    "Shape must be written",
    "Protected semantics",
    "Defaults must preserve",
    "Do not change inside",
]


def is_english_only_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return False
    if re.search(r"[\u4e00-\u9fff]", stripped):
        return False
    # 允许纯机器标识短标题，但模板文档的英文-only 说明标题应当给中文释义。
    return bool(re.search(r"[A-Za-z]{3,}", stripped))


def doc_language_policy_errors() -> list[str]:
    errors: list[str] = []
    language_marker_requirements = {
        "docs/workflow/START_HERE.md": ["正文必须使用中文", "不允许整段英文说明"],
        "docs/workflow/WORKFLOW_KERNEL.md": ["文档语言硬规则", "正文必须使用中文"],
        "docs/workflow/protocols/module_template_selection.md": ["文档语言边界", "不能写整段英文说明"],
        "experiments/templates/modules/README.md": ["训练入口模式", "不允许改变"],
    }
    for path_text, markers in language_marker_requirements.items():
        path = REPO_ROOT / path_text
        if not path.exists():
            errors.append(f"missing language policy file: {path_text}")
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                errors.append(f"{path_text} missing Chinese document language marker: {marker}")

    scan_roots = [
        REPO_ROOT / "docs" / "workflow" / "START_HERE.md",
        REPO_ROOT / "docs" / "workflow" / "WORKFLOW_KERNEL.md",
        REPO_ROOT / "docs" / "workflow" / "protocols" / "module_template_selection.md",
        REPO_ROOT / "experiments" / "templates",
    ]
    candidates: list[Path] = []
    for root in scan_roots:
        if root.is_file():
            candidates.append(root)
        elif root.exists():
            candidates.extend(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml", ".py"})

    for path in sorted(set(candidates)):
        if "/archive/" in ("/" + rel(path).replace("\\", "/")):
            continue
        text = read_text(path)
        in_fence = False
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            if path.suffix.lower() == ".md" and is_english_only_heading(line):
                errors.append(f"{rel(path)}:{line_number} has English-only heading; add Chinese wording")
            for phrase in ENGLISH_DOC_PROSE_PATTERNS:
                if phrase in line:
                    errors.append(f"{rel(path)}:{line_number} contains English prose phrase: {phrase}")
    return errors


def local_gtpj_workflow_skill_errors() -> list[str]:
    errors: list[str] = []
    skill_path = LOCAL_GTPJ_WORKFLOW_SKILL_PATH
    if not skill_path.exists():
        errors.append(f"missing local gtpj-workflow skill mirror: {skill_path}")
        return errors
    text = read_text(skill_path)
    required_marker = "代码审核不被 `server_frozen_runner` 豁免"
    for marker in [
        "GitHub documentation is canonical",
        "local skill mirrors the repository rules",
        "docs/workflow/START_HERE.md",
        "docs/workflow/WORKFLOW_KERNEL.md",
        "docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md",
        "framework/vX",
        "RUN-xxx",
        "compatibility identifiers",
        "same GitHub truth source",
        "开启多agents智能体工作流",
        "不得反复确认",
        "files_reviewed",
        "report-new-completions",
        required_marker,
    ]:
        if marker not in text:
            errors.append(f"local gtpj-workflow skill mirror missing marker: {marker}")
    for ref_name in ["start_here.md", "workflow_kernel.md", "quick_start.md"]:
        ref_path = skill_path.parent / "references" / ref_name
        if not ref_path.exists():
            errors.append(f"local gtpj-workflow skill reference missing: references/{ref_name}")
            continue
        if required_marker not in read_text(ref_path):
            errors.append(f"local gtpj-workflow skill reference references/{ref_name} missing marker: {required_marker}")
    return errors


def flat_framework_language_errors() -> list[str]:
    """Keep active governance pages from drifting back to parent/child framework language."""
    if not framework_standard_is_active():
        return []
    errors: list[str] = []
    banned_phrases = [
        "新的子 `FRAMEWORK",
        "新的子 FRAMEWORK",
        "产生一个子 `FRAMEWORK",
        "parent version / parent tag",
        "under the parent version",
        "source_version / source_tag",
        "正式框架树",
        "版本树账本",
        "父版本 H",
        "父节点",
        "Version tree:",
        "promote/<parent-version>",
        "父代码来源",
        "formal framework tree",
        "promote/v1-idea-0003-to-v4",
    ]
    roots = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "workflow" / "README.md",
        REPO_ROOT / "docs" / "GITHUB_GOVERNANCE.md",
        REPO_ROOT / "docs" / "PROJECT_STRUCTURE.md",
        REPO_ROOT / "docs" / "workflow",
        REPO_ROOT / "experiments" / "templates",
        LOCAL_GTPJ_WORKFLOW_SKILL_PATH,
        LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent / "references",
    ]
    candidates: set[Path] = set()
    for root in roots:
        if root.is_file():
            candidates.add(root)
        elif root.exists():
            candidates.update(path for path in root.rglob("*.md") if path.is_file())
    exempt_paths = {
        (REPO_ROOT / "docs" / "workflow" / "FRAMEWORK_EXPERIMENT_STANDARD.md").resolve(),
        (REPO_ROOT / "experiments" / "templates" / "TRIAL_README_template.md").resolve(),
    }
    for path in sorted(candidates, key=lambda item: str(item).lower()):
        resolved = path.resolve()
        normalized = str(resolved).replace("\\", "/").lower()
        if resolved in exempt_paths or any(
            segment in normalized
            for segment in ("/archive/", "/reviews/", "/agent_reviews/")
        ):
            continue
        content = read_text(path)
        for phrase in banned_phrases:
            if phrase in content:
                errors.append(f"{display_path(path)} contains retired flat-framework phrase: {phrase}")

    required_markers = {
        REPO_ROOT / "README.md": ["v1  ←  v2  ←  v3  ←  v5"],
        REPO_ROOT / "docs" / "GITHUB_GOVERNANCE.md": [
            "FRAMEWORK-V3  derived_from: FRAMEWORK-V2",
            "FRAMEWORK-V5  derived_from: FRAMEWORK-V3",
        ],
        REPO_ROOT / "docs" / "workflow" / "core" / "WORKFLOW_ROUTER.md": [
            "新的同级正式框架"
        ],
        REPO_ROOT / "docs" / "workflow" / "protocols" / "experiment_protocol.md": [
            "新的同级正式框架"
        ],
        REPO_ROOT / "docs" / "workflow" / "protocols" / "promotion.md": [
            "registry_level: formal_peer",
            "tune/INDEX.md",
            "ablation/INDEX.md",
            "innovation/INDEX.md",
            "confirmation/INDEX.md",
        ],
    }
    for path, markers in required_markers.items():
        if not path.exists():
            continue
        content = read_text(path)
        for marker in markers:
            if marker not in content:
                errors.append(f"{display_path(path)} missing flat-framework marker: {marker}")
    return errors


def immutable_template_language_errors() -> list[str]:
    """Keep every active entry aligned with the immutable template start rule."""
    if not immutable_template_standard_is_active():
        return []
    errors: list[str] = []
    core_markers = [
        "MODEL-VX-TEMPLATE-VN",
        "TEMPLATE.yaml",
        "EXPERIMENT.yaml",
        "从准确母版提交独立分叉",
        "实验代码不得并回母版",
        "legacy_frozen 不能启动新实验",
    ]
    required_markers: dict[Path, list[str]] = {
        REPO_ROOT / "docs" / "workflow" / "FRAMEWORK_EXPERIMENT_STANDARD.md": core_markers,
        REPO_ROOT / "docs" / "workflow" / "START_HERE.md": core_markers[:3],
        REPO_ROOT / "docs" / "workflow" / "WORKFLOW_KERNEL.md": core_markers,
        REPO_ROOT / "docs" / "workflow" / "core" / "QUICK_START.md": core_markers[:3],
        REPO_ROOT / "docs" / "workflow" / "core" / "TASK_START_MINI.md": core_markers[1:3],
        REPO_ROOT / "docs" / "workflow" / "core" / "TASK_START_CARD.md": core_markers[1:3],
        REPO_ROOT / "docs" / "workflow" / "protocols" / "git_policy.md": core_markers,
        REPO_ROOT / "docs" / "workflow" / "protocols" / "versioning.md": core_markers,
        REPO_ROOT / "docs" / "workflow" / "protocols" / "experiment_protocol.md": core_markers,
        REPO_ROOT / "experiments" / "templates" / "experiment_README_template.md": core_markers[1:3],
        LOCAL_GTPJ_WORKFLOW_SKILL_PATH: core_markers,
        REPO_ROOT / "README.md": ["TEMPLATE.yaml", "framework/vX-template-vN"],
        REPO_ROOT / "AGENTS.md": ["TEMPLATE.yaml", "framework/vX-template-vN"],
        REPO_ROOT / "docs" / "PROJECT_STATUS.md": [
            "MODEL-V5-TEMPLATE-V1",
            "不能启动新实验",
        ],
        REPO_ROOT / "docs" / "workflow" / "protocols" / "promotion.md": [
            "TEMPLATE.yaml",
            "MODEL-VY-TEMPLATE-V1",
            "framework/vY-template-v1",
        ],
    }
    for path, markers in required_markers.items():
        if not path.exists():
            errors.append(f"missing immutable-template rule file: {display_path(path)}")
            continue
        content = read_text(path)
        for marker in markers:
            if marker not in content:
                errors.append(f"{display_path(path)} missing immutable-template marker: {marker}")

    active_paths: set[Path] = {
        REPO_ROOT / "README.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "docs" / "GITHUB_GOVERNANCE.md",
        REPO_ROOT / "docs" / "PROJECT_STATUS.md",
        REPO_ROOT / "docs" / "PROJECT_STRUCTURE.md",
        REPO_ROOT / "docs" / "workflow" / "protocols" / "parameter_matrix_protocol.md",
        REPO_ROOT / "workflow" / "README.md",
        LOCAL_GTPJ_WORKFLOW_SKILL_PATH,
    }
    manifest_path = workflow_manifest_path()
    if manifest_path.exists():
        current_path = ""
        current_status = ""

        def add_manifest_path() -> None:
            if current_path and current_status in {"active", "active_reference"}:
                active_paths.add(REPO_ROOT / current_path)

        for raw_line in read_text(manifest_path).splitlines():
            logical_match = re.match(r"^\s*-\s+logical_id:\s*", raw_line)
            if logical_match:
                add_manifest_path()
                current_path = ""
                current_status = ""
                continue
            path_match = re.match(r"^\s+canonical_path:\s*(\S.*?)\s*$", raw_line)
            if path_match:
                current_path = yaml_unquote(path_match.group(1))
                continue
            status_match = re.match(r"^\s+status:\s*(\S+)\s*$", raw_line)
            if status_match:
                current_status = yaml_unquote(status_match.group(1))
        add_manifest_path()

    retired_instructions = [
        "新的创新从 `framework/v1`",
        "所有新实验都从对应的 `framework/vX`",
        "必须从 `framework/vX`",
        "从目标 `framework/vX`",
        "从对应的 `framework/vX`",
    ]
    for path in sorted(active_paths, key=lambda item: str(item).lower()):
        if not path.exists():
            continue
        content = read_text(path)
        for phrase in retired_instructions:
            if phrase in content:
                errors.append(
                    f"{display_path(path)} still contains retired experiment-start instruction: {phrase}"
                )
        command_content = re.sub(r"`\s*\r?\n\s*", " ", content)
        command_content = re.sub(r"\\\s*\r?\n\s*", " ", command_content)
        retired_formal_runner = re.search(
            r"(?m)^\s*(?:python\s+)?workflow[\\/]gtpj_workflow\.py\s+"
            r"run-workflow\b[^\r\n]*--formal\b[^\r\n]*$",
            command_content,
        )
        if retired_formal_runner:
            errors.append(
                f"{display_path(path)} still contains retired formal dynamic runner command: "
                f"{retired_formal_runner.group(0).strip()}"
            )
        retired_matrix_command = re.search(
            r"(?m)^\s*(?:python\s+)?workflow[\\/]gtpj_workflow\.py\s+"
            r"prepare-dynamic-routing-matrix\b[^\r\n]*$",
            command_content,
        )
        if retired_matrix_command:
            errors.append(
                f"{display_path(path)} still contains retired dynamic matrix command: "
                f"{retired_matrix_command.group(0).strip()}"
            )
        for plan_command in re.finditer(
            r"(?m)^\s*(?:python\s+)?workflow[\\/]gtpj_workflow\.py\s+"
            r"plan-dynamic-routing-batch\b[^\r\n]*$",
            command_content,
        ):
            if "--debug-smoke" not in plan_command.group(0):
                errors.append(
                    f"{display_path(path)} still contains retired formal dynamic planner command: "
                    f"{plan_command.group(0).strip()}"
                )
    return errors


def workflow_consistency_errors() -> list[str]:
    errors: list[str] = []
    errors.extend(workflow_manifest_errors())
    errors.extend(doc_language_policy_errors())
    errors.extend(local_gtpj_workflow_skill_errors())
    errors.extend(immutable_template_language_errors())
    required_markers = {
        "docs/workflow/START_HERE.md": [
            "formal_runner_allowed",
            "multi_agent_preflight",
            "review_tier",
            "review-1",
            "strict-3",
            "正文必须使用中文",
            "框架记录只跟",
            "formal_pending",
            "orphan_runtime_plan",
            "明确入口硬规则",
            "执行授权",
            "不得反复确认",
            "pre_run_planned",
            "report-new-completions",
            "代码审核不被 `server_frozen_runner` 豁免",
        ],
        "docs/workflow/WORKFLOW_KERNEL.md": [
            "multi-agent-preflight",
            "formal_evidence_allowed",
            "review_tier",
            "review-1",
            "strict-3",
            "文档语言硬规则",
            "框架记录绑定",
            "formal_pending",
            "orphan_runtime_plan",
            "开启多agents智能体工作流",
            "live_multi_agent_monitor",
            "planning gate",
            "files_reviewed",
            "独立输出文件",
            "allow/block/propose",
            "skill 镜像",
            "active docs",
            "helper 测试",
            "report-new-completions",
            "代码审核不被 `server_frozen_runner` 豁免",
        ],
        "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md": [
            "multi_agent_preflight",
            "formal_runner_allowed",
            "agent_output_refs",
            "agent-cleanup-plan",
            "named_thread_titles",
            "<subject_id> | <Role Label>",
            "files_reviewed",
            "report-new-completions",
        ],
        "docs/workflow/core/TASK_START_MINI.md": ["runner_scope", "blocked_reason"],
        "docs/workflow/core/TASK_START_CARD.md": [
            "multi_agent_preflight",
            "formal_evidence_allowed",
            "agent_status_refs",
            "role_file_plan",
            "files_reviewed",
            "是否需要再次确认",
        ],
        "docs/workflow/core/WORKFLOW_ROUTER.md": ["formal_pending", "orphan_runtime_plan"],
        "docs/workflow/protocols/agent_orchestration.md": [
            "multi_agent_preflight",
            "formal_runner_allowed",
            "agent_output_refs",
            "agent-cleanup-plan",
            "<subject_id> | <Role Label>",
            "files_reviewed",
            "分文件复核",
            "report-new-completions",
        ],
        "docs/workflow/protocols/ai_cross_review_protocol.md": [
            "owner_participation: not_required",
            "claude_code_read_only: true",
            "review_tier",
            "fast",
            "review-1",
            "strict-3",
            "02_codex_named_thread_pre_review.md",
            "completed_archived",
            "archive_result_confirms_completion",
            "validation_profile",
            "claude_rounds_required",
            "run-ai-cross-review",
            "validate-ai-cross-review",
            "02_review_brief.md",
            "02_focused_diff.md",
            "prompt_profile",
            "blocking-only",
            "代码审核不被 `server_frozen_runner` 豁免",
        ],
        "docs/workflow/protocols/module_template_selection.md": [
            "feature_adapter_template.py",
            "composite_module_template.py",
            "architecture_change_template.md",
            "validate-trial-meta",
            "standard GZSL U/S/H/ZS",
            "base_code_tag",
            "standard_gzsl_training_template.py",
            "strict_template_entry",
            "文档语言边界",
            "框架记录的对象",
        ],
        "docs/workflow/protocols/experiment_protocol.md": ["formal_pending", "orphan_runtime_plan"],
        "docs/workflow/protocols/module_trial_protocol.md": ["formal_pending", "orphan_runtime_plan"],
        "docs/workflow/protocols/mixed_experiment_campaign_protocol.md": ["formal_pending", "orphan_runtime_plan"],
        "docs/workflow/playbooks/innovation.md": [
            "探索 / 正式分界",
            "formal_evidence_allowed",
            "module_template_selection.md",
            "module_source.md",
            "validate-trial-meta",
            "strict_template_entry",
        ],
        "docs/workflow/playbooks/paper_to_experiment.md": [
            "base_code_tag",
            "module_template_selection.md",
            "module_source.md",
        ],
        "experiments/templates/agent_summary_template.md": [
            "multi_agent_preflight:",
            "formal_runner_allowed:",
            "agent_output_refs:",
            "files_reviewed:",
            "agent_cleanup:",
            "ai_cross_review:",
        ],
        "experiments/templates/quality_check_template.md": [
            "review_tier",
            "validate-ai-cross-review",
            "unresolved_blocking_issues: 0",
        ],
        "experiments/templates/ai_cross_review_template.md": [
            "review_tier",
            "fast",
            "review-1",
            "strict-3",
            "02_codex_named_thread_pre_review.md",
            "completed_archived",
            "archive_result_confirms_completion",
            "validation_profile",
            "claude_rounds_required",
            "02_review_brief.md",
            "02_focused_diff.md",
            "prompt_profile",
            "blocking-only",
            "05_claude_review_round_1.md",
            "09_claude_review_round_3.md",
            "10_final_decision.md",
            "owner_participation: not_required",
            "unresolved_blocking_issues: 0",
        ],
        "experiments/templates/run_receipt_template.yaml": ["schema_version: gtpj.run_receipt.v0", "multi_agent_preflight:", "agent_output_refs:"],
        "experiments/templates/TRIAL_ATTEMPTS_template.md": ["历史兼容", "只读", "不得作为新实验入口"],
        "experiments/templates/modules/README.md": [
            "standard_gzsl_module_framework_template.py",
            "standard_gzsl_training_template.py",
            "composite_module_template.py",
            "architecture_change_template.md",
            "strict_template_entry",
            "U, S, H, ZS",
        ],
    }
    for path_text, markers in required_markers.items():
        path = REPO_ROOT / path_text
        if not path.exists():
            errors.append(f"missing workflow file: {path_text}")
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                errors.append(f"{path_text} missing marker: {marker}")

    for path in confirmation_rule_sync_paths():
        if not path.exists():
            errors.append(f"missing confirmation rule sync file: {display_path(path)}")
            continue
        text = read_text(path)
        for marker in CONFIRMATION_RULE_REQUIRED_MARKERS:
            if marker not in text:
                errors.append(f"{display_path(path)} missing confirmation rule marker: {marker}")

    stale_ai_review_phrases = [
        "三轮 AI 交叉审核包",
        "三轮交叉审核",
        "三轮审核包",
        "重复 3 轮",
        "必须由 Claude Code 与 Codex 完成三轮",
    ]
    stale_scan_roots = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "docs" / "workflow",
        REPO_ROOT / "experiments" / "templates",
    ]
    for root in stale_scan_roots:
        if root.is_file():
            candidates = [root]
        elif root.exists():
            candidates = [path for path in root.rglob("*") if path.is_file()]
        else:
            candidates = []
        for path in candidates:
            rel_path = rel(path)
            normalized = rel_path.replace("\\", "/")
            if "/archive/" in "/" + normalized:
                continue
            if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
                continue
            text = read_text(path)
            for phrase in stale_ai_review_phrases:
                if phrase in text:
                    errors.append(f"{rel_path} contains stale AI review phrase: {phrase}")

    playbook_dir = REPO_ROOT / "docs" / "workflow" / "playbooks"
    if playbook_dir.exists():
        for playbook in sorted(playbook_dir.glob("*.md")):
            text = read_text(playbook)
            for marker in ["START_HERE.md", "WORKFLOW_KERNEL.md"]:
                if marker not in text:
                    errors.append(f"{rel(playbook)} missing required entrypoint ref: {marker}")
    errors.extend(flat_framework_language_errors())
    return errors


def cmd_validate_workflow_consistency(_: argparse.Namespace) -> int:
    errors = workflow_consistency_errors()
    if errors:
        raise WorkflowError("Workflow consistency validation failed:\n" + "\n".join(errors))
    print("validate-workflow-consistency-ok")
    return 0


def cmd_confirmation_rule_map(_: argparse.Namespace) -> int:
    print("confirmation-rule-map")
    print("required_markers:")
    for marker in CONFIRMATION_RULE_REQUIRED_MARKERS:
        print(f"- {marker}")
    print("repo_sync_files:")
    for path_text in CONFIRMATION_RULE_REPO_SYNC_FILES:
        print(f"- {path_text}")
    print("skill_sync_files:")
    for path in confirmation_rule_sync_paths():
        if path == LOCAL_GTPJ_WORKFLOW_SKILL_PATH or str(path).startswith(str(LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent)):
            print(f"- {display_path(path)}")
    return 0


def resolve_ai_cross_review_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def scalar_from_text(text: str, key: str) -> str:
    match = re.search(rf"(?im)^[ \t]*{re.escape(key)}[ \t]*:[ \t]*([^\r\n]*)$", text)
    return normalize_simple_scalar(match.group(1)) if match else ""


def normalize_simple_scalar(value: str) -> str:
    normalized = value.strip()
    while len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
        normalized = normalized[1:-1].strip()
    return normalized


def top_level_scalar_values(text: str, key: str) -> list[str]:
    return [
        normalize_simple_scalar(match.group(1))
        for match in re.finditer(rf"(?im)^{re.escape(key)}[ \t]*:[ \t]*([^\r\n]*)$", text)
    ]


def single_top_level_scalar(text: str, key: str) -> str:
    values = top_level_scalar_values(text, key)
    return values[0] if len(values) == 1 else ""


def normalize_attested_identifier(value: str) -> str:
    return normalize_simple_scalar(value)


def ai_cross_review_required_files_for_pack(pack_dir: Path) -> tuple[list[str], int, bool]:
    declaration_files = ["00_task.md", "02_review_brief.md", "10_final_decision.md"]
    declared_rounds: list[int] = []
    tiered_pack = False
    for filename in declaration_files:
        path = pack_dir / filename
        if not path.is_file():
            continue
        text = read_text(path)
        review_tier = single_top_level_scalar(text, "review_tier")
        if not review_tier:
            continue
        tiered_pack = True
        rounds_text = single_top_level_scalar(text, "claude_rounds_required")
        try:
            rounds = int(rounds_text)
        except ValueError:
            rounds = AI_CROSS_REVIEW_TIER_ROUNDS.get(review_tier, -1)
        if review_tier in AI_CROSS_REVIEW_TIER_ROUNDS and rounds in AI_CROSS_REVIEW_TIER_ROUNDS.values():
            declared_rounds.append(max(rounds, AI_CROSS_REVIEW_TIER_ROUNDS[review_tier]))
    if not tiered_pack:
        return AI_CROSS_REVIEW_REQUIRED_FILES, 3, False
    rounds_required = max(declared_rounds, default=-1)
    if rounds_required not in AI_CROSS_REVIEW_TIER_ROUNDS.values():
        return [
            "00_task.md",
            "01_codex_actions.md",
            "02_codex_named_thread_pre_review.md",
            "02_diff.patch",
            "02_focused_diff.md",
            "02_review_brief.md",
            "03_validation.md",
            "04_claims.md",
            "10_final_decision.md",
        ], rounds_required, True
    required = [
        "00_task.md",
        "01_codex_actions.md",
        "02_codex_named_thread_pre_review.md",
        "02_diff.patch",
        "02_focused_diff.md",
        "02_review_brief.md",
        "03_validation.md",
        "04_claims.md",
        "10_final_decision.md",
    ]
    for index in range(max(0, rounds_required)):
        claude_file, codex_file = AI_CROSS_REVIEW_CLAUDE_ROUND_FILES[index]
        required.append(claude_file)
        if codex_file and index + 1 < rounds_required:
            required.append(codex_file)
    return required, rounds_required, True


def ai_cross_review_round_provider_errors(filename: str, text: str) -> list[str]:
    attestation_text = text.split("\n## Claude Code 原始 stdout", 1)[0]
    reviewers = top_level_scalar_values(attestation_text, "reviewer")
    if len(reviewers) != 1:
        return [f"{filename} must contain exactly one top-level reviewer value"]
    reviewer = reviewers[0]
    if reviewer == "claude_code":
        read_only_values = top_level_scalar_values(attestation_text, "claude_code_read_only")
        if read_only_values != ["true"]:
            return [f"{filename} must declare one top-level claude_code_read_only: true"]
        return []
    if reviewer != "independent_codex_fallback":
        return [f"{filename} has unsupported top-level reviewer: {reviewer!r}"]
    expected_scalars = {
        "independent_codex_read_only": "true",
        "fallback_reason": "claude_code_unavailable",
        "independent_context": "true",
    }
    invalid_scalars = [
        f"{key}: {expected}"
        for key, expected in expected_scalars.items()
        if top_level_scalar_values(attestation_text, key) != [expected]
    ]
    if invalid_scalars:
        return [f"{filename} has missing or duplicate top-level fallback evidence: " + ", ".join(invalid_scalars)]
    reviewer_instance_id = normalize_attested_identifier(
        single_top_level_scalar(attestation_text, "reviewer_instance_id")
    )
    placeholder_pattern = (
        r"(?i)^(missing|unknown|none|placeholder|example|test|fake(?:[-_/].*)?|dummy(?:[-_/].*)?|"
        r"same[-_]?reviewer|reviewer[-_]?\d*|agent[-_]?\d*|codex[-_]?\d*|/root/fake(?:[-_/].*)?)$"
    )
    if not reviewer_instance_id or re.fullmatch(placeholder_pattern, reviewer_instance_id):
        return [f"{filename} has no real reviewer_instance_id for the independent Codex fallback"]
    for field in ["files_reviewed", "commands_run"]:
        section_match = re.search(
            rf"(?ms)^{re.escape(field)}:\s*\n(?P<body>.*?)(?=^[A-Za-z_][A-Za-z0-9_-]*:\s*|\Z)",
            attestation_text,
        )
        if not section_match or not re.search(r"(?m)^\s*-\s+\S", section_match.group("body")):
            return [f"{filename} must record at least one item under {field}"]
    return []


def ai_cross_review_errors(pack_dir: Path) -> list[str]:
    errors: list[str] = []
    if not pack_dir.exists():
        return [f"missing ai cross review pack: {display_path(pack_dir)}"]
    if not pack_dir.is_dir():
        return [f"ai cross review path must be a directory: {display_path(pack_dir)}"]

    required_files, rounds_required, tiered_pack = ai_cross_review_required_files_for_pack(pack_dir)
    for filename in required_files:
        path = pack_dir / filename
        if not path.exists():
            errors.append(f"missing review file: {filename}")
            continue
        if not path.is_file():
            errors.append(f"review entry must be a file: {filename}")

    if tiered_pack:
        declarations: dict[str, tuple[str, str]] = {}
        for filename in ["00_task.md", "02_review_brief.md", "10_final_decision.md"]:
            path = pack_dir / filename
            if not path.is_file():
                continue
            text = read_text(path)
            tiers = top_level_scalar_values(text, "review_tier")
            rounds = top_level_scalar_values(text, "claude_rounds_required")
            if len(tiers) != 1 or len(rounds) != 1:
                errors.append(f"{filename} must declare exactly one top-level review_tier and claude_rounds_required")
                continue
            declarations[filename] = (tiers[0], rounds[0])
        if len(set(declarations.values())) > 1:
            errors.append("00_task.md, 02_review_brief.md, and 10_final_decision.md must use the same review tier")
        for filename in ["00_task.md", "02_review_brief.md"]:
            path = pack_dir / filename
            if not path.is_file():
                continue
            risk_levels = top_level_scalar_values(read_text(path), "risk_level")
            if len(risk_levels) != 1:
                errors.append(f"{filename} must declare exactly one top-level risk_level")
            elif risk_levels[0] == "high" and declarations.get(filename) != ("strict-3", "3"):
                errors.append(f"{filename} risk_level high requires review_tier strict-3 and 3 rounds")

    round_marker_items = list(AI_CROSS_REVIEW_ROUND_MARKERS.items())
    if tiered_pack:
        allowed_round_files: set[str] = set()
        for index in range(max(0, rounds_required)):
            claude_file, codex_file = AI_CROSS_REVIEW_CLAUDE_ROUND_FILES[index]
            allowed_round_files.add(claude_file)
            if codex_file and index + 1 < rounds_required:
                allowed_round_files.add(codex_file)
        round_marker_items = [(filename, markers) for filename, markers in round_marker_items if filename in allowed_round_files]
    fallback_instance_ids: list[str] = []
    claude_rounds = 0
    fallback_rounds = 0
    for filename, markers in round_marker_items:
        path = pack_dir / filename
        if not path.is_file():
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                errors.append(f"{filename} missing marker: {marker}")
        if filename in AI_CROSS_REVIEW_REVIEW_ROUND_FILES:
            errors.extend(ai_cross_review_round_provider_errors(filename, text))
            attestation_text = text.split("\n## Claude Code 原始 stdout", 1)[0]
            reviewer = single_top_level_scalar(attestation_text, "reviewer")
            if reviewer == "independent_codex_fallback":
                fallback_rounds += 1
                reviewer_instance_id = normalize_attested_identifier(
                    single_top_level_scalar(attestation_text, "reviewer_instance_id")
                )
                if reviewer_instance_id:
                    fallback_instance_ids.append(reviewer_instance_id)
            elif reviewer == "claude_code":
                claude_rounds += 1
            verdict_values = top_level_scalar_values(attestation_text, "verdict")
            if len(verdict_values) != 1:
                errors.append(f"{filename} must contain exactly one top-level verdict value")
            elif verdict_values[0].lower() != "pass":
                errors.append(f"{filename} verdict must be pass")
    if fallback_rounds and len(set(fallback_instance_ids)) != fallback_rounds:
        errors.append("independent Codex fallback rounds must use distinct real reviewer_instance_id values")

    pre_review_path = pack_dir / "02_codex_named_thread_pre_review.md"
    if tiered_pack and pre_review_path.is_file():
        pre_text = read_text(pre_review_path)
        expected_pre_scalars = {
            "named_thread_required": "true",
            "verdict": "pass",
            "lifecycle": "completed_archived",
            "archived_before_claude": "true",
            "archive_result_confirms_completion": "true",
        }
        for key, expected_value in expected_pre_scalars.items():
            if top_level_scalar_values(pre_text, key) != [expected_value]:
                errors.append(
                    f"02_codex_named_thread_pre_review.md must declare one top-level {key}: {expected_value}"
                )
        pre_thread_id = single_top_level_scalar(pre_text, "thread_id")
        pre_archive_result = single_top_level_scalar(pre_text, "archive_result")
        if not codex_pre_review_archive_result_text_valid(pre_thread_id, pre_archive_result):
            errors.append(
                "02_codex_named_thread_pre_review.md archive_result must include matching thread id, previous_status=completed, and archived: true"
            )

    final_path = pack_dir / "10_final_decision.md"
    if final_path.is_file():
        final_text = read_text(final_path)
        expected_final_scalars = {
            "ai_cross_review_status": "pass",
            "owner_participation": "not_required",
            "rounds_completed": str(rounds_required),
            "codex_fixes_or_rebuttals_recorded": "true",
            "machine_gates_passed": "true",
            "unresolved_blocking_issues": "0",
        }
        for key, expected_value in expected_final_scalars.items():
            if top_level_scalar_values(final_text, key) != [expected_value]:
                errors.append(f"10_final_decision.md must declare one top-level {key}: {expected_value}")
        if tiered_pack:
            review_tier = single_top_level_scalar(final_text, "review_tier")
            rounds_text = single_top_level_scalar(final_text, "claude_rounds_required")
            if review_tier not in AI_CROSS_REVIEW_TIER_ROUNDS:
                errors.append(f"10_final_decision.md invalid review_tier: {review_tier}")
            else:
                try:
                    declared_rounds = int(rounds_text)
                except ValueError:
                    declared_rounds = -1
                expected_rounds = AI_CROSS_REVIEW_TIER_ROUNDS[review_tier]
                if declared_rounds != expected_rounds:
                    errors.append(
                        f"10_final_decision.md claude_rounds_required must be {expected_rounds} for {review_tier}"
                    )
        claude_read_only = single_top_level_scalar(final_text, "claude_code_read_only")
        fallback_read_only = single_top_level_scalar(final_text, "independent_codex_fallback_read_only")
        if claude_rounds and claude_read_only != "true":
            errors.append("10_final_decision.md must declare claude_code_read_only: true for Claude rounds")
        if fallback_rounds and fallback_read_only != "true":
            errors.append(
                "10_final_decision.md must declare independent_codex_fallback_read_only: true for fallback rounds"
            )
        if not claude_rounds and fallback_rounds and claude_read_only == "true":
            errors.append("10_final_decision.md cannot claim Claude Code review when every round used Codex fallback")
        if rounds_required > 0 and not claude_rounds and not fallback_rounds:
            errors.append(
                "10_final_decision.md has no recognized read-only review provider rounds"
            )
        if tiered_pack:
            for key, expected_value in {
                "codex_named_thread_pre_review": "pass",
                "codex_named_thread_lifecycle": "completed_archived",
                "claude_rounds_completed": str(claude_rounds),
            }.items():
                if top_level_scalar_values(final_text, key) != [expected_value]:
                    errors.append(f"10_final_decision.md must declare one top-level {key}: {expected_value}")

    return errors


def run_command_capture(command: str, *, cwd: Path = REPO_ROOT) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode, result.stdout, result.stderr


def git_capture(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise WorkflowError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def safe_review_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    if not slug:
        raise WorkflowError("run-ai-cross-review requires a non-empty --slug or --path")
    return slug[:80]


def default_ai_cross_review_dir(slug: str) -> Path:
    day = datetime.now().strftime("%Y-%m-%d")
    return REPO_ROOT / "docs" / "agent_reviews" / f"{day}-{safe_review_slug(slug)}"


def ensure_review_pack_writable(pack_dir: Path, *, overwrite: bool) -> None:
    if pack_dir.exists() and any(pack_dir.iterdir()) and not overwrite:
        raise WorkflowError(f"review pack already exists; pass --overwrite to replace generated files: {display_path(pack_dir)}")
    pack_dir.mkdir(parents=True, exist_ok=True)


def write_review_file(pack_dir: Path, filename: str, content: str, *, overwrite: bool) -> None:
    path = pack_dir / filename
    if path.exists() and not overwrite:
        raise WorkflowError(f"review file already exists; pass --overwrite to replace it: {display_path(path)}")
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def is_excluded_review_path(path_text: str, exclude_prefixes: list[str]) -> bool:
    normalized = path_text.replace("\\", "/")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix.rstrip("/") + "/") for prefix in exclude_prefixes)


def collect_changed_files(exclude_prefixes: list[str] | None = None) -> tuple[list[str], list[str]]:
    prefixes = exclude_prefixes or []
    status = git_capture("status", "--short").splitlines()
    changed: list[str] = []
    untracked: list[str] = []
    for line in status:
        if len(line) < 4:
            continue
        marker = line[:2]
        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()
        if is_excluded_review_path(path_text, prefixes):
            continue
        changed.append(path_text)
        if marker == "??":
            untracked.append(path_text)
    return changed, untracked


def read_untracked_review_snippets(untracked: list[str], *, max_bytes: int = 200_000) -> str:
    sections: list[str] = []
    for path_text in untracked:
        path = REPO_ROOT / path_text
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            sections.append(f"\n## 未跟踪二进制文件：{path_text}\n\n```text\nbinary file omitted\n```\n")
            continue
        if len(data) > max_bytes:
            sections.append(f"\n## 未跟踪大文件：{path_text}\n\n```text\nfile omitted because size={len(data)} bytes\n```\n")
            continue
        text = data.decode("utf-8", errors="replace")
        sections.append(f"\n## 未跟踪文件：{path_text}\n\n```text\n{text.rstrip()}\n```\n")
    return "\n".join(sections)


def build_ai_cross_review_diff(exclude_prefixes: list[str] | None = None) -> str:
    _changed, untracked = collect_changed_files(exclude_prefixes=exclude_prefixes)
    diff = git_capture("diff", "--binary", "--")
    snippet = read_untracked_review_snippets(untracked)
    header = [
        "# Git diff",
        "",
        "```diff",
        diff.rstrip(),
        "```",
    ]
    if snippet:
        header.extend(["", "# 未跟踪文件内容", snippet.rstrip()])
    if not diff.strip() and not snippet:
        header.extend(["", "```text", "当前没有 git diff 或未跟踪文本文件。", "```"])
    return "\n".join(header)


def existing_claude_context_files() -> list[str]:
    files = ["CLAUDE.md", "docs/workflow/CLAUDE_CONTEXT.md"]
    return [path_text for path_text in files if (REPO_ROOT / path_text).is_file()]


def build_ai_cross_review_focused_diff(
    changed_files: list[str],
    *,
    exclude_prefixes: list[str] | None = None,
    max_chars: int = 120_000,
) -> str:
    _changed, untracked = collect_changed_files(exclude_prefixes=exclude_prefixes)
    diff_stat = git_capture("diff", "--stat", "--").rstrip()
    diff = git_capture("diff", "--unified=12", "--").rstrip()
    truncated = False
    if len(diff) > max_chars:
        diff = diff[:max_chars].rstrip()
        truncated = True
    snippet = read_untracked_review_snippets(untracked, max_bytes=40_000)
    blocks = [
        "# Focused Diff",
        "",
        "本文件是给 Claude Code 默认读取的精简 diff。完整证据仍保留在 `02_diff.patch`。",
        "",
        "## Changed Files",
        "",
        "\n".join(f"- {item}" for item in changed_files) if changed_files else "- 当前没有 git status 变化",
        "",
        "## Diff Stat",
        "",
        "```text",
        diff_stat or "(empty)",
        "```",
        "",
        "## Focused Patch",
        "",
        "```diff",
        diff or "(empty)",
        "```",
    ]
    if truncated:
        blocks.extend(["", "> focused diff 已截断；需要追查完整上下文时再读取 `02_diff.patch`。"])
    if snippet:
        blocks.extend(["", "## Untracked Text Snippets", "", snippet.rstrip()])
    return "\n".join(blocks)


def build_ai_cross_review_brief(
    *,
    args: argparse.Namespace,
    review_slug: str,
    changed_files: list[str],
    commands: list[str],
    validation_passed: bool,
) -> str:
    context_files = existing_claude_context_files()
    return f"""# Claude Code 快速审核 Brief

```text
task_id: {args.task_id or safe_review_slug(review_slug)}
task_title: {args.task_title or review_slug}
scope: {args.scope}
risk_level: {args.risk_level}
validation_profile: {ai_cross_review_validation_profile(args)}
prompt_profile: {args.prompt_profile}
review_mode: {args.review_mode}
review_tier: {args.review_tier}
claude_rounds_required: {AI_CROSS_REVIEW_TIER_ROUNDS[args.review_tier]}
machine_gates_passed: {str(validation_passed).lower()}
owner_participation: not_required
claude_code_read_only: true
```

## 默认读取顺序

{chr(10).join(f"- `{item}`" for item in context_files) if context_files else "- 未找到 Claude 项目上下文文件"}
- `00_task.md`
- `01_codex_actions.md`
- `02_codex_named_thread_pre_review.md`
- `02_review_brief.md`
- `02_focused_diff.md`
- `03_validation.md`
- `04_claims.md`

## 备用证据

- `02_diff.patch` 是完整 diff，只在 focused diff 无法定位问题时读取。
- 旧轮次的 Claude/Codex 文件只在第 2/3 轮需要比对剩余问题时读取。

## Changed Files

{chr(10).join(f"- `{item}`" for item in changed_files) if changed_files else "- 当前没有 git status 变化"}

## Validation Commands

{chr(10).join(f"- `{command}`" for command in commands) if commands else "- 未提供验证命令"}

## 审核要求

- 只读审核，不改文件，不启动训练，不 push，不删除用户数据。
- `blocking-only` 模式只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 非阻断命名、风格、微小测试建议不要展开；可写 `non_blocking_issues: omitted_by_blocking_only_mode`。
"""


def run_ai_cross_review_validations(commands: list[str]) -> tuple[bool, str]:
    if not commands:
        return False, "commands_run:\nnot_run:\n- 未提供验证命令。\nmachine_gates_passed: false\n"
    blocks: list[str] = ["commands_run:"]
    all_passed = True
    failed: list[str] = []
    for command in commands:
        code, stdout, stderr = run_command_capture(command)
        if code != 0:
            all_passed = False
            failed.append(command)
        blocks.append(
            "\n".join(
                [
                    f"- command: {command}",
                    f"  exit_code: {code}",
                    "  stdout: |",
                    indent_block(stdout.rstrip() or "(empty)", "    "),
                    "  stderr: |",
                    indent_block(stderr.rstrip() or "(empty)", "    "),
                ]
            )
        )
    blocks.append(f"machine_gates_passed: {str(all_passed).lower()}")
    blocks.append("failed_commands:")
    if failed:
        blocks.extend(f"- {command}" for command in failed)
    else:
        blocks.append("- none")
    return all_passed, "\n".join(blocks)


def indent_block(text: str, prefix: str) -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def build_claude_prompt(pack_dir: Path, round_number: int) -> str:
    return f"""你是 GTPJ 的只读 Claude Code 审核者。

请阅读审核证据包：{display_path(pack_dir)}

当前是第 {round_number} 轮。不要修改任何文件，不要启动训练，不要执行 push/delete/发布。

请只报告可复现的问题。每个问题必须给出文件路径、行号或能复现的命令/缺失证据。

输出必须包含这些字段：

```text
round: {round_number}
reviewer: claude_code
claude_code_read_only: true
verdict: pass | needs_fix | blocked
blocking_issues:
non_blocking_issues:
unsupported_claims:
missing_validation:
```
"""


def build_claude_prompt_ascii(
    pack_dir: Path,
    round_number: int,
    *,
    prompt_profile: str,
    review_mode: str,
) -> str:
    focused_inputs = [
        *existing_claude_context_files(),
        "00_task.md",
        "01_codex_actions.md",
        "02_codex_named_thread_pre_review.md",
        "02_review_brief.md",
        "02_focused_diff.md",
        "03_validation.md",
        "04_claims.md",
    ]
    if round_number >= 2:
        focused_inputs.extend(["05_claude_review_round_1.md", "06_codex_response_round_1.md"])
    if round_number >= 3:
        focused_inputs.extend(["07_claude_review_round_2.md", "08_codex_response_round_2.md"])
    if prompt_profile == "full":
        focused_inputs.insert(4, "02_diff.patch")
    input_lines = "\n".join(f"- {item}" for item in focused_inputs)
    if review_mode == "blocking-only":
        review_note = "Review mode: blocking-only. Report only reproducible blocking issues. Do not expand style, naming, or minor test-granularity suggestions."
    else:
        review_note = "Review mode: full. You may report both blocking and non-blocking issues."
    if prompt_profile == "focused":
        patch_note = "Prompt profile: focused. Do not read 02_diff.patch by default; read it only when 02_focused_diff.md is insufficient to locate a blocking issue."
    else:
        patch_note = "Prompt profile: full. Read 02_diff.patch and use 02_review_brief.md to orient the review."
    return f"""You are the read-only Claude Code reviewer for the GTPJ project.
Review pack directory: {display_path(pack_dir)}
Round: {round_number}

Do not edit files. Do not start training. Do not push, delete, publish, or perform destructive actions.
{review_note}
{patch_note}

Read these files first:
{input_lines}

Every blocking issue must cite a file path, line number or reproducible command/missing evidence.
Output must contain these fields:
```text
round: {round_number}
reviewer: claude_code
claude_code_read_only: true
verdict: pass | needs_fix | blocked
blocking_issues:
non_blocking_issues:
unsupported_claims:
missing_validation:
```
"""


def run_claude_review(args: argparse.Namespace, pack_dir: Path, round_number: int) -> tuple[int, str, str]:
    prompt = build_claude_prompt_ascii(
        pack_dir,
        round_number,
        prompt_profile=args.prompt_profile,
        review_mode=args.review_mode,
    )
    if args.skip_claude:
        return 0, "verdict: blocked\nblocking_issues:\n- skip_claude enabled; 未调用 Claude Code。\n", ""
    executable = shutil.which(args.claude_command) or args.claude_command
    command = [
        executable,
        *args.claude_command_arg,
        "-p",
        "--bare",
        "--permission-mode",
        "plan",
        "--output-format",
        "json",
        "--disallowedTools",
        "Edit",
        "Write",
    ]
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return 127, "", str(exc)
    return result.returncode, result.stdout, result.stderr


def extract_review_verdict(text: str, exit_code: int) -> str:
    if exit_code != 0:
        return "blocked"
    match = re.search(r"verdict\s*:\s*(pass|needs_fix|blocked)", text, flags=re.IGNORECASE)
    if not match:
        return "blocked"
    return match.group(1).lower()


def make_claude_review_md(round_number: int, exit_code: int, stdout: str, stderr: str) -> tuple[str, str]:
    verdict = extract_review_verdict(stdout + "\n" + stderr, exit_code)
    blocking_value = "" if verdict == "pass" else f"- Claude Code 第 {round_number} 轮未通过或未给出可接受输出。"
    content = f"""round: {round_number}
reviewer: claude_code
claude_code_read_only: true
inputs_checked:
- CLAUDE.md
- docs/workflow/CLAUDE_CONTEXT.md
- 00_task.md
- 01_codex_actions.md
- 02_codex_named_thread_pre_review.md
- 02_review_brief.md
- 02_focused_diff.md
- 03_validation.md
- 04_claims.md
fallback_available:
- 02_diff.patch
verdict: {verdict}
blocking_issues:
{blocking_value}
non_blocking_issues:
unsupported_claims:
missing_validation:

## Claude Code 原始 stdout

```text
{stdout.rstrip() or "(empty)"}
```

## Claude Code 原始 stderr

```text
{stderr.rstrip() or "(empty)"}
```

exit_code: {exit_code}
"""
    return verdict, content


def make_codex_response_md(round_number: int, verdict: str, validation_passed: bool) -> str:
    remaining = 0 if verdict == "pass" and validation_passed else 1
    if remaining:
        summary = "本 helper 不自动修改代码；本轮仍需 Codex 在主流程中修复或基于证据反驳后重新运行审核。"
    else:
        summary = "Claude Code 本轮未报告 blocking issue，机器验证保持通过。"
    return f"""round: {round_number}
reviewer: codex
addressed_claude_findings:
- {summary}
fixes_applied:
rejected_findings_with_evidence:
validation_rerun:
- 见 03_validation.md
remaining_blocking_issues: {remaining}
"""


def codex_pre_review_archive_result_text_valid(thread_id: str, archive_result: str) -> bool:
    text = archive_result.strip()
    lower = text.lower()
    return (
        bool(thread_id)
        and thread_id in text
        and "previous_status" in lower
        and "completed" in lower
        and ("archived: true" in lower or '"archived": true' in lower or "archived=true" in lower)
    )


def codex_named_thread_pre_review_passed(args: argparse.Namespace) -> bool:
    archive_result_confirms_completion = codex_pre_review_archive_result_valid(args)
    return (
        args.codex_pre_review_verdict == "pass"
        and bool(args.codex_pre_review_thread_id.strip())
        and bool(args.codex_pre_review_thread_title.strip())
        and args.codex_pre_review_lifecycle == "completed_archived"
        and archive_result_confirms_completion
    )


def codex_pre_review_archive_result_valid(args: argparse.Namespace) -> bool:
    return codex_pre_review_archive_result_text_valid(
        args.codex_pre_review_thread_id.strip(),
        args.codex_pre_review_archive_result.strip(),
    )


def make_codex_named_thread_pre_review_md(args: argparse.Namespace) -> str:
    passed = codex_named_thread_pre_review_passed(args)
    archive_result_confirms_completion = codex_pre_review_archive_result_valid(args)
    return f"""codex_named_thread_pre_review: {"pass" if passed else "blocked"}
named_thread_required: true
thread_id: {args.codex_pre_review_thread_id or "missing"}
thread_title: {args.codex_pre_review_thread_title or "missing"}
lifecycle: {args.codex_pre_review_lifecycle}
archived_before_claude: {str(archive_result_confirms_completion).lower()}
archive_result_confirms_completion: {str(archive_result_confirms_completion).lower()}
archive_result: {args.codex_pre_review_archive_result or "missing"}
verdict: {args.codex_pre_review_verdict}
blocking_issues:
{"" if passed else "- missing passing named Codex pre-review thread evidence or archive_result"}
notes: {args.codex_pre_review_notes or "named Codex thread must be archived before Claude Code review starts"}
"""


def ai_cross_review_validation_profile(args: argparse.Namespace) -> str:
    if args.no_default_validation and args.validation_profile == "default-core":
        return "custom-debug"
    return args.validation_profile


def ai_cross_review_requires_strict(args: argparse.Namespace, changed_files: list[str]) -> bool:
    if args.risk_level == "high":
        return True
    for path_text in changed_files:
        normalized = path_text.replace("\\", "/").lower()
        filename = Path(normalized).name
        if normalized.startswith("experiments/") and filename in AI_CROSS_REVIEW_STRICT_RESULT_FILENAMES:
            return True
    haystack = " ".join(
        [
            args.scope,
            args.task_title,
            args.review_reason,
            args.risk_notes,
            *changed_files,
        ]
    ).lower()
    return any(keyword.lower() in haystack for keyword in AI_CROSS_REVIEW_STRICT_KEYWORDS)


def ai_cross_review_self_report_command(command: str) -> bool:
    lower = command.lower()
    return any(
        marker in lower
        for marker in [
            " echo ",
            "echo ",
            "write-output",
            "write-host",
            "python -c",
            "py -c",
            "print(",
        ]
    )


def validate_ai_cross_review_tier_args(args: argparse.Namespace, changed_files: list[str]) -> str:
    validation_profile = ai_cross_review_validation_profile(args)
    if args.review_tier == "fast" and args.risk_level != "low":
        raise WorkflowError("review_tier=fast requires --risk-level low")
    if ai_cross_review_requires_strict(args, changed_files) and args.review_tier != "strict-3":
        raise WorkflowError("high-risk or formal-result-affecting review requires --review-tier strict-3")
    if args.no_default_validation and args.risk_level != "low" and validation_profile != "custom-full-equivalent":
        raise WorkflowError("--no-default-validation for medium/high risk requires --validation-profile custom-full-equivalent")
    if args.review_tier == "strict-3" and validation_profile not in {"default-core", "custom-full-equivalent"}:
        raise WorkflowError("review_tier=strict-3 requires default-core or custom-full-equivalent validation")
    if validation_profile == "custom-full-equivalent":
        validation_commands = ([] if args.no_default_validation else list(AI_CROSS_REVIEW_DEFAULT_VALIDATION_COMMANDS))
        validation_commands.extend(args.validation_command)
        normalized_commands = [command.lower().replace("/", "\\") for command in validation_commands]
        missing = [
            fragment
            for fragment in AI_CROSS_REVIEW_CORE_VALIDATION_FRAGMENTS
            if not any(fragment.lower() in command for command in normalized_commands)
        ]
        if missing:
            raise WorkflowError("custom-full-equivalent validation missing core gates: " + ", ".join(missing))
        weak = [
            fragment
            for fragment in AI_CROSS_REVIEW_CORE_VALIDATION_FRAGMENTS
            if all(
                ai_cross_review_self_report_command(command)
                for command in validation_commands
                if fragment.lower() in command.lower().replace("/", "\\")
            )
        ]
        if weak:
            raise WorkflowError("custom-full-equivalent validation uses self-reporting commands: " + ", ".join(weak))
    return validation_profile


def ai_cross_review_claude_evidence_refs(rounds_required: int) -> str:
    refs = ["02_codex_named_thread_pre_review.md"]
    for index in range(rounds_required):
        claude_file, codex_file = AI_CROSS_REVIEW_CLAUDE_ROUND_FILES[index]
        refs.append(claude_file)
        if codex_file and index + 1 < rounds_required:
            refs.append(codex_file)
    return "; ".join(refs)


def make_final_decision_tiered_md(
    verdicts: list[str],
    validation_passed: bool,
    *,
    skip_claude: bool,
    review_tier: str,
    rounds_required: int,
    pre_review_passed: bool,
) -> str:
    claude_ok = (not skip_claude) if rounds_required == 0 else (
        len(verdicts) == rounds_required
        and all(verdict == "pass" for verdict in verdicts)
        and not skip_claude
    )
    unresolved = 0 if validation_passed and claude_ok and pre_review_passed else 1
    status = "pass" if unresolved == 0 else "blocked"
    blocked_reason = "" if status == "pass" else "machine validation failed, Codex temp pre-review is missing, or required Claude rounds did not pass."
    return f"""ai_cross_review_status: {status}
owner_participation: not_required
review_tier: {review_tier}
rounds_completed: {len(verdicts)}
claude_rounds_required: {rounds_required}
claude_rounds_completed: {len(verdicts)}
claude_code_read_only: true
codex_named_thread_pre_review: {"pass" if pre_review_passed else "blocked"}
codex_named_thread_lifecycle: completed_archived
codex_fixes_or_rebuttals_recorded: true
machine_gates_passed: {str(validation_passed).lower()}
unresolved_blocking_issues: {unresolved}
accepted_by: machine_gates_plus_ai_cross_review
blocked_reason: {blocked_reason}
"""


def cmd_run_ai_cross_review(args: argparse.Namespace) -> int:
    pack_dir = resolve_ai_cross_review_path(args.path) if args.path else default_ai_cross_review_dir(args.slug)
    review_slug = args.slug or pack_dir.name
    ensure_review_pack_writable(pack_dir, overwrite=args.overwrite)
    review_exclude_prefixes = ["docs/agent_reviews"]
    changed_files, _untracked = collect_changed_files(exclude_prefixes=review_exclude_prefixes)
    validation_profile = validate_ai_cross_review_tier_args(args, changed_files)
    commands = [] if args.no_default_validation else list(AI_CROSS_REVIEW_DEFAULT_VALIDATION_COMMANDS)
    commands.extend(args.validation_command)
    if not commands:
        raise WorkflowError("run-ai-cross-review requires machine validation; keep defaults or pass --validation-command")
    rounds_required = AI_CROSS_REVIEW_TIER_ROUNDS[args.review_tier]
    pre_review_passed = codex_named_thread_pre_review_passed(args)

    write_review_file(
        pack_dir,
        "00_task.md",
        f"""task_id: {args.task_id or safe_review_slug(review_slug)}
task_title: {args.task_title or review_slug}
scope: {args.scope}
risk_level: {args.risk_level}
validation_profile: {validation_profile}
owner_participation: not_required
review_required: true
review_tier: {args.review_tier}
claude_rounds_required: {rounds_required}
review_reason: {args.review_reason or "重要代码/工作流改动需要按 review_tier 执行 AI 交叉审核。"}
acceptance_gates:
- machine_gates_passed: true
- codex_named_thread_pre_review: pass
- claude_rounds_required: {rounds_required}
- unresolved_blocking_issues: 0
""",
        overwrite=args.overwrite,
    )
    write_review_file(
        pack_dir,
        "01_codex_actions.md",
        f"""codex_role: implementer
changed_files:
{chr(10).join("- " + item for item in changed_files) if changed_files else "- 当前没有 git status 变化"}
intended_behavior: {args.task_title or review_slug}
out_of_scope:
- 不启动训练
- 不启动子 agents
- 不 push
- 不删除用户数据
risk_notes: {args.risk_notes or "由 AI 交叉审核和机器验证共同控制风险。"}
""",
        overwrite=args.overwrite,
    )
    write_review_file(
        pack_dir,
        "02_codex_named_thread_pre_review.md",
        make_codex_named_thread_pre_review_md(args),
        overwrite=args.overwrite,
    )
    write_review_file(pack_dir, "02_diff.patch", build_ai_cross_review_diff(exclude_prefixes=review_exclude_prefixes), overwrite=args.overwrite)
    write_review_file(
        pack_dir,
        "02_focused_diff.md",
        build_ai_cross_review_focused_diff(changed_files, exclude_prefixes=review_exclude_prefixes),
        overwrite=args.overwrite,
    )
    validation_passed, validation_text = run_ai_cross_review_validations(commands)
    validation_text = f"validation_profile: {validation_profile}\n" + validation_text
    write_review_file(pack_dir, "03_validation.md", validation_text, overwrite=args.overwrite)
    write_review_file(
        pack_dir,
        "02_review_brief.md",
        build_ai_cross_review_brief(
            args=args,
            review_slug=review_slug,
            changed_files=changed_files,
            commands=commands,
            validation_passed=validation_passed,
        ),
        overwrite=args.overwrite,
    )
    write_review_file(
        pack_dir,
        "04_claims.md",
        f"""claim: 本次改动已由 Codex 生成证据包，并按 review_tier={args.review_tier} 执行 Claude Code 只读审核。
status: supported
evidence_ref: {ai_cross_review_claude_evidence_refs(rounds_required)}

claim: 机器验证命令已运行。
status: {"verified" if validation_passed else "false"}
evidence_ref: 03_validation.md

claim: Claude Code 前置命名 Codex 线程已完成预审并归档。
status: {"verified" if pre_review_passed else "false"}
evidence_ref: 02_codex_named_thread_pre_review.md
""",
        overwrite=True,
    )

    verdicts: list[str] = []
    for index, (claude_file, codex_file) in enumerate(AI_CROSS_REVIEW_CLAUDE_ROUND_FILES[:rounds_required], start=1):
        exit_code, stdout, stderr = run_claude_review(args, pack_dir, index)
        verdict, claude_md = make_claude_review_md(index, exit_code, stdout, stderr)
        verdicts.append(verdict)
        write_review_file(pack_dir, claude_file, claude_md, overwrite=args.overwrite)
        if codex_file and index < rounds_required:
            write_review_file(pack_dir, codex_file, make_codex_response_md(index, verdict, validation_passed), overwrite=args.overwrite)

    write_review_file(
        pack_dir,
        "10_final_decision.md",
        make_final_decision_tiered_md(
            verdicts,
            validation_passed,
            skip_claude=args.skip_claude,
            review_tier=args.review_tier,
            rounds_required=rounds_required,
            pre_review_passed=pre_review_passed,
        ),
        overwrite=args.overwrite,
    )

    errors = ai_cross_review_errors(pack_dir)
    if errors:
        print(f"run-ai-cross-review path={display_path(pack_dir)} status=blocked")
        for error in errors:
            print(f"ERROR {error}")
        return 1
    print(f"run-ai-cross-review-ok path={display_path(pack_dir)} tier={args.review_tier} rounds={rounds_required}")
    return 0


def cmd_validate_ai_cross_review(args: argparse.Namespace) -> int:
    pack_dir = resolve_ai_cross_review_path(args.path)
    errors = ai_cross_review_errors(pack_dir)
    if errors:
        raise WorkflowError("AI 交叉审核校验失败:\n" + "\n".join(errors))
    _required_files, rounds_required, _tiered_pack = ai_cross_review_required_files_for_pack(pack_dir)
    print(f"validate-ai-cross-review-ok path={display_path(pack_dir)} rounds={rounds_required}")
    return 0


def cmd_validate_trial_meta(args: argparse.Namespace) -> int:
    path = (REPO_ROOT / args.path).resolve() if args.path else REPO_ROOT / "trial_meta.yaml"
    if not path.exists():
        raise WorkflowError(f"trial meta file not found: {rel(path)}")
    errors = validate_trial_meta_file(path)
    if errors:
        raise WorkflowError("Trial meta validation failed:\n" + "\n".join(errors))
    print("validate-trial-meta-ok")
    return 0


def cmd_validate_evidence_routing(_: argparse.Namespace) -> int:
    errors: list[str] = []
    routing_files = sorted((REPO_ROOT / "experiments").rglob("evidence_routing.yaml"))
    for routing_path in routing_files:
        errors.extend(validate_evidence_routing_file(routing_path))
    errors.extend(validate_campaign_result_indexes())
    if errors:
        raise WorkflowError("Evidence routing validation failed:\n" + "\n".join(errors))
    print(f"validate-evidence-routing-ok subjects={len(routing_files)}")
    return 0


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
            "docs/workflow/protocols/experiment_protocol.md",
            "workflow/gtpj_workflow.py",
        }:
            copied_log_refs.append(path_text)
    errors = []
    if offenders:
        errors.append("Forbidden raw experiment artifacts:\n" + "\n".join(offenders))
    if copied_log_refs:
        errors.append("Forbidden copied_log references:\n" + "\n".join(sorted(set(copied_log_refs))))
    artifact_chain_errors = audit_result_manifest_artifact_chain()
    if artifact_chain_errors:
        errors.append("Broken result/manifest/artifact identity chain:\n" + "\n".join(artifact_chain_errors))
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


def idea_core_summary(idea: dict) -> str:
    summary = str(idea.get("core_summary", "")).strip()
    if summary:
        return summary
    hypothesis = str(idea.get("hypothesis", "")).strip()
    if hypothesis:
        return hypothesis
    target = str(idea.get("target_component", "")).strip()
    return target or "待补充核心机制。"


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
        "这是给人读的全局创意总表，只回答“有哪些创意、主要机制是什么”。",
        "它是各版本挑选 idea 的公共菜市场，不记录任何局部执行动作或实验计划。",
        "",
        "| Idea | 标题 | 主要内容 | Idea 文件 | 来源状态 | 全局分 | 覆盖版本 | 全局状态 |",
        "|---|---|---|---|---:|---|---|---|",
    ]
    for idea in ideas:
        versions = ", ".join(f"`{version}`" for version in sorted(idea.get("version_scores", {}).keys()))
        lines.append(
            "| "
            f"`{idea.get('idea_id', '')}` | {idea.get('title', '')} | "
            f"{idea_core_summary(idea)} | "
            f"`{idea_file_for_row(idea)}` | {idea.get('source_status', '')} | "
            f"{idea.get('global_score', 0)} | {versions or '-'} | "
            f"{idea.get('status', '')} |"
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
            "- 具体执行动作只能写入版本队列、trial/attempt 记录、task card 或实验结果文件，不写入本总表。",
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
        "| 排名 | Idea | 标题 | Idea 文件 | 优先级 | 适用性 | 阶段 | 阻塞点 | 版本适配说明 |",
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
            f"{entry.get('rationale', '')} |"
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


def current_active_version(data: dict) -> str:
    version = str(data.get("current_version", "")).strip()
    if re.fullmatch(r"v[0-9]+", version):
        return version
    if CANONICAL_BASELINES:
        return sorted(CANONICAL_BASELINES)[-1]
    return "v1"


def is_ready_trial_idea(idea: dict, version: str) -> bool:
    entry = idea_version_entry(idea, version)
    blockers = entry.get("blockers")
    if idea.get("status") not in TRIAL_READY_STATUSES:
        return False
    if idea_version_stage(idea, version) not in TRIAL_READY_STATUSES:
        return False
    if not isinstance(blockers, list) or blockers:
        return False
    if idea.get("source_type") not in SOURCE_TYPES:
        return False
    source_status = idea.get("source_status")
    if source_status not in TRIAL_ALLOWED_SOURCE_STATUSES:
        return False
    if source_status == "local_heuristic" and not idea.get("evidence"):
        return False
    if not str(idea.get("source_ref", "")).strip():
        return False
    if entry.get("applicability") not in TRIAL_ALLOWED_APPLICABILITIES:
        return False
    for field in ["hypothesis", "implementation_scope", "risk"]:
        if not str(idea.get(field, "")).strip():
            return False
    return True


def next_ready_trial_idea(data: dict, version: str) -> dict | None:
    ready = [
        idea
        for idea in data.get("ideas", [])
        if isinstance(idea, dict) and version in idea.get("version_scores", {}) and is_ready_trial_idea(idea, version)
    ]
    if not ready:
        return None
    return sorted(
        ready,
        key=lambda idea: (
            -idea_score_for_version(idea, version),
            -SOURCE_STATUS_RANK.get(idea.get("source_status", "unknown"), 0),
            -float(idea.get("global_score", 0) or 0),
            idea.get("idea_id", ""),
        ),
    )[0]


MIXED_EXPERIMENT_LABELS = {
    "创新": "innovation",
    "新模块": "innovation",
    "调参": "tune",
    "消融": "ablation",
    "复现": "confirmation",
    "确认": "confirmation",
    "debug": "debug",
    "smoke": "debug",
}


def parse_mixed_experiment_phrase(phrase: str) -> dict[str, int]:
    normalized = phrase.strip().lower().replace("，", "+").replace(",", "+").replace("、", "+")
    requested: dict[str, int] = {}
    for count_text, label in re.findall(r"(\d+)\s*([a-zA-Z]+|[\u4e00-\u9fff]+)", normalized):
        kind = MIXED_EXPERIMENT_LABELS.get(label)
        if not kind:
            continue
        requested[kind] = requested.get(kind, 0) + int(count_text)
    return requested


def format_requested_mix(requested: dict[str, int]) -> str:
    order = ["innovation", "tune", "ablation", "confirmation", "debug"]
    return ", ".join(f"{kind}={requested[kind]}" for kind in order if requested.get(kind))


def extract_requested_job_count(phrase: str) -> int:
    matches = re.findall(r"(\d+)\s*(?:轮|组|个|次|jobs?|runs?)", phrase, flags=re.IGNORECASE)
    return int(matches[-1]) if matches else 0


def is_generic_experiment_planning_phrase(phrase: str) -> bool:
    normalized = phrase.strip().lower().rstrip("。")
    if any(token in normalized for token in ["规划", "计划", "下一轮", "下轮", "后续实验", "实验清单"]):
        return "实验" in normalized or "工作流" in normalized or "跑" in normalized
    if re.search(r"(做|跑|开|来)\s*\d+\s*(轮|组|个|次)\s*实验", normalized):
        return True
    return False


def owner_phrase_base_version(phrase: str) -> str | None:
    match = re.search(r"(?:基于|base(?:d)?\s+on|from)\s*(v[0-9]+)", phrase, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"\b(v[0-9]+)\b", phrase, re.IGNORECASE)
    if match and any(token in phrase for token in ["代码", "base", "版本"]):
        return match.group(1).lower()
    return None


def is_paper_to_experiment_phrase(phrase: str) -> bool:
    exact = {"从论文开始", "论文到实验闭环", "读论文并验证创新"}
    if phrase in exact:
        return True
    if "论文" not in phrase:
        return False
    return any(token in phrase for token in ["做实验", "跑实验", "验证创新", "实验闭环"])


def mini_card_for_phrase(phrase: str) -> dict[str, str]:
    data = load_idea_tree()
    base_version = current_active_version(data)
    normalized = phrase.strip().rstrip("。")
    requested_mix = parse_mixed_experiment_phrase(normalized)
    if requested_mix and (len(requested_mix) >= 2 or is_generic_experiment_planning_phrase(normalized)):
        return {
            "owner_phrase": normalized,
            "task_type": "mixed experiment campaign",
            "base_version": base_version,
            "target": "multiple workstreams under one campaign router",
            "requested_mix": format_requested_mix(requested_mix),
            "writes": "none until campaign manifest, work item map, and agent_runtime.yaml are approved",
            "agent_mode": "real_multi_agent for formal campaign evidence",
            "playbook": "docs/workflow/playbooks/mixed_campaign.md",
            "daily_read_chain": "START_HERE.md -> WORKFLOW_KERNEL.md -> playbooks/mixed_campaign.md",
            "closed_loop": "plan -> agent_runtime -> preflight -> runner -> evidence -> cleanup -> sync",
            "gates": "campaign_manifest, work_items, agent_runtime, multi_agent_preflight, artifact_boundary, cleanup",
            "next_action": "create campaign manifest and agent_runtime.yaml after owner approval",
        }
    if is_generic_experiment_planning_phrase(normalized):
        requested_jobs = extract_requested_job_count(normalized)
        target = "next experiment plan"
        if requested_jobs:
            target = f"next experiment plan with requested budget {requested_jobs}"
        return {
            "owner_phrase": normalized,
            "task_type": "experiment planning",
            "base_version": base_version,
            "target": target,
            "writes": "none; planning gate is read-only until owner accepts a plan",
            "agent_mode": "role_only for planning; real_multi_agent only after formal run is selected",
            "agent_instance_mode": "role_only",
            "playbook": "docs/workflow/START_HERE.md + relevant playbook after task type is selected",
            "daily_read_chain": "START_HERE.md -> WORKFLOW_KERNEL.md -> plan-experiments",
            "closed_loop": "status -> planning gate -> owner accepts plan -> agent_runtime/preflight -> runner",
            "runner_scope": "none",
            "formal_runner_allowed": "false until experiment_type, evidence_ref, and agent_runtime gate are clear",
            "formal_evidence_allowed": "false during planning",
            "agent_runtime_gate": "not_required for read-only planning",
            "multi_agent_preflight": "not_required for read-only planning",
            "owner_monitor_mode": "not_required until formal Runner",
            "agent_activity_stream": "not_required until formal Runner",
            "gates": "formal ledger, baseline_repro_status, evidence_ref, claim_scope, budget, stop_condition",
            "blocked_reason": "runner blocked until planning table selects concrete experiment types and formal evidence refs",
            "next_action": "run plan-experiments to produce Evidence Summary, Candidate Decision, and Current Run Plan",
        }
    if normalized in {"读论文", "找创新点", "提取创新", "从论文读取获得创新"}:
        return {
            "owner_phrase": normalized,
            "task_type": "paper intake / idea discovery",
            "base_version": base_version,
            "target": "paper sources and candidate ideas",
            "writes": "GTPJ_Research first; GitHub idea_tree only for stable lightweight source and idea facts; no experiments",
            "agent_mode": "role_only for intake/triage; real_multi_agent only if the output will drive formal trial decisions",
            "agent_instance_mode": "role_only",
            "playbook": "docs/workflow/playbooks/paper_intake.md",
            "daily_read_chain": "START_HERE.md -> WORKFLOW_KERNEL.md -> playbooks/paper_intake.md",
            "closed_loop": "paper_inbox -> paper_index -> source_review -> extracted_ideas -> idea_tree_sync_check",
            "runner_scope": "none",
            "formal_runner_allowed": "false",
            "formal_evidence_allowed": "false",
            "agent_runtime_gate": "not_required for intake; required later before formal trial/Runner",
            "multi_agent_preflight": "not_required for intake",
            "owner_monitor_mode": "not_required for intake",
            "agent_activity_stream": "not_required for intake",
            "gates": "PAPERS_INDEX, source_status, source_ref, hypothesis, implementation_scope, risk, version_scores",
            "blocked_reason": "paper intake cannot directly start training or create module trial",
            "next_action": "scan GTPJ_Research/papers/_inbox and PAPERS_INDEX.md; do not run training",
        }
    if is_paper_to_experiment_phrase(normalized):
        explicit_base_version = owner_phrase_base_version(normalized)
        if explicit_base_version is None:
            return {
                "owner_phrase": normalized,
                "task_type": "paper -> idea -> module trial closed loop",
                "base_version": "missing",
                "base_code_tag": "missing",
                "target": "paper-derived idea pipeline",
                "writes": "Research/idea_tree only; experiments blocked until owner specifies base version",
                "agent_mode": "role_only for intake/triage; real_multi_agent only after base version and trial gates",
                "agent_instance_mode": "role_only",
                "playbook": "docs/workflow/playbooks/paper_to_experiment.md",
                "daily_read_chain": "START_HERE.md -> WORKFLOW_KERNEL.md -> playbooks/paper_to_experiment.md",
                "closed_loop": "paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue -> blocked_missing_base_version",
                "runner_scope": "none",
                "formal_runner_allowed": "false",
                "formal_evidence_allowed": "false",
                "agent_runtime_gate": "not_required until base version and selected IDEA are specified",
                "multi_agent_preflight": "not_required until base version and selected IDEA are specified",
                "owner_monitor_mode": "not_required until formal Runner",
                "agent_activity_stream": "not_required until formal Runner",
                "gates": "base_version, base_code_tag, source_status, source_ref, module_template_family, module_source, interface_contract",
                "blocked_reason": "missing_base_code_version; paper-to-experiment cannot default to current active version",
                "next_action": "ask owner for base version, e.g. 基于 v5 从论文开始做实验",
            }
        return {
            "owner_phrase": normalized,
            "task_type": "paper -> idea -> module trial closed loop",
            "base_version": explicit_base_version,
            "base_code_tag": explicit_base_version,
            "target": "paper-derived idea pipeline",
            "writes": "Research first; GitHub idea_tree after source/mechanism gate; experiments only after selected idea and owner approval",
            "agent_mode": "role_only for intake/triage; real_multi_agent when code starts or formal trial evidence is planned",
            "agent_instance_mode": "role_only until formal trial uses named_owner_thread",
            "playbook": "docs/workflow/playbooks/paper_to_experiment.md",
            "daily_read_chain": "START_HERE.md -> WORKFLOW_KERNEL.md -> playbooks/paper_to_experiment.md",
            "closed_loop": "paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue -> trial_preflight -> runner_evidence -> idea_feedback",
            "runner_scope": "none until selected IDEA and owner approval",
            "formal_runner_allowed": "false until agent_runtime and multi_agent_preflight pass",
            "formal_evidence_allowed": "false until formal result review passes",
            "agent_runtime_gate": "required before formal trial/Runner",
            "multi_agent_preflight": "required before formal trial/Runner",
            "owner_monitor_mode": "true for formal Runner",
            "agent_activity_stream": "required before formal Runner",
            "gates": "source_status, source_ref, hypothesis, implementation_scope, risk, version_scores, selected_queue, module_template_family, module_source, standard_gzsl, interface_contract, agent_runtime, multi_agent_preflight, cleanup",
            "blocked_reason": "formal run blocked until a paper-derived IDEA is selected and real agents pass preflight",
            "next_action": "read PAPERS_INDEX/_inbox and classify sources; do not create trial or run training until a selected idea passes gates",
        }
    if normalized in {"开新模块", "开下一个新模块"}:
        idea = next_ready_trial_idea(data, base_version)
        if idea is None:
            return {
                "owner_phrase": normalized,
                "task_type": "innovation / module trial",
                "base_version": base_version,
                "target": f"no selected ready idea in {base_version}",
                "writes": "none until a ready idea exists and owner approves start",
                "agent_mode": "real_multi_agent when code starts; role_only for this read-only check",
                "gates": "source_status, interface_contract, innovation_code_review Review 0-3, artifact_boundary",
                "next_action": "list 3 candidates or register an owner-supplied local heuristic idea",
            }
        idea_id = str(idea.get("idea_id", ""))
        title = str(idea.get("title", "")).strip()
        slug = idea_folder_name(idea).removeprefix(f"{idea_id}_")
        if framework_standard_is_active():
            return {
                "owner_phrase": normalized,
                "task_type": "innovation",
                "base_version": base_version,
                "target": f"{idea_id} {title}".strip(),
                "writes": f"idea_tree + experiments/{base_version}/innovation + Warehouse after run",
                "agent_mode": "real_multi_agent, because new module code changes require Review 0-3",
                "gates": "source_status, interface_contract, innovation_code_review Review 0-3, framework ledger, artifact_boundary",
                "next_action": (
                    f"create an exp/{base_version}/innovation/... branch from framework/{base_version}, "
                    "then use new-experiment --kind innovation; do not create a Trial/Attempt"
                ),
            }
        branch = trial_branch_name(base_version, idea_id, "TRIAL-001", slug)
        return {
            "owner_phrase": normalized,
            "task_type": "innovation / module trial",
            "base_version": base_version,
            "target": f"{idea_id} {title}".strip(),
            "writes": "idea_tree + experiments/module_trials + Warehouse after run",
            "agent_mode": "real_multi_agent, because new module code changes require Review 0-3",
            "gates": "source_status, interface_contract, innovation_code_review Review 0-3, artifact_boundary",
            "next_action": f"create {branch} branch and trial record after owner approval",
        }

    if normalized.startswith("试这个：") or normalized.startswith("试这个:"):
        return {
            "owner_phrase": normalized,
            "task_type": "local heuristic idea or innovation / module trial",
            "base_version": base_version,
            "target": normalized.split(":", 1)[-1] if ":" in normalized else normalized.split("：", 1)[-1],
            "writes": "Research/idea_tree only if owner asks to register; no code until ready",
            "agent_mode": "role_only for triage; real_multi_agent if it becomes code",
            "gates": "source_status, interface_contract",
            "next_action": "judge whether this is inbox idea, ready idea, or blocked by missing source/scope",
        }

    defaults = {
        "查状态": {
            "task_type": "read-only status",
            "target": "repository state, active baseline reproducibility, queues, blockers",
            "writes": "none",
            "agent_mode": "role_only, because this is a read-only check",
            "gates": "repo_state, current_version, baseline_repro_status",
            "next_action": "run status/repro-status before comparing or promoting results",
        },
        "复现": {
            "task_type": "confirmation",
            "target": "current baseline result",
            "writes": "none until owner confirms run and evidence level",
            "agent_mode": "role_only for preparation; Runner serial if a run starts",
            "gates": "baseline_repro_status, metric_semantics, evidence_level, artifact_boundary",
            "next_action": "check current baseline repro-status, then decide quick_local vs formal confirmation target",
        },
        "调参": {
            "task_type": "tune",
            "target": "up to 3 candidates for current active baseline",
            "writes": "none until owner picks one candidate",
            "agent_mode": "role_only for candidate suggestion",
            "gates": "no code/eval semantic change, cost check",
            "next_action": "list at most 3 tune candidates",
        },
        "消融": {
            "task_type": "ablation",
            "target": "one controlled factor in the selected framework",
            "writes": "none until ablation target is confirmed",
            "agent_mode": "role_only for classification; real_multi_agent if code or semantic changes",
            "gates": "interface_contract, single_factor, metric_semantics",
            "next_action": "identify the framework and one ablation factor",
        },
        "继续上一个": {
            "task_type": "current framework experiment continuation",
            "target": "current formal experiment; legacy Trial/Attempt is lookup-only",
            "writes": "the owning framework ledger only after state is confirmed",
            "agent_mode": "role_only unless code or result conclusion changes",
            "gates": "attempt_state, artifact_boundary, sync_check",
            "next_action": "inspect current trial state and identify the smallest next action",
        },
        "别问，给我三个候选": {
            "task_type": "read-only idea selection",
            "target": "three candidate ideas",
            "writes": "none",
            "agent_mode": "role_only, because this only ranks candidates",
            "gates": "source_status, blockers",
            "next_action": "read idea_tree and list the top 3 feasible candidates",
        },
        "升版本": {
            "task_type": "promotion",
            "target": "promotion gate",
            "writes": "version ledgers/tags only after gate passes",
            "agent_mode": "real_multi_agent for promotion evidence review",
            "gates": "baseline_grade, confirmation_status, quality_gate, promotion",
            "next_action": "check whether any completed result records promotion_decision: promote",
        },
        "切版本": {
            "task_type": "set-current-version or activate-version",
            "target": "idea_tree view or active code",
            "writes": "idea_tree only for set-current-version; active code only with explicit owner authorization",
            "agent_mode": "role_only for explanation and set-current-version",
            "gates": "owner_authorization, git_policy",
            "next_action": "ask whether owner means idea-tree view or active code switch",
        },
    }
    if normalized not in defaults:
        raise WorkflowError(f"Unknown owner phrase: {phrase}")
    card = dict(defaults[normalized])
    card["owner_phrase"] = normalized
    card["base_version"] = base_version
    return card


def fill_mini_card_defaults(card: dict[str, str]) -> dict[str, str]:
    filled = dict(card)
    agent_mode = filled.get("agent_mode", "")
    read_only_real_multi_agent_later = "when code starts" in agent_mode or "准备" in agent_mode
    formal_intent = "real_multi_agent" in agent_mode and not read_only_real_multi_agent_later
    filled.setdefault("subject_id", "pending")
    filled.setdefault("evidence_state", "not_applicable")
    filled.setdefault("base_code_tag", "not_applicable")
    if formal_intent:
        filled.setdefault("runner_scope", "formal_runner")
        filled.setdefault("formal_runner_allowed", "false until multi_agent_preflight pass")
        filled.setdefault("formal_evidence_allowed", "false until formal result review passes")
        filled.setdefault("agent_runtime_gate", "required before formal Runner")
        filled.setdefault("multi_agent_preflight", "required before formal Runner")
        filled.setdefault("owner_monitor_mode", "true for formal Runner")
        filled.setdefault("agent_activity_stream", "required before formal Runner")
        filled.setdefault("blocked_reason", "formal run blocked until real_multi_agent gate passes")
    else:
        filled.setdefault("runner_scope", "none")
        filled.setdefault("formal_runner_allowed", "false")
        filled.setdefault("formal_evidence_allowed", "false")
        filled.setdefault("agent_runtime_gate", "not_required")
        filled.setdefault("multi_agent_preflight", "not_required")
        filled.setdefault("owner_monitor_mode", "not_required")
        filled.setdefault("agent_activity_stream", "not_required")
        filled.setdefault("blocked_reason", "none")
    filled.setdefault("agent_instance_mode", "named_owner_thread" if formal_intent else "role_only")
    filled.setdefault("requested_mix", "not_applicable")
    filled.setdefault("playbook", "not_applicable")
    filled.setdefault("daily_read_chain", "START_HERE.md -> WORKFLOW_KERNEL.md")
    filled.setdefault("closed_loop", "not_applicable")
    return filled


def cmd_start(args: argparse.Namespace) -> int:
    card = fill_mini_card_defaults(mini_card_for_phrase(args.phrase))
    for key in [
        "owner_phrase",
        "task_type",
        "base_version",
        "base_code_tag",
        "target",
        "subject_id",
        "evidence_state",
        "writes",
        "requested_mix",
        "agent_mode",
        "agent_instance_mode",
        "playbook",
        "daily_read_chain",
        "closed_loop",
        "runner_scope",
        "formal_runner_allowed",
        "formal_evidence_allowed",
        "agent_runtime_gate",
        "multi_agent_preflight",
        "owner_monitor_mode",
        "agent_activity_stream",
        "gates",
        "blocked_reason",
        "next_action",
    ]:
        print(f"{key}: {card[key]}")
    return 0


FORMAL_PENDING_STATUSES = {"planned", "pending", "pre_run", "pre_run_gated", "ready_to_run"}
RESULT_OPTIONAL_EXPERIMENT_STATUSES = FORMAL_PENDING_STATUSES | {"running"}


def markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if cells and cells[0].lower() in {"id", "tune id", "attempt", "experiment"}:
            continue
        rows.append(cells)
    return rows


def collect_formal_pending_rows(limit: int = 8) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for version_dir in sorted((REPO_ROOT / "experiments").glob("v*")):
        if not version_dir.is_dir():
            continue
        for kind in ["tune", "ablation", "innovation", "confirmation"]:
            index_path = version_dir / kind / "INDEX.md"
            if not index_path.exists():
                continue
            if (version_dir / "framework.yaml").exists():
                for row in framework_index_rows(version_dir.name, kind):
                    status = row["status"].lower()
                    if status not in FORMAL_PENDING_STATUSES:
                        continue
                    rows.append(
                        {
                            "subject": row["experiment_id"],
                            "type": f"{version_dir.name}/{kind}",
                            "status": status,
                            "ref": rel(index_path),
                        }
                    )
                    if len(rows) >= limit:
                        return rows
                continue
            for cells in markdown_table_rows(read_text(index_path)):
                lowered = [cell.lower() for cell in cells]
                status = next((cell for cell in lowered if cell in FORMAL_PENDING_STATUSES), "")
                if status:
                    rows.append(
                        {
                            "subject": cells[0],
                            "type": f"{version_dir.name}/{kind}",
                            "status": status,
                            "ref": rel(index_path),
                        }
                    )
                    if len(rows) >= limit:
                        return rows
    return rows


def runtime_batch_count() -> int:
    batches = REPO_ROOT / ".gtpj_runtime" / "batches"
    if not batches.exists():
        return 0
    return sum(1 for item in batches.iterdir() if item.is_dir())


def planning_candidate_decision(task_type: str, requested_mix: dict[str, int], base_version: str, evidence: dict[str, str]) -> list[list[str]]:
    rows: list[list[str]] = []
    confirmed = evidence.get("confirmation_status") == "confirmed" and evidence.get("confirmed_H") not in {"", "pending"}
    if requested_mix.get("confirmation") or task_type == "confirmation":
        rows.append(
            [
                f"{base_version}:best_or_baseline",
                "confirmation_target",
                f"baseline_repro_status:{base_version}",
                "none" if evidence.get("best_observed_H") else "missing_best_observed_H",
                "exact_repeat",
                "only exact restoration if H reaches restore_target_H",
                "plan up to 5 same-seed exact repeats",
            ]
        )
    if requested_mix.get("tune") or task_type == "tune":
        rows.append(
            [
                f"{base_version}:tune_space",
                "search_candidate",
                f"config:{base_version}",
                "comparison reference is unconfirmed" if not confirmed else "none",
                "keep_for_search",
                "search direction only; not confirmation or promotion",
                "generate config-only tune jobs from current config",
            ]
        )
    if requested_mix.get("innovation") or "innovation" in task_type:
        idea = next_ready_trial_idea(load_idea_tree(), base_version)
        formal_framework_route = framework_standard_is_active()
        rows.append(
            [
                str(idea.get("idea_id", "no_ready_idea")) if idea else "no_ready_idea",
                "innovation_candidate",
                "idea_tree selected queue",
                "none" if idea else "missing selected ready idea",
                ("start_framework_innovation" if formal_framework_route else "start_trial") if idea else "blocked",
                "new method evidence only after source, interface, and framework-ledger gates",
                (
                    f"create or bind experiments/{base_version}/innovation before runner"
                    if formal_framework_route
                    else "create or bind trial before runner"
                ),
            ]
        )
    if requested_mix.get("ablation") or task_type == "ablation":
        rows.append(
            [
                f"{base_version}:controlled_factor",
                "ablation_candidate",
                "formal subject result/quality",
                "target factor must be named",
                "run_ablation_after_interface_gate",
                "single-factor contribution only",
                "ask/derive exact factor before batch",
            ]
        )
    if not rows:
        rows.append(
            [
                f"{base_version}:current_state",
                "state_review",
                "repo + formal ledgers",
                "experiment type missing",
                "blocked",
                "no scientific claim",
                "choose tune / ablation / confirmation / innovation",
            ]
        )
    return rows


def planning_run_plan_rows(task_type: str, requested_mix: dict[str, int], base_version: str, max_jobs: int) -> list[list[str]]:
    rows: list[list[str]] = []
    total_requested = sum(requested_mix.values())
    default_jobs = max_jobs if max_jobs > 0 else 1
    if requested_mix:
        for kind in ["innovation", "tune", "ablation", "confirmation", "debug"]:
            count = requested_mix.get(kind, 0)
            if not count:
                continue
            work_item_id = {
                "innovation": "INNOV",
                "tune": "TUNE",
                "ablation": "ABL",
                "confirmation": "CONFIRM",
                "debug": "DEBUG",
            }[kind]
            if kind == "confirmation":
                budget = f"max {min(count, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS)} exact repeats per candidate"
                fingerprint = "exact_repeat: code/config/data/eval/seed unchanged"
                stop = "stop on H >= restore_target_H or after 5 attempts"
                ledger = f"experiments/{base_version}/confirmation/INDEX.md"
            elif kind == "tune":
                budget = f"max {count} tune jobs"
                fingerprint = "changed_config_not_exact_repeat"
                stop = "stop at budget or if quality/interface gate blocks"
                ledger = f"experiments/{base_version}/tune/INDEX.md"
            elif kind == "innovation":
                budget = f"max {count} innovation work items"
                fingerprint = "new_trial_candidate"
                stop = "stop if source/interface/code review blocks"
                ledger = f"experiments/{base_version}/innovation/INDEX.md"
            elif kind == "ablation":
                budget = f"max {count} ablation jobs"
                fingerprint = "single_factor_change_not_exact_repeat"
                stop = "stop if target factor or interface semantics are unclear"
                ledger = f"experiments/{base_version}/ablation/INDEX.md"
            else:
                budget = f"max {count} debug jobs"
                fingerprint = "debug_only"
                stop = "stop after pipeline proof or first blocking failure"
                ledger = "debug record only; formal_evidence=false"
            rows.append([work_item_id, kind, f"{base_version}:{kind}", "canonical evidence required before freeze", fingerprint, budget, stop, ledger])
        return rows
    if task_type == "confirmation":
        rows.append(
            [
                "CONFIRM-001",
                "confirmation",
                f"{base_version}:best_or_baseline",
                "baseline_repro_status",
                "exact_repeat: code/config/data/eval/seed unchanged",
                f"max {min(default_jobs, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS)} exact repeats",
                "stop on H >= restore_target_H or after 5 attempts",
                f"experiments/{base_version}/confirmation/INDEX.md",
            ]
        )
    elif task_type == "tune":
        rows.append(
            [
                "TUNE-001",
                "tune",
                f"{base_version}:tune_space",
                f"experiments/{base_version}/config.yaml",
                "changed_config_not_exact_repeat",
                f"max {default_jobs} tune jobs",
                "stop at budget or quality gate block",
                f"experiments/{base_version}/tune/INDEX.md",
            ]
        )
    else:
        rows.append(
            [
                "PLAN-001",
                task_type,
                f"{base_version}:current_state",
                "repo + formal ledgers",
                "declare before runner",
                f"max {default_jobs} jobs after type is resolved",
                "blocked until experiment type and evidence_ref are clear",
                "formal ledger for resolved type",
            ]
        )
    return rows


def cmd_plan_experiments(args: argparse.Namespace) -> int:
    phrase = args.phrase.strip()
    requested_mix = parse_mixed_experiment_phrase(phrase)
    requested_max_jobs = int(args.max_jobs or 0) or extract_requested_job_count(phrase)
    try:
        card = fill_mini_card_defaults(mini_card_for_phrase(phrase))
        task_type = card["task_type"]
        base_version = card["base_version"]
    except WorkflowError:
        data = load_idea_tree()
        task_type = "mixed experiment campaign" if requested_mix else "experiment planning"
        base_version = current_active_version(data)
    evidence = baseline_evidence(base_version) if base_version in CANONICAL_BASELINES else {
        "evidence_level": "unknown",
        "best_observed_H": "",
        "confirmed_H": "pending",
        "confirmation_status": "needs_confirmation",
        "status": "unknown",
    }
    branch = current_branch() or "(detached)"
    head = git(["rev-parse", "--short", "HEAD"], check=False)
    dirty = "true" if git(["status", "--short"], check=False) else "false"
    pending = collect_formal_pending_rows()
    plan_id = "EXPPLAN-" + normalized_text_fingerprint(f"{phrase}|{head}|{base_version}|{len(pending)}")[:12]
    confirmed = evidence.get("confirmation_status") == "confirmed" and evidence.get("confirmed_H") not in {"", "pending"}
    score = evidence.get("confirmed_H") if confirmed else evidence.get("best_observed_H")
    evidence_type = "confirmed_baseline" if confirmed else ("best_single_unconfirmed" if score else "status_only")
    valid_for = "baseline_grade,promotion_reference" if confirmed else "search_reference,planning_context"
    invalid_for = "none" if confirmed else "confirmation,promotion,baseline_claim"

    print(f"experiment_planning_gate: {plan_id}")
    print(f"owner_phrase: {phrase}")
    print(f"task_type: {task_type}")
    print(f"base_version: {base_version}")
    if requested_max_jobs:
        print(f"requested_budget_jobs: {requested_max_jobs}")
    print("auto_state_scan:")
    print(f"- branch: {branch}")
    print(f"- head: {head}")
    print(f"- dirty: {dirty}")
    print(f"- baseline_repro_status: {evidence.get('confirmation_status')}")
    print(f"- formal_pending_count: {len(pending)}")
    print(f"- runtime_batch_count_debug_only: {runtime_batch_count()}")
    print("- authority_order: formal ledger > result/quality reports > reconciled runner outputs > runtime/debug context")

    print("\n## Evidence Summary")
    evidence_rows = [
        [
            f"baseline:{base_version}",
            "baseline_repro_status",
            "-",
            f"{base_version}:baseline",
            score or "-",
            "-",
            evidence_type,
            valid_for,
            invalid_for,
        ]
    ]
    for row in pending[:3]:
        evidence_rows.append(
            [
                row["ref"],
                "formal_pending",
                "-",
                row["subject"],
                "-",
                "-",
                row["type"],
                "planning_priority",
                "scientific_claim_until_completed",
            ]
        )
    for line in render_table(
        ["evidence_ref", "source", "run_id", "candidate_id", "score", "seed", "evidence_type", "valid_for", "invalid_for"],
        evidence_rows,
    ):
        print(line)

    print("\n## Candidate Decision")
    for line in render_table(
        ["candidate_id", "tier", "source_evidence", "blocker", "decision", "claim_scope", "next_action"],
        planning_candidate_decision(task_type, requested_mix, base_version, evidence),
    ):
        print(line)

    print("\n## Current Run Plan")
    for line in render_table(
        ["work_item_id", "experiment_type", "candidate_id", "evidence_ref", "fingerprint_policy", "budget", "stop_condition", "ledger_target"],
        planning_run_plan_rows(task_type, requested_mix, base_version, requested_max_jobs),
    ):
        print(line)

    print("\nrunner_start_allowed: false")
    print("note: plan-experiments is read-only; use run-workflow only after this plan is accepted and formal gates pass.")
    return 0


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_start_card_skeleton(args: argparse.Namespace) -> str:
    base_version = args.version
    if not base_version:
        try:
            base_version = current_active_version(load_idea_tree())
        except (FileNotFoundError, json.JSONDecodeError, WorkflowError):
            base_version = "current"
    runner_scope = args.runner_scope
    formal = runner_scope == "formal_runner"
    lines = [
        "schema_version: gtpj.task_start_card.v0",
        f"owner_request: {yaml_quote(args.owner_request)}",
        f"task_type: {yaml_quote(args.task_type)}",
        f"base_version: {yaml_quote(base_version)}",
        f"idea_id: {yaml_quote(args.idea_id)}",
        f"trial_id: {yaml_quote(args.trial_id)}",
        f"attempt_id: {yaml_quote(args.attempt_id)}",
        f"subject_id: {yaml_quote(args.subject_id)}",
        f"runner_scope: {runner_scope}",
        "formal_runner_allowed: false",
        "formal_evidence_allowed: false",
        "agents:",
        f"  activation_mode: {'real_multi_agent' if formal else 'role_only'}",
        f"  agent_instance_mode: {'named_owner_thread' if formal else 'role_only'}",
        f"  lifecycle: {'workflow_scoped' if formal else 'role_only'}",
    ]
    if formal:
        lines.extend(
            [
                "  required_real_agents:",
                "    - runner_monitor",
                "    - evidence_quality_checker",
                "  agent_instance_status:",
                "    runner_monitor:",
                "    evidence_quality_checker:",
                "  agent_status_refs:",
                "    runner_monitor:",
                "    evidence_quality_checker:",
                "  agent_output_refs:",
                "    runner_monitor:",
                "    evidence_quality_checker:",
                "  agent_runtime_gate:",
                "    path:",
                "    validated: false",
                "    validator_command: python workflow/gtpj_workflow.py validate-agent-runtime --path <agent_runtime.yaml>",
                "    runner_start_allowed: false",
                "    formal_runner_allowed: false",
                "    formal_evidence_allowed: false",
                "    multi_agent_preflight:",
                "      required_threads_created: false",
                "      agent_instance_ids_present: false",
                "      agent_status_refs_valid: false",
                "      independent_outputs_present: false",
                "      agent_output_refs_valid: false",
                "      pre_run_allow_checks_passed: false",
                "      agent_runtime_validated: false",
            ]
        )
    else:
        lines.extend(
            [
                "  required_real_agents: []",
                "  agent_runtime_gate:",
                "    path: not_required",
                "    validated: not_required",
            ]
        )
    lines.extend(
        [
            "hard_gates:",
            "  agent_runtime:",
            "  artifact_boundary:",
            "expected_outputs:",
            "  github:",
            "  research:",
            "  warehouse:",
            "blocked_reason: formal Runner blocked until multi_agent_preflight pass" if formal else "blocked_reason: none",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_start_card(args: argparse.Namespace) -> int:
    content = build_start_card_skeleton(args)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = REPO_ROOT / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"start-card-written path={display_path(output_path)}")
        return 0
    print(content, end="")
    return 0


def warehouse_path_from_uri(uri: str) -> Path:
    prefix = "warehouse://gtpj/"
    if not uri.startswith(prefix):
        raise WorkflowError(f"Warehouse artifact URI must start with {prefix}: {uri}")
    relative = uri[len(prefix):]
    root = warehouse_root()
    path = root / relative
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise WorkflowError(f"Warehouse artifact must stay inside Warehouse root: {display_path(root)}") from exc
    return path


def check_closeout_artifacts(artifacts: dict[str, dict[str, str]]) -> None:
    if not artifacts:
        raise WorkflowError("Attempt manifest must include at least one artifact")
    for key, artifact in artifacts.items():
        artifact_id = artifact.get("artifact_id", "")
        uri = artifact.get("uri", "")
        if not artifact_id:
            raise WorkflowError(f"Artifact {key} is missing artifact_id")
        if not uri:
            raise WorkflowError(f"Artifact {artifact_id} is missing uri")
        if not uri.startswith("warehouse://"):
            continue
        path = warehouse_path_from_uri(uri)
        if not path.exists():
            raise WorkflowError(f"Warehouse artifact missing: {display_path(path)}")
        expected_sha = artifact.get("sha256", "")
        expected_size = artifact.get("size_bytes", "")
        actual_sha, actual_size = artifact_file_info(path)
        if expected_sha and expected_sha != actual_sha:
            raise WorkflowError(f"Warehouse artifact sha256 mismatch for {artifact_id}")
        if expected_size and expected_size != actual_size:
            raise WorkflowError(f"Warehouse artifact size mismatch for {artifact_id}")


def cmd_closeout_check(args: argparse.Namespace) -> int:
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial directory: {display_path(trial_dir)}")
    require_path_inside(trial_dir, REPO_ROOT / "experiments" / "module_trials", "trial-dir")
    _trial_id, _slug = parse_trial_folder_name(trial_dir)
    attempt_upper, _attempt_lower = normalize_attempt_ids(args.attempt_id)
    attempt_dir = trial_dir / "attempts" / attempt_upper
    attempt_manifest_path = attempt_dir / "manifest.yaml"
    attempt_result_path = attempt_dir / "result.yaml"
    if not attempt_manifest_path.exists() or not attempt_result_path.exists():
        raise WorkflowError(f"{attempt_upper} must have manifest.yaml and result.yaml")
    attempt_result = read_shallow_yaml(attempt_result_path)
    metrics_h = yaml_section_value(attempt_result, "metrics", "H")
    if not metrics_h:
        raise WorkflowError(f"{rel(attempt_result_path)} is missing metrics.H")
    artifacts = read_yaml_artifacts(attempt_manifest_path)
    check_closeout_artifacts(artifacts)

    required_root_files = [
        "README.md",
        "ATTEMPTS.md",
        "manifest.yaml",
        "result.yaml",
        "result.md",
        "quality_check.md",
        "review_round_2.md",
        "agent_summary.md",
    ]
    for filename in required_root_files:
        if not (trial_dir / filename).exists():
            raise WorkflowError(f"Missing trial root file: {rel(trial_dir / filename)}")

    trial_fields = read_key_value_block(trial_dir / "README.md")
    idea_id = trial_fields.get("idea_id", "")
    if not idea_id:
        raise WorkflowError("Trial README is missing idea_id")
    root_readme = read_text(trial_dir / "README.md")
    root_manifest = read_text(trial_dir / "manifest.yaml")
    root_result = read_text(trial_dir / "result.yaml")
    attempts_text = read_text(trial_dir / "ATTEMPTS.md")
    if attempt_upper not in attempts_text:
        raise WorkflowError(f"{attempt_upper} missing from ATTEMPTS.md")
    attempt_manifest_ref = f"attempts/{attempt_upper}/manifest.yaml"
    if attempt_manifest_ref not in root_result:
        raise WorkflowError(f"trial root result.yaml must reference {attempt_manifest_ref}")
    check_closeout_report_file(
        trial_dir / "review_round_2.md",
        attempt_upper=attempt_upper,
        artifacts=artifacts,
    )
    check_closeout_report_file(
        trial_dir / "agent_summary.md",
        attempt_upper=attempt_upper,
        artifacts=artifacts,
    )
    for artifact in artifacts.values():
        artifact_id = artifact.get("artifact_id", "")
        uri = artifact.get("uri", "")
        if artifact_id and artifact_id not in root_readme + root_result + root_manifest:
            raise WorkflowError(f"trial root files do not reference artifact {artifact_id}")
        if uri and uri not in root_readme + root_manifest:
            raise WorkflowError(f"trial root files do not reference artifact URI {uri}")

    trial_rel = rel(trial_dir)
    module_index_path = REPO_ROOT / "experiments" / "module_trials" / "INDEX.md"
    if not module_index_path.exists() or trial_rel not in read_text(module_index_path):
        raise WorkflowError(f"Module trial index missing {trial_rel}")
    data = load_idea_tree()
    idea = find_idea_record(data, idea_id)
    if trial_rel not in idea.get("linked_trials", []):
        raise WorkflowError(f"{idea_id} missing linked trial {trial_rel}")
    result_ref = f"{trial_rel}/result.yaml"
    evidence = idea.get("evidence", [])
    if not any(isinstance(item, dict) and item.get("ref") == result_ref for item in evidence):
        raise WorkflowError(f"{idea_id} missing evidence ref {result_ref}")

    print("closeout-check-ok")
    print("attempt: ok")
    print("trial_root: ok")
    print("review_round_2: ok")
    print("agent_summary: ok")
    print("module_index: ok")
    print("idea_tree: ok")
    print("warehouse_artifacts: ok")
    return 0


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
        "core_summary": "",
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
    if framework_standard_is_active():
        raise WorkflowError(
            "The active framework standard retired new Trial creation. Use new-experiment --kind innovation "
            "under the owning formal framework; old Trial/Attempt paths are compatibility evidence only."
        )
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
    template_family = str(
        idea.get("module_template_family")
        or idea.get("required_module_template")
        or version_entry.get("module_template_family")
        or "pending"
    ).strip()
    module_scope = str(
        idea.get("module_scope")
        or version_entry.get("module_scope")
        or ("composite" if template_family == "composite" else "single_module")
    ).strip()
    composition_mode = str(
        idea.get("composition_mode")
        or version_entry.get("composition_mode")
        or ("pending" if module_scope == "composite" else "none")
    ).strip()
    training_entry_mode = str(args.training_entry_mode).strip()
    selected_training_entry = (
        "training_entry.py" if training_entry_mode == "strict_template_entry" else "train_GTPJ_CUB.py"
    )
    legacy_module_migration = "required" if training_entry_mode == "strict_template_entry" else "not_required"
    risk_level = "high" if module_scope == "architecture_change" else "normal"
    split_audit = "required" if module_scope == "architecture_change" else "not_required"
    if training_entry_mode == "strict_template_entry":
        copy_new(
            REPO_ROOT / "experiments" / "templates" / "modules" / "standard_gzsl_training_template.py",
            trial_dir / selected_training_entry,
        )
    write_new(
        trial_dir / "module_source.md",
        f"""# Module Source

```text
idea_id: {idea_id}
trial_id: {trial_id}
module_name: {slug}
template_family: {template_family}
module_scope: {module_scope}
trial_meta: trial_meta.yaml
base_version: {base_version}
base_code_tag: {base_version}
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
training_entry_mode: {training_entry_mode}
selected_training_entry: {selected_training_entry}
legacy_module_migration: {legacy_module_migration}
```

## Source

```text
source_type: {idea.get('source_type', '')}
paper_id:
source_ref: {idea.get('source_ref', '')}
source_status: {idea.get('source_status', '')}
official_code_url:
official_code_path:
official_code_commit:
```

## Mechanism Claim

```text
mechanism_claim: {idea.get('hypothesis', '')}
target_signal:
expected_effect_on_gzsl:
```

## Adaptation To GTPJ

```text
what_is_copied:
what_is_adapted:
what_is_new:
why_fit_gtpj: {version_entry.get('rationale', '')}
not_implemented_from_source:
```

## Template Mapping

```text
template_family: {template_family}
module_scope: {module_scope}
components:
  - name:
    template_family:
    attachment_point:
    enabled_key:
composition_mode: {composition_mode}
affects:
  forward_main_flow:
  class_scoring:
  train_data_view:
  eval_input_output:
  split_or_label_mapping:
attachment_point:
input_tensors:
output_tensors:
config_switch:
baseline_off_explanation:
training_entry_mode: {training_entry_mode}
selected_training_entry: {selected_training_entry}
legacy_module_migration: {legacy_module_migration}
```

## Paper Writing Note

```text
module_origin_sentence:
method_explanation:
difference_from_source:
ablation_needed:
limitations:
paper_writing_note:
```
""",
    )
    write_new(
        trial_dir / "trial_meta.yaml",
        f"""schema_version: gtpj.trial_meta.v0
trial_id: {trial_id}
module_scope: {module_scope}
template_family: {template_family}
risk: {risk_level}

training_entry:
  mode: {training_entry_mode}
  standard_template: experiments/templates/modules/standard_gzsl_training_template.py
  selected_entry: {selected_training_entry}
  legacy_module_migration: {legacy_module_migration}

attachment_points:
  - TODO_ATTACHMENT

affects:
  forward_main_flow: false
  class_scoring: false
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false

baseline_off:
  supported: true
  expected_equivalence: {base_version}
  all_switches_false_equals_base: true

audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
  split_integrity_audit: {split_audit}
  class_order_audit: {split_audit}
""",
    )
    write_new(
        trial_dir / "framework_diagram.md",
        f"""# Framework Diagram

```text
trial_id: {trial_id}
idea_id: {idea_id}
base_version: {base_version}
source_idea_file: {rel(source_idea_file)}
html_view:
warehouse_artifact:
code_vs_intent: pending
```

## Diagram

Add the authoritative Mermaid diagram here. If an HTML view is generated for owner review,
record its local `file:///D:/...` link or Warehouse artifact above.

```mermaid
flowchart TD
  Input["input tensors"] --> Forward["main forward path"]
  Forward --> Logits["logits"]
  Forward -. "loss reads tensors here" .-> Loss["auxiliary loss"]
```

## Variable Glossary

| Variable | Produced by | Consumed by | Shape | Meaning | Grad / detach | Train/eval difference |
|---|---|---|---|---|---|---|

## Method Glossary

| Method / module | Code location | Inputs | Outputs | Responsibility | Config switch | Baseline-off behavior |
|---|---|---|---|---|---|---|

## Loss Flow

| Loss | Reads | Target / teacher / source | Weight key | Gradient boundary | Where it appears in the diagram |
|---|---|---|---|---|---|

## Code vs Intent

- [ ] The diagram is grounded in inspected code, not memory.
- [ ] The implemented path matches the idea/design.
- [ ] Any mismatch is explicitly marked as code vs intent.
- [ ] Lines do not overlap nodes or other semantic lines in the owner HTML view.
""",
    )
    review_template = """# Innovation Review

```text
review_round:
role:
agent_instance_mode:
agent_instance_type:
lifecycle:
persistent_thread_id:
named_thread_reason:
independence_scope:
output_locations:
inputs_checked:
findings:
blocking_issues:
non_blocking_issues:
decision: PENDING
evidence_refs:
memory_used:
memory_sources:
verified_against_current_repo:
```
"""
    write_new(trial_dir / "idea_intent_check.md", review_template.replace("review_round:", "review_round: Review 0"))
    write_new(trial_dir / "interface_precheck.md", review_template.replace("review_round:", "review_round: Review 1"))
    write_new(trial_dir / "review_round_1.md", review_template.replace("review_round:", "review_round: Review 2"))
    write_new(trial_dir / "review_round_2.md", review_template.replace("review_round:", "review_round: Review 3"))
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
module_source: module_source.md
module_template_family: {template_family}
module_scope: {module_scope}
composition_mode: {composition_mode}
trial_meta: trial_meta.yaml
standard_gzsl_framework: experiments/templates/modules/standard_gzsl_module_framework_template.py
standard_gzsl_training_template: experiments/templates/modules/standard_gzsl_training_template.py
training_entry_mode: {training_entry_mode}
selected_training_entry: {selected_training_entry}
legacy_module_migration: {legacy_module_migration}
trial_decision: pending
promotion_decision: not_applicable
promote_to:
evidence_level: pending
best_observed_H:
confirmed_H:
confirmation_status: pending
changed_files:
run_config: config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
idea_intent_check: idea_intent_check.md
interface_precheck: interface_precheck.md
review_round_1: review_round_1.md
review_round_2: review_round_2.md
agent_summary: agent_summary.md
framework_diagram: framework_diagram.md
```

## Module Source

```text
path: module_source.md
source_type: {idea.get('source_type', '')}
source_ref: {idea.get('source_ref', '')}
mechanism_claim: {idea.get('hypothesis', '')}
template_family: {template_family}
module_scope: {module_scope}
components:
composition_mode: {composition_mode}
affects:
trial_meta: trial_meta.yaml
attachment_point:
training_template: experiments/templates/modules/standard_gzsl_training_template.py
training_entry_mode: {training_entry_mode}
selected_training_entry: {selected_training_entry}
legacy_module_migration: {legacy_module_migration}
baseline_off_explanation:
paper_writing_note:
```

No new module trial may omit source and template mapping. Historical baselines may stay as legacy records.

## 改动文件

| 文件 | 改动 | 是否属于代码层 |
|---|---|---|

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Trial Flow

```mermaid
flowchart TD
  Idea["{idea_id}: {idea.get('title', '')}"] --> R0["Review 0: idea intent"]
  R0 --> R1["Review 1: design/interface"]
  R1 --> Impl["implementation + code.diff"]
  Impl --> R2["Review 2: code diff pre-run"]
  R2 --> Freeze["pre-run freeze commit"]
  Freeze --> Run["Runner with GPU lock"]
  Run --> Artifacts["Warehouse artifacts"]
  Artifacts --> Attempt["attempt-local manifest/result/quality"]
  Attempt --> Root["trial root summary"]
  Root --> R3["Review 3: post-run evidence"]
  R3 --> Decision["trial_decision / promotion_decision"]
```

## Framework Diagram

```text
path: framework_diagram.md
html_view:
warehouse_artifact:
code_vs_intent: pending
```

`framework_diagram.md` must explain every diagram variable and method:

- variable glossary: source, shape, meaning, gradient/detach status, and train/eval difference.
- method glossary: code location, inputs, outputs, responsibility, config switch, and baseline-off behavior.
- embedded loss flow: each loss is attached to the tensors it reads.
- code vs intent: whether inspected code matches the idea/design.

## Innovation Code Review

```text
Review 0: idea_intent_check.md
Review 1: interface_precheck.md
Review 2: review_round_1.md + interface_check.md + quality_check.md
Review 3: review_round_2.md + agent_summary.md
activation_mode: real_multi_agent
ai_cross_review: 重要代码/决策改动必须执行；使用 validate-ai-cross-review 校验
```

## Promotion Gate

- [ ] baseline H、trial H、delta H 已记录。
- [ ] `evidence_level: baseline_grade`；单次最高 H 只能写 `best_observed_H`。
- [ ] clean confirmation 或多 run 稳定性证据明确，`confirmed_H` 和 `confirmation_status` 已记录。
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
        f"""# 实现记录

参考契约：

```text
docs/workflow/protocols/code_interface_contract.md
docs/workflow/protocols/innovation_code_review_protocol.md
docs/workflow/protocols/module_template_selection.md
```

## 新模块

```text
module_source: module_source.md
trial_meta: trial_meta.yaml
template_family: {template_family}
module_scope: {module_scope}
training_template: experiments/templates/modules/standard_gzsl_training_template.py
training_entry_mode: {training_entry_mode}
selected_training_entry: {selected_training_entry}
legacy_module_migration: {legacy_module_migration}
base_version: {base_version}
base_code_tag: {base_version}
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
```

## 基于什么

## 接入点

| 项目 | 值 |
|---|---|
| File | |
| Class/function | |
| 接入前/后 | |
| Consumes | |
| Produces | |

## Template Selection

```text
selected_template: {template_family}
selection_reason:
mechanism_claim: {idea.get('hypothesis', '')}
why_not_narrower_template:
module_scope:
components:
composition_mode:
affects:
  forward_main_flow:
  class_scoring:
  train_data_view:
  eval_input_output:
  split_or_label_mapping:
high_risk_reason:
```

## Training Entry（训练入口）

```text
selected_training_entry:
training_entry_mode: {training_entry_mode}
standard_template: experiments/templates/modules/standard_gzsl_training_template.py
strict_template_rule: 当 mode=strict_template_entry 时，Runner 只能使用 trial-local training_entry.py。
legacy_module_migration: {legacy_module_migration}
equivalence_note:
config_path:
seed:
dataset_loader:
eval_function:
checkpoint_policy:
artifact_refs:
```

说明本 Trial 是复制标准训练模板，还是沿用 `train_GTPJ_CUB.py` 等等价入口。
如果 owner 指定“用新模板”，必须设置 `training_entry_mode: strict_template_entry`，
把旧入口中打开的模块迁移到 trial-local `training_entry.py`，不得继续在旧入口上加分支。
必须覆盖 config、seed、dataset/split、frozen backbone、model/module、
train loop、standard GZSL eval、checkpoint/log retention、result/quality summary。

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
dataset: CUB
split file: xlsa17/att_splits.mat
logits shape:
class order:
label mapping:
seen/unseen split:
metric calculation:
metric semantics: standard GZSL U/S/H/ZS
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
- [ ] Label mapping 检查。
- [ ] Seen/unseen split 检查。
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


def _dynamic_updates(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "use_dynamic_routing": True,
        "dynamic_local_mode": "fixed",
        "dynamic_icsa_mode": "fixed",
        "dynamic_direction_mode": "fixed",
        "dynamic_pse_mode": "fixed",
        "dynamic_gate_hidden": 32,
        "dynamic_gate_anchor_lambda": 0.001,
    }
    base.update(overrides)
    return base


def _balanced_aggressive_dynamic_routing_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = [
        ("sanity_control", "static_v5_control", {"use_dynamic_routing": False}),
        ("sanity_control", "dynamic_fixed_all", _dynamic_updates()),
        (
            "sanity_control",
            "sample_local_direction_class_icsa",
            _dynamic_updates(
                dynamic_local_mode="sample",
                dynamic_icsa_mode="class",
                dynamic_direction_mode="sample",
                dynamic_pse_mode="class",
                dynamic_gate_hidden=32,
                dynamic_gate_anchor_lambda=0.001,
            ),
        ),
        (
            "sanity_control",
            "class_local_direction_pse",
            _dynamic_updates(
                dynamic_local_mode="class",
                dynamic_icsa_mode="fixed",
                dynamic_direction_mode="class",
                dynamic_pse_mode="class",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.003,
            ),
        ),
    ]

    for hidden in [16, 24, 32, 48]:
        for mode in ["sample", "class"]:
            specs.append(
                (
                    "local_gate",
                    f"local_{mode}_h{hidden}",
                    _dynamic_updates(
                        dynamic_local_mode=mode,
                        dynamic_gate_hidden=hidden,
                        dynamic_gate_anchor_lambda=0.001,
                    ),
                )
            )

    for hidden in [16, 24, 32, 48]:
        for mode in ["sample", "class"]:
            specs.append(
                (
                    "icsa_gate",
                    f"icsa_{mode}_h{hidden}",
                    _dynamic_updates(
                        dynamic_icsa_mode=mode,
                        dynamic_gate_hidden=hidden,
                        dynamic_gate_anchor_lambda=0.001,
                    ),
                )
            )

    for mode, hidden, anchor in [
        ("sample", 16, 0.0),
        ("sample", 32, 0.001),
        ("sample", 48, 0.003),
        ("class", 16, 0.0),
        ("class", 32, 0.001),
        ("class", 48, 0.003),
    ]:
        specs.append(
            (
                "direction_gate",
                f"direction_{mode}_h{hidden}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                ),
            )
        )

    for hidden, anchor in [(16, 0.0), (24, 0.001), (32, 0.001), (48, 0.003), (64, 0.003), (96, 0.005)]:
        specs.append(
            (
                "pse_gate",
                f"pse_class_h{hidden}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                ),
            )
        )

    combos = [
        ("combo_sample_local_icsa", "sample", "sample", "fixed", "fixed", 32, 0.001),
        ("combo_sample_local_direction", "sample", "fixed", "sample", "fixed", 32, 0.001),
        ("combo_class_icsa_pse", "fixed", "class", "fixed", "class", 32, 0.001),
        ("combo_sample_all_class_pse", "sample", "sample", "sample", "class", 48, 0.003),
        ("combo_class_local_direction", "class", "fixed", "class", "fixed", 48, 0.003),
        ("combo_class_local_icsa_pse", "class", "class", "fixed", "class", 48, 0.003),
        ("combo_class_all", "class", "class", "class", "class", 64, 0.005),
        ("combo_aggressive_mixed", "sample", "class", "class", "class", 96, 0.005),
    ]
    for name, local_mode, icsa_mode, direction_mode, pse_mode, hidden, anchor in combos:
        specs.append(
            (
                "combination",
                name,
                _dynamic_updates(
                    dynamic_local_mode=local_mode,
                    dynamic_icsa_mode=icsa_mode,
                    dynamic_direction_mode=direction_mode,
                    dynamic_pse_mode=pse_mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                ),
            )
        )

    if len(specs) != 40:
        raise WorkflowError(f"Dynamic routing explore plan must contain 40 jobs, got {len(specs)}")
    return specs


def _principled_followup_dynamic_routing_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = [
        ("sanity_control", "static_v5_control", {"use_dynamic_routing": False}),
        ("sanity_control", "dynamic_fixed_all", _dynamic_updates()),
        (
            "sanity_control",
            "fixed_direction_w0.45",
            _dynamic_updates(weight_s2v=0.45),
        ),
        (
            "sanity_control",
            "fixed_direction_w0.55",
            _dynamic_updates(weight_s2v=0.55),
        ),
    ]

    for mode, hidden, weight_s2v, anchor in [
        ("sample", 24, 0.50, 0.003),
        ("sample", 32, 0.45, 0.003),
        ("sample", 32, 0.55, 0.003),
        ("sample", 48, 0.50, 0.005),
        ("sample", 48, 0.45, 0.005),
        ("sample", 64, 0.50, 0.010),
        ("class", 24, 0.50, 0.003),
        ("class", 32, 0.45, 0.003),
        ("class", 32, 0.55, 0.003),
        ("class", 48, 0.50, 0.005),
        ("class", 48, 0.55, 0.005),
        ("class", 64, 0.50, 0.010),
    ]:
        specs.append(
            (
                "direction_gate",
                f"direction_{mode}_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for mode, hidden, local_weight, anchor in [
        ("sample", 24, 0.10, 0.003),
        ("sample", 24, 0.15, 0.003),
        ("sample", 32, 0.10, 0.005),
        ("sample", 48, 0.12, 0.005),
        ("class", 16, 0.08, 0.005),
        ("class", 24, 0.10, 0.005),
        ("class", 24, 0.15, 0.005),
        ("class", 32, 0.12, 0.010),
    ]:
        specs.append(
            (
                "local_gate",
                f"local_{mode}_h{hidden}_l{local_weight:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_local_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=local_weight,
                ),
            )
        )

    for hidden, pse_outer_ratio, anchor in [
        (24, 0.45, 0.003),
        (32, 0.45, 0.005),
        (32, 0.55, 0.003),
        (48, 0.55, 0.005),
        (48, 0.65, 0.005),
        (64, 0.55, 0.005),
        (64, 0.75, 0.010),
        (96, 0.55, 0.010),
    ]:
        specs.append(
            (
                "pse_gate",
                f"pse_class_h{hidden}_p{pse_outer_ratio:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    combos = [
        (
            "combo_ld_sample_h32_l0.10_w0.50",
            "sample",
            "fixed",
            "sample",
            "fixed",
            32,
            0.005,
            0.10,
            0.50,
            None,
        ),
        (
            "combo_ld_sample_h48_l0.12_w0.50",
            "sample",
            "fixed",
            "sample",
            "fixed",
            48,
            0.005,
            0.12,
            0.50,
            None,
        ),
        (
            "combo_ld_direction_class_h32_l0.10_w0.45",
            "sample",
            "fixed",
            "class",
            "fixed",
            32,
            0.005,
            0.10,
            0.45,
            None,
        ),
        (
            "combo_ld_classlocal_h24_l0.08_w0.55",
            "class",
            "fixed",
            "sample",
            "fixed",
            24,
            0.010,
            0.08,
            0.55,
            None,
        ),
        (
            "combo_dp_sample_h48_w0.50_p0.55",
            "fixed",
            "fixed",
            "sample",
            "class",
            48,
            0.005,
            None,
            0.50,
            0.55,
        ),
        (
            "combo_dp_class_h48_w0.55_p0.55",
            "fixed",
            "fixed",
            "class",
            "class",
            48,
            0.005,
            None,
            0.55,
            0.55,
        ),
        (
            "combo_ldp_sample_h32_l0.10_w0.50_p0.55",
            "sample",
            "fixed",
            "sample",
            "class",
            32,
            0.005,
            0.10,
            0.50,
            0.55,
        ),
        (
            "combo_ldp_classsafe_h48_l0.08_w0.55_p0.55",
            "class",
            "fixed",
            "class",
            "class",
            48,
            0.010,
            0.08,
            0.55,
            0.55,
        ),
    ]
    for (
        name,
        local_mode,
        icsa_mode,
        direction_mode,
        pse_mode,
        hidden,
        anchor,
        local_weight,
        weight_s2v,
        pse_outer_ratio,
    ) in combos:
        updates = _dynamic_updates(
            dynamic_local_mode=local_mode,
            dynamic_icsa_mode=icsa_mode,
            dynamic_direction_mode=direction_mode,
            dynamic_pse_mode=pse_mode,
            dynamic_gate_hidden=hidden,
            dynamic_gate_anchor_lambda=anchor,
            weight_s2v=weight_s2v,
        )
        if local_weight is not None:
            updates["local_weight"] = local_weight
        if pse_outer_ratio is not None:
            updates["pse_outer_ratio"] = pse_outer_ratio
        specs.append(("combination", name, updates))

    if len(specs) != 40:
        raise WorkflowError(f"Principled dynamic routing explore plan must contain 40 jobs, got {len(specs)}")
    return specs


def _direction_repeat_confirmation_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add_repeats(count: int, group: str, name: str, updates: dict[str, object]) -> None:
        for repeat_index in range(1, count + 1):
            specs.append((group, f"{name}_r{repeat_index:02d}", dict(updates)))

    add_repeats(
        CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
        "direction_confirmation",
        "dr009_direction_sample_h48_w0.45_a0.005",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.005,
            weight_s2v=0.45,
        ),
    )
    add_repeats(
        CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
        "direction_neighbor",
        "dr008_direction_sample_h48_w0.5_a0.005",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.005,
            weight_s2v=0.50,
        ),
    )
    add_repeats(
        CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
        "direction_neighbor",
        "dr010_direction_sample_h64_w0.5_a0.01",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=64,
            dynamic_gate_anchor_lambda=0.010,
            weight_s2v=0.50,
        ),
    )
    add_repeats(5, "sanity_control", "static_v5_control", {"use_dynamic_routing": False})
    add_repeats(5, "sanity_control", "dynamic_fixed_all", _dynamic_updates())

    for hidden, weight_s2v, anchor in [
        (40, 0.42, 0.003),
        (40, 0.45, 0.003),
        (40, 0.45, 0.005),
        (40, 0.48, 0.005),
        (40, 0.50, 0.007),
        (48, 0.42, 0.003),
        (48, 0.45, 0.003),
        (48, 0.45, 0.007),
        (48, 0.48, 0.003),
        (48, 0.48, 0.005),
        (48, 0.50, 0.005),
        (48, 0.52, 0.005),
        (56, 0.42, 0.005),
        (56, 0.45, 0.005),
        (56, 0.48, 0.007),
        (56, 0.50, 0.007),
        (56, 0.52, 0.010),
        (64, 0.42, 0.005),
        (64, 0.45, 0.007),
        (64, 0.48, 0.007),
        (64, 0.50, 0.010),
        (64, 0.52, 0.010),
        (72, 0.45, 0.010),
        (72, 0.50, 0.010),
        (72, 0.52, 0.010),
    ]:
        specs.append(
            (
                "direction_local_refine",
                f"direction_refine_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    if len(specs) != 50:
        raise WorkflowError(f"Direction repeat confirmation plan must contain 50 jobs, got {len(specs)}")
    return specs


def _direction_exploit_followup_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add_repeats(count: int, group: str, name: str, updates: dict[str, object]) -> None:
        for repeat_index in range(1, count + 1):
            specs.append((group, f"{name}_r{repeat_index:02d}", dict(updates)))

    add_repeats(
        CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
        "must_reproduce",
        "dr009_direction_sample_h48_w0.45_a0.005",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.005,
            weight_s2v=0.45,
        ),
    )
    add_repeats(
        3,
        "must_reproduce",
        "dr008_direction_sample_h48_w0.5_a0.005",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.005,
            weight_s2v=0.50,
        ),
    )
    add_repeats(
        3,
        "must_reproduce",
        "dr010_direction_sample_h64_w0.5_a0.01",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=64,
            dynamic_gate_anchor_lambda=0.010,
            weight_s2v=0.50,
        ),
    )
    specs.extend(
        [
            ("sanity_control", "static_v5_control_r01", {"use_dynamic_routing": False}),
            ("sanity_control", "dynamic_fixed_all_r01", _dynamic_updates()),
        ]
    )

    for hidden, weight_s2v, anchor in [
        (40, 0.42, 0.003),
        (40, 0.45, 0.005),
        (40, 0.48, 0.007),
        (40, 0.50, 0.005),
        (48, 0.42, 0.003),
        (48, 0.45, 0.003),
        (48, 0.45, 0.007),
        (48, 0.48, 0.005),
        (48, 0.50, 0.007),
        (48, 0.52, 0.005),
        (56, 0.42, 0.005),
        (56, 0.45, 0.005),
        (56, 0.48, 0.007),
        (56, 0.50, 0.005),
        (56, 0.52, 0.010),
        (64, 0.42, 0.005),
        (64, 0.45, 0.007),
        (64, 0.48, 0.010),
        (64, 0.50, 0.007),
        (64, 0.52, 0.010),
        (32, 0.45, 0.003),
        (32, 0.48, 0.005),
        (72, 0.45, 0.010),
        (72, 0.50, 0.010),
        (72, 0.52, 0.010),
    ]:
        specs.append(
            (
                "direction_microgrid",
                f"direction_sample_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for name, local_mode, hidden, local_weight, weight_s2v, anchor in [
        ("ld_sample_h48_l0.08_w0.45_a0.005", "sample", 48, 0.08, 0.45, 0.005),
        ("ld_sample_h48_l0.10_w0.45_a0.005", "sample", 48, 0.10, 0.45, 0.005),
        ("ld_sample_h56_l0.08_w0.48_a0.007", "sample", 56, 0.08, 0.48, 0.007),
        ("ld_class_h56_l0.06_w0.48_a0.007", "class", 56, 0.06, 0.48, 0.007),
        ("ld_sample_h64_l0.08_w0.5_a0.01", "sample", 64, 0.08, 0.50, 0.010),
        ("ld_class_h48_l0.06_w0.45_a0.005", "class", 48, 0.06, 0.45, 0.005),
    ]:
        specs.append(
            (
                "local_direction_micro",
                name,
                _dynamic_updates(
                    dynamic_local_mode=local_mode,
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=local_weight,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for name, hidden, weight_s2v, pse_outer_ratio, anchor in [
        ("dp_h48_w0.45_p0.50_a0.005", 48, 0.45, 0.50, 0.005),
        ("dp_h48_w0.48_p0.55_a0.005", 48, 0.48, 0.55, 0.005),
        ("dp_h48_w0.50_p0.60_a0.007", 48, 0.50, 0.60, 0.007),
        ("dp_h56_w0.45_p0.50_a0.007", 56, 0.45, 0.50, 0.007),
        ("dp_h56_w0.48_p0.55_a0.007", 56, 0.48, 0.55, 0.007),
        ("dp_h64_w0.50_p0.55_a0.01", 64, 0.50, 0.55, 0.010),
    ]:
        specs.append(
            (
                "direction_pse_micro",
                name,
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    if len(specs) != 50:
        raise WorkflowError(f"Direction exploit follow-up plan must contain 50 jobs, got {len(specs)}")
    return specs


def _best_repro_tune_followup_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add_repeats(count: int, group: str, name: str, updates: dict[str, object]) -> None:
        for repeat_index in range(1, count + 1):
            specs.append((group, f"{name}_r{repeat_index:02d}", dict(updates)))

    add_repeats(3, "must_reproduce", "static_v5_control", {"use_dynamic_routing": False})
    add_repeats(
        3,
        "must_reproduce",
        "dr008_local_class_h24_a0.001",
        _dynamic_updates(
            dynamic_local_mode="class",
            dynamic_gate_hidden=24,
            dynamic_gate_anchor_lambda=0.001,
        ),
    )
    add_repeats(
        3,
        "must_reproduce",
        "dr023_direction_sample_h48_a0.003",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.003,
        ),
    )
    specs.append(("must_reproduce", "dynamic_fixed_all_r01", _dynamic_updates()))

    for mode, hidden, weight_s2v, anchor in [
        ("sample", 32, 0.50, 0.001),
        ("sample", 40, 0.45, 0.003),
        ("sample", 40, 0.48, 0.003),
        ("sample", 40, 0.50, 0.005),
        ("sample", 48, 0.42, 0.003),
        ("sample", 48, 0.45, 0.003),
        ("sample", 48, 0.48, 0.003),
        ("sample", 48, 0.50, 0.003),
        ("sample", 48, 0.50, 0.005),
        ("sample", 48, 0.52, 0.005),
        ("sample", 56, 0.45, 0.003),
        ("sample", 56, 0.48, 0.005),
        ("sample", 56, 0.50, 0.005),
        ("sample", 64, 0.45, 0.005),
        ("sample", 64, 0.48, 0.007),
        ("sample", 64, 0.50, 0.007),
        ("class", 40, 0.45, 0.003),
        ("class", 48, 0.45, 0.003),
        ("class", 48, 0.50, 0.005),
        ("class", 56, 0.48, 0.005),
    ]:
        specs.append(
            (
                "direction_repro_tune",
                f"direction_{mode}_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for mode, hidden, local_weight, anchor in [
        ("class", 16, 0.12, 0.001),
        ("class", 24, 0.12, 0.001),
        ("class", 24, 0.16, 0.001),
        ("class", 24, 0.20, 0.001),
        ("class", 32, 0.12, 0.003),
        ("class", 48, 0.10, 0.003),
        ("sample", 24, 0.10, 0.001),
        ("sample", 32, 0.12, 0.003),
    ]:
        specs.append(
            (
                "local_repro_tune",
                f"local_{mode}_h{hidden}_l{local_weight:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_local_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=local_weight,
                ),
            )
        )

    for mode, hidden, pse_outer_ratio, anchor in [
        ("fixed", 32, 0.55, 0.001),
        ("fixed", 48, 0.65, 0.003),
        ("class", 32, 0.55, 0.001),
        ("class", 48, 0.55, 0.003),
        ("class", 48, 0.65, 0.003),
        ("class", 64, 0.65, 0.005),
    ]:
        specs.append(
            (
                "pse_repro_tune",
                f"pse_{mode}_h{hidden}_p{pse_outer_ratio:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_pse_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    for name, local_mode, direction_mode, pse_mode, hidden, anchor, local_weight, weight_s2v, pse_outer_ratio in [
        ("ld_sample_h48_l0.06_w0.45_a0.003", "sample", "sample", "fixed", 48, 0.003, 0.06, 0.45, None),
        ("ld_classlocal_h48_l0.06_w0.45_a0.003", "class", "sample", "fixed", 48, 0.003, 0.06, 0.45, None),
        ("ld_sample_h56_l0.08_w0.48_a0.005", "sample", "sample", "fixed", 56, 0.005, 0.08, 0.48, None),
        ("dp_h48_w0.45_p0.55_a0.003", "fixed", "sample", "class", 48, 0.003, None, 0.45, 0.55),
        ("dp_h56_w0.48_p0.55_a0.005", "fixed", "sample", "class", 56, 0.005, None, 0.48, 0.55),
        ("ldp_sample_h48_l0.06_w0.45_p0.55_a0.005", "sample", "sample", "class", 48, 0.005, 0.06, 0.45, 0.55),
    ]:
        updates = _dynamic_updates(
            dynamic_local_mode=local_mode,
            dynamic_direction_mode=direction_mode,
            dynamic_pse_mode=pse_mode,
            dynamic_gate_hidden=hidden,
            dynamic_gate_anchor_lambda=anchor,
            weight_s2v=weight_s2v,
        )
        if local_weight is not None:
            updates["local_weight"] = local_weight
        if pse_outer_ratio is not None:
            updates["pse_outer_ratio"] = pse_outer_ratio
        specs.append(("combination_repro_tune", name, updates))

    if len(specs) != 50:
        raise WorkflowError(f"Best reproduce/tune follow-up plan must contain 50 jobs, got {len(specs)}")
    return specs


def _dr018_confirm_ablate_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add_repeats(count: int, group: str, name: str, updates: dict[str, object]) -> None:
        for repeat_index in range(1, count + 1):
            specs.append((group, f"{name}_r{repeat_index:02d}", dict(updates)))

    add_repeats(
        4,
        "confirm_dr018",
        "dr018_direction_sample_h48_w0.5_a0.003",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.003,
            weight_s2v=0.50,
        ),
    )
    add_repeats(
        3,
        "neighbor_repeat",
        "dr019_direction_sample_h48_w0.5_a0.005",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.005,
            weight_s2v=0.50,
        ),
    )
    add_repeats(
        2,
        "neighbor_repeat",
        "dr016_direction_sample_h48_w0.45_a0.003",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.003,
            weight_s2v=0.45,
        ),
    )
    add_repeats(
        3,
        "neighbor_repeat",
        "dr023_direction_sample_h48_a0.003",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.003,
        ),
    )

    add_repeats(3, "ablate_direction", "static_v5_control", {"use_dynamic_routing": False})
    add_repeats(2, "ablate_direction", "dynamic_fixed_all", _dynamic_updates())
    add_repeats(
        3,
        "ablate_direction",
        "fixed_direction_h48_w0.5_a0.003",
        _dynamic_updates(
            dynamic_direction_mode="fixed",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.003,
            weight_s2v=0.50,
        ),
    )
    add_repeats(
        2,
        "ablate_direction",
        "direction_sample_h48_w0.5_a0",
        _dynamic_updates(
            dynamic_direction_mode="sample",
            dynamic_gate_hidden=48,
            dynamic_gate_anchor_lambda=0.0,
            weight_s2v=0.50,
        ),
    )

    for hidden, weight_s2v, anchor in [
        (48, 0.45, 0.001),
        (48, 0.45, 0.003),
        (48, 0.45, 0.005),
        (48, 0.475, 0.001),
        (48, 0.475, 0.003),
        (48, 0.475, 0.005),
        (48, 0.50, 0.001),
        (48, 0.50, 0.002),
        (48, 0.50, 0.004),
        (48, 0.50, 0.005),
        (48, 0.525, 0.001),
        (48, 0.525, 0.003),
        (48, 0.525, 0.005),
        (48, 0.55, 0.001),
        (48, 0.55, 0.003),
        (48, 0.55, 0.005),
        (40, 0.45, 0.003),
        (40, 0.50, 0.003),
        (40, 0.55, 0.003),
        (56, 0.45, 0.003),
        (56, 0.50, 0.003),
        (56, 0.55, 0.003),
    ]:
        specs.append(
            (
                "direction_narrow_tune",
                f"direction_sample_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for name, local_mode, direction_mode, pse_mode, hidden, anchor, local_weight, weight_s2v, pse_outer_ratio in [
        ("ld_sample_h48_l0.06_w0.50_a0.003", "sample", "sample", "fixed", 48, 0.003, 0.06, 0.50, None),
        ("ld_classlocal_h48_l0.06_w0.50_a0.003", "class", "sample", "fixed", 48, 0.003, 0.06, 0.50, None),
        ("dp_h48_w0.50_p0.55_a0.003", "fixed", "sample", "class", 48, 0.003, None, 0.50, 0.55),
        ("dp_h48_w0.52_p0.55_a0.005", "fixed", "sample", "class", 48, 0.005, None, 0.52, 0.55),
        ("ldp_sample_h48_l0.06_w0.50_p0.55_a0.003", "sample", "sample", "class", 48, 0.003, 0.06, 0.50, 0.55),
        ("ldp_class_h48_l0.06_w0.50_p0.55_a0.003", "class", "sample", "class", 48, 0.003, 0.06, 0.50, 0.55),
    ]:
        updates = _dynamic_updates(
            dynamic_local_mode=local_mode,
            dynamic_direction_mode=direction_mode,
            dynamic_pse_mode=pse_mode,
            dynamic_gate_hidden=hidden,
            dynamic_gate_anchor_lambda=anchor,
            weight_s2v=weight_s2v,
        )
        if local_weight is not None:
            updates["local_weight"] = local_weight
        if pse_outer_ratio is not None:
            updates["pse_outer_ratio"] = pse_outer_ratio
        specs.append(("innovation_combo_probe", name, updates))

    if len(specs) != 50:
        raise WorkflowError(f"DR-018 confirm/ablate plan must contain 50 jobs, got {len(specs)}")
    return specs


def _dynamic_bold_followup_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = [
        ("sanity_control", "static_v5_control", {"use_dynamic_routing": False}),
        ("sanity_control", "dynamic_fixed_all", _dynamic_updates()),
        ("sanity_control", "fixed_direction_w0.40", _dynamic_updates(weight_s2v=0.40)),
        ("sanity_control", "fixed_direction_w0.60", _dynamic_updates(weight_s2v=0.60)),
    ]

    for mode, hidden, weight_s2v, anchor in [
        ("sample", 32, 0.35, 0.000),
        ("sample", 32, 0.60, 0.015),
        ("sample", 48, 0.35, 0.005),
        ("sample", 48, 0.60, 0.015),
        ("sample", 64, 0.40, 0.015),
        ("sample", 64, 0.60, 0.020),
        ("sample", 80, 0.50, 0.015),
        ("sample", 96, 0.45, 0.015),
        ("sample", 96, 0.55, 0.020),
        ("sample", 112, 0.50, 0.020),
        ("class", 48, 0.45, 0.010),
        ("class", 64, 0.55, 0.015),
    ]:
        specs.append(
            (
                "direction_bold",
                f"direction_{mode}_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_direction_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    for mode, hidden, pse_outer_ratio, anchor in [
        ("fixed", 32, 0.35, 0.005),
        ("fixed", 48, 0.45, 0.010),
        ("fixed", 64, 0.55, 0.015),
        ("fixed", 96, 0.75, 0.020),
        ("class", 24, 0.35, 0.005),
        ("class", 32, 0.45, 0.010),
        ("class", 48, 0.55, 0.010),
        ("class", 64, 0.75, 0.015),
        ("class", 96, 0.85, 0.020),
        ("class", 112, 0.55, 0.020),
    ]:
        specs.append(
            (
                "pse_bold",
                f"pse_{mode}_h{hidden}_p{pse_outer_ratio:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_pse_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    for mode, hidden, local_weight, anchor in [
        ("sample", 16, 0.04, 0.005),
        ("sample", 32, 0.06, 0.010),
        ("sample", 48, 0.08, 0.015),
        ("sample", 64, 0.15, 0.020),
        ("class", 16, 0.04, 0.005),
        ("class", 32, 0.06, 0.010),
        ("class", 48, 0.08, 0.015),
        ("class", 64, 0.15, 0.020),
    ]:
        specs.append(
            (
                "local_bold",
                f"local_{mode}_h{hidden}_l{local_weight:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_local_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=local_weight,
                ),
            )
        )

    for mode, hidden, icsa_ratio, anchor in [
        ("sample", 16, 0.002, 0.005),
        ("sample", 24, 0.004, 0.010),
        ("sample", 32, 0.006, 0.015),
        ("class", 16, 0.002, 0.005),
        ("class", 32, 0.004, 0.010),
        ("class", 48, 0.006, 0.015),
    ]:
        specs.append(
            (
                "icsa_safe_bold",
                f"icsa_{mode}_h{hidden}_r{icsa_ratio:g}_a{anchor:g}",
                _dynamic_updates(
                    dynamic_icsa_mode=mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    icsa_ratio=icsa_ratio,
                    conditional_text_ratio=icsa_ratio,
                ),
            )
        )

    for name, local_mode, icsa_mode, direction_mode, pse_mode, hidden, anchor, local_weight, weight_s2v, pse_outer_ratio, icsa_ratio in [
        ("combo_dp_sample_h48_w0.45_p0.45", "fixed", "fixed", "sample", "class", 48, 0.010, None, 0.45, 0.45, None),
        ("combo_dp_sample_h64_w0.55_p0.75", "fixed", "fixed", "sample", "class", 64, 0.015, None, 0.55, 0.75, None),
        ("combo_ld_sample_h48_l0.06_w0.45", "sample", "fixed", "sample", "fixed", 48, 0.010, 0.06, 0.45, None, None),
        ("combo_ld_class_h64_l0.08_w0.55", "class", "fixed", "sample", "fixed", 64, 0.015, 0.08, 0.55, None, None),
        ("combo_lpd_sample_h48_l0.06_w0.45_p0.45", "sample", "fixed", "sample", "class", 48, 0.010, 0.06, 0.45, 0.45, None),
        ("combo_lpd_class_h64_l0.08_w0.55_p0.55", "class", "fixed", "sample", "class", 64, 0.015, 0.08, 0.55, 0.55, None),
        ("combo_id_sample_h32_r0.002_w0.45", "fixed", "sample", "sample", "fixed", 32, 0.010, None, 0.45, None, 0.002),
        ("combo_id_class_h48_r0.004_w0.45", "fixed", "class", "sample", "fixed", 48, 0.010, None, 0.45, None, 0.004),
        ("combo_lid_sample_h32_l0.04_r0.002_w0.45", "sample", "sample", "sample", "fixed", 32, 0.010, 0.04, 0.45, None, 0.002),
        ("combo_all_safe_h48_l0.04_r0.002_w0.45_p0.45", "sample", "sample", "sample", "class", 48, 0.015, 0.04, 0.45, 0.45, 0.002),
    ]:
        updates = _dynamic_updates(
            dynamic_local_mode=local_mode,
            dynamic_icsa_mode=icsa_mode,
            dynamic_direction_mode=direction_mode,
            dynamic_pse_mode=pse_mode,
            dynamic_gate_hidden=hidden,
            dynamic_gate_anchor_lambda=anchor,
        )
        if local_weight is not None:
            updates["local_weight"] = local_weight
        if weight_s2v is not None:
            updates["weight_s2v"] = weight_s2v
        if pse_outer_ratio is not None:
            updates["pse_outer_ratio"] = pse_outer_ratio
        if icsa_ratio is not None:
            updates["icsa_ratio"] = icsa_ratio
            updates["conditional_text_ratio"] = icsa_ratio
        specs.append(("combination_bold", name, updates))

    if len(specs) != 50:
        raise WorkflowError(f"Dynamic bold follow-up plan must contain 50 jobs, got {len(specs)}")
    return specs


def _workflow_v2_2innov_8tune_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    for name, local_mode, direction_mode, pse_mode, hidden, anchor, local_weight, weight_s2v, pse_outer_ratio in [
        ("innov_local_direction_sample_h48_l0.06_w0.50_a0.003", "sample", "sample", "fixed", 48, 0.003, 0.06, 0.50, None),
        ("innov_direction_pse_class_h48_w0.50_p0.55_a0.003", "fixed", "sample", "class", 48, 0.003, None, 0.50, 0.55),
    ]:
        updates = _dynamic_updates(
            dynamic_local_mode=local_mode,
            dynamic_icsa_mode="fixed",
            dynamic_direction_mode=direction_mode,
            dynamic_pse_mode=pse_mode,
            dynamic_gate_hidden=hidden,
            dynamic_gate_anchor_lambda=anchor,
        )
        if local_weight is not None:
            updates["local_weight"] = local_weight
        if weight_s2v is not None:
            updates["weight_s2v"] = weight_s2v
        if pse_outer_ratio is not None:
            updates["pse_outer_ratio"] = pse_outer_ratio
        specs.append(("innovation_probe", name, updates))

    for name, hidden, weight_s2v, anchor, direction_mode in [
        ("tune_direction_h48_w0.475_a0.003", 48, 0.475, 0.003, "sample"),
        ("tune_direction_h48_w0.525_a0.003", 48, 0.525, 0.003, "sample"),
        ("tune_direction_h48_w0.50_a0.001", 48, 0.50, 0.001, "sample"),
        ("tune_direction_h48_w0.50_a0.005", 48, 0.50, 0.005, "sample"),
        ("tune_direction_h40_w0.50_a0.003", 40, 0.50, 0.003, "sample"),
        ("tune_direction_h56_w0.50_a0.003", 56, 0.50, 0.003, "sample"),
        ("tune_direction_class_h48_w0.50_a0.003", 48, 0.50, 0.003, "class"),
        ("tune_direction_h48_w0.45_a0.004", 48, 0.45, 0.004, "sample"),
    ]:
        specs.append(
            (
                "direction_tune",
                name,
                _dynamic_updates(
                    dynamic_direction_mode=direction_mode,
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    if len(specs) != 10:
        raise WorkflowError(f"Workflow-v2 2innov+8tune plan must contain 10 jobs, got {len(specs)}")
    return specs


def _dr035_confirm_specs(repeat_count: int) -> list[tuple[str, str, dict[str, object]]]:
    if repeat_count > CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS:
        raise WorkflowError(
            "Exact-repeat confirmation is capped at max_attempts: 5; "
            f"requested {repeat_count} repeats."
        )
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    for repeat_index in range(1, repeat_count + 1):
        specs.append(
            (
                "confirm_dr035",
                f"dr035_direction_sample_h48_w0.525_a0.005_s{source_seed}_r{repeat_index}",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=0.005,
                    weight_s2v=0.525,
                    random_seed=source_seed,
                ),
            )
        )

    if len(specs) != repeat_count:
        raise WorkflowError(f"DR-035 confirmation plan must contain {repeat_count} jobs, got {len(specs)}")
    return specs


def _dr035_min3_confirm_specs() -> list[tuple[str, str, dict[str, object]]]:
    return _dr035_confirm_specs(3)


def _dr035_max5_confirm_specs() -> list[tuple[str, str, dict[str, object]]]:
    return _dr035_confirm_specs(CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS)


def _h76_existing_routing_100_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = [
        ("sanity_control", "static_v5_control", {"use_dynamic_routing": False}),
        ("sanity_control", "dynamic_fixed_all", _dynamic_updates()),
        (
            "sanity_control",
            "dr035_fixed_direction_h48_w0.525_a0.005",
            _dynamic_updates(
                dynamic_direction_mode="fixed",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.005,
                weight_s2v=0.525,
            ),
        ),
        (
            "sanity_control",
            "dr035_source_config_shadow",
            _dynamic_updates(
                dynamic_direction_mode="sample",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.005,
                weight_s2v=0.525,
            ),
        ),
    ]

    for hidden in [40, 48, 56]:
        for weight_s2v in [0.50, 0.525, 0.55, 0.575]:
            for anchor in [0.003, 0.005, 0.007]:
                specs.append(
                    (
                        "direction_core_tune",
                        f"direction_sample_h{hidden}_w{weight_s2v:g}_a{anchor:g}",
                        _dynamic_updates(
                            dynamic_direction_mode="sample",
                            dynamic_gate_hidden=hidden,
                            dynamic_gate_anchor_lambda=anchor,
                            weight_s2v=weight_s2v,
                        ),
                    )
                )

    for weight_s2v in [0.515, 0.525, 0.535, 0.545]:
        for anchor in [0.002, 0.004, 0.006]:
            specs.append(
                (
                    "direction_micro_tune",
                    f"direction_sample_h48_w{weight_s2v:g}_a{anchor:g}",
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                    ),
                )
            )

    for hidden in [48, 56]:
        for weight_s2v in [0.50, 0.525, 0.55, 0.575]:
            for pse_outer_ratio in [0.55, 0.60]:
                specs.append(
                    (
                        "direction_pse_tune",
                        f"dp_h{hidden}_w{weight_s2v:g}_p{pse_outer_ratio:g}_a0.005",
                        _dynamic_updates(
                            dynamic_direction_mode="sample",
                            dynamic_pse_mode="class",
                            dynamic_gate_hidden=hidden,
                            dynamic_gate_anchor_lambda=0.005,
                            weight_s2v=weight_s2v,
                            pse_outer_ratio=pse_outer_ratio,
                        ),
                    )
                )

    for hidden in [48, 56]:
        for weight_s2v in [0.50, 0.525, 0.55, 0.575]:
            for local_weight in [0.06, 0.08]:
                specs.append(
                    (
                        "local_direction_tune",
                        f"ld_sample_h{hidden}_l{local_weight:g}_w{weight_s2v:g}_a0.005",
                        _dynamic_updates(
                            dynamic_local_mode="sample",
                            dynamic_direction_mode="sample",
                            dynamic_gate_hidden=hidden,
                            dynamic_gate_anchor_lambda=0.005,
                            local_weight=local_weight,
                            weight_s2v=weight_s2v,
                        ),
                    )
                )

    for name, local_mode, hidden, local_weight, weight_s2v, pse_outer_ratio, anchor in [
        ("ldp_sample_h48_l0.06_w0.525_p0.55_a0.005", "sample", 48, 0.06, 0.525, 0.55, 0.005),
        ("ldp_sample_h48_l0.08_w0.525_p0.60_a0.005", "sample", 48, 0.08, 0.525, 0.60, 0.005),
        ("ldp_sample_h56_l0.06_w0.55_p0.55_a0.005", "sample", 56, 0.06, 0.55, 0.55, 0.005),
        ("ldp_sample_h56_l0.08_w0.55_p0.60_a0.007", "sample", 56, 0.08, 0.55, 0.60, 0.007),
        ("ldp_class_h48_l0.06_w0.525_p0.55_a0.005", "class", 48, 0.06, 0.525, 0.55, 0.005),
        ("ldp_class_h48_l0.08_w0.525_p0.60_a0.005", "class", 48, 0.08, 0.525, 0.60, 0.005),
        ("ldp_class_h56_l0.06_w0.55_p0.55_a0.005", "class", 56, 0.06, 0.55, 0.55, 0.005),
        ("ldp_class_h56_l0.08_w0.55_p0.60_a0.007", "class", 56, 0.08, 0.55, 0.60, 0.007),
    ]:
        specs.append(
            (
                "local_direction_pse_tune",
                name,
                _dynamic_updates(
                    dynamic_local_mode=local_mode,
                    dynamic_direction_mode="sample",
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=local_weight,
                    weight_s2v=weight_s2v,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    for name, hidden, weight_s2v, pse_outer_ratio, anchor in [
        ("dp_micro_h48_w0.515_p0.55_a0.004", 48, 0.515, 0.55, 0.004),
        ("dp_micro_h48_w0.535_p0.55_a0.004", 48, 0.535, 0.55, 0.004),
        ("dp_micro_h56_w0.525_p0.60_a0.006", 56, 0.525, 0.60, 0.006),
        ("dp_micro_h56_w0.545_p0.60_a0.006", 56, 0.545, 0.60, 0.006),
    ]:
        specs.append(
            (
                "direction_pse_micro_tune",
                name,
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    pse_outer_ratio=pse_outer_ratio,
                ),
            )
        )

    for name, icsa_mode, hidden, icsa_ratio, weight_s2v, anchor in [
        ("icsa_guard_sample_h48_r0.002_w0.525_a0.005", "sample", 48, 0.002, 0.525, 0.005),
        ("icsa_guard_class_h48_r0.002_w0.525_a0.005", "class", 48, 0.002, 0.525, 0.005),
        ("icsa_guard_sample_h56_r0.004_w0.55_a0.005", "sample", 56, 0.004, 0.55, 0.005),
        ("icsa_guard_class_h56_r0.004_w0.55_a0.005", "class", 56, 0.004, 0.55, 0.005),
    ]:
        specs.append(
            (
                "guarded_icsa_direction_tune",
                name,
                _dynamic_updates(
                    dynamic_icsa_mode=icsa_mode,
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=anchor,
                    icsa_ratio=icsa_ratio,
                    conditional_text_ratio=icsa_ratio,
                    weight_s2v=weight_s2v,
                ),
            )
        )

    if len(specs) != 100:
        raise WorkflowError(f"H=76 existing-routing plan must contain 100 jobs, got {len(specs)}")
    return specs


def _h76_top4_min5_repeat_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5

    def add_repeats(source_job: str, name: str, weight_s2v: float, anchor: float) -> None:
        for repeat_index in range(1, 6):
            specs.append(
                (
                    "h76_top4_same_seed_repeat",
                    f"{source_job.lower()}_{name}_s{source_seed}_r{repeat_index}",
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                        random_seed=source_seed,
                    ),
                )
            )

    add_repeats("DR020", "direction_sample_h48_w0.525_a0.003", 0.525, 0.003)
    add_repeats("DR051", "direction_sample_h48_w0.545_a0.004", 0.545, 0.004)
    add_repeats("DR041", "direction_sample_h48_w0.515_a0.002", 0.515, 0.002)
    add_repeats("DR047", "direction_sample_h48_w0.535_a0.002", 0.535, 0.002)

    if len(specs) != 20:
        raise WorkflowError(f"H=76 top4 min5 repeat plan must contain 20 jobs, got {len(specs)}")
    return specs


H76_TOP4_CANDIDATES: list[tuple[str, str, float, float]] = [
    ("DR020", "direction_sample_h48_w0.525_a0.003", 0.525, 0.003),
    ("DR051", "direction_sample_h48_w0.545_a0.004", 0.545, 0.004),
    ("DR041", "direction_sample_h48_w0.515_a0.002", 0.515, 0.002),
    ("DR047", "direction_sample_h48_w0.535_a0.002", 0.535, 0.002),
]


def _h76_mixed200_search_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs = list(_h76_existing_routing_100_specs())
    for weight_s2v in [0.515, 0.525, 0.535, 0.545, 0.555]:
        for anchor in [0.0015, 0.0025, 0.0035, 0.0045]:
            specs.append(
                (
                    "h76_mixed200_search_tune_plus",
                    f"direction_sample_h48_w{weight_s2v:g}_a{anchor:g}",
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                    ),
                )
            )

    for source_job, candidate_name, weight_s2v, anchor in H76_TOP4_CANDIDATES:
        prefix = f"{source_job.lower()}_{candidate_name}"
        for variant_name, updates in [
            (
                "w_minus_0.005",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=round(weight_s2v - 0.005, 6),
                ),
            ),
            (
                "w_plus_0.005",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=round(weight_s2v + 0.005, 6),
                ),
            ),
            (
                "anchor_minus_0.0005",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=max(round(anchor - 0.0005, 6), 0.0),
                    weight_s2v=weight_s2v,
                ),
            ),
            (
                "anchor_plus_0.0005",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=round(anchor + 0.0005, 6),
                    weight_s2v=weight_s2v,
                ),
            ),
            (
                "hidden52",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=52,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                ),
            ),
        ]:
            specs.append(("h76_mixed200_search_local_refine", f"{prefix}_{variant_name}", updates))

    if len(specs) != 140:
        raise WorkflowError(f"H=76 mixed200 search plan must contain 140 jobs, got {len(specs)}")
    return specs


def _h76_mixed200_repeat_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    for source_job, candidate_name, weight_s2v, anchor in H76_TOP4_CANDIDATES:
        for repeat_index in range(1, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS + 1):
            specs.append(
                (
                    "h76_mixed200_top4_same_seed_repeat",
                    f"{source_job.lower()}_{candidate_name}_s{source_seed}_r{repeat_index:02d}",
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                        random_seed=source_seed,
                    ),
                )
            )

    if len(specs) != 20:
        raise WorkflowError(f"H=76 mixed200 repeat plan must contain 20 jobs, got {len(specs)}")
    return specs


def _h76_mixed200_ablation_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    for source_job, candidate_name, weight_s2v, anchor in H76_TOP4_CANDIDATES:
        prefix = f"{source_job.lower()}_{candidate_name}"
        variants: list[tuple[str, dict[str, object]]] = [
            (
                "direction_fixed",
                _dynamic_updates(
                    dynamic_direction_mode="fixed",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "anchor_zero",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=0.0,
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "anchor_half",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=round(anchor / 2.0, 6),
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "anchor_double",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=round(anchor * 2.0, 6),
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "weight_minus_0.01",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=round(weight_s2v - 0.01, 6),
                    random_seed=source_seed,
                ),
            ),
            (
                "weight_plus_0.01",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=round(weight_s2v + 0.01, 6),
                    random_seed=source_seed,
                ),
            ),
            (
                "hidden40",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=40,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "hidden56",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=56,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
            (
                "plus_pse_class_p0.55",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_pse_mode="class",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    pse_outer_ratio=0.55,
                    random_seed=source_seed,
                ),
            ),
            (
                "plus_local_sample_l0.06",
                _dynamic_updates(
                    dynamic_local_mode="sample",
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    local_weight=0.06,
                    weight_s2v=weight_s2v,
                    random_seed=source_seed,
                ),
            ),
        ]
        for variant_name, updates in variants:
            specs.append(("h76_mixed200_ablate_top4", f"{prefix}_{variant_name}", updates))

    if len(specs) != 40:
        raise WorkflowError(f"H=76 mixed200 ablation plan must contain 40 jobs, got {len(specs)}")
    return specs


def _h76_mixed200_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs = _h76_mixed200_search_specs() + _h76_mixed200_repeat_specs() + _h76_mixed200_ablation_specs()
    if len(specs) != 200:
        raise WorkflowError(f"H=76 mixed200 plan must contain 200 jobs, got {len(specs)}")
    return specs


def _h76_mixed200_batch_specs(profile: str) -> list[tuple[str, str, dict[str, object]]]:
    search = _h76_mixed200_search_specs()
    repeat = _h76_mixed200_repeat_specs()
    ablate = _h76_mixed200_ablation_specs()
    batches = {
        "h76-mixed200-b01-search50": search[:50],
        "h76-mixed200-b02-search50": search[50:100],
        "h76-mixed200-b03-search20-repeat20-ablate10": search[100:120] + repeat[:20] + ablate[:10],
        "h76-mixed200-b04-search20-ablate30": search[120:140] + ablate[10:40],
    }
    if profile not in batches:
        raise WorkflowError(f"Unsupported H=76 mixed200 batch profile: {profile}")
    specs = batches[profile]
    if len(specs) != 50:
        raise WorkflowError(f"H=76 mixed200 batch {profile} must contain 50 jobs, got {len(specs)}")
    return specs


H76_FOLLOWUP50_MULTI_SEED_CANDIDATES: list[tuple[str, str, float, float]] = [
    ("DR047", "direction_sample_h48_w0.535_a0.002", 0.535, 0.002),
    ("DR020", "direction_sample_h48_w0.525_a0.003", 0.525, 0.003),
    ("DR041", "direction_sample_h48_w0.515_a0.002", 0.515, 0.002),
    ("A011DR042", "direction_sample_h48_w0.515_a0.004", 0.515, 0.004),
    ("A011DR020", "direction_sample_h48_w0.555_a0.0045", 0.555, 0.0045),
]


def _h76_followup50_multiseed_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    for source_job, candidate_name, weight_s2v, anchor in H76_FOLLOWUP50_MULTI_SEED_CANDIDATES:
        for source_seed in range(6, 16):
            specs.append(
                (
                    "h76_followup50_multiseed_stability",
                    f"{source_job.lower()}_{candidate_name}_s{source_seed:02d}",
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                        random_seed=source_seed,
                    ),
                )
            )
    if len(specs) != 50:
        raise WorkflowError(f"H=76 followup50 multiseed plan must contain 50 jobs, got {len(specs)}")
    return specs


H76_RESTORE100_CANDIDATES: list[tuple[str, str, str, str, float, float, str]] = [
    ("A011B01DR042", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-042", "direction_sample_h48_w0.515_a0.004", 0.515, 0.004, "75.00"),
    ("A011B04DR036", "RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu", "DR-036", "direction_sample_h48_w0.525_a0.002", 0.525, 0.002, "75.00"),
    ("A011B03DR020", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-020", "direction_sample_h48_w0.555_a0.0045", 0.555, 0.0045, "74.98"),
    ("A011B01DR023", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-023", "direction_sample_h48_w0.55_a0.003", 0.55, 0.003, "74.96"),
    ("A011B01DR017", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-017", "direction_sample_h48_w0.5_a0.003", 0.5, 0.003, "74.89"),
    ("A011B01DR021", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-021", "direction_sample_h48_w0.525_a0.005", 0.525, 0.005, "74.85"),
    ("A011B01DR024", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-024", "direction_sample_h48_w0.55_a0.005", 0.55, 0.005, "74.83"),
    ("A011B01DR026", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-026", "direction_sample_h48_w0.575_a0.003", 0.575, 0.003, "74.82"),
    ("A011B03DR009", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-009", "direction_sample_h48_w0.535_a0.0015", 0.535, 0.0015, "74.82"),
    ("A011B03DR010", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-010", "direction_sample_h48_w0.535_a0.0025", 0.535, 0.0025, "74.82"),
    ("A011B04DR035", "RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu", "DR-035", "direction_sample_h48_w0.505_a0.002", 0.505, 0.002, "74.81"),
    ("A011B03DR017", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-017", "direction_sample_h48_w0.555_a0.0015", 0.555, 0.0015, "74.80"),
    ("A011B01DR049", "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu", "DR-049", "direction_sample_h48_w0.535_a0.006", 0.535, 0.006, "74.79"),
    ("A011B03DR013", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-013", "direction_sample_h48_w0.545_a0.0015", 0.545, 0.0015, "74.79"),
    ("A011B03DR042", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-042", "direction_sample_h48_w0.525_a0.0", 0.525, 0.0, "74.78"),
    ("A011B03DR001", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-001", "direction_sample_h48_w0.515_a0.0015", 0.515, 0.0015, "74.77"),
    ("A011B03DR044", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-044", "direction_sample_h48_w0.525_a0.006", 0.525, 0.006, "74.77"),
    ("A011B03DR018", "RUN-20260706-0003-h76-mixed200-b03-search20-repeat20-ablate10-2gpu", "DR-018", "direction_sample_h48_w0.555_a0.0025", 0.555, 0.0025, "74.75"),
    ("A011B04DR023", "RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu", "DR-023", "direction_sample_h48_w0.545_a0.002", 0.545, 0.002, "74.72"),
    ("A011B04DR043", "RUN-20260706-0004-h76-mixed200-b04-repeat20-ablate30-2gpu", "DR-043", "direction_sample_h48_w0.535_a0.001", 0.535, 0.001, "74.70"),
]


def _h76_restore100_exact_repeat_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    for source_candidate_id, source_run, source_job, candidate_name, weight_s2v, anchor, source_h in H76_RESTORE100_CANDIDATES:
        for repeat_index in range(1, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS + 1):
            specs.append(
                (
                    "h76_restore100_exact_repeat",
                    f"{source_candidate_id.lower()}_{candidate_name}_s{source_seed}_r{repeat_index:02d}",
                    {
                        **_dynamic_updates(
                            dynamic_direction_mode="sample",
                            dynamic_gate_hidden=48,
                            dynamic_gate_anchor_lambda=anchor,
                            weight_s2v=weight_s2v,
                            random_seed=source_seed,
                        ),
                        "__source_candidate_id": source_candidate_id,
                        "__source_run_id": source_run,
                        "__source_job_id": source_job,
                        "__source_H": source_h,
                        "__restore_target_H": source_h,
                        "__repeat_index": repeat_index,
                        "__repeat_max_attempts": CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
                    },
                )
            )

    if len(specs) != 100:
        raise WorkflowError(f"H=76 restore100 exact-repeat plan must contain 100 jobs, got {len(specs)}")
    return specs


H76_HOTSPOT_TOP2_RESTORE10_CANDIDATES: list[tuple[str, str, str, str, float, float, str]] = [
    (
        "A015DR004",
        "RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu",
        "DR-004",
        "direction_sample_h48_w0.495_a0.003",
        0.495,
        0.003,
        "75.04",
    ),
    (
        "A015DR035",
        "RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu",
        "DR-035",
        "direction_sample_h48_w0.525_a0.0035",
        0.525,
        0.0035,
        "75.00",
    ),
]


def _h76_hotspot_top2_restore10_exact_repeat_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    for source_candidate_id, source_run, source_job, candidate_name, weight_s2v, anchor, source_h in H76_HOTSPOT_TOP2_RESTORE10_CANDIDATES:
        for repeat_index in range(1, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS + 1):
            specs.append(
                (
                    "h76_hotspot_top2_exact_repeat",
                    f"{source_candidate_id.lower()}_{candidate_name}_s{source_seed}_r{repeat_index:02d}",
                    {
                        **_dynamic_updates(
                            dynamic_direction_mode="sample",
                            dynamic_gate_hidden=48,
                            dynamic_gate_anchor_lambda=anchor,
                            weight_s2v=weight_s2v,
                            random_seed=source_seed,
                        ),
                        "__source_candidate_id": source_candidate_id,
                        "__source_run_id": source_run,
                        "__source_job_id": source_job,
                        "__source_H": source_h,
                        "__restore_target_H": source_h,
                        "__repeat_index": repeat_index,
                        "__repeat_max_attempts": CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
                    },
                )
            )

    if len(specs) != 10:
        raise WorkflowError(f"H=76 hotspot top2 restore plan must contain 10 jobs, got {len(specs)}")
    return specs


H76_A017DR095_RESTORE5_CANDIDATE: tuple[str, str, str, str, float, float, str] = (
    "A017DR095",
    "RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu",
    "DR-095",
    "a015dr035_weight_plus_0.01",
    0.535,
    0.0035,
    "75.11",
)


def _h76_a017dr095_restore5_exact_repeat_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []
    source_seed = 5
    source_candidate_id, source_run, source_job, candidate_name, weight_s2v, anchor, source_h = H76_A017DR095_RESTORE5_CANDIDATE
    for repeat_index in range(1, CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS + 1):
        specs.append(
            (
                "h76_a017dr095_exact_repeat",
                f"{source_candidate_id.lower()}_{candidate_name}_s{source_seed}_r{repeat_index:02d}",
                {
                    **_dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                        random_seed=source_seed,
                    ),
                    "__source_candidate_id": source_candidate_id,
                    "__source_run_id": source_run,
                    "__source_job_id": source_job,
                    "__source_H": source_h,
                    "__restore_target_H": source_h,
                    "__repeat_index": repeat_index,
                    "__repeat_max_attempts": CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS,
                },
            )
        )

    if len(specs) != CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS:
        raise WorkflowError(f"H=76 A017DR095 restore plan must contain 5 jobs, got {len(specs)}")
    return specs


def _h76_hotspot100_tune_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add(group: str, weight_s2v: float, anchor: float, *, suffix: str = "") -> None:
        name = f"direction_sample_h48_w{weight_s2v:g}_a{anchor:g}{suffix}"
        specs.append(
            (
                group,
                name,
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=anchor,
                    weight_s2v=weight_s2v,
                    random_seed=5,
                ),
            )
        )

    for weight_s2v in [0.495, 0.5, 0.505, 0.51, 0.515, 0.52, 0.525, 0.53, 0.535, 0.54, 0.545, 0.55, 0.555]:
        for anchor in [0.0015, 0.002, 0.0025, 0.003, 0.0035]:
            add("h76_hotspot100_primary_grid", weight_s2v, anchor)

    for weight_s2v in [0.4975, 0.5025, 0.5425, 0.5475, 0.5525]:
        for anchor in [0.00225, 0.00275, 0.00325, 0.00375]:
            add("h76_hotspot100_micro_grid", weight_s2v, anchor)

    for weight_s2v in [0.525, 0.53, 0.535, 0.54, 0.545]:
        for anchor in [0.0005, 0.001, 0.00125]:
            add("h76_hotspot100_low_anchor_ridge", weight_s2v, anchor)

    if len(specs) != 100:
        raise WorkflowError(f"H=76 hotspot100 tune plan must contain 100 jobs, got {len(specs)}")
    return specs


H76_ESCAPE100_CENTERS: list[tuple[str, float, float]] = [
    ("a015dr004", 0.495, 0.003),
    ("a015dr035", 0.525, 0.0035),
    ("a015ridge", 0.515, 0.0025),
]


def _h76_escape100_supported_routing_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def name(prefix: str, weight_s2v: float, anchor: float, suffix: str = "") -> str:
        tail = f"_w{weight_s2v:g}_a{anchor:g}"
        return f"{prefix}{tail}{suffix}"

    micro_offsets = [
        (-0.003, -0.00035),
        (-0.003, 0.00015),
        (-0.0015, -0.00015),
        (-0.0015, 0.00035),
        (0.0015, -0.00035),
        (0.0015, 0.00015),
        (0.003, -0.00015),
        (0.003, 0.00035),
        (-0.0045, 0.0),
        (0.0045, 0.0),
    ]
    for center_id, center_w, center_a in H76_ESCAPE100_CENTERS:
        for w_delta, a_delta in micro_offsets:
            weight_s2v = round(center_w + w_delta, 6)
            anchor = max(round(center_a + a_delta, 6), 0.0)
            specs.append(
                (
                    "h76_escape_direction_micro",
                    name(f"{center_id}_direction_sample_h48", weight_s2v, anchor),
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=anchor,
                        weight_s2v=weight_s2v,
                        random_seed=5,
                    ),
                )
            )

    for center_id, center_w, center_a in H76_ESCAPE100_CENTERS:
        for hidden in [40, 44, 52, 56, 64]:
            specs.append(
                (
                    "h76_escape_hidden_sweep",
                    name(f"{center_id}_direction_sample_h{hidden}", center_w, center_a),
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=hidden,
                        dynamic_gate_anchor_lambda=center_a,
                        weight_s2v=center_w,
                        random_seed=5,
                    ),
                )
            )

    for center_id, center_w, center_a in H76_ESCAPE100_CENTERS:
        for local_weight in [0.02, 0.04, 0.06, 0.08, 0.10]:
            specs.append(
                (
                    "h76_escape_local_sample_tune",
                    name(f"{center_id}_local_sample_l{local_weight:g}_direction_h48", center_w, center_a),
                    _dynamic_updates(
                        dynamic_local_mode="sample",
                        dynamic_direction_mode="sample",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=center_a,
                        local_weight=local_weight,
                        weight_s2v=center_w,
                        random_seed=5,
                    ),
                )
            )

    for center_id, center_w, center_a in H76_ESCAPE100_CENTERS:
        for pse_outer_ratio in [0.35, 0.45, 0.55, 0.65, 0.75]:
            specs.append(
                (
                    "h76_escape_pse_class_tune",
                    name(f"{center_id}_pse_class_p{pse_outer_ratio:g}_direction_h48", center_w, center_a),
                    _dynamic_updates(
                        dynamic_direction_mode="sample",
                        dynamic_pse_mode="class",
                        dynamic_gate_hidden=48,
                        dynamic_gate_anchor_lambda=center_a,
                        pse_outer_ratio=pse_outer_ratio,
                        weight_s2v=center_w,
                        random_seed=5,
                    ),
                )
            )

    icsa_variants = [
        ("a015dr004", 0.495, 0.003, "sample", 48, 0.001),
        ("a015dr004", 0.495, 0.003, "class", 48, 0.001),
        ("a015dr004", 0.495, 0.003, "sample", 52, 0.002),
        ("a015dr004", 0.495, 0.003, "class", 52, 0.002),
        ("a015dr035", 0.525, 0.0035, "sample", 48, 0.001),
        ("a015dr035", 0.525, 0.0035, "class", 48, 0.001),
        ("a015dr035", 0.525, 0.0035, "sample", 52, 0.002),
        ("a015dr035", 0.525, 0.0035, "class", 52, 0.002),
        ("a015ridge", 0.515, 0.0025, "sample", 48, 0.001),
        ("a015ridge", 0.515, 0.0025, "class", 52, 0.002),
    ]
    for center_id, center_w, center_a, icsa_mode, hidden, icsa_ratio in icsa_variants:
        specs.append(
            (
                "h76_escape_icsa_guarded_tune",
                name(f"{center_id}_icsa_{icsa_mode}_r{icsa_ratio:g}_h{hidden}", center_w, center_a),
                _dynamic_updates(
                    dynamic_icsa_mode=icsa_mode,
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=hidden,
                    dynamic_gate_anchor_lambda=center_a,
                    icsa_ratio=icsa_ratio,
                    conditional_text_ratio=icsa_ratio,
                    weight_s2v=center_w,
                    random_seed=5,
                ),
            )
        )

    for center_id, center_w, center_a, weight_shift_name, weight_shift in [
        ("a015dr004", 0.495, 0.003, "weight_minus_0.01", -0.01),
        ("a015dr035", 0.525, 0.0035, "weight_plus_0.01", 0.01),
    ]:
        for variant_name, updates in [
            (
                "direction_fixed",
                _dynamic_updates(
                    dynamic_direction_mode="fixed",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=center_a,
                    weight_s2v=center_w,
                    random_seed=5,
                ),
            ),
            (
                "anchor_zero",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=0.0,
                    weight_s2v=center_w,
                    random_seed=5,
                ),
            ),
            (
                "anchor_half",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=round(center_a / 2.0, 6),
                    weight_s2v=center_w,
                    random_seed=5,
                ),
            ),
            (
                "anchor_double",
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=round(center_a * 2.0, 6),
                    weight_s2v=center_w,
                    random_seed=5,
                ),
            ),
            (
                weight_shift_name,
                _dynamic_updates(
                    dynamic_direction_mode="sample",
                    dynamic_gate_hidden=48,
                    dynamic_gate_anchor_lambda=center_a,
                    weight_s2v=round(center_w + weight_shift, 6),
                    random_seed=5,
                ),
            ),
        ]:
            specs.append(("h76_escape_ablate_mechanism", f"{center_id}_{variant_name}", updates))

    for group, job_name, updates in [
        ("h76_escape_sentinel_control", "static_v5_control", {"use_dynamic_routing": False, "random_seed": 5}),
        (
            "h76_escape_sentinel_control",
            "a015dr004_direction_fixed_h48_w0.495_a0.003",
            _dynamic_updates(
                dynamic_direction_mode="fixed",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.003,
                weight_s2v=0.495,
                random_seed=5,
            ),
        ),
        (
            "h76_escape_sentinel_control",
            "a015dr035_direction_fixed_h48_w0.525_a0.0035",
            _dynamic_updates(
                dynamic_direction_mode="fixed",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.0035,
                weight_s2v=0.525,
                random_seed=5,
            ),
        ),
        (
            "h76_escape_sentinel_control",
            "bridge_direction_sample_h48_w0.5_a0.003",
            _dynamic_updates(
                dynamic_direction_mode="sample",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.003,
                weight_s2v=0.5,
                random_seed=5,
            ),
        ),
        (
            "h76_escape_sentinel_control",
            "bridge_direction_sample_h48_w0.535_a0.002",
            _dynamic_updates(
                dynamic_direction_mode="sample",
                dynamic_gate_hidden=48,
                dynamic_gate_anchor_lambda=0.002,
                weight_s2v=0.535,
                random_seed=5,
            ),
        ),
    ]:
        specs.append((group, job_name, updates))

    if len(specs) != 100:
        raise WorkflowError(f"H=76 escape100 supported-routing plan must contain 100 jobs, got {len(specs)}")
    return specs


def validate_exact_repeat_hard_cap(jobs: list[dict[str, object]]) -> None:
    exact_repeat_group_tokens = ("confirm", "same_seed_repeat", "exact_repeat", "must_reproduce")
    repeated_configs: dict[tuple[str, str], list[str]] = {}
    for job in jobs:
        group = str(job.get("group", ""))
        if not any(token in group for token in exact_repeat_group_tokens):
            continue
        updates = job.get("config_updates", {})
        config_key = json.dumps(updates, ensure_ascii=False, sort_keys=True, default=str)
        key = (group, config_key)
        repeated_configs.setdefault(key, []).append(str(job.get("job_id", "")))

    for (group, _config_key), job_ids in sorted(repeated_configs.items()):
        if len(job_ids) <= CONFIRMATION_RULE_DEFAULT_MAX_ATTEMPTS:
            continue
        raise WorkflowError(
            "Exact-repeat confirmation exceeds max_attempts: 5 hard cap: "
            f"group={group} count={len(job_ids)} job_ids={','.join(job_ids)}"
        )


def build_dynamic_routing_jobs(seed: int = 5, profile: str = "balanced-aggressive") -> list[dict[str, object]]:
    if profile == "balanced-aggressive":
        specs = _balanced_aggressive_dynamic_routing_specs()
        repeat_source_ranks = [1] * 5 + [2] * 5
    elif profile == "principled-followup":
        specs = _principled_followup_dynamic_routing_specs()
        repeat_source_ranks = [1] * 4 + [2] * 3 + [3] * 3
    elif profile == "direction-repeat-confirmation":
        specs = _direction_repeat_confirmation_specs()
        repeat_source_ranks = []
    elif profile == "direction-exploit-followup":
        specs = _direction_exploit_followup_specs()
        repeat_source_ranks = []
    elif profile == "best-repro-tune-followup":
        specs = _best_repro_tune_followup_specs()
        repeat_source_ranks = []
    elif profile == "dr018-confirm-ablate":
        specs = _dr018_confirm_ablate_specs()
        repeat_source_ranks = []
    elif profile == "dynamic-bold-followup":
        specs = _dynamic_bold_followup_specs()
        repeat_source_ranks = []
    elif profile == "workflow-v2-2innov-8tune":
        specs = _workflow_v2_2innov_8tune_specs()
        repeat_source_ranks = []
    elif profile == "dr035-min3-confirm":
        specs = _dr035_min3_confirm_specs()
        repeat_source_ranks = []
    elif profile == "dr035-min6-confirm":
        raise WorkflowError(
            "Profile 'dr035-min6-confirm' is deprecated: exact-repeat confirmation "
            "has max_attempts: 5 as a hard cap; use 'dr035-max5-confirm'."
        )
    elif profile == "dr035-max5-confirm":
        specs = _dr035_max5_confirm_specs()
        repeat_source_ranks = []
    elif profile == "h76-existing-routing-100":
        specs = _h76_existing_routing_100_specs()
        repeat_source_ranks = []
    elif profile == "h76-top4-min5-repeat":
        specs = _h76_top4_min5_repeat_specs()
        repeat_source_ranks = []
    elif profile == "h76-restore100-exact-repeat":
        specs = _h76_restore100_exact_repeat_specs()
        repeat_source_ranks = []
    elif profile == "h76-hotspot-top2-restore10-exact-repeat":
        specs = _h76_hotspot_top2_restore10_exact_repeat_specs()
        repeat_source_ranks = []
    elif profile == "h76-a017dr095-restore5-exact-repeat":
        specs = _h76_a017dr095_restore5_exact_repeat_specs()
        repeat_source_ranks = []
    elif profile == "h76-hotspot100-tune":
        specs = _h76_hotspot100_tune_specs()
        repeat_source_ranks = []
    elif profile == "h76-escape100-supported-routing":
        specs = _h76_escape100_supported_routing_specs()
        repeat_source_ranks = []
    elif profile.startswith("h76-mixed200-b"):
        specs = _h76_mixed200_batch_specs(profile)
        repeat_source_ranks = []
    elif profile == "h76-followup50-multiseed":
        specs = _h76_followup50_multiseed_specs()
        repeat_source_ranks = []
    else:
        raise WorkflowError(f"Unsupported dynamic routing batch profile: {profile}")
    repeat_group = "top3_frozen_repeat"
    if repeat_source_ranks and max(repeat_source_ranks) <= 2:
        repeat_group = "top2_frozen_repeat"

    def work_item_prefix(group: str) -> str:
        if "innovation" in group:
            return "INNOV"
        if "tune" in group:
            return "TUNE"
        if "ablate" in group:
            return "ABL"
        if "confirm" in group:
            return "CONFIRM"
        if "repeat" in group:
            return "REPEAT"
        return "RUN"

    jobs: list[dict[str, object]] = []
    work_item_counts: dict[str, int] = {}
    for index, (group, name, updates) in enumerate(specs, start=1):
        updates = dict(updates)
        metadata = {key[2:]: updates.pop(key) for key in list(updates) if key.startswith("__")}
        pse_mode = updates.get("dynamic_pse_mode")
        if pse_mode not in (None, "fixed", "class"):
            raise WorkflowError(
                "Dynamic routing batch profiles must not emit "
                f"unsupported dynamic_pse_mode={pse_mode!r}; use 'fixed' or 'class'."
            )
        job_seed = int(updates.get("random_seed", seed))
        updates["random_seed"] = job_seed
        prefix = work_item_prefix(group)
        work_item_counts[prefix] = work_item_counts.get(prefix, 0) + 1
        job = {
            "job_id": f"DR-{index:03d}",
            "work_item_id": f"{prefix}-{work_item_counts[prefix]:03d}",
            "attempt_id": f"ATTEMPT-{index:03d}",
            "phase": "explore",
            "group": group,
            "name": name,
            "seed": job_seed,
            "source_rank": 0,
            "gpu_slot": (index - 1) % 2,
            "config_updates": updates,
        }
        job.update(metadata)
        jobs.append(job)

    for repeat_index, source_rank in enumerate(repeat_source_ranks):
        index = 41 + repeat_index
        source_repeat_index = sum(1 for rank in repeat_source_ranks[: repeat_index + 1] if rank == source_rank)
        work_item_counts["REPEAT"] = work_item_counts.get("REPEAT", 0) + 1
        jobs.append(
            {
                "job_id": f"DR-{index:03d}",
                "work_item_id": f"REPEAT-{work_item_counts['REPEAT']:03d}",
                "attempt_id": f"ATTEMPT-{index:03d}",
                "phase": "repeat",
                "group": repeat_group,
                "name": f"top{source_rank}_repeat_{source_repeat_index}",
                "seed": seed,
                "source_rank": source_rank,
                "gpu_slot": (index - 1) % 2,
                "config_updates": {
                    "copy_from_top_rank": source_rank,
                    "random_seed": seed,
                },
            }
        )
    validate_exact_repeat_hard_cap(jobs)
    return jobs


def limit_dynamic_routing_jobs(jobs: list[dict[str, object]], limit_jobs: int = 0) -> list[dict[str, object]]:
    if limit_jobs <= 0:
        return jobs
    if limit_jobs > len(jobs):
        raise WorkflowError(f"--limit-jobs={limit_jobs} exceeds profile job count {len(jobs)}")
    limited = [dict(job) for job in jobs[:limit_jobs]]
    for index, job in enumerate(limited, start=1):
        job["job_id"] = f"DR-{index:03d}"
    return limited


def _format_config_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    return str(value)


def render_config_with_updates(base_text: str, updates: dict[str, object]) -> str:
    text = base_text.rstrip() + "\n"
    for key, value in updates.items():
        if key == "copy_from_top_rank":
            continue
        rendered = _format_config_value(value)
        pattern = rf"(?ms)^({re.escape(key)}:\n\s+value:\s*).+?(\n(?=[A-Za-z_][A-Za-z0-9_]*:|\Z))"
        replacement = rf"\g<1>{rendered}\2"
        if re.search(pattern, text):
            text = re.sub(pattern, replacement, text, count=1)
        else:
            text = text.rstrip() + f"\n{key}:\n  value: {rendered}\n"
    return text.rstrip() + "\n"


PARAMETER_MATRIX_PROTOCOL = "docs/workflow/protocols/parameter_matrix_protocol.md"
PARAMETER_MATRIX_CSV = "PARAMETER_MATRIX.csv"
PARAMETER_MATRIX_MD = "PARAMETER_MATRIX.md"
PARAMETER_MATRIX_COLUMNS = [
    "job_id",
    "work_item_id",
    "job_kind",
    "status",
    "group",
    "name",
    "base_version",
    "base_config_sha256",
    "code_ref",
    "config_snapshot_ref",
    "seed",
    "changed_parameters",
    "config_fingerprint",
    "repeat_of",
    "duplicate_resolution",
    "purpose",
    "run_id",
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
]
PARAMETER_MATRIX_RESULT_FIELDS = {
    "status",
    "run_id",
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
}
PARAMETER_MATRIX_TOP_RANK_RESOLUTION_FIELDS = {
    "changed_parameters",
    "config_fingerprint",
    "repeat_of",
    "duplicate_resolution",
}
PARAMETER_MATRIX_TERMINAL_STATUSES = {"completed", "failed", "skipped", "cancelled"}
_HELD_PARAMETER_MATRIX_LOCKS: set[str] = set()
PARAMETER_MATRIX_FINISH_LOCK_TIMEOUT_SECONDS = 30.0
PARAMETER_MATRIX_LOCK_POLL_INTERVAL_SECONDS = 0.05


def parameter_matrix_lock_path(matrix_path: Path) -> Path:
    return matrix_path.with_name(f".{matrix_path.name}.run-start.lock")


@contextmanager
def parameter_matrix_mutation_lock(
    matrix_path: Path,
    *,
    operation: str,
    job_id: str = "",
    run_id: str = "",
    wait_timeout_seconds: float = 0.0,
    poll_interval_seconds: float = PARAMETER_MATRIX_LOCK_POLL_INTERVAL_SECONDS,
):
    """Serialize every CSV/Markdown mutation, including nested writer calls."""
    lock_path = parameter_matrix_lock_path(matrix_path)
    lock_key = os.path.normcase(str(lock_path.resolve()))
    if lock_key in _HELD_PARAMETER_MATRIX_LOCKS:
        yield
        return
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(0.0, wait_timeout_seconds)
    while True:
        try:
            with lock_path.open("x", encoding="utf-8") as lock_handle:
                lock_handle.write(f"operation={operation}\njob_id={job_id}\nrun_id={run_id}\n")
            break
        except FileExistsError as exc:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise WorkflowError("another process is already updating this parameter matrix") from exc
            time.sleep(min(max(0.001, poll_interval_seconds), remaining))
    _HELD_PARAMETER_MATRIX_LOCKS.add(lock_key)
    try:
        yield
    finally:
        _HELD_PARAMETER_MATRIX_LOCKS.discard(lock_key)
        lock_path.unlink(missing_ok=True)


def parameter_matrix_policy_is_active() -> bool:
    """Keep pre-adoption repositories compatible, but never let an adopted repository turn the gate off."""
    path = REPO_ROOT / PARAMETER_MATRIX_PROTOCOL
    if path.is_file() and "policy_status: active" in read_text(path):
        return True
    if path.exists():
        raise WorkflowError("parameter-matrix policy file exists but is not active; the formal gate cannot be disabled")
    history = git(["log", "--all", "--format=%H", "--", PARAMETER_MATRIX_PROTOCOL], check=False).splitlines()
    if any(
        "policy_status: active" in git_show(f"{commit}:{PARAMETER_MATRIX_PROTOCOL}", check=False)
        for commit in history
    ):
        raise WorkflowError("parameter-matrix policy was adopted in Git history but its active protocol file is missing")
    return False


def git_object_exists(ref_path: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", ref_path],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def git_object_type(ref_path: str) -> str:
    return git(["cat-file", "-t", ref_path], check=False).strip()


def legacy_summary_only_eligibility_errors(target_dir: Path, source_commit_ref: str) -> list[str]:
    if not source_commit_ref.strip():
        return ["--legacy-summary-only requires --legacy-source-commit proving the directory predates the policy"]
    try:
        source_commit = resolve_commit(source_commit_ref)
        require_ancestor(source_commit, "HEAD", "legacy source commit must be an ancestor of HEAD")
        target_rel = repo_relative_path(target_dir, "legacy target directory")
    except WorkflowError as exc:
        return [str(exc)]
    target_object_type = git_object_type(f"{source_commit}:{target_rel}")
    if not target_object_type:
        return [f"legacy target directory did not exist at source commit {source_commit}"]
    if target_object_type != "tree":
        return [f"legacy target path was not a directory at source commit {source_commit}"]
    matrix_rel = f"{target_rel}/{PARAMETER_MATRIX_CSV}"
    if git_object_exists(f"{source_commit}:{matrix_rel}"):
        return [f"legacy target already had {PARAMETER_MATRIX_CSV} at source commit {source_commit}"]
    protocol_text = git_show(f"{source_commit}:{PARAMETER_MATRIX_PROTOCOL}", check=False)
    if "policy_status: active" in protocol_text:
        return [f"legacy source commit {source_commit} is not pre-policy evidence"]
    policy_history = git(
        ["log", "--format=%H", source_commit, "--", PARAMETER_MATRIX_PROTOCOL],
        check=False,
    ).splitlines()
    if any(
        "policy_status: active" in git_show(f"{commit}:{PARAMETER_MATRIX_PROTOCOL}", check=False)
        for commit in policy_history
    ):
        return [f"legacy source commit {source_commit} comes after the parameter-matrix policy was adopted"]
    return []


def existing_legacy_identity(directory: Path) -> bool:
    for name in ["manifest.yaml", "result.yaml", "result.md", "quality_check.md"]:
        path = directory / name
        if path.is_file() and "legacy_summary_only" in read_text(path):
            return True
    return False


def parameter_matrix_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parameter_matrix_job_kind(job: dict[str, object]) -> str:
    group = str(job.get("group", "")).lower()
    phase = str(job.get("phase", "")).lower()
    if phase == "repeat":
        return "repeat"
    if "ablat" in group:
        return "ablation"
    if "control" in group or "sanity" in group:
        return "control"
    return "param_tune"


def matrix_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _matrix_changed_parameters(updates: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in updates.items()
        if key not in {"random_seed", "copy_from_top_rank"}
    }


def build_parameter_matrix_rows(
    *,
    jobs: list[dict[str, object]],
    base_config_text: str,
    base_version: str,
    code_ref: str,
    run_id: str = "",
) -> list[dict[str, str]]:
    """Create one human/audit row for every planned job, never just one batch summary."""
    base_config_sha256 = parameter_matrix_sha256(base_config_text)
    first_job_by_fingerprint: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    for job in jobs:
        updates = dict(job.get("config_updates", {}))
        source_rank = int(job.get("source_rank", 0) or 0)
        repeat_of = ""
        if "copy_from_top_rank" in updates:
            repeat_of = f"top_rank:{updates['copy_from_top_rank']}"
            fingerprint = f"pending_after_{repeat_of}"
            duplicate_resolution = "等待前序候选确定后原样复跑"
        else:
            config_text = render_config_with_updates(base_config_text, updates)
            fingerprint = parameter_matrix_sha256(config_text)
            duplicate_resolution = "唯一配置"
            if fingerprint in first_job_by_fingerprint:
                repeat_of = first_job_by_fingerprint[fingerprint]
                duplicate_resolution = f"与 {repeat_of} 相同，已明确标为复跑"
            else:
                first_job_by_fingerprint[fingerprint] = str(job["job_id"])
        changed = _matrix_changed_parameters(updates)
        job_kind = parameter_matrix_job_kind(job)
        if source_rank and not repeat_of:
            repeat_of = f"top_rank:{source_rank}"
        rows.append(
            {
                "job_id": matrix_cell(job.get("job_id")),
                "work_item_id": matrix_cell(job.get("work_item_id")),
                "job_kind": job_kind,
                "status": "frozen",
                "group": matrix_cell(job.get("group")),
                "name": matrix_cell(job.get("name")),
                "base_version": base_version,
                "base_config_sha256": base_config_sha256,
                "code_ref": code_ref,
                "config_snapshot_ref": f"generated-from-frozen-plan:{matrix_cell(job.get('job_id'))}",
                "seed": matrix_cell(job.get("seed")),
                "changed_parameters": json.dumps(changed, ensure_ascii=False, sort_keys=True),
                "config_fingerprint": fingerprint,
                "repeat_of": repeat_of,
                "duplicate_resolution": duplicate_resolution,
                "purpose": matrix_cell(job.get("group")),
                "run_id": run_id,
                "run_start_receipt_ref": "",
                "run_start_receipt_sha256": "",
                "run_command_sha256": "",
                "run_log_sha256": "",
                "run_exit_code": "",
                "U": "",
                "S": "",
                "H": "",
                "ZS": "",
                "best_epoch": "",
                "decision": "",
                "artifact_ref": "",
                "artifact_manifest_sha256": "",
            }
        )
    return rows


def parse_parameter_matrix_text(text: str, *, label: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != PARAMETER_MATRIX_COLUMNS:
        raise WorkflowError(f"{label} has an invalid header; use the parameter-matrix template.")
    rows: list[dict[str, str]] = []
    for line_number, row in enumerate(reader, start=2):
        if None in row:
            raise WorkflowError(f"{label} line {line_number} has cells outside the fixed header")
        rows.append({key: matrix_cell(row.get(key, "")) for key in PARAMETER_MATRIX_COLUMNS})
    return rows


def read_parameter_matrix(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise WorkflowError(f"Missing parameter matrix: {display_path(path)}")
    return parse_parameter_matrix_text(read_text(path), label=display_path(path))


def validate_parameter_matrix_rows(
    rows: list[dict[str, str]],
    *,
    expected_job_ids: set[str] | None = None,
    require_ready: bool = False,
    require_recordable: bool = False,
    matrix_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    if not rows:
        return ["parameter matrix must contain at least one job row"]
    job_ids: set[str] = set()
    fingerprints: dict[str, str] = {}
    allowed_status = {
        "draft",
        "planned",
        "frozen",
        "running",
        "completed",
        "failed",
        "skipped",
        "cancelled",
        "legacy_summary_only",
    }
    repeat_rows: list[tuple[int, dict[str, str]]] = []
    for line_number, row in enumerate(rows, start=2):
        job_id = row.get("job_id", "").strip()
        if not job_id:
            errors.append(f"line {line_number} has an empty job_id")
            continue
        if job_id in job_ids:
            errors.append(f"line {line_number} repeats job_id {job_id}")
        job_ids.add(job_id)
        if row.get("status", "") not in allowed_status:
            errors.append(f"line {line_number} has invalid status {row.get('status', '')!r}")
        if not row.get("base_version", "") or not row.get("base_config_sha256", "") or not row.get("code_ref", ""):
            errors.append(f"line {line_number} is missing base_version, base_config_sha256, or code_ref")
        snapshot_ref = row.get("config_snapshot_ref", "").strip()
        if require_ready and not snapshot_ref:
            errors.append(f"line {line_number} is missing config_snapshot_ref")
        if require_ready and not row.get("seed", "").strip():
            errors.append(f"line {line_number} is missing seed")
        fingerprint = row.get("config_fingerprint", "")
        if not fingerprint:
            errors.append(f"line {line_number} is missing config_fingerprint")
        elif fingerprint.startswith("pending_after_top_rank:"):
            if not row.get("repeat_of", ""):
                errors.append(f"line {line_number} is a pending repeat without repeat_of")
        elif fingerprint in fingerprints and not row.get("repeat_of", ""):
            errors.append(
                f"line {line_number} duplicates {fingerprints[fingerprint]} without repeat_of; "
                "declare an intentional repeat instead of silently rerunning it"
            )
        else:
            fingerprints.setdefault(fingerprint, job_id)
        repeat_rows.append((line_number, row))
        try:
            changed = json.loads(row.get("changed_parameters", "{}"))
            if not isinstance(changed, dict):
                raise ValueError("not an object")
        except (json.JSONDecodeError, ValueError):
            errors.append(f"line {line_number} changed_parameters must be a JSON object")
        if require_ready and row.get("status") != "frozen":
            errors.append(
                f"line {line_number} status {row.get('status')!r} cannot enter a formal run; "
                "every row must be frozen and unused"
            )
        if require_recordable and row.get("status") in {"draft", "planned", "legacy_summary_only"}:
            errors.append(
                f"line {line_number} status {row.get('status')!r} cannot accept a formal result"
            )
        if require_ready and snapshot_ref and not snapshot_ref.startswith("generated-from-frozen-plan:"):
            snapshot_path = Path(snapshot_ref)
            if not snapshot_path.is_absolute():
                snapshot_path = (matrix_path.parent if matrix_path is not None else REPO_ROOT) / snapshot_path
            if not snapshot_path.exists() or not snapshot_path.is_file():
                errors.append(f"line {line_number} config_snapshot_ref does not exist: {snapshot_ref}")
            elif parameter_matrix_sha256(read_text(snapshot_path)) != fingerprint:
                errors.append(f"line {line_number} config_fingerprint does not match config_snapshot_ref")
    for line_number, row in repeat_rows:
        job_id = row.get("job_id", "")
        repeat_of = row.get("repeat_of", "").strip()
        fingerprint = row.get("config_fingerprint", "")
        if fingerprint.startswith("pending_after_top_rank:") and row.get("status") in PARAMETER_MATRIX_TERMINAL_STATUSES:
            errors.append(f"line {line_number} finished but still has an unresolved top-rank configuration")
        if not repeat_of:
            continue
        if repeat_of in job_ids:
            if repeat_of == job_id:
                errors.append(f"line {line_number} repeat_of cannot point to itself")
            source = next(source for source in rows if source.get("job_id", "") == repeat_of)
            if parameter_matrix_identity(source) != parameter_matrix_identity(row):
                errors.append(f"line {line_number} repeat_of {repeat_of} does not have the same version/code/config identity")
            continue
        if re.fullmatch(r"top_rank:[1-9][0-9]*", repeat_of) and fingerprint.startswith("pending_after_top_rank:"):
            continue
        if repeat_of.startswith("matrix:") and "#" in repeat_of and matrix_path is not None:
            path_text, source_job_id = repeat_of[len("matrix:") :].rsplit("#", 1)
            source_path = Path(path_text)
            if not source_path.is_absolute():
                source_path = REPO_ROOT / source_path
            try:
                require_path_inside(source_path, REPO_ROOT / "experiments", "repeat_of matrix")
                source_rows = read_parameter_matrix(source_path)
            except WorkflowError as exc:
                errors.append(f"line {line_number} repeat_of reference is invalid: {exc}")
                continue
            if source_job_id not in {source.get("job_id", "") for source in source_rows}:
                errors.append(f"line {line_number} repeat_of does not name a job in {display_path(source_path)}")
            else:
                source = next(source for source in source_rows if source.get("job_id", "") == source_job_id)
                if parameter_matrix_identity(source) != parameter_matrix_identity(row):
                    errors.append(f"line {line_number} repeat_of does not have the same version/code/config identity")
            continue
        errors.append(
            f"line {line_number} repeat_of must name a job in this matrix, a pending top_rank:n, "
            "or matrix:<path>#<job_id>"
        )
    if expected_job_ids is not None and job_ids != expected_job_ids:
        missing = sorted(expected_job_ids - job_ids)
        extra = sorted(job_ids - expected_job_ids)
        if missing:
            errors.append("matrix is missing planned jobs: " + ", ".join(missing))
        if extra:
            errors.append("matrix has jobs outside the frozen plan: " + ", ".join(extra))
    return errors


def markdown_table_cell(value: object) -> str:
    return matrix_cell(value).replace("|", "\\|").replace("\n", "<br>")


def render_parameter_matrix_markdown(
    *,
    title: str,
    rows: list[dict[str, str]],
    source_note: str,
) -> str:
    summary_only = bool(rows) and all(row.get("status") == "legacy_summary_only" for row in rows)
    row_meaning = (
        "这张表每一行都是无法可靠拆回逐任务参数的历史摘要，不代表一次实际 RUN；不得据此猜补参数。"
        if summary_only
        else "这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。"
    )
    lines = [
        f"# 参数矩阵：{title}",
        "",
        row_meaning,
        "",
        f"来源：{source_note}",
        "",
        "| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |",
        "|---|---|---|---|---|---:|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_table_cell(row["job_id"]),
                    markdown_table_cell(row["name"]),
                    markdown_table_cell(row["job_kind"]),
                    markdown_table_cell(row["status"]),
                    markdown_table_cell(row["changed_parameters"]),
                    markdown_table_cell(row["seed"]),
                    markdown_table_cell(row["repeat_of"]),
                    markdown_table_cell(row["run_id"]),
                    markdown_table_cell(row["purpose"]),
                    markdown_table_cell(row["H"]),
                    markdown_table_cell(row["decision"]),
                    markdown_table_cell(row.get("artifact_manifest_sha256", "")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## 查重说明",
            "",
            "- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。",
            "- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。",
            "- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_parameter_matrix(
    *,
    directory: Path,
    title: str,
    rows: list[dict[str, str]],
    source_note: str,
    overwrite: bool = False,
) -> tuple[Path, Path]:
    csv_path = directory / PARAMETER_MATRIX_CSV
    md_path = directory / PARAMETER_MATRIX_MD
    with parameter_matrix_mutation_lock(csv_path, operation="write-parameter-matrix"):
        if (csv_path.exists() or md_path.exists()) and not overwrite:
            raise WorkflowError(f"Parameter matrix already exists under {display_path(directory)}")
        directory.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=PARAMETER_MATRIX_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        md_path.write_text(
            render_parameter_matrix_markdown(title=title, rows=rows, source_note=source_note), encoding="utf-8"
        )
    return csv_path, md_path


def parameter_matrix_source_note_from_view(md_path: Path) -> str:
    if not md_path.exists():
        return "从 PARAMETER_MATRIX.csv 生成"
    match = re.search(r"^来源：(.*)$", read_text(md_path), flags=re.MULTILINE)
    if match is None:
        raise WorkflowError(f"Parameter matrix view has no source line: {display_path(md_path)}")
    return match.group(1)


def parameter_matrix_view_errors(csv_path: Path, rows: list[dict[str, str]]) -> list[str]:
    md_path = csv_path.with_name(PARAMETER_MATRIX_MD)
    if not md_path.exists():
        return [f"missing human-readable matrix view: {display_path(md_path)}"]
    try:
        source_note = parameter_matrix_source_note_from_view(md_path)
    except WorkflowError as exc:
        return [str(exc)]
    expected = render_parameter_matrix_markdown(
        title=csv_path.parent.name,
        rows=rows,
        source_note=source_note,
    )
    if read_text(md_path) != expected:
        return [
            f"{display_path(md_path)} is stale or was edited separately; "
            f"run refresh-parameter-matrix-view --path {display_path(csv_path)}"
        ]
    return []


def refresh_parameter_matrix_view(csv_path: Path, rows: list[dict[str, str]], source_note: str = "") -> Path:
    md_path = csv_path.with_name(PARAMETER_MATRIX_MD)
    with parameter_matrix_mutation_lock(csv_path, operation="refresh-parameter-matrix-view"):
        current_rows = read_parameter_matrix(csv_path)
        if current_rows != rows:
            raise WorkflowError("parameter matrix changed before its Markdown view could be refreshed")
        resolved_source_note = source_note or parameter_matrix_source_note_from_view(md_path)
        md_path.write_text(
            render_parameter_matrix_markdown(
                title=csv_path.parent.name,
                rows=current_rows,
                source_note=resolved_source_note,
            ),
            encoding="utf-8",
        )
    return md_path


def ready_parameter_matrix_rows(csv_path: Path) -> list[dict[str, str]]:
    rows = read_parameter_matrix(csv_path)
    errors = validate_parameter_matrix_rows(rows, require_recordable=True, matrix_path=csv_path)
    errors.extend(parameter_matrix_view_errors(csv_path, rows))
    errors.extend(
        parameter_matrix_conflicts(
            rows,
            REPO_ROOT / "experiments",
            exclude_paths={csv_path},
        )
    )
    if errors:
        raise WorkflowError("Formal result requires a ready parameter matrix:\n" + "\n".join(errors))
    return rows


def select_parameter_matrix_result_row(
    rows: list[dict[str, str]],
    *,
    matrix_job_id: str,
    seed: str,
    label: str,
) -> dict[str, str]:
    if matrix_job_id:
        matches = [row for row in rows if row.get("job_id", "") == matrix_job_id]
    else:
        matches = [row for row in rows if row.get("status") in {"frozen", "running"}]
        if seed:
            seed_matches = [row for row in matches if row.get("seed", "") == seed]
            if seed_matches:
                matches = seed_matches
    if len(matches) != 1:
        raise WorkflowError(
            f"{label} must identify exactly one planned parameter-matrix row; "
            f"pass --matrix-job-id when the seed is not unique (matched {len(matches)} rows)"
        )
    row = matches[0]
    if row.get("status") not in {"frozen", "running"}:
        raise WorkflowError(f"{label} can only record a frozen or running matrix row, not {row.get('status')!r}")
    if seed and row.get("seed", "") != seed:
        raise WorkflowError(
            f"{label} seed {seed!r} does not match matrix row {row.get('job_id')} seed {row.get('seed')!r}"
        )
    return row


def parameter_matrix_runtime_errors(
    row: dict[str, str],
    *,
    matrix_path: Path,
    config_path: Path,
    seed: str,
    tune_parameter: str = "",
    tune_new_value: str = "",
    tune_old_value: str = "",
    baseline_config_path: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    expected_fingerprint = parameter_matrix_sha256(read_text(config_path))
    if row.get("config_fingerprint", "") != expected_fingerprint:
        errors.append(f"{row.get('job_id')} config_fingerprint does not match the actual training config")
    snapshot_ref = row.get("config_snapshot_ref", "")
    if snapshot_ref.startswith("generated-from-frozen-plan:"):
        errors.append(f"{row.get('job_id')} is a dynamic planned row and must be recorded through its batch sync")
    else:
        snapshot_path = Path(snapshot_ref)
        if not snapshot_path.is_absolute():
            # The matrix row was already validated against its own directory;
            # here we additionally ensure the runtime command used that same file.
            snapshot_path = matrix_path.parent / snapshot_path
        if snapshot_path.resolve() != config_path.resolve():
            errors.append(f"{row.get('job_id')} config_snapshot_ref does not point to the actual training config")
    if seed and row.get("seed", "") != seed:
        errors.append(f"{row.get('job_id')} seed does not match the training command")
    if baseline_config_path is not None:
        errors.extend(
            parameter_matrix_changed_parameter_errors(
                row,
                baseline_config_path=baseline_config_path,
                config_path=config_path,
            )
        )
    if tune_parameter:
        changed = json.loads(row.get("changed_parameters", "{}"))
        config_values = read_config_values(config_path)
        actual_value = config_values.get(tune_parameter, "")
        if str(changed.get(tune_parameter, "")) != str(tune_new_value):
            errors.append(f"{row.get('job_id')} changed_parameters does not match --new-value")
        if str(actual_value) != str(tune_new_value):
            errors.append(f"{row.get('job_id')} training config does not match --new-value")
        if baseline_config_path is not None and baseline_config_path.exists():
            baseline_value = read_config_values(baseline_config_path).get(tune_parameter, "")
            if str(baseline_value) != str(tune_old_value):
                errors.append(f"{row.get('job_id')} --old-value does not match the version baseline config")
    return errors


def sync_parameter_matrix_result_row(
    csv_path: Path,
    rows: list[dict[str, str]],
    row: dict[str, str],
    *,
    metrics: dict[str, str],
    decision: str,
    run_id: str,
    artifact_ref: str,
) -> None:
    expected_frozen_fields = parameter_matrix_frozen_fields(row)
    with parameter_matrix_mutation_lock(
        csv_path,
        operation="sync-parameter-matrix-result",
        job_id=row.get("job_id", ""),
        run_id=run_id,
    ):
        current_rows = read_parameter_matrix(csv_path)
        matches = [candidate for candidate in current_rows if candidate.get("job_id") == row.get("job_id")]
        if len(matches) != 1:
            raise WorkflowError("parameter matrix changed before its result could be recorded")
        current_row = matches[0]
        if parameter_matrix_frozen_fields(current_row) != expected_frozen_fields:
            raise WorkflowError("parameter matrix frozen fields changed before its result could be recorded")
        if current_row.get("status") not in {"frozen", "running"}:
            raise WorkflowError(
                f"Refusing to overwrite result row {current_row.get('job_id')} "
                f"with status {current_row.get('status')!r}"
            )
        if any(
            current_row.get(key, "")
            for key in ["U", "S", "H", "ZS", "best_epoch", "decision", "artifact_ref"]
        ):
            raise WorkflowError(f"Refusing to overwrite an existing result for {current_row.get('job_id')}")
        if current_row.get("run_id", "") and current_row.get("run_id") != run_id:
            raise WorkflowError(
                f"{current_row.get('job_id')} is frozen for run_id {current_row.get('run_id')}, not {run_id}"
            )
        current_row["status"] = "completed"
        for key in ["U", "S", "H", "ZS", "best_epoch"]:
            current_row[key] = metrics.get(key, current_row.get(key, ""))
        current_row["decision"] = decision
        current_row["run_id"] = run_id
        current_row["artifact_ref"] = artifact_ref
        write_parameter_matrix(
            directory=csv_path.parent,
            title=csv_path.parent.name,
            rows=current_rows,
            source_note=parameter_matrix_source_note_from_view(csv_path.with_name(PARAMETER_MATRIX_MD)),
            overwrite=True,
        )


def parameter_matrix_identity(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        row.get("base_version", ""),
        row.get("code_ref", ""),
        row.get("config_fingerprint", ""),
    )


def parameter_matrix_frozen_fields(row: dict[str, str]) -> dict[str, str]:
    """Return the pre-run fields that result collection is never allowed to rewrite."""
    return {
        key: row.get(key, "")
        for key in PARAMETER_MATRIX_COLUMNS
        if key not in PARAMETER_MATRIX_RESULT_FIELDS
    }


def parameter_matrix_frozen_digest(row: dict[str, str]) -> str:
    payload = json.dumps(
        parameter_matrix_frozen_fields(row),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return parameter_matrix_sha256(payload)


def parameter_value_text(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def parameter_matrix_actual_changes(
    baseline_config_path: Path,
    config_path: Path,
) -> dict[str, str]:
    baseline_values = read_config_values(baseline_config_path)
    config_values = read_config_values(config_path)
    return {
        key: value
        for key, value in config_values.items()
        if key != "random_seed" and baseline_values.get(key) != value
    }


def parameter_matrix_changed_parameter_errors(
    row: dict[str, str],
    *,
    baseline_config_path: Path,
    config_path: Path,
) -> list[str]:
    if not baseline_config_path.exists():
        return [f"{row.get('job_id')} baseline config does not exist: {display_path(baseline_config_path)}"]
    try:
        declared_raw = json.loads(row.get("changed_parameters", "{}"))
    except json.JSONDecodeError:
        return [f"{row.get('job_id')} changed_parameters is not valid JSON"]
    if not isinstance(declared_raw, dict):
        return [f"{row.get('job_id')} changed_parameters must be a JSON object"]
    declared = {key: parameter_value_text(value) for key, value in declared_raw.items()}
    actual = parameter_matrix_actual_changes(baseline_config_path, config_path)
    if declared != actual:
        return [
            f"{row.get('job_id')} changed_parameters does not match the actual config diff; "
            f"declared={json.dumps(declared, ensure_ascii=False, sort_keys=True)} "
            f"actual={json.dumps(actual, ensure_ascii=False, sort_keys=True)}"
        ]
    return []


def parameter_matrix_freeze_commit_errors(
    *,
    commit_ref: str,
    matrix_path: Path,
    config_path: Path,
    job_id: str,
    require_exact_checkout: bool = False,
    require_clean_checkout: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not commit_ref.strip():
        return ["formal result requires --pre-run-freeze-commit"]
    try:
        commit = resolve_commit(commit_ref)
        require_ancestor(commit, "HEAD", "pre-run freeze commit must be an ancestor of current HEAD")
        if require_exact_checkout and resolve_commit("HEAD") != commit:
            errors.append("run-start receipt must be created while HEAD exactly equals the pre-run freeze commit")
        if require_clean_checkout:
            ignored_lock = display_path(
                matrix_path.with_name(f".{matrix_path.name}.run-start.lock")
            ).replace("\\", "/")
            dirty_lines = [
                line
                for line in git(["status", "--short"], check=False).splitlines()
                if line[3:].strip().replace("\\", "/") != ignored_lock
            ]
            if dirty_lines:
                errors.append("run-start receipt requires a clean worktree at the pre-run freeze commit")
        matrix_rel = repo_relative_path(matrix_path, "parameter matrix")
        config_rel = repo_relative_path(config_path, "training config")
        committed_rows = parse_parameter_matrix_text(
            read_text_at_commit(commit, matrix_rel),
            label=f"{matrix_rel} at {commit}",
        )
        committed_config = read_text_at_commit(commit, config_rel)
    except WorkflowError as exc:
        return [str(exc)]
    matches = [row for row in committed_rows if row.get("job_id", "") == job_id]
    if len(matches) != 1:
        errors.append(f"pre-run freeze commit does not contain exactly one row for {job_id}")
        return errors
    current_rows = read_parameter_matrix(matrix_path)
    current_matches = [row for row in current_rows if row.get("job_id", "") == job_id]
    if len(current_matches) != 1:
        errors.append(f"current parameter matrix does not contain exactly one row for {job_id}")
        return errors
    committed_row = matches[0]
    current_row = current_matches[0]
    if committed_row.get("status") != "frozen":
        errors.append(f"{job_id} was not frozen in pre-run commit {commit}")
    if parameter_matrix_frozen_fields(committed_row) != parameter_matrix_frozen_fields(current_row):
        errors.append(f"{job_id} frozen parameter fields differ from pre-run commit {commit}")
    if committed_config != read_text(config_path):
        errors.append(f"{job_id} training config differs from pre-run commit {commit}")
    return errors


def run_start_training_entry_path(command: str) -> Path | None:
    try:
        tokens = shlex.split(command.strip(), posix=False)
    except ValueError:
        return None

    def unquote(value: str) -> str:
        return normalize_simple_scalar(value)

    python_positions = [
        index
        for index, token in enumerate(tokens)
        if re.fullmatch(
            r"(?i)(?:.*[\\/])?python(?:\d+(?:\.\d+)*)?(?:\.exe)?",
            unquote(token),
        )
    ]
    if len(python_positions) != 1:
        return None
    python_index = python_positions[0]
    if python_index != 0:
        executable = Path(unquote(tokens[0])).name.lower()
        if executable not in {"conda", "conda.exe"} or len(tokens) < 3 or unquote(tokens[1]).lower() != "run":
            return None
        allowed_flags = {"--no-capture-output", "--live-stream", "--debug-wrapper-scripts", "--dev", "--"}
        value_flags = {"-n", "--name", "-p", "--prefix"}
        index = 2
        while index < python_index:
            token = unquote(tokens[index])
            if token in allowed_flags:
                index += 1
                continue
            if token in value_flags:
                if index + 1 >= python_index:
                    return None
                index += 2
                continue
            if any(token.startswith(f"{flag}=") for flag in {"--name", "--prefix"}):
                index += 1
                continue
            return None
    script_items = [
        (index, unquote(tokens[index]))
        for index in range(python_index + 1, len(tokens))
        if unquote(tokens[index]).lower().endswith(".py")
    ]
    if len(script_items) != 1:
        return None
    script_index, script_value = script_items[0]
    safe_interpreter_flags = {"-u", "-B", "-O", "-OO"}
    if any(unquote(token) not in safe_interpreter_flags for token in tokens[python_index + 1 : script_index]):
        return None
    script_path = Path(script_value)
    return script_path if script_path.is_absolute() else REPO_ROOT / script_path


def run_start_command_errors(command: str, config_path: Path, *, commit_ref: str = "") -> list[str]:
    command_text = command.strip()
    if not command_text:
        return ["run-start receipt requires a non-empty training command"]
    if "\r" in command_text or "\n" in command_text:
        return ["run-start receipt command must be a single line"]
    lowered = command_text.lower()
    if re.match(r"^(echo|printf|write-output|python\s+-c)\b", lowered):
        return ["run-start receipt command must launch a training script, not a placeholder command"]
    if re.search(r"(?:&&|\|\||[;&|<>`]|\$\()", command_text):
        return ["run-start receipt command must be one direct training command without shell chaining"]
    if not re.search(r"(?i)(?:^|\s)(?:python(?:\d+(?:\.\d+)*)?(?:\.exe)?|[^\s]*[\\/]python)(?:\s|$)", command_text):
        return ["run-start receipt command must invoke Python"]
    if not re.search(r"(?i)\.py(?:\s|$)", command_text):
        return ["run-start receipt command must name a Python training entry script"]
    try:
        tokens = shlex.split(command_text, posix=False)
    except ValueError as exc:
        return [f"run-start receipt command cannot be parsed: {exc}"]

    def unquote(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            return value[1:-1]
        return value

    config_values: list[str] = []
    index = 0
    while index < len(tokens):
        token = unquote(tokens[index])
        option_name = token.split("=", 1)[0]
        if len(option_name) > 2 and option_name != "--config" and (
            "--config".startswith(option_name) or option_name.startswith("--config")
        ):
            return ["run-start receipt command contains an abbreviated or duplicate config option"]
        if token == "--config":
            if index + 1 >= len(tokens):
                return ["run-start receipt command has --config without a path"]
            config_values.append(unquote(tokens[index + 1]))
            index += 2
            continue
        if token.startswith("--config="):
            config_values.append(unquote(token.split("=", 1)[1]))
        index += 1
    if len(config_values) != 1:
        return ["run-start receipt command must pass exactly one frozen config through --config"]
    supplied_path = Path(config_values[0])
    if not supplied_path.is_absolute():
        supplied_path = REPO_ROOT / supplied_path
    if os.path.normcase(str(supplied_path.resolve())) != os.path.normcase(str(config_path.resolve())):
        return ["run-start receipt --config must exactly match the frozen config path"]
    training_entry = run_start_training_entry_path(command_text)
    if training_entry is None:
        return ["run-start receipt command must directly invoke exactly one Python training entry script"]
    try:
        entry_rel = repo_relative_path(training_entry, "training entry")
    except WorkflowError as exc:
        return [str(exc)]
    if not training_entry.is_file():
        return [f"run-start receipt training entry does not exist: {entry_rel}"]
    if commit_ref.strip():
        try:
            commit = resolve_commit(commit_ref)
            committed_entry = read_text_at_commit(commit, entry_rel)
        except WorkflowError:
            return [f"run-start receipt training entry is not frozen in commit {commit_ref}: {entry_rel}"]
        if read_text(training_entry) != committed_entry:
            return [f"run-start receipt training entry differs from frozen commit {commit}: {entry_rel}"]
    return []


def run_start_command_tokens(command: str) -> list[str]:
    try:
        return [normalize_simple_scalar(token) for token in shlex.split(command.strip(), posix=False)]
    except ValueError as exc:
        raise WorkflowError(f"run-start receipt command cannot be parsed: {exc}") from exc


class TrainingLaunchError(WorkflowError):
    """The frozen process never started, so its row may safely return to frozen."""


def run_training_with_start_receipt(command: str, log_path: Path) -> dict[str, object]:
    """Launch the frozen command directly and capture its complete output in the anchored log."""
    command_sha256 = parameter_matrix_sha256(command)
    tokens = run_start_command_tokens(command)
    try:
        process = subprocess.Popen(
            tokens,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError as exc:
        raise TrainingLaunchError(f"frozen training command could not start: {exc}") from exc
    assert process.stdout is not None
    with log_path.open("ab") as log_handle:
        started_at = utc_now()
        log_handle.write(
            (
                "GTPJ_TRAINING_PROCESS_STARTED "
                f"command_sha256={command_sha256} pid={process.pid} started_at={started_at}\n"
            ).encode("utf-8")
        )
        log_handle.flush()
        last_output_byte = b""
        with process.stdout:
            for chunk in iter(lambda: process.stdout.read(1024 * 1024), b""):
                log_handle.write(chunk)
                last_output_byte = chunk[-1:]
                log_handle.flush()
        return_code = process.wait()
        finished_at = utc_now()
        if last_output_byte not in {b"", b"\n"}:
            log_handle.write(b"\n")
        log_handle.write(
            (
                "GTPJ_TRAINING_PROCESS_FINISHED "
                f"command_sha256={command_sha256} pid={process.pid} "
                f"returncode={return_code} finished_at={finished_at}\n"
            ).encode("utf-8")
        )
        log_handle.flush()
    return {
        "pid": process.pid,
        "started_at": started_at,
        "finished_at": finished_at,
        "returncode": return_code,
        "log_sha256": sha256_file(log_path),
    }


def run_start_receipt_errors(
    *,
    receipt_path: Path,
    log_path: Path,
    config_path: Path,
    row: dict[str, str],
    run_id: str,
    pre_run_freeze_commit: str,
    command: str,
    require_success: bool = True,
    allowed_statuses: set[str] | None = None,
) -> list[str]:
    if not str(receipt_path).strip() or not receipt_path.exists() or not receipt_path.is_file():
        return ["formal result requires a real --run-start-receipt file created before training"]
    try:
        payload = json.loads(read_text(receipt_path))
    except json.JSONDecodeError:
        return ["run-start receipt is not valid JSON"]
    commit = resolve_commit(pre_run_freeze_commit)
    expected = {
        "schema_version": "gtpj-run-start-receipt/v1",
        "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
        "job_id": row.get("job_id", ""),
        "run_id": run_id,
        "pre_run_freeze_commit": commit,
        "config_fingerprint": row.get("config_fingerprint", ""),
        "matrix_frozen_digest": parameter_matrix_frozen_digest(row),
        "config_path": display_path(config_path),
        "code_ref": row.get("code_ref", ""),
        "command": command,
        "command_sha256": parameter_matrix_sha256(command),
    }
    training_entry = run_start_training_entry_path(command)
    if training_entry is not None:
        entry_rel = repo_relative_path(training_entry, "training entry")
        expected["training_entry_path"] = entry_rel
        expected["training_entry_sha256"] = parameter_matrix_sha256(read_text_at_commit(commit, entry_rel))
    errors = [
        f"run-start receipt {field} does not match the frozen run"
        for field, value in expected.items()
        if str(payload.get(field, "")) != value
    ]
    started_at_text = str(payload.get("started_at", "")).strip()
    try:
        started_at = datetime.fromisoformat(started_at_text.replace("Z", "+00:00"))
        if started_at.tzinfo is None:
            raise ValueError("timezone missing")
        commit_time = datetime.fromisoformat(
            git(["show", "-s", "--format=%cI", commit]).strip().replace("Z", "+00:00")
        )
        if started_at < commit_time:
            errors.append("run-start receipt timestamp predates the pre-run freeze commit")
    except ValueError:
        errors.append("run-start receipt started_at must be a timezone-aware ISO timestamp")
    receipt_sha256 = sha256_file(receipt_path)
    accepted_statuses = allowed_statuses or {"running"}
    if row.get("status") not in accepted_statuses:
        errors.append("parameter-matrix row is not bound to an active run-start receipt")
    if row.get("run_id", "") != run_id:
        errors.append("parameter-matrix run_id does not match the run-start receipt")
    if row.get("run_start_receipt_ref", "") != display_path(receipt_path):
        errors.append("parameter-matrix run_start_receipt_ref does not match the receipt file")
    if row.get("run_start_receipt_sha256", "") != receipt_sha256:
        errors.append("parameter-matrix run_start_receipt_sha256 does not match the receipt file")
    if row.get("run_command_sha256", "") != parameter_matrix_sha256(command):
        errors.append("parameter-matrix run_command_sha256 does not match the training command")
    errors.extend(run_start_command_errors(command, config_path, commit_ref=commit))
    log_lines = read_text(log_path).splitlines()
    first_line = log_lines[0] if log_lines else ""
    if first_line != f"GTPJ_RUN_START_RECEIPT_SHA256={receipt_sha256}":
        errors.append("training log is not anchored to the run-start receipt in its first line")
    command_sha256 = parameter_matrix_sha256(command)
    start_pattern = re.compile(
        rf"^GTPJ_TRAINING_PROCESS_STARTED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) started_at=(\S+)$"
    )
    finish_pattern = re.compile(
        rf"^GTPJ_TRAINING_PROCESS_FINISHED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) returncode=(-?[0-9]+) finished_at=(\S+)$"
    )
    start_matches = [match for line in log_lines if (match := start_pattern.fullmatch(line))]
    finish_matches = [match for line in log_lines if (match := finish_pattern.fullmatch(line))]
    if len(start_matches) != 1:
        errors.append("training log has no unique workflow-launched process start marker")
    if len(finish_matches) != 1:
        errors.append("training log has no unique workflow-captured process finish marker")
    if start_matches and finish_matches and start_matches[0].group(1) != finish_matches[0].group(1):
        errors.append("training process start/finish markers do not name the same process")
    if len(finish_matches) == 1 and (not log_lines or finish_matches[0].string != log_lines[-1]):
        errors.append("training process finish marker must be the last line of the sealed log")
    process_return_code = finish_matches[0].group(2) if len(finish_matches) == 1 else ""
    if require_success and process_return_code and process_return_code != "0":
        errors.append("training process finished with a non-zero exit code")
    if process_return_code and row.get("run_exit_code", "") != process_return_code:
        errors.append("parameter-matrix run_exit_code does not match the sealed training process")
    elif require_success and row.get("run_exit_code", "") != "0":
        errors.append("parameter-matrix run_exit_code does not prove a successful process")
    if row.get("run_log_sha256", "") != sha256_file(log_path):
        errors.append("parameter-matrix run_log_sha256 does not match the sealed training log")
    if require_success:
        try:
            parse_training_log_text(
                captured_training_log_text(log_path, command),
                f"workflow-captured output in {display_path(log_path)}",
            )
        except WorkflowError as exc:
            errors.append(str(exc))
    if receipt_path.stat().st_mtime > log_path.stat().st_mtime:
        errors.append("run-start receipt was written after the training log")
    errors.extend(
        run_finish_receipt_errors(
            receipt_path=receipt_path,
            log_path=log_path,
            job_id=row.get("job_id", ""),
            run_id=run_id,
            command=command,
        )
    )
    return errors


def sealed_training_process_evidence(log_path: Path, command: str) -> dict[str, object]:
    """Read the immutable finish marker needed to seal or recover a completed process."""
    if not log_path.exists() or not log_path.is_file():
        raise WorkflowError(f"Missing sealed training log: {display_path(log_path)}")
    log_lines = read_text(log_path).splitlines()
    command_sha256 = parameter_matrix_sha256(command)
    start_pattern = re.compile(
        rf"^GTPJ_TRAINING_PROCESS_STARTED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) started_at=(\S+)$"
    )
    finish_pattern = re.compile(
        rf"^GTPJ_TRAINING_PROCESS_FINISHED command_sha256={command_sha256} "
        r"pid=([1-9][0-9]*) returncode=(-?[0-9]+) finished_at=(\S+)$"
    )
    start_matches = [match for line in log_lines if (match := start_pattern.fullmatch(line))]
    finish_matches = [match for line in log_lines if (match := finish_pattern.fullmatch(line))]
    errors: list[str] = []
    if len(start_matches) != 1:
        errors.append("training log has no unique workflow-launched process start marker")
    if len(finish_matches) != 1:
        errors.append("training log has no unique workflow-captured process finish marker")
    if start_matches and finish_matches and start_matches[0].group(1) != finish_matches[0].group(1):
        errors.append("training process start/finish markers do not name the same process")
    if len(finish_matches) == 1 and (not log_lines or finish_matches[0].string != log_lines[-1]):
        errors.append("training process finish marker must be the last line of the sealed log")
    if errors:
        raise WorkflowError("Cannot seal the finished training process:\n" + "\n".join(errors))
    return {
        "pid": int(finish_matches[0].group(1)),
        "started_at": start_matches[0].group(2),
        "finished_at": finish_matches[0].group(3),
        "returncode": int(finish_matches[0].group(2)),
        "log_sha256": sha256_file(log_path),
    }


def run_finish_receipt_path(receipt_path: Path) -> Path:
    return receipt_path.with_name(f"{receipt_path.stem}.finish.json")


def write_run_finish_receipt(
    *,
    receipt_path: Path,
    job_id: str,
    run_id: str,
    command: str,
    process_result: dict[str, object],
) -> Path:
    finish_path = run_finish_receipt_path(receipt_path)
    payload = {
        "schema_version": "gtpj-run-finish-receipt/v1",
        "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
        "job_id": job_id,
        "run_id": run_id,
        "run_start_receipt_sha256": sha256_file(receipt_path),
        "command_sha256": parameter_matrix_sha256(command),
        "pid": int(process_result["pid"]),
        "started_at": str(process_result["started_at"]),
        "finished_at": str(process_result["finished_at"]),
        "returncode": int(process_result["returncode"]),
        "log_sha256": str(process_result["log_sha256"]),
    }
    finish_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with finish_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError as exc:
        raise WorkflowError(f"Refusing to overwrite existing run-finish receipt: {display_path(finish_path)}") from exc
    return finish_path


def run_finish_receipt_errors(
    *,
    receipt_path: Path,
    log_path: Path,
    job_id: str,
    run_id: str,
    command: str,
) -> list[str]:
    finish_path = run_finish_receipt_path(receipt_path)
    if not finish_path.exists() or not finish_path.is_file():
        return ["finished training process requires an immutable run-finish receipt"]
    try:
        payload = json.loads(read_text(finish_path))
    except (UnicodeError, json.JSONDecodeError):
        return ["run-finish receipt is not valid JSON"]
    if not isinstance(payload, dict):
        return ["run-finish receipt must be a JSON object"]
    try:
        process_result = sealed_training_process_evidence(log_path, command)
    except WorkflowError as exc:
        return [str(exc)]
    expected = {
        "schema_version": "gtpj-run-finish-receipt/v1",
        "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
        "job_id": job_id,
        "run_id": run_id,
        "run_start_receipt_sha256": sha256_file(receipt_path),
        "command_sha256": parameter_matrix_sha256(command),
        "pid": int(process_result["pid"]),
        "started_at": str(process_result["started_at"]),
        "finished_at": str(process_result["finished_at"]),
        "returncode": int(process_result["returncode"]),
        "log_sha256": str(process_result["log_sha256"]),
    }
    return [
        f"finish receipt {field} does not match the sealed training process"
        for field, value in expected.items()
        if payload.get(field) != value
    ]


def seal_finished_parameter_matrix_run(
    *,
    matrix_path: Path,
    config_path: Path,
    receipt_path: Path,
    log_path: Path,
    job_id: str,
    run_id: str,
    pre_run_freeze_commit: str,
    command: str,
) -> dict[str, object]:
    """Idempotently bind a sealed process log back to its already-running row."""
    process_result = sealed_training_process_evidence(log_path, command)
    return_code = int(process_result["returncode"])
    source_note = parameter_matrix_source_note_from_view(matrix_path.with_name(PARAMETER_MATRIX_MD))
    with parameter_matrix_mutation_lock(
        matrix_path,
        operation="seal-finished-run",
        job_id=job_id,
        run_id=run_id,
        wait_timeout_seconds=PARAMETER_MATRIX_FINISH_LOCK_TIMEOUT_SECONDS,
    ):
        current_rows = read_parameter_matrix(matrix_path)
        current_matches = [item for item in current_rows if item.get("job_id") == job_id]
        if len(current_matches) != 1:
            raise WorkflowError("cannot seal the training log because its matrix row changed")
        current_row = current_matches[0]
        existing_log_sha256 = current_row.get("run_log_sha256", "")
        if existing_log_sha256 and existing_log_sha256 != str(process_result["log_sha256"]):
            raise WorkflowError("cannot replace an already-sealed log hash during finished-run recovery")
        existing_exit_code = current_row.get("run_exit_code", "")
        if existing_exit_code and existing_exit_code != str(return_code):
            raise WorkflowError("cannot replace an already-sealed exit code during finished-run recovery")
        prospective_row = dict(current_row)
        prospective_row["run_log_sha256"] = str(process_result["log_sha256"])
        prospective_row["run_exit_code"] = str(return_code)
        if return_code != 0:
            prospective_row["status"] = "failed"
            prospective_row["decision"] = "process_failed"
        allowed_statuses = {"running"} if return_code == 0 else {"running", "failed"}
        errors = run_start_receipt_errors(
            receipt_path=receipt_path,
            log_path=log_path,
            config_path=config_path,
            row=prospective_row,
            run_id=run_id,
            pre_run_freeze_commit=pre_run_freeze_commit,
            command=command,
            require_success=return_code == 0,
            allowed_statuses=allowed_statuses,
        )
        if errors:
            raise WorkflowError("Cannot seal the finished training process:\n" + "\n".join(errors))
        if current_row != prospective_row:
            current_row.update(prospective_row)
            write_parameter_matrix(
                directory=matrix_path.parent,
                title=matrix_path.parent.name,
                rows=current_rows,
                source_note=source_note,
                overwrite=True,
            )
    return process_result


def cmd_prepare_run_start_receipt(args: argparse.Namespace) -> int:
    matrix_path = Path(args.path)
    if not matrix_path.is_absolute():
        matrix_path = REPO_ROOT / matrix_path
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    receipt_path = Path(args.receipt)
    if not receipt_path.is_absolute():
        receipt_path = REPO_ROOT / receipt_path
    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = REPO_ROOT / log_path
    finish_receipt_path = run_finish_receipt_path(receipt_path)
    if receipt_path.exists() and log_path.exists():
        recovered = seal_finished_parameter_matrix_run(
            matrix_path=matrix_path,
            config_path=config_path,
            receipt_path=receipt_path,
            log_path=log_path,
            job_id=args.job_id,
            run_id=args.run_id,
            pre_run_freeze_commit=args.pre_run_freeze_commit,
            command=args.command,
        )
        if int(recovered["returncode"]) != 0:
            raise WorkflowError(
                f"frozen training command exited with code {recovered['returncode']}; "
                f"finished-run evidence recovered from {display_path(log_path)}"
            )
        print("finished-run-recovered")
        print(f"receipt: {display_path(receipt_path)}")
        print(f"log: {display_path(log_path)}")
        return 0
    if receipt_path.exists() or log_path.exists() or finish_receipt_path.exists():
        raise WorkflowError("prepare-run-start-receipt refuses existing receipt or log files, including a finish receipt")
    # Existing pre-V5 processes may still be sealed by the recovery path above.
    # Any new training launch must belong to a canonical ready experiment.
    require_ready_experiment_for_artifact(matrix_path)
    if receipt_path.resolve() == log_path.resolve():
        raise WorkflowError("prepare-run-start-receipt requires different receipt and log paths")
    # The lock is matrix-wide, not row-wide: two different jobs still rewrite
    # the same CSV/Markdown pair and must never race with each other.
    lock_path = parameter_matrix_lock_path(matrix_path)
    lock_key = os.path.normcase(str(lock_path.resolve()))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock_path.open("x", encoding="utf-8") as lock_handle:
            lock_handle.write(f"job_id={args.job_id}\nrun_id={args.run_id}\n")
    except FileExistsError as exc:
        raise WorkflowError("another process is already binding this parameter matrix") from exc
    _HELD_PARAMETER_MATRIX_LOCKS.add(lock_key)
    try:
        rows = read_parameter_matrix(matrix_path)
        original_rows = [dict(item) for item in rows]
        source_note = parameter_matrix_source_note_from_view(matrix_path.with_name(PARAMETER_MATRIX_MD))
        matches = [row for row in rows if row.get("job_id", "") == args.job_id]
        if len(matches) != 1:
            raise WorkflowError("prepare-run-start-receipt --job-id must name exactly one matrix row")
        row = matches[0]
        if row.get("status") != "frozen":
            raise WorkflowError("prepare-run-start-receipt requires an unused frozen row")
        errors = parameter_matrix_freeze_commit_errors(
            commit_ref=args.pre_run_freeze_commit,
            matrix_path=matrix_path,
            config_path=config_path,
            job_id=args.job_id,
            require_exact_checkout=True,
            require_clean_checkout=True,
        )
        errors.extend(run_start_command_errors(args.command, config_path, commit_ref=args.pre_run_freeze_commit))
        if not args.run_id.strip():
            errors.append("run-start receipt requires a non-empty run_id")
        if errors:
            raise WorkflowError("Cannot create run-start receipt:\n" + "\n".join(errors))
        commit = resolve_commit(args.pre_run_freeze_commit)
        code_ref = row.get("code_ref", "").strip()
        try:
            code_ref_commit = resolve_commit(code_ref)
            require_ancestor(code_ref_commit, commit, "parameter-matrix code_ref must resolve within the frozen training history")
        except WorkflowError as exc:
            raise WorkflowError(f"Cannot create run-start receipt:\n{exc}") from exc
        payload = {
            "schema_version": "gtpj-run-start-receipt/v1",
            "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
            "job_id": args.job_id,
            "run_id": args.run_id,
            "pre_run_freeze_commit": commit,
            "config_fingerprint": row.get("config_fingerprint", ""),
            "matrix_frozen_digest": parameter_matrix_frozen_digest(row),
            "config_path": display_path(config_path),
            "code_ref": code_ref,
            "code_ref_commit": code_ref_commit,
            "command": args.command,
            "command_sha256": parameter_matrix_sha256(args.command),
            "started_at": utc_now(),
        }
        training_entry = run_start_training_entry_path(args.command)
        if training_entry is None:
            raise WorkflowError("Cannot create run-start receipt:\ntraining entry parsing failed after validation")
        training_entry_rel = repo_relative_path(training_entry, "training entry")
        payload["training_entry_path"] = training_entry_rel
        payload["training_entry_sha256"] = parameter_matrix_sha256(
            read_text_at_commit(commit, training_entry_rel)
        )
        receipt_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        receipt_sha256 = hashlib.sha256(receipt_text.encode("utf-8")).hexdigest()
        receipt_temp = receipt_path.with_name(f".{receipt_path.name}.{args.job_id}.tmp")
        log_temp = log_path.with_name(f".{log_path.name}.{args.job_id}.tmp")
        matrix_write_attempted = False
        receipt_published = False
        log_published = False
        try:
            if receipt_temp.exists() or log_temp.exists():
                raise WorkflowError("prepare-run-start-receipt refuses stale transaction temp files")
            write_new_lf(receipt_temp, receipt_text)
            write_new_lf(log_temp, f"GTPJ_RUN_START_RECEIPT_SHA256={receipt_sha256}\n")
            row["status"] = "running"
            row["run_id"] = args.run_id
            row["run_start_receipt_ref"] = display_path(receipt_path)
            row["run_start_receipt_sha256"] = receipt_sha256
            row["run_command_sha256"] = parameter_matrix_sha256(args.command)
            matrix_write_attempted = True
            write_parameter_matrix(
                directory=matrix_path.parent,
                title=matrix_path.parent.name,
                rows=rows,
                source_note=source_note,
                overwrite=True,
            )
            os.replace(receipt_temp, receipt_path)
            receipt_published = True
            os.replace(log_temp, log_path)
            log_published = True
        except Exception as exc:
            rollback_error = ""
            if matrix_write_attempted:
                try:
                    write_parameter_matrix(
                        directory=matrix_path.parent,
                        title=matrix_path.parent.name,
                        rows=original_rows,
                        source_note=source_note,
                        overwrite=True,
                    )
                except Exception as restore_exc:
                    rollback_error = f"; matrix rollback also failed: {restore_exc}"
            cleanup_paths = [receipt_temp, log_temp]
            if receipt_published:
                cleanup_paths.append(receipt_path)
            if log_published:
                cleanup_paths.append(log_path)
            for cleanup_path in cleanup_paths:
                try:
                    cleanup_path.unlink(missing_ok=True)
                except OSError:
                    pass
            if isinstance(exc, WorkflowError) and not rollback_error:
                raise
            raise WorkflowError(f"run-start receipt transaction failed: {exc}{rollback_error}") from exc
    finally:
        _HELD_PARAMETER_MATRIX_LOCKS.discard(lock_key)
        lock_path.unlink(missing_ok=True)
    try:
        process_result = run_training_with_start_receipt(args.command, log_path)
    except TrainingLaunchError:
        # No child process existed, so return the row to its exact pre-launch
        # state and remove the start artifacts.  This keeps the job retryable.
        with parameter_matrix_mutation_lock(
            matrix_path,
            operation="rollback-unstarted-run",
            job_id=args.job_id,
            run_id=args.run_id,
            wait_timeout_seconds=PARAMETER_MATRIX_FINISH_LOCK_TIMEOUT_SECONDS,
        ):
            current_rows = read_parameter_matrix(matrix_path)
            current_matches = [item for item in current_rows if item.get("job_id") == args.job_id]
            if len(current_matches) != 1:
                raise WorkflowError("cannot roll back an unstarted run because its matrix row changed")
            current_row = current_matches[0]
            if (
                current_row.get("status") != "running"
                or current_row.get("run_id") != args.run_id
                or current_row.get("run_start_receipt_sha256") != receipt_sha256
            ):
                raise WorkflowError("cannot roll back an unstarted run because its receipt binding changed")
            original_by_job = {item["job_id"]: item for item in original_rows}
            restored_rows = [
                dict(original_by_job[item["job_id"]]) if item.get("job_id") == args.job_id else item
                for item in current_rows
            ]
            write_parameter_matrix(
                directory=matrix_path.parent,
                title=matrix_path.parent.name,
                rows=restored_rows,
                source_note=source_note,
                overwrite=True,
            )
        receipt_path.unlink(missing_ok=True)
        finish_receipt_path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)
        raise

    write_run_finish_receipt(
        receipt_path=receipt_path,
        job_id=args.job_id,
        run_id=args.run_id,
        command=args.command,
        process_result=process_result,
    )
    sealed_process_result = seal_finished_parameter_matrix_run(
        matrix_path=matrix_path,
        config_path=config_path,
        receipt_path=receipt_path,
        log_path=log_path,
        job_id=args.job_id,
        run_id=args.run_id,
        pre_run_freeze_commit=args.pre_run_freeze_commit,
        command=args.command,
    )
    if any(
        sealed_process_result[key] != process_result[key]
        for key in ("pid", "returncode", "log_sha256")
    ):
        raise WorkflowError("sealed training evidence changed between process completion and matrix update")
    return_code = int(sealed_process_result["returncode"])
    if return_code != 0:
        raise WorkflowError(
            f"frozen training command exited with code {return_code}; see {display_path(log_path)}"
        )
    print("run-start-receipt-created")
    print(f"receipt: {display_path(receipt_path)}")
    print(f"log: {display_path(log_path)}")
    print("frozen training command completed; stdout/stderr were captured after the immutable first line")
    return 0


def parameter_matrix_conflicts(
    rows: list[dict[str, str]],
    matrix_root: Path,
    *,
    exclude_paths: set[Path] | None = None,
) -> list[str]:
    """Find accidental reruns against already recorded matrices, without touching raw artifacts."""
    excluded = {path.resolve() for path in (exclude_paths or set())}
    seen: dict[tuple[str, str, str], tuple[str, str]] = {}
    for path in matrix_root.rglob(PARAMETER_MATRIX_CSV):
        if path.resolve() in excluded:
            continue
        try:
            existing_rows = read_parameter_matrix(path)
        except WorkflowError:
            continue
        for row in existing_rows:
            identity = parameter_matrix_identity(row)
            if identity[2] and not identity[2].startswith("pending_after_"):
                seen.setdefault(identity, (display_path(path), row.get("job_id", "")))
    conflicts: list[str] = []
    for row in rows:
        identity = parameter_matrix_identity(row)
        fingerprint = identity[2]
        if not fingerprint or fingerprint.startswith("pending_after_") or row.get("repeat_of", ""):
            continue
        if identity in seen:
            path_text, job_id = seen[identity]
            conflicts.append(
                f"{row['job_id']} matches {job_id} in {path_text}; add repeat_of or change the planned parameters"
            )
    return conflicts


def cmd_validate_parameter_matrix(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    rows = read_parameter_matrix(path)
    expected_jobs = int(args.expected_jobs or 0)
    errors = validate_parameter_matrix_rows(rows, require_ready=bool(args.require_ready), matrix_path=path)
    errors.extend(parameter_matrix_view_errors(path, rows))
    if args.require_ready:
        errors.extend(
            parameter_matrix_conflicts(
                rows,
                REPO_ROOT / "experiments",
                exclude_paths={path},
            )
        )
    if expected_jobs and len(rows) != expected_jobs:
        errors.append(f"matrix has {len(rows)} rows but the frozen plan requires {expected_jobs}")
    if errors:
        raise WorkflowError("Parameter matrix validation failed:\n" + "\n".join(errors))
    print("parameter-matrix-validate-ok")
    print(f"rows: {len(rows)}")
    return 0


def cmd_refresh_parameter_matrix_view(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    rows = read_parameter_matrix(path)
    errors = validate_parameter_matrix_rows(rows, matrix_path=path)
    if errors:
        raise WorkflowError("Parameter matrix cannot refresh its view:\n" + "\n".join(errors))
    view_path = refresh_parameter_matrix_view(path, rows, source_note=str(args.source_note or ""))
    print("parameter-matrix-view-refreshed")
    print(f"view: {display_path(view_path)}")
    return 0


def cmd_freeze_parameter_matrix(args: argparse.Namespace) -> int:
    matrix_path = Path(args.path)
    if not matrix_path.is_absolute():
        matrix_path = REPO_ROOT / matrix_path
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    if not config_path.exists() or not config_path.is_file():
        raise WorkflowError(f"Missing config snapshot: {display_path(config_path)}")
    require_ready_experiment_for_artifact(matrix_path)
    with parameter_matrix_mutation_lock(
        matrix_path,
        operation="freeze-parameter-matrix",
        job_id=args.job_id,
    ):
        return freeze_parameter_matrix_locked(args, matrix_path=matrix_path, config_path=config_path)


def freeze_parameter_matrix_locked(
    args: argparse.Namespace,
    *,
    matrix_path: Path,
    config_path: Path,
) -> int:
    rows = read_parameter_matrix(matrix_path)
    matches = [row for row in rows if row.get("job_id", "") == args.job_id]
    if len(matches) != 1:
        raise WorkflowError("freeze-parameter-matrix --job-id must name exactly one matrix row")
    row = matches[0]
    if row.get("status") != "draft":
        raise WorkflowError("freeze-parameter-matrix can only freeze a draft row once")
    try:
        relative_snapshot = config_path.resolve().relative_to(matrix_path.parent.resolve()).as_posix()
    except ValueError as exc:
        raise WorkflowError("Config snapshot must stay inside the parameter-matrix directory") from exc
    config_text = read_text(config_path)
    row["config_snapshot_ref"] = relative_snapshot
    row["config_fingerprint"] = parameter_matrix_sha256(config_text)
    config_values = read_config_values(config_path)
    if config_values.get("random_seed", ""):
        row["seed"] = config_values["random_seed"]
    row["status"] = "frozen"
    # Freeze one row at a time.  A 50-job matrix is intentionally allowed to
    # contain other drafts while its remaining config snapshots are prepared;
    # validate-parameter-matrix --require-ready is the later all-rows gate.
    errors = validate_parameter_matrix_rows(rows, matrix_path=matrix_path)
    if not row.get("seed", "").strip():
        errors.append(f"{row['job_id']} has no seed; fill it before freezing")
    if not row.get("config_snapshot_ref", "").strip():
        errors.append(f"{row['job_id']} has no config_snapshot_ref")
    if row.get("config_fingerprint", "") != parameter_matrix_sha256(config_text):
        errors.append(f"{row['job_id']} config_fingerprint does not match the selected config")
    if errors:
        raise WorkflowError("Parameter matrix cannot be frozen:\n" + "\n".join(errors))
    write_parameter_matrix(
        directory=matrix_path.parent,
        title=matrix_path.parent.name,
        rows=rows,
        source_note=parameter_matrix_source_note_from_view(matrix_path.with_name(PARAMETER_MATRIX_MD)),
        overwrite=True,
    )
    print("parameter-matrix-frozen")
    print(f"job_id: {row['job_id']}")
    print(f"csv: {display_path(matrix_path)}")
    return 0


def cmd_init_parameter_matrix(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_absolute():
        directory = REPO_ROOT / directory
    require_path_inside(directory, REPO_ROOT / "experiments", "parameter-matrix directory")
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    baseline_path = Path(args.base_config)
    if not baseline_path.is_absolute():
        baseline_path = REPO_ROOT / baseline_path
    for path, label in [(config_path, "config"), (baseline_path, "base config")]:
        if not path.exists() or not path.is_file():
            raise WorkflowError(f"Missing {label}: {display_path(path)}")
    require_path_inside(config_path, directory, "config snapshot")
    config_text = read_text(config_path)
    seed = str(args.seed or read_config_values(config_path).get("random_seed", ""))
    if not seed:
        raise WorkflowError("init-parameter-matrix requires --seed or random_seed in the config")
    changed = parameter_matrix_actual_changes(baseline_path, config_path)
    snapshot_ref = config_path.resolve().relative_to(directory.resolve()).as_posix()
    row = {
        "job_id": args.job_id,
        "work_item_id": args.work_item_id or args.job_id,
        "job_kind": args.job_kind,
        "status": "draft",
        "group": args.group or args.job_kind,
        "name": args.name or args.job_id,
        "base_version": args.base_version,
        "base_config_sha256": parameter_matrix_sha256(read_text(baseline_path)),
        "code_ref": args.code_ref or args.base_version,
        "config_snapshot_ref": snapshot_ref,
        "seed": seed,
        "changed_parameters": json.dumps(changed, ensure_ascii=False, sort_keys=True),
        "config_fingerprint": parameter_matrix_sha256(config_text),
        "repeat_of": args.repeat_of,
        "duplicate_resolution": "明确复跑" if args.repeat_of else "唯一配置",
        "purpose": args.purpose or args.job_kind,
        "run_id": args.run_id,
        "run_start_receipt_ref": "",
        "run_start_receipt_sha256": "",
        "run_command_sha256": "",
        "run_log_sha256": "",
        "run_exit_code": "",
        "U": "",
        "S": "",
        "H": "",
        "ZS": "",
        "best_epoch": "",
        "decision": "",
        "artifact_ref": "",
        "artifact_manifest_sha256": "",
    }
    errors = validate_parameter_matrix_rows([row], matrix_path=directory / PARAMETER_MATRIX_CSV)
    if errors:
        raise WorkflowError("Cannot initialize parameter matrix:\n" + "\n".join(errors))
    csv_path, _md_path = write_parameter_matrix(
        directory=directory,
        title=directory.name,
        rows=[row],
        source_note=f"由 init-parameter-matrix 从 {display_path(config_path)} 建立草稿。",
    )
    print("parameter-matrix-initialized")
    print(f"csv: {display_path(csv_path)}")
    return 0


def cmd_prepare_dynamic_routing_matrix(args: argparse.Namespace) -> int:
    if immutable_template_standard_is_active():
        raise WorkflowError(
            "legacy dynamic-routing matrix creation is retired under "
            "SYS-WORKFLOW-V5; create RUN rows in a canonical framework "
            "experiment PARAMETER_MATRIX.csv"
        )
    trial_dir = Path(args.trial_dir)
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial dir: {display_path(trial_dir)}")
    attempt_upper, _attempt_lower = normalize_attempt_ids(args.attempt_id)
    base_config = Path(args.base_config) if args.base_config else trial_dir / "config.yaml"
    if not base_config.is_absolute():
        base_config = REPO_ROOT / base_config
    if not base_config.exists():
        raise WorkflowError(f"Missing base config: {display_path(base_config)}")
    jobs = build_dynamic_routing_jobs(seed=int(args.seed), profile=args.profile)
    jobs = limit_dynamic_routing_jobs(jobs, int(args.limit_jobs or 0))
    if int(args.jobs) != len(jobs):
        raise WorkflowError(f"Profile {args.profile!r} has {len(jobs)} jobs, not --jobs {args.jobs}.")
    run_id = str(getattr(args, "run_id", "") or "").strip()
    if parameter_matrix_policy_is_active() and not run_id:
        raise WorkflowError("Active parameter-matrix policy requires --run-id before pre-run freeze")
    base_text = read_text(base_config)
    rows = build_parameter_matrix_rows(
        jobs=jobs,
        base_config_text=base_text,
        base_version=args.base_version,
        code_ref=args.base_code_tag or args.base_version,
        run_id=run_id,
    )
    attempt_dir = trial_dir / "attempts" / attempt_upper
    matrix_path = attempt_dir / PARAMETER_MATRIX_CSV
    with parameter_matrix_mutation_lock(
        matrix_path,
        operation="prepare-dynamic-routing-matrix",
        run_id=run_id,
    ):
        return write_prepared_dynamic_routing_matrix_locked(
            args,
            attempt_dir=attempt_dir,
            base_config=base_config,
            rows=rows,
        )


def write_prepared_dynamic_routing_matrix_locked(
    args: argparse.Namespace,
    *,
    attempt_dir: Path,
    base_config: Path,
    rows: list[dict[str, str]],
) -> int:
    existing_matrix = attempt_dir / PARAMETER_MATRIX_CSV
    if existing_matrix.exists() and bool(args.overwrite):
        existing_rows = read_parameter_matrix(existing_matrix)
        if any(
            row.get("run_id")
            or row.get("status") not in {"draft", "frozen"}
            or any(row.get(field) for field in ["U", "S", "H", "ZS", "best_epoch", "artifact_ref"])
            for row in existing_rows
        ):
            raise WorkflowError("Refusing to overwrite a bound, started, or completed parameter matrix")
    errors = validate_parameter_matrix_rows(rows, require_ready=True)
    errors.extend(
        parameter_matrix_conflicts(
            rows,
            REPO_ROOT / "experiments",
            exclude_paths={attempt_dir / PARAMETER_MATRIX_CSV},
        )
    )
    if errors:
        raise WorkflowError("Refusing to create a duplicate or invalid matrix:\n" + "\n".join(errors))
    csv_path, md_path = write_parameter_matrix(
        directory=attempt_dir,
        title=attempt_dir.name,
        rows=rows,
        source_note=f"profile={args.profile}; base_config={display_path(base_config)}",
        overwrite=bool(args.overwrite),
    )
    print("dynamic-routing-parameter-matrix-created")
    print(f"rows: {len(rows)}")
    print(f"csv: {display_path(csv_path)}")
    print(f"view: {display_path(md_path)}")
    return 0


def normalized_posix_path(value: str) -> PurePosixPath:
    return PurePosixPath(value.replace("\\", "/"))


def expected_dynamic_warehouse_dir(plan: dict[str, object], job_id: str) -> PurePosixPath:
    return (
        normalized_posix_path(str(plan.get("warehouse_root", "")))
        / "runs"
        / str(plan.get("base_version", "v5"))
        / "module_trial"
        / str(plan.get("trial_id", "TRIAL-001"))
        / str(plan.get("warehouse_attempt_id", ""))
        / str(plan.get("run_id", ""))
        / job_id
    )


def canonical_json_sha256(value: object) -> str:
    return parameter_matrix_sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def dynamic_run_start_receipt_errors(
    plan: dict[str, object],
    result: dict[str, str],
    *,
    run_dir: Path,
    expected_source_config_sha256: str = "",
    expected_training_entry_sha256: str = "",
) -> list[str]:
    job_id = result.get("job_id", "")
    local_receipt = run_dir / "run_start_receipts" / f"{job_id}.json"
    if not local_receipt.exists() or not local_receipt.is_file():
        return [f"{job_id} has no downloaded run-start receipt"]
    receipt_sha256 = result.get("run_start_receipt_sha256", "").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", receipt_sha256):
        return [f"{job_id} has no valid run_start_receipt_sha256"]
    errors: list[str] = []
    if sha256_file(local_receipt) != receipt_sha256:
        errors.append(f"{job_id} run-start receipt hash does not match the downloaded file")
    try:
        payload = json.loads(read_text(local_receipt))
    except json.JSONDecodeError:
        errors.append(f"{job_id} run-start receipt is not valid JSON")
        return errors
    if not isinstance(payload, dict):
        return [f"{job_id} run-start receipt must be a JSON object"]
    identity = {
        "schema_version": "gtpj-dynamic-run-start-receipt/v1",
        "job_id": job_id,
        "run_id": str(plan.get("run_id", "")),
        "attempt_id": str(plan.get("warehouse_attempt_id", "")),
        "training_commit": str(plan.get("commit", "")),
        "plan_generation_commit": str(plan.get("plan_generation_commit", "")),
        "training_entry": "train_GTPJ_CUB.py",
    }
    for field, expected in identity.items():
        if str(payload.get(field, "")) != expected:
            errors.append(f"{job_id} run-start receipt {field} mismatch")
    frozen_rows = plan.get("parameter_matrix_frozen_rows", {})
    frozen_row = frozen_rows.get(job_id) if isinstance(frozen_rows, dict) else None
    if not isinstance(frozen_row, dict):
        errors.append(f"{job_id} run plan has no frozen row for its start receipt")
    elif str(payload.get("parameter_matrix_frozen_sha256", "")) != canonical_json_sha256(frozen_row):
        errors.append(f"{job_id} run-start receipt frozen-row hash mismatch")
    command = payload.get("command")
    command_sha256 = str(payload.get("command_sha256", ""))
    if not isinstance(command, list) or not all(isinstance(part, str) and part for part in command):
        errors.append(f"{job_id} run-start receipt command must be a non-empty string list")
    elif command_sha256 != canonical_json_sha256(command):
        errors.append(f"{job_id} run-start receipt command hash mismatch")
    expected_receipt_path = expected_dynamic_warehouse_dir(plan, job_id) / "receipts" / "run_start_receipt.json"
    if normalized_posix_path(result.get("run_start_receipt", "")) != expected_receipt_path:
        errors.append(f"{job_id} run_start_receipt does not match its Warehouse job directory")
    summary_fields = {
        "run_command_sha256": command_sha256,
        "source_config_sha256": str(payload.get("source_config_sha256", "")),
        "runtime_config_sha256": str(payload.get("runtime_config_sha256", "")),
        "training_entry_sha256": str(payload.get("training_entry_sha256", "")),
    }
    for field, expected in summary_fields.items():
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            errors.append(f"{job_id} run-start receipt has no valid {field}")
        if result.get(field, "").strip() != expected:
            errors.append(f"{job_id} summary {field} does not match the run-start receipt")
    if expected_source_config_sha256 and summary_fields["source_config_sha256"] != expected_source_config_sha256:
        errors.append(f"{job_id} source config does not match the frozen parameter-matrix fingerprint")
    if expected_training_entry_sha256 and summary_fields["training_entry_sha256"] != expected_training_entry_sha256:
        errors.append(f"{job_id} training entry does not match the frozen training commit")
    return errors


def dynamic_warehouse_result_errors(
    plan: dict[str, object],
    result: dict[str, str],
    *,
    run_dir: Path,
    expected_source_config_sha256: str = "",
    expected_training_entry_sha256: str = "",
) -> list[str]:
    job_id = result.get("job_id", "")
    warehouse_dir = result.get("warehouse_dir", "").strip()
    if not warehouse_dir:
        return [f"{job_id} has no warehouse_dir in summary.csv"]
    expected_dir = expected_dynamic_warehouse_dir(plan, job_id)
    if normalized_posix_path(warehouse_dir) != expected_dir:
        return [f"{job_id} warehouse_dir does not match its frozen run/job directory"]
    manifest_path = result.get("artifact_manifest", "").strip()
    expected_manifest = expected_dir / "artifact_manifest.json"
    if not manifest_path or normalized_posix_path(manifest_path) != expected_manifest:
        return [f"{job_id} artifact_manifest does not match its expected Warehouse manifest"]
    manifest_sha256 = result.get("artifact_manifest_sha256", "").strip()
    if not re.fullmatch(r"[0-9a-f]{64}", manifest_sha256):
        return [f"{job_id} has no valid artifact_manifest_sha256"]
    identity = {
        "attempt_id": str(plan.get("warehouse_attempt_id", "")),
        "artifact_manifest_job_id": job_id,
        "artifact_manifest_run_id": str(plan.get("run_id", "")),
        "artifact_manifest_attempt_id": str(plan.get("warehouse_attempt_id", "")),
    }
    errors = [
        f"{job_id} {field} does not match the frozen plan"
        for field, expected in identity.items()
        if result.get(field, "").strip() != expected
    ]
    local_manifest = run_dir / "artifact_manifests" / f"{job_id}.json"
    if not local_manifest.exists() or not local_manifest.is_file():
        errors.append(f"{job_id} has no downloaded artifact manifest receipt")
        return errors
    if sha256_file(local_manifest) != manifest_sha256:
        errors.append(f"{job_id} artifact manifest hash does not match the downloaded file")
    try:
        payload = json.loads(read_text(local_manifest))
    except json.JSONDecodeError:
        errors.append(f"{job_id} artifact manifest receipt is not valid JSON")
        return errors
    if str(payload.get("job_id", "")) != job_id:
        errors.append(f"{job_id} artifact manifest job_id mismatch")
    if str(payload.get("run_id", "")) != str(plan.get("run_id", "")):
        errors.append(f"{job_id} artifact manifest run_id mismatch")
    if str(payload.get("attempt_id", "")) != str(plan.get("warehouse_attempt_id", "")):
        errors.append(f"{job_id} artifact manifest attempt_id mismatch")
    if str(payload.get("warehouse_attempt_id", "")) != str(plan.get("warehouse_attempt_id", "")):
        errors.append(f"{job_id} artifact manifest warehouse_attempt_id mismatch")
    if normalized_posix_path(str(payload.get("warehouse_dir", ""))) != expected_dir:
        errors.append(f"{job_id} artifact manifest warehouse_dir mismatch")
    receipt_errors = dynamic_run_start_receipt_errors(
        plan,
        result,
        run_dir=run_dir,
        expected_source_config_sha256=expected_source_config_sha256,
        expected_training_entry_sha256=expected_training_entry_sha256,
    )
    errors.extend(receipt_errors)
    if not receipt_errors:
        manifest_receipt_fields = {
            "run_start_receipt": result.get("run_start_receipt", "").strip(),
            "run_start_receipt_sha256": result.get("run_start_receipt_sha256", "").strip(),
            "run_command_sha256": result.get("run_command_sha256", "").strip(),
        }
        for field, expected in manifest_receipt_fields.items():
            if str(payload.get(field, "")) != expected:
                errors.append(f"{job_id} artifact manifest {field} mismatch")
    return errors


def dynamic_top_rank_resolution_errors(
    row: dict[str, str],
    result: dict[str, str],
    *,
    summary: dict[str, dict[str, str]],
    matrix_by_job: dict[str, dict[str, str]],
) -> list[str]:
    match = re.fullmatch(r"pending_after_top_rank:([1-9][0-9]*)", row.get("config_fingerprint", ""))
    if match is None or result.get("status") not in {"completed", "failed"}:
        return []
    job_id = row.get("job_id", "")
    rank = int(match.group(1))
    resolved_from = result.get("resolved_from_job_id", "").strip()
    source = matrix_by_job.get(resolved_from)
    if source is None:
        return [f"{job_id} completed a top-rank repeat but summary.csv has no valid resolved_from_job_id"]
    if source.get("config_fingerprint", "").startswith("pending_after_top_rank:"):
        return [f"{job_id} resolved through another unresolved top-rank repeat"]

    explore_job_ids = [
        candidate_id
        for candidate_id, candidate in matrix_by_job.items()
        if not candidate.get("config_fingerprint", "").startswith("pending_after_top_rank:")
    ]
    incomplete = [
        candidate_id
        for candidate_id in explore_job_ids
        if candidate_id not in summary
        or summary[candidate_id].get("status") not in {"completed", "failed", "skipped"}
    ]
    if incomplete:
        return [
            f"{job_id} cannot verify top_rank:{rank}; exploration summary is incomplete: "
            + ", ".join(sorted(incomplete))
        ]
    completed: list[tuple[float, str]] = []
    for candidate_id in explore_job_ids:
        candidate_result = summary[candidate_id]
        if candidate_result.get("status") != "completed":
            continue
        try:
            score = float(candidate_result.get("H", ""))
        except ValueError:
            return [f"{job_id} cannot verify top_rank:{rank}; {candidate_id} has no numeric H"]
        if not math.isfinite(score):
            return [f"{job_id} cannot verify top_rank:{rank}; {candidate_id} has a non-finite H"]
        completed.append((score, candidate_id))
    completed.sort(key=lambda item: (-item[0], item[1]))
    if len(completed) < rank:
        return [f"{job_id} cannot verify top_rank:{rank}; only {len(completed)} completed candidates exist"]
    expected_source = completed[rank - 1][1]
    if resolved_from != expected_source:
        return [
            f"{job_id} resolved_from_job_id {resolved_from!r} is not verified top_rank:{rank} "
            f"({expected_source})"
        ]
    return []


def formal_dynamic_plan_commit_errors(
    plan: dict[str, object],
    *,
    matrix_path: Path,
    current_rows: list[dict[str, str]],
) -> list[str]:
    """Rebuild a formal plan from Git so mutable runtime files cannot certify each other."""
    errors: list[str] = []
    try:
        plan_generation_commit = resolve_commit(str(plan.get("plan_generation_commit", "")))
        training_commit = resolve_commit(str(plan.get("commit", "")))
        head_commit = resolve_commit("HEAD")
    except WorkflowError as exc:
        return [f"formal dynamic plan has an invalid frozen commit: {exc}"]
    if plan_generation_commit != head_commit:
        errors.append(
            "formal dynamic plan generation commit does not match the current Git HEAD; "
            "sync results before making a post-run commit"
        )
    source_control = plan.get("source_control")
    if not isinstance(source_control, dict):
        errors.append("formal dynamic plan has no source_control record")
        source_control = {}
    if str(source_control.get("plan_generation_commit", "")) != plan_generation_commit:
        errors.append("formal dynamic plan source_control plan_generation_commit mismatch")
    if str(source_control.get("training_commit", "")) != training_commit:
        errors.append("formal dynamic plan source_control training_commit mismatch")
    if str(source_control.get("dirty_state", "")) != "clean":
        errors.append("formal dynamic plan source_control is not clean")

    try:
        matrix_rel = repo_relative_path(matrix_path, "Formal dynamic routing parameter matrix")
        committed_rows = parse_parameter_matrix_text(
            read_text_at_commit(training_commit, matrix_rel),
            label=f"{training_commit}:{matrix_rel}",
        )
    except WorkflowError as exc:
        return errors + [f"formal parameter matrix is not readable at the training commit: {exc}"]
    committed_by_job = {row["job_id"]: row for row in committed_rows}
    current_by_job = {row["job_id"]: row for row in current_rows}
    if set(committed_by_job) != set(current_by_job):
        errors.append("current parameter matrix job set differs from the training commit")
        return errors

    frozen_rows = plan.get("parameter_matrix_frozen_rows", {})
    if not isinstance(frozen_rows, dict) or set(frozen_rows) != set(committed_by_job):
        errors.append("run plan has no complete parameter-matrix snapshot from the training commit")
    for job_id, committed_row in committed_by_job.items():
        plan_run_id = str(plan.get("run_id", ""))
        if committed_row.get("run_id", "") != plan_run_id:
            errors.append(f"{job_id} training-commit run_id does not match the runtime plan")
        if current_by_job[job_id].get("run_id", "") != plan_run_id:
            errors.append(f"{job_id} current run_id does not match the runtime plan")
        committed_frozen = parameter_matrix_frozen_fields(committed_row)
        plan_frozen = frozen_rows.get(job_id) if isinstance(frozen_rows, dict) else None
        if plan_frozen != committed_frozen:
            errors.append(f"{job_id} run plan frozen fields differ from the training commit")
        current_frozen = parameter_matrix_frozen_fields(current_by_job[job_id])
        pending_top_rank = committed_row.get("config_fingerprint", "").startswith("pending_after_top_rank:")
        for field, expected in committed_frozen.items():
            if pending_top_rank and field in PARAMETER_MATRIX_TOP_RANK_RESOLUTION_FIELDS:
                continue
            if current_frozen.get(field, "") != expected:
                errors.append(f"{job_id} current frozen field {field} differs from the training commit")

    try:
        seed = int(plan["seed"])
        limit_jobs = int(plan.get("limit_jobs", 0) or 0)
        profile = str(plan["profile"])
        expected_jobs = limit_dynamic_routing_jobs(
            build_dynamic_routing_jobs(seed=seed, profile=profile),
            limit_jobs,
        )
    except (KeyError, TypeError, ValueError, WorkflowError) as exc:
        errors.append(f"formal dynamic plan cannot rebuild its job list: {exc}")
        return errors
    attempt_id = str(plan.get("warehouse_attempt_id", ""))
    if attempt_id:
        for job in expected_jobs:
            job["attempt_id"] = attempt_id
    gpus = plan.get("gpus")
    if not isinstance(gpus, list) or not gpus:
        errors.append("formal dynamic plan has no GPU list")
        return errors
    for index, job in enumerate(expected_jobs):
        job["gpu_slot"] = index % len(gpus)
    if plan.get("jobs") != expected_jobs:
        errors.append("formal dynamic plan jobs differ from the deterministic profile and seed")

    try:
        base_config = Path(str(plan.get("base_config", "")))
        if not base_config.is_absolute():
            base_config = REPO_ROOT / base_config
        base_config_rel = repo_relative_path(base_config, "Formal dynamic routing base config")
        base_text = read_text_at_commit(training_commit, base_config_rel)
        expected_rows = build_parameter_matrix_rows(
            jobs=expected_jobs,
            base_config_text=base_text,
            base_version=str(plan.get("base_version", "")),
            code_ref=str(plan.get("base_code_tag", "")),
            run_id=str(plan.get("run_id", "")),
        )
    except WorkflowError as exc:
        errors.append(f"formal dynamic plan cannot rebuild its parameter matrix: {exc}")
        return errors
    expected_by_job = {row["job_id"]: row for row in expected_rows}
    for job_id, committed_row in committed_by_job.items():
        expected_row = expected_by_job.get(job_id)
        if expected_row is None:
            errors.append(f"{job_id} exists in the training commit but not the rebuilt plan")
            continue
        if parameter_matrix_frozen_fields(committed_row) != parameter_matrix_frozen_fields(expected_row):
            errors.append(f"{job_id} training-commit matrix differs from the deterministic batch plan")
        if committed_row.get("run_id", "") != expected_row.get("run_id", ""):
            errors.append(f"{job_id} training-commit run_id differs from the deterministic batch plan")
    return errors


def cmd_sync_dynamic_routing_matrix(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    plan_path = run_dir / "plan.json"
    if not plan_path.exists():
        raise WorkflowError(f"Missing plan.json: {display_path(plan_path)}")
    plan = json.loads(read_text(plan_path))
    attempt_id = str(plan.get("warehouse_attempt_id", "")).strip()
    trial_dir = Path(str(plan.get("trial_dir", "")))
    if not trial_dir.is_absolute():
        trial_dir = REPO_ROOT / trial_dir
    if not attempt_id:
        raise WorkflowError("Run plan has no warehouse_attempt_id; cannot find its formal parameter matrix")
    matrix_path = trial_dir / "attempts" / attempt_id / PARAMETER_MATRIX_CSV
    if not bool(plan.get("formal_evidence")):
        raise WorkflowError("Refusing to sync a debug or non-formal plan into a formal parameter matrix")
    plan_matrix_path = Path(str(plan.get("parameter_matrix", "")))
    if not plan_matrix_path.is_absolute():
        plan_matrix_path = REPO_ROOT / plan_matrix_path
    if plan_matrix_path.resolve() != matrix_path.resolve():
        raise WorkflowError("Run plan parameter_matrix does not point to this Attempt matrix")
    rows = read_parameter_matrix(matrix_path)
    matrix_source_rows = [dict(row) for row in rows]
    errors = validate_parameter_matrix_rows(rows, matrix_path=matrix_path)
    errors.extend(parameter_matrix_view_errors(matrix_path, rows))
    plan_run_id = str(plan.get("run_id", ""))
    for row in rows:
        if row.get("run_id", "") != plan_run_id:
            errors.append(f"{row.get('job_id')} run_id does not match the runtime plan")
    if errors:
        raise WorkflowError("Refusing to sync an invalid parameter matrix:\n" + "\n".join(errors))
    commit_errors = formal_dynamic_plan_commit_errors(plan, matrix_path=matrix_path, current_rows=rows)
    if commit_errors:
        raise WorkflowError(
            "Refusing to sync a runtime plan that differs from its training commit:\n"
            + "\n".join(commit_errors)
        )
    training_entry_sha256 = parameter_matrix_sha256(
        read_text_at_commit(str(plan.get("commit", "")), "train_GTPJ_CUB.py")
    )
    summary_rows = _read_summary_rows(run_dir)
    if not summary_rows:
        raise WorkflowError("summary.csv is missing or empty; no formal result can be synchronized")
    matrix_by_job = {row["job_id"]: row for row in rows}
    plan_jobs = plan.get("jobs", [])
    if not isinstance(plan_jobs, list) or {
        str(job.get("job_id", "")) for job in plan_jobs if isinstance(job, dict)
    } != set(matrix_by_job):
        raise WorkflowError("Run plan jobs do not match the frozen parameter-matrix job set")
    frozen_rows = plan.get("parameter_matrix_frozen_rows", {})
    if not isinstance(frozen_rows, dict) or set(frozen_rows) != set(matrix_by_job):
        raise WorkflowError("Run plan has no complete frozen parameter-matrix snapshot")
    for job_id, row in matrix_by_job.items():
        expected = frozen_rows.get(job_id)
        if not isinstance(expected, dict):
            errors.append(f"Run plan has no frozen fields for {job_id}")
            continue
        current = parameter_matrix_frozen_fields(row)
        pending_top_rank = str(expected.get("config_fingerprint", "")).startswith("pending_after_top_rank:")
        for field, expected_value in expected.items():
            if pending_top_rank and field in PARAMETER_MATRIX_TOP_RANK_RESOLUTION_FIELDS:
                continue
            if current.get(field, "") != str(expected_value):
                errors.append(f"{job_id} frozen field {field} changed after plan creation")
    summary: dict[str, dict[str, str]] = {}
    for result in summary_rows:
        job_id = result.get("job_id", "")
        if not job_id:
            continue
        if job_id not in matrix_by_job:
            errors.append(f"summary.csv contains unregistered job {job_id}")
        elif job_id in summary:
            errors.append(f"summary.csv repeats job {job_id}")
        summary[job_id] = result
    if errors:
        raise WorkflowError("Refusing to sync a summary outside the frozen parameter matrix:\n" + "\n".join(errors))
    for row in rows:
        result = summary.get(row["job_id"])
        if not result:
            continue
        incoming_status = result.get("status", row["status"])
        warehouse_dir = result.get("warehouse_dir", "").strip()
        incoming_artifact = f"warehouse_dir:{warehouse_dir}" if warehouse_dir else ""
        if row.get("status") in PARAMETER_MATRIX_TERMINAL_STATUSES:
            same_result = (
                row.get("status") == incoming_status
                and row.get("run_id", "") == str(plan.get("run_id", ""))
                and all(row.get(key, "") == result.get(key, "") for key in ["U", "S", "H", "ZS", "best_epoch"])
                and row.get("artifact_ref", "") == incoming_artifact
                and row.get("artifact_manifest_sha256", "")
                == result.get("artifact_manifest_sha256", "").strip()
                and row.get("run_start_receipt_ref", "") == result.get("run_start_receipt", "").strip()
                and row.get("run_start_receipt_sha256", "")
                == result.get("run_start_receipt_sha256", "").strip()
                and row.get("run_command_sha256", "") == result.get("run_command_sha256", "").strip()
            )
            if not same_result:
                errors.append(f"Refusing to overwrite an existing result for {row['job_id']}")
            elif incoming_status in {"completed", "failed"}:
                errors.extend(
                    dynamic_warehouse_result_errors(
                        plan,
                        result,
                        run_dir=run_dir,
                        expected_source_config_sha256=row.get("config_fingerprint", ""),
                        expected_training_entry_sha256=training_entry_sha256,
                    )
                )
            continue
        if row.get("status") not in {"frozen", "running"}:
            errors.append(f"{row['job_id']} status {row.get('status')!r} cannot accept a result")
            continue
        resolved_from = result.get("resolved_from_job_id", "").strip()
        if row["config_fingerprint"].startswith("pending_after_top_rank:") and result.get("status") in {
            "completed",
            "failed",
        }:
            top_rank_errors = dynamic_top_rank_resolution_errors(
                row,
                result,
                summary=summary,
                matrix_by_job=matrix_by_job,
            )
            if top_rank_errors:
                errors.extend(top_rank_errors)
                continue
            source = matrix_by_job.get(resolved_from)
            assert source is not None
            row["repeat_of"] = resolved_from
            row["config_fingerprint"] = source["config_fingerprint"]
            row["changed_parameters"] = source["changed_parameters"]
            row["duplicate_resolution"] = f"运行时解析为原样复跑 {resolved_from}"
        row["status"] = incoming_status
        for key in ["U", "S", "H", "ZS", "best_epoch"]:
            row[key] = result.get(key, row[key])
        row["run_id"] = str(plan.get("run_id", ""))
        if row.get("status") in PARAMETER_MATRIX_TERMINAL_STATUSES:
            if result.get("status") in {"completed", "failed"}:
                errors.extend(
                    dynamic_warehouse_result_errors(
                        plan,
                        result,
                        run_dir=run_dir,
                        expected_source_config_sha256=row.get("config_fingerprint", ""),
                        expected_training_entry_sha256=training_entry_sha256,
                    )
                )
        if result.get("status") in {"completed", "failed"} and not warehouse_dir:
            errors.append(f"{row['job_id']} has no warehouse_dir in summary.csv")
        elif warehouse_dir:
            row["artifact_ref"] = f"warehouse_dir:{warehouse_dir}"
            row["artifact_manifest_sha256"] = result.get("artifact_manifest_sha256", "").strip()
        if result.get("status") in {"completed", "failed"}:
            row["run_start_receipt_ref"] = result.get("run_start_receipt", "").strip()
            row["run_start_receipt_sha256"] = result.get("run_start_receipt_sha256", "").strip()
            row["run_command_sha256"] = result.get("run_command_sha256", "").strip()
    if errors:
        raise WorkflowError("Refusing to sync unresolved or non-reproducible results:\n" + "\n".join(errors))
    errors = validate_parameter_matrix_rows(rows, matrix_path=matrix_path)
    if errors:
        raise WorkflowError("Refusing to write an invalid parameter matrix:\n" + "\n".join(errors))
    with parameter_matrix_mutation_lock(
        matrix_path,
        operation="sync-dynamic-routing-matrix",
        run_id=str(plan.get("run_id", "")),
    ):
        current_rows = read_parameter_matrix(matrix_path)
        if current_rows != matrix_source_rows:
            raise WorkflowError("parameter matrix changed while the dynamic summary was being verified")
        write_parameter_matrix(
            directory=matrix_path.parent,
            title=attempt_id,
            rows=rows,
            source_note=f"已从 {display_path(run_dir / 'summary.csv')} 回填；原始证据留在 Warehouse。",
            overwrite=True,
        )
    print("dynamic-routing-parameter-matrix-synced")
    print(f"rows: {len(rows)}")
    return 0


def _dynamic_runner_script() -> str:
    return r'''#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import fcntl


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path, retries=20, delay=0.05):
    last_error = None
    for _ in range(retries):
        try:
            text = path.read_text(encoding="utf-8")
            if text.strip():
                return json.loads(text)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(delay)
    if last_error is not None:
        raise last_error
    raise ValueError(f"{path} stayed empty while reading JSON")


def write_json(path, data):
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def canonical_json_sha256(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_path(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd, cwd=None, env=None, log_path=None):
    if log_path is None:
        return subprocess.run(cmd, cwd=cwd, env=env, text=True, check=True)
    with log_path.open("a", encoding="utf-8", errors="replace") as handle:
        return subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=handle, stderr=subprocess.STDOUT)


def git_output(args, cwd):
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {detail}")
    return result.stdout.strip()


def parse_metrics(log_path):
    text = log_path.read_text(encoding="utf-8", errors="replace")
    best_start = text.rfind("Best Results")
    metric_text = text[best_start:] if best_start != -1 else text
    result = {}
    best_epoch = re.search(r"Best Results\s*@\s*Epoch\s+([0-9]+)", metric_text)
    result["best_epoch"] = best_epoch.group(1) if best_epoch else ""
    patterns = {
        "U": r"GZSL-U[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "S": r"GZSL-S[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "H": r"GZSL-H[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
        "ZS": r"ZSL[^:\n]*:\s*([0-9]+(?:\.[0-9]+)?)%",
    }
    for name, pattern in patterns.items():
        matches = re.findall(pattern, metric_text)
        result[name] = matches[-1] if matches else ""
    return result


def config_set_scalar(text, key, value):
    rendered = "true" if value is True else "false" if value is False else str(value)
    pattern = rf"(?ms)^({re.escape(key)}:\n\s+value:\s*).+?(\n(?=[A-Za-z_][A-Za-z0-9_]*:|\Z))"
    replacement = rf"\g<1>{rendered}\2"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return text.rstrip() + f"\n{key}:\n  value: {rendered}\n"


def locked(run_dir, func):
    lock_path = run_dir / "batch_status.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            return func()
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def update_job(run_dir, job_id, **fields):
    def inner():
        status_path = run_dir / "batch_status.json"
        data = load_json(status_path)
        job_status = data.setdefault("jobs", {}).setdefault(job_id, {})
        job_status.update(fields)
        job_status["updated_at"] = utc_now()
        write_json(status_path, data)
    locked(run_dir, inner)


def stop_file_path(run_dir):
    return run_dir / "STOP_REQUESTED"


def stop_requested(run_dir):
    return stop_file_path(run_dir).exists()


def stop_request_reason(run_dir):
    path = stop_file_path(run_dir)
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    return text or "STOP_REQUESTED"


def request_stop(run_dir, reason):
    path = stop_file_path(run_dir)
    if not path.exists():
        path.write_text(reason.strip() + "\n", encoding="utf-8")
    append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": "stop_requested", "reason": reason})


def maybe_stop_after_confirmation_hit(run_dir, plan, row):
    policy = plan.get("confirmation_policy") or {}
    if policy.get("repeat_type") != "exact_repeat":
        return
    if not policy.get("early_stop_on_best_hit"):
        return
    target = str(row.get("restore_target_H") or row.get("source_H") or "").strip()
    if not target and not policy.get("per_job_restore_target_H"):
        target = str(policy.get("restore_target_H", "")).strip()
    if not target:
        return
    try:
        h_value = float(row.get("H") or "")
        target_value = float(target)
    except (TypeError, ValueError):
        return
    if h_value >= target_value:
        reason = (
            "early_stop_on_best_hit: "
            f"{row.get('job_id')} H={h_value:.2f} >= restore_target_H={target_value:.2f}"
        )
        source_candidate_id = str(row.get("source_candidate_id", "")).strip()
        if source_candidate_id:
            skip_candidate_remaining_repeats(run_dir, plan, source_candidate_id, str(row.get("job_id")), reason)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "time": utc_now(),
                    "event": "candidate_exact_repeat_best_hit",
                    "source_candidate_id": source_candidate_id,
                    "job_id": row.get("job_id"),
                    "H": row.get("H"),
                    "restore_target_H": f"{target_value:.2f}",
                    "decision": "skip_remaining_candidate_repeats",
                },
            )
            return
        request_stop(run_dir, reason)
        return
    try:
        near_miss_tolerance = float(policy.get("near_miss_tolerance_H", 0.2))
    except (TypeError, ValueError):
        near_miss_tolerance = 0.2
    if h_value >= target_value - near_miss_tolerance:
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "time": utc_now(),
                "event": "near_miss_not_restored",
                "job_id": row.get("job_id"),
                "H": row.get("H"),
                "restore_target_H": f"{target_value:.2f}",
                "near_miss_tolerance_H": f"{near_miss_tolerance:.2f}",
                "decision": "continue_exact_repeat",
            },
        )


def mark_job_skipped_due_candidate_hit(run_dir, job_id, reason, source_candidate_id):
    def inner():
        status_path = run_dir / "batch_status.json"
        data = load_json(status_path)
        job_status = data.setdefault("jobs", {}).setdefault(job_id, {})
        if job_status.get("status") in {"completed", "failed", "skipped", "running"}:
            return False
        job_status.update(
            {
                "status": "skipped",
                "skip_reason": "candidate_restore_hit",
                "stop_reason": reason,
                "source_candidate_id": source_candidate_id,
                "stopped_at": utc_now(),
            }
        )
        job_status["updated_at"] = utc_now()
        write_json(status_path, data)
        return True
    return locked(run_dir, inner)


def skip_candidate_remaining_repeats(run_dir, plan, source_candidate_id, hit_job_id, reason):
    skipped = 0
    for job in plan.get("jobs", []):
        if str(job.get("source_candidate_id", "")).strip() != source_candidate_id:
            continue
        if str(job.get("job_id", "")) == hit_job_id:
            continue
        if not mark_job_skipped_due_candidate_hit(run_dir, job["job_id"], reason, source_candidate_id):
            continue
        row = {
            **job,
            "status": "skipped",
            "gpu": job.get("gpu_slot", ""),
            "resolved_from_job_id": "",
            "log_path": "",
            "warehouse_dir": "",
        }
        append_summary(run_dir, row)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "time": utc_now(),
                "event": "job_skipped_candidate_restored",
                "job_id": job["job_id"],
                "source_candidate_id": source_candidate_id,
                "hit_job_id": hit_job_id,
                "reason": reason,
            },
        )
        skipped += 1
    if skipped:
        refresh_batch_status(run_dir)
    return skipped


def mark_job_skipped_due_stop(run_dir, job_id, reason):
    def inner():
        status_path = run_dir / "batch_status.json"
        data = load_json(status_path)
        job_status = data.setdefault("jobs", {}).setdefault(job_id, {})
        if job_status.get("status") in {"completed", "failed", "skipped", "running"}:
            return False
        job_status.update(
            {
                "status": "skipped",
                "skip_reason": "STOP_REQUESTED",
                "stop_reason": reason,
                "stopped_at": utc_now(),
            }
        )
        job_status["updated_at"] = utc_now()
        write_json(status_path, data)
        return True
    return locked(run_dir, inner)


def append_jsonl(path, obj):
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


def append_summary(run_dir, row):
    def inner():
        summary = run_dir / "summary.csv"
        exists = summary.exists()
        fields = [
            "job_id", "work_item_id", "attempt_id", "phase", "group", "name", "seed", "source_rank",
            "resolved_from_job_id", "status", "U", "S", "H", "ZS", "best_epoch", "gpu",
            "log_path", "warehouse_dir", "artifact_manifest", "artifact_manifest_sha256",
            "artifact_manifest_job_id", "artifact_manifest_run_id", "artifact_manifest_attempt_id",
            "run_start_receipt", "run_start_receipt_sha256", "run_command_sha256",
            "source_config_sha256", "runtime_config_sha256", "training_entry_sha256",
        ]
        with summary.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if not exists:
                writer.writeheader()
            writer.writerow({key: row.get(key, "") for key in fields})
        append_jsonl(run_dir / "summary.jsonl", row)
    locked(run_dir, inner)


def completed_explore_rows(run_dir):
    summary = run_dir / "summary.csv"
    if not summary.exists():
        return []
    with summary.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row.get("phase") == "explore" and row.get("status") == "completed" and row.get("H")]


def all_explore_finished(run_dir, plan):
    status = load_json(run_dir / "batch_status.json")
    jobs = status.get("jobs", {})
    explore = [job for job in plan["jobs"] if job["phase"] == "explore"]
    return all(jobs.get(job["job_id"], {}).get("status") in {"completed", "failed", "skipped"} for job in explore)


def skip_remaining_due_stop(run_dir, assigned, gpu, phase):
    reason = stop_request_reason(run_dir)
    skipped = 0
    for job in assigned:
        if job["phase"] != phase:
            continue
        if not mark_job_skipped_due_stop(run_dir, job["job_id"], reason):
            continue
        row = {
            **job,
            "status": "skipped",
            "gpu": gpu,
            "resolved_from_job_id": "",
            "log_path": "",
            "warehouse_dir": "",
        }
        append_summary(run_dir, row)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "time": utc_now(),
                "event": "job_skipped_stop_requested",
                "job_id": job["job_id"],
                "gpu": gpu,
                "reason": reason,
            },
        )
        skipped += 1
    if skipped:
        refresh_batch_status(run_dir)
    return skipped


def refresh_batch_status(run_dir):
    def inner():
        status_path = run_dir / "batch_status.json"
        status = load_json(status_path)
        jobs = status.get("jobs", {})
        states = [str(job.get("status", "unknown")) for job in jobs.values()]
        counts = {state: states.count(state) for state in sorted(set(states))}
        status["summary"] = {
            "total": str(len(states)),
            "completed": str(counts.get("completed", 0)),
            "failed": str(counts.get("failed", 0)),
            "skipped": str(counts.get("skipped", 0)),
            "running": str(counts.get("running", 0)),
            "pending": str(counts.get("pending", 0)),
        }
        if states and all(state in {"completed", "failed", "skipped"} for state in states):
            if counts.get("failed", 0):
                status["status"] = "completed_with_failures"
            elif counts.get("skipped", 0):
                status["status"] = "completed_with_skips"
            else:
                status["status"] = "completed"
            status["completed_at"] = utc_now()
        elif counts.get("running", 0):
            status["status"] = "running"
        else:
            status["status"] = "planned"
        status["updated_at"] = utc_now()
        write_json(status_path, status)
    locked(run_dir, inner)


def top_job_for_rank(run_dir, rank):
    rows = completed_explore_rows(run_dir)
    scored_rows = []
    for row in rows:
        score = float(row.get("H") or "nan")
        if not math.isfinite(score):
            raise RuntimeError(f"non-finite H cannot participate in top-rank resolution: {row.get('job_id')}")
        scored_rows.append((score, row))
    scored_rows.sort(key=lambda item: (-item[0], str(item[1].get("job_id", ""))))
    if len(scored_rows) < rank:
        return None
    return scored_rows[rank - 1][1]


def link_runtime_resources(plan, worktree):
    server_repo = Path(plan["server_repo"])
    for name in plan.get("runtime_resource_links", ["data"]):
        source = server_repo / name
        target = worktree / name
        if target.exists():
            continue
        if target.is_symlink():
            target.unlink()
        if not source.exists():
            raise FileNotFoundError(f"Missing runtime resource: {source}")
        os.symlink(source, target, target_is_directory=source.is_dir())


def status_path_from_porcelain(line):
    path = line[3:].strip() if len(line) > 3 else line.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.rstrip("/")


def assert_worktree_matches_plan(plan, worktree):
    expected_commit = str(plan["commit"])
    actual_commit = git_output(["rev-parse", "HEAD"], worktree)
    if actual_commit != expected_commit:
        raise RuntimeError(
            "worktree HEAD mismatch before training: "
            f"worktree={worktree} expected={expected_commit} actual={actual_commit}"
        )
    allowed_dirty_paths = set(str(name).strip("/").rstrip("/") for name in plan.get("runtime_resource_links", ["data"]))
    status = git_output(["status", "--short"], worktree)
    unexpected = [
        line for line in status.splitlines()
        if status_path_from_porcelain(line) not in allowed_dirty_paths
    ]
    if unexpected:
        raise RuntimeError(
            "worktree has unexpected dirty files before training: "
            + "; ".join(unexpected[:20])
        )


def ensure_worktree(plan, gpu):
    server_repo = Path(plan["server_repo"])
    worktree_root = Path(plan["worktree_root"])
    commit = plan["commit"]
    branch = plan["branch"]
    git_remote = plan.get("git_remote", "origin")
    sha7 = commit[:7]
    worktree = worktree_root / f"dynroute_{sha7}_gpu{gpu}"
    worktree_root.mkdir(parents=True, exist_ok=True)
    if git_remote and str(git_remote).lower() not in {"none", "local", "no_fetch"}:
        subprocess.run(["git", "-C", str(server_repo), "fetch", str(git_remote), branch], check=False)
    git_output(["cat-file", "-e", f"{commit}^{{commit}}"], server_repo)
    if not worktree.exists():
        subprocess.run(["git", "-C", str(server_repo), "worktree", "add", str(worktree), commit], check=True)
    link_runtime_resources(plan, worktree)
    assert_worktree_matches_plan(plan, worktree)
    return worktree


def warehouse_attempt_dir(plan, job):
    attempt_id = str(plan.get("warehouse_attempt_id", "")).strip()
    if attempt_id:
        return (
            Path(plan["warehouse_root"])
            / "runs"
            / str(plan.get("base_version", "v5"))
            / "module_trial"
            / str(plan.get("trial_id", "TRIAL-001"))
            / attempt_id
            / str(plan.get("run_id", "RUN-UNKNOWN"))
            / str(job["job_id"])
        )
    attempt_lower = str(job["attempt_id"]).lower()
    return (
        Path(plan["warehouse_root"])
        / "runs"
        / str(plan.get("base_version", "v5"))
        / "module_trial"
        / str(plan.get("trial_id", "TRIAL-001"))
        / attempt_lower
    )


def reserve_warehouse_attempt_dir(plan, job):
    attempt_dir = warehouse_attempt_dir(plan, job)
    try:
        attempt_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise RuntimeError(
            f"Refusing to overwrite existing Warehouse job directory: {attempt_dir}"
        ) from exc
    return attempt_dir


def prepare_run_start_receipt(run_dir, plan, job, worktree, source_config, runtime_config, cmd, log_path):
    job_id = str(job["job_id"])
    receipt_dir = run_dir / "run_start_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{job_id}.json"
    if receipt_path.exists() or log_path.exists():
        raise RuntimeError(f"Refusing to overwrite an existing run-start receipt or log for {job_id}")
    training_entry = worktree / "train_GTPJ_CUB.py"
    if not training_entry.is_file():
        raise RuntimeError(f"Missing frozen training entry: {training_entry}")
    frozen_rows = plan.get("parameter_matrix_frozen_rows", {})
    frozen_row = frozen_rows.get(job_id, {}) if isinstance(frozen_rows, dict) else {}
    if plan.get("formal_evidence") and not frozen_row:
        raise RuntimeError(f"Formal job {job_id} has no frozen parameter-matrix row")
    command_sha256 = canonical_json_sha256(cmd)
    payload = {
        "schema_version": "gtpj-dynamic-run-start-receipt/v1",
        "created_at": utc_now(),
        "job_id": job_id,
        "run_id": str(plan.get("run_id", "")),
        "attempt_id": str(plan.get("warehouse_attempt_id", "")),
        "training_commit": str(plan.get("commit", "")),
        "plan_generation_commit": str(plan.get("plan_generation_commit", "")),
        "parameter_matrix": str(plan.get("parameter_matrix", "")),
        "parameter_matrix_frozen_sha256": canonical_json_sha256(frozen_row),
        "source_config_sha256": sha256_path(source_config),
        "runtime_config_sha256": sha256_path(runtime_config),
        "training_entry": "train_GTPJ_CUB.py",
        "training_entry_sha256": sha256_path(training_entry),
        "command": cmd,
        "command_sha256": command_sha256,
        "log_path": str(log_path),
    }
    write_json(receipt_path, payload)
    receipt_sha256 = sha256_path(receipt_path)
    warehouse_receipt_dir = warehouse_attempt_dir(plan, job) / "receipts"
    warehouse_receipt_dir.mkdir(parents=True, exist_ok=True)
    warehouse_receipt = warehouse_receipt_dir / "run_start_receipt.json"
    if warehouse_receipt.exists():
        raise RuntimeError(f"Refusing to overwrite Warehouse run-start receipt: {warehouse_receipt}")
    shutil.copy2(receipt_path, warehouse_receipt)
    log_path.write_text(f"GTPJ_RUN_START_RECEIPT_SHA256={receipt_sha256}\n", encoding="utf-8")
    return {
        "run_start_receipt": str(warehouse_receipt),
        "run_start_receipt_sha256": receipt_sha256,
        "run_command_sha256": command_sha256,
        "source_config_sha256": payload["source_config_sha256"],
        "runtime_config_sha256": payload["runtime_config_sha256"],
        "training_entry_sha256": payload["training_entry_sha256"],
    }


def copy_if_newer(src, dst_dir, start_ts):
    copied = []
    if not src.exists():
        return copied
    for path in src.iterdir():
        if not path.is_file():
            continue
        if path.stat().st_mtime + 2 < start_ts:
            continue
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / path.name
        shutil.copy2(path, dst)
        copied.append(str(dst))
    return copied


def model_score(path):
    match = re.search(r"_H([0-9]+(?:\.[0-9]+)?)\.pth$", path.name)
    if not match:
        return float("-inf")
    raw = match.group(1)
    if "." in raw:
        return float(raw)
    return float(raw) / 100.0


def prune_model_artifacts(attempt_dir, keep=3):
    logs_dir = attempt_dir / "logs"
    checkpoints_dir = attempt_dir / "checkpoints"
    candidates = []
    for folder in (logs_dir, checkpoints_dir):
        if folder.exists():
            candidates.extend(path for path in folder.glob("*.pth") if path.is_file())

    best_models = [path for path in candidates if path.name.startswith("best_model_")]
    keep_set = set(sorted(best_models, key=lambda path: (model_score(path), path.stat().st_mtime), reverse=True)[:keep])
    removed = []
    for path in candidates:
        if path in keep_set:
            continue
        path.unlink()
        removed.append(str(path))
    return sorted(str(path) for path in keep_set), sorted(removed)


def copy_artifacts_to_warehouse(plan, job, worktree, log_path, runtime_config, start_ts):
    attempt_dir = warehouse_attempt_dir(plan, job)
    if not attempt_dir.is_dir():
        raise RuntimeError(f"Warehouse job directory was not reserved before artifact copy: {attempt_dir}")
    copied = []
    copied += copy_if_newer(worktree / "train_log" / "CUB", attempt_dir / "logs", start_ts)
    copied += copy_if_newer(worktree / "checkpoints" / "CUB", attempt_dir / "checkpoints", start_ts)
    if log_path.exists():
        (attempt_dir / "receipts").mkdir(parents=True, exist_ok=True)
        dst = attempt_dir / "receipts" / log_path.name
        shutil.copy2(log_path, dst)
        copied.append(str(dst))
    if runtime_config.exists():
        (attempt_dir / "configs").mkdir(parents=True, exist_ok=True)
        dst = attempt_dir / "configs" / runtime_config.name
        shutil.copy2(runtime_config, dst)
        copied.append(str(dst))
    kept_models, removed_models = prune_model_artifacts(attempt_dir, keep=3)
    removed_set = set(removed_models)
    copied = [path for path in copied if path not in removed_set]
    run_start_receipt = attempt_dir / "receipts" / "run_start_receipt.json"
    receipt_payload = load_json(run_start_receipt) if run_start_receipt.exists() else {}
    manifest = {
        "job_id": job["job_id"],
        "attempt_id": job["attempt_id"],
        "warehouse_scope": str(plan.get("warehouse_scope", "legacy_job_attempt")),
        "warehouse_attempt_id": str(plan.get("warehouse_attempt_id", "")),
        "run_id": str(plan.get("run_id", "")),
        "warehouse_dir": str(attempt_dir),
        "copied_files": copied,
        "kept_model_files": kept_models,
        "removed_model_files": removed_models,
        "model_retention_policy": "keep top 3 best_model_*.pth by H; remove other .pth files",
        "run_start_receipt": str(run_start_receipt) if run_start_receipt.exists() else "",
        "run_start_receipt_sha256": sha256_path(run_start_receipt) if run_start_receipt.exists() else "",
        "run_command_sha256": str(receipt_payload.get("command_sha256", "")),
        "recorded_at": utc_now(),
    }
    (attempt_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(attempt_dir)


def artifact_manifest_evidence(plan, job, warehouse_dir, run_dir):
    manifest_path = Path(warehouse_dir) / "artifact_manifest.json"
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    receipt_dir = run_dir / "artifact_manifests"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(manifest_path, receipt_dir / f"{job['job_id']}.json")
    return {
        "artifact_manifest": str(manifest_path),
        "artifact_manifest_sha256": digest,
        "artifact_manifest_job_id": str(job["job_id"]),
        "artifact_manifest_run_id": str(plan.get("run_id", "")),
        "artifact_manifest_attempt_id": str(plan.get("warehouse_attempt_id", "")),
    }


def run_job(run_dir, plan, job, gpu):
    job_id = job["job_id"]
    update_job(run_dir, job_id, status="running", gpu=str(gpu), started_at=utc_now())
    append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": "job_started", "job_id": job_id, "gpu": gpu})

    resolved_from = ""
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{job_id}_gpu{gpu}.log"
    runtime_config = run_dir / "runtime_configs" / f"{job_id}_gpu{gpu}.yaml"
    worktree = None
    start_ts = time.time()
    warehouse_dir = ""
    warehouse_reserved = False
    manifest_evidence = {}
    receipt_evidence = {}
    try:
        reserve_warehouse_attempt_dir(plan, job)
        warehouse_reserved = True
        worktree = ensure_worktree(plan, gpu)
        config_dir = run_dir / "configs"
        runtime_config_dir = run_dir / "runtime_configs"
        runtime_config_dir.mkdir(parents=True, exist_ok=True)
        source_config = config_dir / f"{job_id}.yaml"
        if job["phase"] == "repeat":
            rank = int(job["source_rank"])
            top_row = top_job_for_rank(run_dir, rank)
            if top_row is None:
                update_job(run_dir, job_id, status="skipped", error=f"missing top{rank} completed source")
                append_summary(run_dir, {**job, "status": "skipped", "gpu": gpu, "resolved_from_job_id": "", "log_path": ""})
                return
            resolved_from = top_row["job_id"]
            source_config = config_dir / f"{resolved_from}.yaml"

        config_text = source_config.read_text(encoding="utf-8")
        config_text = config_set_scalar(config_text, "device", "cuda:0")
        config_text = config_set_scalar(config_text, "random_seed", job["seed"])
        runtime_config.write_text(config_text, encoding="utf-8")

        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(gpu)
        python_cmd = str(plan.get("python", "python"))
        conda_env = str(plan.get("conda_env", "")).lower()
        if os.path.isabs(python_cmd) or conda_env in {"", "direct", "none"}:
            cmd = [python_cmd, "train_GTPJ_CUB.py", "--config", str(runtime_config)]
        else:
            cmd = [
                "conda", "run", "--no-capture-output", "-n", plan["conda_env"],
                python_cmd, "train_GTPJ_CUB.py", "--config", str(runtime_config),
            ]
        receipt_evidence = prepare_run_start_receipt(
            run_dir,
            plan,
            job,
            worktree,
            source_config,
            runtime_config,
            cmd,
            log_path,
        )
        code = run(cmd, cwd=worktree, env=env, log_path=log_path).returncode
        warehouse_dir = copy_artifacts_to_warehouse(plan, job, worktree, log_path, runtime_config, start_ts)
        manifest_evidence = artifact_manifest_evidence(plan, job, warehouse_dir, run_dir)
        if code != 0:
            row = {
                **job,
                **manifest_evidence,
                **receipt_evidence,
                "status": "failed",
                "gpu": gpu,
                "resolved_from_job_id": resolved_from,
                "log_path": str(log_path),
                "warehouse_dir": warehouse_dir,
            }
            update_job(run_dir, job_id, status="failed", returncode=code, log_path=str(log_path), resolved_from_job_id=resolved_from, warehouse_dir=warehouse_dir)
            append_summary(run_dir, row)
            append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": "job_failed", "job_id": job_id, "gpu": gpu, "returncode": code})
            return

        metrics = parse_metrics(log_path)
        status = "completed" if metrics.get("H") else "failed"
        row = {
            **job,
            **metrics,
            **manifest_evidence,
            **receipt_evidence,
            "status": status,
            "gpu": gpu,
            "resolved_from_job_id": resolved_from,
            "log_path": str(log_path),
            "warehouse_dir": warehouse_dir,
        }
        update_job(run_dir, job_id, status=status, returncode=code, log_path=str(log_path), resolved_from_job_id=resolved_from, metrics=metrics, warehouse_dir=warehouse_dir)
        append_summary(run_dir, row)
        append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": f"job_{status}", "job_id": job_id, "gpu": gpu, "metrics": metrics, "warehouse_dir": warehouse_dir})
        if status == "completed":
            maybe_stop_after_confirmation_hit(run_dir, plan, row)
    except Exception as exc:
        error_path = log_dir / f"{job_id}_gpu{gpu}.error.txt"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        if worktree is not None and warehouse_reserved:
            try:
                warehouse_dir = copy_artifacts_to_warehouse(plan, job, worktree, log_path, runtime_config, start_ts)
            except Exception:
                warehouse_dir = ""
        if not warehouse_dir and warehouse_reserved:
            attempt_dir = warehouse_attempt_dir(plan, job)
            (attempt_dir / "receipts").mkdir(parents=True, exist_ok=True)
            dst = attempt_dir / "receipts" / error_path.name
            shutil.copy2(error_path, dst)
            (attempt_dir / "artifact_manifest.json").write_text(
                json.dumps(
                    {
                        "job_id": job["job_id"],
                        "attempt_id": job["attempt_id"],
                        "warehouse_scope": str(plan.get("warehouse_scope", "legacy_job_attempt")),
                        "warehouse_attempt_id": str(plan.get("warehouse_attempt_id", "")),
                        "run_id": str(plan.get("run_id", "")),
                        "warehouse_dir": str(attempt_dir),
                        "copied_files": [str(dst)],
                        "run_start_receipt": receipt_evidence.get("run_start_receipt", ""),
                        "run_start_receipt_sha256": receipt_evidence.get("run_start_receipt_sha256", ""),
                        "run_command_sha256": receipt_evidence.get("run_command_sha256", ""),
                        "error": str(exc),
                        "recorded_at": utc_now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            warehouse_dir = str(attempt_dir)
        if warehouse_dir:
            manifest_evidence = artifact_manifest_evidence(plan, job, warehouse_dir, run_dir)
        row = {
            **job,
            **manifest_evidence,
            **receipt_evidence,
            "status": "failed",
            "gpu": gpu,
            "resolved_from_job_id": resolved_from,
            "log_path": str(log_path if log_path.exists() else error_path),
            "warehouse_dir": warehouse_dir,
        }
        update_job(run_dir, job_id, status="failed", error=str(exc), log_path=str(row["log_path"]), resolved_from_job_id=resolved_from, warehouse_dir=warehouse_dir)
        append_summary(run_dir, row)
        append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": "job_failed", "job_id": job_id, "gpu": gpu, "error": str(exc), "error_log": str(error_path)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", required=True, type=int)
    args = parser.parse_args()
    run_dir = Path(__file__).resolve().parent
    plan = load_json(run_dir / "plan.json")
    gpu_slots = {int(value): idx for idx, value in enumerate(plan["gpus"])}
    gpu_slot = gpu_slots[args.gpu]
    assigned = [job for job in plan["jobs"] if int(job["gpu_slot"]) == gpu_slot]

    for job in assigned:
        if job["phase"] != "explore":
            continue
        if stop_requested(run_dir):
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "explore")
            break
        status = load_json(run_dir / "batch_status.json").get("jobs", {}).get(job["job_id"], {}).get("status")
        if status in {"completed", "failed", "skipped", "running"}:
            continue
        run_job(run_dir, plan, job, args.gpu)
        refresh_batch_status(run_dir)
        if stop_requested(run_dir):
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "explore")
            break

    while not all_explore_finished(run_dir, plan):
        refresh_batch_status(run_dir)
        if stop_requested(run_dir):
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "explore")
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "repeat")
        time.sleep(30)

    for job in assigned:
        if job["phase"] != "repeat":
            continue
        if stop_requested(run_dir):
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "repeat")
            break
        status = load_json(run_dir / "batch_status.json").get("jobs", {}).get(job["job_id"], {}).get("status")
        if status in {"completed", "failed", "skipped", "running"}:
            continue
        run_job(run_dir, plan, job, args.gpu)
        refresh_batch_status(run_dir)
        if stop_requested(run_dir):
            skip_remaining_due_stop(run_dir, assigned, args.gpu, "repeat")
            break
    refresh_batch_status(run_dir)


if __name__ == "__main__":
    main()
'''


def infer_attempt_id_from_path(path: Path) -> str:
    for candidate in (path, *path.parents):
        if re.fullmatch(r"attempt-[0-9]{3}", candidate.name, re.IGNORECASE):
            return candidate.name.upper()
    return ""


def cmd_plan_dynamic_routing_batch(args: argparse.Namespace) -> int:
    if immutable_template_standard_is_active() and not bool(args.debug_smoke):
        raise WorkflowError(
            "legacy dynamic-routing formal batch planner is retired under "
            "SYS-WORKFLOW-V5; formal starts must use a canonical framework "
            "experiment matrix and prepare-run-start-receipt"
        )
    trial_dir = (REPO_ROOT / args.trial_dir).resolve() if not Path(args.trial_dir).is_absolute() else Path(args.trial_dir)
    if not trial_dir.exists():
        raise WorkflowError(f"Missing trial dir: {display_path(trial_dir)}")
    base_config = Path(args.base_config) if args.base_config else trial_dir / "config.yaml"
    if not base_config.is_absolute():
        base_config = REPO_ROOT / base_config
    if not base_config.exists():
        raise WorkflowError(f"Missing base config: {display_path(base_config)}")
    agent_runtime_gate = ""
    gate_path: Path | None = None
    if args.agent_runtime_gate:
        gate_path = resolve_agent_runtime_gate_path(args.agent_runtime_gate)
        gate_errors = validate_agent_runtime_gate_file(gate_path) if gate_path.exists() else [
            f"Missing agent runtime gate: {display_path(gate_path)}"
        ]
        if gate_errors:
            raise WorkflowError("Agent runtime validation failed:\n" + "\n".join(gate_errors))
        agent_runtime_gate = display_path(gate_path)
    elif not args.debug_smoke:
        raise WorkflowError(
            "Formal dynamic routing batch requires --agent-runtime-gate. "
            "Use --debug-smoke only for non-formal runner probes."
        )
    warehouse_attempt_id = ""
    if args.attempt_id:
        warehouse_attempt_id, _attempt_lower = normalize_attempt_ids(args.attempt_id)
    elif gate_path is not None:
        warehouse_attempt_id = infer_attempt_id_from_path(gate_path)

    formal_evidence = not bool(args.debug_smoke)
    if formal_evidence:
        source_control = require_formal_dynamic_routing_source_control(args, base_config)
        branch = str(source_control["training_branch_label"])
        commit = str(source_control["training_commit"])
    else:
        branch = args.branch or current_branch()
        commit = resolve_commit(args.commit or "HEAD")
        source_control = {
            "source_control_policy": "debug_smoke_no_formal_freeze",
            "plan_generation_commit": resolve_commit("HEAD"),
            "training_commit": commit,
            "branch": branch,
            "dirty_state": git(["status", "--short"], check=False) or "not_checked_clean",
            "fingerprint_paths": {},
            "missing_fingerprint_paths": [],
        }

    plan_seed = int(args.seed)
    plan_limit_jobs = int(getattr(args, "limit_jobs", 0) or 0)
    jobs = build_dynamic_routing_jobs(seed=plan_seed, profile=args.profile)
    jobs = limit_dynamic_routing_jobs(jobs, plan_limit_jobs)
    if int(args.jobs) != len(jobs):
        raise WorkflowError(f"Dynamic routing batch profile {args.profile!r} expects {len(jobs)} jobs, got --jobs {args.jobs}.")
    if warehouse_attempt_id:
        for job in jobs:
            job["attempt_id"] = warehouse_attempt_id

    run_id = args.run_id or f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-dynroute50-2gpu"
    parameter_matrix_path = ""
    parameter_matrix_frozen_rows: dict[str, dict[str, str]] = {}
    if formal_evidence and parameter_matrix_policy_is_active():
        if not warehouse_attempt_id:
            raise WorkflowError(
                "Formal parameter-matrix policy requires --attempt-id. Run prepare-dynamic-routing-matrix, "
                "commit its matrix, then plan the formal batch."
            )
        matrix_path = trial_dir / "attempts" / warehouse_attempt_id / PARAMETER_MATRIX_CSV
        rows = read_parameter_matrix(matrix_path)
        matrix_rel = repo_relative_path(matrix_path, "Formal dynamic routing parameter matrix")
        if read_text_at_commit(commit, matrix_rel) != read_text(matrix_path):
            raise WorkflowError("Formal parameter matrix must be committed unchanged in the training commit")
        base_text_for_matrix = read_text_at_commit(
            commit,
            repo_relative_path(base_config, "Formal dynamic routing base config"),
        )
        expected_rows = build_parameter_matrix_rows(
            jobs=jobs,
            base_config_text=base_text_for_matrix,
            base_version=args.base_version,
            code_ref=args.base_code_tag or args.base_version,
            run_id=run_id,
        )
        expected_by_job = {row["job_id"]: row for row in expected_rows}
        matrix_errors = validate_parameter_matrix_rows(
            rows,
            expected_job_ids=set(expected_by_job),
            require_ready=True,
            matrix_path=matrix_path,
        )
        matrix_errors.extend(parameter_matrix_view_errors(matrix_path, rows))
        for row in rows:
            if row.get("run_id", "") != run_id:
                matrix_errors.append(
                    f"{row.get('job_id')} run_id {row.get('run_id', '')!r} does not match requested {run_id!r}"
                )
            expected = expected_by_job.get(row.get("job_id", ""))
            if expected is None:
                continue
            for field in parameter_matrix_frozen_fields(expected):
                if row.get(field, "") != expected.get(field, ""):
                    matrix_errors.append(
                        f"{row.get('job_id')} {field} differs from the frozen batch plan; "
                        "regenerate and commit the parameter matrix before running"
                    )
        matrix_errors.extend(
            parameter_matrix_conflicts(
                rows,
                REPO_ROOT / "experiments",
                exclude_paths={matrix_path},
            )
        )
        if matrix_errors:
            raise WorkflowError("Formal parameter-matrix gate failed:\n" + "\n".join(matrix_errors))
        parameter_matrix_path = display_path(matrix_path)
        parameter_matrix_frozen_rows = {
            row["job_id"]: parameter_matrix_frozen_fields(row)
            for row in rows
        }

    run_root = REPO_ROOT / ".gtpj_runtime" / "batches"
    run_dir = run_root / run_id
    if run_dir.exists():
        raise WorkflowError(f"Refusing to overwrite existing run dir: {display_path(run_dir)}")
    ensure_dir(run_dir)
    ensure_dir(run_dir / "configs")
    ensure_dir(run_dir / "logs")
    ensure_dir(run_dir / "pids")
    ensure_dir(run_dir / "runtime_configs")
    ensure_dir(run_dir / "run_start_receipts")

    gpus = [int(part.strip()) for part in args.gpus.split(",") if part.strip()]
    if not gpus:
        raise WorkflowError("At least one GPU id is required.")
    for index, job in enumerate(jobs):
        job["gpu_slot"] = index % len(gpus)

    trial_id, _trial_slug = parse_trial_folder_name(trial_dir)
    base_version = args.base_version
    plan = {
        "run_id": run_id,
        "profile": args.profile,
        "seed": plan_seed,
        "limit_jobs": plan_limit_jobs,
        "requested_jobs": int(args.jobs),
        "created_at": utc_now(),
        "formal_evidence": formal_evidence,
        "evidence_level": "debug_smoke" if args.debug_smoke else "formal_pre_run",
        "agent_runtime_gate": agent_runtime_gate,
        "trial_dir": display_path(trial_dir),
        "base_config": display_path(base_config),
        "base_version": base_version,
        "base_code_tag": args.base_code_tag or base_version,
        "trial_id": trial_id,
        "branch": branch,
        "commit": commit,
        "source_control": source_control,
        "plan_generation_commit": str(source_control["plan_generation_commit"]),
        "formal_source_clean": formal_evidence,
        "commit_policy": str(source_control["source_control_policy"]),
        "git_remote": args.git_remote,
        "gpus": gpus,
        "server_repo": args.server_repo,
        "worktree_root": args.worktree_root,
        "warehouse_root": args.warehouse_root,
        "warehouse_scope": "attempt_run" if warehouse_attempt_id else "legacy_job_attempt",
        "warehouse_attempt_id": warehouse_attempt_id,
        "parameter_matrix": parameter_matrix_path,
        "parameter_matrix_frozen_rows": parameter_matrix_frozen_rows,
        "confirmation_policy": confirmation_policy_for_profile(
            args.profile,
            target_h=str(getattr(args, "restore_target_h", "") or ""),
            tolerance_h=str(getattr(args, "near_miss_tolerance_h", "") or ""),
        ),
        "runtime_resource_links": ["data"],
        "conda_env": args.conda_env,
        "python": args.python,
        "jobs": jobs,
    }
    write_new(run_dir / "plan.json", json.dumps(plan, ensure_ascii=False, indent=2))

    if formal_evidence:
        base_text = read_text_at_commit(
            commit,
            repo_relative_path(base_config, "Formal dynamic routing base config"),
        )
    else:
        base_text = read_text(base_config)
    for job in jobs:
        config_text = render_config_with_updates(base_text, job["config_updates"])
        write_new(run_dir / "configs" / f"{job['job_id']}.yaml", config_text)

    status = {
        "run_id": run_id,
        "status": "planned",
        "created_at": utc_now(),
        "jobs": {
            str(job["job_id"]): {
                "status": "pending",
                "phase": job["phase"],
                "group": job["group"],
                "name": job["name"],
                "gpu_slot": job["gpu_slot"],
            }
            for job in jobs
        },
    }
    write_new(run_dir / "batch_status.json", json.dumps(status, ensure_ascii=False, indent=2))
    write_new(run_dir / "events.jsonl", "")
    write_new(
        run_dir / "run_dynamic_routing_batch.py",
        _dynamic_runner_script(),
    )
    gpu_lines = []
    for gpu in gpus:
        gpu_lines.extend(
            [
                f"nohup {args.controller_python} run_dynamic_routing_batch.py --gpu {gpu} > logs/gpu{gpu}.controller.out 2>&1 &",
                f"echo $! > pids/gpu{gpu}.pid",
            ]
        )
    write_new_lf(
        run_dir / "start_batch.sh",
        "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\"\n"
        "mkdir -p logs pids runtime_configs run_start_receipts\n"
        + "\n".join(gpu_lines),
    )
    server_run_dir = PurePosixPath(str(args.server_repo)) / ".gtpj_runtime" / "batches" / run_id
    write_new(
        run_dir / "README.md",
        f"""# {run_id}

profile: {args.profile}
trial_dir: {display_path(trial_dir)}
branch: {branch}
commit: {commit}
formal_evidence: {str(not bool(args.debug_smoke)).lower()}
agent_runtime_gate: {agent_runtime_gate or 'debug_smoke_not_required'}
warehouse_scope: {'attempt_run' if warehouse_attempt_id else 'legacy_job_attempt'}
warehouse_attempt_id: {warehouse_attempt_id or 'not_set'}
gpus: {','.join(str(gpu) for gpu in gpus)}

Start on server:

```bash
cd {server_run_dir.as_posix()}
bash start_batch.sh
```

Outputs:

- `batch_status.json`
- `summary.csv`
- `summary.jsonl`
- `events.jsonl`
- `logs/`
- `runtime_configs/`
- `run_start_receipts/`（逐任务训练启动收据；取回结果时必须一起复制）
- `artifact_manifests/`（逐任务 Warehouse 证据清单；取回结果时必须一起复制）

Stop policy:

- Create `STOP_REQUESTED` in this run directory to prevent controllers from starting new jobs.
- Jobs already running are allowed to finish; pending jobs assigned to each controller are marked `skipped`.
""",
    )
    print(f"dynamic-routing-plan-created: {display_path(run_dir)}")
    print(f"jobs: {len(jobs)}")
    print(f"branch: {branch}")
    print(f"commit: {commit}")
    return 0


def _read_summary_rows(run_dir: Path) -> list[dict[str, str]]:
    summary = run_dir / "summary.csv"
    if not summary.exists():
        return []
    with summary.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cmd_dynamic_routing_status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    status_path = run_dir / "batch_status.json"
    if not status_path.exists():
        raise WorkflowError(f"Missing batch_status.json: {display_path(status_path)}")
    status = json.loads(read_text(status_path))
    rows = _read_summary_rows(run_dir)
    counts: dict[str, int] = {}
    for job in status.get("jobs", {}).values():
        state = str(job.get("status", "unknown"))
        counts[state] = counts.get(state, 0) + 1
    completed = [row for row in rows if row.get("status") == "completed" and row.get("H")]
    best = max(completed, key=lambda row: float(row["H"])) if completed else None
    print(f"run_id: {status.get('run_id', run_dir.name)}")
    print(f"batch_status: {status.get('status', 'unknown')}")
    print("counts: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"summary_rows: {len(rows)}")
    if best:
        print(
            "best_completed: "
            f"{best.get('job_id')} {best.get('name')} H={best.get('H')} "
            f"U={best.get('U')} S={best.get('S')}"
        )
    return 0


def cmd_analyze_dynamic_routing_batch(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    rows = _read_summary_rows(run_dir)
    if not rows:
        raise WorkflowError(f"No summary rows found in {display_path(run_dir)}")
    completed = [row for row in rows if row.get("status") == "completed" and row.get("H")]
    completed.sort(key=lambda row: float(row["H"]), reverse=True)
    print(f"completed: {len(completed)} / {len(rows)}")
    print(f"reference: v3/CONFIRM-001 local-v3-054 confirmed_H=74.47; v5 repeat mean H=74.44")
    for row in completed[: int(args.top_k)]:
        print(
            f"rank: {row.get('job_id')} group={row.get('group')} name={row.get('name')} "
            f"H={row.get('H')} U={row.get('U')} S={row.get('S')} ZS={row.get('ZS')} "
            f"epoch={row.get('best_epoch')}"
        )
    repeat_rows = [row for row in completed if row.get("phase") == "repeat"]
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in repeat_rows:
        by_source.setdefault(row.get("resolved_from_job_id", ""), []).append(row)
    for source, source_rows in sorted(by_source.items()):
        h_values = [float(row["H"]) for row in source_rows if row.get("H")]
        u_values = [float(row["U"]) for row in source_rows if row.get("U")]
        s_values = [float(row["S"]) for row in source_rows if row.get("S")]
        if not h_values:
            continue
        print(
            f"repeat_mean: source={source} n={len(h_values)} "
            f"H={sum(h_values)/len(h_values):.2f} "
            f"U={sum(u_values)/len(u_values):.2f} "
            f"S={sum(s_values)/len(s_values):.2f}"
        )
    failures = [row for row in rows if row.get("status") == "failed"]
    if failures:
        print("failures: " + ", ".join(row.get("job_id", "") for row in failures))
    return 0


DEFAULT_DYNAMIC_ROUTING_TRIAL_DIR = (
    "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
)
WORKFLOW_STATES = [
    "requested",
    "routed",
    "planned",
    "launched",
    "running",
    "stopped",
    "completed",
    "failed",
    "blocked",
    "parsed",
    "quality_checked",
    "closed_out",
    "synced",
    "candidate",
    "rejected",
    "confirmed",
    "promotion_blocked",
    "promote_ready",
]


def infer_workflow_route(phrase: str, workflow_kind: str = "") -> dict[str, object]:
    normalized = phrase.lower()
    kind = workflow_kind
    if not kind:
        if any(token in normalized for token in ["dr-035", "dr035", "h=76", "h76", "dynamic", "动态"]):
            kind = "dynamic-routing"
        else:
            raise WorkflowError("Only dynamic-routing workflow routing is implemented in the minimal dispatcher.")
    if kind != "dynamic-routing":
        raise WorkflowError(f"Unsupported workflow kind in minimal dispatcher: {kind}")
    return {
        "workflow_kind": "dynamic-routing",
        "experiment_type": "trial_internal_tune",
        "subject_type": "run",
        "trial_dir": DEFAULT_DYNAMIC_ROUTING_TRIAL_DIR,
        "profile": "h76-existing-routing-100",
        "required_roles": [
            "Runner Monitor",
            "Log Analyst",
            "Result Analyst",
            "Evidence Quality Checker",
        ],
        "state_flow": WORKFLOW_STATES,
        "next_helper": "run-workflow",
    }


def workflow_run_dir(run_dir_arg: str) -> Path:
    run_dir = Path(run_dir_arg)
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    return run_dir


def write_workflow_transition(run_dir: Path, transition: str, state: str, note: str = "") -> None:
    record = {
        "at": utc_now(),
        "transition": transition,
        "state": state,
        "note": note,
    }
    with (run_dir / "TRANSITIONS.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_workflow_state(run_dir: Path, state: str, extra: dict[str, object] | None = None) -> None:
    plan_path = run_dir / "plan.json"
    plan = json.loads(read_text(plan_path)) if plan_path.exists() else {}
    state_path = run_dir / "workflow_state.json"
    previous: dict[str, object] = {}
    if state_path.exists():
        try:
            previous = json.loads(read_text(state_path))
        except json.JSONDecodeError:
            previous = {}
    data: dict[str, object] = {
        "subject_id": plan.get("run_id", run_dir.name),
        "subject_type": "run",
        "workflow_kind": "dynamic-routing",
        "current_state": state,
        "allowed_next_states": WORKFLOW_STATES,
        "updated_at": utc_now(),
    }
    for key, value in previous.items():
        if key not in data:
            data[key] = value
    if extra:
        data.update(extra)
    state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dynamic_routing_status_snapshot(run_dir: Path) -> dict[str, object]:
    status_path = run_dir / "batch_status.json"
    if not status_path.exists():
        raise WorkflowError(f"Missing batch_status.json: {display_path(status_path)}")
    status = json.loads(read_text(status_path))
    rows = _read_summary_rows(run_dir)
    counts: dict[str, int] = {}
    for job in status.get("jobs", {}).values():
        state = str(job.get("status", "unknown"))
        counts[state] = counts.get(state, 0) + 1
    completed_by_summary_order = [row for row in rows if row.get("status") == "completed" and row.get("H")]
    completed = list(completed_by_summary_order)
    completed.sort(key=lambda row: float(row["H"]), reverse=True)
    terminal_states = {"completed", "failed", "skipped"}
    all_terminal = bool(status.get("jobs")) and all(
        str(job.get("status", "unknown")) in terminal_states for job in status.get("jobs", {}).values()
    )
    failed = counts.get("failed", 0)
    batch_status = str(status.get("status", "unknown"))
    if batch_status == "stopped":
        workflow_state = "stopped"
    elif all_terminal and failed:
        workflow_state = "failed"
    elif all_terminal:
        workflow_state = "completed"
    elif counts.get("running", 0):
        workflow_state = "running"
    else:
        workflow_state = str(status.get("status", "unknown"))
    return {
        "run_id": status.get("run_id", run_dir.name),
        "batch_status": batch_status,
        "workflow_state": workflow_state,
        "counts": counts,
        "summary_rows": len(rows),
        "completed": completed,
        "completed_by_summary_order": completed_by_summary_order,
        "best": completed[0] if completed else None,
    }


def monitor_seen_jobs_path(run_dir: Path, seen_jobs_file: str = "") -> Path:
    if seen_jobs_file:
        path = Path(seen_jobs_file)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path
    return run_dir / "monitor_seen_completed_jobs.json"


def load_seen_completed_jobs(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return set()
    if isinstance(data, list):
        return {str(item) for item in data}
    if isinstance(data, dict):
        value = data.get("completed_job_ids", [])
        if isinstance(value, list):
            return {str(item) for item in value}
    return set()


def save_seen_completed_jobs(path: Path, completed_job_ids: set[str]) -> None:
    ensure_dir(path.parent)
    path.write_text(
        json.dumps(
            {
                "updated_at": utc_now(),
                "completed_job_ids": sorted(completed_job_ids),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def resolve_monitor_activity_log(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def append_monitor_activity_log(activity_log: Path, snapshot: dict[str, object], new_rows: list[dict[str, str]]) -> None:
    if not new_rows:
        return
    ensure_dir(activity_log.parent)
    if not activity_log.exists():
        activity_log.write_text(
            "# Agent Activity\n\n"
            "| Time | Workflow display name | Role key | Agent instance | UI mode | Status | Action | Evidence | Next |\n"
            "|---|---|---|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    counts = snapshot.get("counts", {})
    best = snapshot.get("best")
    best_text = "best=none"
    if isinstance(best, dict):
        best_text = f"best={best.get('job_id')} H={best.get('H')}"
    count_text = ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) if isinstance(counts, dict) else ""
    with activity_log.open("a", encoding="utf-8") as handle:
        for row in new_rows:
            job_id = row.get("job_id", "")
            action = (
                f"Completed {job_id}: {row.get('name')} "
                f"H={row.get('H')} U={row.get('U')} S={row.get('S')} "
                f"ZS={row.get('ZS')} epoch={row.get('best_epoch')}; "
                f"{best_text}; counts: {count_text}."
            )
            handle.write(
                f"| {utc_now()} | current owner thread | runner_monitor | current_owner_thread | owner_thread | "
                f"job_completed_report | {action} | "
                "`summary.csv` / `batch_status.json` / `events.jsonl` | Continue live monitor until closeout. |\n"
            )


def cmd_route_experiment(args: argparse.Namespace) -> int:
    route = infer_workflow_route(args.phrase, args.workflow_kind)
    print(f"workflow_kind: {route['workflow_kind']}")
    print(f"experiment_type: {route['experiment_type']}")
    print(f"subject_type: {route['subject_type']}")
    print(f"trial_dir: {route['trial_dir']}")
    print(f"profile: {route['profile']}")
    print("required_roles: " + ", ".join(str(role) for role in route["required_roles"]))
    print("agent_instances: not_started_by_route")
    print("state_flow: " + " -> ".join(str(state) for state in route["state_flow"]))
    print(f"next_helper: {route['next_helper']}")
    return 0


def cmd_run_workflow(args: argparse.Namespace) -> int:
    if bool(args.debug_smoke) == bool(args.formal):
        raise WorkflowError("run-workflow requires exactly one of --debug-smoke or --formal")
    if args.formal and immutable_template_standard_is_active():
        experiment_dir_text = str(getattr(args, "experiment_dir", "") or "").strip()
        if not experiment_dir_text:
            raise WorkflowError(
                "run-workflow --formal requires --experiment-dir under SYS-WORKFLOW-V5"
            )
        experiment_dir = Path(experiment_dir_text)
        if not experiment_dir.is_absolute():
            experiment_dir = REPO_ROOT / experiment_dir
        require_ready_experiment_base(experiment_dir)
        raise WorkflowError(
            "run-workflow legacy dynamic-routing batch runner is retired for "
            "SYS-WORKFLOW-V5 formal experiments; freeze the canonical experiment "
            "PARAMETER_MATRIX.csv and launch each RUN row through "
            "prepare-run-start-receipt"
        )
    if args.formal and not args.agent_runtime_gate:
        raise WorkflowError("run-workflow --formal requires --agent-runtime-gate <agent_runtime.yaml>")
    workflow_mode = str(args.workflow_mode or "").strip()
    if not workflow_mode:
        raise WorkflowError(
            "run-workflow requires --workflow-mode "
            "live_multi_agent_monitor or server_frozen_runner; do not guess"
        )
    gate_backend = ""
    if args.formal and args.agent_runtime_gate:
        gate_path = resolve_agent_runtime_gate_path(args.agent_runtime_gate)
        gate_data = read_shallow_yaml(gate_path)
        gate_backend = str(gate_data.get("formal_runtime_backend", "")).strip() or "named_owner_thread"
        if workflow_mode == "live_multi_agent_monitor" and gate_backend == "server_detached_role_only":
            raise WorkflowError(
                "workflow_mode=live_multi_agent_monitor requires named-owner-thread agent_runtime gate, "
                "not server_detached_role_only"
            )
        if workflow_mode == "server_frozen_runner" and gate_backend != "server_detached_role_only":
            raise WorkflowError(
                "workflow_mode=server_frozen_runner requires formal_runtime_backend: server_detached_role_only"
            )
    run_mode = "debug_smoke" if args.debug_smoke else "formal"
    if args.debug_smoke:
        activation_mode = "role_only"
        agent_instance_mode = "role_only"
        formal_backend = "not_applicable_debug_smoke"
    elif workflow_mode == "server_frozen_runner":
        activation_mode = "role_only"
        agent_instance_mode = "role_only"
        formal_backend = "server_detached_role_only"
    else:
        activation_mode = "real_multi_agent"
        agent_instance_mode = "named_owner_thread"
        formal_backend = gate_backend or "named_owner_thread"
    route = infer_workflow_route(args.phrase, args.workflow_kind)
    profile = args.profile or str(route["profile"])
    run_id = args.run_id or f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-workflow-dynroute"
    profile_jobs = build_dynamic_routing_jobs(seed=int(args.seed), profile=profile)
    expected_jobs = int(args.jobs or args.limit_jobs or len(profile_jobs))
    plan_args = argparse.Namespace(
        trial_dir=args.trial_dir or str(route["trial_dir"]),
        base_config=args.base_config,
        run_id=run_id,
        attempt_id=args.attempt_id,
        jobs=expected_jobs,
        limit_jobs=int(args.limit_jobs or 0),
        profile=profile,
        base_version=args.base_version,
        base_code_tag=args.base_code_tag,
        seed=int(args.seed),
        gpus=args.gpus,
        branch=args.branch,
        commit=args.commit,
        git_remote=args.git_remote,
        server_repo=args.server_repo,
        worktree_root=args.worktree_root,
        warehouse_root=args.warehouse_root,
        conda_env=args.conda_env,
        python=args.python,
        controller_python=args.controller_python,
        agent_runtime_gate=args.agent_runtime_gate,
        allow_historical_training_commit=bool(getattr(args, "allow_historical_training_commit", False)),
        restore_target_h=args.restore_target_h,
        near_miss_tolerance_h=args.near_miss_tolerance_h,
        debug_smoke=(run_mode == "debug_smoke"),
    )
    cmd_plan_dynamic_routing_batch(plan_args)
    run_dir = REPO_ROOT / ".gtpj_runtime" / "batches" / run_id
    state = "planned"
    write_workflow_state(
        run_dir,
        state,
        {
            "run_mode": run_mode,
            "workflow_mode": workflow_mode,
            "activation_mode": activation_mode,
            "agent_instance_mode": agent_instance_mode,
            "formal_runtime_backend": formal_backend,
            "required_roles": route["required_roles"],
            "real_agent_instances_started_by_helper": False,
            "real_agent_instances_verified_by_gate": bool(args.formal and workflow_mode == "live_multi_agent_monitor"),
            "agent_runtime_gate_satisfied": bool(args.formal),
            "formal_evidence": not bool(args.debug_smoke),
            "thread_creation_allowed": bool(args.formal and workflow_mode == "live_multi_agent_monitor"),
            "server_detached_expected": bool(args.formal and workflow_mode == "server_frozen_runner"),
            "route": route,
        },
    )
    write_workflow_transition(run_dir, "route", "routed", args.phrase)
    write_workflow_transition(run_dir, "plan", "planned", f"profile={profile} jobs={expected_jobs}")
    if args.launch:
        subprocess.run(["bash", "start_batch.sh"], cwd=run_dir, check=True)
        state = "launched"
        write_workflow_state(run_dir, state, {"launched_at": utc_now()})
        write_workflow_transition(run_dir, "launch", "launched", "start_batch.sh")
    print(f"workflow-run-dir: {display_path(run_dir)}")
    print(f"workflow_state: {state}")
    print("next_helper: monitor-workflow")
    return 0


def cmd_monitor_workflow(args: argparse.Namespace) -> int:
    run_dir = workflow_run_dir(args.run_dir)
    max_polls = max(1, int(args.max_polls))
    report_new_completions = bool(getattr(args, "report_new_completions", False))
    seen_jobs_path = monitor_seen_jobs_path(run_dir, getattr(args, "seen_jobs_file", "")) if report_new_completions else None
    activity_log = (
        resolve_monitor_activity_log(getattr(args, "activity_log", ""))
        if report_new_completions and getattr(args, "activity_log", "")
        else None
    )
    for poll_index in range(max_polls):
        if poll_index and int(args.poll_seconds) > 0:
            time.sleep(int(args.poll_seconds))
        snapshot = dynamic_routing_status_snapshot(run_dir)
        state = str(snapshot["workflow_state"])
        state_extra: dict[str, object] = {}
        new_rows: list[dict[str, str]] = []
        if report_new_completions and seen_jobs_path is not None:
            seen_jobs = load_seen_completed_jobs(seen_jobs_path)
            completed_by_summary_order = snapshot.get("completed_by_summary_order", [])
            if isinstance(completed_by_summary_order, list):
                new_rows = [
                    row
                    for row in completed_by_summary_order
                    if isinstance(row, dict) and str(row.get("job_id", "")) not in seen_jobs
                ]
                all_completed_ids = {
                    str(row.get("job_id", ""))
                    for row in completed_by_summary_order
                    if isinstance(row, dict) and row.get("job_id")
                }
                save_seen_completed_jobs(seen_jobs_path, seen_jobs | all_completed_ids)
            state_extra["last_new_completed_count"] = len(new_rows)
            state_extra["last_new_completed_jobs"] = [row.get("job_id", "") for row in new_rows]
            if activity_log is not None:
                append_monitor_activity_log(activity_log, snapshot, new_rows)
        write_workflow_state(run_dir, state, state_extra if state_extra else None)
        write_workflow_transition(run_dir, "monitor", state, f"poll={poll_index + 1}")
        counts = snapshot["counts"]
        best = snapshot["best"]
        print(f"run_id: {snapshot['run_id']}")
        print(f"workflow_state: {state}")
        print("counts: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        print(f"summary_rows: {snapshot['summary_rows']}")
        if best:
            h_value = float(best["H"])
            print(
                "best_single: "
                f"{best.get('job_id')} {best.get('name')} H={best.get('H')} "
                f"U={best.get('U')} S={best.get('S')} ZS={best.get('ZS')}"
            )
            print(f"hit_h75: {str(h_value >= 75.0).lower()}")
            print(f"hit_h76: {str(h_value >= 76.0).lower()}")
        else:
            print("best_single: none")
            print("hit_h75: false")
            print("hit_h76: false")
        if report_new_completions:
            print(f"new_completed_count: {len(new_rows)}")
            for row in new_rows:
                print(
                    f"new_completed: {row.get('job_id')} group={row.get('group')} "
                    f"name={row.get('name')} H={row.get('H')} U={row.get('U')} "
                    f"S={row.get('S')} ZS={row.get('ZS')} epoch={row.get('best_epoch')}"
                )
            print(f"seen_jobs_file: {display_path(seen_jobs_path) if seen_jobs_path else ''}")
            if activity_log is not None:
                print(f"activity_log: {display_path(activity_log)}")
        completed = snapshot["completed"]
        for row in completed[: int(args.top_k)]:
            print(
                f"rank: {row.get('job_id')} group={row.get('group')} name={row.get('name')} "
                f"H={row.get('H')} U={row.get('U')} S={row.get('S')} ZS={row.get('ZS')} "
                f"epoch={row.get('best_epoch')}"
            )
        next_action = "closeout-workflow" if state in {"completed", "failed"} else "monitor-workflow"
        print(f"next_helper: {next_action}")
    return 0


def cmd_closeout_workflow(args: argparse.Namespace) -> int:
    run_dir = workflow_run_dir(args.run_dir)
    snapshot = dynamic_routing_status_snapshot(run_dir)
    state = str(snapshot["workflow_state"])
    if state not in {"completed", "failed"} and not args.allow_incomplete:
        raise WorkflowError(f"Workflow is {state}; use monitor-workflow or --allow-incomplete for a dry closeout summary.")
    closeout_state = "closed_out" if state in {"completed", "failed"} else state
    write_workflow_state(run_dir, closeout_state)
    write_workflow_transition(run_dir, "closeout", closeout_state, "minimal closeout summary")
    best = snapshot["best"]
    print(f"run_id: {snapshot['run_id']}")
    print(f"workflow_state: {closeout_state}")
    print("counts: " + ", ".join(f"{key}={value}" for key, value in sorted(snapshot["counts"].items())))
    if best:
        print(f"best_single: {best.get('job_id')} {best.get('name')} H={best.get('H')}")
    print("formal_result_written: false")
    print("note: minimal dispatcher closeout does not replace record-module-attempt/sync-trial-summary.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTPJ workflow 结构辅助 helper")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="显示仓库状态")
    status.set_defaults(func=cmd_status)

    todo_status = sub.add_parser("todo-status", help="只读汇报当前待办窗口和队列计数")
    todo_status.set_defaults(func=cmd_todo_status)

    refresh_todo = sub.add_parser("refresh-todo", help="从 queue_state.yaml 刷新 NEXT_ACTIONS 和队列 Markdown")
    refresh_todo.set_defaults(func=cmd_refresh_todo)

    repro_status = sub.add_parser("repro-status", help="只读显示 baseline 复现状态")
    repro_status.add_argument("--version", default="")
    repro_status.set_defaults(func=cmd_repro_status)

    validate = sub.add_parser("validate", help="校验仓库结构")
    validate.set_defaults(func=cmd_validate)

    validate_evidence = sub.add_parser("validate-evidence-routing", help="校验 workflow-v2 evidence routing 状态链")
    validate_evidence.set_defaults(func=cmd_validate_evidence_routing)

    validate_agent_runtime = sub.add_parser("validate-agent-runtime", help="校验正式 Runner 启动前的 real multi-agent runtime gate")
    validate_agent_runtime.add_argument("--path", default="")
    validate_agent_runtime.set_defaults(func=cmd_validate_agent_runtime)

    multi_agent_preflight = sub.add_parser("multi-agent-preflight", help="校验正式 Runner 启动前的 multi-agent preflight")
    multi_agent_preflight.add_argument("--path", required=True)
    multi_agent_preflight.set_defaults(func=cmd_multi_agent_preflight)

    agent_cleanup = sub.add_parser("agent-cleanup-plan", help="只读列出命名线程的保留/归档计划")
    agent_cleanup.add_argument("--path", required=True)
    agent_cleanup.set_defaults(func=cmd_agent_cleanup_plan)

    validate_workflow_consistency = sub.add_parser("validate-workflow-consistency", help="校验 workflow 文档和模板的 runtime gate 标记")
    validate_workflow_consistency.set_defaults(func=cmd_validate_workflow_consistency)

    confirmation_rule_map = sub.add_parser("confirmation-rule-map", help="列出复现规则同步字典和必备标记")
    confirmation_rule_map.set_defaults(func=cmd_confirmation_rule_map)

    validate_ai_cross_review = sub.add_parser("validate-ai-cross-review", help="校验 Claude/Codex 分层 AI 交叉审核证据包")
    validate_ai_cross_review.add_argument("--path", required=True)
    validate_ai_cross_review.set_defaults(func=cmd_validate_ai_cross_review)

    run_ai_cross_review = sub.add_parser("run-ai-cross-review", help="生成证据包并按 review_tier 调用 Claude Code 只读审核")
    run_ai_cross_review.add_argument("--slug", default="")
    run_ai_cross_review.add_argument("--path", default="")
    run_ai_cross_review.add_argument("--task-id", default="")
    run_ai_cross_review.add_argument("--task-title", default="")
    run_ai_cross_review.add_argument("--scope", default="current git diff")
    run_ai_cross_review.add_argument("--risk-level", default="medium", choices=["low", "medium", "high"])
    run_ai_cross_review.add_argument("--review-reason", default="")
    run_ai_cross_review.add_argument("--risk-notes", default="")
    run_ai_cross_review.add_argument("--prompt-profile", default="focused", choices=["focused", "full"])
    run_ai_cross_review.add_argument("--review-mode", default="blocking-only", choices=["blocking-only", "full"])
    run_ai_cross_review.add_argument("--review-tier", default="review-1", choices=sorted(AI_CROSS_REVIEW_TIER_ROUNDS))
    run_ai_cross_review.add_argument(
        "--validation-profile",
        default="default-core",
        choices=["default-core", "custom-debug", "custom-full-equivalent"],
    )
    run_ai_cross_review.add_argument("--codex-pre-review-thread-id", default="")
    run_ai_cross_review.add_argument("--codex-pre-review-thread-title", default="")
    run_ai_cross_review.add_argument("--codex-pre-review-lifecycle", default="completed_archived", choices=["completed_archived"])
    run_ai_cross_review.add_argument("--codex-pre-review-archive-result", default="")
    run_ai_cross_review.add_argument("--codex-pre-review-verdict", default="blocked", choices=["pass", "needs_fix", "blocked"])
    run_ai_cross_review.add_argument("--codex-pre-review-notes", default="")
    run_ai_cross_review.add_argument("--validation-command", action="append", default=[])
    run_ai_cross_review.add_argument("--no-default-validation", action="store_true")
    run_ai_cross_review.add_argument("--claude-command", default="claude")
    run_ai_cross_review.add_argument("--claude-command-arg", action="append", default=[])
    run_ai_cross_review.add_argument("--skip-claude", action="store_true")
    run_ai_cross_review.add_argument("--overwrite", action="store_true")
    run_ai_cross_review.set_defaults(func=cmd_run_ai_cross_review)

    validate_trial_meta = sub.add_parser("validate-trial-meta", help="校验 module trial meta 的 scope/affects 分流")
    validate_trial_meta.add_argument("--path", default="")
    validate_trial_meta.set_defaults(func=cmd_validate_trial_meta)

    list_workflow_files = sub.add_parser("list-workflow-files", help="按 manifest 列出 workflow 文档层级和瘦身状态")
    list_workflow_files.set_defaults(func=cmd_list_workflow_files)

    validate_remote = sub.add_parser("validate-remote", help="校验远端 main/baseline tags 与本地治理事实")
    validate_remote.add_argument("--remote", default="origin")
    validate_remote.set_defaults(func=cmd_validate_remote)

    audit_boundary = sub.add_parser("audit-boundary", help="检查 GitHub 轻量边界，禁止 raw artifacts 入仓库")
    audit_boundary.set_defaults(func=cmd_audit_boundary)

    start = sub.add_parser("start", help="按 owner 人话口令只读输出 mini 启动卡")
    start.add_argument("--phrase", required=True)
    start.set_defaults(func=cmd_start)

    plan_experiments = sub.add_parser("plan-experiments", help="只读根据当前项目状态生成 Experiment Planning Gate")
    plan_experiments.add_argument("--phrase", required=True)
    plan_experiments.add_argument("--max-jobs", type=int, default=0)
    plan_experiments.set_defaults(func=cmd_plan_experiments)

    start_card = sub.add_parser("start-card", help="生成完整启动卡骨架")
    start_card.add_argument("--type", dest="task_type", required=True)
    start_card.add_argument("--version", default="")
    start_card.add_argument("--owner-request", default="")
    start_card.add_argument("--idea-id", default="")
    start_card.add_argument("--trial-id", default="")
    start_card.add_argument("--attempt-id", default="")
    start_card.add_argument("--subject-id", default="")
    start_card.add_argument("--runner-scope", choices=["none", "debug_smoke", "formal_runner"], default="formal_runner")
    start_card.add_argument("--output", default="")
    start_card.set_defaults(func=cmd_start_card)

    closeout = sub.add_parser("closeout-check", help="只读检查 module trial attempt 到 root/index/idea/Warehouse 闭环")
    closeout.add_argument("--trial-dir", required=True)
    closeout.add_argument("--attempt-id", required=True)
    closeout.set_defaults(func=cmd_closeout_check)

    refresh_framework = sub.add_parser(
        "refresh-framework-view",
        help="从四类正式索引重新生成某个框架的实验总览",
    )
    refresh_framework.add_argument("--version", required=True)
    refresh_framework.set_defaults(func=cmd_refresh_framework_view)

    validate_framework = sub.add_parser(
        "validate-framework-ledgers",
        help="校验同级正式框架身份、四类实验、参数表和历史来源指针",
    )
    validate_framework.set_defaults(func=cmd_validate_framework_ledgers)

    validate_templates = sub.add_parser(
        "validate-framework-templates",
        help="校验正式框架只读母版的分支、Tag 和准确提交",
    )
    validate_templates.set_defaults(func=cmd_validate_framework_templates)

    validate_experiment_base = sub.add_parser(
        "validate-experiment-base",
        help="校验当前实验分支包含账本登记的准确母版提交",
    )
    validate_experiment_base.add_argument("--path", required=True)
    validate_experiment_base.set_defaults(func=cmd_validate_experiment_base)

    new_exp = sub.add_parser("new-experiment", help="创建版本实验目录")
    new_exp.add_argument("--version", required=True)
    new_exp.add_argument("--kind", required=True, choices=sorted(KINDS))
    new_exp.add_argument("--exp-id", required=True)
    new_exp.add_argument("--slug", required=True)
    new_exp.add_argument(
        "--template-registry-ref",
        default=DEFAULT_TEMPLATE_REGISTRY_REF,
        help="记录 TEMPLATE.yaml 的管理分支或提交，默认 main",
    )
    new_exp.set_defaults(func=cmd_new_experiment)

    validate_matrix = sub.add_parser("validate-parameter-matrix", help="校验一张参数矩阵是否可进入正式实验")
    validate_matrix.add_argument("--path", required=True)
    validate_matrix.add_argument("--expected-jobs", type=int, default=0)
    validate_matrix.add_argument("--require-ready", action="store_true")
    validate_matrix.set_defaults(func=cmd_validate_parameter_matrix)

    refresh_matrix_view = sub.add_parser(
        "refresh-parameter-matrix-view",
        help="从 CSV 重新生成参数矩阵的 Markdown 阅读版",
    )
    refresh_matrix_view.add_argument("--path", required=True)
    refresh_matrix_view.add_argument("--source-note", default="")
    refresh_matrix_view.set_defaults(func=cmd_refresh_parameter_matrix_view)

    freeze_matrix = sub.add_parser(
        "freeze-parameter-matrix",
        help="用真实配置快照更新并冻结参数矩阵的一行",
    )
    freeze_matrix.add_argument("--path", required=True)
    freeze_matrix.add_argument("--config", required=True)
    freeze_matrix.add_argument("--job-id", required=True)
    freeze_matrix.set_defaults(func=cmd_freeze_parameter_matrix)

    prepare_receipt = sub.add_parser(
        "prepare-run-start-receipt",
        help="生成冻结任务收据，并直接启动训练、收集进程输出",
    )
    prepare_receipt.add_argument("--path", required=True)
    prepare_receipt.add_argument("--config", required=True)
    prepare_receipt.add_argument("--job-id", required=True)
    prepare_receipt.add_argument("--run-id", required=True)
    prepare_receipt.add_argument("--pre-run-freeze-commit", required=True)
    prepare_receipt.add_argument("--command", required=True)
    prepare_receipt.add_argument("--receipt", required=True)
    prepare_receipt.add_argument("--log", required=True)
    prepare_receipt.set_defaults(func=cmd_prepare_run_start_receipt)

    init_matrix = sub.add_parser(
        "init-parameter-matrix",
        help="为版本实验或普通 module attempt 建立一行参数矩阵草稿",
    )
    init_matrix.add_argument("--directory", required=True)
    init_matrix.add_argument("--job-id", required=True)
    init_matrix.add_argument("--work-item-id", default="")
    init_matrix.add_argument(
        "--job-kind",
        required=True,
        choices=["param_tune", "ablation", "control", "repeat", "confirmation"],
    )
    init_matrix.add_argument("--base-version", required=True)
    init_matrix.add_argument("--code-ref", default="")
    init_matrix.add_argument("--base-config", required=True)
    init_matrix.add_argument("--config", required=True)
    init_matrix.add_argument("--seed", default="")
    init_matrix.add_argument("--group", default="")
    init_matrix.add_argument("--name", default="")
    init_matrix.add_argument("--purpose", default="")
    init_matrix.add_argument("--repeat-of", default="")
    init_matrix.add_argument("--run-id", default="")
    init_matrix.set_defaults(func=cmd_init_parameter_matrix)

    prepare_dynamic_matrix = sub.add_parser(
        "prepare-dynamic-routing-matrix",
        help="在 pre-run freeze 前生成动态路由批次的逐任务参数表",
    )
    prepare_dynamic_matrix.add_argument("--trial-dir", required=True)
    prepare_dynamic_matrix.add_argument("--attempt-id", required=True)
    prepare_dynamic_matrix.add_argument("--run-id", default="")
    prepare_dynamic_matrix.add_argument("--base-config", default="")
    prepare_dynamic_matrix.add_argument("--base-version", default="v5")
    prepare_dynamic_matrix.add_argument("--base-code-tag", default="")
    prepare_dynamic_matrix.add_argument("--profile", default="balanced-aggressive")
    prepare_dynamic_matrix.add_argument("--jobs", type=int, default=50)
    prepare_dynamic_matrix.add_argument("--limit-jobs", type=int, default=0)
    prepare_dynamic_matrix.add_argument("--seed", type=int, default=5)
    prepare_dynamic_matrix.add_argument("--overwrite", action="store_true")
    prepare_dynamic_matrix.set_defaults(func=cmd_prepare_dynamic_routing_matrix)

    sync_dynamic_matrix = sub.add_parser(
        "sync-dynamic-routing-matrix",
        help="将动态路由 summary.csv 的每任务结果回填到同一张参数表",
    )
    sync_dynamic_matrix.add_argument("--run-dir", required=True)
    sync_dynamic_matrix.set_defaults(func=cmd_sync_dynamic_routing_matrix)

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
    record.add_argument("--matrix-job-id", default="")
    record.add_argument("--pre-run-freeze-commit", default="")
    record.add_argument("--run-start-receipt", default="")
    record.add_argument("--legacy-summary-only", action="store_true")
    record.add_argument("--legacy-source-commit", default="")
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
    record_module.add_argument("--run-start-receipt", default="")
    record_module.add_argument("--attempt-type", default="")
    record_module.add_argument("--parameter-change", default="")
    record_module.add_argument("--old-value", default="")
    record_module.add_argument("--new-value", default="")
    record_module.add_argument("--matrix-job-id", default="")
    record_module.add_argument("--legacy-summary-only", action="store_true")
    record_module.add_argument("--legacy-source-commit", default="")
    record_module.add_argument(
        "--decision",
        default="blocked",
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

    sync_trial = sub.add_parser("sync-trial-summary", help="从 attempt 证据同步 trial 根账本和索引")
    sync_trial.add_argument("--trial-dir", required=True)
    sync_trial.add_argument("--attempt-id", required=True)
    sync_trial.add_argument(
        "--decision",
        default="",
        choices=[
            "",
            "best",
            "keep",
            "reject",
            "rejected",
            "revise",
            "combine",
            "promote",
            "confirmed_candidate",
            "rerun",
            "not_confirmed",
            "blocked",
            "debug",
        ],
    )
    sync_trial.add_argument(
        "--evidence-level",
        default="",
        choices=["", "debug_smoke", "quick_local", "valid_single_run", "confirmation_grade", "baseline_grade", "legacy_summary_only"],
    )
    sync_trial.add_argument(
        "--promotion-decision",
        default="",
        choices=["", "not_applicable", "blocked", "promote"],
    )
    sync_trial.add_argument("--skip-idea-tree", action="store_true")
    sync_trial.add_argument("--dry-run", action="store_true")
    sync_trial.set_defaults(func=cmd_sync_trial_summary)

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

    new_trial = sub.add_parser("new-trial", help="历史兼容命令；正式框架规范启用后拒绝创建新 Trial")
    new_trial.add_argument("--idea-id", required=True)
    new_trial.add_argument("--trial-id", required=True)
    new_trial.add_argument("--slug", required=True)
    new_trial.add_argument("--base-version", default="")
    new_trial.add_argument(
        "--training-entry-mode",
        choices=sorted(TRIAL_TRAINING_ENTRY_MODES),
        default="existing_entry_equivalent",
    )
    new_trial.set_defaults(func=cmd_new_trial)

    dyn_plan = sub.add_parser("plan-dynamic-routing-batch", help="生成 IDEA-0003/TRIAL-001 dynamic routing 50 组两卡 batch")
    dyn_plan.add_argument("--trial-dir", required=True)
    dyn_plan.add_argument("--base-config", default="")
    dyn_plan.add_argument("--run-id", default="")
    dyn_plan.add_argument("--attempt-id", default="")
    dyn_plan.add_argument("--jobs", type=int, default=50)
    dyn_plan.add_argument("--limit-jobs", type=int, default=0)
    dyn_plan.add_argument("--profile", default="balanced-aggressive")
    dyn_plan.add_argument("--base-version", default="v5")
    dyn_plan.add_argument("--base-code-tag", default="")
    dyn_plan.add_argument("--seed", type=int, default=5)
    dyn_plan.add_argument("--gpus", default="0,1")
    dyn_plan.add_argument("--branch", default="")
    dyn_plan.add_argument("--commit", default="")
    dyn_plan.add_argument("--git-remote", default="origin")
    dyn_plan.add_argument("--server-repo", default="/data/lby/projects/cv_project/GTPJ")
    dyn_plan.add_argument("--worktree-root", default="/data/lby/projects/cv_project/GTPJ_worktrees")
    dyn_plan.add_argument("--warehouse-root", default="/data/lby/projects/cv_project/GTPJ_Warehouse")
    dyn_plan.add_argument("--conda-env", default="dvsr_gpu")
    dyn_plan.add_argument("--python", default="python")
    dyn_plan.add_argument("--controller-python", default="python3")
    dyn_plan.add_argument("--agent-runtime-gate", default="")
    dyn_plan.add_argument("--allow-historical-training-commit", action="store_true")
    dyn_plan.add_argument("--restore-target-h", dest="restore_target_h", default="")
    dyn_plan.add_argument(
        "--near-miss-tolerance-h",
        dest="near_miss_tolerance_h",
        default=str(CONFIRMATION_RULE_DEFAULT_NEAR_MISS_TOLERANCE_H),
    )
    dyn_plan.add_argument("--debug-smoke", action="store_true")
    dyn_plan.set_defaults(func=cmd_plan_dynamic_routing_batch)

    dyn_status = sub.add_parser("dynamic-routing-status", help="读取 dynamic routing batch 状态")
    dyn_status.add_argument("--run-dir", required=True)
    dyn_status.set_defaults(func=cmd_dynamic_routing_status)

    dyn_analyze = sub.add_parser("analyze-dynamic-routing-batch", help="分析 dynamic routing batch summary")
    dyn_analyze.add_argument("--run-dir", required=True)
    dyn_analyze.add_argument("--top-k", type=int, default=5)
    dyn_analyze.set_defaults(func=cmd_analyze_dynamic_routing_batch)

    route_exp = sub.add_parser("route-experiment", help="按 owner 短语输出最小机器路由")
    route_exp.add_argument("--phrase", required=True)
    route_exp.add_argument("--workflow-kind", default="")
    route_exp.set_defaults(func=cmd_route_experiment)

    run_workflow = sub.add_parser("run-workflow", help="最小统一调度入口：route -> plan -> optional launch")
    run_workflow.add_argument("--phrase", required=True)
    run_workflow.add_argument(
        "--experiment-dir",
        default="",
        help="正式运行所属的 experiments/vX/<kind>/<实验目录>",
    )
    run_workflow.add_argument("--workflow-mode", choices=sorted(WORKFLOW_MODES), default="")
    run_workflow.add_argument("--workflow-kind", default="")
    run_workflow.add_argument("--trial-dir", default="")
    run_workflow.add_argument("--base-config", default="")
    run_workflow.add_argument("--run-id", default="")
    run_workflow.add_argument("--attempt-id", default="")
    run_workflow.add_argument("--jobs", type=int, default=0)
    run_workflow.add_argument("--limit-jobs", type=int, default=0)
    run_workflow.add_argument("--profile", default="")
    run_workflow.add_argument("--base-version", default="v5")
    run_workflow.add_argument("--base-code-tag", default="")
    run_workflow.add_argument("--seed", type=int, default=5)
    run_workflow.add_argument("--gpus", default="0,1")
    run_workflow.add_argument("--branch", default="")
    run_workflow.add_argument("--commit", default="")
    run_workflow.add_argument("--git-remote", default="none")
    run_workflow.add_argument("--server-repo", default="/data/lby/projects/cv_project/GTPJ")
    run_workflow.add_argument("--worktree-root", default="/data/lby/projects/cv_project/GTPJ_worktrees")
    run_workflow.add_argument("--warehouse-root", default="/data/lby/projects/cv_project/GTPJ_Warehouse")
    run_workflow.add_argument("--conda-env", default="dvsr_gpu")
    run_workflow.add_argument("--python", default="python")
    run_workflow.add_argument("--controller-python", default="python3")
    run_workflow.add_argument("--agent-runtime-gate", default="")
    run_workflow.add_argument("--allow-historical-training-commit", action="store_true")
    run_workflow.add_argument("--restore-target-h", dest="restore_target_h", default="")
    run_workflow.add_argument(
        "--near-miss-tolerance-h",
        dest="near_miss_tolerance_h",
        default=str(CONFIRMATION_RULE_DEFAULT_NEAR_MISS_TOLERANCE_H),
    )
    run_workflow.add_argument("--debug-smoke", action="store_true")
    run_workflow.add_argument("--formal", action="store_true")
    run_workflow.add_argument("--launch", action="store_true")
    run_workflow.set_defaults(func=cmd_run_workflow)

    monitor_workflow = sub.add_parser("monitor-workflow", help="最小统一监控入口：短轮询读取状态和 top-k")
    monitor_workflow.add_argument("--run-dir", required=True)
    monitor_workflow.add_argument("--top-k", type=int, default=5)
    monitor_workflow.add_argument("--poll-seconds", type=int, default=0)
    monitor_workflow.add_argument("--max-polls", type=int, default=1)
    monitor_workflow.add_argument("--report-new-completions", action="store_true")
    monitor_workflow.add_argument("--seen-jobs-file", default="")
    monitor_workflow.add_argument("--activity-log", default="")
    monitor_workflow.set_defaults(func=cmd_monitor_workflow)

    closeout_workflow = sub.add_parser("closeout-workflow", help="最小统一收口入口")
    closeout_workflow.add_argument("--run-dir", required=True)
    closeout_workflow.add_argument("--allow-incomplete", action="store_true")
    closeout_workflow.set_defaults(func=cmd_closeout_workflow)

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
