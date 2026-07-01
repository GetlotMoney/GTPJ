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
            "next_action": "trial",
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

    def test_required_files_include_owner_facing_start_docs(self) -> None:
        required = self.module.required_repository_files()

        self.assertIn("docs/workflow/QUICK_START.md", required)
        self.assertIn("docs/workflow/TASK_START_MINI.md", required)

    def test_scan_ignores_runtime_state(self) -> None:
        legacy_marker = "TUNE" + "-024"
        self._write(".gtpj_runtime/batches/old/summary.csv", f"legacy {legacy_marker} runtime evidence\n")
        self._write("docs/visible.md", "visible governance text\n")

        scanned = {path.relative_to(self.repo).as_posix() for path in self.module.list_files_for_scan()}

        self.assertIn("docs/visible.md", scanned)
        self.assertNotIn(".gtpj_runtime/batches/old/summary.csv", scanned)

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
        preserved = self.module.preserve_trial_best_for_non_best_sync(
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
        self.assertIn("总创意清单", global_index)
        self.assertIn("IDEA-0001_token_router/IDEA.md", global_index)
        self.assertIn("v1 创意选择清单", v1_view)
        self.assertIn("IDEA-0001_token_router/IDEA.md", v1_view)

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
        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("已创建 experiments/module_trials/IDEA-0001_token_router/TRIAL-001_token_router", stdout)
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

    def test_dynamic_routing_runner_records_failures_and_warehouse_artifacts(self) -> None:
        script = self.module._dynamic_runner_script()

        self.assertIn("except Exception as exc", script)
        self.assertIn("status=\"failed\"", script)
        self.assertIn("copy_artifacts_to_warehouse", script)
        self.assertIn("warehouse_attempt_dir", script)
        self.assertIn("artifact_manifest.json", script)
        self.assertIn("link_runtime_resources", script)
        self.assertIn('plan.get("runtime_resource_links", ["data"])', script)
        self.assertIn("prune_model_artifacts", script)
        self.assertIn("keep top 3 best_model_*.pth by H", script)
        self.assertIn("def load_json(path, retries=20, delay=0.05):", script)
        self.assertIn("os.replace(tmp_path, path)", script)

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
        self._write(
            "experiments/v1/tune/TUNE-999_ok/manifest.yaml",
            "schema_version: gtpj-manifest/v1\n"
            "artifacts:\n"
            "  train_log:\n"
            "    artifact_id: log:TUNE-999_ok:attempt-001\n"
            "    uri: warehouse://gtpj/runs/v1/tune/TUNE-999_ok/attempt-001/logs/train.log\n",
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
