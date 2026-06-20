#!/usr/bin/env python
"""Executable workflow helper for the GTPJ repository.

This script is intentionally small and deterministic. It creates workflow
folders, copies version configs, and validates repository invariants. It does
not run training, push to GitHub, or mutate Git history.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
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


class WorkflowError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExperimentKind:
    name: str
    folder: str
    prefix: str
    default_review: str


KINDS = {
    "tune": ExperimentKind("tune", "tune", "TUNE", "TUNE-LITE"),
    "ablation": ExperimentKind("ablation", "ablation", "ABL", "STANDARD"),
    "final": ExperimentKind("final", "final", "FINAL", "STRICT"),
}


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


def git(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise WorkflowError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def require_clean_id(value: str, pattern: str, label: str) -> str:
    if not re.fullmatch(pattern, value):
        raise WorkflowError(f"Invalid {label}: {value}")
    return value


def require_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\\-]*", value):
        raise WorkflowError(
            "Slug must use lowercase letters, numbers, underscore, or hyphen"
        )
    return value


def branch_slug(value: str) -> str:
    return value.replace("_", "-")


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


def cmd_status(_: argparse.Namespace) -> int:
    branch = git(["branch", "--show-current"], check=False) or "(detached)"
    head = git(["rev-parse", "--short", "HEAD"], check=False)
    tags = git(["tag", "--points-at", "HEAD"], check=False)
    porcelain = git(["status", "--short"], check=False)

    print("GTPJ workflow status")
    print(f"- branch: {branch}")
    print(f"- head: {head}")
    print(f"- tags at head: {tags or '(none)'}")
    print(f"- working tree: {'dirty' if porcelain else 'clean'}")
    print()
    print("Available versions:")
    for version_dir in sorted((REPO_ROOT / "experiments").glob("v*")):
        if version_dir.is_dir():
            print(f"- {version_dir.name}: {rel(version_dir)}")
    print()
    print("Next queues:")
    for queue in sorted((REPO_ROOT / "idea_tree" / "queues").glob("*.md")):
        print(f"- {rel(queue)}")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    required = [
        "README.md",
        "AGENTS.md",
        "docs/workflow/README.md",
        "docs/workflow/git_policy.md",
        "docs/workflow/versioning.md",
        "docs/workflow/module_trial_protocol.md",
        "docs/workflow/experiment_protocol.md",
        "docs/workflow/idea_tree_protocol.md",
        "docs/workflow/review_gate.md",
        "docs/workflow/runbook.md",
        "workflow/README.md",
        "workflow/openclaw/README.md",
        "workflow/codex/README.md",
        "idea_tree/schema.json",
        "idea_tree/idea_tree.json",
        "experiments/EXPERIMENT_REGISTRY.md",
        "experiments/v1/VERSION.md",
        "experiments/v1/config.yaml",
        "config/versions/v1.yaml",
    ]
    missing = [item for item in required if not (REPO_ROOT / item).exists()]
    if missing:
        raise WorkflowError("Missing required files:\n" + "\n".join(missing))

    idea_tree = json.loads(read_text(REPO_ROOT / "idea_tree" / "idea_tree.json"))
    if idea_tree.get("project") != "GTPJ":
        raise WorkflowError("idea_tree.json project must be GTPJ")

    if not git(["tag", "--list", "v1"], check=False):
        raise WorkflowError("Missing required tag: v1")

    v1_config = read_text(REPO_ROOT / "config" / "versions" / "v1.yaml")
    archived_config = read_text(REPO_ROOT / "experiments" / "v1" / "config.yaml")
    if v1_config != archived_config:
        raise WorkflowError("config/versions/v1.yaml and experiments/v1/config.yaml differ")

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


def make_experiment_readme(version: str, kind: ExperimentKind, exp_id: str, slug: str) -> str:
    return f"""# {exp_id}_{slug}

```text
experiment_id: {exp_id}
version: {version}
code_tag: {version}
runtime: OpenClaw preferred / Codex compatible
review_mode: {kind.default_review}
run_commit:
config: config.yaml
log:
status: planned
```

## Question

Describe the exact question this experiment answers.

## Pre-Run Checklist

- [ ] Branch starts from tag `{version}`.
- [ ] Config is copied from `experiments/{version}/config.yaml`.
- [ ] Only the declared variable or switch changes.
- [ ] Review decision is `ACCEPTED`.

## Result

| Dataset | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Conclusion

Pending.
"""


def make_review(kind: ExperimentKind) -> str:
    return f"""# Review

```text
runtime:
review_mode: {kind.default_review}
decision: PENDING
```

## Scope

## Findings

## Decision

PENDING
"""


def append_version_experiment_registry(
    version: str, kind: ExperimentKind, exp_id: str, slug: str, folder: Path
) -> None:
    registry = REPO_ROOT / "experiments" / "EXPERIMENT_REGISTRY.md"
    content = read_text(registry)
    experiment_name = f"{exp_id}_{slug}"
    row = (
        f"| `{experiment_name}` | `{version}` | `{kind.name}` | planned | "
        f"`{rel(folder)}` | Created by workflow helper. |"
    )
    if experiment_name in content:
        return

    placeholder = "No clean GTPJ-run experiments yet."
    table = "\n".join(
        [
            "| Experiment | Version | Kind | Status | Folder | Notes |",
            "|---|---|---|---|---|---|",
            row,
        ]
    )
    if placeholder in content:
        content = content.replace(placeholder, table)
    else:
        content = content.rstrip() + "\n" + row + "\n"
    registry.write_text(content, encoding="utf-8")


def cmd_new_experiment(args: argparse.Namespace) -> int:
    version = require_clean_id(args.version, r"v[0-9]+", "version")
    kind = KINDS[args.kind]
    exp_id = require_clean_id(args.exp_id, rf"{kind.prefix}-[0-9]{{3}}", "experiment id")
    slug = require_slug(args.slug)

    base_dir = REPO_ROOT / "experiments" / version
    if not base_dir.exists():
        raise WorkflowError(f"Unknown version directory: {rel(base_dir)}")
    src_config = base_dir / "config.yaml"
    exp_dir = base_dir / kind.folder / f"{exp_id}_{slug}"
    if exp_dir.exists():
        raise WorkflowError(f"Experiment already exists: {rel(exp_dir)}")

    ensure_dir(exp_dir / "logs")
    write_new(exp_dir / "README.md", make_experiment_readme(version, kind, exp_id, slug))
    write_new(exp_dir / "review.md", make_review(kind))
    copy_new(src_config, exp_dir / "config.yaml")
    append_version_experiment_registry(version, kind, exp_id, slug, exp_dir)

    print(f"created {rel(exp_dir)}")
    print(f"suggested branch: exp/{version}-{exp_id.lower()}-{branch_slug(slug)}")
    return 0


def load_idea_tree() -> dict:
    return json.loads(read_text(REPO_ROOT / "idea_tree" / "idea_tree.json"))


def save_idea_tree(data: dict) -> None:
    path = REPO_ROOT / "idea_tree" / "idea_tree.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_idea_record(data: dict, idea_id: str) -> dict:
    for item in data.get("ideas", []):
        if item.get("idea_id") == idea_id:
            return item
    raise WorkflowError(f"Missing idea in idea_tree.json: {idea_id}")


def cmd_new_idea(args: argparse.Namespace) -> int:
    idea_id = require_clean_id(args.idea_id, r"IDEA-[0-9]{4}", "idea id")
    slug = require_slug(args.slug)
    base_version = require_clean_id(args.base_version, r"v[0-9]+", "base version")
    if args.source_type not in {"paper", "user", "observation", "hybrid"}:
        raise WorkflowError("Invalid source_type")
    if not (REPO_ROOT / "experiments" / base_version / "config.yaml").exists():
        raise WorkflowError(f"Unknown base version: {base_version}")

    data = load_idea_tree()
    if any(item.get("idea_id") == idea_id for item in data.get("ideas", [])):
        raise WorkflowError(f"Idea already exists in idea_tree.json: {idea_id}")

    idea = {
        "idea_id": idea_id,
        "title": args.title,
        "status": "candidate",
        "source_type": args.source_type,
        "source_ref": args.source_ref or "",
        "base_versions": [base_version],
        "based_on_modules": [],
        "target_component": "",
        "hypothesis": "",
        "expected_effect": {"U": "", "S": "", "H": ""},
        "implementation_scope": "",
        "risk": "",
        "compatibility": "",
        "priority": 0,
        "linked_trials": [],
        "linked_versions": [],
        "linked_experiments": [],
        "evidence": [],
        "next_action": "fill IDEA.md and decide whether to select",
    }
    data.setdefault("ideas", []).append(idea)
    save_idea_tree(data)

    idea_dir = REPO_ROOT / "experiments" / "module_trials" / f"{idea_id}_{slug}"
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
base_version: {base_version}
```

## Based On Modules

## Target Component

## Hypothesis

## Implementation Scope

## Risk

## Planned Trials

## Decision Rule
""",
    )

    print(f"created {rel(idea_dir)}")
    return 0


def find_idea_dir(idea_id: str) -> Path:
    matches = sorted((REPO_ROOT / "experiments" / "module_trials").glob(f"{idea_id}_*"))
    if not matches:
        raise WorkflowError(f"Missing idea directory for {idea_id}")
    if len(matches) > 1:
        raise WorkflowError(f"Multiple idea directories found for {idea_id}")
    return matches[0]


def cmd_new_trial(args: argparse.Namespace) -> int:
    idea_id = require_clean_id(args.idea_id, r"IDEA-[0-9]{4}", "idea id")
    trial_id = require_clean_id(args.trial_id, r"TRIAL-[0-9]{3}", "trial id")
    slug = require_slug(args.slug)
    data = load_idea_tree()
    idea = find_idea_record(data, idea_id)
    base_versions = idea.get("base_versions") or []
    if not base_versions:
        raise WorkflowError(f"Idea has no base_versions: {idea_id}")
    base_version = require_clean_id(base_versions[0], r"v[0-9]+", "base version")
    idea_dir = find_idea_dir(idea_id)
    trial_dir = idea_dir / f"{trial_id}_{slug}"
    if trial_dir.exists():
        raise WorkflowError(f"Trial already exists: {rel(trial_dir)}")

    ensure_dir(trial_dir / "logs")
    copy_new(REPO_ROOT / "experiments" / base_version / "config.yaml", trial_dir / "config.yaml")
    write_new(trial_dir / "code.diff", "")
    write_new(
        trial_dir / "README.md",
        f"""# {trial_id}_{slug}

```text
trial_id: {trial_id}
idea_id: {idea_id}
base_version: {base_version}
base_code_tag: {base_version}
code_branch: dev/{idea_id.lower()}-{trial_id.lower()}-{slug}
code_tag: trial/{idea_id.lower()}/{trial_id.lower()}
code_commit:
decision: pending
promote_to:
```

## Changed Files

## Result

| Dataset | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Decision

Pending.
""",
    )
    write_new(
        trial_dir / "implementation.md",
        """# Implementation

## New Module

## Based On

## Insert Point

## Input

## Output

## Config Switch

## Baseline-Off Path

## Risks

## Verification Points
""",
    )
    write_new(trial_dir / "review.md", make_review(ExperimentKind("module-trial", "module_trials", "TRIAL", "STRICT")))
    write_new(trial_dir / "result.md", "# Result\n\nPending.\n")

    print(f"created {rel(trial_dir)}")
    print(f"suggested branch: dev/{idea_id.lower()}-{trial_id.lower()}-{branch_slug(slug)}")
    print(f"suggested tag after implementation: trial/{idea_id.lower()}/{trial_id.lower()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTPJ executable workflow helper")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show workflow status")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="Validate workflow structure")
    validate.set_defaults(func=cmd_validate)

    new_exp = sub.add_parser("new-experiment", help="Create a version experiment folder")
    new_exp.add_argument("--version", required=True)
    new_exp.add_argument("--kind", required=True, choices=sorted(KINDS))
    new_exp.add_argument("--exp-id", required=True)
    new_exp.add_argument("--slug", required=True)
    new_exp.set_defaults(func=cmd_new_experiment)

    new_idea = sub.add_parser("new-idea", help="Create a new idea node and folder")
    new_idea.add_argument("--idea-id", required=True)
    new_idea.add_argument("--slug", required=True)
    new_idea.add_argument("--title", required=True)
    new_idea.add_argument("--source-type", required=True)
    new_idea.add_argument("--source-ref", default="")
    new_idea.add_argument("--base-version", required=True)
    new_idea.set_defaults(func=cmd_new_idea)

    new_trial = sub.add_parser("new-trial", help="Create a trial folder under an idea")
    new_trial.add_argument("--idea-id", required=True)
    new_trial.add_argument("--trial-id", required=True)
    new_trial.add_argument("--slug", required=True)
    new_trial.set_defaults(func=cmd_new_trial)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except WorkflowError as exc:
        print(f"workflow-error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
