from __future__ import annotations

import contextlib
from collections import Counter
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

    def _write(self, relative: str, content: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

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
            "--codex-pre-review-agent-id",
            "agent-test-001",
            "--codex-pre-review-agent-name",
            "Temp Review Agent",
            "--codex-pre-review-close-result",
            "agent_id=agent-test-001 previous_status=completed closed: true",
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
        bad_display_name: bool = False,
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
                f"# {role}\nrole_key: {role}\nagent_instance_id: {instance_id}\noutput: {role} checked test gate.\n",
            )
        agent_ids = (
            "temporary_subagent_ids:\n"
            "  runner_monitor: 019f1111-1111-7111-8111-111111111111\n"
            "  interface_checker: 019f2222-2222-7222-8222-222222222222\n"
            "  evidence_quality_checker: 019f3333-3333-7333-8333-333333333333\n"
        )
        if duplicate_agent_id:
            agent_ids = (
                "temporary_subagent_ids:\n"
                "  runner_monitor: 019f1111-1111-7111-8111-111111111111\n"
                "  interface_checker: 019f2222-2222-7222-8222-222222222222\n"
                "  evidence_quality_checker: 019f2222-2222-7222-8222-222222222222\n"
            )
        if not include_agent_ids:
            agent_ids = "temporary_subagent_ids:\n  runner_monitor: temporary_subagent\n"
        display_names = (
            "temporary_subagent_display_names:\n"
            "  runner_monitor: ATTEMPT-001 | Runner Monitor\n"
            "  interface_checker: ATTEMPT-001 | Interface Checker\n"
            "  evidence_quality_checker: ATTEMPT-001 | Evidence Quality Checker\n"
        )
        if bad_display_name:
            display_names = (
                "temporary_subagent_display_names:\n"
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
            "right_sidebar_retention_policy: current_stage_active_only\n"
            "close_completed_agents_on_stage_end: true\n"
            "closed_agents_record: AGENT_ACTIVITY.md\n"
        )
        if not include_owner_monitor:
            owner_monitor = ""
        preflight = (
            "multi_agent_preflight:\n"
            "  required_agents_spawned: true\n"
            "  agent_instance_ids_present: true\n"
            "  agent_status_refs_valid: true\n"
            "  independent_outputs_present: true\n"
            "  agent_output_refs_valid: true\n"
            "  pre_run_allow_checks_passed: true\n"
            "  agent_runtime_validated: true\n"
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
            "agent_instance_mode: temporary_subagent\n"
            "lifecycle: workflow_scoped\n"
            "ui_visibility: right_sidebar_temporary_agents\n"
            "tool_support_real_multi_agent_available: true\n"
            "spawn_tool: multi_agent_v1.spawn_agent\n"
            "single_agent_execution: false\n"
            "runner_start_allowed: true\n"
            "formal_runner_allowed: true\n"
            "formal_evidence_allowed: true\n"
            f"{owner_monitor}"
            f"{agent_ids}"
            f"{display_names}"
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
        self.assertEqual(groups["direction_confirmation"], 20)
        self.assertEqual(groups["direction_neighbor"], 20)
        self.assertEqual(groups["sanity_control"], 10)
        self.assertEqual(phases["explore"], 50)
        self.assertNotIn("repeat", phases)
        self.assertEqual(names["dr009_direction_sample_h48_w0.45_a0.005"], 20)
        self.assertEqual(names["dr008_direction_sample_h48_w0.5_a0.005"], 10)
        self.assertEqual(names["dr010_direction_sample_h64_w0.5_a0.01"], 10)
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
        self.assertEqual(groups["must_reproduce"], 12)
        self.assertEqual(groups["direction_microgrid"], 24)
        self.assertEqual(groups["local_direction_micro"], 6)
        self.assertEqual(groups["direction_pse_micro"], 6)
        self.assertEqual(names["dr009_direction_sample_h48_w0.45_a0.005"], 6)
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

    def test_dynamic_routing_batch_plan_has_dr035_min6_confirm_jobs(self) -> None:
        jobs = self.module.build_dynamic_routing_jobs(seed=99, profile="dr035-min6-confirm")
        updates = [job["config_updates"] for job in jobs]

        self.assertEqual(len(jobs), 6)
        self.assertEqual([job["job_id"] for job in jobs], [f"DR-{i:03d}" for i in range(1, 7)])
        self.assertEqual([job["group"] for job in jobs], ["confirm_dr035"] * 6)
        self.assertEqual([job["phase"] for job in jobs], ["explore"] * 6)
        self.assertEqual([job["seed"] for job in jobs], [5] * 6)
        self.assertEqual([update["random_seed"] for update in updates], [5] * 6)
        self.assertEqual(
            [job["name"] for job in jobs],
            [
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r1",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r2",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r3",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r4",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r5",
                "dr035_direction_sample_h48_w0.525_a0.005_s5_r6",
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

    def test_plan_dynamic_routing_batch_uses_attempt_scoped_warehouse_from_gate(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/attempts/ATTEMPT-007/agent_runtime.yaml")

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

    def test_plan_dynamic_routing_batch_accepts_explicit_attempt_id_for_warehouse(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")

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

    def test_plan_dynamic_routing_batch_accepts_workflow_v2_10_job_profile(self) -> None:
        trial_dir = "experiments/module_trials/IDEA-0003_x/TRIAL-001_x"
        self._write(f"{trial_dir}/config.yaml", "version: v5\n")
        gate_path = self._write_agent_runtime_gate(path=f"{trial_dir}/agent_runtime.yaml")

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

    def test_validate_agent_runtime_rejects_placeholder_agent_id(self) -> None:
        gate_path = self._write_agent_runtime_gate(include_agent_ids=False)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("not a real agent/thread id", stderr)

    def test_validate_agent_runtime_rejects_random_display_name(self) -> None:
        gate_path = self._write_agent_runtime_gate(bad_display_name=True)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("uses a random legacy nickname", stderr)

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

    def test_agent_cleanup_plan_lists_keep_and_close_agents(self) -> None:
        gate_path = self._write_agent_runtime_gate()

        code, stdout, stderr = self._run_main("agent-cleanup-plan", "--path", str(gate_path))

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("agent-cleanup-plan path=", stdout)
        self.assertIn("keep_count=1", stdout)
        self.assertIn("KEEP role=runner_monitor", stdout)
        self.assertIn("close_count=2", stdout)
        self.assertIn("CLOSE role=interface_checker", stdout)
        self.assertIn("CLOSE role=evidence_quality_checker", stdout)
        self.assertIn("duplicate_instance_ids=0", stdout)

    def test_validate_agent_runtime_rejects_missing_owner_monitor_mode(self) -> None:
        gate_path = self._write_agent_runtime_gate(include_owner_monitor=False)

        code, _stdout, stderr = self._run_main("validate-agent-runtime", "--path", str(gate_path))

        self.assertEqual(1, code)
        self.assertIn("missing owner_monitor_mode", stderr)

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
        self.assertTrue((pack / "02_codex_temp_agent_pre_review.md").exists())
        self.assertTrue((pack / "05_claude_review_round_1.md").exists())
        self.assertTrue((pack / "07_claude_review_round_2.md").exists())
        self.assertTrue((pack / "09_claude_review_round_3.md").exists())
        prompt_text = (self.repo / "captured_claude_prompt.txt").read_text(encoding="utf-8")
        brief_text = (pack / "02_review_brief.md").read_text(encoding="utf-8")
        pre_review_text = (pack / "02_codex_temp_agent_pre_review.md").read_text(encoding="utf-8")
        round_text = (pack / "05_claude_review_round_1.md").read_text(encoding="utf-8")
        self.assertIn("02_codex_temp_agent_pre_review.md", prompt_text)
        self.assertIn("02_review_brief.md", prompt_text)
        self.assertIn("02_focused_diff.md", prompt_text)
        self.assertIn("Do not read 02_diff.patch by default", prompt_text)
        self.assertIn("review_mode: blocking-only", brief_text)
        self.assertIn("prompt_profile: focused", brief_text)
        self.assertIn("review_tier: strict-3", brief_text)
        self.assertIn("lifecycle: completed_closed", pre_review_text)
        self.assertIn("closed_before_claude: true", pre_review_text)
        self.assertIn("close_result_confirms_completion: true", pre_review_text)
        self.assertIn("verdict: pass", pre_review_text)
        self.assertIn("02_review_brief.md", round_text)
        self.assertIn("02_focused_diff.md", round_text)
        final_text = (pack / "10_final_decision.md").read_text(encoding="utf-8")
        self.assertIn("ai_cross_review_status: pass", final_text)
        self.assertIn("review_tier: strict-3", final_text)
        self.assertIn("claude_rounds_required: 3", final_text)
        self.assertIn("codex_temp_agent_pre_review: pass", final_text)
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
        self.assertIn("codex_temp_agent_pre_review: pass", final_text)
        claims_text = (pack / "04_claims.md").read_text(encoding="utf-8")
        self.assertIn("evidence_ref: 02_codex_temp_agent_pre_review.md", claims_text)
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
        self.assertIn("codex_temp_agent_pre_review: blocked", final_text)

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

    def test_run_ai_cross_review_rejects_unstructured_pre_review_close_result(self) -> None:
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
            "--codex-pre-review-agent-id",
            "agent-test-001",
            "--codex-pre-review-agent-name",
            "Temp Review Agent",
            "--codex-pre-review-close-result",
            "closed",
            "--codex-pre-review-verdict",
            "pass",
        )

        self.assertEqual("", stderr)
        self.assertEqual(1, code)
        self.assertIn("status=blocked", stdout)
        pre_review_text = (self.repo / "docs/agent_reviews/bad-close-result/02_codex_temp_agent_pre_review.md").read_text(encoding="utf-8")
        self.assertIn("close_result_confirms_completion: false", pre_review_text)

    def test_validate_ai_cross_review_rejects_handwritten_bad_close_result(self) -> None:
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
            "docs/agent_reviews/handwritten-bad-close/02_codex_temp_agent_pre_review.md",
            "codex_temp_agent_pre_review: pass\n"
            "temporary_agent_required: true\n"
            "agent_instance_id: agent-test-001\n"
            "ui_display_name: Temp Review Agent\n"
            "lifecycle: completed_closed\n"
            "closed_before_claude: true\n"
            "close_result_confirms_completion: true\n"
            "close_result: closed\n"
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
        self.assertIn("close_result must include matching agent id", stderr)

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
        self._write("docs/workflow/START_HERE.md", "formal_runner_allowed\nmulti_agent_preflight\nreview_tier\nreview-1\nstrict-3\n")
        self._write("docs/workflow/WORKFLOW_KERNEL.md", "multi-agent-preflight\nformal_evidence_allowed\nreview_tier\nreview-1\nstrict-3\n")
        self._write("docs/workflow/core/QUICK_START.md", "repro-status\nbaseline_repro_status\n")
        self._write("docs/workflow/core/WORKFLOW_ROUTER.md", "# Router\n")
        self._write("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\ntemporary_subagent_display_names\n<subject_id> | <Role Label>\n")
        self._write("docs/workflow/core/TASK_START_MINI.md", "runner_scope\nblocked_reason\n")
        self._write("docs/workflow/core/TASK_START_CARD.md", "multi_agent_preflight\nformal_evidence_allowed\nagent_status_refs\n")
        self._write("docs/workflow/protocols/agent_cleanup_protocol.md", "agent cleanup\n")
        self._write("docs/workflow/protocols/agent_orchestration.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n<subject_id> | <Role Label>\n")
        self._write(
            "docs/workflow/protocols/ai_cross_review_protocol.md",
            "owner_participation: not_required\nclaude_code_read_only: true\nreview_tier\nfast\nreview-1\nstrict-3\n02_codex_temp_agent_pre_review.md\ncompleted_closed\nclose_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\nrun-ai-cross-review\nvalidate-ai-cross-review\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n",
        )
        self._write(
            "docs/workflow/protocols/module_template_selection.md",
            "feature_adapter_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nvalidate-trial-meta\nstandard GZSL U/S/H/ZS\nbase_code_tag\nstandard_gzsl_training_template.py\nstrict_template_entry\n",
        )
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
        self._write("experiments/templates/agent_summary_template.md", "multi_agent_preflight:\nformal_runner_allowed:\nagent_output_refs:\nagent_cleanup:\nai_cross_review:\n")
        self._write(
            "experiments/templates/ai_cross_review_template.md",
            "review_tier\nfast\nreview-1\nstrict-3\n02_codex_temp_agent_pre_review.md\ncompleted_closed\nclose_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
        )
        self._write("experiments/templates/quality_check_template.md", "review_tier\nvalidate-ai-cross-review\nunresolved_blocking_issues: 0\n")
        self._write("experiments/templates/run_receipt_template.yaml", "schema_version: gtpj.run_receipt.v0\nmulti_agent_preflight:\nagent_output_refs:\n")
        self._write("experiments/templates/modules/README.md", "standard_gzsl_module_framework_template.py\nstandard_gzsl_training_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nstrict_template_entry\nU, S, H, ZS\n")

        code, stdout, stderr = self._run_main("validate-workflow-consistency")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-workflow-consistency-ok", stdout)

    def test_validate_workflow_consistency_rejects_stale_ai_review_phrase(self) -> None:
        self._write_minimal_workflow_manifest()
        self._write("docs/workflow/README.md", "# Workflow\n")
        self._write("docs/workflow/START_HERE.md", "formal_runner_allowed\nmulti_agent_preflight\nreview_tier\nreview-1\nstrict-3\n重复 3 轮\n")
        self._write("docs/workflow/WORKFLOW_KERNEL.md", "multi-agent-preflight\nformal_evidence_allowed\nreview_tier\nreview-1\nstrict-3\n")
        self._write("docs/workflow/core/QUICK_START.md", "repro-status\nbaseline_repro_status\n")
        self._write("docs/workflow/core/WORKFLOW_ROUTER.md", "# Router\n")
        self._write("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\ntemporary_subagent_display_names\n<subject_id> | <Role Label>\n")
        self._write("docs/workflow/core/TASK_START_MINI.md", "runner_scope\nblocked_reason\n")
        self._write("docs/workflow/core/TASK_START_CARD.md", "multi_agent_preflight\nformal_evidence_allowed\nagent_status_refs\n")
        self._write("docs/workflow/protocols/agent_cleanup_protocol.md", "agent cleanup\n")
        self._write("docs/workflow/protocols/agent_orchestration.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n<subject_id> | <Role Label>\n")
        self._write(
            "docs/workflow/protocols/ai_cross_review_protocol.md",
            "owner_participation: not_required\nclaude_code_read_only: true\nreview_tier\nfast\nreview-1\nstrict-3\n02_codex_temp_agent_pre_review.md\ncompleted_closed\nclose_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\nrun-ai-cross-review\nvalidate-ai-cross-review\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n",
        )
        self._write(
            "docs/workflow/protocols/module_template_selection.md",
            "feature_adapter_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nvalidate-trial-meta\nstandard GZSL U/S/H/ZS\nbase_code_tag\nstandard_gzsl_training_template.py\nstrict_template_entry\n",
        )
        self._write(
            "docs/workflow/playbooks/innovation.md",
            "START_HERE.md\nWORKFLOW_KERNEL.md\n探索 / 正式分界\nformal_evidence_allowed\nmodule_template_selection.md\nmodule_source.md\nvalidate-trial-meta\nstrict_template_entry\n",
        )
        for name in ["tune", "ablation", "confirmation", "promotion", "mixed_campaign", "paper_intake"]:
            self._write(f"docs/workflow/playbooks/{name}.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
        self._write("docs/workflow/playbooks/paper_to_experiment.md", "START_HERE.md\nWORKFLOW_KERNEL.md\nbase_code_tag\nmodule_template_selection.md\nmodule_source.md\n")
        self._write("experiments/templates/agent_summary_template.md", "multi_agent_preflight:\nformal_runner_allowed:\nagent_output_refs:\nagent_cleanup:\nai_cross_review:\n")
        self._write(
            "experiments/templates/ai_cross_review_template.md",
            "review_tier\nfast\nreview-1\nstrict-3\n02_codex_temp_agent_pre_review.md\ncompleted_closed\nclose_result_confirms_completion\nvalidation_profile\nclaude_rounds_required\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
        )
        self._write("experiments/templates/quality_check_template.md", "review_tier\nvalidate-ai-cross-review\nunresolved_blocking_issues: 0\n")
        self._write("experiments/templates/run_receipt_template.yaml", "schema_version: gtpj.run_receipt.v0\nmulti_agent_preflight:\nagent_output_refs:\n")
        self._write("experiments/templates/modules/README.md", "standard_gzsl_module_framework_template.py\nstandard_gzsl_training_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nstrict_template_entry\nU, S, H, ZS\n")

        code, stdout, stderr = self._run_main("validate-workflow-consistency")

        self.assertEqual("", stdout)
        self.assertEqual(1, code)
        self.assertIn("contains stale AI review phrase", stderr)
        self.assertIn("重复 3 轮", stderr)

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
