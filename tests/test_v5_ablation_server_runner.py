"""V5-ABLATION-001 服务器双卡执行器的静态行为测试。"""

from pathlib import Path
import json
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import run_v5_ablation_001_server_controller as controller
from tools.run_v5_ablation_001_training import training_spec


class V5AblationServerRunnerTest(unittest.TestCase):
    def test_groups_are_fixed_to_two_distinct_gpus_and_entries(self):
        self.assertEqual(
            {"gpu": "0", "entry": "train_GTPJ_CUB.py"},
            training_spec("FULL"),
        )
        self.assertEqual(
            {"gpu": "1", "entry": "train_V5_ABLATION_001_CUB.py"},
            training_spec("GLOBAL_ONLY"),
        )

    def test_each_group_has_the_expected_three_job_queue(self):
        self.assertEqual(
            ("RUN-001", "RUN-002", "RUN-003"), controller.GROUP_JOBS["FULL"]
        )
        self.assertEqual(
            ("RUN-004", "RUN-005", "RUN-006"),
            controller.GROUP_JOBS["GLOBAL_ONLY"],
        )

    def test_receipt_command_names_exactly_one_python_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = controller.build_training_command(
                Path("/data/lby/.conda/envs/dvsr_gpu/bin/python"),
                "GLOBAL_ONLY",
                root / "RUN-004.yaml",
                root / "code_GLOBAL_ONLY",
                "a" * 40,
            )
        self.assertEqual(1, sum(token.endswith(".py") for token in command.split()))
        self.assertIn("--group GLOBAL_ONLY", command)
        self.assertIn("--config", command)
        self.assertNotIn("&&", command)
        self.assertNotIn(";", command)

    def test_launch_manifest_blocks_formal_start_when_any_gate_is_not_passed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch_manifest.json"
            payload = {
                "schema_version": "gtpj.v5_ablation_001.launch.v1",
                "experiment_id": "V5-ABLATION-001",
                "workflow_mode": "server_frozen_runner",
                "pre_run_freeze_commit": "a" * 40,
                "formal_runner_allowed": False,
                "codex_named_thread_pre_review": "pass",
                "codex_named_thread_archived": True,
                "ai_cross_review_validation": "pass",
                "machine_validation": "pass",
                "matrix_validation": "pass",
                "agent_runtime_validation": "pass",
                "server_preflight": "pass",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "formal_runner_allowed"):
                controller.validate_launch_manifest(path, "a" * 40)

    def test_launch_manifest_requires_the_exact_frozen_commit_and_all_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch_manifest.json"
            payload = {
                "schema_version": "gtpj.v5_ablation_001.launch.v1",
                "experiment_id": "V5-ABLATION-001",
                "workflow_mode": "server_frozen_runner",
                "pre_run_freeze_commit": "a" * 40,
                "formal_runner_allowed": True,
                "codex_named_thread_pre_review": "pass",
                "codex_named_thread_archived": True,
                "ai_cross_review_validation": "pass",
                "machine_validation": "pass",
                "matrix_validation": "pass",
                "agent_runtime_validation": "pass",
                "server_preflight": "pass",
            }
            path.write_text(json.dumps(payload), encoding="utf-8")

            manifest, digest = controller.validate_launch_manifest(path, "a" * 40)
            self.assertEqual(payload, manifest)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

            with self.assertRaisesRegex(ValueError, "pre_run_freeze_commit"):
                controller.validate_launch_manifest(path, "b" * 40)

    def test_training_pid_is_read_from_the_anchored_training_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "training.log"
            path.write_text(
                "GTPJ_RUN_START_RECEIPT_SHA256=" + "a" * 64 + "\n"
                "GTPJ_TRAINING_PROCESS_STARTED command_sha256="
                + "b" * 64
                + " pid=4321 started_at=2026-08-07T00:00:00+00:00\n",
                encoding="utf-8",
            )
            self.assertEqual(4321, controller.training_pid_from_log(path))

    @patch.object(controller.os, "kill")
    def test_stop_escalates_from_term_to_kill_when_training_does_not_exit(
        self, kill
    ):
        helper = Mock()
        helper.poll.side_effect = [None, None, None, 1]
        outcome = controller.terminate_training_process(
            training_pid=4321,
            helper_process=helper,
            term_timeout_seconds=0,
            kill_timeout_seconds=1,
            poll_interval_seconds=0,
        )
        self.assertEqual("killed", outcome)
        self.assertEqual(
            [
                unittest.mock.call(4321, signal.SIGTERM),
                unittest.mock.call(4321, controller.KILL_SIGNAL),
            ],
            kill.call_args_list,
        )

    def test_failure_gate_never_allows_a_later_job_to_start(self):
        gate = controller.RunGate()
        self.assertTrue(gate.claim_start())
        gate.mark_failure()
        self.assertFalse(gate.claim_start())

    def test_recovery_handoff_forbids_reusing_a_partial_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recovery_handoff.json"
            status = {
                "experiment_id": "V5-ABLATION-001",
                "status": "stopped",
                "jobs": {
                    "RUN-001": {"status": "stopped", "ledger": "ledger_RUN-001"},
                    "RUN-002": {"status": "not_started_after_stop_or_failure"},
                },
            }
            controller.write_recovery_handoff(path, status)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(payload["automatic_resume_allowed"])
            self.assertEqual(["RUN-001"], payload["partial_jobs"])
            self.assertIn("new frozen RUN row", payload["required_next_action"])


if __name__ == "__main__":
    unittest.main()
