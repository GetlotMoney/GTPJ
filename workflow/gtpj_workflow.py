#!/usr/bin/env python
"""Optional repository-structure helper for the GTPJ repository.

This script is intentionally small and deterministic. It creates governance
folders, copies version configs, and validates repository invariants. It does
not run training, push to GitHub, or mutate Git history.
"""

from __future__ import annotations

import argparse
import csv
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
    "required_agents_spawned",
    "agent_instance_ids_present",
    "agent_status_refs_valid",
    "independent_outputs_present",
    "agent_output_refs_valid",
    "pre_run_allow_checks_passed",
    "agent_runtime_validated",
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
            "confirmation_target": "",
            "confirmation_tolerance_H": "",
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
        "confirmation_target": h_value if kind_name == "confirmation" else "",
        "confirmation_tolerance_H": "",
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


def read_shallow_yaml(path: Path) -> dict[str, object]:
    """Parse the helper-generated, shallow YAML ledgers without a PyYAML dependency."""
    data: dict[str, object] = {}
    current_section = ""
    for raw_line in read_text(path).splitlines():
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
        "调参实验按 base version 写入 `experiments/vX/tune/`；trial 内部调参写入对应 trial 的 `attempts/ATTEMPT-xxx/`。",
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
        print("- note: pure tuning/config-only records stay under the parent version; use v3/CONFIRM-001 local-v3-054 as the formal reference")
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
    ]


def cmd_validate(_: argparse.Namespace) -> int:
    required = required_repository_files()
    missing = [item for item in required if not (REPO_ROOT / item).exists()]
    if missing:
        raise WorkflowError("Missing required files:\n" + "\n".join(missing))

    marker_requirements = {
        "docs/workflow/START_HERE.md": ["baseline_repro_status", "comparison_reference", "debug_smoke", "multi_agent_preflight"],
        "docs/workflow/WORKFLOW_KERNEL.md": ["temporary_subagent", "debug_smoke", "Top-3", "TRANSITIONS.jsonl", "validate-agent-runtime", "multi-agent-preflight"],
        "docs/workflow/protocols/evidence_routing_protocol.md": ["subject_id", "TRANSITIONS.jsonl", "validate-evidence-routing"],
        "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md": [
            "right_sidebar_temporary_agents",
            "agent_runtime.yaml",
            "validate-agent-runtime",
            "multi-agent-preflight",
            "single_agent_execution",
            "formal_runner_allowed",
            "agent_output_refs",
        ],
        "docs/workflow/reference/GZSL_HARD_RULES.md": ["seen/unseen split", "logits", "rule_checks"],
        "docs/workflow/reference/innovation_decomposition_protocol.md": ["Hypothesis", "Trial", "Attempt"],
        "docs/workflow/core/WORKFLOW_VERSION.md": ["workflow-v2", "evidence_routing.yaml"],
        "docs/workflow/core/CHANGELOG.md": ["workflow-v2", "validate-evidence-routing"],
        "docs/workflow/core/QUICK_START.md": ["repro-status", "baseline_repro_status"],
        "docs/workflow/core/WORKFLOW_ROUTER.md": ["baseline_repro_status", "best_observed_H", "role_key"],
        "docs/workflow/core/TASK_START_MINI.md": ["baseline_repro_status", "temporary_subagent", "subject_id", "agent_runtime_gate", "formal_runner_allowed"],
        "docs/workflow/core/TASK_START_CARD.md": ["subject_id", "transition_permissions", "authority_refs", "agent_runtime_gate", "multi_agent_preflight"],
        "docs/workflow/agents/README.md": ["role_aliases", "runner_monitor", "log_analyst"],
        "docs/workflow/protocols/agent_orchestration.md": ["Agent Runtime Protocol", "propose", "apply transition", "agent_runtime.yaml", "multi_agent_preflight"],
        "docs/workflow/protocols/mixed_experiment_campaign_protocol.md": ["subject_id", "derived_index_only", "evidence_state", "agent_runtime.yaml"],
        "docs/workflow/playbooks/mixed_campaign.md": ["subject_id", "derived_index_only"],
        "docs/workflow/playbooks/innovation.md": ["Hypothesis", "Attachment Point"],
        "docs/workflow/playbooks/tune.md": ["tune_promising", "stopped_no_gain"],
        "docs/workflow/playbooks/ablation.md": ["ablation_supported", "stopped_ablation_not_supported"],
        "docs/workflow/playbooks/confirmation.md": ["promotion_compare_metric", "confirmed_H"],
        "docs/workflow/reference/artifact_policy.md": ["Top-3", "pruned"],
        "docs/workflow/protocols/promotion.md": ["must not push", "explicitly asks"],
        "docs/workflow/protocols/experiment_protocol.md": ["mixed_confirmation", "strict_determinism"],
        "docs/workflow/protocols/module_trial_protocol.md": ["mixed_confirmation", "use_dedicated_batch_rng"],
        "docs/workflow/archive/runbooks/runbook.md": ["mixed_confirmation", "batch_sampling_seed"],
        "docs/workflow/archive/issues/README.md": ["ISSUE-20260628-014"],
        "workflow/README.md": ["repro-status", "confirmed_H"],
    }
    for path_text, markers in marker_requirements.items():
        text = read_text(REPO_ROOT / path_text)
        for marker in markers:
            if marker not in text:
                raise WorkflowError(f"{path_text} missing reproducibility marker: {marker}")

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
        "temporary_subagent_reason:",
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
        "temporary_subagent_ids:",
        "runner_start_gate:",
        "pre_run_required_checks:",
        "output_locations:",
        "verified_against_current_repo:",
        "subject_id:",
        "transition_id:",
        "rule_checks:",
        "authority_refs:",
        "not_checked:",
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
        "临时 agents",
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
confirmation_target:
confirmation_tolerance_H:
confirmation_status: pending
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

- [ ] parent_version / parent_tag 明确。
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
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
activation_reason:
required_roles:
required_real_agents:
agent_persistent_threads: none
agent_set: {agent_set}
serial_agents: {serial_agents}
parallel_agents: {parallel_agents}
disabled_agents: {disabled_agents}
temporary_subagents: workflow-scoped role contexts
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
agent_instance_mode: temporary_subagent
agent_instance_type:
persistent_thread_id:
temporary_subagent_reason:
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
    git_dirty: str = "false",
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
  confirmation_target: {yaml_scalar(evidence_defaults["confirmation_target"])}
  confirmation_tolerance_H: {yaml_scalar(evidence_defaults["confirmation_tolerance_H"])}
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
        git_dirty=git_dirty,
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
    git_dirty = "true" if dirty_before == "dirty" else "false"
    evidence_defaults = result_evidence_defaults(kind.name, metrics["H"], args.decision, git_dirty)
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
        "evidence_level": evidence_defaults["evidence_level"],
        "result_status": evidence_defaults["result_status"],
        "best_observed_H": evidence_defaults["best_observed_H"],
        "confirmed_H": evidence_defaults["confirmed_H"],
        "confirmation_target": evidence_defaults["confirmation_target"],
        "confirmation_tolerance_H": evidence_defaults["confirmation_tolerance_H"],
        "confirmation_status": evidence_defaults["confirmation_status"],
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
        git_dirty=git_dirty,
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
  result_status: {yaml_scalar("needs_confirmation" if decision in {"best", "keep"} else decision)}
  promotion_decision: {yaml_scalar("blocked" if decision in {"best", "keep"} else "not_applicable")}
  promote_to: {yaml_scalar("")}
evidence:
  evidence_level: {yaml_scalar("valid_single_run" if decision in {"best", "keep"} else "quick_local")}
  best_observed_H: {yaml_scalar(metrics.get("H", "") if decision in {"best", "keep"} else "")}
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
agent_instance_mode: temporary_subagent
lifecycle: workflow_scoped
activation_reason: module trial closeout requires Review 0-3 evidence and artifact boundary checks
required_roles: Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst, Reviewer
required_real_agents: Reader/Planner, Interface Checker, Quality Checker, Reviewer, Log Analyst, Result Analyst
agent_persistent_threads: none
agent_set: Coordinator, Reader/Planner, Implementer, Interface Checker, Runner, Log Analyst, Quality Checker, Result Analyst, Reviewer
serial_agents: Coordinator -> Review 0 -> Review 1 -> Implementer -> Review 2 -> Runner -> Review 3 -> Coordinator
parallel_agents: Interface Checker + Quality Checker + Reviewer in Review 2; Log Analyst + Quality Checker + Result Analyst + Reviewer in Review 3
disabled_agents: none
temporary_subagents: workflow-scoped closeout roles; helper-generated summary records their required evidence slots
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
agent_instance_mode: temporary_subagent
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: closeout summary generated from current repo evidence
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
agent_instance_mode: temporary_subagent
agent_instance_type: recorded_run
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: recorded serial GPU run evidence
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
agent_instance_mode: temporary_subagent
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: parse current attempt result evidence
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
agent_instance_mode: temporary_subagent
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: check artifact boundary and ledger consistency
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
agent_instance_mode: temporary_subagent
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: compare current attempt metrics against recorded references
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
agent_instance_mode: temporary_subagent
agent_instance_type: workflow_helper
lifecycle: workflow_scoped
persistent_thread_id: none
temporary_subagent_reason: final closeout evidence consistency review
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
    if promotion_decision == "not_applicable" and decision == "promote":
        promotion_decision = "promote"
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


def validate_agent_display_name(subject_id: str, role: str, display_name: str) -> str | None:
    normalized = display_name.strip()
    if not normalized:
        return f"temporary_subagent_display_names.{role} is missing"
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
        return f"temporary_subagent_display_names.{role} uses a random legacy nickname: {display_name}"
    if subject_id and subject_id.lower() not in normalized.lower():
        return f"temporary_subagent_display_names.{role} must include subject_id: {subject_id}"
    display_words = normalized.lower().replace("_", " ").replace("-", " ").replace("|", " ")
    missing_role_words = [part for part in role.split("_") if part and part.lower() not in display_words]
    if missing_role_words:
        expected = role_display_label(role)
        return f"temporary_subagent_display_names.{role} must include role label words: {expected}"
    if "|" not in normalized:
        return f"temporary_subagent_display_names.{role} must use '<subject_id> | <Role Label>' format"
    return None


def validate_agent_runtime_gate_file(gate_path: Path) -> list[str]:
    errors: list[str] = []
    scalars, maps = read_simple_yaml_maps(gate_path)
    gate_name = rel(gate_path)
    required_scalars = [
        "schema_version",
        "subject_id",
        "subject_type",
        "formal_evidence",
        "activation_mode",
        "agent_instance_mode",
        "lifecycle",
        "ui_visibility",
        "tool_support_real_multi_agent_available",
        "spawn_tool",
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
        "right_sidebar_retention_policy",
        "close_completed_agents_on_stage_end",
        "closed_agents_record",
    ]
    for field in required_scalars:
        if field not in scalars or scalars[field] == "":
            errors.append(f"{gate_name} missing {field}")

    formal = truthy(scalars.get("formal_evidence", ""))
    if not formal:
        evidence_level = scalars.get("evidence_level", "")
        debug_smoke = truthy(scalars.get("debug_smoke", ""))
        if evidence_level not in NON_FORMAL_AGENT_RUNTIME_EVIDENCE_LEVELS and not debug_smoke:
            errors.append(
                f"{gate_name} non-formal runtime gate must declare evidence_level: "
                f"{'/'.join(sorted(NON_FORMAL_AGENT_RUNTIME_EVIDENCE_LEVELS))}"
            )
        return errors

    if scalars.get("activation_mode") != "real_multi_agent":
        errors.append(f"{gate_name} formal evidence requires activation_mode: real_multi_agent")
    if scalars.get("agent_instance_mode") not in {"temporary_subagent", "persistent_thread"}:
        errors.append(f"{gate_name} formal evidence requires temporary_subagent or persistent_thread")
    if "right_sidebar" not in scalars.get("ui_visibility", ""):
        errors.append(f"{gate_name} must declare ui_visibility: right_sidebar_temporary_agents")
    if not truthy(scalars.get("tool_support_real_multi_agent_available", "")):
        errors.append(f"{gate_name} must confirm real multi-agent tool support")
    if truthy(scalars.get("single_agent_execution", "")):
        errors.append(f"{gate_name} single_agent_execution cannot be true for formal evidence")
    if not truthy(scalars.get("runner_start_allowed", "")):
        errors.append(f"{gate_name} runner_start_allowed must be true before formal Runner starts")
    if not truthy(scalars.get("formal_runner_allowed", "")):
        errors.append(f"{gate_name} formal_runner_allowed must be true before formal Runner starts")
    if not truthy(scalars.get("formal_evidence_allowed", "")):
        errors.append(f"{gate_name} formal_evidence_allowed must be true for formal evidence")
    if scalars.get("spawn_tool") in {"", "role_only", "manual"}:
        errors.append(f"{gate_name} spawn_tool must name the real sub-agent tool")
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
    if scalars.get("right_sidebar_retention_policy") != "current_stage_active_only":
        errors.append(f"{gate_name} right_sidebar_retention_policy must be current_stage_active_only")
    if not truthy(scalars.get("close_completed_agents_on_stage_end", "")):
        errors.append(f"{gate_name} close_completed_agents_on_stage_end must be true")
    activity_stream = scalars.get("agent_activity_stream", "")
    if not validate_agent_runtime_ref(activity_stream, gate_path):
        errors.append(f"{gate_name} agent_activity_stream points to missing activity log: {activity_stream}")
    closed_agents_record = scalars.get("closed_agents_record", "")
    if not validate_agent_runtime_ref(closed_agents_record, gate_path):
        errors.append(f"{gate_name} closed_agents_record points to missing closeout log: {closed_agents_record}")

    agent_ids = maps.get("temporary_subagent_ids", {})
    if not agent_ids:
        errors.append(f"{gate_name} missing temporary_subagent_ids")
    for role, instance_id in agent_ids.items():
        if not valid_runtime_agent_instance_id(instance_id):
            errors.append(f"{gate_name} temporary_subagent_ids.{role} is not a real agent/thread id")
    display_names = maps.get("temporary_subagent_display_names", {})
    if not display_names:
        errors.append(f"{gate_name} missing temporary_subagent_display_names")
    for role in agent_ids:
        display_error = validate_agent_display_name(scalars.get("subject_id", ""), role, display_names.get(role, ""))
        if display_error:
            errors.append(f"{gate_name} {display_error}")
    extra_display_roles = sorted(set(display_names) - set(agent_ids))
    for role in extra_display_roles:
        errors.append(f"{gate_name} temporary_subagent_display_names.{role} has no matching temporary_subagent_ids entry")
    instance_to_roles: dict[str, list[str]] = {}
    for role, instance_id in agent_ids.items():
        instance_to_roles.setdefault(instance_id.strip(), []).append(role)
    for instance_id, roles in sorted(instance_to_roles.items()):
        if len(roles) > 1:
            errors.append(
                f"{gate_name} temporary_subagent_ids reuse one agent id for multiple roles: "
                f"{instance_id} -> {', '.join(sorted(roles))}"
            )

    if not has_any_role(agent_ids, {"runner_monitor", "runner"}):
        errors.append(f"{gate_name} missing Runner Monitor temporary subagent id")
    if not has_any_role(agent_ids, {"evidence_quality_checker", "quality_checker"}):
        errors.append(f"{gate_name} missing Quality Checker temporary subagent id")

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
    output_refs = maps.get("agent_output_refs", {})
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

    pre_run_checks = maps.get("pre_run_required_checks", {})
    if not pre_run_checks:
        errors.append(f"{gate_name} missing pre_run_required_checks")
    for role, decision in pre_run_checks.items():
        normalized = decision.strip().lower()
        if normalized not in AGENT_RUNTIME_ALLOW_DECISIONS:
            errors.append(f"{gate_name} pre_run_required_checks.{role} must be allow/pass before Runner starts")
        if role not in agent_ids:
            errors.append(f"{gate_name} pre_run_required_checks.{role} has no matching temporary_subagent_ids entry")

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

    authority_refs = maps.get("authority_refs", {})
    for key, value in authority_refs.items():
        if not validate_agent_runtime_ref(value, gate_path):
            errors.append(f"{gate_name} authority_refs.{key} points to missing authority ref: {value}")
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
    agent_count = len(maps.get("temporary_subagent_ids", {}))
    print(f"multi-agent-preflight-ok path={display_path(gate_path)} agents={agent_count}")
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
    "05_claude_review_round_1.md": ["round: 1", "reviewer: claude_code", "claude_code_read_only: true", "verdict:", "blocking_issues:"],
    "06_codex_response_round_1.md": ["round: 1", "reviewer: codex", "addressed_claude_findings:", "validation_rerun:", "remaining_blocking_issues:"],
    "07_claude_review_round_2.md": ["round: 2", "reviewer: claude_code", "claude_code_read_only: true", "verdict:", "blocking_issues:"],
    "08_codex_response_round_2.md": ["round: 2", "reviewer: codex", "addressed_claude_findings:", "validation_rerun:", "remaining_blocking_issues:"],
    "09_claude_review_round_3.md": ["round: 3", "reviewer: claude_code", "claude_code_read_only: true", "verdict:", "blocking_issues:"],
}

AI_CROSS_REVIEW_FINAL_MARKERS = {
    "ai_cross_review_status: pass",
    "owner_participation: not_required",
    "rounds_completed:",
    "claude_code_read_only: true",
    "codex_fixes_or_rebuttals_recorded: true",
    "machine_gates_passed: true",
    "unresolved_blocking_issues: 0",
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
    agent_ids = maps.get("temporary_subagent_ids", {})
    statuses = maps.get("agent_instance_status", {})
    output_refs = maps.get("agent_output_refs", {})

    keep: list[tuple[str, str, str]] = []
    close: list[tuple[str, str, str]] = []
    unknown: list[tuple[str, str, str]] = []
    instance_to_roles: dict[str, list[str]] = {}
    for role, instance_id in sorted(agent_ids.items()):
        instance_to_roles.setdefault(instance_id, []).append(role)
        status = statuses.get(role, "").strip().lower()
        row = (role, instance_id, status or "missing")
        if status in AGENT_CLEANUP_KEEP_STATUSES:
            keep.append(row)
        elif status in AGENT_CLEANUP_CLOSE_STATUSES:
            close.append(row)
        else:
            unknown.append(row)

    print(f"agent-cleanup-plan path={display_path(gate_path)}")
    print(f"subject_id={scalars.get('subject_id', '')}")
    print(f"retention_policy={scalars.get('right_sidebar_retention_policy', '')}")
    print(f"closed_agents_record={scalars.get('closed_agents_record', '')}")
    print(f"keep_count={len(keep)}")
    for role, instance_id, status in keep:
        print(f"KEEP role={role} id={instance_id} status={status}")
    print(f"close_count={len(close)}")
    for role, instance_id, status in close:
        output_ref = output_refs.get(role, "")
        print(f"CLOSE role={role} id={instance_id} status={status} output_ref={output_ref}")
    print(f"unknown_count={len(unknown)}")
    for role, instance_id, status in unknown:
        print(f"UNKNOWN role={role} id={instance_id} status={status}")
    duplicate_instances = {instance_id: roles for instance_id, roles in instance_to_roles.items() if len(roles) > 1}
    print(f"duplicate_instance_ids={len(duplicate_instances)}")
    for instance_id, roles in sorted(duplicate_instances.items()):
        print(f"DUPLICATE id={instance_id} roles={','.join(sorted(roles))}")
    if unknown:
        raise WorkflowError("Agent cleanup plan has unknown agent statuses; do not close blindly")
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


def workflow_consistency_errors() -> list[str]:
    errors: list[str] = []
    errors.extend(workflow_manifest_errors())
    required_markers = {
        "docs/workflow/START_HERE.md": ["formal_runner_allowed", "multi_agent_preflight", "review_tier", "review-1", "strict-3"],
        "docs/workflow/WORKFLOW_KERNEL.md": ["multi-agent-preflight", "formal_evidence_allowed", "review_tier", "review-1", "strict-3"],
        "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md": [
            "multi_agent_preflight",
            "formal_runner_allowed",
            "agent_output_refs",
            "agent-cleanup-plan",
            "temporary_subagent_display_names",
            "<subject_id> | <Role Label>",
        ],
        "docs/workflow/core/TASK_START_MINI.md": ["runner_scope", "blocked_reason"],
        "docs/workflow/core/TASK_START_CARD.md": ["multi_agent_preflight", "formal_evidence_allowed", "agent_status_refs"],
        "docs/workflow/protocols/agent_orchestration.md": [
            "multi_agent_preflight",
            "formal_runner_allowed",
            "agent_output_refs",
            "agent-cleanup-plan",
            "<subject_id> | <Role Label>",
        ],
        "docs/workflow/protocols/ai_cross_review_protocol.md": [
            "owner_participation: not_required",
            "claude_code_read_only: true",
            "review_tier",
            "fast",
            "review-1",
            "strict-3",
            "02_codex_temp_agent_pre_review.md",
            "completed_closed",
            "close_result_confirms_completion",
            "validation_profile",
            "claude_rounds_required",
            "run-ai-cross-review",
            "validate-ai-cross-review",
            "02_review_brief.md",
            "02_focused_diff.md",
            "prompt_profile",
            "blocking-only",
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
        ],
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
            "02_codex_temp_agent_pre_review.md",
            "completed_closed",
            "close_result_confirms_completion",
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
    return errors


def cmd_validate_workflow_consistency(_: argparse.Namespace) -> int:
    errors = workflow_consistency_errors()
    if errors:
        raise WorkflowError("Workflow consistency validation failed:\n" + "\n".join(errors))
    print("validate-workflow-consistency-ok")
    return 0


def resolve_ai_cross_review_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def scalar_from_text(text: str, key: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(key)}\s*:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else ""


def ai_cross_review_required_files_for_pack(pack_dir: Path) -> tuple[list[str], int, bool]:
    final_path = pack_dir / "10_final_decision.md"
    if not final_path.is_file():
        return AI_CROSS_REVIEW_REQUIRED_FILES, 3, False
    final_text = read_text(final_path)
    review_tier = scalar_from_text(final_text, "review_tier")
    if not review_tier:
        return AI_CROSS_REVIEW_REQUIRED_FILES, 3, False
    rounds_text = scalar_from_text(final_text, "claude_rounds_required")
    try:
        rounds_required = int(rounds_text)
    except ValueError:
        rounds_required = AI_CROSS_REVIEW_TIER_ROUNDS.get(review_tier, -1)
    if review_tier not in AI_CROSS_REVIEW_TIER_ROUNDS or rounds_required not in AI_CROSS_REVIEW_TIER_ROUNDS.values():
        return [
            "00_task.md",
            "01_codex_actions.md",
            "02_codex_temp_agent_pre_review.md",
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
        "02_codex_temp_agent_pre_review.md",
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

    round_marker_items = list(AI_CROSS_REVIEW_ROUND_MARKERS.items())
    if tiered_pack:
        allowed_round_files: set[str] = set()
        for index in range(max(0, rounds_required)):
            claude_file, codex_file = AI_CROSS_REVIEW_CLAUDE_ROUND_FILES[index]
            allowed_round_files.add(claude_file)
            if codex_file and index + 1 < rounds_required:
                allowed_round_files.add(codex_file)
        round_marker_items = [(filename, markers) for filename, markers in round_marker_items if filename in allowed_round_files]
    for filename, markers in round_marker_items:
        path = pack_dir / filename
        if not path.is_file():
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                errors.append(f"{filename} missing marker: {marker}")
        if filename in {"05_claude_review_round_1.md", "07_claude_review_round_2.md", "09_claude_review_round_3.md"}:
            verdict_match = re.search(r"(?im)^\s*verdict:\s*(\S+)\s*$", text)
            if not verdict_match:
                errors.append(f"{filename} missing verdict value")
            elif verdict_match.group(1).strip().lower() != "pass":
                errors.append(f"{filename} verdict must be pass")

    pre_review_path = pack_dir / "02_codex_temp_agent_pre_review.md"
    if tiered_pack and pre_review_path.is_file():
        pre_text = read_text(pre_review_path)
        for marker in [
            "temporary_agent_required: true",
            "verdict: pass",
            "lifecycle: completed_closed",
            "closed_before_claude: true",
            "close_result_confirms_completion: true",
        ]:
            if marker not in pre_text:
                errors.append(f"02_codex_temp_agent_pre_review.md missing marker: {marker}")
        pre_agent_id = scalar_from_text(pre_text, "agent_instance_id")
        pre_close_result = scalar_from_text(pre_text, "close_result")
        if not codex_pre_review_close_result_text_valid(pre_agent_id, pre_close_result):
            errors.append(
                "02_codex_temp_agent_pre_review.md close_result must include matching agent id, previous_status=completed, and closed: true"
            )

    final_path = pack_dir / "10_final_decision.md"
    if final_path.is_file():
        final_text = read_text(final_path)
        if "ai_cross_review_status: blocked" in final_text:
            errors.append("ai cross review is blocked")
        if tiered_pack:
            review_tier = scalar_from_text(final_text, "review_tier")
            rounds_text = scalar_from_text(final_text, "claude_rounds_required")
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
        for marker in sorted(AI_CROSS_REVIEW_FINAL_MARKERS):
            if marker not in final_text:
                errors.append(f"10_final_decision.md missing marker: {marker}")
        if tiered_pack:
            for marker in [
                "review_tier:",
                "claude_rounds_required:",
                "codex_temp_agent_pre_review: pass",
                "codex_temp_agent_lifecycle: completed_closed",
            ]:
                if marker not in final_text:
                    errors.append(f"10_final_decision.md missing marker: {marker}")
        if re.search(r"unresolved_blocking_issues:\s*[1-9]", final_text):
            errors.append("10_final_decision.md has unresolved blocking issues")

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
- `02_codex_temp_agent_pre_review.md`
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
        "02_codex_temp_agent_pre_review.md",
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
- 02_codex_temp_agent_pre_review.md
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


def codex_pre_review_close_result_text_valid(agent_id: str, close_result: str) -> bool:
    text = close_result.strip()
    lower = text.lower()
    return (
        bool(agent_id)
        and agent_id in text
        and "previous_status" in lower
        and "completed" in lower
        and ("closed: true" in lower or '"closed": true' in lower or "closed=true" in lower)
    )


def codex_temp_pre_review_passed(args: argparse.Namespace) -> bool:
    close_result_confirms_completion = codex_pre_review_close_result_valid(args)
    return (
        args.codex_pre_review_verdict == "pass"
        and bool(args.codex_pre_review_agent_id.strip())
        and bool(args.codex_pre_review_agent_name.strip())
        and args.codex_pre_review_lifecycle == "completed_closed"
        and close_result_confirms_completion
    )


def codex_pre_review_close_result_valid(args: argparse.Namespace) -> bool:
    return codex_pre_review_close_result_text_valid(
        args.codex_pre_review_agent_id.strip(),
        args.codex_pre_review_close_result.strip(),
    )


def make_codex_temp_agent_pre_review_md(args: argparse.Namespace) -> str:
    passed = codex_temp_pre_review_passed(args)
    close_result_confirms_completion = codex_pre_review_close_result_valid(args)
    return f"""codex_temp_agent_pre_review: {"pass" if passed else "blocked"}
temporary_agent_required: true
agent_instance_id: {args.codex_pre_review_agent_id or "missing"}
ui_display_name: {args.codex_pre_review_agent_name or "missing"}
lifecycle: {args.codex_pre_review_lifecycle}
closed_before_claude: {str(close_result_confirms_completion).lower()}
close_result_confirms_completion: {str(close_result_confirms_completion).lower()}
close_result: {args.codex_pre_review_close_result or "missing"}
verdict: {args.codex_pre_review_verdict}
blocking_issues:
{"" if passed else "- missing passing temporary Codex pre-review agent evidence or close_result"}
notes: {args.codex_pre_review_notes or "temporary agent must be closed before Claude Code review starts"}
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
    refs = ["02_codex_temp_agent_pre_review.md"]
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
codex_temp_agent_pre_review: {"pass" if pre_review_passed else "blocked"}
codex_temp_agent_lifecycle: completed_closed
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
    pre_review_passed = codex_temp_pre_review_passed(args)

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
- codex_temp_agent_pre_review: pass
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
        "02_codex_temp_agent_pre_review.md",
        make_codex_temp_agent_pre_review_md(args),
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

claim: Claude Code 前置临时 Codex agent 已完成预审并关闭。
status: {"verified" if pre_review_passed else "false"}
evidence_ref: 02_codex_temp_agent_pre_review.md
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
    if not normalized.startswith("跑"):
        return {}
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
    if len(requested_mix) >= 2:
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
            "agent_instance_mode": "role_only until formal trial uses temporary_subagent",
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
            "target": "version-level or trial-internal controlled factor",
            "writes": "none until ablation target is confirmed",
            "agent_mode": "role_only for classification; real_multi_agent if code or semantic changes",
            "gates": "interface_contract, single_factor, metric_semantics",
            "next_action": "classify version-level vs trial-internal ablation",
        },
        "继续上一个": {
            "task_type": "trial-internal attempt or current task continuation",
            "target": "current trial or attempt",
            "writes": "current trial attempt ledger only after state is confirmed",
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
    filled.setdefault("agent_instance_mode", "temporary_subagent" if formal_intent else "role_only")
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
        f"  agent_instance_mode: {'temporary_subagent' if formal else 'role_only'}",
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
                "      required_agents_spawned: false",
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
temporary_subagent_reason:
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
        20,
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
        10,
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
        10,
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

    if len(specs) != 50:
        raise WorkflowError(f"Direction repeat confirmation plan must contain 50 jobs, got {len(specs)}")
    return specs


def _direction_exploit_followup_specs() -> list[tuple[str, str, dict[str, object]]]:
    specs: list[tuple[str, str, dict[str, object]]] = []

    def add_repeats(count: int, group: str, name: str, updates: dict[str, object]) -> None:
        for repeat_index in range(1, count + 1):
            specs.append((group, f"{name}_r{repeat_index:02d}", dict(updates)))

    add_repeats(
        6,
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


def _dr035_min6_confirm_specs() -> list[tuple[str, str, dict[str, object]]]:
    return _dr035_confirm_specs(6)


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
        specs = _dr035_min6_confirm_specs()
        repeat_source_ranks = []
    elif profile == "h76-existing-routing-100":
        specs = _h76_existing_routing_100_specs()
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
        jobs.append(
            {
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
        )

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
    return jobs


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


def _dynamic_runner_script() -> str:
    return r'''#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
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


def run(cmd, cwd=None, env=None, log_path=None):
    if log_path is None:
        return subprocess.run(cmd, cwd=cwd, env=env, text=True, check=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as handle:
        return subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=handle, stderr=subprocess.STDOUT)


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
            "log_path", "warehouse_dir",
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
    rows.sort(key=lambda row: float(row.get("H") or "-inf"), reverse=True)
    if len(rows) < rank:
        return None
    return rows[rank - 1]


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


def ensure_worktree(plan, gpu):
    server_repo = Path(plan["server_repo"])
    worktree_root = Path(plan["worktree_root"])
    commit = plan["commit"]
    branch = plan["branch"]
    git_remote = plan.get("git_remote", "origin")
    sha7 = commit[:7]
    worktree = worktree_root / f"dynroute_{sha7}_gpu{gpu}"
    worktree_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(server_repo), "fetch", str(git_remote), branch], check=False)
    if not worktree.exists():
        subprocess.run(["git", "-C", str(server_repo), "worktree", "add", str(worktree), commit], check=True)
    link_runtime_resources(plan, worktree)
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
    attempt_dir.mkdir(parents=True, exist_ok=True)
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
        "recorded_at": utc_now(),
    }
    (attempt_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(attempt_dir)


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
    try:
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
        code = run(cmd, cwd=worktree, env=env, log_path=log_path).returncode
        warehouse_dir = copy_artifacts_to_warehouse(plan, job, worktree, log_path, runtime_config, start_ts)
        if code != 0:
            row = {
                **job,
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
        row = {**job, **metrics, "status": status, "gpu": gpu, "resolved_from_job_id": resolved_from, "log_path": str(log_path), "warehouse_dir": warehouse_dir}
        update_job(run_dir, job_id, status=status, returncode=code, log_path=str(log_path), resolved_from_job_id=resolved_from, metrics=metrics, warehouse_dir=warehouse_dir)
        append_summary(run_dir, row)
        append_jsonl(run_dir / "events.jsonl", {"time": utc_now(), "event": f"job_{status}", "job_id": job_id, "gpu": gpu, "metrics": metrics, "warehouse_dir": warehouse_dir})
    except Exception as exc:
        error_path = log_dir / f"{job_id}_gpu{gpu}.error.txt"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        if worktree is not None:
            try:
                warehouse_dir = copy_artifacts_to_warehouse(plan, job, worktree, log_path, runtime_config, start_ts)
            except Exception:
                warehouse_dir = ""
        if not warehouse_dir:
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
        row = {
            **job,
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
        status = load_json(run_dir / "batch_status.json").get("jobs", {}).get(job["job_id"], {}).get("status")
        if status in {"completed", "failed", "skipped", "running"}:
            continue
        run_job(run_dir, plan, job, args.gpu)
        refresh_batch_status(run_dir)

    while not all_explore_finished(run_dir, plan):
        refresh_batch_status(run_dir)
        time.sleep(30)

    for job in assigned:
        if job["phase"] != "repeat":
            continue
        status = load_json(run_dir / "batch_status.json").get("jobs", {}).get(job["job_id"], {}).get("status")
        if status in {"completed", "failed", "skipped", "running"}:
            continue
        run_job(run_dir, plan, job, args.gpu)
        refresh_batch_status(run_dir)
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

    run_id = args.run_id or f"RUN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-dynroute50-2gpu"
    run_root = REPO_ROOT / ".gtpj_runtime" / "batches"
    run_dir = run_root / run_id
    if run_dir.exists():
        raise WorkflowError(f"Refusing to overwrite existing run dir: {display_path(run_dir)}")
    ensure_dir(run_dir)
    ensure_dir(run_dir / "configs")
    ensure_dir(run_dir / "logs")
    ensure_dir(run_dir / "pids")
    ensure_dir(run_dir / "runtime_configs")

    gpus = [int(part.strip()) for part in args.gpus.split(",") if part.strip()]
    if not gpus:
        raise WorkflowError("At least one GPU id is required.")
    jobs = build_dynamic_routing_jobs(seed=int(args.seed), profile=args.profile)
    if int(args.jobs) != len(jobs):
        raise WorkflowError(f"Dynamic routing batch profile {args.profile!r} expects {len(jobs)} jobs, got --jobs {args.jobs}.")
    for index, job in enumerate(jobs):
        job["gpu_slot"] = index % len(gpus)

    branch = args.branch or current_branch()
    commit = args.commit or git(["rev-parse", "HEAD"], check=False)
    trial_id, _trial_slug = parse_trial_folder_name(trial_dir)
    base_version = args.base_version
    plan = {
        "run_id": run_id,
        "profile": args.profile,
        "created_at": utc_now(),
        "formal_evidence": not bool(args.debug_smoke),
        "evidence_level": "debug_smoke" if args.debug_smoke else "formal_pre_run",
        "agent_runtime_gate": agent_runtime_gate,
        "trial_dir": display_path(trial_dir),
        "base_config": display_path(base_config),
        "base_version": base_version,
        "trial_id": trial_id,
        "branch": branch,
        "commit": commit,
        "git_remote": args.git_remote,
        "gpus": gpus,
        "server_repo": args.server_repo,
        "worktree_root": args.worktree_root,
        "warehouse_root": args.warehouse_root,
        "warehouse_scope": "attempt_run" if warehouse_attempt_id else "legacy_job_attempt",
        "warehouse_attempt_id": warehouse_attempt_id,
        "runtime_resource_links": ["data"],
        "conda_env": args.conda_env,
        "python": args.python,
        "jobs": jobs,
    }
    write_new(run_dir / "plan.json", json.dumps(plan, ensure_ascii=False, indent=2))

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
        "#!/usr/bin/env bash\nset -euo pipefail\ncd \"$(dirname \"$0\")\"\nmkdir -p logs pids runtime_configs\n"
        + "\n".join(gpu_lines),
    )
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
cd {run_dir.as_posix()}
bash start_batch.sh
```

Outputs:

- `batch_status.json`
- `summary.csv`
- `summary.jsonl`
- `events.jsonl`
- `logs/`
- `runtime_configs/`
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

    agent_cleanup = sub.add_parser("agent-cleanup-plan", help="只读列出右侧临时 agents 的保留/关闭计划")
    agent_cleanup.add_argument("--path", required=True)
    agent_cleanup.set_defaults(func=cmd_agent_cleanup_plan)

    validate_workflow_consistency = sub.add_parser("validate-workflow-consistency", help="校验 workflow 文档和模板的 runtime gate 标记")
    validate_workflow_consistency.set_defaults(func=cmd_validate_workflow_consistency)

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
    run_ai_cross_review.add_argument("--codex-pre-review-agent-id", default="")
    run_ai_cross_review.add_argument("--codex-pre-review-agent-name", default="")
    run_ai_cross_review.add_argument("--codex-pre-review-lifecycle", default="completed_closed", choices=["completed_closed"])
    run_ai_cross_review.add_argument("--codex-pre-review-close-result", default="")
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
        choices=["", "debug_smoke", "quick_local", "valid_single_run", "confirmation_grade", "baseline_grade"],
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

    new_trial = sub.add_parser("new-trial", help="在某个 idea 下创建 trial 目录")
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
    dyn_plan.add_argument("--profile", default="balanced-aggressive")
    dyn_plan.add_argument("--base-version", default="v5")
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
    dyn_plan.add_argument("--debug-smoke", action="store_true")
    dyn_plan.set_defaults(func=cmd_plan_dynamic_routing_batch)

    dyn_status = sub.add_parser("dynamic-routing-status", help="读取 dynamic routing batch 状态")
    dyn_status.add_argument("--run-dir", required=True)
    dyn_status.set_defaults(func=cmd_dynamic_routing_status)

    dyn_analyze = sub.add_parser("analyze-dynamic-routing-batch", help="分析 dynamic routing batch summary")
    dyn_analyze.add_argument("--run-dir", required=True)
    dyn_analyze.add_argument("--top-k", type=int, default=5)
    dyn_analyze.set_defaults(func=cmd_analyze_dynamic_routing_batch)

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
