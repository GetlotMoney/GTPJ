from __future__ import annotations

import contextlib
from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "workflow" / "gtpj_workflow.py"
CONFIRMATION_RULE_MARKERS_TEXT = (
    "repeat_type: exact_repeat\n"
    "original_seed\n"
    "max_attempts: 5\n"
    "max_attempts_hard_cap\n"
    "early_stop_on_best_hit: true\n"
    "restore_target_H\n"
    "near_miss_tolerance_H\n"
    "near_miss_not_restored\n"
    "seed_sweep\n"
    "multi_seed_stability\n"
    "not_confirmation_evidence\n"
)


def load_helper():
    spec = importlib.util.spec_from_file_location("gtpj_workflow_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load workflow helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WorkflowHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.module = load_helper()
        self.module.REPO_ROOT = self.repo
        self.module.LOCAL_GTPJ_WORKFLOW_SKILL_PATH = self.repo / ".codex" / "skills" / "gtpj-workflow" / "SKILL.md"
        self.module.LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent.mkdir(parents=True, exist_ok=True)
        skill_reference_dir = self.module.LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent / "references"
        skill_reference_dir.mkdir(parents=True, exist_ok=True)
        self.module.LOCAL_GTPJ_WORKFLOW_SKILL_PATH.write_text(
            "GitHub documentation is canonical\n"
            "local skill mirrors the repository rules\n"
            "docs/workflow/START_HERE.md\n"
            "docs/workflow/WORKFLOW_KERNEL.md\n"
            "same GitHub truth source\n"
            "开启多agents智能体工作流\n"
            "不得反复确认\n"
            "files_reviewed\n"
            "report-new-completions\n"
            "代码审核不被 `server_frozen_runner` 豁免\n"
            + CONFIRMATION_RULE_MARKERS_TEXT,
            encoding="utf-8",
        )
        for reference_name in ["start_here.md", "workflow_kernel.md", "quick_start.md"]:
            (skill_reference_dir / reference_name).write_text(
                "代码审核不被 `server_frozen_runner` 豁免\n",
                encoding="utf-8",
            )
        for reference_path in self.module.CONFIRMATION_RULE_SKILL_REFERENCE_FILES:
            path = self.module.LOCAL_GTPJ_WORKFLOW_SKILL_PATH.parent / reference_path
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text(CONFIRMATION_RULE_MARKERS_TEXT, encoding="utf-8")
            elif CONFIRMATION_RULE_MARKERS_TEXT not in path.read_text(encoding="utf-8"):
                path.write_text(path.read_text(encoding="utf-8") + "\n" + CONFIRMATION_RULE_MARKERS_TEXT, encoding="utf-8")
        self.module.CANONICAL_BASELINES = {
            "v1": {
                "name": "GTPJ-v1",
                "H": "73.93",
                "result_file": "experiments/v1/result.md",
                "version_file": "experiments/v1/VERSION.md",
            }
        }
        self.module.TUNE_CANDIDATE_RULES = [
            {
                "parameter": "conditional_text_ratio",
                "suggested_value": "0.010",
                "why": "Test candidate.",
                "risk": "Low.",
                "cost": "1 seed.",
            },
            {
                "parameter": "lambda_topo_pearson",
                "suggested_value": "0.15",
                "why": "Test candidate.",
                "risk": "Low.",
                "cost": "1 seed.",
            },
            {
                "parameter": "adapter_ratio",
                "suggested_value": "0.3",
                "why": "Test candidate.",
                "risk": "Low.",
                "cost": "1 seed.",
            },
        ]
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Workflow Test")
        self._write_minimal_repo()
        self._git("add", ".")
        self._git("commit", "-m", "seed minimal governance repo")
        self._git("tag", "v1")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def _commit_all(self, message: str = "commit test fixture") -> None:
        self._git("add", ".")
        if self._git("status", "--short").stdout.strip():
            self._git("commit", "-m", message)

    def _write(self, relative: str, content: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _add_confirmation_rule_markers(self) -> None:
        for relative in self.module.CONFIRMATION_RULE_REPO_SYNC_FILES:
            path = self.repo / relative
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            if CONFIRMATION_RULE_MARKERS_TEXT not in existing:
                self._write(relative, existing + "\n" + CONFIRMATION_RULE_MARKERS_TEXT)

    def _write_minimal_repo(self) -> None:
        self._write(
            "experiments/v1/config.yaml",
            "version: v1\n"
            "conditional_text_ratio:\n"
            "  value: 0.008\n"
            "lambda_topo_pearson:\n"
            "  value: 0.10\n"
            "adapter_ratio:\n"
            "  value: 0.2\n"
            "tf_dropout:\n"
            "  value: 0.1\n",
        )
        self._write(
            "idea_tree/idea_tree.json",
            '{\n  "project": "GTPJ",\n  "version": "test",\n  "current_version": "v1",\n  "ideas": []\n}\n',
        )
        self._write("idea_tree/INDEX.md", "# 总创意清单\n\n")
        self._write("idea_tree/versions/v1.md", "# v1 创意选择清单\n\n")
        self._write(
            "idea_tree/queues/queue_state.yaml",
            'schema_version: "gtpj-queue-state/v1"\n'
            'updated_at: "test"\n'
            "current_window:\n"
            '  focus: "test focus"\n'
            '  policy: "test policy"\n'
            "actions:\n"
            '  - priority: "P0"\n'
            '    item: "Run queue smoke."\n'
            '    type: "workflow"\n'
            '    owner: "Coordinator"\n'
            '    status: "open"\n'
            '    blocked_by: "-"\n'
            '    evidence_ref: "NEXT_ACTIONS.md"\n'
            "completed: []\n"
            "selected_next: []\n"
            "module_candidates: []\n"
            "ablation_questions: []\n"
            "tuning_questions: []\n",
        )
        self._write("idea_tree/queues/01_selected_next.md", "# 已选队列\n\n")
        self._write("idea_tree/queues/02_module_candidates.md", "# 模块候选\n\n")
        self._write("idea_tree/queues/03_ablation_questions.md", "# 消融问题队列\n\n")
        self._write("idea_tree/queues/04_tuning_questions.md", "# 调参问题队列\n\n")
        self._write(
            "experiments/EXPERIMENT_REGISTRY.md",
            "# Experiment Registry\n\n| Experiment | Version | Kind | Status | Directory | Note |\n"
            "|---|---|---|---|---|---|\n| 暂无 | - | - | - | - | - |\n",
        )
        self._write(
            "experiments/v1/confirmation/INDEX.md",
            "# Confirmation Index\n\n| 实验 | 状态 | 目录 | 说明 |\n"
            "|---|---|---|---|\n| 暂无 | - | - | - |\n",
        )
        self._write(
            "experiments/v1/tune/INDEX.md",
            "# Tune Index\n\n| 实验 | 状态 | 目录 | 说明 |\n"
            "|---|---|---|---|\n| 暂无 | - | - | - |\n",
        )

    def _run_main(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = self.module.main(list(args))
            except SystemExit as exc:
                code = int(exc.code or 0)
        return code, stdout.getvalue(), stderr.getvalue()

    def _passing_codex_pre_review_args(self) -> list[str]:
        return [
            "--codex-pre-review-thread-id",
            "thread-test-001",
            "--codex-pre-review-thread-title",
            "ATTEMPT-REVIEW | Codex Pre Review",
            "--codex-pre-review-archive-result",
            "thread_id=thread-test-001 previous_status=completed archived: true",
            "--codex-pre-review-verdict",
            "pass",
        ]

    def _custom_full_validation_command(self) -> str:
        self._write(
            "workflow/gtpj_workflow.py",
            "import sys\n"
            "allowed = {'validate', 'validate-workflow-consistency', 'audit-boundary'}\n"
            "command = sys.argv[1] if len(sys.argv) > 1 else ''\n"
            "if command not in allowed:\n"
            "    raise SystemExit(1)\n"
            "print(command + '-ok')\n",
        )
        return (
            f'"{sys.executable}" workflow\\gtpj_workflow.py validate && '
            f'"{sys.executable}" workflow\\gtpj_workflow.py validate-workflow-consistency && '
            f'"{sys.executable}" workflow\\gtpj_workflow.py audit-boundary && '
            f'"{sys.executable}" -m py_compile workflow\\gtpj_workflow.py'
        )

    def _registry_text(self) -> str:
        return (self.repo / "experiments/EXPERIMENT_REGISTRY.md").read_text(encoding="utf-8")

    def _confirmation_index_text(self) -> str:
        return (self.repo / "experiments/v1/confirmation/INDEX.md").read_text(encoding="utf-8")

    def _tune_index_text(self) -> str:
        return (self.repo / "experiments/v1/tune/INDEX.md").read_text(encoding="utf-8")

    def _selected_idea(self, *, stage: str | None = "selected") -> dict:
        version_score = {
            "score": 70,
            "applicability": "direct",
            "rationale": "Fits the current v1 bottleneck.",
            "blockers": [],
        }
        if stage is not None:
            version_score["stage"] = stage
        return {
            "idea_id": "IDEA-0001",
            "idea_dir": "idea_tree/ideas/IDEA-0001_token_router/",
            "title": "Token Router",
            "status": "selected",
            "source_type": "paper",
            "source_ref": "paper-x",
            "source_status": "verified",
            "global_score": 80,
            "core_summary": "Token routing core idea.",
            "version_scores": {"v1": version_score},
            "base_versions": ["v1"],
            "based_on_modules": [],
            "target_component": "model",
            "hypothesis": "Improve visual-text routing.",
            "implementation_scope": "Small routing module.",
            "risk": "May overfit.",
            "transfer_notes": "",
            "linked_trials": [],
            "linked_versions": [],
            "linked_experiments": [],
            "evidence": [],
        }

    def _write_idea_tree(self, ideas: list[dict]) -> None:
        payload = {
            "project": "GTPJ",
            "version": "test",
            "current_version": "v1",
            "ideas": ideas,
        }
        self._write("idea_tree/idea_tree.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def _write_selected_idea_files(self, *, stage: str | None = "selected") -> dict:
        idea = self._selected_idea(stage=stage)
        self._write("idea_tree/ideas/IDEA-0001_token_router/IDEA.md", "# IDEA-0001\n")
        self._write_idea_tree([idea])
        return idea

    def _transition_record(
        self,
        *,
        transition_id: str = "TRN-20260701-0001",
        previous_transition_id: str | None = None,
        previous_transition_hash: str | None = None,
        from_state: str = "smoke_passed",
        to_state: str = "single_run_valid",
        transition_type: str = "advance",
        verdict: str = "pass",
        authority_ref: str = "experiments/v1/tune/TUNE-001_ok/manifest.yaml",
        include_not_checked: bool = True,
    ) -> dict:
        record = {
            "schema_version": "gtpj.transition.v0",
            "transition_id": transition_id,
            "previous_transition_id": previous_transition_id,
            "previous_transition_hash": previous_transition_hash,
            "subject": {
                "subject_id": "ATTEMPT-001",
                "subject_type": "attempt",
                "hypothesis_id": "HYP-0001",
            },
            "transition": {
                "transition_type": transition_type,
                "from_state": from_state,
                "to_state": to_state,
                "reason_summary": "test transition",
            },
            "rule_checks": [
                {
                    "rule_id": "GZSL.LOGITS_SHAPE",
                    "verdict": verdict,
                    "checked_by": "interface_checker",
                    "authority_ref": authority_ref,
                }
            ],
            "authority_refs": {
                "manifest": authority_ref,
            },
            "agent_attribution": {
                "proposed_by": {"role_key": "log_analyst", "agent_instance_id": "LOG-001"},
                "checked_by": [{"role_key": "quality_checker", "agent_instance_id": "QC-001"}],
                "applied_by": {"role_key": "coordinator", "agent_instance_id": "COORD-001"},
            },
            "decision": {
                "blocking_issues": [],
                "non_blocking_warnings": [],
                "not_checked": [],
            },
            "created_at": "2026-07-01T00:00:00Z",
            "current_transition_hash": "",
        }
        if not include_not_checked:
            record["decision"].pop("not_checked")
        record["current_transition_hash"] = self.module.evidence_transition_hash(record)
        return record

    def _write_evidence_routing_subject(self, transitions: list[dict]) -> Path:
        subject_dir = self.repo / "experiments/v1/tune/TUNE-001_ok"
        self._write(
            "experiments/v1/tune/TUNE-001_ok/manifest.yaml",
            "schema_version: gtpj-manifest/v1\n",
        )
        transitions_text = "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in transitions) + "\n"
        self._write("experiments/v1/tune/TUNE-001_ok/TRANSITIONS.jsonl", transitions_text)
        head = transitions[-1]
        self._write(
            "experiments/v1/tune/TUNE-001_ok/evidence_routing.yaml",
            "schema_version: gtpj.evidence_routing.v0\n"
            "subject:\n"
            "  subject_id: ATTEMPT-001\n"
            "  subject_type: attempt\n"
            "  hypothesis_id: HYP-0001\n"
            "current_state:\n"
            f"  evidence_state: {head['transition']['to_state']}\n"
            f"  derived_from_transition_id: {head['transition_id']}\n"
            f"  derived_from_transition_hash: {head['current_transition_hash']}\n"
            "transitions:\n"
            "  file: TRANSITIONS.jsonl\n"
            f"  chain_head_transition_id: {head['transition_id']}\n"
            f"  chain_head_hash: {head['current_transition_hash']}\n",
        )
        return subject_dir

    def _write_agent_runtime_gate(
        self,
        *,
        path: str = "experiments/v1/tune/TUNE-001_ok/agent_runtime.yaml",
        runner_decision: str = "allow",
        quality_decision: str = "allow",
        include_agent_ids: bool = True,
        include_owner_monitor: bool = True,
        include_preflight: bool = True,
        duplicate_agent_id: bool = False,
        bad_thread_title: bool = False,
    ) -> Path:
        gate_path = self.repo / path
        self._write(str((gate_path.parent / "manifest.yaml").relative_to(self.repo)).replace("\\", "/"), "schema_version: gtpj-manifest/v1\n")
        self._write(str((gate_path.parent / "agent_summary.md").relative_to(self.repo)).replace("\\", "/"), "# Agent Summary\n")
        self._write(str((gate_path.parent / "quality_check.md").relative_to(self.repo)).replace("\\", "/"), "# Quality\n")
        self._write(str((gate_path.parent / "TRANSITIONS.jsonl").relative_to(self.repo)).replace("\\", "/"), "")
        self._write(
            str((gate_path.parent / "AGENT_ACTIVITY.md").relative_to(self.repo)).replace("\\", "/"),
            "# Agent Activity\n"
            "runner_monitor 019f1111-1111-7111-8111-111111111111 running\n"
            "interface_checker 019f2222-2222-7222-8222-222222222222 completed\n"
            "evidence_quality_checker 019f3333-3333-7333-8333-333333333333 completed\n",
        )
        for role, instance_id in {
            "runner_monitor": "019f1111-1111-7111-8111-111111111111",
            "interface_checker": "019f2222-2222-7222-8222-222222222222",
            "evidence_quality_checker": "019f3333-3333-7333-8333-333333333333",
        }.items():
            self._write(
                str((gate_path.parent / "agent_outputs" / f"{role}.md").relative_to(self.repo)).replace("\\", "/"),
                f"# {role}\nrole_key: {role}\nthread_id: {instance_id}\noutput: {role} checked test gate.\n",
            )
        agent_ids = (
            "named_thread_ids:\n"
            "  runner_monitor: 019f1111-1111-7111-8111-111111111111\n"
            "  interface_checker: 019f2222-2222-7222-8222-222222222222\n"
            "  evidence_quality_checker: 019f3333-3333-7333-8333-333333333333\n"
        )
        if duplicate_agent_id:
            agent_ids = (
                "named_thread_ids:\n"
                "  runner_monitor: 019f1111-1111-7111-8111-111111111111\n"
                "  interface_checker: 019f2222-2222-7222-8222-222222222222\n"
                "  evidence_quality_checker: 019f2222-2222-7222-8222-222222222222\n"
            )
        if not include_agent_ids:
            agent_ids = "named_thread_ids:\n  runner_monitor: temporary_subagent\n"
        thread_titles = (
            "named_thread_titles:\n"
            "  runner_monitor: ATTEMPT-001 | Runner Monitor\n"
            "  interface_checker: ATTEMPT-001 | Interface Checker\n"
            "  evidence_quality_checker: ATTEMPT-001 | Evidence Quality Checker\n"
        )
        if bad_thread_title:
            thread_titles = (
                "named_thread_titles:\n"
                "  runner_monitor: Galileo\n"
                "  interface_checker: ATTEMPT-001 | Interface Checker\n"
                "  evidence_quality_checker: ATTEMPT-001 | Evidence Quality Checker\n"
            )
        owner_monitor = (
            "owner_monitor_mode: true\n"
            "owner_role: monitor\n"
            "owner_visible_reporting: true\n"
            "report_channel: current_conversation\n"
            "report_interval_minutes: 15\n"
            "agent_activity_stream: AGENT_ACTIVITY.md\n"
            "monitor_handoff_on_pause: required\n"
            "thread_archive_policy: archive_completed_threads_on_stage_end\n"
            "archive_completed_threads_on_stage_end: true\n"
            "archived_threads_record: AGENT_ACTIVITY.md\n"
        )
        if not include_owner_monitor:
            owner_monitor = ""
        preflight = (
            "multi_agent_preflight:\n"
            "  required_threads_created: true\n"
            "  agent_instance_ids_present: true\n"
            "  agent_status_refs_valid: true\n"
            "  independent_outputs_present: true\n"
            "  agent_output_refs_valid: true\n"
            "  pre_run_allow_checks_passed: true\n"
            "  agent_runtime_validated: true\n"
            "  threads_archivable: true\n"
        )
        if not include_preflight:
            preflight = ""
        self._write(
            path,
            "schema_version: gtpj.agent_runtime_gate.v0\n"
            "subject_id: ATTEMPT-001\n"
            "subject_type: attempt\n"
            "formal_evidence: true\n"
            "activation_mode: real_multi_agent\n"
            "agent_instance_mode: named_owner_thread\n"
            "lifecycle: workflow_scoped\n"
            "ui_visibility: left_sidebar_named_threads\n"
            "tool_support_real_multi_agent_available: true\n"
            "thread_management_tool: codex_app.create_thread\n"
            "single_agent_execution: false\n"
            "runner_start_allowed: true\n"
            "formal_runner_allowed: true\n"
            "formal_evidence_allowed: true\n"
            f"{owner_monitor}"
            f"{agent_ids}"
            f"{thread_titles}"
            "agent_instance_status:\n"
            "  runner_monitor: running\n"
            "  interface_checker: completed\n"
            "  evidence_quality_checker: completed\n"
            "agent_status_refs:\n"
            "  runner_monitor: AGENT_ACTIVITY.md\n"
            "  interface_checker: AGENT_ACTIVITY.md\n"
            "  evidence_quality_checker: AGENT_ACTIVITY.md\n"
            "agent_output_refs:\n"
            "  runner_monitor: agent_outputs/runner_monitor.md\n"
            "  interface_checker: agent_outputs/interface_checker.md\n"
            "  evidence_quality_checker: agent_outputs/evidence_quality_checker.md\n"
            "pre_run_required_checks:\n"
            f"  runner_monitor: {runner_decision}\n"
            "  interface_checker: allow\n"
            f"  evidence_quality_checker: {quality_decision}\n"
            f"{preflight}"
            "authority_refs:\n"
            "  manifest: manifest.yaml\n"
            "  agent_summary: agent_summary.md\n"
            "  quality_check: quality_check.md\n"
            "  transitions: TRANSITIONS.jsonl\n"
            "  agent_activity: AGENT_ACTIVITY.md\n",
        )
        return gate_path

    def _write_server_detached_formal_gate(
        self,
        *,
        path: str = "experiments/v1/tune/TUNE-001_ok/server_detached_agent_runtime.yaml",
        runner_decision: str = "allow",
        quality_decision: str = "allow",
    ) -> Path:
        gate_path = self.repo / path
        self._write(str((gate_path.parent / "manifest.yaml").relative_to(self.repo)).replace("\\", "/"), "schema_version: gtpj-manifest/v1\n")
        self._write(str((gate_path.parent / "agent_summary.md").relative_to(self.repo)).replace("\\", "/"), "# Agent Summary\n")
        self._write(str((gate_path.parent / "quality_check.md").relative_to(self.repo)).replace("\\", "/"), "# Quality\n")
        self._write(str((gate_path.parent / "TRANSITIONS.jsonl").relative_to(self.repo)).replace("\\", "/"), "")
        self._write(
            str((gate_path.parent / "AGENT_ACTIVITY.md").relative_to(self.repo)).replace("\\", "/"),
            "# Agent Activity\n"
            "current_owner_thread role_only formal server_detached\n",
        )
        for role in ("runner_monitor", "interface_checker", "evidence_quality_checker"):
            self._write(
                str((gate_path.parent / "agent_outputs" / f"{role}.md").relative_to(self.repo)).replace("\\", "/"),
                f"# {role}\nrole_key: {role}\nexecution_mode: role_only\noutput: {role} checked server_detached formal gate.\n",
            )
        self._write(
            path,
            "schema_version: gtpj.agent_runtime_gate.v0\n"
            "subject_id: ATTEMPT-011\n"
            "subject_type: attempt\n"
            "formal_evidence: true\n"
            "activation_mode: role_only\n"
            "agent_instance_mode: role_only\n"
            "lifecycle: server_detached_formal\n"
            "formal_runtime_backend: server_detached_role_only\n"
            "ui_visibility: current_owner_thread_only\n"
            "tool_support_real_multi_agent_available: true\n"
            "thread_management_tool: not_used\n"
            "single_agent_execution: true\n"
            "real_multi_agent_required: false\n"
            "thread_creation_allowed: false\n"
            "runner_start_allowed: true\n"
            "formal_runner_allowed: true\n"
            "formal_evidence_allowed: true\n"
            "owner_monitor_mode: true\n"
            "owner_role: monitor\n"
            "owner_visible_reporting: true\n"
            "report_channel: current_conversation\n"
            "report_interval_minutes: 15\n"
            "agent_activity_stream: AGENT_ACTIVITY.md\n"
            "monitor_handoff_on_pause: required\n"
            "thread_archive_policy: not_applicable_no_named_threads\n"
            "archive_completed_threads_on_stage_end: false\n"
            "archived_threads_record: AGENT_ACTIVITY.md\n"
            "agent_output_refs:\n"
            "  runner_monitor: agent_outputs/runner_monitor.md\n"
            "  interface_checker: agent_outputs/interface_checker.md\n"
            "  evidence_quality_checker: agent_outputs/evidence_quality_checker.md\n"
            "pre_run_required_checks:\n"
            f"  runner_monitor: {runner_decision}\n"
            "  interface_checker: allow\n"
            f"  evidence_quality_checker: {quality_decision}\n"
            "sequential_role_preflight:\n"
            "  role_plan_recorded: true\n"
            "  independent_outputs_present: true\n"
            "  pre_run_allow_checks_passed: true\n"
            "  agent_runtime_validated: true\n"
            "  server_detached_ready: true\n"
            "  stop_mechanism_ready: true\n"
            "  cleanup_not_required: true\n"
            "authority_refs:\n"
            "  manifest: manifest.yaml\n"
            "  agent_summary: agent_summary.md\n"
            "  quality_check: quality_check.md\n"
            "  transitions: TRANSITIONS.jsonl\n"
            "  agent_activity: AGENT_ACTIVITY.md\n",
        )
        return gate_path

    def _write_minimal_workflow_manifest(self) -> None:
        entries = [
            ("workflow_readme", "docs/workflow/README.md", "daily_entry", "active", False),
            ("manifest", "docs/workflow/WORKFLOW_MANIFEST.yaml", "daily_entry", "active", False),
            ("start_here", "docs/workflow/START_HERE.md", "daily_entry", "active", True),
            ("kernel", "docs/workflow/WORKFLOW_KERNEL.md", "daily_entry", "active", True),
            ("quick_start", "docs/workflow/core/QUICK_START.md", "core", "active", False),
            ("router", "docs/workflow/core/WORKFLOW_ROUTER.md", "core", "active", False),
            ("task_start_mini", "docs/workflow/core/TASK_START_MINI.md", "core", "active", False),
            ("task_start_card", "docs/workflow/core/TASK_START_CARD.md", "core", "active", False),
            ("agent_runtime_hard_gate", "docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "core", "active", False),
            ("agent_cleanup_protocol", "docs/workflow/protocols/agent_cleanup_protocol.md", "protocol", "active_reference", False),
            ("module_template_selection", "docs/workflow/protocols/module_template_selection.md", "protocol", "active_reference", False),
            ("ai_cross_review_protocol", "docs/workflow/protocols/ai_cross_review_protocol.md", "protocol", "active_reference", False),
            ("playbook_tune", "docs/workflow/playbooks/tune.md", "playbook", "active", False),
            ("playbook_ablation", "docs/workflow/playbooks/ablation.md", "playbook", "active", False),
            ("playbook_confirmation", "docs/workflow/playbooks/confirmation.md", "playbook", "active", False),
            ("playbook_innovation", "docs/workflow/playbooks/innovation.md", "playbook", "active", False),
            ("playbook_promotion", "docs/workflow/playbooks/promotion.md", "playbook", "active", False),
            ("playbook_mixed_campaign", "docs/workflow/playbooks/mixed_campaign.md", "playbook", "active", False),
            ("playbook_paper_intake", "docs/workflow/playbooks/paper_intake.md", "playbook", "active", False),
            ("playbook_paper_to_experiment", "docs/workflow/playbooks/paper_to_experiment.md", "playbook", "active", False),
        ]
        lines = ["workflow_version: v2", "files:"]
        for logical_id, path, category, status, daily_read in entries:
            lines.extend(
                [
                    f"  - logical_id: {logical_id}",
                    f"    canonical_path: {path}",
                    f"    category: {category}",
                    f"    status: {status}",
                    f"    daily_read: {str(daily_read).lower()}",
                ]
            )
        self._write("docs/workflow/WORKFLOW_MANIFEST.yaml", "\n".join(lines) + "\n")

    def test_required_files_include_owner_facing_start_docs(self) -> None:
        required = self.module.required_repository_files()

        self.assertIn("docs/workflow/core/QUICK_START.md", required)
        self.assertIn("docs/workflow/WORKFLOW_MANIFEST.yaml", required)
        self.assertIn("docs/workflow/core/TASK_START_MINI.md", required)
        self.assertIn("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", required)
        self.assertIn("docs/workflow/protocols/ai_cross_review_protocol.md", required)
        self.assertIn("experiments/templates/ai_cross_review_template.md", required)
        self.assertIn("experiments/templates/modules/standard_gzsl_training_template.py", required)
        self.assertIn("experiments/templates/modules/composite_module_template.py", required)
        self.assertIn("experiments/templates/modules/trial_meta_template.yaml", required)
        self.assertIn("experiments/templates/modules/architecture_change_template.md", required)

    def test_validate_trial_meta_accepts_safe_single_module(self) -> None:
        self._write(
            "trial_meta.yaml",
            """schema_version: gtpj.trial_meta.v0
trial_id: TRIAL-001
module_scope: single_module
template_family: feature_adapter
risk: normal
training_entry:
  mode: existing_entry_equivalent
  standard_template: experiments/templates/modules/standard_gzsl_training_template.py
  selected_entry: train_GTPJ_CUB.py
  legacy_module_migration: not_required
affects:
  forward_main_flow: false
  class_scoring: false
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false
baseline_off:
  supported: true
  expected_equivalence: v1
  all_switches_false_equals_base: true
audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
  split_integrity_audit: not_required
  class_order_audit: not_required
""",
        )

        code, stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")

        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout + stderr)
        self.assertIn("validate-trial-meta-ok", stdout)

    def test_validate_trial_meta_rejects_single_module_scoring_change(self) -> None:
        self._write(
            "trial_meta.yaml",
            """schema_version: gtpj.trial_meta.v0
trial_id: TRIAL-001
module_scope: single_module
template_family: feature_adapter
risk: normal
training_entry:
  mode: existing_entry_equivalent
  standard_template: experiments/templates/modules/standard_gzsl_training_template.py
  selected_entry: train_GTPJ_CUB.py
  legacy_module_migration: not_required
affects:
  forward_main_flow: false
  class_scoring: true
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false
baseline_off:
  supported: true
  expected_equivalence: v1
  all_switches_false_equals_base: true
audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
  split_integrity_audit: not_required
  class_order_audit: not_required
""",
        )

        code, _stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")

        self.assertEqual(1, code)
        self.assertIn("module_scope must be architecture_change", stderr)

    def test_validate_trial_meta_rejects_strict_mode_using_old_entry(self) -> None:
        self._write(
            "trial_meta.yaml",
            """schema_version: gtpj.trial_meta.v0
trial_id: TRIAL-001
module_scope: single_module
template_family: feature_adapter
risk: normal
training_entry:
  mode: strict_template_entry
  standard_template: experiments/templates/modules/standard_gzsl_training_template.py
  selected_entry: train_GTPJ_CUB.py
  legacy_module_migration: required
affects:
  forward_main_flow: false
  class_scoring: false
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false
baseline_off:
  supported: true
  expected_equivalence: v1
  all_switches_false_equals_base: true
audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
  split_integrity_audit: not_required
  class_order_audit: not_required
""",
        )

        code, _stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")

        self.assertEqual(1, code)
        self.assertIn("strict_template_entry must select a trial-local training entry", stderr)

    def test_validate_trial_meta_accepts_strict_template_entry(self) -> None:
        self._write(
            "trial_meta.yaml",
            """schema_version: gtpj.trial_meta.v0
trial_id: TRIAL-001
module_scope: single_module
template_family: feature_adapter
risk: normal
training_entry:
  mode: strict_template_entry
  standard_template: experiments/templates/modules/standard_gzsl_training_template.py
  selected_entry: training_entry.py
  legacy_module_migration: completed
affects:
  forward_main_flow: false
  class_scoring: false
  train_data_view: false
  eval_input_output: false
  split_or_label_mapping: false
baseline_off:
  supported: true
  expected_equivalence: v1
  all_switches_false_equals_base: true
audit:
  shape_audit: required
  switch_off_equivalence: required
  standard_gzsl_eval_audit: required
  split_integrity_audit: not_required
  class_order_audit: not_required
""",
        )

        code, stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")

        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout + stderr)
        self.assertIn("validate-trial-meta-ok", stdout)

    def test_scan_ignores_runtime_state(self) -> None:
        legacy_marker = "TUNE" + "-024"
        self._write(".gtpj_runtime/batches/old/summary.csv", f"legacy {legacy_marker} runtime evidence\n")
        self._write("docs/visible.md", "visible governance text\n")

        scanned = {path.relative_to(self.repo).as_posix() for path in self.module.list_files_for_scan()}

        self.assertIn("docs/visible.md", scanned)
        self.assertNotIn(".gtpj_runtime/batches/old/summary.csv", scanned)

    def test_framework_diagram_docs_reject_missing_version_docs(self) -> None:
        self._write(
            "experiments/v1/VERSION.md",
            "# GTPJ-v1\n\n## Version Flow\n\n```mermaid\nflowchart TD\n  A --> B\n```\n",
        )

        errors = self.module.validate_framework_diagram_docs()

        self.assertTrue(any("## Framework Diagram" in error for error in errors))
        self.assertTrue(any("framework_diagram.md is required" in error for error in errors))
        self.assertTrue(any("MODULES.md is required" in error for error in errors))

    def test_framework_diagram_docs_accept_complete_version_docs(self) -> None:
        self._write(
            "experiments/v1/VERSION.md",
            "# GTPJ-v1\n\n"
            "```text\n"
            "framework_diagram: experiments/v1/framework_diagram.md\n"
            "module_glossary: experiments/v1/MODULES.md\n"
            "```\n\n"
            "## Framework Diagram\n\n"
            "framework_diagram: framework_diagram.md\n"
            "module_glossary: MODULES.md\n\n"
            "## Version Flow\n\n"
            "```mermaid\nflowchart TD\n  A --> B\n```\n",
        )
        self._write(
            "experiments/v1/framework_diagram.md",
            "# Diagram\n\n"
            "## Main Forward Flow\n\n"
            "## Variable Glossary\n\n"
            "## Module Glossary\n\n"
            "## Loss And Training Flow\n\n"
            "## GZSL Hard Rules\n",
        )
        self._write(
            "experiments/v1/MODULES.md",
            "# Modules\n\n"
            "## Module Table\n\n"
            "| Module | Purpose | Input | Output | Config switch | Baseline-off behavior |\n"
            "|---|---|---|---|---|---|\n"
            "| A | test | x | y | switch | off |\n\n"
            "## Config Switches\n\n"
            "## Version Delta\n",
        )

        errors = self.module.validate_framework_diagram_docs()

        self.assertEqual([], errors)

    def test_repro_status_marks_best_observed_as_unconfirmed(self) -> None:
        self.module.CANONICAL_BASELINES["v2"] = {
            "name": "GTPJ-v2",
            "H": "74.29",
            "result_file": "experiments/v2/result.md",
            "version_file": "experiments/v2/VERSION.md",
            "evidence_level": "valid_single_run",
            "best_observed_H": "74.29",
            "confirmed_H": "pending",
            "confirmation_status": "needs_confirmation",
            "status": "owner_activated_unconfirmed",
        }

        code, stdout, stderr = self._run_main("repro-status", "--version", "v2")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("verdict: needs_confirmation", stdout)
        self.assertIn("comparison_reference: best_observed_H=74.29 (unconfirmed)", stdout)
        self.assertIn("can_claim_confirmed_baseline: no", stdout)

    def test_confirmation_grade_keep_sync_defaults_mark_attempt_confirmed(self) -> None:
        defaults = self.module.sync_evidence_defaults(
            decision="keep",
            metrics={"H": "74.24"},
            raw_evidence_level="confirmation_grade",
            promotion_decision="blocked",
        )

        self.assertEqual("confirmation_grade", defaults["evidence_level"])
        self.assertEqual("confirmed", defaults["result_status"])
        self.assertEqual("74.24", defaults["best_observed_H"])
        self.assertEqual("74.24", defaults["confirmed_H"])
        self.assertEqual("confirmed", defaults["confirmation_status"])
        self.assertEqual("blocked", defaults["promotion_decision"])

    def test_not_confirmed_sync_preserves_existing_trial_best(self) -> None:
        defaults = self.module.sync_evidence_defaults(
            decision="not_confirmed",
            metrics={"H": "73.79"},
            raw_evidence_level="quick_local",
            promotion_decision="not_applicable",
        )
        preserved = self.module.preserve_trial_best_observed_for_sync(
            defaults,
            {
                "evidence_level": "valid_single_run",
                "best_observed_H": "74.27",
                "confirmed_H": "pending",
                "confirmation_status": "needs_confirmation",
            },
            "not_confirmed",
        )

        self.assertEqual("not_confirmed", preserved["result_status"])
        self.assertEqual("valid_single_run", preserved["evidence_level"])
        self.assertEqual("74.27", preserved["best_observed_H"])
        self.assertEqual("pending", preserved["confirmed_H"])
        self.assertEqual("needs_confirmation", preserved["confirmation_status"])
        self.assertEqual("blocked", preserved["promotion_decision"])

    def test_start_open_new_module_outputs_mini_card_without_writing(self) -> None:
        self._write_selected_idea_files()
        idea_before = (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8")
        version_before = (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8")

        code, stdout, stderr = self._run_main("start", "--phrase", "开新模块")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 开新模块", stdout)
        self.assertIn("task_type: innovation / module trial", stdout)
        self.assertIn("base_version: v1", stdout)
        self.assertIn("target: IDEA-0001 Token Router", stdout)
        self.assertIn("writes: idea_tree + experiments/module_trials + Warehouse after run", stdout)
        self.assertIn("agent_mode: real_multi_agent", stdout)
        self.assertIn("Review 0-3", stdout)
        self.assertIn("next_action: create dev/v1-idea-0001-trial-001-token-router branch and trial record after owner approval", stdout)
        self.assertFalse((self.repo / "experiments/module_trials/IDEA-0001_token_router").exists())
        self.assertEqual(idea_before, (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8"))
        self.assertEqual(version_before, (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8"))

    def test_start_routes_paper_intake_phrase_without_writing(self) -> None:
        idea_before = (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8")
        version_before = (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8")

        code, stdout, stderr = self._run_main("start", "--phrase", "读论文")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 读论文", stdout)
        self.assertIn("task_type: paper intake / idea discovery", stdout)
        self.assertIn("playbook: docs/workflow/playbooks/paper_intake.md", stdout)
        self.assertIn("closed_loop: paper_inbox -> paper_index -> source_review -> extracted_ideas -> idea_tree_sync_check", stdout)
        self.assertIn("formal_runner_allowed: false", stdout)
        self.assertIn("next_action: scan GTPJ_Research/papers/_inbox and PAPERS_INDEX.md; do not run training", stdout)
        self.assertEqual(idea_before, (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8"))
        self.assertEqual(version_before, (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8"))

    def test_start_blocks_paper_to_experiment_without_base_version(self) -> None:
        idea_before = (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8")
        version_before = (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8")

        code, stdout, stderr = self._run_main("start", "--phrase", "从论文开始")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 从论文开始", stdout)
        self.assertIn("task_type: paper -> idea -> module trial closed loop", stdout)
        self.assertIn("base_version: missing", stdout)
        self.assertIn("base_code_tag: missing", stdout)
        self.assertIn("playbook: docs/workflow/playbooks/paper_to_experiment.md", stdout)
        self.assertIn("blocked_missing_base_version", stdout)
        self.assertIn("formal_runner_allowed: false", stdout)
        self.assertIn("blocked_reason: missing_base_code_version; paper-to-experiment cannot default to current active version", stdout)
        self.assertIn("next_action: ask owner for base version, e.g. 基于 v5 从论文开始做实验", stdout)
        self.assertEqual(idea_before, (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8"))
        self.assertEqual(version_before, (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8"))

    def test_start_routes_paper_to_experiment_with_explicit_base_version(self) -> None:
        code, stdout, stderr = self._run_main("start", "--phrase", "基于 v1 从论文开始做实验")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 基于 v1 从论文开始做实验", stdout)
        self.assertIn("task_type: paper -> idea -> module trial closed loop", stdout)
        self.assertIn("base_version: v1", stdout)
        self.assertIn("base_code_tag: v1", stdout)
        self.assertIn("playbook: docs/workflow/playbooks/paper_to_experiment.md", stdout)
        self.assertIn(
            "closed_loop: paper_inbox -> source_review -> idea_candidate -> formal_IDEA -> selected_queue -> trial_preflight -> runner_evidence -> idea_feedback",
            stdout,
        )
        self.assertIn("module_template_family", stdout)
        self.assertIn("module_source", stdout)
        self.assertIn("standard_gzsl", stdout)
        self.assertIn("formal_runner_allowed: false until agent_runtime and multi_agent_preflight pass", stdout)

    def test_start_auto_routes_mixed_experiment_phrase_to_closed_loop_campaign(self) -> None:
        code, stdout, stderr = self._run_main("start", "--phrase", "跑2创新+8调参")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 跑2创新+8调参", stdout)
        self.assertIn("task_type: mixed experiment campaign", stdout)
        self.assertIn("requested_mix: innovation=2, tune=8", stdout)
        self.assertIn("playbook: docs/workflow/playbooks/mixed_campaign.md", stdout)
        self.assertIn("daily_read_chain: START_HERE.md -> WORKFLOW_KERNEL.md -> playbooks/mixed_campaign.md", stdout)
        self.assertIn("closed_loop: plan -> agent_runtime -> preflight -> runner -> evidence -> cleanup -> sync", stdout)
        self.assertIn("next_action: create campaign manifest and agent_runtime.yaml after owner approval", stdout)

    def test_start_routes_generic_experiment_planning_phrase(self) -> None:
        code, stdout, stderr = self._run_main("start", "--phrase", "规划下一轮实验")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("owner_phrase: 规划下一轮实验", stdout)
        self.assertIn("task_type: experiment planning", stdout)
        self.assertIn("runner_scope: none", stdout)
        self.assertIn("next_action: run plan-experiments", stdout)

    def test_plan_experiments_auto_scans_state_without_writing(self) -> None:
        idea_before = (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8")

        code, stdout, stderr = self._run_main("plan-experiments", "--phrase", "调参", "--max-jobs", "3")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("experiment_planning_gate: EXPPLAN-", stdout)
        self.assertIn("auto_state_scan:", stdout)
        self.assertIn("baseline_repro_status:", stdout)
        self.assertIn("## Evidence Summary", stdout)
        self.assertIn("## Candidate Decision", stdout)
        self.assertIn("## Current Run Plan", stdout)
        self.assertIn("TUNE-001", stdout)
        self.assertIn("changed_config_not_exact_repeat", stdout)
        self.assertIn("runner_start_allowed: false", stdout)
        self.assertEqual(idea_before, (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8"))

    def test_plan_experiments_reads_formal_pending_ledger_rows(self) -> None:
        self._write(
            "experiments/v1/tune/INDEX.md",
            "# Tune Index\n\n| 实验 | 状态 | 目录 | 说明 |\n"
            "|---|---|---|---|\n"
            "| `TUNE-777_pending` | planned | `experiments/v1/tune/TUNE-777_pending` | formal_pending |\n",
        )

        code, stdout, stderr = self._run_main("plan-experiments", "--phrase", "调参")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("formal_pending_count: 1", stdout)
        self.assertIn("TUNE-777_pending", stdout)
        self.assertIn("formal_pending", stdout)

    def test_plan_experiments_extracts_budget_from_generic_phrase(self) -> None:
        code, stdout, stderr = self._run_main("plan-experiments", "--phrase", "批量规划50轮实验")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("task_type: experiment planning", stdout)
        self.assertIn("requested_budget_jobs: 50", stdout)
        self.assertIn("max 50 jobs after type is resolved", stdout)
        self.assertIn("runner_start_allowed: false", stdout)

    def test_plan_experiments_routes_mixed_common_planning_phrase(self) -> None:
        code, stdout, stderr = self._run_main("plan-experiments", "--phrase", "规划2创新+8调参")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("task_type: mixed experiment campaign", stdout)
        self.assertIn("| INNOV | innovation |", stdout)
        self.assertIn("| TUNE | tune |", stdout)
        self.assertIn("runner_start_allowed: false", stdout)

    def test_closeout_check_accepts_synced_module_trial_loop_without_writing(self) -> None:
        idea = self._write_selected_idea_files()
        trial_dir = "experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router"
        artifact_rel = "runs/v1/module_trial/TRIAL-001/attempt-001/logs/train.log"
        artifact_uri = f"warehouse://gtpj/{artifact_rel}"
        artifact_bytes = b"raw log\n"
        artifact_sha = hashlib.sha256(artifact_bytes).hexdigest()
        artifact_size = str(len(artifact_bytes))
        warehouse_root = self.repo / "warehouse"
        artifact_path = warehouse_root / artifact_rel
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_bytes(artifact_bytes)
        self._write(".gtpj/local_paths.yaml", f"warehouse_root: {warehouse_root.as_posix()}\n")
        idea["linked_trials"] = [trial_dir]
        idea["evidence"] = [{"type": "trial", "ref": f"{trial_dir}/result.yaml", "note": "synced"}]
        self._write_idea_tree([idea])
        self._write(
            "experiments/module_trials/INDEX.md",
            "# Module Trials Index\n\n"
            "| Idea | Source idea file | Trial evidence directory | Trial status | Summary |\n"
            "|---|---|---|---|---|\n"
            f"| `IDEA-0001` | `idea_tree/ideas/IDEA-0001_token_router/IDEA.md` | `{trial_dir}` | keep | synced |\n",
        )
        self._write(
            f"{trial_dir}/README.md",
            f"""# TRIAL-001_token_router

```text
trial_id: TRIAL-001
idea_id: IDEA-0001
base_version: v1
base_code_tag: v1
idea_source_file: idea_tree/ideas/IDEA-0001_token_router/IDEA.md
trial_decision: keep
log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-001
log_uri: {artifact_uri}
log_sha256: {artifact_sha}
log_size_bytes: {artifact_size}
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
```

## Trial Flow

```mermaid
flowchart TD
  Idea --> Run
```
""",
        )
        self._write(
            f"{trial_dir}/ATTEMPTS.md",
            "# Attempts\n\n| Attempt | Decision | Log |\n|---|---|---|\n"
            "| ATTEMPT-001 | keep | log:v1:module_trial:TRIAL-001:attempt-001 |\n",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-001/manifest.yaml",
            f"""schema_version: gtpj-manifest/v1
experiment:
  id: "TRIAL-001"
  kind: "module-trial"
version:
  base_version: "v1"
  code_commit: "abc123"
  git_dirty: "false"
reproducibility:
  config_file: "{trial_dir}/attempts/ATTEMPT-001/config.yaml"
  config_sha256: "sha-config"
  pre_run_freeze_commit: "abc123"
  command: "python train_GTPJ_CUB.py --config config.yaml"
  seed: "5"
artifacts:
  train_log:
    artifact_id: "log:v1:module_trial:TRIAL-001:attempt-001"
    role: "training_log"
    uri: "{artifact_uri}"
    sha256: "{artifact_sha}"
    size_bytes: "{artifact_size}"
    status: "available"
""",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-001/result.yaml",
            """schema_version: gtpj-result/v1
experiment_id: "TRIAL-001"
kind: "module-trial"
version: "v1"
attempt_id: "ATTEMPT-001"
metrics:
  U: "70.00"
  S: "72.00"
  H: "70.99"
  ZS: "80.00"
  best_epoch: "12"
  seed: "5"
decision:
  status: "keep"
evidence:
  evidence_level: "valid_single_run"
""",
        )
        self._write(
            f"{trial_dir}/manifest.yaml",
            f"""schema_version: gtpj-manifest/v1
experiment:
  id: "TRIAL-001"
  attempt_id: "ATTEMPT-001"
version:
  base_version: "v1"
artifacts:
  train_log:
    artifact_id: "log:v1:module_trial:TRIAL-001:attempt-001"
    role: "training_log"
    uri: "{artifact_uri}"
    sha256: "{artifact_sha}"
    size_bytes: "{artifact_size}"
    status: "available"
""",
        )
        self._write(
            f"{trial_dir}/result.yaml",
            """schema_version: gtpj-result/v1
experiment_id: "TRIAL-001"
kind: "module-trial"
version: "v1"
attempt_id: "ATTEMPT-001"
evidence:
  attempt_manifest: "attempts/ATTEMPT-001/manifest.yaml"
  train_log_artifact_id: "log:v1:module_trial:TRIAL-001:attempt-001"
""",
        )
        self._write(f"{trial_dir}/result.md", "# Result\n\nATTEMPT-001\n")
        self._write(f"{trial_dir}/quality_check.md", "# Quality\n\nATTEMPT-001\n")
        self._write(
            f"{trial_dir}/review_round_2.md",
            """# Review 3

```text
attempt_id: ATTEMPT-001
decision: keep
```

log:v1:module_trial:TRIAL-001:attempt-001
""",
        )
        self._write(
            f"{trial_dir}/agent_summary.md",
            """# Agent Summary

```text
attempt_id: ATTEMPT-001
final_decision: keep
```

log:v1:module_trial:TRIAL-001:attempt-001
""",
        )
        readme_before = (self.repo / trial_dir / "README.md").read_text(encoding="utf-8")
        index_before = (self.repo / "experiments/module_trials/INDEX.md").read_text(encoding="utf-8")

        code, stdout, stderr = self._run_main(
            "closeout-check",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-001",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("closeout-check-ok", stdout)
        self.assertIn("attempt: ok", stdout)
        self.assertIn("trial_root: ok", stdout)
        self.assertIn("review_round_2: ok", stdout)
        self.assertIn("agent_summary: ok", stdout)
        self.assertIn("module_index: ok", stdout)
        self.assertIn("idea_tree: ok", stdout)
        self.assertIn("warehouse_artifacts: ok", stdout)
        self.assertEqual(readme_before, (self.repo / trial_dir / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(index_before, (self.repo / "experiments/module_trials/INDEX.md").read_text(encoding="utf-8"))

    def test_validate_idea_tree_data_rejects_missing_ideas_list(self) -> None:
        with self.assertRaisesRegex(self.module.WorkflowError, "ideas must be a list"):
            self.module.validate_idea_tree_data(
                {"project": "GTPJ", "version": "test", "current_version": "v1"}
            )

    def test_validate_idea_tree_data_rejects_invalid_idea_status(self) -> None:
        idea = self._selected_idea()
        idea["status"] = "ready-ish"

        with self.assertRaisesRegex(self.module.WorkflowError, "invalid status"):
            self.module.validate_idea_tree_data(
                {"project": "GTPJ", "version": "test", "current_version": "v1", "ideas": [idea]}
            )

    def test_new_idea_refreshes_global_and_version_views(self) -> None:
        code, stdout, stderr = self._run_main(
            "new-idea",
            "--idea-id",
            "IDEA-0001",
            "--slug",
            "token_router",
            "--title",
            "Token Router",
            "--source-type",
            "paper",
            "--source-ref",
            "paper-x",
            "--source-status",
            "verified",
            "--base-version",
            "v1",
            "--global-score",
            "80",
            "--version-score",
            "60",
            "--applicability",
            "direct",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("已创建 idea_tree/ideas/IDEA-0001_token_router", stdout)
        idea_json = (self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8")
        global_index = (self.repo / "idea_tree/INDEX.md").read_text(encoding="utf-8")
        v1_view = (self.repo / "idea_tree/versions/v1.md").read_text(encoding="utf-8")
        self.assertIn('"stage": "candidate"', idea_json)
        self.assertIn('"core_summary": ""', idea_json)
        self.assertIn("总创意清单", global_index)
        self.assertIn("主要内容", global_index)
        self.assertNotIn("下一步", global_index)
        self.assertIn("IDEA-0001_token_router/IDEA.md", global_index)
        self.assertIn("v1 创意选择清单", v1_view)
        self.assertIn("版本适配说明", v1_view)
        self.assertIn("IDEA-0001_token_router/IDEA.md", v1_view)

    def test_todo_status_reports_queue_state(self) -> None:
        code, stdout, stderr = self._run_main("todo-status")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("todo-status", stdout)
        self.assertIn("source: idea_tree/queues/queue_state.yaml", stdout)
        self.assertIn("focus: test focus", stdout)
        self.assertIn("current_actions: 1 open / 1 total", stdout)

    def test_refresh_todo_writes_owner_views_from_queue_state(self) -> None:
        code, stdout, stderr = self._run_main("refresh-todo")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("refresh-todo-ok", stdout)
        next_actions = (self.repo / "NEXT_ACTIONS.md").read_text(encoding="utf-8")
        candidates = (self.repo / "idea_tree/queues/02_module_candidates.md").read_text(encoding="utf-8")
        tuning = (self.repo / "idea_tree/queues/04_tuning_questions.md").read_text(encoding="utf-8")
        self.assertIn("GTPJ 当前待办", next_actions)
        self.assertIn("Run queue smoke.", next_actions)
        self.assertIn("queue_state.yaml", candidates)
        self.assertNotIn("下一步 |", candidates)
        self.assertIn("experiments/vX/tune/", tuning)
        self.assertNotIn("experiments/v1/tune/", tuning)

    def test_new_trial_requires_explicit_selected_version_stage(self) -> None:
        self._write_selected_idea_files(stage=None)

        code, _stdout, stderr = self._run_main(
            "new-trial",
            "--idea-id",
            "IDEA-0001",
            "--trial-id",
            "TRIAL-001",
            "--slug",
            "token_router",
            "--base-version",
            "v1",
        )

        self.assertEqual(1, code)
        self.assertIn("must be selected in idea_tree/versions/v1.md", stderr)
        self.assertFalse((self.repo / "experiments/module_trials/IDEA-0001_token_router").exists())

    def test_new_trial_rejects_main_branch(self) -> None:
        self._write_selected_idea_files()

        code, _stdout, stderr = self._run_main(
            "new-trial",
            "--idea-id",
            "IDEA-0001",
            "--trial-id",
            "TRIAL-001",
            "--slug",
            "token_router",
            "--base-version",
            "v1",
        )

        self.assertEqual(1, code)
        self.assertIn("expected branch dev/v1-idea-0001-trial-001-token-router", stderr)
        self.assertFalse((self.repo / "experiments/module_trials/IDEA-0001_token_router").exists())

    def test_new_trial_rejects_dirty_expected_branch(self) -> None:
        self._write_selected_idea_files()
        self._git("add", ".")
        self._git("commit", "-m", "select idea")
        self._git("switch", "-c", "dev/v1-idea-0001-trial-001-token-router")
        self._write("scratch.txt", "dirty\n")

        code, _stdout, stderr = self._run_main(
            "new-trial",
            "--idea-id",
            "IDEA-0001",
            "--trial-id",
            "TRIAL-001",
            "--slug",
            "token_router",
            "--base-version",
            "v1",
        )

        self.assertEqual(1, code)
        self.assertIn("Working tree must be clean", stderr)
        self.assertFalse((self.repo / "experiments/module_trials/IDEA-0001_token_router").exists())

    def test_new_trial_rejects_expected_branch_not_based_on_main(self) -> None:
        self._write_selected_idea_files()
        self._git("add", ".")
        self._git("commit", "-m", "select idea")
        self._git("checkout", "--orphan", "dev/v1-idea-0001-trial-001-token-router")
        self._git("commit", "-m", "orphan trial branch")

        code, _stdout, stderr = self._run_main(
            "new-trial",
            "--idea-id",
            "IDEA-0001",
            "--trial-id",
            "TRIAL-001",
            "--slug",
            "token_router",
            "--base-version",
            "v1",
        )

        self.assertEqual(1, code)
        self.assertIn("new-trial branch must contain current local main", stderr)
        self.assertFalse((self.repo / "experiments/module_trials/IDEA-0001_token_router").exists())

    def test_new_trial_creates_framework_diagram_entrypoint(self) -> None:
        self._write_selected_idea_files()
        self._write(
            "experiments/module_trials/INDEX.md",
            "# Module Trials Index\n\n当前还没有已经启动的模块 trial。\n",
        )
        self._git("add", ".")
        self._git("commit", "-m", "select idea")
        self._git("switch", "-c", "dev/v1-idea-0001-trial-001-token-router")

        code, stdout, stderr = self._run_main(
            "new-trial",
            "--idea-id",
            "IDEA-0001",
            "--trial-id",
            "TRIAL-001",
            "--slug",
            "token_router",
            "--base-version",
            "v1",
        )

        trial_dir = self.repo / "experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router"
        readme = (trial_dir / "README.md").read_text(encoding="utf-8")
        framework = (trial_dir / "framework_diagram.md").read_text(encoding="utf-8")
        module_source = (trial_dir / "module_source.md").read_text(encoding="utf-8")
        trial_meta = (trial_dir / "trial_meta.yaml").read_text(encoding="utf-8")
        implementation = (trial_dir / "implementation.md").read_text(encoding="utf-8")
        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("已创建 experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router", stdout)
        self.assertIn("module_source: module_source.md", readme)
        self.assertIn("trial_meta: trial_meta.yaml", readme)
        self.assertIn("module_template_family:", readme)
        self.assertIn("module_scope:", readme)
        self.assertIn("composition_mode:", readme)
        self.assertIn("standard_gzsl_framework: experiments/templates/modules/standard_gzsl_module_framework_template.py", readme)
        self.assertIn("standard_gzsl_training_template: experiments/templates/modules/standard_gzsl_training_template.py", readme)
        self.assertIn("template_family:", module_source)
        self.assertIn("trial_meta: trial_meta.yaml", module_source)
        self.assertIn("module_scope:", module_source)
        self.assertIn("composition_mode:", module_source)
        self.assertIn("affects:", module_source)
        self.assertIn("schema_version: gtpj.trial_meta.v0", trial_meta)
        self.assertIn("module_scope: single_module", trial_meta)
        self.assertIn("training_entry:", trial_meta)
        self.assertIn("mode: existing_entry_equivalent", trial_meta)
        self.assertIn("selected_entry: train_GTPJ_CUB.py", trial_meta)
        self.assertIn("affects:", trial_meta)
        self.assertIn("paper_writing_note:", module_source)
        self.assertIn("standard GZSL U/S/H/ZS", module_source)
        self.assertIn("training_entry_mode: existing_entry_equivalent", module_source)
        self.assertIn("Template Selection", implementation)
        self.assertIn("trial_meta: trial_meta.yaml", implementation)
        self.assertIn("module_scope", implementation)
        self.assertIn("composition_mode", implementation)
        self.assertIn("affects", implementation)
        self.assertIn("training_entry_mode: existing_entry_equivalent", implementation)
        self.assertIn("standard_gzsl_training_template.py", implementation)
        self.assertIn("module_template_selection.md", implementation)
        self.assertIn("framework_diagram: framework_diagram.md", readme)
        self.assertIn("## Framework Diagram", readme)
        self.assertIn("## Variable Glossary", framework)
        self.assertIn("## Method Glossary", framework)
        self.assertIn("## Loss Flow", framework)
        self.assertIn("## Code vs Intent", framework)

    def test_new_experiment_rejects_main_branch(self) -> None:
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("expected branch exp/v1-confirm-001-v1-seed5", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_dirty_worktree(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-001-v1-seed5")
        self._write("scratch.txt", "dirty\n")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("Working tree must be clean", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_wrong_exp_branch(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-999-other")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("expected branch exp/v1-confirm-001-v1-seed5", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_expected_branch_not_based_on_main(self) -> None:
        self._git("checkout", "--orphan", "exp/v1-confirm-001-v1-seed5")
        self._git("commit", "-m", "orphan experiment branch")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("new-experiment branch must contain current local main", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_succeeds_on_expected_clean_branch(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-001-v1-seed5")

        code, stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("已创建 experiments/v1/confirmation/CONFIRM-001_v1_seed5", stdout)
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/README.md").exists())
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/manifest.yaml").exists())
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/result.yaml").exists())
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/result.md").exists())
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/agent_summary.md").exists())
        confirmation_index = self._confirmation_index_text()
        self.assertIn("| 实验 | 状态 | Run ID | Formal | 目录 | 说明 |", confirmation_index)
        self.assertIn("formal_pending", confirmation_index)

    def test_tune_suggest_lists_at_most_three_candidates_without_writing(self) -> None:
        index_before = self._tune_index_text()
        registry_before = self._registry_text()

        code, stdout, stderr = self._run_main("tune-suggest", "--version", "v1")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertEqual(3, stdout.count("parameter:"))
        self.assertIn("conditional_text_ratio", stdout)
        self.assertIn("lambda_topo_pearson", stdout)
        self.assertIn("adapter_ratio", stdout)
        self.assertIn("用户选择 1 个候选后再运行", stdout)
        self.assertEqual(index_before, self._tune_index_text())
        self.assertEqual(registry_before, self._registry_text())

    def test_dynamic_routing_batch_plan_has_balanced_aggressive_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5)
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)

        self.assertEqual(len(jobs), 50)
        self.assertEqual(groups["sanity_control"], 4)
        self.assertEqual(groups["local_gate"], 8)
        self.assertEqual(groups["icsa_gate"], 8)
        self.assertEqual(groups["direction_gate"], 6)
        self.assertEqual(groups["pse_gate"], 6)
        self.assertEqual(groups["combination"], 8)
        self.assertEqual(groups["top2_frozen_repeat"], 10)
        self.assertEqual(phases["explore"], 40)
        self.assertEqual(phases["repeat"], 10)
        self.assertEqual(jobs[0]["config_updates"]["use_dynamic_routing"], False)
        self.assertTrue(all(job["seed"] == 5 for job in jobs[:40]))
        self.assertEqual({job["source_rank"] for job in jobs[40:]}, {1, 2})

    def test_dynamic_routing_batch_plan_has_principled_followup_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=7, profile="principled-followup")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        repeat_ranks = Counter(job["source_rank"] for job in jobs if job["phase"] == "repeat")
        explore_updates = [job["config_updates"] for job in jobs if job["phase"] == "explore"]

        self.assertEqual(len(jobs), 50)
        self.assertEqual(groups["sanity_control"], 4)
        self.assertEqual(groups["direction_gate"], 12)
        self.assertEqual(groups["local_gate"], 8)
        self.assertEqual(groups["pse_gate"], 8)
        self.assertEqual(groups["combination"], 8)
        self.assertEqual(groups["top3_frozen_repeat"], 10)
        self.assertEqual(phases["explore"], 40)
        self.assertEqual(phases["repeat"], 10)
        self.assertEqual(repeat_ranks, Counter({1: 4, 2: 3, 3: 3}))
        self.assertTrue(all(job["seed"] == 7 for job in jobs))
        self.assertTrue(
            all(update.get("dynamic_icsa_mode", "fixed") == "fixed" for update in explore_updates)
        )
        self.assertTrue(
            any(
                update.get("dynamic_direction_mode") == "sample"
                and update.get("dynamic_gate_anchor_lambda") == 0.005
                for update in explore_updates
            )
        )
        self.assertTrue(any(update.get("local_weight") == 0.08 for update in explore_updates))
        self.assertTrue(any(update.get("pse_outer_ratio") == 0.55 for update in explore_updates))

    def test_dynamic_routing_batch_plan_has_direction_repeat_confirmation_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="direction-repeat-confirmation")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        names = Counter(job["name"].rsplit("_r", 1)[0] for job in jobs)

        self.assertEqual(len(jobs), 50)
        self.assertEqual(groups["direction_confirmation"], 5)
        self.assertEqual(groups["direction_neighbor"], 10)
        self.assertEqual(groups["direction_local_refine"], 25)
        self.assertEqual(groups["sanity_control"], 10)
        self.assertEqual(phases["explore"], 50)
        self.assertNotIn("repeat", phases)
        self.assertEqual(names["dr009_direction_sample_h48_w0.45_a0.005"], 5)
        self.assertEqual(names["dr008_direction_sample_h48_w0.5_a0.005"], 5)
        self.assertEqual(names["dr010_direction_sample_h64_w0.5_a0.01"], 5)
        self.assertTrue(all(job["seed"] == 5 for job in jobs))
        target_updates = jobs[0]["config_updates"]
        self.assertEqual(target_updates["dynamic_direction_mode"], "sample")
        self.assertEqual(target_updates["dynamic_gate_hidden"], 48)
        self.assertEqual(target_updates["dynamic_gate_anchor_lambda"], 0.005)
        self.assertEqual(target_updates["weight_s2v"], 0.45)
        self.assertEqual(target_updates.get("dynamic_icsa_mode"), "fixed")

    def test_dynamic_routing_batch_plan_has_direction_exploit_followup_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="direction-exploit-followup")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        names = Counter(job["name"].rsplit("_r", 1)[0] for job in jobs)

        self.assertEqual(len(jobs), 50)
        self.assertEqual(phases["explore"], 50)
        self.assertEqual(groups["must_reproduce"], 11)
        self.assertEqual(groups["direction_microgrid"], 25)
        self.assertEqual(groups["local_direction_micro"], 6)
        self.assertEqual(groups["direction_pse_micro"], 6)
        self.assertEqual(names["dr009_direction_sample_h48_w0.45_a0.005"], 5)
        self.assertEqual(names["dr008_direction_sample_h48_w0.5_a0.005"], 3)
        self.assertEqual(names["dr010_direction_sample_h64_w0.5_a0.01"], 3)
        self.assertTrue(all(job["seed"] == 5 for job in jobs))

    def test_dynamic_routing_batch_plan_has_best_repro_tune_followup_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="best-repro-tune-followup")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        names = Counter(job["name"].rsplit("_r", 1)[0] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 50)
        self.assertEqual(phases["explore"], 50)
        self.assertEqual(groups["must_reproduce"], 10)
        self.assertEqual(groups["direction_repro_tune"], 20)
        self.assertEqual(groups["local_repro_tune"], 8)
        self.assertEqual(groups["pse_repro_tune"], 6)
        self.assertEqual(groups["combination_repro_tune"], 6)
        self.assertEqual(names["static_v5_control"], 3)
        self.assertEqual(names["dr008_local_class_h24_a0.001"], 3)
        self.assertEqual(names["dr023_direction_sample_h48_a0.003"], 3)
        self.assertTrue(all(job["seed"] == 5 for job in jobs))
        self.assertFalse(any("copy_from_top_rank" in update for update in updates))
        self.assertTrue(all(update.get("dynamic_icsa_mode", "fixed") == "fixed" for update in updates))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(any(update.get("weight_s2v") == 0.45 for update in updates))
        self.assertTrue(any(update.get("local_weight") == 0.12 for update in updates))
        self.assertTrue(any(update.get("pse_outer_ratio") == 0.55 for update in updates))

    def test_dynamic_routing_batch_plan_has_dr018_confirm_ablate_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=9, profile="dr018-confirm-ablate")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        names = Counter(job["name"].rsplit("_r", 1)[0] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 50)
        self.assertEqual(phases["explore"], 50)
        self.assertEqual(groups["confirm_dr018"], 4)
        self.assertEqual(groups["neighbor_repeat"], 8)
        self.assertEqual(groups["ablate_direction"], 10)
        self.assertEqual(groups["direction_narrow_tune"], 22)
        self.assertEqual(groups["innovation_combo_probe"], 6)
        self.assertEqual(names["dr018_direction_sample_h48_w0.5_a0.003"], 4)
        self.assertEqual(names["dr019_direction_sample_h48_w0.5_a0.005"], 3)
        self.assertEqual(names["dr016_direction_sample_h48_w0.45_a0.003"], 2)
        self.assertEqual(names["dr023_direction_sample_h48_a0.003"], 3)
        self.assertEqual(names["fixed_direction_h48_w0.5_a0.003"], 3)
        self.assertEqual(names["static_v5_control"], 3)
        self.assertEqual(names["dynamic_fixed_all"], 2)
        self.assertTrue(all(job["seed"] == 9 for job in jobs))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(
            any(
                update.get("dynamic_direction_mode") == "sample"
                and update.get("dynamic_gate_hidden") == 48
                and update.get("dynamic_gate_anchor_lambda") == 0.003
                and update.get("weight_s2v") == 0.50
                for update in updates
            )
        )
        self.assertTrue(any(update.get("dynamic_direction_mode") == "fixed" for update in updates))
        self.assertTrue(any(update.get("weight_s2v") == 0.475 for update in updates))
        self.assertTrue(any(update.get("dynamic_gate_anchor_lambda") == 0.004 for update in updates))
        self.assertTrue(any(update.get("pse_outer_ratio") == 0.55 for update in updates))
        self.assertTrue(any(update.get("local_weight") == 0.06 for update in updates))

    def test_dynamic_routing_batch_plan_has_dr035_min3_confirm_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="dr035-min3-confirm")
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 3)
        self.assertEqual([job["job_id"] for job in jobs], ["DR-001", "DR-002", "DR-003"])
        self.assertEqual([job["group"] for job in jobs], ["confirm_dr035"] * 3)
        self.assertEqual([job["phase"] for job in jobs], ["explore"] * 3)
        self.assertEqual([job["seed"] for job in jobs], [5, 5, 5])
        self.assertEqual([update["random_seed"] for update in updates], [5, 5, 5])
        self.assertEqual(
            [job["name"] for job in jobs],
            [
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r1",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r2",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r3",
            ],
        )
        self.assertTrue(all(update["use_dynamic_routing"] for update in updates))
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))
        self.assertTrue(all(update["dynamic_gate_anchor_lambda"] == 0.005 for update in updates))
        self.assertTrue(all(update["weight_s2v"] == 0.525 for update in updates))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})

    def test_dynamic_routing_batch_plan_has_dr035_max5_confirm_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="dr035-max5-confirm")
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 5)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 6)])
        self.assertEqual([job["group"] for job in jobs], ["confirm_dr035"] * 5)
        self.assertEqual([job["phase"] for job in jobs], ["explore"] * 5)
        self.assertEqual([job["seed"] for job in jobs], [5] * 5)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 5)
        self.assertEqual(
            [job["name"] for job in jobs],
            [
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r1",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r2",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r3",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r4",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r5",
            ],
        )
        self.assertTrue(all(update["use_dynamic_routing"] for update in updates))
        self.assertTrue(all(update["dynamic_local_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_icsa_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_pse_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))
        self.assertTrue(all(update["dynamic_gate_anchor_lambda"] == 0.005 for update in updates))
        self.assertTrue(all(update["weight_s2v"] == 0.525 for update in updates))

    def test_dynamic_routing_batch_rejects_dr035_min6_confirm_profile(self) -> None:
        with self.assertRaisesRegex(self.module.WorkflowError, "max_attempts: 5"):
            self.module.build_dynamic_routing_jobs(seed=99, profile="dr035-min6-confirm")

    def test_exact_repeat_hard_cap_rejects_more_than_five_same_config_runs(self) -> None:
        with self.assertRaisesRegex(self.module.WorkflowError, "max_attempts: 5"):
            self.module._dr035_confirm_specs(6)

    def test_dynamic_routing_batch_plan_has_h76_existing_routing_100_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="h76-existing-routing-100")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 100)
        self.assertEqual(phases["explore"], 100)
        self.assertEqual(groups["sanity_control"], 4)
        self.assertEqual(groups["direction_core_tune"], 36)
        self.assertEqual(groups["direction_micro_tune"], 12)
        self.assertEqual(groups["direction_pse_tune"], 16)
        self.assertEqual(groups["local_direction_tune"], 16)
        self.assertEqual(groups["local_direction_pse_tune"], 8)
        self.assertEqual(groups["direction_pse_micro_tune"], 4)
        self.assertEqual(groups["guarded_icsa_direction_tune"], 4)
        self.assertTrue(all(job["seed"] == 5 for job in jobs))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(
            any(
                update.get("dynamic_direction_mode") == "sample"
                and update.get("dynamic_gate_hidden") == 48
                and update.get("dynamic_gate_anchor_lambda") == 0.005
                and update.get("weight_s2v") == 0.525
                for update in updates
            )
        )
        self.assertTrue(any(update.get("dynamic_local_mode") == "sample" for update in updates))
        self.assertTrue(any(update.get("dynamic_pse_mode") == "class" for update in updates))
        self.assertTrue(any(update.get("dynamic_icsa_mode") in {"sample", "class"} for update in updates))
        self.assertTrue(
            all(float(update.get("icsa_ratio", 0.0)) <= 0.004 for update in updates if "icsa_ratio" in update)
        )

    def test_dynamic_routing_batch_plan_has_h76_top4_min5_repeat_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-top4-min5-repeat")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 20)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 21)])
        self.assertEqual(groups["h76_top4_same_seed_repeat"], 20)
        self.assertEqual([job["phase"] for job in jobs], ["explore"] * 20)
        self.assertEqual([job["seed"] for job in jobs], [5] * 20)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 20)
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})

        expected = [
            (0.525, 0.003),
            (0.545, 0.004),
            (0.515, 0.002),
            (0.535, 0.002),
        ]
        for weight_s2v, anchor in expected:
            matching = [
                update
                for update in updates
                if update.get("dynamic_direction_mode") == "sample"
                and update.get("dynamic_gate_hidden") == 48
                and update.get("weight_s2v") == weight_s2v
                and update.get("dynamic_gate_anchor_lambda") == anchor
            ]
            self.assertEqual(len(matching), 5)

    def test_dynamic_routing_batch_plan_has_h76_mixed200_four_frozen_batches(self) -> None:
        profiles = [
            "h76-mixed200-b01-search50",
            "h76-mixed200-b02-search50",
            "h76-mixed200-b03-search20-repeat20-ablate10",
            "h76-mixed200-b04-search20-ablate30",
        ]
        batches = [self.module.build_dynamic_routing_jobs(seed=5, profile=profile) for profile in profiles]
        jobs = [job for batch in batches for job in batch]
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual([len(batch) for batch in batches], [50, 50, 50, 50])
        self.assertEqual(len(jobs), 200)
        self.assertEqual(groups["h76_mixed200_search_tune_plus"], 20)
        self.assertEqual(groups["h76_mixed200_search_local_refine"], 20)
        self.assertEqual(groups["h76_mixed200_top4_same_seed_repeat"], 20)
        self.assertEqual(groups["h76_mixed200_ablate_top4"], 40)
        self.assertEqual(
            sum(1 for job in jobs if job["group"] not in {"h76_mixed200_top4_same_seed_repeat", "h76_mixed200_ablate_top4"}),
            140,
        )
        self.assertTrue(all(job["phase"] == "explore" for job in jobs))
        self.assertTrue(all(job["seed"] == 5 for job in jobs))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})

        self.assertEqual(Counter(job["group"] for job in batches[0])["h76_mixed200_top4_same_seed_repeat"], 0)
        self.assertEqual(Counter(job["group"] for job in batches[1])["h76_mixed200_top4_same_seed_repeat"], 0)
        self.assertEqual(Counter(job["group"] for job in batches[2])["h76_mixed200_top4_same_seed_repeat"], 20)
        self.assertEqual(Counter(job["group"] for job in batches[2])["h76_mixed200_ablate_top4"], 10)
        self.assertEqual(Counter(job["group"] for job in batches[3])["h76_mixed200_top4_same_seed_repeat"], 0)
        self.assertEqual(Counter(job["group"] for job in batches[3])["h76_mixed200_search_local_refine"], 20)
        self.assertEqual(Counter(job["group"] for job in batches[3])["h76_mixed200_ablate_top4"], 30)

        repeated_configs = [
            (
                update.get("weight_s2v"),
                update.get("dynamic_gate_anchor_lambda"),
            )
            for job, update in zip(jobs, updates)
            if job["group"] == "h76_mixed200_top4_same_seed_repeat"
        ]
        self.assertEqual(Counter(repeated_configs), Counter({(0.525, 0.003): 5, (0.545, 0.004): 5, (0.515, 0.002): 5, (0.535, 0.002): 5}))

    def test_dynamic_routing_batch_plan_has_h76_followup50_multiseed_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-followup50-multiseed")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 50)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 51)])
        self.assertEqual(groups["h76_followup50_multiseed_stability"], 50)
        self.assertEqual([job["phase"] for job in jobs], ["explore"] * 50)
        self.assertEqual(Counter(job["seed"] for job in jobs), Counter({seed: 5 for seed in range(6, 16)}))
        self.assertEqual(Counter(update["random_seed"] for update in updates), Counter({seed: 5 for seed in range(6, 16)}))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(all(update["use_dynamic_routing"] for update in updates))
        self.assertTrue(all(update["dynamic_local_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_icsa_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_pse_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))

        candidate_names = Counter(str(job["name"]).rsplit("_s", 1)[0] for job in jobs)
        self.assertEqual(
            candidate_names,
            Counter(
                {
                    "dr047_direction_sample_h48_w0.535_a0.002": 10,
                    "dr020_direction_sample_h48_w0.525_a0.003": 10,
                    "dr041_direction_sample_h48_w0.515_a0.002": 10,
                    "a011dr042_direction_sample_h48_w0.515_a0.004": 10,
                    "a011dr020_direction_sample_h48_w0.555_a0.0045": 10,
                }
            ),
        )
        self.assertEqual(
            Counter((update["weight_s2v"], update["dynamic_gate_anchor_lambda"]) for update in updates),
            Counter({(0.535, 0.002): 10, (0.525, 0.003): 10, (0.515, 0.002): 10, (0.515, 0.004): 10, (0.555, 0.0045): 10}),
        )

    def test_dynamic_routing_batch_plan_has_h76_restore100_exact_repeat_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-restore100-exact-repeat")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]
        candidates = Counter(str(job["source_candidate_id"]) for job in jobs)

        self.assertEqual(len(jobs), 100)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 101)])
        self.assertEqual(groups["h76_restore100_exact_repeat"], 100)
        self.assertEqual(len(candidates), 20)
        self.assertEqual(set(candidates.values()), {5})
        self.assertEqual([job["seed"] for job in jobs], [5] * 100)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 100)
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(all(job["repeat_max_attempts"] == 5 for job in jobs))
        self.assertTrue(all(str(job["restore_target_H"]) for job in jobs))
        self.assertEqual(jobs[0]["source_candidate_id"], "A011B01DR042")
        self.assertEqual(jobs[0]["restore_target_H"], "75.00")
        self.assertEqual(jobs[0]["source_run_id"], "RUN-20260706-0001-h76-mixed200-b01-search50-2gpu")

    def test_dynamic_routing_restore100_policy_uses_per_job_restore_target(self) -> None:
        policy = self.module.confirmation_policy_for_profile("h76-restore100-exact-repeat")

        self.assertEqual(policy["repeat_type"], "exact_repeat")
        self.assertEqual(policy["restore_target_H"], "per_job_source_H")
        self.assertTrue(policy["per_job_restore_target_H"])
        self.assertEqual(policy["max_attempts"], 5)
        self.assertFalse(policy["seed_change_allowed"])

    def test_dynamic_routing_batch_plan_has_h76_hotspot_top2_restore10_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-hotspot-top2-restore10-exact-repeat")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]
        candidates = Counter(str(job["source_candidate_id"]) for job in jobs)

        self.assertEqual(len(jobs), 10)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 11)])
        self.assertEqual(groups["h76_hotspot_top2_exact_repeat"], 10)
        self.assertEqual(candidates, Counter({"A015DR004": 5, "A015DR035": 5}))
        self.assertEqual([job["seed"] for job in jobs], [5] * 10)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 10)
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))
        self.assertEqual(
            Counter((update["weight_s2v"], update["dynamic_gate_anchor_lambda"]) for update in updates),
            Counter({(0.495, 0.003): 5, (0.525, 0.0035): 5}),
        )
        self.assertEqual(jobs[0]["source_run_id"], "RUN-20260708-0003-h76-hotspot100-tune-live-multiagent-2gpu")
        self.assertEqual(jobs[0]["source_job_id"], "DR-004")
        self.assertEqual(jobs[0]["restore_target_H"], "75.04")
        self.assertEqual(jobs[5]["source_job_id"], "DR-035")
        self.assertEqual(jobs[5]["restore_target_H"], "75.00")
        self.assertTrue(all(job["repeat_max_attempts"] == 5 for job in jobs))

    def test_dynamic_routing_hotspot_top2_restore_policy_uses_per_job_restore_target(self) -> None:
        policy = self.module.confirmation_policy_for_profile("h76-hotspot-top2-restore10-exact-repeat")

        self.assertEqual(policy["repeat_type"], "exact_repeat")
        self.assertEqual(policy["restore_target_H"], "per_job_source_H")
        self.assertTrue(policy["per_job_restore_target_H"])
        self.assertEqual(policy["max_attempts"], 5)
        self.assertFalse(policy["seed_change_allowed"])
        self.assertTrue(policy["early_stop_on_best_hit"])

    def test_dynamic_routing_batch_plan_has_a017dr095_restore5_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-a017dr095-restore5-exact-repeat")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]
        candidates = Counter(str(job["source_candidate_id"]) for job in jobs)

        self.assertEqual(len(jobs), 5)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 6)])
        self.assertEqual(groups["h76_a017dr095_exact_repeat"], 5)
        self.assertEqual(candidates, Counter({"A017DR095": 5}))
        self.assertEqual([job["seed"] for job in jobs], [5] * 5)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 5)
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))
        self.assertEqual(
            Counter((update["weight_s2v"], update["dynamic_gate_anchor_lambda"]) for update in updates),
            Counter({(0.535, 0.0035): 5}),
        )
        self.assertEqual(jobs[0]["source_run_id"], "RUN-20260709-0001-h76-escape100-supported-routing-server-frozen-2gpu")
        self.assertEqual(jobs[0]["source_job_id"], "DR-095")
        self.assertEqual(jobs[0]["restore_target_H"], "75.11")
        self.assertTrue(all(job["repeat_max_attempts"] == 5 for job in jobs))

    def test_dynamic_routing_a017dr095_restore_policy_uses_per_job_restore_target(self) -> None:
        policy = self.module.confirmation_policy_for_profile("h76-a017dr095-restore5-exact-repeat")

        self.assertEqual(policy["repeat_type"], "exact_repeat")
        self.assertEqual(policy["restore_target_H"], "per_job_source_H")
        self.assertTrue(policy["per_job_restore_target_H"])
        self.assertEqual(policy["max_attempts"], 5)
        self.assertFalse(policy["seed_change_allowed"])
        self.assertTrue(policy["early_stop_on_best_hit"])

    def test_dynamic_routing_batch_plan_has_h76_hotspot100_tune_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-hotspot100-tune")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 100)
        self.assertEqual(groups["h76_hotspot100_primary_grid"], 65)
        self.assertEqual(groups["h76_hotspot100_micro_grid"], 20)
        self.assertEqual(groups["h76_hotspot100_low_anchor_ridge"], 15)
        self.assertEqual([job["seed"] for job in jobs], [5] * 100)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 100)
        self.assertTrue(all(update["dynamic_direction_mode"] == "sample" for update in updates))
        self.assertTrue(all(update["dynamic_gate_hidden"] == 48 for update in updates))
        self.assertTrue(all(update["dynamic_local_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_icsa_mode"] == "fixed" for update in updates))
        self.assertTrue(all(update["dynamic_pse_mode"] == "fixed" for update in updates))
        self.assertGreaterEqual(min(update["weight_s2v"] for update in updates), 0.495)
        self.assertLessEqual(max(update["weight_s2v"] for update in updates), 0.555)
        self.assertLessEqual(max(update["dynamic_gate_anchor_lambda"] for update in updates), 0.00375)

        policy = self.module.confirmation_policy_for_profile("h76-hotspot100-tune")
        self.assertEqual(policy["repeat_type"], "not_confirmation")
        self.assertTrue(policy["not_confirmation_evidence"])

    def test_dynamic_routing_batch_plan_has_h76_escape100_supported_routing_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="h76-escape100-supported-routing")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 100)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 101)])
        self.assertEqual(groups["h76_escape_direction_micro"], 30)
        self.assertEqual(groups["h76_escape_hidden_sweep"], 15)
        self.assertEqual(groups["h76_escape_local_sample_tune"], 15)
        self.assertEqual(groups["h76_escape_pse_class_tune"], 15)
        self.assertEqual(groups["h76_escape_icsa_guarded_tune"], 10)
        self.assertEqual(groups["h76_escape_ablate_mechanism"], 10)
        self.assertEqual(groups["h76_escape_sentinel_control"], 5)
        self.assertEqual([job["seed"] for job in jobs], [5] * 100)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 100)
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(any(update.get("use_dynamic_routing") is False for update in updates))
        self.assertTrue(any(update.get("dynamic_gate_hidden") in {40, 44, 52, 56, 64} for update in updates))
        self.assertTrue(any(update.get("dynamic_local_mode") == "sample" for update in updates))
        self.assertTrue(any(update.get("dynamic_pse_mode") == "class" for update in updates))
        self.assertTrue(any(update.get("dynamic_icsa_mode") in {"sample", "class"} for update in updates))
        self.assertTrue(
            all(float(update.get("icsa_ratio", 0.0)) <= 0.002 for update in updates if "icsa_ratio" in update)
        )

        policy = self.module.confirmation_policy_for_profile("h76-escape100-supported-routing")
        self.assertEqual(policy["repeat_type"], "not_confirmation")
        self.assertTrue(policy["not_confirmation_evidence"])

    def test_dynamic_runner_candidate_hit_skips_only_candidate_repeats(self) -> None:
        runner = self.module._dynamic_runner_script()

        self.assertIn("candidate_exact_repeat_best_hit", runner)
        self.assertIn("skip_remaining_candidate_repeats", runner)
        self.assertIn("job_skipped_candidate_restored", runner)
        self.assertIn("source_candidate_id", runner)

    def test_dynamic_runner_script_honors_stop_requested_file(self) -> None:
        script = self.module._dynamic_runner_script()

        self.assertIn("STOP_REQUESTED", script)
        self.assertIn("stop_requested(run_dir)", script)
        self.assertIn("skip_remaining_due_stop", script)
        self.assertIn("job_skipped_stop_requested", script)

    def test_plan_dynamic_routing_batch_rejects_formal_run_without_agent_runtime_gate(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-NO-GATE",
        )

        self.assertEqual(1, code)
        self.assertIn("requires --agent-runtime-gate", stderr)

    def test_plan_dynamic_routing_batch_allows_explicit_debug_smoke_without_gate(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-DEBUG-SMOKE",
            "--debug-smoke",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("dynamic-routing-plan-created", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-DEBUG-SMOKE/plan.json").read_text(encoding="utf-8"))
        self.assertFalse(plan["formal_evidence"])
        self.assertEqual("debug_smoke", plan["evidence_level"])

    def test_prepare_dynamic_routing_matrix_creates_one_readable_row_per_job(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, stdout, stderr = self._run_main(
            "prepare-dynamic-routing-matrix",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-009",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
        )

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("dynamic-routing-parameter-matrix-created", stdout)
        matrix_dir = self.repo / trial_dir / "attempts" / "ATTEMPT-009"
        with (matrix_dir / "PARAMETER_MATRIX.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(["DR-001", "DR-002", "DR-003"], [row["job_id"] for row in rows])
        self.assertTrue(all(row["status"] == "frozen" for row in rows))
        self.assertTrue(all(row["config_fingerprint"] for row in rows))
        view = (matrix_dir / "PARAMETER_MATRIX.md").read_text(encoding="utf-8")
        self.assertIn("| DR-001 |", view)
        self.assertIn("config_fingerprint", view)

    def test_formal_dynamic_routing_requires_frozen_matrix_and_syncs_its_results(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        self._write(
            "docs/workflow/protocols/parameter_matrix_protocol.md",
            "policy_status: active\n",
        )
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal fixture before creating its parameter matrix")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-MATRIX-MISSING",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
            "--agent-runtime-gate",
            str(gate_path),
            "--attempt-id",
            "ATTEMPT-009",
        )
        self.assertEqual(1, code)
        self.assertIn("Missing parameter matrix", stderr)
        self.assertFalse((self.repo / ".gtpj_runtime/batches/RUN-TEST-MATRIX-MISSING").exists())

        code, _stdout, stderr = self._run_main(
            "prepare-dynamic-routing-matrix",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-009",
            "--run-id",
            "RUN-TEST-MATRIX-SYNC",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self._commit_all("freeze parameter matrix before formal batch")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-MATRIX-SYNC",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
            "--agent-runtime-gate",
            str(gate_path),
            "--attempt-id",
            "ATTEMPT-009",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("dynamic-routing-plan-created", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-MATRIX-SYNC"
        manifest_rel = ".gtpj_runtime/batches/RUN-TEST-MATRIX-SYNC/artifact_manifests/DR-001.json"
        self._write(
            manifest_rel,
            json.dumps(
                {
                    "job_id": "DR-001",
                    "run_id": "RUN-TEST-MATRIX-SYNC",
                    "warehouse_attempt_id": "ATTEMPT-009",
                    "warehouse_dir": "/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/"
                    "module_trial/TRIAL-001/ATTEMPT-009/RUN-TEST-MATRIX-SYNC/DR-001",
                }
            ),
        )
        manifest_path = self.repo / manifest_rel
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-MATRIX-SYNC/summary.csv",
            "job_id,status,U,S,H,ZS,best_epoch,resolved_from_job_id,warehouse_dir,"
            "artifact_manifest,artifact_manifest_sha256,artifact_manifest_job_id,"
            "artifact_manifest_run_id,artifact_manifest_attempt_id\n"
            "DR-001,completed,70.1,72.2,71.1,73.3,12,,"
            "/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/"
            "ATTEMPT-009/RUN-TEST-MATRIX-SYNC/DR-001,"
            "/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/TRIAL-001/"
            "ATTEMPT-009/RUN-TEST-MATRIX-SYNC/DR-001/artifact_manifest.json,"
            f"{manifest_sha256},DR-001,RUN-TEST-MATRIX-SYNC,ATTEMPT-009\n",
        )

        code, stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("dynamic-routing-parameter-matrix-synced", stdout)
        with (self.repo / trial_dir / "attempts/ATTEMPT-009/PARAMETER_MATRIX.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual("completed", rows[0]["status"])
        self.assertEqual("71.1", rows[0]["H"])
        self.assertEqual("RUN-TEST-MATRIX-SYNC", rows[0]["run_id"])
        self.assertEqual(
            "warehouse_dir:/data/lby/projects/cv_project/GTPJ_Warehouse/runs/v5/module_trial/"
            "TRIAL-001/ATTEMPT-009/RUN-TEST-MATRIX-SYNC/DR-001",
            rows[0]["artifact_ref"],
        )
        code, _stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        summary_path = run_dir / "summary.csv"
        self._write(
            str(summary_path.relative_to(self.repo)).replace("\\", "/"),
            summary_path.read_text(encoding="utf-8").replace(",71.1,73.3,", ",71.2,73.3,"),
        )
        code, _stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(1, code)
        self.assertIn("Refusing to overwrite an existing result", stderr)

    def test_parameter_matrix_refresh_rejects_a_stale_reading_view(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        code, _stdout, stderr = self._run_main(
            "prepare-dynamic-routing-matrix",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-010",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        matrix_path = f"{trial_dir}/attempts/ATTEMPT-010/PARAMETER_MATRIX.csv"
        csv_path = self.repo / matrix_path
        self._write(matrix_path, csv_path.read_text(encoding="utf-8").replace(",frozen,", ",running,", 1))

        code, _stdout, stderr = self._run_main("validate-parameter-matrix", "--path", matrix_path)
        self.assertEqual(1, code)
        self.assertIn("stale or was edited separately", stderr)

        code, stdout, stderr = self._run_main("refresh-parameter-matrix-view", "--path", matrix_path)
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-view-refreshed", stdout)
        code, stdout, stderr = self._run_main("validate-parameter-matrix", "--path", matrix_path)
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-validate-ok", stdout)

    def test_parameter_matrix_conflicts_do_not_mix_versions_or_code_refs(self) -> None:
        jobs = [
            {
                "job_id": "JOB-001",
                "work_item_id": "WORK-001",
                "group": "tune",
                "name": "same config",
                "seed": 5,
                "config_updates": {"weight_s2v": 0.5},
            }
        ]
        old_rows = self.module.build_parameter_matrix_rows(
            jobs=jobs,
            base_config_text="version: v4\n",
            base_version="v4",
            code_ref="v4",
        )
        old_rows[0]["config_fingerprint"] = "same-fingerprint"
        old_dir = self.repo / "experiments/v4/tune/TUNE-001_old"
        self.module.write_parameter_matrix(
            directory=old_dir,
            title=old_dir.name,
            rows=old_rows,
            source_note="test old version",
        )
        new_rows = [dict(old_rows[0], base_version="v5", code_ref="v5")]
        self.assertEqual([], self.module.parameter_matrix_conflicts(new_rows, self.repo / "experiments"))
        same_version_rows = [dict(old_rows[0])]
        self.assertTrue(self.module.parameter_matrix_conflicts(same_version_rows, self.repo / "experiments"))

    def test_sync_dynamic_routing_matrix_resolves_top_rank_repeats_and_rejects_unknown_jobs(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        code, _stdout, stderr = self._run_main(
            "prepare-dynamic-routing-matrix",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-011",
            "--profile",
            "balanced-aggressive",
            "--jobs",
            "50",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        matrix_path = self.repo / trial_dir / "attempts/ATTEMPT-011/PARAMETER_MATRIX.csv"
        before_rows = self.module.read_parameter_matrix(matrix_path)
        pending = next(row for row in before_rows if row["config_fingerprint"].startswith("pending_after_top_rank:"))
        source = next(row for row in before_rows if row["job_id"] == "DR-001")
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC"
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/plan.json",
            json.dumps(
                {
                    "run_id": "RUN-TEST-TOP-RANK-SYNC",
                    "trial_dir": trial_dir,
                    "warehouse_root": "/warehouse",
                    "base_version": "v5",
                    "trial_id": "TRIAL-001",
                    "warehouse_attempt_id": "ATTEMPT-011",
                    "formal_evidence": True,
                    "parameter_matrix": str(matrix_path.relative_to(self.repo)).replace("\\", "/"),
                    "parameter_matrix_frozen_rows": {
                        row["job_id"]: self.module.parameter_matrix_frozen_fields(row) for row in before_rows
                    },
                    "jobs": [{"job_id": row["job_id"]} for row in before_rows],
                }
            ),
        )
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/summary.csv",
            "job_id,status,U,S,H,ZS,best_epoch,resolved_from_job_id,warehouse_dir\n"
            "DR-999,completed,70,71,70.5,72,9,DR-001,/warehouse/unknown\n",
        )
        plan_path = run_dir / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["formal_evidence"] = False
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/plan.json",
            json.dumps(plan),
        )
        code, _stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(1, code)
        self.assertIn("debug or non-formal", stderr)
        plan["formal_evidence"] = True
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/plan.json",
            json.dumps(plan),
        )
        code, _stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(1, code)
        self.assertIn("unregistered job DR-999", stderr)

        expected_warehouse = (
            f"/warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-011/"
            f"RUN-TEST-TOP-RANK-SYNC/{pending['job_id']}"
        )
        manifest_rel = (
            f".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/"
            f"artifact_manifests/{pending['job_id']}.json"
        )
        self._write(
            manifest_rel,
            json.dumps(
                {
                    "job_id": pending["job_id"],
                    "run_id": "RUN-TEST-TOP-RANK-SYNC",
                    "warehouse_attempt_id": "ATTEMPT-011",
                    "warehouse_dir": expected_warehouse,
                }
            ),
        )
        manifest_path = self.repo / manifest_rel
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        self._write(
            ".gtpj_runtime/batches/RUN-TEST-TOP-RANK-SYNC/summary.csv",
            "job_id,status,U,S,H,ZS,best_epoch,resolved_from_job_id,warehouse_dir,"
            "artifact_manifest,artifact_manifest_sha256,artifact_manifest_job_id,"
            "artifact_manifest_run_id,artifact_manifest_attempt_id\n"
            f"{pending['job_id']},completed,70,71,70.5,72,9,DR-001,"
            f"/warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-011/"
            f"RUN-TEST-TOP-RANK-SYNC/{pending['job_id']},"
            f"/warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-011/"
            f"RUN-TEST-TOP-RANK-SYNC/{pending['job_id']}/artifact_manifest.json,"
            f"{manifest_sha256},{pending['job_id']},RUN-TEST-TOP-RANK-SYNC,ATTEMPT-011\n",
        )
        code, stdout, stderr = self._run_main("sync-dynamic-routing-matrix", "--run-dir", str(run_dir))
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("dynamic-routing-parameter-matrix-synced", stdout)
        after_rows = self.module.read_parameter_matrix(matrix_path)
        resolved = next(row for row in after_rows if row["job_id"] == pending["job_id"])
        self.assertEqual("DR-001", resolved["repeat_of"])
        self.assertEqual(source["config_fingerprint"], resolved["config_fingerprint"])
        self.assertEqual(source["changed_parameters"], resolved["changed_parameters"])
        self.assertEqual(
            f"warehouse_dir:/warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-011/"
            f"RUN-TEST-TOP-RANK-SYNC/{pending['job_id']}",
            resolved["artifact_ref"],
        )

    def test_record_result_requires_a_ready_matrix_and_syncs_the_matching_job(self) -> None:
        self._git("switch", "-c", "exp/v1-tune-001-topo008")
        self._write("docs/workflow/protocols/parameter_matrix_protocol.md", "policy_status: active\n")
        self._commit_all("activate parameter-matrix policy")
        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-001",
            "--slug",
            "topo008",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        training_log_text = (
            "Best Results @ Epoch 2\n  GZSL-U : 70.0%\n  GZSL-S : 72.0%\n"
            "  GZSL-H : 71.0%\n  ZSL : 73.0%\n"
        )
        self._write("train_log/tune.log", training_log_text)
        record_args = (
            "record-result",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-001",
            "--slug",
            "topo008",
            "--matrix-job-id",
            "TUNE-001-001",
            "--parameter",
            "conditional_text_ratio",
            "--old-value",
            "0.008",
            "--new-value",
            "0.006",
            "--seed",
            "5",
            "--log",
            "train_log/tune.log",
            "--pre-run-freeze-commit",
            "HEAD",
            "--run-start-receipt",
            "train_log/tune.run_start.json",
            "--command",
            "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml",
        )
        code, _stdout, stderr = self._run_main(*record_args)
        self.assertEqual(1, code)
        self.assertIn("cannot accept a formal result", stderr)

        matrix_path = self.repo / "experiments/v1/tune/TUNE-001_topo008/PARAMETER_MATRIX.csv"
        rows = self.module.read_parameter_matrix(matrix_path)
        rows[0]["seed"] = "5"
        rows[0]["changed_parameters"] = json.dumps({"conditional_text_ratio": 0.006})
        self.module.write_parameter_matrix(
            directory=matrix_path.parent,
            title=matrix_path.parent.name,
            rows=rows,
            source_note="test version-level experiment",
            overwrite=True,
        )
        config_path = self.repo / "experiments/v1/tune/TUNE-001_topo008/config.yaml"
        config_path.write_text(
            self.module.render_config_with_updates(config_path.read_text(encoding="utf-8"), {"conditional_text_ratio": 0.006}),
            encoding="utf-8",
        )
        code, stdout, stderr = self._run_main(
            "freeze-parameter-matrix",
            "--path",
            str(matrix_path),
            "--config",
            str(config_path),
            "--job-id",
            "TUNE-001-001",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-frozen", stdout)
        no_commit_args = list(record_args)
        freeze_arg = no_commit_args.index("--pre-run-freeze-commit")
        del no_commit_args[freeze_arg : freeze_arg + 2]
        code, _stdout, stderr = self._run_main(*no_commit_args)
        self.assertEqual(1, code)
        self.assertIn("requires --pre-run-freeze-commit", stderr)
        self._commit_all("freeze parameter matrix before result")
        log_path = self.repo / "train_log/tune.log"
        code, _stdout, stderr = self._run_main(
            "prepare-run-start-receipt",
            "--path",
            str(matrix_path),
            "--config",
            str(config_path),
            "--job-id",
            "TUNE-001-001",
            "--run-id",
            "attempt-001",
            "--pre-run-freeze-commit",
            "HEAD",
            "--command",
            "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml",
            "--receipt",
            "train_log/tune.run_start.json",
            "--log",
            "train_log/tune.log",
        )
        self.assertEqual(1, code)
        self.assertIn("refuses existing receipt or log files", stderr)
        log_path.unlink()
        code, stdout, stderr = self._run_main(
            "prepare-run-start-receipt",
            "--path",
            str(matrix_path),
            "--config",
            str(config_path),
            "--job-id",
            "TUNE-001-001",
            "--run-id",
            "attempt-001",
            "--pre-run-freeze-commit",
            "HEAD",
            "--command",
            "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml",
            "--receipt",
            "train_log/tune.run_start.json",
            "--log",
            "train_log/tune.log",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("run-start-receipt-created", stdout)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(training_log_text)
        bad_seed_args = list(record_args)
        bad_seed_args[bad_seed_args.index("5")] = "6"
        code, _stdout, stderr = self._run_main(*bad_seed_args)
        self.assertEqual(1, code)
        self.assertIn("seed", stderr)
        config_path.write_text(
            self.module.render_config_with_updates(config_path.read_text(encoding="utf-8"), {"conditional_text_ratio": 0.007}),
            encoding="utf-8",
        )
        code, _stdout, stderr = self._run_main(*record_args)
        self.assertEqual(1, code)
        self.assertIn("config", stderr)
        config_path.write_text(
            self.module.render_config_with_updates(config_path.read_text(encoding="utf-8"), {"conditional_text_ratio": 0.006}),
            encoding="utf-8",
        )
        code, _stdout, stderr = self._run_main(
            "freeze-parameter-matrix",
            "--path",
            str(matrix_path),
            "--config",
            str(config_path),
            "--job-id",
            "TUNE-001-001",
        )
        self.assertEqual(1, code)
        self.assertIn("only freeze a draft row once", stderr)
        code, stdout, stderr = self._run_main(*record_args)
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("record-result-ok", stdout)
        rows = self.module.read_parameter_matrix(matrix_path)
        self.assertEqual("completed", rows[0]["status"])
        self.assertEqual("71.0", rows[0]["H"])
        receipt_copy = self.repo / "experiments/v1/tune/TUNE-001_topo008/run_start_receipt.json"
        self.assertTrue(receipt_copy.is_file())
        result_yaml = (self.repo / "experiments/v1/tune/TUNE-001_topo008/result.yaml").read_text(encoding="utf-8")
        self.assertIn("run_start_receipt_sha256:", result_yaml)
        self.assertIn("run_start_receipt_ref:", result_yaml)
        code, _stdout, stderr = self._run_main(*record_args)
        self.assertEqual(1, code)
        self.assertIn("frozen or running", stderr)

    def test_freeze_parameter_matrix_allows_multi_job_rows_to_be_frozen_one_at_a_time(self) -> None:
        matrix_dir = self.repo / "experiments/v1/tune/TUNE-002_batch"
        config_one = matrix_dir / "configs/JOB-001.yaml"
        config_two = matrix_dir / "configs/JOB-002.yaml"
        self._write(str(config_one.relative_to(self.repo)).replace("\\", "/"), "version: v1\nalpha:\n  value: 0.1\n")
        self._write(str(config_two.relative_to(self.repo)).replace("\\", "/"), "version: v1\nalpha:\n  value: 0.2\n")
        base_rows = []
        for job_id, seed in [("JOB-001", "5"), ("JOB-002", "6")]:
            base_rows.append(
                {
                    "job_id": job_id,
                    "work_item_id": job_id,
                    "job_kind": "param_tune",
                    "status": "draft",
                    "group": "batch",
                    "name": job_id,
                    "base_version": "v1",
                    "base_config_sha256": "base",
                    "code_ref": "v1",
                    "config_snapshot_ref": "",
                    "seed": seed,
                    "changed_parameters": "{}",
                    "config_fingerprint": "pending-freeze-" + job_id,
                    "repeat_of": "",
                    "duplicate_resolution": "unique",
                    "purpose": "test",
                    "run_id": "",
                    "U": "",
                    "S": "",
                    "H": "",
                    "ZS": "",
                    "best_epoch": "",
                    "decision": "",
                    "artifact_ref": "",
                }
            )
        self.module.write_parameter_matrix(
            directory=matrix_dir,
            title=matrix_dir.name,
            rows=base_rows,
            source_note="two-job freeze test",
        )
        matrix_path = matrix_dir / "PARAMETER_MATRIX.csv"

        code, stdout, stderr = self._run_main(
            "freeze-parameter-matrix",
            "--path",
            str(matrix_path),
            "--config",
            str(config_one),
            "--job-id",
            "JOB-001",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-frozen", stdout)
        rows = self.module.read_parameter_matrix(matrix_path)
        self.assertEqual("frozen", rows[0]["status"])
        self.assertEqual("draft", rows[1]["status"])

        code, _stdout, stderr = self._run_main(
            "freeze-parameter-matrix",
            "--path",
            str(matrix_path),
            "--config",
            str(config_two),
            "--job-id",
            "JOB-002",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        code, stdout, stderr = self._run_main(
            "validate-parameter-matrix",
            "--path",
            str(matrix_path),
            "--expected-jobs",
            "2",
            "--require-ready",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-validate-ok", stdout)

    def test_legacy_summary_only_blocks_promotion_and_persists_its_identity(self) -> None:
        self._git("switch", "-c", "exp/v1-tune-901-legacy-summary")
        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-901",
            "--slug",
            "legacy-summary",
        )
        self.assertEqual(0, code, stderr)
        self.assertEqual("", stderr)
        exp_dir = self.repo / "experiments/v1/tune/TUNE-901_legacy-summary"
        (exp_dir / "PARAMETER_MATRIX.csv").unlink()
        (exp_dir / "PARAMETER_MATRIX.md").unlink()
        self._write(
            "train_log/legacy-summary.log",
            "Best Results @ Epoch 2\n  GZSL-U : 60.0%\n  GZSL-S : 62.0%\n"
            "  GZSL-H : 61.0%\n  ZSL : 63.0%\n",
        )
        base_args = (
            "record-result",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-901",
            "--slug",
            "legacy-summary",
            "--log",
            "train_log/legacy-summary.log",
            "--decision",
            "rejected",
            "--parameter",
            "conditional_text_ratio",
            "--old-value",
            "0.008",
            "--new-value",
            "0.006",
            "--legacy-summary-only",
        )
        code, _stdout, stderr = self._run_main(
            *base_args,
            "--promotion-decision",
            "promote",
            "--promote-to",
            "v2",
        )
        self.assertEqual(1, code)
        self.assertIn("cannot set promotion_decision=promote or promote_to", stderr)
        code, stdout, stderr = self._run_main(*base_args)
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("record-result-ok", stdout)
        result = (exp_dir / "result.yaml").read_text(encoding="utf-8")
        manifest = (exp_dir / "manifest.yaml").read_text(encoding="utf-8")
        self.assertIn('result_status: "legacy_summary_only"', result)
        self.assertIn('promotion_decision: "blocked"', result)
        self.assertIn('evidence_level: "legacy_summary_only"', result)
        self.assertNotIn('promote_to: "v2"', result)
        self.assertIn('evidence_mode: "legacy_summary_only"', manifest)

    def test_parameter_matrix_ready_gate_rejects_terminal_and_legacy_rows(self) -> None:
        rows = self.module.build_parameter_matrix_rows(
            jobs=[
                {
                    "job_id": "JOB-001",
                    "work_item_id": "WORK-001",
                    "job_kind": "ablation",
                    "group": "local-branch",
                    "name": "baseline",
                    "seed": 5,
                    "config_updates": {"local_weight": 0.2},
                }
            ],
            base_config_text="version: v5\nlocal_weight:\n  value: 0.2\n",
            base_version="v5",
            code_ref="v5",
            run_id="RUN-READY-GATE",
        )
        rows[0]["status"] = "completed"
        completed_errors = self.module.validate_parameter_matrix_rows(rows, require_ready=True)
        self.assertIn("must be frozen and unused", "\n".join(completed_errors))
        rows[0]["status"] = "legacy_summary_only"
        self.assertEqual([], self.module.validate_parameter_matrix_rows(rows))
        ready_errors = self.module.validate_parameter_matrix_rows(rows, require_ready=True)
        record_errors = self.module.validate_parameter_matrix_rows(rows, require_recordable=True)
        self.assertIn("must be frozen and unused", "\n".join(ready_errors))
        self.assertIn("cannot accept a formal result", "\n".join(record_errors))

    def test_parameter_matrix_reader_rejects_cells_outside_the_fixed_header(self) -> None:
        matrix_dir = self.repo / "experiments/v5/ablation/ABLATION-900_extra-cell"
        rows = self.module.build_parameter_matrix_rows(
            jobs=[{"job_id": "JOB-001", "seed": 5, "config_updates": {}}],
            base_config_text="version: v5\n",
            base_version="v5",
            code_ref="v5",
        )
        matrix_path, _view = self.module.write_parameter_matrix(
            directory=matrix_dir,
            title=matrix_dir.name,
            rows=rows,
            source_note="extra-cell test",
        )
        matrix_path.write_text(matrix_path.read_text(encoding="utf-8").rstrip() + ",unexpected\n", encoding="utf-8")
        with self.assertRaisesRegex(self.module.WorkflowError, "cells outside the fixed header"):
            self.module.read_parameter_matrix(matrix_path)

    def test_init_parameter_matrix_supports_an_ordinary_module_attempt(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        attempt_dir = f"{trial_dir}/attempts/ATTEMPT-012"
        self._write(f"{trial_dir}/config.yaml", "version: v5\nrandom_seed:\n  value: 5\nalpha:\n  value: 0.1\n")
        self._write(
            f"{attempt_dir}/config.yaml",
            "version: v5\nrandom_seed:\n  value: 5\nalpha:\n  value: 0.2\n",
        )
        code, stdout, stderr = self._run_main(
            "init-parameter-matrix",
            "--directory",
            attempt_dir,
            "--job-id",
            "ATTEMPT-012-001",
            "--job-kind",
            "ablation",
            "--base-version",
            "v5",
            "--base-config",
            f"{trial_dir}/config.yaml",
            "--config",
            f"{attempt_dir}/config.yaml",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("parameter-matrix-initialized", stdout)
        matrix_path = self.repo / attempt_dir / "PARAMETER_MATRIX.csv"
        rows = self.module.read_parameter_matrix(matrix_path)
        self.assertEqual("draft", rows[0]["status"])
        self.assertIn("alpha", rows[0]["changed_parameters"])
        code, _stdout, stderr = self._run_main(
            "freeze-parameter-matrix",
            "--path",
            str(matrix_path),
            "--config",
            f"{attempt_dir}/config.yaml",
            "--job-id",
            "ATTEMPT-012-001",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertEqual("frozen", self.module.read_parameter_matrix(matrix_path)[0]["status"])

    def test_dynamic_warehouse_result_must_match_frozen_identity_and_manifest(self) -> None:
        plan = {
            "warehouse_root": "/warehouse",
            "base_version": "v5",
            "trial_id": "TRIAL-001",
            "warehouse_attempt_id": "ATTEMPT-013",
            "run_id": "RUN-WAREHOUSE-GATE",
        }
        result = {
            "job_id": "DR-001",
            "warehouse_dir": "/warehouse/arbitrary",
        }
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-WAREHOUSE-GATE"
        self.assertIn(
            "does not match",
            "\n".join(self.module.dynamic_warehouse_result_errors(plan, result, run_dir=run_dir)),
        )
        expected = "/warehouse/runs/v5/module_trial/TRIAL-001/ATTEMPT-013/RUN-WAREHOUSE-GATE/DR-001"
        result["warehouse_dir"] = expected
        self.assertIn(
            "artifact_manifest",
            "\n".join(self.module.dynamic_warehouse_result_errors(plan, result, run_dir=run_dir)),
        )
        fake_sha = "a" * 64
        result.update(
            {
                "artifact_manifest": expected + "/artifact_manifest.json",
                "artifact_manifest_sha256": fake_sha,
                "artifact_manifest_job_id": "DR-001",
                "artifact_manifest_run_id": "RUN-WAREHOUSE-GATE",
                "artifact_manifest_attempt_id": "ATTEMPT-013",
            }
        )
        missing_errors = self.module.dynamic_warehouse_result_errors(plan, result, run_dir=run_dir)
        self.assertIn("no downloaded artifact manifest receipt", "\n".join(missing_errors))
        manifest_rel = ".gtpj_runtime/batches/RUN-WAREHOUSE-GATE/artifact_manifests/DR-001.json"
        self._write(
            manifest_rel,
            json.dumps(
                {
                    "job_id": "DR-001",
                    "run_id": "RUN-WAREHOUSE-GATE",
                    "warehouse_attempt_id": "ATTEMPT-013",
                    "warehouse_dir": expected,
                }
            ),
        )
        manifest_path = self.repo / manifest_rel
        result["artifact_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        self.assertEqual([], self.module.dynamic_warehouse_result_errors(plan, result, run_dir=run_dir))

    def test_formal_dynamic_plan_rejects_a_changed_frozen_field(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        self._write("docs/workflow/protocols/parameter_matrix_protocol.md", "policy_status: active\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal changed-field fixture")
        code, _stdout, stderr = self._run_main(
            "prepare-dynamic-routing-matrix",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-014",
            "--run-id",
            "RUN-CHANGED-FROZEN-FIELD",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
        )
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        matrix_path = self.repo / trial_dir / "attempts/ATTEMPT-014/PARAMETER_MATRIX.csv"
        rows = self.module.read_parameter_matrix(matrix_path)
        rows[0]["base_version"] = "v4"
        self.module.write_parameter_matrix(
            directory=matrix_path.parent,
            title=matrix_path.parent.name,
            rows=rows,
            source_note="changed frozen field test",
            overwrite=True,
        )
        self._commit_all("commit altered frozen field fixture")
        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-CHANGED-FROZEN-FIELD",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
            "--agent-runtime-gate",
            str(gate_path),
            "--attempt-id",
            "ATTEMPT-014",
        )
        self.assertEqual(1, code)
        self.assertIn("base_version differs from the frozen batch plan", stderr)

    def test_plan_dynamic_routing_batch_writes_start_script_with_lf_newlines(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-LF-SCRIPT",
            "--debug-smoke",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        script_bytes = (self.repo / ".gtpj_runtime/batches/RUN-TEST-LF-SCRIPT/start_batch.sh").read_bytes()
        self.assertTrue(script_bytes.startswith(b"#!/usr/bin/env bash\n"))
        self.assertNotIn(b"\r", script_bytes)

    def test_plan_dynamic_routing_batch_accepts_valid_agent_runtime_gate(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-FORMAL-GATE",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("dynamic-routing-plan-created", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-FORMAL-GATE/plan.json").read_text(encoding="utf-8"))
        self.assertTrue(plan["formal_evidence"])
        self.assertEqual("experiments/module_trials/IDEA-0003_x/TRIAL-001_x/agent_runtime.yaml", plan["agent_runtime_gate"])
        head = self._git("rev-parse", "HEAD").stdout.strip()
        self.assertEqual(head, plan["commit"])
        self.assertEqual(head, plan["plan_generation_commit"])
        self.assertTrue(plan["formal_source_clean"])
        self.assertEqual("formal_same_clean_head", plan["commit_policy"])
        self.assertEqual(head, plan["source_control"]["training_commit"])
        self.assertEqual(head, plan["source_control"]["plan_generation_commit"])
        self.assertEqual("main", plan["source_control"]["plan_generation_branch"])
        self.assertEqual("main", plan["source_control"]["training_branch_label"])
        self.assertEqual("clean", plan["source_control"]["dirty_state"])
        self.assertIn("experiments/module_trials/IDEA-0003_x/TRIAL-001_x/config.yaml", plan["source_control"]["fingerprint_paths"])

    def test_plan_dynamic_routing_batch_rejects_formal_dirty_worktree(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")
        self._write("scratch_dirty.txt", "uncommitted formal planner change\n")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-FORMAL-DIRTY",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual(1, code)
        self.assertIn("Working tree must be clean before formal dynamic routing batch planning creates files", stderr)
        self.assertFalse((self.repo / ".gtpj_runtime/batches/RUN-TEST-FORMAL-DIRTY").exists())

    def test_plan_dynamic_routing_batch_rejects_formal_commit_mismatch(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")
        frozen_commit = self._git("rev-parse", "HEAD").stdout.strip()
        self._write("advance_head.txt", "advance clean HEAD\n")
        self._commit_all("advance clean head")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-FORMAL-COMMIT-MISMATCH",
            "--agent-runtime-gate",
            str(gate_path),
            "--commit",
            frozen_commit,
        )

        self.assertEqual(1, code)
        self.assertIn("requires --commit to equal the clean local HEAD", stderr)
        self.assertFalse((self.repo / ".gtpj_runtime/batches/RUN-TEST-FORMAL-COMMIT-MISMATCH").exists())

    def test_plan_dynamic_routing_batch_allows_explicit_historical_training_commit(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze historical training source")
        training_commit = self._git("rev-parse", "HEAD").stdout.strip()
        self._write(f"{trial_dir}/config.yaml", "version: planner-only-new\n")
        self._write("planner_fix.txt", "planner-only safety fix\n")
        self._commit_all("advance planner helper")
        planner_commit = self._git("rev-parse", "HEAD").stdout.strip()

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-HISTORICAL-COMMIT",
            "--agent-runtime-gate",
            str(gate_path),
            "--commit",
            training_commit,
            "--branch",
            "main",
            "--allow-historical-training-commit",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("dynamic-routing-plan-created", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-HISTORICAL-COMMIT/plan.json").read_text(encoding="utf-8"))
        self.assertEqual(training_commit, plan["commit"])
        self.assertEqual(planner_commit, plan["plan_generation_commit"])
        self.assertEqual("main", plan["branch"])
        self.assertEqual("formal_explicit_historical_training_commit", plan["commit_policy"])
        self.assertEqual(training_commit, plan["source_control"]["training_commit"])
        self.assertEqual(planner_commit, plan["source_control"]["plan_generation_commit"])
        self.assertEqual("main", plan["source_control"]["training_branch_label"])
        rendered_config = (self.repo / ".gtpj_runtime/batches/RUN-TEST-HISTORICAL-COMMIT/configs/DR-001.yaml").read_text(encoding="utf-8")
        self.assertIn("version: v5", rendered_config)
        self.assertNotIn("planner-only-new", rendered_config)

    def test_plan_dynamic_routing_batch_rejects_formal_branch_mismatch(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-FORMAL-BRANCH-MISMATCH",
            "--agent-runtime-gate",
            str(gate_path),
            "--branch",
            "not-the-current-branch",
        )

        self.assertEqual(1, code)
        self.assertIn("requires --branch to match the current branch", stderr)
        self.assertFalse((self.repo / ".gtpj_runtime/batches/RUN-TEST-FORMAL-BRANCH-MISMATCH").exists())

    def test_plan_dynamic_routing_batch_uses_attempt_scoped_warehouse_from_gate(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/attempts/ATTEMPT-007/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-ATTEMPT-WAREHOUSE",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("dynamic-routing-plan-created", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-ATTEMPT-WAREHOUSE"
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        readme = (run_dir / "README.md").read_text(encoding="utf-8")
        self.assertEqual("attempt_run", plan["warehouse_scope"])
        self.assertEqual("ATTEMPT-007", plan["warehouse_attempt_id"])
        self.assertIn("warehouse_scope: attempt_run", readme)
        self.assertIn("warehouse_attempt_id: ATTEMPT-007", readme)
        self.assertIn("cd /data/lby/projects/cv_project/GTPJ/.gtpj_runtime/batches/RUN-TEST-ATTEMPT-WAREHOUSE", readme)

    def test_plan_dynamic_routing_batch_accepts_explicit_attempt_id_for_warehouse(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, _stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-EXPLICIT-ATTEMPT-WAREHOUSE",
            "--profile",
            "dr035-min3-confirm",
            "--jobs",
            "3",
            "--agent-runtime-gate",
            str(gate_path),
            "--attempt-id",
            "attempt-009",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-EXPLICIT-ATTEMPT-WAREHOUSE/plan.json").read_text(encoding="utf-8"))
        self.assertEqual("attempt_run", plan["warehouse_scope"])
        self.assertEqual("ATTEMPT-009", plan["warehouse_attempt_id"])
        self.assertEqual({"ATTEMPT-009"}, {job["attempt_id"] for job in plan["jobs"]})

    def test_plan_dynamic_routing_batch_accepts_workflow_v2_10_job_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-WF2-10",
            "--profile",
            "workflow-v2-2innov-8tune",
            "--jobs",
            "10",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 10", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-WF2-10/plan.json").read_text(encoding="utf-8"))
        self.assertEqual("workflow-v2-2innov-8tune", plan["profile"])
        self.assertEqual(10, len(plan["jobs"]))

    def test_plan_dynamic_routing_batch_accepts_h76_100_job_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-100",
            "--profile",
            "h76-existing-routing-100",
            "--jobs",
            "100",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 100", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-100/plan.json").read_text(encoding="utf-8"))
        self.assertEqual("h76-existing-routing-100", plan["profile"])
        self.assertEqual(100, len(plan["jobs"]))

    def test_plan_dynamic_routing_batch_accepts_h76_escape100_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-ESCAPE100",
            "--profile",
            "h76-escape100-supported-routing",
            "--jobs",
            "100",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 100", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-ESCAPE100/plan.json").read_text(encoding="utf-8"))
        groups = Counter(job["group"] for job in plan["jobs"])
        self.assertEqual("h76-escape100-supported-routing", plan["profile"])
        self.assertEqual(100, len(plan["jobs"]))
        self.assertEqual(groups["h76_escape_direction_micro"], 30)
        self.assertEqual(groups["h76_escape_ablate_mechanism"], 10)

    def test_plan_dynamic_routing_batch_accepts_h76_mixed200_batch_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-MIXED200-B03",
            "--profile",
            "h76-mixed200-b03-search20-repeat20-ablate10",
            "--jobs",
            "50",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 50", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-MIXED200-B03"
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        readme = (run_dir / "README.md").read_text(encoding="utf-8")
        runner = (run_dir / "run_dynamic_routing_batch.py").read_text(encoding="utf-8")
        groups = Counter(job["group"] for job in plan["jobs"])
        self.assertEqual("h76-mixed200-b03-search20-repeat20-ablate10", plan["profile"])
        self.assertEqual(50, len(plan["jobs"]))
        self.assertEqual(groups["h76_mixed200_top4_same_seed_repeat"], 20)
        self.assertEqual(groups["h76_mixed200_ablate_top4"], 10)
        self.assertIn("STOP_REQUESTED", readme)
        self.assertIn("STOP_REQUESTED", runner)

    def test_plan_dynamic_routing_batch_marks_h76_top4_repeat_as_exact_repeat(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-TOP4-REPEAT",
            "--profile",
            "h76-top4-min5-repeat",
            "--jobs",
            "20",
            "--restore-target-h",
            "75.00",
            "--near-miss-tolerance-h",
            "0.20",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 20", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-TOP4-REPEAT/plan.json").read_text(encoding="utf-8"))
        self.assertEqual("exact_repeat", plan["confirmation_policy"]["repeat_type"])
        self.assertEqual(5, plan["confirmation_policy"]["max_attempts"])
        self.assertTrue(plan["confirmation_policy"]["early_stop_on_best_hit"])
        self.assertEqual("75.00", plan["confirmation_policy"]["restore_target_H"])
        self.assertEqual("0.20", plan["confirmation_policy"]["near_miss_tolerance_H"])
        self.assertTrue(plan["confirmation_policy"]["near_miss_not_restored"])

    def test_dynamic_runner_near_miss_does_not_trigger_stop(self) -> None:
        runner = self.module._dynamic_runner_script()

        self.assertIn("h_value >= target_value", runner)
        self.assertIn("event\": \"near_miss_not_restored\"", runner)
        self.assertIn("decision\": \"continue_exact_repeat\"", runner)
        self.assertNotIn("threshold = target_value - tolerance", runner)

    def test_dynamic_runner_verifies_worktree_source_control_before_training(self) -> None:
        runner = self.module._dynamic_runner_script()

        self.assertIn("git_output([\"cat-file\", \"-e\"", runner)
        self.assertIn("worktree HEAD mismatch before training", runner)
        self.assertIn("worktree has unexpected dirty files before training", runner)
        self.assertIn("allowed_dirty_paths", runner)

    def test_plan_dynamic_routing_batch_accepts_h76_followup50_multiseed_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal dynamic routing fixture")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-FOLLOWUP50",
            "--profile",
            "h76-followup50-multiseed",
            "--jobs",
            "50",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 50", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-FOLLOWUP50"
        plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
        groups = Counter(job["group"] for job in plan["jobs"])
        self.assertEqual("h76-followup50-multiseed", plan["profile"])
        self.assertEqual(50, len(plan["jobs"]))
        self.assertEqual(groups["h76_followup50_multiseed_stability"], 50)
        self.assertEqual(plan["confirmation_policy"]["repeat_type"], "multi_seed_stability")
        self.assertTrue(plan["confirmation_policy"]["not_confirmation_evidence"])

    def test_plan_dynamic_routing_batch_can_limit_profile_for_workflow_probe(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, stdout, stderr = self._run_main(
            "plan-dynamic-routing-batch",
            "--trial-dir",
            trial_dir,
            "--run-id",
            "RUN-TEST-H76-20",
            "--profile",
            "h76-existing-routing-100",
            "--jobs",
            "20",
            "--limit-jobs",
            "20",
            "--debug-smoke",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("jobs: 20", stdout)
        plan = json.loads((self.repo / ".gtpj_runtime/batches/RUN-TEST-H76-20/plan.json").read_text(encoding="utf-8"))
        self.assertEqual("h76-existing-routing-100", plan["profile"])
        self.assertEqual(20, len(plan["jobs"]))
        self.assertEqual("DR-020", plan["jobs"][-1]["job_id"])

    def test_route_experiment_routes_h76_phrase_to_dynamic_routing(self) -> None:
        code, stdout, stderr = self._run_main(
            "route-experiment",
            "--phrase",
            "基于DR-035跑20组冲H=76",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow_kind: dynamic-routing", stdout)
        self.assertIn("profile: h76-existing-routing-100", stdout)
        self.assertIn("required_roles:", stdout)
        self.assertIn("agent_instances: not_started_by_route", stdout)
        self.assertIn("Runner Monitor", stdout)

    def test_run_workflow_requires_explicit_debug_or_formal_mode(self) -> None:
        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "基于DR-035跑3组冲H=76",
            "--run-id",
            "RUN-TEST-WORKFLOW-NO-MODE",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
        )

        self.assertEqual(1, code)
        self.assertIn("requires exactly one of --debug-smoke or --formal", stderr)

    def test_run_workflow_rejects_ambiguous_debug_and_formal_mode(self) -> None:
        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "基于DR-035跑3组冲H=76",
            "--run-id",
            "RUN-TEST-WORKFLOW-BOTH-MODES",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--debug-smoke",
            "--formal",
        )

        self.assertEqual(1, code)
        self.assertIn("requires exactly one of --debug-smoke or --formal", stderr)

    def test_run_workflow_formal_requires_agent_runtime_gate(self) -> None:
        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "基于DR-035跑3组冲H=76",
            "--run-id",
            "RUN-TEST-WORKFLOW-FORMAL-NO-GATE",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--formal",
        )

        self.assertEqual(1, code)
        self.assertIn("--formal requires --agent-runtime-gate", stderr)

    def test_run_workflow_requires_explicit_workflow_mode(self) -> None:
        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "workflow mode required",
            "--run-id",
            "RUN-TEST-WORKFLOW-NO-WORKFLOW-MODE",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--debug-smoke",
        )

        self.assertEqual(1, code)
        self.assertIn("requires --workflow-mode", stderr)

    def test_run_monitor_closeout_workflow_minimal_dispatcher(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")

        code, stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "基于DR-035跑20组冲H=76",
            "--workflow-mode",
            "server_frozen_runner",
            "--run-id",
            "RUN-TEST-WORKFLOW-20",
            "--jobs",
            "20",
            "--limit-jobs",
            "20",
            "--debug-smoke",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow-run-dir:", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20"
        state = json.loads((run_dir / "workflow_state.json").read_text(encoding="utf-8"))
        self.assertEqual("planned", state["current_state"])
        self.assertEqual("debug_smoke", state["run_mode"])
        self.assertEqual("server_frozen_runner", state["workflow_mode"])
        self.assertEqual("role_only", state["activation_mode"])
        self.assertEqual("role_only", state["agent_instance_mode"])
        self.assertEqual("not_applicable_debug_smoke", state["formal_runtime_backend"])
        self.assertFalse(state["real_agent_instances_started_by_helper"])
        self.assertFalse(state["real_agent_instances_verified_by_gate"])
        self.assertFalse(state["agent_runtime_gate_satisfied"])
        self.assertIn("Runner Monitor", state["required_roles"])
        self.assertTrue((run_dir / "TRANSITIONS.jsonl").exists())

        status = json.loads((run_dir / "batch_status.json").read_text(encoding="utf-8"))
        status["status"] = "running"
        status["jobs"]["DR-001"]["status"] = "completed"
        status["jobs"]["DR-002"]["status"] = "running"
        (run_dir / "batch_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "summary.csv").write_text(
            "job_id,status,phase,group,name,H,U,S,ZS,best_epoch\n"
            "DR-001,completed,explore,sanity_control,static_v5_control,75.01,72.00,78.00,81.00,48\n",
            encoding="utf-8",
        )

        code, stdout, stderr = self._run_main(
            "monitor-workflow",
            "--run-dir",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20",
            "--top-k",
            "3",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow_state: running", stdout)
        self.assertIn("hit_h75: true", stdout)
        self.assertIn("next_helper: monitor-workflow", stdout)
        state = json.loads((run_dir / "workflow_state.json").read_text(encoding="utf-8"))
        self.assertEqual("debug_smoke", state["run_mode"])
        self.assertEqual("server_frozen_runner", state["workflow_mode"])
        self.assertEqual("role_only", state["activation_mode"])
        self.assertEqual("not_applicable_debug_smoke", state["formal_runtime_backend"])
        self.assertFalse(state["agent_runtime_gate_satisfied"])

        code, stdout, stderr = self._run_main(
            "monitor-workflow",
            "--run-dir",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20",
            "--report-new-completions",
            "--activity-log",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20/AGENT_ACTIVITY.md",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("new_completed_count: 1", stdout)
        self.assertIn("new_completed: DR-001", stdout)
        seen_jobs = json.loads((run_dir / "monitor_seen_completed_jobs.json").read_text(encoding="utf-8"))
        self.assertEqual(["DR-001"], seen_jobs["completed_job_ids"])
        self.assertIn("job_completed_report", (run_dir / "AGENT_ACTIVITY.md").read_text(encoding="utf-8"))

        code, stdout, stderr = self._run_main(
            "monitor-workflow",
            "--run-dir",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20",
            "--report-new-completions",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("new_completed_count: 0", stdout)

        status = json.loads((run_dir / "batch_status.json").read_text(encoding="utf-8"))
        status["status"] = "stopped"
        status["jobs"]["DR-002"]["status"] = "skipped"
        status["jobs"]["DR-002"]["skip_reason"] = "STOP_REQUESTED"
        (run_dir / "batch_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        code, stdout, stderr = self._run_main(
            "monitor-workflow",
            "--run-dir",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20",
            "--top-k",
            "3",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow_state: stopped", stdout)
        state = json.loads((run_dir / "workflow_state.json").read_text(encoding="utf-8"))
        self.assertEqual("stopped", state["current_state"])
        self.assertEqual("server_frozen_runner", state["workflow_mode"])

        code, stdout, stderr = self._run_main(
            "closeout-workflow",
            "--run-dir",
            ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-20",
            "--allow-incomplete",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("formal_result_written: false", stdout)

    def test_run_workflow_formal_records_real_multi_agent_gate_status(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal workflow fixture")

        code, stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "基于DR-035跑3组冲H=76",
            "--workflow-mode",
            "live_multi_agent_monitor",
            "--run-id",
            "RUN-TEST-WORKFLOW-FORMAL",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--formal",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow-run-dir:", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-FORMAL"
        state = json.loads((run_dir / "workflow_state.json").read_text(encoding="utf-8"))
        self.assertEqual("formal", state["run_mode"])
        self.assertEqual("live_multi_agent_monitor", state["workflow_mode"])
        self.assertEqual("real_multi_agent", state["activation_mode"])
        self.assertEqual("named_owner_thread", state["agent_instance_mode"])
        self.assertEqual("named_owner_thread", state["formal_runtime_backend"])
        self.assertFalse(state["real_agent_instances_started_by_helper"])
        self.assertTrue(state["real_agent_instances_verified_by_gate"])
        self.assertTrue(state["agent_runtime_gate_satisfied"])
        self.assertTrue(state["formal_evidence"])

    def test_run_workflow_formal_records_server_frozen_runner_gate_status(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_server_detached_formal_gate(path=f"{trial_dir}/agent_runtime.yaml")
        self._commit_all("freeze formal workflow fixture")

        code, stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "server frozen workflow",
            "--workflow-kind",
            "dynamic-routing",
            "--workflow-mode",
            "server_frozen_runner",
            "--run-id",
            "RUN-TEST-WORKFLOW-SERVER-FROZEN",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--formal",
            "--agent-runtime-gate",
            str(gate_path),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow-run-dir:", stdout)
        run_dir = self.repo / ".gtpj_runtime/batches/RUN-TEST-WORKFLOW-SERVER-FROZEN"
        state = json.loads((run_dir / "workflow_state.json").read_text(encoding="utf-8"))
        self.assertEqual("formal", state["run_mode"])
        self.assertEqual("server_frozen_runner", state["workflow_mode"])
        self.assertEqual("role_only", state["activation_mode"])
        self.assertEqual("role_only", state["agent_instance_mode"])
        self.assertEqual("server_detached_role_only", state["formal_runtime_backend"])
        self.assertFalse(state["real_agent_instances_started_by_helper"])
        self.assertFalse(state["real_agent_instances_verified_by_gate"])
        self.assertTrue(state["agent_runtime_gate_satisfied"])
        self.assertTrue(state["server_detached_expected"])
        self.assertFalse(state["thread_creation_allowed"])
        self.assertTrue(state["formal_evidence"])

    def test_run_workflow_rejects_workflow_mode_gate_backend_mismatch(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        named_gate = self._write_agent_runtime_gate(path=f"{trial_dir}/named_agent_runtime.yaml")
        server_gate = self._write_server_detached_formal_gate(path=f"{trial_dir}/server_agent_runtime.yaml")

        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "server frozen mismatch",
            "--workflow-mode",
            "server_frozen_runner",
            "--run-id",
            "RUN-TEST-WORKFLOW-MISMATCH-1",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--formal",
            "--agent-runtime-gate",
            str(named_gate),
        )
        self.assertEqual(1, code)
        self.assertIn("server_frozen_runner requires formal_runtime_backend: server_detached_role_only", stderr)

        code, _stdout, stderr = self._run_main(
            "run-workflow",
            "--phrase",
            "live monitor mismatch",
            "--workflow-mode",
            "live_multi_agent_monitor",
            "--run-id",
            "RUN-TEST-WORKFLOW-MISMATCH-2",
            "--jobs",
            "3",
            "--limit-jobs",
            "3",
            "--formal",
            "--agent-runtime-gate",
            str(server_gate),
        )
        self.assertEqual(1, code)
        self.assertIn("live_multi_agent_monitor requires named-owner-thread", stderr)

    def test_config_epoch_schedule_uses_lr_stages_total(self) -> None:
        config_path = self.repo / "experiments/module_trials/IDEA-0001_x/TRIAL-001_x/attempts/ATTEMPT-001/config.yaml"
        self._write(
            str(config_path.relative_to(self.repo)).replace("\\", "/"),
            "epochs:\n"
            "  value: 30\n"
            "lr_stages:\n"
            "  value:\n"
            "  - lr: 0.001\n"
            "    epochs: 20\n"
            "  - lr: 0.0001\n"
            "    epochs: 20\n"
            "  - lr: 1.0e-05\n"
            "    epochs: 10\n",
        )

        schedule = self.module.config_epoch_schedule(config_path)

        self.assertEqual(schedule["config_epochs_field"], 30)
        self.assertEqual(schedule["planned_train_epochs"], 50)
        self.assertEqual(schedule["epoch_schedule_source"], "lr_stages")
        self.assertEqual(schedule["lr_stage_epochs"], [20, 20, 10])

    def test_validate_rejects_ambiguous_pre_run_epochs_when_lr_stages_override(self) -> None:
        attempt_dir = "experiments/module_trials/IDEA-0001_x/TRIAL-001_x/attempts/ATTEMPT-001"
        self._write(
            f"{attempt_dir}/config.yaml",
            "epochs:\n"
            "  value: 30\n"
            "lr_stages:\n"
            "  value:\n"
            "  - lr: 0.001\n"
            "    epochs: 20\n"
            "  - lr: 0.0001\n"
            "    epochs: 20\n"
            "  - lr: 1.0e-05\n"
            "    epochs: 10\n",
        )
        self._write(f"{attempt_dir}/pre_run_plan.md", "# Plan\n\n- Epochs: 30\n")

        errors = self.module.validate_attempt_epoch_schedule_disclosure()

        self.assertTrue(any("Planned train epochs: 50" in error for error in errors))
        self.assertTrue(any("ambiguous '- Epochs:'" in error for error in errors))

    def test_dynamic_routing_batch_plan_has_dynamic_bold_followup_50_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="dynamic-bold-followup")
        groups = Counter(job["group"] for job in jobs)
        phases = Counter(job["phase"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 50)
        self.assertEqual(phases["explore"], 50)
        self.assertEqual(groups["sanity_control"], 4)
        self.assertEqual(groups["direction_bold"], 12)
        self.assertEqual(groups["pse_bold"], 10)
        self.assertEqual(groups["local_bold"], 8)
        self.assertEqual(groups["icsa_safe_bold"], 6)
        self.assertEqual(groups["combination_bold"], 10)
        self.assertTrue(any(update.get("dynamic_icsa_mode") == "sample" for update in updates))
        self.assertTrue(any(update.get("pse_outer_ratio") == 0.85 for update in updates))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(
            all(float(update.get("icsa_ratio", 0.0)) <= 0.006 for update in updates if "icsa_ratio" in update)
        )

    def test_dynamic_routing_batch_plan_has_workflow_v2_2innov_8tune_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=5, profile="workflow-v2-2innov-8tune")
        groups = Counter(job["group"] for job in jobs)
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 10)
        self.assertEqual(groups["innovation_probe"], 2)
        self.assertEqual(groups["direction_tune"], 8)
        self.assertEqual([job["work_item_id"] for job in jobs[:2]], ["INNOV-001", "INNOV-002"])
        self.assertEqual([job["work_item_id"] for job in jobs[2:]], [f"TUNE-{i:03d}" for i in range(1, 9)])
        self.assertTrue(all(job["seed"] == 5 for job in jobs))
        self.assertNotIn("sample", {update.get("dynamic_pse_mode") for update in updates})
        self.assertTrue(any(update.get("dynamic_local_mode") == "sample" for update in updates))
        self.assertTrue(any(update.get("dynamic_pse_mode") == "class" for update in updates))
        self.assertTrue(any(update.get("dynamic_direction_mode") == "class" for update in updates))

    def test_dynamic_routing_runner_records_failures_and_warehouse_artifacts(self) -> None:
        script = self.module._dynamic_runner_script()

        self.assertIn("except Exception as exc", script)
        self.assertIn("status=\"failed\"", script)
        self.assertIn("copy_artifacts_to_warehouse", script)
        self.assertIn("warehouse_attempt_dir", script)
        self.assertIn("artifact_manifest.json", script)
        self.assertIn('receipt_dir = run_dir / "artifact_manifests"', script)
        self.assertIn('shutil.copy2(manifest_path, receipt_dir / f"{job[\'job_id\']}.json")', script)
        self.assertIn("link_runtime_resources", script)
        self.assertIn('plan.get("runtime_resource_links", ["data"])', script)
        self.assertIn("os.path.isabs(python_cmd)", script)
        self.assertIn("prune_model_artifacts", script)
        self.assertIn("keep top 3 best_model_*.pth by H", script)
        self.assertIn("def load_json(path, retries=20, delay=0.05):", script)
        self.assertIn("os.replace(tmp_path, path)", script)
        self.assertIn("def refresh_batch_status(run_dir):", script)
        self.assertIn("def inner():", script)
        self.assertIn('status_path = run_dir / "batch_status.json"', script)
        self.assertIn("write_json(status_path, status)", script)
        self.assertIn("completed_with_failures", script)
        self.assertIn('str(plan.get("warehouse_attempt_id", ""))', script)
        self.assertIn('/ str(plan.get("run_id", "RUN-UNKNOWN"))', script)

    def test_runner_lock_rejects_second_run_until_unlocked(self) -> None:
        code, stdout, stderr = self._run_main(
            "runner-lock",
            "--run-id",
            "RUN-20260625-001",
            "--experiment-id",
            "TUNE-001",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("gpu-runner-locked", stdout)
        self.assertTrue((self.repo / ".gtpj_runtime/gpu_runner.lock").exists())

        code, _stdout, stderr = self._run_main(
            "runner-lock",
            "--run-id",
            "RUN-20260625-002",
            "--experiment-id",
            "TUNE-002",
        )

        self.assertEqual(1, code)
        self.assertIn("GPU Runner is already locked", stderr)

        code, stdout, stderr = self._run_main("runner-unlock", "--run-id", "RUN-20260625-001")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("gpu-runner-free", stdout)
        self.assertFalse((self.repo / ".gtpj_runtime/gpu_runner.lock").exists())

    def test_tune_record_result_parses_log_updates_index_and_cleanup_prompt(self) -> None:
        self._git("switch", "-c", "exp/v1-tune-001-topo008")
        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-001",
            "--slug",
            "topo008",
        )
        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self._write(
            "train_log/tune.log",
            "Best Results @ Epoch 26\n"
            "  GZSL-U : 72.36%\n"
            "  GZSL-S : 75.57%\n"
            "  GZSL-H : 73.93%\n"
            "  ZSL    : 81.62%\n",
        )

        code, stdout, stderr = self._run_main(
            "record-result",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-001",
            "--slug",
            "topo008",
            "--parameter",
            "conditional_text_ratio",
            "--old-value",
            "0.008",
            "--new-value",
            "0.006",
            "--seed",
            "5",
            "--log",
            "train_log/tune.log",
            "--command",
            "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml",
            "--decision",
            "keep",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("record-result-ok", stdout)
        self.assertIn("临时分支清理提示", stdout)
        exp_dir = self.repo / "experiments/v1/tune/TUNE-001_topo008"
        readme = (exp_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn("kind: tune", readme)
        self.assertIn("tuned_parameter: conditional_text_ratio", readme)
        self.assertIn("old_value: 0.008", readme)
        self.assertIn("new_value: 0.006", readme)
        self.assertIn("U: 72.36", readme)
        self.assertIn("S: 75.57", readme)
        self.assertIn("H: 73.93", readme)
        self.assertIn("ZS: 81.62", readme)
        self.assertIn("best_epoch: 26", readme)
        self.assertIn("decision: keep", readme)
        self.assertIn("log_artifact_id: log:TUNE-001_topo008:attempt-001", readme)
        self.assertIn("log_uri: warehouse://gtpj/runs/v1/tune/TUNE-001_topo008/attempt-001/logs/tune.log", readme)
        self.assertIn("log_sha256:", readme)
        self.assertFalse((exp_dir / "logs/tune.log").exists())
        manifest = (exp_dir / "manifest.yaml").read_text(encoding="utf-8")
        result_yaml = (exp_dir / "result.yaml").read_text(encoding="utf-8")
        result_md = (exp_dir / "result.md").read_text(encoding="utf-8")
        self.assertIn("schema_version: gtpj-manifest/v1", manifest)
        self.assertIn("warehouse://gtpj/runs/v1/tune/TUNE-001_topo008/attempt-001/logs/tune.log", manifest)
        self.assertIn('label_mapping_id: "standard_v1"', manifest)
        self.assertIn('metric_contract_id: "gzsl_u_s_h_zs_v1"', manifest)
        self.assertIn("schema_version: gtpj-result/v1", result_yaml)
        self.assertIn('H: "73.93"', result_yaml)
        self.assertIn('metric_semantics: "GZSL U/S/H/ZS from protected evaluator"', result_yaml)
        self.assertIn('label_mapping_id: "standard_v1"', result_yaml)
        self.assertIn('split_id: "standard_v1"', result_yaml)
        self.assertIn('class_order_id: "standard_v1"', result_yaml)
        self.assertIn("log:TUNE-001_topo008:attempt-001", result_md)
        index = self._tune_index_text()
        self.assertIn("## 结果记录", index)
        self.assertIn("`TUNE-001_topo008` | `conditional_text_ratio` | 0.008 | 0.006 | 5 | 72.36", index)
        registry = self._registry_text()
        self.assertIn("| `TUNE-001_topo008` | `v1` | `tune` | keep |", registry)

    def test_record_result_uses_entry_dirty_state_for_readme_and_manifest(self) -> None:
        self._git("switch", "-c", "exp/v1-tune-001-topo008")
        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "tune",
            "--exp-id",
            "TUNE-001",
            "--slug",
            "topo008",
        )
        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self._git("add", ".")
        self._git("commit", "-m", "add planned tune")

        with tempfile.TemporaryDirectory() as log_tmp:
            log_path = Path(log_tmp) / "tune.log"
            log_path.write_text(
                "Best Results @ Epoch 26\n"
                "  GZSL-U : 72.36%\n"
                "  GZSL-S : 75.57%\n"
                "  GZSL-H : 73.93%\n"
                "  ZSL    : 81.62%\n",
                encoding="utf-8",
            )

            code, _stdout, stderr = self._run_main(
                "record-result",
                "--version",
                "v1",
                "--kind",
                "tune",
                "--exp-id",
                "TUNE-001",
                "--slug",
                "topo008",
                "--parameter",
                "conditional_text_ratio",
                "--old-value",
                "0.008",
                "--new-value",
                "0.006",
                "--seed",
                "5",
                "--log",
                str(log_path),
                "--command",
                "python train_GTPJ_CUB.py --config experiments/v1/tune/TUNE-001_topo008/config.yaml",
            )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        exp_dir = self.repo / "experiments/v1/tune/TUNE-001_topo008"
        readme = (exp_dir / "README.md").read_text(encoding="utf-8")
        manifest = (exp_dir / "manifest.yaml").read_text(encoding="utf-8")
        self.assertIn("dirty_state: clean", readme)
        self.assertIn('git_dirty: "false"', manifest)

    def test_sync_trial_summary_updates_root_ledgers_and_idea_tree(self) -> None:
        self._write_selected_idea_files()
        trial_dir = "experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router"
        self._write(
            f"{trial_dir}/README.md",
            """# TRIAL-001_token_router

```text
trial_id: TRIAL-001
idea_id: IDEA-0001
base_version: v1
base_code_tag: v1
branch_source: main
idea_source_file: idea_tree/ideas/IDEA-0001_token_router/IDEA.md
idea_title: Token Router
code_branch: dev/v1-idea-0001-trial-001-token-router
code_tag: trial/v1/idea-0001/trial-001
code_commit:
trial_decision: pending
promotion_decision: not_applicable
promote_to:
evidence_level: pending
best_observed_H:
confirmed_H:
confirmation_status: pending
run_config: config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
```

## 结果

| 数据集 | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|

## Trial Flow

```mermaid
flowchart TD
  Idea --> Run
```
""",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-001/manifest.yaml",
            """schema_version: gtpj-manifest/v1
experiment:
  id: "TRIAL-001"
  name: "TRIAL-001_token_router"
  kind: "module-trial"
  status: "completed"
  attempt_id: "attempt-001"
version:
  base_version: "v1"
  base_code_tag: "v1"
  code_branch: "dev/v1-idea-0001-trial-001-token-router"
  code_commit: "abc123"
  git_dirty: "false"
reproducibility:
  config_file: "experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router/attempts/ATTEMPT-001/config.yaml"
  config_sha256: "sha-config"
  pre_run_freeze_commit: "abc123"
  command: "python train_GTPJ_CUB.py --config config.yaml"
  seed: "5"
idea:
  idea_id: "IDEA-0001"
  title: "Token Router"
  hypothesis: "Improve routing."
artifacts:
  train_log:
    artifact_id: "log:v1:module_trial:TRIAL-001:attempt-001"
    role: "training_log"
    uri: "warehouse://gtpj/runs/v1/module_trials/TRIAL-001/attempt-001/logs/train.log"
    sha256: "sha-log"
    size_bytes: "123"
    required_for: "audit"
    status: "available"
""",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-001/result.yaml",
            """schema_version: gtpj-result/v1
experiment_id: "TRIAL-001"
kind: "module-trial"
version: "v1"
attempt_id: "attempt-001"
metrics:
  U: "70.00"
  S: "72.00"
  H: "70.99"
  ZS: "80.00"
  best_epoch: "12"
  baseline_H: "73.93"
  delta_H: "-2.94"
  seed: "5"
run:
  seed: "5"
  pre_run_freeze_commit: "abc123"
  command: "python train_GTPJ_CUB.py --config config.yaml"
decision:
  status: "revise"
  promotion_decision: "not_applicable"
evidence:
  evidence_level: "quick_local"
""",
        )
        self._write(
            f"{trial_dir}/review_round_2.md",
            """# Stale Review

```text
attempt_id: ATTEMPT-000
decision: pending
```

No training result has been recorded.
""",
        )
        self._write(
            f"{trial_dir}/agent_summary.md",
            """# Stale Agent Summary

```text
attempt_id: ATTEMPT-000
final_decision: pending
```

No training result has been recorded.
""",
        )

        attempt_manifest_path = self.repo / trial_dir / "attempts/ATTEMPT-001/manifest.yaml"
        attempt_result_path = self.repo / trial_dir / "attempts/ATTEMPT-001/result.yaml"
        original_manifest = attempt_manifest_path.read_text(encoding="utf-8")
        original_result = attempt_result_path.read_text(encoding="utf-8")
        attempt_manifest_path.write_text(
            original_manifest.replace('  status: "completed"', '  status: "completed"\n  evidence_mode: "legacy_summary_only"'),
            encoding="utf-8",
        )
        attempt_result_path.write_text(
            original_result.replace('  status: "revise"', '  status: "rejected"\n  result_status: "legacy_summary_only"')
            .replace('  evidence_level: "quick_local"', '  evidence_level: "legacy_summary_only"'),
            encoding="utf-8",
        )
        code, _stdout, stderr = self._run_main(
            "sync-trial-summary",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-001",
            "--decision",
            "promote",
            "--promotion-decision",
            "promote",
        )
        self.assertEqual(1, code)
        self.assertIn("legacy_summary_only attempt cannot be synced", stderr)
        attempt_manifest_path.write_text(original_manifest, encoding="utf-8")
        attempt_result_path.write_text(original_result, encoding="utf-8")

        code, stdout, stderr = self._run_main(
            "sync-trial-summary",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-001",
            "--decision",
            "revise",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("sync-trial-summary-ok", stdout)
        root_result = (self.repo / trial_dir / "result.yaml").read_text(encoding="utf-8")
        root_readme = (self.repo / trial_dir / "README.md").read_text(encoding="utf-8")
        review_round_2 = (self.repo / trial_dir / "review_round_2.md").read_text(encoding="utf-8")
        agent_summary = (self.repo / trial_dir / "agent_summary.md").read_text(encoding="utf-8")
        module_index = (self.repo / "experiments/module_trials/INDEX.md").read_text(encoding="utf-8")
        idea_json = json.loads((self.repo / "idea_tree/idea_tree.json").read_text(encoding="utf-8"))
        idea = idea_json["ideas"][0]

        self.assertIn('evidence_level: "valid_single_run"', root_result)
        self.assertIn('best_observed_H: ""', root_result)
        self.assertIn('attempt_manifest: "attempts/ATTEMPT-001/manifest.yaml"', root_result)
        self.assertIn("trial_decision: revise", root_readme)
        self.assertIn("log_artifact_id: log:v1:module_trial:TRIAL-001:attempt-001", root_readme)
        self.assertIn("| CUB | 5 | 70.00 | 72.00 | 70.99 | 80.00 | 12 |", root_readme)
        self.assertIn("attempt_id: ATTEMPT-001", review_round_2)
        self.assertIn("log:v1:module_trial:TRIAL-001:attempt-001", review_round_2)
        self.assertNotIn("No training result has been recorded", review_round_2)
        self.assertIn("attempt_id: ATTEMPT-001", agent_summary)
        self.assertIn("log:v1:module_trial:TRIAL-001:attempt-001", agent_summary)
        self.assertNotIn("No training result has been recorded", agent_summary)
        self.assertIn("| `IDEA-0001` | `idea_tree/ideas/IDEA-0001_token_router/IDEA.md` |", module_index)
        self.assertIn("delta_H=-2.94", module_index)
        self.assertEqual("weakened", idea["status"])
        self.assertEqual("trialing", idea["version_scores"]["v1"]["stage"])
        self.assertIn(f"{trial_dir}/result.yaml", {item["ref"] for item in idea["evidence"]})

    def test_sync_trial_summary_confirmed_candidate_preserves_best_observed(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing"
        self._write(
            f"{trial_dir}/README.md",
            """# TRIAL-001_dynamic-routing

```text
trial_id: TRIAL-001
idea_id: IDEA-0003
base_version: v5
base_code_tag: v5
branch_source: main
idea_source_file: idea_tree/ideas/IDEA-0003_dynamic_residual_routing/IDEA.md
idea_title: Dynamic Residual Routing
code_branch: codex/dr035-exact-repeat-20260703
code_tag: trial/v5/idea-0003/trial-001
code_commit:
trial_decision: pending
promotion_decision: blocked
promote_to:
evidence_level: valid_single_run
best_observed_H: 75.02
confirmed_H: pending
confirmation_status: needs_confirmation
run_config: config.yaml
log_artifact_id:
log_uri:
log_sha256:
log_size_bytes:
manifest: manifest.yaml
result_yaml: result.yaml
result_md: result.md
```

## Results

| Dataset | Seed | U | S | H | ZS | Best epoch | Log |
|---|---:|---:|---:|---:|---:|---:|---|
""",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-007/manifest.yaml",
            """schema_version: gtpj-manifest/v1
experiment:
  id: "TRIAL-001"
  name: "TRIAL-001_dynamic-routing"
  kind: "module-trial"
  status: "completed"
  attempt_id: "attempt-007"
version:
  base_version: "v5"
  base_code_tag: "v5"
  code_branch: "codex/dr035-exact-repeat-20260703"
  code_commit: "abc123"
  git_dirty: "false"
reproducibility:
  config_file: "experiments/module_trials/IDEA-0003_dynamic_residual_routing/TRIAL-001_dynamic-routing/attempts/ATTEMPT-007/config.yaml"
  config_sha256: "sha-config"
  pre_run_freeze_commit: "abc123"
  command: "bash start_batch.sh"
  seed: "5"
idea:
  idea_id: "IDEA-0003"
  title: "Dynamic Residual Routing"
  hypothesis: "Confirm DR-035."
artifacts:
  train_log:
    artifact_id: "log:v5:module_trial:TRIAL-001:attempt-007"
    role: "training_log"
    uri: "warehouse://gtpj/runs/v5/module_trial/TRIAL-001/ATTEMPT-007/RUN-DR035/DR-001/logs/train.log"
    sha256: "sha-log"
    size_bytes: "123"
    required_for: "audit"
    status: "available"
""",
        )
        self._write(
            f"{trial_dir}/attempts/ATTEMPT-007/result.yaml",
            """schema_version: gtpj-attempt-result/v1
experiment_id: "TRIAL-001"
kind: "module-trial"
version: "v5"
attempt_id: "attempt-007"
metrics:
  U: "73.38"
  S: "75.88"
  H: "74.61"
  ZS: "81.84"
  best_epoch: "37"
  baseline_H: "74.44"
  delta_H: "+0.17"
  seed: "5"
decision:
  status: "confirmed_candidate"
  promotion_decision: "blocked"
evidence:
  evidence_level: "confirmation_grade"
""",
        )

        code, stdout, stderr = self._run_main(
            "sync-trial-summary",
            "--trial-dir",
            trial_dir,
            "--attempt-id",
            "ATTEMPT-007",
            "--decision",
            "confirmed_candidate",
            "--evidence-level",
            "confirmation_grade",
            "--promotion-decision",
            "blocked",
            "--skip-idea-tree",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("sync-trial-summary-ok", stdout)
        root_result = (self.repo / trial_dir / "result.yaml").read_text(encoding="utf-8")
        root_readme = (self.repo / trial_dir / "README.md").read_text(encoding="utf-8")
        self.assertIn('result_status: "confirmed_candidate"', root_result)
        self.assertIn('best_observed_H: "75.02"', root_result)
        self.assertIn('confirmed_H: "74.61"', root_result)
        self.assertIn('confirmation_status: "confirmed_candidate"', root_result)
        self.assertIn("trial_decision: confirmed_candidate", root_readme)
        self.assertIn("best_observed_H: 75.02", root_readme)
        self.assertIn("confirmed_H: 74.61", root_readme)
        self.assertIn("confirmation_status: confirmed_candidate", root_readme)

    def test_attempt_sync_metrics_accepts_batch_best_single(self) -> None:
        result_path = self.repo / "experiments/module_trials/IDEA-0001_x/TRIAL-001_x/attempts/ATTEMPT-002/result.yaml"
        self._write(
            str(result_path.relative_to(self.repo)).replace("\\", "/"),
            """schema_version: gtpj-attempt-result/v1
metrics:
  best_single:
    job_id: "DR-018"
    U: 73.10
    S: 76.71
    H: 74.86
    ZS: 81.84
    best_epoch: 37
decision:
  status: "tune_promising"
""",
        )
        result = self.module.read_shallow_yaml(result_path)

        metrics = self.module.attempt_sync_metrics(result, result_path)

        self.assertEqual("74.86", metrics["H"])
        self.assertEqual("73.10", metrics["U"])
        self.assertEqual("76.71", metrics["S"])
        self.assertEqual("81.84", metrics["ZS"])
        self.assertEqual("37", metrics["best_epoch"])

    def test_audit_boundary_rejects_raw_experiment_log(self) -> None:
        self._write("experiments/v1/tune/TUNE-999_bad/logs/train.log", "raw log\n")

        code, _stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual(1, code)
        self.assertIn("Forbidden raw experiment artifacts", stderr)

    def test_audit_boundary_rejects_root_level_txt_raw_log(self) -> None:
        self._write("experiments/v1/tune/TUNE-999_bad/train.txt", "raw log\n")

        code, _stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual(1, code)
        self.assertIn("Forbidden raw experiment artifacts", stderr)
        self.assertIn("train.txt", stderr)

    def test_audit_boundary_rejects_experiment_image_outside_figures_dir(self) -> None:
        self._write("experiments/v1/tune/TUNE-999_bad/plot.png", "raw figure\n")

        code, _stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual(1, code)
        self.assertIn("Forbidden raw experiment artifacts", stderr)
        self.assertIn("plot.png", stderr)

    def test_audit_boundary_rejects_experiment_checkpoint(self) -> None:
        self._write("experiments/v1/tune/TUNE-999_bad/model.pth", "checkpoint\n")

        code, _stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual(1, code)
        self.assertIn("Forbidden raw experiment artifacts", stderr)
        self.assertIn("model.pth", stderr)

    def test_audit_boundary_accepts_manifest_result_without_raw_artifacts(self) -> None:
        sha = "0" * 64
        self._write(
            "experiments/v1/tune/TUNE-999_ok/manifest.yaml",
            f"schema_version: gtpj-manifest/v1\n"
            f"artifacts:\n"
            f"  train_log:\n"
            f"    artifact_id: log:TUNE-999_ok:attempt-001\n"
            f"    uri: warehouse://gtpj/runs/v1/tune/TUNE-999_ok/attempt-001/logs/train.log\n"
            f"    sha256: {sha}\n"
            f"    size_bytes: 12\n",
        )
        self._write(
            "experiments/v1/tune/TUNE-999_ok/result.yaml",
            "schema_version: gtpj-result/v1\n"
            "evidence:\n"
            "  log_artifact_id: log:TUNE-999_ok:attempt-001\n",
        )

        code, stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("audit-boundary-ok", stdout)

    def test_audit_boundary_rejects_result_artifact_missing_manifest_identity(self) -> None:
        self._write(
            "experiments/v1/tune/TUNE-999_bad/manifest.yaml",
            "schema_version: gtpj-manifest/v1\n"
            "artifacts:\n"
            "  train_log:\n"
            "    artifact_id: log:TUNE-999_bad:attempt-001\n"
            "    uri: warehouse://gtpj/runs/v1/tune/TUNE-999_bad/attempt-001/logs/train.log\n",
        )
        self._write(
            "experiments/v1/tune/TUNE-999_bad/result.yaml",
            "schema_version: gtpj-result/v1\n"
            "evidence:\n"
            "  log_artifact_id: log:TUNE-999_bad:attempt-001\n",
        )

        code, _stdout, stderr = self._run_main("audit-boundary")

        self.assertEqual(1, code)
        self.assertIn("Broken result/manifest/artifact identity chain", stderr)
        self.assertIn("missing identity fields: sha256, size_bytes", stderr)

    def test_validate_evidence_routing_accepts_valid_transition_chain(self) -> None:
        transition = self._transition_record()
        self._write_evidence_routing_subject([transition])

        code, stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-evidence-routing-ok subjects=1", stdout)

    def test_validate_evidence_routing_rejects_current_state_mismatch(self) -> None:
        transition = self._transition_record()
        self._write_evidence_routing_subject([transition])
        routing_path = self.repo / "experiments/v1/tune/TUNE-001_ok/evidence_routing.yaml"
        routing_text = routing_path.read_text(encoding="utf-8").replace(
            "evidence_state: single_run_valid",
            "evidence_state: min3_confirmed",
        )
        routing_path.write_text(routing_text, encoding="utf-8")

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("current_state evidence_state does not match chain head", stderr)

    def test_validate_evidence_routing_rejects_transition_hash_mutation(self) -> None:
        transition = self._transition_record()
        self._write_evidence_routing_subject([transition])
        transition_path = self.repo / "experiments/v1/tune/TUNE-001_ok/TRANSITIONS.jsonl"
        transition_text = transition_path.read_text(encoding="utf-8").replace("test transition", "mutated")
        transition_path.write_text(transition_text, encoding="utf-8")

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("current_transition_hash mismatch", stderr)

    def test_validate_evidence_routing_rejects_duplicate_transition_id(self) -> None:
        first = self._transition_record(transition_id="TRN-20260701-0001")
        second = self._transition_record(
            transition_id="TRN-20260701-0001",
            previous_transition_id=first["transition_id"],
            previous_transition_hash=first["current_transition_hash"],
            from_state="single_run_valid",
            to_state="tune_promising",
        )
        self._write_evidence_routing_subject([first, second])

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("duplicate transition_id", stderr)

    def test_validate_evidence_routing_rejects_missing_authority_ref(self) -> None:
        transition = self._transition_record(authority_ref="experiments/v1/tune/TUNE-001_ok/missing.yaml")
        self._write_evidence_routing_subject([transition])

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("missing authority ref", stderr)

    def test_validate_evidence_routing_rejects_hard_rule_fail_advance(self) -> None:
        transition = self._transition_record(verdict="fail")
        self._write_evidence_routing_subject([transition])

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("cannot advance/promote with failed rule_checks", stderr)

    def test_validate_evidence_routing_rejects_authoritative_campaign_metrics(self) -> None:
        self._write(
            "experiments/campaigns/CAMP-001/RESULT_INDEX.md",
            "# Result Index\n\nsubject_id: ATTEMPT-001\nH: 74.50\nauthority: authoritative_result\n",
        )

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("derived_index_only", stderr)

    def test_validate_evidence_routing_accepts_derived_campaign_index(self) -> None:
        self._write(
            "experiments/campaigns/CAMP-001/RESULT_INDEX.md",
            "# Result Index\n\nauthority: derived_index_only\nmetric_source: result_ref only\n",
        )

        code, stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-evidence-routing-ok", stdout)

    def test_validate_evidence_routing_rejects_missing_agent_runtime_field(self) -> None:
        transition = self._transition_record(include_not_checked=False)
        self._write_evidence_routing_subject([transition])

        code, _stdout, stderr = self._run_main("validate-evidence-routing")

        self.assertEqual(1, code)
        self.assertIn("decision missing not_checked", stderr)

    def test_validate_agent_runtime_accepts_valid_gate(self) -> None:
        gate_path = self._write_agent_runtime_gate()

        code, stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-agent-runtime-ok gates=1", stdout)

    def test_validate_agent_runtime_accepts_minimal_debug_smoke_gate(self) -> None:
        gate_path = self.repo / "experiments/v1/tune/TUNE-001_ok/debug_agent_runtime.yaml"
        self._write(
            str(gate_path.relative_to(self.repo)).replace("\\", "/"),
            "schema_version: gtpj.agent_runtime_gate.v0\n"
            "subject_id: DEBUG-001\n"
            "subject_type: run\n"
            "formal_evidence: false\n"
            "activation_mode: role_only\n"
            "agent_instance_mode: role_only\n"
            "runner_scope: debug_smoke\n"
            "evidence_level: debug_smoke\n"
            "formal_runner_allowed: false\n"
            "formal_evidence_allowed: false\n",
        )

        code, stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-agent-runtime-ok gates=1", stdout)

    def test_validate_agent_runtime_accepts_server_detached_formal_role_only_gate(self) -> None:
        gate_path = self._write_server_detached_formal_gate()

        code, stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-agent-runtime-ok gates=1", stdout)

    def test_validate_agent_runtime_rejects_placeholder_agent_id(self) -> None:
        gate_path = self._write_agent_runtime_gate(include_agent_ids=False)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("not a real agent/thread id", stderr)

    def test_validate_agent_runtime_rejects_spawn_agent_named_thread_id(self) -> None:
        gate_path = self._write_agent_runtime_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace(
                "runner_monitor: 019f1111-1111-7111-8111-111111111111",
                "runner_monitor: multi_agent_v1.spawn_agent",
            ),
            encoding="utf-8",
        )

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("not a real agent/thread id", stderr)

    def test_validate_agent_runtime_rejects_random_thread_title(self) -> None:
        gate_path = self._write_agent_runtime_gate(bad_thread_title=True)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("uses a random legacy nickname", stderr)

    def test_validate_agent_runtime_rejects_temporary_subagent_formal_gate(self) -> None:
        gate_path = self._write_agent_runtime_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace(
                "agent_instance_mode: named_owner_thread",
                "agent_instance_mode: temporary_subagent",
            ),
            encoding="utf-8",
        )

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("formal evidence requires agent_instance_mode: named_owner_thread", stderr)

    def test_validate_agent_runtime_rejects_missing_pre_run_allow(self) -> None:
        gate_path = self._write_agent_runtime_gate(quality_decision="not_checked")

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("pre_run_required_checks.evidence_quality_checker must be allow/pass", stderr)

    def test_validate_agent_runtime_rejects_missing_multi_agent_preflight(self) -> None:
        gate_path = self._write_agent_runtime_gate(include_preflight=False)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("missing multi_agent_preflight", stderr)

    def test_validate_agent_runtime_rejects_missing_agent_output_ref_file(self) -> None:
        gate_path = self._write_agent_runtime_gate()
        (gate_path.parent / "agent_outputs" / "runner_monitor.md").unlink()

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("agent_output_refs.runner_monitor must point to a local evidence file", stderr)

    def test_validate_agent_runtime_rejects_duplicate_agent_id_roles(self) -> None:
        gate_path = self._write_agent_runtime_gate(duplicate_agent_id=True)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("reuse one agent id for multiple roles", stderr)

    def test_multi_agent_preflight_accepts_valid_gate(self) -> None:
        gate_path = self._write_agent_runtime_gate()

        code, stdout, stderr = self._run_main("multi-agent-preflight", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("multi-agent-preflight-ok", stdout)
        self.assertIn("formal_runner_allowed=true", stdout)

    def test_multi_agent_preflight_accepts_server_detached_formal_role_only_gate(self) -> None:
        gate_path = self._write_server_detached_formal_gate()

        code, stdout, stderr = self._run_main("multi-agent-preflight", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("multi-agent-preflight-ok", stdout)
        self.assertIn("backend=server_detached_role_only", stdout)

    def test_agent_cleanup_plan_lists_keep_and_archive_threads(self) -> None:
        gate_path = self._write_agent_runtime_gate()

        code, stdout, stderr = self._run_main("agent-cleanup-plan", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("agent-cleanup-plan path=", stdout)
        self.assertIn("keep_count=1", stdout)
        self.assertIn("KEEP role=runner_monitor", stdout)
        self.assertIn("archive_count=2", stdout)
        self.assertIn("ARCHIVE role=interface_checker", stdout)
        self.assertIn("ARCHIVE role=evidence_quality_checker", stdout)
        self.assertIn("duplicate_instance_ids=0", stdout)

    def test_agent_cleanup_plan_defers_archive_during_live_stage(self) -> None:
        gate_path = self._write_agent_runtime_gate()
        text = gate_path.read_text(encoding="utf-8")
        text = text.replace(
            "archived_threads_record: AGENT_ACTIVITY.md\n",
            "archived_threads_record: AGENT_ACTIVITY.md\n"
            "current_stage_status: running\n"
            "archive_after_closeout_only: true\n"
        )
        text = text.replace("  runner_monitor: running\n", "  runner_monitor: completed\n")
        gate_path.write_text(text, encoding="utf-8")

        code, stdout, stderr = self._run_main("agent-cleanup-plan", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("archive_deferred_until_closeout=true", stdout)
        self.assertIn("keep_count=3", stdout)
        self.assertIn("KEEP role=runner_monitor", stdout)
        self.assertIn("archive_count=0", stdout)

    def test_agent_cleanup_plan_accepts_server_detached_formal_without_named_threads(self) -> None:
        gate_path = self._write_server_detached_formal_gate()

        code, stdout, stderr = self._run_main("agent-cleanup-plan", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("cleanup_mode=not_applicable_no_named_threads", stdout)
        self.assertIn("archive_count=0", stdout)

    def test_validate_agent_runtime_rejects_missing_owner_monitor_mode(self) -> None:
        gate_path = self._write_agent_runtime_gate(include_owner_monitor=False)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("missing owner_monitor_mode", stderr)

    def test_validate_agent_runtime_rejects_server_detached_formal_if_thread_creation_allowed(self) -> None:
        gate_path = self._write_server_detached_formal_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace(
                "thread_creation_allowed: false",
                "thread_creation_allowed: true",
            ),
            encoding="utf-8",
        )

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("thread_creation_allowed: false", stderr)

    def test_start_card_generates_formal_preflight_skeleton(self) -> None:
        code, stdout, stderr = self._run_main(
            "start-card",
            "--type",
            "tune",
            "--version",
            "v1",
            "--owner-request",
            "调参",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("runner_scope: formal_runner", stdout)
        self.assertIn("multi_agent_preflight:", stdout)
        self.assertIn("formal_runner_allowed: false", stdout)

    def _write_valid_ai_cross_review_pack(self, pack_dir: str) -> None:
        self._write(f"{pack_dir}/00_task.md", "task_id: TEST\nowner_participation: not_required\n")
        self._write(f"{pack_dir}/01_codex_actions.md", "codex_role: implementer\nchanged_files:\n")
        self._write(f"{pack_dir}/02_diff.patch", "diff --git a/file b/file\n")
        self._write(f"{pack_dir}/03_validation.md", "commands_run:\nmachine_gates_passed: true\n")
        self._write(f"{pack_dir}/04_claims.md", "claim:\nstatus: verified\nevidence_ref:\n")
        self._write(
            f"{pack_dir}/05_claude_review_round_1.md",
            "round: 1\nreviewer: claude_code\nclaude_code_read_only: true\nverdict: pass\nblocking_issues:\n",
        )
        self._write(
            f"{pack_dir}/06_codex_response_round_1.md",
            "round: 1\nreviewer: codex\naddressed_claude_findings:\nvalidation_rerun:\nremaining_blocking_issues:\n",
        )
        self._write(
            f"{pack_dir}/07_claude_review_round_2.md",
            "round: 2\nreviewer: claude_code\nclaude_code_read_only: true\nverdict: pass\nblocking_issues:\n",
        )
        self._write(
            f"{pack_dir}/08_codex_response_round_2.md",
            "round: 2\nreviewer: codex\naddressed_claude_findings:\nvalidation_rerun:\nremaining_blocking_issues:\n",
        )
        self._write(
            f"{pack_dir}/09_claude_review_round_3.md",
            "round: 3\nreviewer: claude_code\nclaude_code_read_only: true\nverdict: pass\nblocking_issues:\n",
        )
        self._write(
            f"{pack_dir}/10_final_decision.md",
            "ai_cross_review_status: pass\n"
            "owner_participation: not_required\n"
            "rounds_completed: 3\n"
            "claude_code_read_only: true\n"
            "codex_fixes_or_rebuttals_recorded: true\n"
            "machine_gates_passed: true\n"
            "unresolved_blocking_issues: 0\n",
        )

    def test_validate_ai_cross_review_accepts_three_round_pack(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-test"
        self._write_valid_ai_cross_review_pack(pack_dir)

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-ai-cross-review-ok", stdout)
        self.assertIn("rounds=3", stdout)

    def test_validate_ai_cross_review_accepts_independent_codex_fallback_rounds(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-codex-fallback"
        self._write_valid_ai_cross_review_pack(pack_dir)
        for round_number, filename, reviewer_instance_id in [
            (1, "05_claude_review_round_1.md", "/root/audit_freeze_receipt"),
            (2, "07_claude_review_round_2.md", "/root/audit_warehouse_integrity"),
            (3, "09_claude_review_round_3.md", "/root/audit_legacy_review_gate"),
        ]:
            self._write(
                f"{pack_dir}/{filename}",
                f"round: {round_number}\n"
                "reviewer: independent_codex_fallback\n"
                "independent_codex_read_only: true\n"
                "fallback_reason: claude_code_unavailable\n"
                f"reviewer_instance_id: {reviewer_instance_id}\n"
                "independent_context: true\n"
                "files_reviewed:\n"
                "- workflow/gtpj_workflow.py\n"
                "commands_run:\n"
                "- python -m unittest\n"
                "verdict: pass\n"
                "blocking_issues:\n",
            )
        final_path = self.repo / pack_dir / "10_final_decision.md"
        final_path.write_text(
            final_path.read_text(encoding="utf-8").replace(
                "claude_code_read_only: true",
                "claude_code_read_only: false\nindependent_codex_fallback_read_only: true",
            ),
            encoding="utf-8",
        )
        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)
        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertIn("validate-ai-cross-review-ok", stdout)

    def test_validate_ai_cross_review_rejects_incomplete_codex_fallback_identity(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-bad-codex-fallback"
        self._write_valid_ai_cross_review_pack(pack_dir)
        self._write(
            f"{pack_dir}/05_claude_review_round_1.md",
            "round: 1\n"
            "reviewer: independent_codex_fallback\n"
            "independent_codex_read_only: true\n"
            "fallback_reason: claude_code_unavailable\n"
            "independent_context: true\n"
            "files_reviewed:\n"
            "- workflow/gtpj_workflow.py\n"
            "commands_run:\n"
            "- python -m unittest\n"
            "verdict: pass\n"
            "blocking_issues:\n",
        )
        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)
        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("reviewer_instance_id", stderr)

    def test_validate_ai_cross_review_rejects_placeholder_codex_fallback_identity(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-placeholder-codex-fallback"
        self._write_valid_ai_cross_review_pack(pack_dir)
        self._write(
            f"{pack_dir}/05_claude_review_round_1.md",
            "round: 1\n"
            "reviewer: independent_codex_fallback\n"
            "independent_codex_read_only: true\n"
            "fallback_reason: claude_code_unavailable\n"
            "reviewer_instance_id: reviewer-1\n"
            "independent_context: true\n"
            "files_reviewed:\n"
            "- workflow/gtpj_workflow.py\n"
            "commands_run:\n"
            "- python -m unittest\n"
            "verdict: pass\n"
            "blocking_issues:\n",
        )

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("no real reviewer_instance_id", stderr)

    def test_validate_ai_cross_review_rejects_reused_codex_fallback_identity(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-reused-codex-fallback"
        self._write_valid_ai_cross_review_pack(pack_dir)
        for round_number, filename in [
            (1, "05_claude_review_round_1.md"),
            (2, "07_claude_review_round_2.md"),
            (3, "09_claude_review_round_3.md"),
        ]:
            self._write(
                f"{pack_dir}/{filename}",
                f"round: {round_number}\n"
                "reviewer: independent_codex_fallback\n"
                "independent_codex_read_only: true\n"
                "fallback_reason: claude_code_unavailable\n"
                "reviewer_instance_id: /root/audit_same_reviewer\n"
                "independent_context: true\n"
                "files_reviewed:\n"
                "- workflow/gtpj_workflow.py\n"
                "commands_run:\n"
                "- python -m unittest\n"
                "verdict: pass\n"
                "blocking_issues:\n",
            )
        final_path = self.repo / pack_dir / "10_final_decision.md"
        final_path.write_text(
            final_path.read_text(encoding="utf-8").replace(
                "claude_code_read_only: true",
                "claude_code_read_only: false\nindependent_codex_fallback_read_only: true",
            ),
            encoding="utf-8",
        )

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("distinct real reviewer_instance_id", stderr)

    def test_validate_ai_cross_review_rejects_fallback_pack_claiming_claude_only(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-fallback-claims-claude"
        self._write_valid_ai_cross_review_pack(pack_dir)
        for round_number, filename, reviewer_instance_id in [
            (1, "05_claude_review_round_1.md", "/root/audit_freeze_receipt"),
            (2, "07_claude_review_round_2.md", "/root/audit_warehouse_integrity"),
            (3, "09_claude_review_round_3.md", "/root/audit_legacy_review_gate"),
        ]:
            self._write(
                f"{pack_dir}/{filename}",
                f"round: {round_number}\n"
                "reviewer: independent_codex_fallback\n"
                "independent_codex_read_only: true\n"
                "fallback_reason: claude_code_unavailable\n"
                f"reviewer_instance_id: {reviewer_instance_id}\n"
                "independent_context: true\n"
                "files_reviewed:\n"
                "- workflow/gtpj_workflow.py\n"
                "commands_run:\n"
                "- python -m unittest\n"
                "verdict: pass\n"
                "blocking_issues:\n",
            )

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual(1, code)
        self.assertEqual("", stdout)
        self.assertIn("cannot claim Claude Code review", stderr)

    def test_validate_ai_cross_review_rejects_non_pass_claude_verdict(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-non-pass"
        self._write_valid_ai_cross_review_pack(pack_dir)
        self._write(
            f"{pack_dir}/05_claude_review_round_1.md",
            "round: 1\n"
            "reviewer: claude_code\n"
            "claude_code_read_only: true\n"
            "verdict: needs_fix\n"
            "blocking_issues:\n",
        )

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("05_claude_review_round_1.md verdict must be pass", stderr)

    def test_validate_ai_cross_review_rejects_missing_round_three(self) -> None:
        pack_dir = "docs/agent_reviews/2026-07-03-bad"
        for filename in [
            "00_task.md",
            "01_codex_actions.md",
            "02_diff.patch",
            "03_validation.md",
            "04_claims.md",
            "05_claude_review_round_1.md",
            "06_codex_response_round_1.md",
            "07_claude_review_round_2.md",
            "08_codex_response_round_2.md",
            "10_final_decision.md",
        ]:
            self._write(f"{pack_dir}/{filename}", "placeholder\n")

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("missing review file: 09_claude_review_round_3.md", stderr)

    def test_run_ai_cross_review_creates_three_round_pack_with_fake_claude(self) -> None:
        self._write(
            "fake_claude.py",
            "import sys\n"
            "prompt = sys.stdin.read()\n"
            "with open('captured_claude_prompt.txt', 'a', encoding='utf-8', errors='replace') as handle:\n"
            "    handle.write(prompt + '\\n---PROMPT---\\n')\n"
            "print('round: fake')\n"
            "print('reviewer: claude_code')\n"
            "print('claude_code_read_only: true')\n"
            "print('verdict: pass')\n"
            "print('blocking_issues:')\n",
        )
        self._write("docs/example.md", "changed\n")
        validation_command = self._custom_full_validation_command()

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/run-test",
            "--slug",
            "run-test",
            "--task-title",
            "测试三轮 AI 交叉审核",
            "--review-tier",
            "strict-3",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            "--claude-command",
            sys.executable,
            "--claude-command-arg",
            "fake_claude.py",
            *self._passing_codex_pre_review_args(),
        )

        pack = self.repo / "docs/agent_reviews/run-test"
        debug_review = ""
        if pack.exists():
            debug_review = "\n".join(
                (pack / name).read_text(encoding="utf-8")
                for name in [
                    "05_claude_review_round_1.md",
                    "07_claude_review_round_2.md",
                    "09_claude_review_round_3.md",
                    "10_final_decision.md",
                ]
                if (pack / name).exists()
            )
        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout + stderr + debug_review)
        self.assertIn("run-ai-cross-review-ok", stdout)
        self.assertIn("tier=strict-3", stdout)
        self.assertTrue((pack / "02_focused_diff.md").exists())
        self.assertTrue((pack / "02_review_brief.md").exists())
        self.assertTrue((pack / "02_codex_named_thread_pre_review.md").exists())
        self.assertTrue((pack / "05_claude_review_round_1.md").exists())
        self.assertTrue((pack / "07_claude_review_round_2.md").exists())
        self.assertTrue((pack / "09_claude_review_round_3.md").exists())
        prompt_text = (self.repo / "captured_claude_prompt.txt").read_text(encoding="utf-8")
        brief_text = (pack / "02_review_brief.md").read_text(encoding="utf-8")
        pre_review_text = (pack / "02_codex_named_thread_pre_review.md").read_text(encoding="utf-8")
        round_text = (pack / "05_claude_review_round_1.md").read_text(encoding="utf-8")
        self.assertIn("02_codex_named_thread_pre_review.md", prompt_text)
        self.assertIn("02_review_brief.md", prompt_text)
        self.assertIn("02_focused_diff.md", prompt_text)
        self.assertIn("Do not read 02_diff.patch by default", prompt_text)
        self.assertIn("review_mode: blocking-only", brief_text)
        self.assertIn("prompt_profile: focused", brief_text)
        self.assertIn("review_tier: strict-3", brief_text)
        self.assertIn("lifecycle: completed_archived", pre_review_text)
        self.assertIn("archived_before_claude: true", pre_review_text)
        self.assertIn("archive_result_confirms_completion: true", pre_review_text)
        self.assertIn("verdict: pass", pre_review_text)
        self.assertIn("02_review_brief.md", round_text)
        self.assertIn("02_focused_diff.md", round_text)
        final_text = (pack / "10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("ai_cross_review_status: pass", final_text)
        self.assertIn("review_tier: strict-3", final_text)
        self.assertIn("claude_rounds_required: 3", final_text)
        self.assertIn("codex_named_thread_pre_review: pass", final_text)
        self.assertIn("unresolved_blocking_issues: 0", final_text)

    def test_run_ai_cross_review_review_one_creates_one_claude_round(self) -> None:
        self._write(
            "fake_claude.py",
            "print('round: fake')\n"
            "print('reviewer: claude_code')\n"
            "print('claude_code_read_only: true')\n"
            "print('verdict: pass')\n"
            "print('blocking_issues:')\n",
        )
        validation_command = self._custom_full_validation_command()

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/review-one",
            "--slug",
            "review-one",
            "--review-tier",
            "review-1",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            "--claude-command",
            sys.executable,
            "--claude-command-arg",
            "fake_claude.py",
            *self._passing_codex_pre_review_args(),
        )

        pack = self.repo / "docs/agent_reviews/review-one"
        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout)
        self.assertIn("tier=review-1", stdout)
        self.assertTrue((pack / "05_claude_review_round_1.md").exists())
        self.assertFalse((pack / "06_codex_response_round_1.md").exists())
        self.assertFalse((pack / "07_claude_review_round_2.md").exists())
        final_text = (pack / "10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("review_tier: review-1", final_text)
        self.assertIn("claude_rounds_required: 1", final_text)

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", "docs/agent_reviews/review-one")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("rounds=1", stdout)

    def test_run_ai_cross_review_fast_uses_no_claude_rounds(self) -> None:
        self._write(
            "fake_claude.py",
            "raise SystemExit('Claude should not run for fast tier')\n",
        )
        validation_command = f'"{sys.executable}" -c "print(123)"'

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/fast",
            "--slug",
            "fast",
            "--review-tier",
            "fast",
            "--risk-level",
            "low",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            "--claude-command",
            sys.executable,
            "--claude-command-arg",
            "fake_claude.py",
            *self._passing_codex_pre_review_args(),
        )

        pack = self.repo / "docs/agent_reviews/fast"
        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout)
        self.assertIn("tier=fast", stdout)
        self.assertFalse((pack / "05_claude_review_round_1.md").exists())
        final_text = (pack / "10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("review_tier: fast", final_text)
        self.assertIn("claude_rounds_required: 0", final_text)
        self.assertIn("codex_named_thread_pre_review: pass", final_text)
        claims_text = (pack / "04_claims.md").read_text(encoding="utf-8")
        self.assertIn("evidence_ref: 02_codex_named_thread_pre_review.md", claims_text)
        self.assertNotIn("05_claude_review_round_1.md", claims_text)

        code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", "docs/agent_reviews/fast")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("rounds=0", stdout)

    def test_run_ai_cross_review_rejects_missing_machine_validation(self) -> None:
        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/no-validation",
            "--slug",
            "no-validation",
            "--review-tier",
            "fast",
            "--risk-level",
            "low",
            "--no-default-validation",
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("requires machine validation", stderr)

    def test_run_ai_cross_review_missing_pre_review_blocks_pack(self) -> None:
        validation_command = f'"{sys.executable}" -c "print(123)"'

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/missing-pre-review",
            "--slug",
            "missing-pre-review",
            "--review-tier",
            "fast",
            "--risk-level",
            "low",
            "--no-default-validation",
            "--validation-command",
            validation_command,
        )

        self.assertEqual("", stderr)
        self.assertEqual(1, code)
        self.assertIn("status=blocked", stdout)
        final_text = (self.repo / "docs/agent_reviews/missing-pre-review/10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("codex_named_thread_pre_review: blocked", final_text)

    def test_run_ai_cross_review_rejects_high_risk_non_strict_tier(self) -> None:
        validation_command = self._custom_full_validation_command()

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/high-risk",
            "--slug",
            "high-risk",
            "--risk-level",
            "high",
            "--review-tier",
            "review-1",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("requires --review-tier strict-3", stderr)

    def test_run_ai_cross_review_rejects_weak_custom_full_equivalent_validation(self) -> None:
        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/weak-full",
            "--slug",
            "weak-full",
            "--review-tier",
            "review-1",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            f'"{sys.executable}" -c "print(123)"',
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("custom-full-equivalent validation missing core gates", stderr)

    def test_run_ai_cross_review_rejects_formal_result_file_non_strict_tier(self) -> None:
        self._write("experiments/v1/confirmation/result.yaml", "H: 75.0\n")

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/formal-result",
            "--slug",
            "formal-result",
            "--review-tier",
            "review-1",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            self._custom_full_validation_command(),
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("requires --review-tier strict-3", stderr)

    def test_run_ai_cross_review_rejects_unstructured_pre_review_archive_result(self) -> None:
        validation_command = f'"{sys.executable}" -c "print(123)"'

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/bad-close-result",
            "--slug",
            "bad-close-result",
            "--review-tier",
            "fast",
            "--risk-level",
            "low",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            "--codex-pre-review-thread-id",
            "thread-test-001",
            "--codex-pre-review-thread-title",
            "ATTEMPT-REVIEW | Codex Pre Review",
            "--codex-pre-review-archive-result",
            "closed",
            "--codex-pre-review-verdict",
            "pass",
        )

        self.assertEqual("", stderr)
        self.assertEqual(1, code)
        self.assertIn("status=blocked", stdout)
        pre_review_text = (self.repo / "docs/agent_reviews/bad-close-result/02_codex_named_thread_pre_review.md").read_text(encoding="utf-8")
        self.assertIn("archive_result_confirms_completion: false", pre_review_text)

    def test_validate_ai_cross_review_rejects_handwritten_bad_archive_result(self) -> None:
        validation_command = f'"{sys.executable}" -c "print(123)"'

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/handwritten-bad-close",
            "--slug",
            "handwritten-bad-close",
            "--review-tier",
            "fast",
            "--risk-level",
            "low",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code, stdout)
        self._write(
            "docs/agent_reviews/handwritten-bad-close/02_codex_named_thread_pre_review.md",
            "codex_named_thread_pre_review: pass\n"
            "named_thread_required: true\n"
            "thread_id: thread-test-001\n"
            "thread_title: ATTEMPT-REVIEW | Codex Pre Review\n"
            "lifecycle: completed_archived\n"
            "archived_before_claude: true\n"
            "archive_result_confirms_completion: true\n"
            "archive_result: closed\n"
            "verdict: pass\n"
            "blocking_issues:\n"
            "notes: forged marker should not pass validation\n",
        )

        code, stdout, stderr = self._run_main(
            "validate-ai-cross-review",
            "--path",
            "docs/agent_reviews/handwritten-bad-close",
        )

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("archive_result must include matching thread id", stderr)

    def test_run_ai_cross_review_skip_claude_blocks_pack(self) -> None:
        validation_command = self._custom_full_validation_command()

        code, stdout, stderr = self._run_main(
            "run-ai-cross-review",
            "--path",
            "docs/agent_reviews/skip-claude",
            "--slug",
            "skip-claude",
            "--review-tier",
            "review-1",
            "--validation-profile",
            "custom-full-equivalent",
            "--no-default-validation",
            "--validation-command",
            validation_command,
            "--skip-claude",
            *self._passing_codex_pre_review_args(),
        )

        self.assertEqual("", stderr)
        self.assertEqual(1, code)
        self.assertIn("status=blocked", stdout)
        final_text = (self.repo / "docs/agent_reviews/skip-claude/10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("ai_cross_review_status: blocked", final_text)

    def test_validate_workflow_consistency_accepts_preflight_markers(self) -> None:
        self._write_minimal_workflow_manifest()
        self._write("docs/workflow/README.md", "# Workflow\n")
        self._write("docs/workflow/START_HERE.md", "formal_runner_allowed\nmulti_agent_preflight\nreview_tier\nreview-1\nstrict-3\n正文必须使用中文\n不允许整段英文说明\n框架记录只跟\nformal_pending\norphan_runtime_plan\n明确入口硬规则\n执行授权\n不得反复确认\npre_run_planned\nreport-new-completions\n代码审核不被 `server_frozen_runner` 豁免\n")
        self._write("docs/workflow/WORKFLOW_KERNEL.md", "multi-agent-preflight\nformal_evidence_allowed\nreview_tier\nreview-1\nstrict-3\n文档语言硬规则\n正文必须使用中文\n框架记录绑定\nformal_pending\norphan_runtime_plan\n开启多agents智能体工作流\nlive_multi_agent_monitor\nplanning gate\nfiles_reviewed\n独立输出文件\nallow/block/propose\nskill 镜像\nactive docs\nhelper 测试\nreport-new-completions\n代码审核不被 `server_frozen_runner` 豁免\n")
        self._write("docs/workflow/core/QUICK_START.md", "repro-status\nbaseline_repro_status\n")
        self._write("docs/workflow/core/WORKFLOW_ROUTER.md", "# Router\nformal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\nnamed_thread_titles\n<subject_id> | <Role Label>\nfiles_reviewed\nreport-new-completions\n")
        self._write("docs/workflow/core/TASK_START_MINI.md", "runner_scope\nblocked_reason\n")
        self._write("docs/workflow/core/TASK_START_CARD.md", "multi_agent_preflight\nformal_evidence_allowed\nagent_status_refs\nrole_file_plan\nfiles_reviewed\n是否需要再次确认\n")
        self._write("docs/workflow/protocols/agent_cleanup_protocol.md", "agent cleanup\n")
        self._write("docs/workflow/protocols/agent_orchestration.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n<subject_id> | <Role Label>\nfiles_reviewed\n分文件复核\nreport-new-completions\n")
        self._write(
            "docs/workflow/protocols/ai_cross_review_protocol.md",
            "owner_participation: not_required\nclaude_code_read_only: true\nreview_tier\nfast\nreview-1\nstrict-3\n02_codex_named_thread_pre_review.md\ncompleted_archived\narchive_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\nrun-ai-cross-review\nvalidate-ai-cross-review\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n代码审核不被 `server_frozen_runner` 豁免\n",
        )
        self._write(
            "docs/workflow/protocols/module_template_selection.md",
            "feature_adapter_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nvalidate-trial-meta\nstandard GZSL U/S/H/ZS\nbase_code_tag\nstandard_gzsl_training_template.py\nstrict_template_entry\n文档语言边界\n不能写整段英文说明\n框架记录的对象\n",
        )
        self._write("docs/workflow/protocols/experiment_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/protocols/module_trial_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/protocols/mixed_experiment_campaign_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write(
            "docs/workflow/playbooks/innovation.md",
            "START_HERE.md\nWORKFLOW_KERNEL.md\n探索 / 正式分界\nformal_evidence_allowed\nmodule_template_selection.md\nmodule_source.md\nvalidate-trial-meta\nstrict_template_entry\n",
        )
        self._write("docs/workflow/playbooks/tune.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/ablation.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/confirmation.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/promotion.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/mixed_campaign.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/paper_intake.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/paper_to_experiment.md", "START_HERE.md\nWORKFLOW_KERNEL.md\nbase_code_tag\nmodule_template_selection.md\nmodule_source.md\n")
        self._write("experiments/templates/agent_summary_template.md", "multi_agent_preflight:\nformal_runner_allowed:\nagent_output_refs:\nfiles_reviewed:\nagent_cleanup:\nai_cross_review:\n")
        self._write(
            "experiments/templates/ai_cross_review_template.md",
            "review_tier\nfast\nreview-1\nstrict-3\n02_codex_named_thread_pre_review.md\ncompleted_archived\narchive_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
        )
        self._write("experiments/templates/quality_check_template.md", "review_tier\nvalidate-ai-cross-review\nunresolved_blocking_issues: 0\n")
        self._write("experiments/templates/run_receipt_template.yaml", "schema_version: gtpj.run_receipt.v0\nmulti_agent_preflight:\nagent_output_refs:\n")
        self._write("experiments/templates/TRIAL_ATTEMPTS_template.md", "formal_pending\norphan_runtime_plan\nStatus\nFormal\n")
        self._write("experiments/templates/modules/README.md", "standard_gzsl_module_framework_template.py\nstandard_gzsl_training_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nstrict_template_entry\nU, S, H, ZS\n训练入口模式\n不允许改变\n")
        self._add_confirmation_rule_markers()

        code, stdout, stderr = self._run_main("validate-workflow-consistency")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-workflow-consistency-ok", stdout)

    def test_validate_workflow_consistency_rejects_stale_ai_review_phrase(self) -> None:
        self._write_minimal_workflow_manifest()
        self._write("docs/workflow/README.md", "# Workflow\n")
        self._write("docs/workflow/START_HERE.md", "formal_runner_allowed\nmulti_agent_preflight\nreview_tier\nreview-1\nstrict-3\n正文必须使用中文\n不允许整段英文说明\n框架记录只跟\nformal_pending\norphan_runtime_plan\n明确入口硬规则\n执行授权\n不得反复确认\npre_run_planned\nreport-new-completions\n代码审核不被 `server_frozen_runner` 豁免\n重复 3 轮\n")
        self._write("docs/workflow/WORKFLOW_KERNEL.md", "multi-agent-preflight\nformal_evidence_allowed\nreview_tier\nreview-1\nstrict-3\n文档语言硬规则\n正文必须使用中文\n框架记录绑定\nformal_pending\norphan_runtime_plan\n开启多agents智能体工作流\nlive_multi_agent_monitor\nplanning gate\nfiles_reviewed\n独立输出文件\nallow/block/propose\nskill 镜像\nactive docs\nhelper 测试\nreport-new-completions\n代码审核不被 `server_frozen_runner` 豁免\n")
        self._write("docs/workflow/core/QUICK_START.md", "repro-status\nbaseline_repro_status\n")
        self._write("docs/workflow/core/WORKFLOW_ROUTER.md", "# Router\nformal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\nnamed_thread_titles\n<subject_id> | <Role Label>\nfiles_reviewed\nreport-new-completions\n")
        self._write("docs/workflow/core/TASK_START_MINI.md", "runner_scope\nblocked_reason\n")
        self._write("docs/workflow/core/TASK_START_CARD.md", "multi_agent_preflight\nformal_evidence_allowed\nagent_status_refs\nrole_file_plan\nfiles_reviewed\n是否需要再次确认\n")
        self._write("docs/workflow/protocols/agent_cleanup_protocol.md", "agent cleanup\n")
        self._write("docs/workflow/protocols/agent_orchestration.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n<subject_id> | <Role Label>\nfiles_reviewed\n分文件复核\nreport-new-completions\n")
        self._write(
            "docs/workflow/protocols/ai_cross_review_protocol.md",
            "owner_participation: not_required\nclaude_code_read_only: true\nreview_tier\nfast\nreview-1\nstrict-3\n02_codex_named_thread_pre_review.md\ncompleted_archived\narchive_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\nrun-ai-cross-review\nvalidate-ai-cross-review\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n代码审核不被 `server_frozen_runner` 豁免\n",
        )
        self._write(
            "docs/workflow/protocols/module_template_selection.md",
            "feature_adapter_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nvalidate-trial-meta\nstandard GZSL U/S/H/ZS\nbase_code_tag\nstandard_gzsl_training_template.py\nstrict_template_entry\n文档语言边界\n不能写整段英文说明\n框架记录的对象\n",
        )
        self._write("docs/workflow/protocols/experiment_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/protocols/module_trial_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write("docs/workflow/protocols/mixed_experiment_campaign_protocol.md", "formal_pending\norphan_runtime_plan\n")
        self._write(
            "docs/workflow/playbooks/innovation.md",
            "START_HERE.md\nWORKFLOW_KERNEL.md\n探索 / 正式分界\nformal_evidence_allowed\nmodule_template_selection.md\nmodule_source.md\nvalidate-trial-meta\nstrict_template_entry\n",
        )
        for name in ["tune", "ablation", "confirmation", "promotion", "mixed_campaign", "paper_intake"]:
            self._write(f"docs/workflow/playbooks/{name}.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/paper_to_experiment.md", "START_HERE.md\nWORKFLOW_KERNEL.md\nbase_code_tag\nmodule_template_selection.md\nmodule_source.md\n")
        self._write("experiments/templates/agent_summary_template.md", "multi_agent_preflight:\nformal_runner_allowed:\nagent_output_refs:\nfiles_reviewed:\nagent_cleanup:\nai_cross_review:\n")
        self._write(
            "experiments/templates/ai_cross_review_template.md",
            "review_tier\nfast\nreview-1\nstrict-3\n02_codex_named_thread_pre_review.md\ncompleted_archived\narchive_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
        )
        self._write("experiments/templates/quality_check_template.md", "review_tier\nvalidate-ai-cross-review\nunresolved_blocking_issues: 0\n")
        self._write("experiments/templates/run_receipt_template.yaml", "schema_version: gtpj.run_receipt.v0\nmulti_agent_preflight:\nagent_output_refs:\n")
        self._write("experiments/templates/TRIAL_ATTEMPTS_template.md", "formal_pending\norphan_runtime_plan\nStatus\nFormal\n")
        self._write("experiments/templates/modules/README.md", "standard_gzsl_module_framework_template.py\nstandard_gzsl_training_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nstrict_template_entry\nU, S, H, ZS\n训练入口模式\n不允许改变\n")
        self._add_confirmation_rule_markers()

        code, stdout, stderr = self._run_main("validate-workflow-consistency")

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("contains stale AI review phrase", stderr)
        self.assertIn("重复 3 轮", stderr)

    def test_confirmation_rule_map_lists_sync_dictionary(self) -> None:
        code, stdout, stderr = self._run_main("confirmation-rule-map")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("confirmation-rule-map", stdout)
        self.assertIn("repeat_type: exact_repeat", stdout)
        self.assertIn("docs/workflow/WORKFLOW_KERNEL.md", stdout)
        self.assertIn("experiments/templates/run_receipt_template.yaml", stdout)

    def test_list_workflow_files_groups_manifest_entries(self) -> None:
        self._write_minimal_workflow_manifest()
        for rel_path in [
            "README.md",
            "START_HERE.md",
            "WORKFLOW_KERNEL.md",
            "core/QUICK_START.md",
            "core/WORKFLOW_ROUTER.md",
            "core/TASK_START_MINI.md",
            "core/TASK_START_CARD.md",
            "core/AGENT_RUNTIME_HARD_GATE.md",
            "protocols/agent_cleanup_protocol.md",
            "protocols/ai_cross_review_protocol.md",
            "protocols/module_template_selection.md",
            "playbooks/tune.md",
            "playbooks/ablation.md",
            "playbooks/confirmation.md",
            "playbooks/innovation.md",
            "playbooks/promotion.md",
            "playbooks/mixed_campaign.md",
            "playbooks/paper_intake.md",
            "playbooks/paper_to_experiment.md",
        ]:
            self._write(f"docs/workflow/{rel_path}", "START_HERE.md\nWORKFLOW_KERNEL.md\n")

        code, stdout, stderr = self._run_main("list-workflow-files")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("workflow-files manifest=docs/workflow/WORKFLOW_MANIFEST.yaml", stdout)
        self.assertIn("daily_entry:", stdout)
        self.assertIn("core:", stdout)
        self.assertIn("playbook:", stdout)
        self.assertIn("manifest_errors=0", stdout)

    def test_validate_remote_accepts_origin_refs_matching_local_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_accepts_annotated_v1_tag(self) -> None:
        self._git("tag", "-d", "v1")
        self._git("tag", "-a", "v1", "-m", "annotated v1")
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_accepts_main_ahead_of_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._write("governance.md", "main ledger update\n")
            self._git("add", "governance.md")
            self._git("commit", "-m", "add governance ledger")
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_uses_local_main_not_current_feature_head(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._git("switch", "-c", "feature/local-work")
            self._write("feature.txt", "feature-only commit\n")
            self._git("add", "feature.txt")
            self._git("commit", "-m", "feature-only work")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_rejects_branch_named_v1_without_local_tag(self) -> None:
        self._git("tag", "-d", "v1")
        self._git("branch", "v1")

        code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("Missing local authoritative tag: v1", stderr)

    def test_validate_remote_rejects_remote_branch_named_v1_without_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main")
            self._git("push", "origin", "HEAD:refs/heads/v1")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("Missing remote ref: origin/v1 (refs/tags/v1)", stderr)

    def test_validate_remote_rejects_origin_main_ahead_of_local_main(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            local_main = self._git("rev-parse", "main").stdout.strip()
            self._write("remote-ahead.txt", "remote main ahead\n")
            self._git("add", "remote-ahead.txt")
            self._git("commit", "-m", "remote main ahead")
            self._git("push", "origin", "HEAD:refs/heads/main")
            self._git("reset", "--hard", local_main)

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/main", stderr)

    def test_validate_remote_rejects_origin_main_not_matching_local_main(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._write("marker.txt", "new commit\n")
            self._git("add", "marker.txt")
            self._git("commit", "-m", "local main not pushed")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/main", stderr)

    def test_validate_remote_rejects_misaligned_origin_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._git("switch", "-c", "move-v1-tag-source")
            self._write("marker.txt", "remote tag moved\n")
            self._git("add", "marker.txt")
            self._git("commit", "-m", "move remote v1 tag only")
            self._git("push", "--force", "origin", "HEAD:refs/tags/v1")
            self._git("switch", "main")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/v1", stderr)

    def test_validate_remote_rejects_local_main_not_containing_v1(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("checkout", "--orphan", "rewritten-main")
            self._write("replacement.txt", "replacement main without v1 history\n")
            self._git("add", ".")
            self._git("commit", "-m", "replace main history")
            self._git("branch", "-M", "main")
            self._git("push", "origin", "main", "v1")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("local main must contain local v1 tag", stderr)


if __name__ == "__main__":
    unittest.main()
