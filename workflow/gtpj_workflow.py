#!/usr/bin/env python
"""Optional repository-structure helper for the GTPJ repository.

This script is intentionally small and deterministic. It creates governance
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
SOURCE_TYPES = {"paper", "user", "observation", "cross_domain", "hybrid"}
SOURCE_STATUSES = {"verified", "unverified", "unknown", "local_heuristic"}
TRIAL_ALLOWED_SOURCE_STATUSES = {"verified", "local_heuristic"}
APPLICABILITIES = {"direct", "needs_adaptation", "unclear", "not_applicable"}
TRIAL_ALLOWED_APPLICABILITIES = {"direct", "needs_adaptation"}
TRIAL_READY_STATUSES = {"selected"}
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

CANONICAL_BASELINES = {
    "v1": {
        "name": "GTPJ-v1",
        "H": "73.93",
        "result_file": "experiments/v1/result.md",
        "version_file": "experiments/v1/VERSION.md",
    }
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


def tag_commit(tag: str) -> str:
    return git(["rev-parse", tag])


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
        "docs/workflow/experiment_protocol.md",
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
        "experiments/README.md",
        "experiments/EXPERIMENT_REGISTRY.md",
        "experiments/VERSION_TREE.md",
        "experiments/module_trials/INDEX.md",
        "experiments/templates/IDEA_template.md",
        "experiments/templates/TRIAL_README_template.md",
        "experiments/templates/VERSION_template.md",
        "experiments/templates/experiment_README_template.md",
        "experiments/templates/implementation_template.md",
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
    ]
    missing = [item for item in required if not (REPO_ROOT / item).exists()]
    if missing:
        raise WorkflowError("Missing required files:\n" + "\n".join(missing))

    idea_tree = json.loads(read_text(REPO_ROOT / "idea_tree" / "idea_tree.json"))
    if idea_tree.get("project") != "GTPJ":
        raise WorkflowError("idea_tree.json project must be GTPJ")
    current_version = idea_tree.get("current_version")
    if not isinstance(current_version, str) or not re.fullmatch(r"v[0-9]+", current_version):
        raise WorkflowError("idea_tree.json current_version must look like v1")

    idea_index = read_text(REPO_ROOT / "idea_tree" / "INDEX.md")
    for idea in idea_tree.get("ideas", []):
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
            if not isinstance(entry.get("blockers"), list):
                raise WorkflowError(f"{idea_id} {version} blockers must be a list")
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

    v1_config = read_text(REPO_ROOT / "config" / "versions" / "v1.yaml")
    archived_config = read_text(REPO_ROOT / "experiments" / "v1" / "config.yaml")
    if v1_config != archived_config:
        raise WorkflowError("config/versions/v1.yaml and experiments/v1/config.yaml differ")

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


def make_experiment_readme(version: str, kind: ExperimentKind, exp_id: str, slug: str) -> str:
    return f"""# {exp_id}_{slug}

```text
experiment_id: {exp_id}
version: {version}
base_code_tag: {version}
branch_source: main
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
original_log:
copied_log:
artifact_manifest:
attempt_id:
failure_stage:
decision:
status: planned
```

## 问题

描述这个实验要回答的精确问题。

## 运行前检查

- [ ] 临时分支从当前 `main` 切出，用 `base_code_tag: {version}` 固定代码来源。
- [ ] 配置复制自 `experiments/{version}/config.yaml`。
- [ ] 只改变声明过的变量或开关。
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

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
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
- [ ] 日志路径明确。
- [ ] 结果口径明确。
- [ ] 没有未声明的 eval / class order / logits shape 改动。

## Promotion Gate（仅正式提升 vX 时填写）

- [ ] parent_version / parent_tag 明确。
- [ ] trial tag 指向 README 中记录的 code_commit。
- [ ] baseline H、trial H、delta H 明确。
- [ ] U/S/ZS、best epoch、seed 明确。
- [ ] 同 seed 对照明确；高风险改动已说明是否需要多 seed。
- [ ] trial config 和新版本 config 路径明确。
- [ ] 原始日志路径和 Git 内日志副本路径明确。
- [ ] class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] switch off 能回到 parent_version 行为。
- [ ] VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] idea_tree current_version 和必要的 version_scores.vX 已更新。
- [ ] 新 baseline tag 准备打在最终 main commit 上。

## 决策

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

    ensure_dir(exp_dir / "logs")
    write_new(exp_dir / "README.md", make_experiment_readme(version, kind, exp_id, slug))
    write_new(exp_dir / "quality_check.md", make_quality_check(kind))
    copy_new(src_config, exp_dir / "config.yaml")
    append_version_experiment_registry(version, kind, exp_id, slug, exp_dir)
    append_kind_index(version, kind, exp_id, slug, exp_dir)

    print(f"已创建 {rel(exp_dir)}")
    print(f"建议分支: {experiment_branch_name(version, kind, exp_id, slug)}")
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


def write_idea_index(data: dict) -> None:
    current_version = data.get("current_version", "v1")
    ideas = sorted(
        data.get("ideas", []),
        key=lambda item: (
            -idea_score_for_version(item, current_version),
            -SOURCE_STATUS_RANK.get(item.get("source_status", "unknown"), 0),
            -float(item.get("global_score", 0) or 0),
            item.get("idea_id", ""),
        ),
    )

    lines = [
        "# 创意树索引",
        "",
        f"当前框架版本：`{current_version}`",
        "",
        "这是给人读的主列表。当前工作窗口优先按",
        f"`{current_version}` 分数排序。`global_score` 表示长期价值，",
        "不直接决定当前实验顺序。",
        "",
        "| 排名 | Idea | 标题 | Idea 文件 | 来源状态 | 全局分 | 当前分 | 适用性 | 状态 | 下一步 |",
        "|---:|---|---|---|---|---:|---:|---|---|---|",
    ]
    for rank, idea in enumerate(ideas, 1):
        entry = idea_version_entry(idea, current_version)
        idea_dir = idea.get("idea_dir", "")
        idea_file = f"{str(idea_dir).rstrip('/')}/IDEA.md" if idea_dir else ""
        lines.append(
            "| "
            f"{rank} | `{idea.get('idea_id', '')}` | {idea.get('title', '')} | "
            f"`{idea_file}` | {idea.get('source_status', '')} | "
            f"{idea.get('global_score', 0)} | {entry.get('score', 0)} | "
            f"{entry.get('applicability', '')} | {idea.get('status', '')} | "
            f"{idea.get('next_action', '')} |"
        )
    if not ideas:
        lines.append("| - | - | - | - | - | - | - | - | - | 等待从可靠来源重新登记。 |")

    lines.extend(
        [
            "",
            "## 版本感知规则",
            "",
            "- 实验顺序使用当前激活版本的分数列。",
            "- 创建新框架版本时，添加新的 `version_scores.vX` 条目。",
            "- 没有重新检查接口适配性前，不要把旧版本分数复制到新版本。",
            "- 高 `global_score` 但低当前分，表示这个想法可能以后有用，不代表现在优先。",
            "",
        ]
    )
    (REPO_ROOT / "idea_tree" / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


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

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `{base_version}` | {version_score} | {args.applicability} | 待补充。 |

机器可读版本评分写在 `idea_tree/idea_tree.json` 的 `version_scores` 字段。
新增 `v2`、`v3` 时必须重新评估，不能复制 `{base_version}` 分数。

## 迁移说明

记录这个创意是否可以迁移到 `v2` 等后续版本，以及需要改变什么。

## 风险

## 阻塞点

## 决策规则
""",
    )
    data.setdefault("ideas", []).append(idea)
    save_idea_tree(data)
    write_idea_index(data)

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
    write_idea_index(data)
    print(f"current_version={version}")
    print("已刷新 idea_tree/INDEX.md")
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

    ensure_dir(trial_dir / "logs")
    copy_new(REPO_ROOT / "experiments" / base_version / "config.yaml", trial_dir / "config.yaml")
    write_new(trial_dir / "code.diff", "")
    code_branch = trial_branch_name(base_version, idea_id, trial_id, slug)
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
run_log:
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
- [ ] 证据目录、日志副本和 code.diff 完整。
- [ ] `promotion_decision` 为 `ACCEPTED` 后才允许提升为正式 vX。

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
- [ ] Logits shape 保持 `[B, C]`。
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
    write_new(trial_dir / "result.md", "# 结果\n\n待记录。\n")
    append_module_trial_index(idea_id, trial_id, slug, trial_dir)
    linked_trials = idea.setdefault("linked_trials", [])
    trial_rel = rel(trial_dir)
    if trial_rel not in linked_trials:
        linked_trials.append(trial_rel)
        save_idea_tree(data)
        write_idea_index(data)

    print(f"已创建 {rel(trial_dir)}")
    print(f"建议分支: {code_branch}")
    print(f"实现后建议 tag: {code_tag}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GTPJ 可选结构辅助 helper")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="显示仓库状态")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="校验仓库结构")
    validate.set_defaults(func=cmd_validate)

    new_exp = sub.add_parser("new-experiment", help="创建版本实验目录")
    new_exp.add_argument("--version", required=True)
    new_exp.add_argument("--kind", required=True, choices=sorted(KINDS))
    new_exp.add_argument("--exp-id", required=True)
    new_exp.add_argument("--slug", required=True)
    new_exp.set_defaults(func=cmd_new_experiment)

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
