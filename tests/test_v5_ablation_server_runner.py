"""V5-ABLATION-001 服务器双卡执行器的静态行为测试。"""

from pathlib import Path
import hashlib
import json
import signal
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from tools import run_v5_ablation_001_server_controller as controller
from tools.run_v5_ablation_001_training import training_spec


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _run_ids():
    return {
        "RUN-001": "RUN-20260807-V5ABL001-FULL-S5",
        "RUN-002": "RUN-20260807-V5ABL001-FULL-S17",
        "RUN-003": "RUN-20260807-V5ABL001-FULL-S29",
        "RUN-004": "RUN-20260807-V5ABL001-GLOBAL-S5",
        "RUN-005": "RUN-20260807-V5ABL001-GLOBAL-S17",
        "RUN-006": "RUN-20260807-V5ABL001-GLOBAL-S29",
    }


def _launch_manifest_payload(commit, hashes=None):
    hashes = hashes or {}
    return {
        "schema_version": "gtpj.v5_ablation_001.launch.v2",
        "experiment_id": "V5-ABLATION-001",
        "workflow_mode": "server_frozen_runner",
        "execution_id": f"V5-ABLATION-001-{commit[:12]}",
        "pre_run_freeze_commit": commit,
        "experiment_branch": controller.EXPERIMENT_BRANCH,
        "template_commit": controller.TEMPLATE_COMMIT,
        "task_start_ref": (
            "experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "TASK_START.yaml"
        ),
        "task_start_sha256": hashes.get("task_start", "1" * 64),
        "agent_runtime_ref": (
            "experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "agent_runtime.yaml"
        ),
        "agent_runtime_sha256": hashes.get("agent_runtime", "2" * 64),
        "review_pack_ref": "docs/agent_reviews/2026-08-07-v5-local-ablation",
        "review_decision_ref": (
            "docs/agent_reviews/2026-08-07-v5-local-ablation/"
            "10_final_decision.md"
        ),
        "review_decision_sha256": hashes.get("review_decision", "3" * 64),
        "parameter_matrix_ref": (
            "experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "PARAMETER_MATRIX.csv"
        ),
        "parameter_matrix_sha256": hashes.get("parameter_matrix", "4" * 64),
        "experiment_binding_ref": (
            "experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "EXPERIMENT.yaml"
        ),
        "experiment_binding_sha256": hashes.get("experiment_binding", "5" * 64),
        "run_ids": _run_ids(),
    }


def _create_evidence_bundle(root, *, tamper_validator=False):
    repo = root / "source"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", controller.EXPERIMENT_BRANCH],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    exp = repo / "experiments/v5/ablation/ABLATION-001_local_branch_effect"
    exp.mkdir(parents=True)
    review = repo / "docs/agent_reviews/2026-08-07-v5-local-ablation"
    review.mkdir(parents=True)
    workflow = repo / "workflow"
    workflow.mkdir()

    task_start = exp / "TASK_START.yaml"
    task_start.write_text(
        json.dumps(
            {
                "formal_runner_allowed": True,
                "formal_evidence_allowed": True,
                "hard_gates": {
                    "code_review": "strict-3 pass",
                    "agent_runtime": "pass",
                    "artifact_boundary": "pass",
                    "pre_run_freeze_commit": "pass",
                },
            }
        ),
        encoding="utf-8",
    )
    agent_runtime = exp / "agent_runtime.yaml"
    agent_runtime.write_text("formal_runner_allowed: true\n", encoding="utf-8")
    review_decision = review / "10_final_decision.md"
    review_decision.write_text("ai_cross_review_status: pass\n", encoding="utf-8")
    matrix = exp / "PARAMETER_MATRIX.csv"
    matrix.write_text(
        "job_id,run_id,status\n"
        + "".join(
            f"{job_id},{run_id},frozen\n" for job_id, run_id in _run_ids().items()
        ),
        encoding="utf-8",
    )
    experiment_binding = exp / "EXPERIMENT.yaml"
    experiment_binding.write_text("experiment_id: V5-ABLATION-001\n", encoding="utf-8")
    (workflow / "gtpj_workflow.py").write_text(
        """from pathlib import Path
import sys

if len(sys.argv) > 1 and sys.argv[1] == "validate-experiment-base":
    path = Path(sys.argv[sys.argv.index("--path") + 1])
    if not path.is_dir() or not (path / "EXPERIMENT.yaml").is_file():
        raise SystemExit(9)
raise SystemExit(0)
""",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "."], cwd=repo, check=True, capture_output=True, text=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=GTPJ Test",
            "-c",
            "user.email=gtpj-test@example.invalid",
            "commit",
            "-m",
            "test evidence",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    template_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tamper_validator:
        (workflow / "gtpj_workflow.py").write_text(
            "raise SystemExit(0)  # forged self-validator\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "workflow/gtpj_workflow.py"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=GTPJ Test",
                "-c",
                "user.email=gtpj-test@example.invalid",
                "commit",
                "-m",
                "forge validator",
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    bundle = root / "evidence.bundle"
    subprocess.run(
        ["git", "bundle", "create", str(bundle), "--all"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    hashes = {
        "task_start": _sha256(task_start),
        "agent_runtime": _sha256(agent_runtime),
        "review_decision": _sha256(review_decision),
        "parameter_matrix": _sha256(matrix),
        "experiment_binding": _sha256(experiment_binding),
    }
    payload = _launch_manifest_payload(commit, hashes)
    payload["template_commit"] = template_commit
    return bundle, commit, payload, template_commit


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
            payload = _launch_manifest_payload("a" * 40)
            payload["experiment_branch"] = "exp/forged"
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "experiment_branch"):
                controller.validate_launch_manifest(path, "a" * 40)

    def test_launch_manifest_requires_the_exact_frozen_commit_and_all_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch_manifest.json"
            payload = _launch_manifest_payload("a" * 40)
            path.write_text(json.dumps(payload), encoding="utf-8")

            manifest, digest = controller.validate_launch_manifest(path, "a" * 40)
            self.assertEqual(payload, manifest)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

            payload["pre_run_freeze_commit"] = "b" * 40
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pre_run_freeze_commit"):
                controller.validate_launch_manifest(path, "a" * 40)

    def test_frozen_evidence_is_verified_from_bundle_not_manifest_booleans(self):
        verify = getattr(controller, "verify_frozen_launch_evidence", None)
        self.assertIsNotNone(verify)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, commit, payload, template_commit = _create_evidence_bundle(root)
            with patch.object(controller, "TEMPLATE_COMMIT", template_commit):
                result = verify(bundle, Path(sys.executable), payload, commit)
                self.assertEqual(_run_ids(), result["run_ids"])

                payload["parameter_matrix_sha256"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "parameter_matrix_sha256"):
                    verify(bundle, Path(sys.executable), payload, commit)

    def test_frozen_evidence_refuses_a_bundle_that_replaces_its_own_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, commit, payload, template_commit = _create_evidence_bundle(
                root, tamper_validator=True
            )
            with patch.object(controller, "TEMPLATE_COMMIT", template_commit):
                with self.assertRaisesRegex(ValueError, "workflow/gtpj_workflow.py"):
                    controller.verify_frozen_launch_evidence(
                        bundle, Path(sys.executable), payload, commit
                    )

    def test_server_controller_rejects_non_linux_process_semantics(self):
        check = getattr(controller, "ensure_supported_platform", None)
        self.assertIsNotNone(check)
        with self.assertRaisesRegex(RuntimeError, "Linux"):
            check(platform_name="nt", killpg_available=False, sigkill_available=False)
        with self.assertRaisesRegex(RuntimeError, "Linux"):
            check(platform_name="darwin", killpg_available=True, sigkill_available=True)

    def test_execution_identity_and_run_ids_are_claimed_only_once(self):
        claim = getattr(controller, "claim_execution_identity", None)
        self.assertIsNotNone(claim)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim(
                root,
                execution_id="V5-ABLATION-001-aaaaaaaaaaaa",
                commit="a" * 40,
                run_ids=_run_ids(),
                runtime_root=root.parent / "runtime-a",
                warehouse_root=root.parent / "warehouse-a",
            )
            with self.assertRaisesRegex(FileExistsError, "execution_id"):
                claim(
                    root,
                    execution_id="V5-ABLATION-001-aaaaaaaaaaaa",
                    commit="a" * 40,
                    run_ids={key: value + "-new" for key, value in _run_ids().items()},
                    runtime_root=root.parent / "runtime-b",
                    warehouse_root=root.parent / "warehouse-b",
                )
            with self.assertRaisesRegex(FileExistsError, "run_id"):
                claim(
                    root,
                    execution_id="V5-ABLATION-001-bbbbbbbbbbbb",
                    commit="b" * 40,
                    run_ids=_run_ids(),
                    runtime_root=root.parent / "runtime-c",
                    warehouse_root=root.parent / "warehouse-c",
                )

    def test_runtime_and_warehouse_roots_must_be_new_and_commit_named(self):
        check = getattr(controller, "validate_fresh_execution_roots", None)
        self.assertIsNotNone(check)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = "V5-ABLATION-001-aaaaaaaaaaaa"
            runtime = root / "runtime" / name
            warehouse = root / "warehouse" / name
            check(
                runtime,
                warehouse,
                "a" * 40,
                runtime_base=root / "runtime",
                warehouse_base=root / "warehouse",
            )
            runtime.mkdir(parents=True)
            with self.assertRaisesRegex(FileExistsError, "runtime"):
                check(
                    runtime,
                    warehouse,
                    "a" * 40,
                    runtime_base=root / "runtime",
                    warehouse_base=root / "warehouse",
                )

    def test_runtime_identity_cannot_be_reclaimed_by_changing_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = "V5-ABLATION-001-aaaaaaaaaaaa"
            with self.assertRaisesRegex(ValueError, "warehouse-root"):
                controller.validate_fresh_execution_roots(
                    root / "runtime" / name,
                    root / "different-warehouse" / name,
                    "a" * 40,
                    runtime_base=root / "runtime",
                    warehouse_base=root / "warehouse",
                )

    def test_signal_handler_only_requests_stop_through_event(self):
        factory = getattr(controller, "make_stop_signal_handler", None)
        self.assertIsNotNone(factory)
        stop_requested = threading.Event()
        handler = factory(stop_requested)
        handler(signal.SIGTERM, None)
        self.assertTrue(stop_requested.is_set())

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

    def test_failure_registration_and_process_launch_are_serialized(self):
        gate = controller.RunGate()
        launch = getattr(gate, "launch_if_allowed", None)
        self.assertIsNotNone(launch)
        entered = threading.Event()
        release = threading.Event()
        failure_recorded = threading.Event()
        result = []

        def factory():
            entered.set()
            release.wait(2)
            return "started"

        launch_thread = threading.Thread(target=lambda: result.append(launch(factory)))
        launch_thread.start()
        self.assertTrue(entered.wait(1))

        def mark_failure():
            gate.mark_failure()
            failure_recorded.set()

        failure_thread = threading.Thread(target=mark_failure)
        failure_thread.start()
        self.assertFalse(failure_recorded.wait(0.05))
        release.set()
        launch_thread.join(1)
        failure_thread.join(1)
        self.assertEqual(["started"], result)
        self.assertTrue(failure_recorded.is_set())

        called = []
        self.assertIsNone(launch(lambda: called.append(True)))
        self.assertEqual([], called)

    def test_cleanup_falls_back_to_helper_group_after_training_stop_error(self):
        cleanup = getattr(controller, "cleanup_process_tree", None)
        self.assertIsNotNone(cleanup)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            process = Mock(pid=1234)
            process.poll.side_effect = [None, None, 1]
            process.wait.return_value = 1
            with patch.object(controller, "training_pid_from_log", return_value=4321), patch.object(
                controller,
                "terminate_training_process",
                side_effect=RuntimeError("training did not exit"),
            ), patch.object(
                controller,
                "_terminate_helper_group",
                return_value="helper_group_killed",
            ) as terminate_group:
                outcome = cleanup(
                    helper_process=process,
                    training_log=root / "training.log",
                    receipt=root / "run_start_receipt.json",
                )
            self.assertTrue(outcome["cleanup_complete"])
            self.assertEqual("incomplete_missing_finish_receipt", outcome["receipt_state"])
            self.assertIn("training did not exit", outcome["errors"][0])
            terminate_group.assert_called_once_with(process)

    def test_missing_training_pid_is_explicitly_incomplete_even_with_receipt(self):
        cleanup = getattr(controller, "cleanup_process_tree", None)
        self.assertIsNotNone(cleanup)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "run_start_receipt.json"
            receipt.write_text("{}\n", encoding="utf-8")
            controller.finish_receipt_path(receipt).write_text(
                json.dumps({"schema_version": "gtpj-run-finish-receipt/v1"}),
                encoding="utf-8",
            )
            process = Mock(pid=1234)
            process.poll.side_effect = [None, None, 1]
            process.wait.return_value = 1
            with patch.object(controller, "training_pid_from_log", return_value=None), patch.object(
                controller,
                "_terminate_helper_group",
                return_value="helper_group_killed",
            ):
                outcome = cleanup(
                    helper_process=process,
                    training_log=root / "training.log",
                    receipt=receipt,
                )
            self.assertEqual(
                "incomplete_before_training_pid", outcome["process_evidence_state"]
            )

    def test_finish_receipt_must_match_job_run_and_return_code(self):
        validate = getattr(controller, "validate_finish_receipt", None)
        self.assertIsNotNone(validate)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt = root / "run_start_receipt.json"
            receipt.write_text("{}\n", encoding="utf-8")
            training_log = root / "training.log"
            training_log.write_text("sealed training output\n", encoding="utf-8")
            command = "python tools/run_v5_ablation_001_training.py --group FULL"
            finish = controller.finish_receipt_path(receipt)
            payload = {
                "schema_version": "gtpj-run-finish-receipt/v1",
                "generated_by": "workflow/gtpj_workflow.py prepare-run-start-receipt",
                "job_id": "RUN-001",
                "run_id": _run_ids()["RUN-001"],
                "run_start_receipt_sha256": _sha256(receipt),
                "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
                "pid": 1234,
                "started_at": "2026-08-07T00:00:00+00:00",
                "finished_at": "2026-08-07T00:01:00+00:00",
                "returncode": 0,
                "log_sha256": _sha256(training_log),
            }
            finish.write_text(json.dumps(payload), encoding="utf-8")
            self.assertEqual(
                payload,
                validate(
                    receipt,
                    training_log,
                    command,
                    "RUN-001",
                    _run_ids()["RUN-001"],
                    0,
                ),
            )
            with self.assertRaisesRegex(RuntimeError, "run_id"):
                validate(
                    receipt,
                    training_log,
                    command,
                    "RUN-001",
                    "different-run",
                    0,
                )
            payload["log_sha256"] = "2" * 64
            finish.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "log_sha256"):
                validate(
                    receipt,
                    training_log,
                    command,
                    "RUN-001",
                    _run_ids()["RUN-001"],
                    0,
                )

    def test_status_write_failure_after_launch_still_cleans_process_tree(self):
        class FailOnRunningStatus:
            def update_job(self, _job_id, **values):
                if values.get("status") == "running":
                    raise RuntimeError("status write failed")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "ledger"
            experiment = ledger / controller.EXPERIMENT_DIR
            experiment.mkdir(parents=True)
            (experiment / "PARAMETER_MATRIX.csv").write_text(
                "job_id,run_id\nRUN-001," + _run_ids()["RUN-001"] + "\n",
                encoding="utf-8",
            )
            (experiment / "configs").mkdir()
            warehouse = root / "warehouse"
            warehouse.mkdir()
            process = Mock(pid=1234)
            process.poll.return_value = None
            cleanup_result = {
                "training_pid": 4321,
                "training_termination": "terminated",
                "helper_termination": None,
                "cleanup_complete": True,
                "errors": [],
                "finish_receipt": str(root / "finish.json"),
                "process_evidence_state": "process_tree_stopped",
                "receipt_state": "incomplete_missing_finish_receipt",
            }
            gate = controller.RunGate()
            with patch.object(controller.subprocess, "Popen", return_value=process), patch.object(
                controller,
                "cleanup_process_tree",
                return_value=cleanup_result,
            ) as cleanup:
                with self.assertRaisesRegex(RuntimeError, "status write failed"):
                    controller.run_job(
                        args=SimpleNamespace(
                            python=Path(sys.executable),
                            commit="a" * 40,
                        ),
                        group="FULL",
                        job_id="RUN-001",
                        code_root=root / "code",
                        ledger_root=ledger,
                        warehouse_root=warehouse,
                        stop_file=root / "STOP",
                        stop_requested=threading.Event(),
                        run_gate=gate,
                        status=FailOnRunningStatus(),
                    )
            cleanup.assert_called_once()
            self.assertFalse(gate.claim_start())

    def test_starting_status_write_failure_blocks_other_queue_immediately(self):
        class FailOnStartingStatus:
            def update_job(self, _job_id, **values):
                if values.get("status") == "starting":
                    raise RuntimeError("starting status write failed")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "ledger"
            experiment = ledger / controller.EXPERIMENT_DIR
            experiment.mkdir(parents=True)
            (experiment / "PARAMETER_MATRIX.csv").write_text(
                "job_id,run_id\nRUN-001," + _run_ids()["RUN-001"] + "\n",
                encoding="utf-8",
            )
            (experiment / "configs").mkdir()
            warehouse = root / "warehouse"
            warehouse.mkdir()
            gate = controller.RunGate()
            with self.assertRaisesRegex(RuntimeError, "starting status write failed"):
                controller.run_job(
                    args=SimpleNamespace(
                        python=Path(sys.executable),
                        commit="a" * 40,
                    ),
                    group="FULL",
                    job_id="RUN-001",
                    code_root=root / "code",
                    ledger_root=ledger,
                    warehouse_root=warehouse,
                    stop_file=root / "STOP",
                    stop_requested=threading.Event(),
                    run_gate=gate,
                    status=FailOnStartingStatus(),
                )
            self.assertFalse(gate.claim_start())

    def test_running_status_binding_is_atomic_with_process_launch(self):
        running_status_started = threading.Event()
        release_running_status = threading.Event()

        class BlockingRunningStatus:
            def update_job(self, _job_id, **values):
                if values.get("status") == "running":
                    running_status_started.set()
                    release_running_status.wait(2)
                    raise RuntimeError("running status write failed")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "ledger"
            experiment = ledger / controller.EXPERIMENT_DIR
            experiment.mkdir(parents=True)
            (experiment / "PARAMETER_MATRIX.csv").write_text(
                "job_id,run_id\nRUN-001," + _run_ids()["RUN-001"] + "\n",
                encoding="utf-8",
            )
            (experiment / "configs").mkdir()
            warehouse = root / "warehouse"
            warehouse.mkdir()
            process = Mock(pid=1234)
            process.poll.return_value = None
            cleanup_result = {
                "training_pid": None,
                "training_termination": None,
                "helper_termination": "helper_group_terminated",
                "cleanup_complete": True,
                "errors": [],
                "finish_receipt": str(root / "finish.json"),
                "process_evidence_state": "incomplete_before_training_pid",
                "receipt_state": "incomplete_missing_finish_receipt",
            }
            gate = controller.RunGate()
            errors = []
            later_results = []

            def execute_job():
                try:
                    controller.run_job(
                        args=SimpleNamespace(
                            python=Path(sys.executable),
                            commit="a" * 40,
                        ),
                        group="FULL",
                        job_id="RUN-001",
                        code_root=root / "code",
                        ledger_root=ledger,
                        warehouse_root=warehouse,
                        stop_file=root / "STOP",
                        stop_requested=threading.Event(),
                        run_gate=gate,
                        status=BlockingRunningStatus(),
                    )
                except Exception as exc:
                    errors.append(exc)

            with patch.object(controller.subprocess, "Popen", return_value=process), patch.object(
                controller,
                "cleanup_process_tree",
                return_value=cleanup_result,
            ) as cleanup:
                worker = threading.Thread(target=execute_job)
                worker.start()
                self.assertTrue(running_status_started.wait(1))
                later = threading.Thread(
                    target=lambda: later_results.append(
                        gate.launch_if_allowed(lambda: "started")
                    )
                )
                later.start()
                later.join(0.05)
                self.assertTrue(later.is_alive())
                release_running_status.set()
                worker.join(1)
                later.join(1)
            self.assertEqual([None], later_results)
            self.assertEqual(1, len(errors))
            cleanup.assert_called_once()

    def test_finish_receipt_failure_blocks_other_queue_before_status_cleanup(self):
        cleanup_status_started = threading.Event()
        release_cleanup_status = threading.Event()

        class BlockingCleanupStatus:
            def update_job(self, _job_id, **values):
                if "finish_receipt_state" in values:
                    cleanup_status_started.set()
                    release_cleanup_status.wait(2)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "ledger"
            experiment = ledger / controller.EXPERIMENT_DIR
            experiment.mkdir(parents=True)
            (experiment / "PARAMETER_MATRIX.csv").write_text(
                "job_id,run_id\nRUN-001," + _run_ids()["RUN-001"] + "\n",
                encoding="utf-8",
            )
            (experiment / "configs").mkdir()
            warehouse = root / "warehouse"
            warehouse.mkdir()
            process = Mock(pid=1234)
            process.poll.return_value = 0
            process.wait.return_value = 0
            cleanup_result = {
                "training_pid": 4321,
                "training_termination": None,
                "helper_termination": None,
                "cleanup_complete": True,
                "errors": [],
                "finish_receipt": str(root / "finish.json"),
                "process_evidence_state": "helper_already_exited",
                "receipt_state": "sealed",
            }
            gate = controller.RunGate()
            errors = []

            def execute_job():
                try:
                    controller.run_job(
                        args=SimpleNamespace(
                            python=Path(sys.executable),
                            commit="a" * 40,
                        ),
                        group="FULL",
                        job_id="RUN-001",
                        code_root=root / "code",
                        ledger_root=ledger,
                        warehouse_root=warehouse,
                        stop_file=root / "STOP",
                        stop_requested=threading.Event(),
                        run_gate=gate,
                        status=BlockingCleanupStatus(),
                    )
                except Exception as exc:
                    errors.append(exc)

            with patch.object(controller.subprocess, "Popen", return_value=process), patch.object(
                controller,
                "cleanup_process_tree",
                return_value=cleanup_result,
            ), patch.object(
                controller,
                "validate_finish_receipt",
                side_effect=RuntimeError("finish receipt invalid"),
            ):
                worker = threading.Thread(target=execute_job)
                worker.start()
                self.assertTrue(cleanup_status_started.wait(1))
                later_launches = []
                self.assertIsNone(
                    gate.launch_if_allowed(lambda: later_launches.append("started"))
                )
                release_cleanup_status.set()
                worker.join(1)
            self.assertEqual([], later_launches)
            self.assertEqual(1, len(errors))

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
