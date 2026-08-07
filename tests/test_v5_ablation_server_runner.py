"""V5-ABLATION-001 服务器双卡执行器的静态行为测试。"""

from pathlib import Path
import hashlib
import json
import os
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
        "schema_version": "gtpj.v5_ablation_001.launch.v3",
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
        "data_manifest_ref": (
            "experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "DATA_MANIFEST.json"
        ),
        "data_manifest_sha256": hashes.get("data_manifest", "7" * 64),
        "python_ref": controller.SERVER_PYTHON.as_posix(),
        "python_sha256": hashes.get("python", "6" * 64),
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
    data_source = root / "formal-data"
    data_source.mkdir()
    data_files = {}
    for index, (logical_name, relative_path) in enumerate(
        controller.V5_REQUIRED_DATA_FILES.items(), start=1
    ):
        path = data_source / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"fixture-{index}-{logical_name}".encode("utf-8"))
        data_files[logical_name] = {
            "relative_path": relative_path,
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
    data_manifest = exp / "DATA_MANIFEST.json"
    data_manifest.write_text(
        json.dumps(
            {
                "schema_version": controller.DATA_MANIFEST_SCHEMA,
                **controller.DATA_CONTRACT_VALUES,
                "data_source_ref": data_source.absolute().as_posix(),
                "files": data_files,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (workflow / "gtpj_workflow.py").write_text(
        """from pathlib import Path
import sys

if len(sys.argv) > 1 and sys.argv[1] == "validate-experiment-base":
    path = Path(sys.argv[sys.argv.index("--path") + 1])
    if not path.is_dir() or not (path / "EXPERIMENT.yaml").is_file():
        raise SystemExit(9)
    import subprocess
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if branch != "exp/v5/ablation/ablation-001-local-branch-effect":
        raise SystemExit(10)
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
        "data_manifest": _sha256(data_manifest),
        "python": _sha256(sys.executable),
    }
    payload = _launch_manifest_payload(commit, hashes)
    payload["python_ref"] = Path(sys.executable).absolute().as_posix()
    payload["template_commit"] = template_commit
    return bundle, commit, payload, template_commit, data_source


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

    def test_launch_manifest_pins_the_exact_python_path_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch_manifest.json"
            payload = _launch_manifest_payload("a" * 40)
            payload["python_ref"] = "/tmp/replaceable-python"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "python_ref"):
                controller.validate_launch_manifest(path, "a" * 40)

            payload = _launch_manifest_payload("a" * 40)
            payload["python_sha256"] = "not-a-digest"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "python_sha256"):
                controller.validate_launch_manifest(path, "a" * 40)

    def test_python_runtime_must_match_fixed_path_hash_and_file_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "python"
            runtime.write_bytes(b"trusted-runtime")
            manifest = {
                "python_ref": runtime.as_posix(),
                "python_sha256": _sha256(runtime),
            }
            with patch.object(controller, "SERVER_PYTHON", runtime.absolute()):
                identity = controller.verify_python_runtime(runtime, manifest)
                runtime.write_bytes(b"replaced-runtime")
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    controller.verify_python_runtime(
                        runtime, manifest, expected_identity=identity
                    )

    def test_python_runtime_is_bound_to_an_open_executable_descriptor(self):
        bind = getattr(controller, "bind_python_runtime", None)
        self.assertIsNotNone(bind)
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "python"
            runtime.write_bytes(b"trusted-runtime")
            manifest = {
                "python_ref": runtime.as_posix(),
                "python_sha256": _sha256(runtime),
            }
            with patch.object(controller, "SERVER_PYTHON", runtime.absolute()):
                binding = bind(runtime, manifest)
                try:
                    self.assertRegex(binding["exec_ref"], r"^/proc/[1-9][0-9]*/fd/[1-9][0-9]*$")
                    self.assertEqual(_sha256(runtime), binding["identity"]["sha256"])
                    self.assertEqual(runtime.as_posix(), binding["argv0"])
                finally:
                    os.close(binding["fd"])

    def test_frozen_evidence_is_verified_from_bundle_not_manifest_booleans(self):
        verify = getattr(controller, "verify_frozen_launch_evidence", None)
        self.assertIsNotNone(verify)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, commit, payload, template_commit, data_source = _create_evidence_bundle(root)
            with patch.object(controller, "TEMPLATE_COMMIT", template_commit), patch.object(
                controller, "SERVER_PYTHON", Path(sys.executable).absolute()
            ), patch.object(
                controller, "SERVER_DATA_SOURCE", data_source.absolute()
            ):
                result = verify(
                    bundle, Path(sys.executable), data_source, payload, commit
                )
                self.assertEqual(_run_ids(), result["run_ids"])

                payload["parameter_matrix_sha256"] = "0" * 64
                with self.assertRaisesRegex(ValueError, "parameter_matrix_sha256"):
                    verify(
                        bundle, Path(sys.executable), data_source, payload, commit
                    )

                changed = data_source / next(iter(controller.V5_REQUIRED_DATA_FILES.values()))
                changed.write_bytes(b"changed-data")
                payload["parameter_matrix_sha256"] = _sha256(
                    root
                    / "source/experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv"
                )
                with self.assertRaisesRegex(ValueError, "数据文件"):
                    verify(
                        bundle, Path(sys.executable), data_source, payload, commit
                    )

    def test_frozen_evidence_refuses_a_bundle_that_replaces_its_own_validator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle, commit, payload, template_commit, data_source = _create_evidence_bundle(
                root, tamper_validator=True
            )
            with patch.object(controller, "TEMPLATE_COMMIT", template_commit), patch.object(
                controller, "SERVER_PYTHON", Path(sys.executable).absolute()
            ), patch.object(
                controller, "SERVER_DATA_SOURCE", data_source.absolute()
            ):
                with self.assertRaisesRegex(ValueError, "workflow/gtpj_workflow.py"):
                    controller.verify_frozen_launch_evidence(
                        bundle, Path(sys.executable), data_source, payload, commit
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

    def test_claim_is_not_published_when_atomic_link_fails(self):
        publish = getattr(controller, "_atomic_create_json", None)
        self.assertIsNotNone(publish)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "claim.json"
            with patch.object(controller.os, "link", side_effect=OSError("link failed")):
                with self.assertRaisesRegex(OSError, "link failed"):
                    publish(target, {"execution_id": "test"})
            self.assertFalse(target.exists())
            self.assertEqual([], list(root.glob(".*.tmp")))

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

    def test_pidfd_signal_targets_the_open_process_handle(self):
        send = getattr(controller, "_signal_pidfd", None)
        self.assertIsNotNone(send)
        with patch.object(controller.signal, "pidfd_send_signal", create=True) as pidfd_send, patch.object(
            controller.os, "kill"
        ) as raw_kill, patch.object(controller.os, "killpg", create=True) as raw_killpg:
            send(17, signal.SIGTERM)
        pidfd_send.assert_called_once_with(17, signal.SIGTERM, None, 0)
        raw_kill.assert_not_called()
        raw_killpg.assert_not_called()

    def test_uncaptured_helper_is_killed_before_it_can_be_reaped(self):
        terminate = getattr(controller, "_terminate_uncaptured_helper", None)
        self.assertIsNotNone(terminate)
        helper = Mock(pid=1234)
        helper.wait.return_value = -int(controller.KILL_SIGNAL)
        with patch.object(controller.os, "killpg", create=True) as killpg:
            outcome = terminate(helper)
        killpg.assert_called_once_with(1234, controller.KILL_SIGNAL)
        helper.wait.assert_called_once()
        self.assertTrue(outcome["cleanup_complete"])

    def test_stop_escalates_from_term_to_kill_when_training_does_not_exit(self):
        helper = Mock()
        helper.poll.return_value = 1
        helper_identity = {
            "pid": 1234,
            "pgid": 1234,
            "sid": 1234,
            "start_time_ticks": 99,
        }
        training_identity = {
            "pid": 4321,
            "pgid": 1234,
            "sid": 1234,
            "start_time_ticks": 101,
        }
        with patch.object(
            controller, "_signal_bound_identity", return_value=True
        ) as signal_training, patch.object(
            controller,
            "_wait_for_process_group_empty",
            side_effect=[False, True],
        ), patch.object(controller, "_signal_bound_helper_group") as signal_group:
            outcome = controller.terminate_training_process(
                training_pid=4321,
                training_identity=training_identity,
                helper_process=helper,
                helper_identity=helper_identity,
                term_timeout_seconds=0,
                kill_timeout_seconds=1,
                poll_interval_seconds=0,
            )
        self.assertEqual("group_killed", outcome)
        signal_training.assert_called_once_with(training_identity, signal.SIGTERM)
        signal_group.assert_called_once_with(helper_identity, controller.KILL_SIGNAL)

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
            process.poll.return_value = 1
            process.wait.return_value = 1
            helper_identity = {
                "pid": 1234,
                "pgid": 1234,
                "sid": 1234,
                "start_time_ticks": 99,
            }
            training_identity = {
                "pid": 4321,
                "pgid": 1234,
                "sid": 1234,
                "start_time_ticks": 101,
            }
            with patch.object(controller, "training_pid_from_log", return_value=4321), patch.object(
                controller, "capture_training_identity", return_value=training_identity
            ), patch.object(
                controller,
                "terminate_training_process",
                side_effect=RuntimeError("training did not exit"),
            ), patch.object(
                controller,
                "_terminate_helper_group",
                return_value="helper_group_killed",
            ) as terminate_group, patch.object(
                controller,
                "process_group_members",
                side_effect=[[training_identity], []],
            ):
                outcome = cleanup(
                    helper_process=process,
                    helper_identity=helper_identity,
                    training_log=root / "training.log",
                    receipt=root / "run_start_receipt.json",
                )
            self.assertTrue(outcome["cleanup_complete"])
            self.assertEqual("incomplete_missing_finish_receipt", outcome["receipt_state"])
            self.assertIn("training did not exit", outcome["errors"][0])
            terminate_group.assert_called_once_with(process, helper_identity)

    def test_cleanup_stops_bound_group_even_after_helper_has_exited(self):
        cleanup = getattr(controller, "cleanup_process_tree", None)
        self.assertIsNotNone(cleanup)
        helper_identity = {
            "pid": 1234,
            "pgid": 1234,
            "sid": 1234,
            "start_time_ticks": 99,
        }
        training_identity = {
            "pid": 4321,
            "pgid": 1234,
            "sid": 1234,
            "start_time_ticks": 101,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            process = Mock(pid=1234)
            process.poll.return_value = 1
            process.wait.return_value = 1
            with patch.object(
                controller, "training_pid_from_log", return_value=4321
            ), patch.object(
                controller,
                "capture_training_identity",
                return_value=training_identity,
            ), patch.object(
                controller,
                "terminate_training_process",
                return_value="group_killed",
            ) as terminate_training, patch.object(
                controller, "process_group_members", return_value=[]
            ):
                outcome = cleanup(
                    helper_process=process,
                    helper_identity=helper_identity,
                    training_log=root / "training.log",
                    receipt=root / "run_start_receipt.json",
                )
            self.assertTrue(outcome["cleanup_complete"])
            terminate_training.assert_called_once()

    def test_cleanup_refuses_training_pid_outside_bound_helper_session(self):
        helper_identity = {
            "pid": 1234,
            "pgid": 1234,
            "sid": 1234,
            "start_time_ticks": 99,
        }
        foreign_identity = {
            "pid": 4321,
            "pgid": 7777,
            "sid": 7777,
            "start_time_ticks": 101,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            process = Mock(pid=1234)
            process.poll.return_value = 1
            process.wait.return_value = 1
            with patch.object(
                controller, "training_pid_from_log", return_value=4321
            ), patch.object(
                controller,
                "capture_training_identity",
                side_effect=RuntimeError("日志中的训练 PID 不属于本次 helper 进程组与会话。"),
            ), patch.object(controller.os, "kill") as kill, patch.object(
                controller, "process_group_members", return_value=[]
            ):
                outcome = controller.cleanup_process_tree(
                    helper_process=process,
                    helper_identity=helper_identity,
                    training_log=root / "training.log",
                    receipt=root / "run_start_receipt.json",
                )
            self.assertFalse(outcome["cleanup_complete"])
            self.assertIn("不属于本次 helper", " ".join(outcome["errors"]))
            kill.assert_not_called()

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
            helper_identity = {
                "pid": 1234,
                "pgid": 1234,
                "sid": 1234,
                "start_time_ticks": 99,
            }
            with patch.object(controller, "training_pid_from_log", return_value=None), patch.object(
                controller,
                "_terminate_helper_group",
                return_value="helper_group_killed",
            ), patch.object(
                controller,
                "process_group_members",
                side_effect=[[helper_identity], []],
            ):
                outcome = cleanup(
                    helper_process=process,
                    helper_identity=helper_identity,
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
            command = "python tools/run_v5_ablation_001_training.py --group FULL"
            command_sha256 = hashlib.sha256(command.encode("utf-8")).hexdigest()
            training_log.write_text(
                "GTPJ_TRAINING_PROCESS_STARTED "
                f"command_sha256={command_sha256} pid=1234 "
                "started_at=2026-08-07T00:00:00+00:00\n"
                "sealed training output\n"
                "GTPJ_TRAINING_PROCESS_FINISHED "
                f"command_sha256={command_sha256} pid=1234 returncode=0 "
                "finished_at=2026-08-07T00:01:00+00:00\n",
                encoding="utf-8",
            )
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

            payload["log_sha256"] = _sha256(training_log)
            payload["pid"] = 9999
            finish.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "pid"):
                validate(
                    receipt,
                    training_log,
                    command,
                    "RUN-001",
                    _run_ids()["RUN-001"],
                    0,
                )

    def test_claimed_layout_failure_writes_immutable_recovery_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim = root / "claim.json"
            claim.write_text('{"execution_id":"V5-ABLATION-001-test"}\n', encoding="utf-8")
            runtime = root / "runtime"
            runtime.mkdir()
            warehouse = root / "warehouse"
            status_data = {
                "experiment_id": "V5-ABLATION-001",
                "status": "failed",
                "jobs": {},
            }
            record = controller.persist_controller_failure(
                claim_path=claim,
                runtime_root=runtime,
                warehouse_root=warehouse,
                stage="prepare_layout",
                error=RuntimeError("clone failed"),
                status_data=status_data,
            )
            self.assertTrue(record.is_file())
            self.assertTrue((runtime / "recovery_handoff.json").is_file())
            payload = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual("prepare_layout", payload["failure_stage"])
            self.assertFalse(payload["automatic_resume_allowed"])
            with self.assertRaises(FileExistsError):
                controller.persist_controller_failure(
                    claim_path=claim,
                    runtime_root=runtime,
                    warehouse_root=warehouse,
                    stage="final_status",
                    error=RuntimeError("status failed"),
                    status_data=status_data,
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
                "cleanup_complete": False,
                "errors": ["helper still alive"],
                "finish_receipt": str(root / "finish.json"),
                "process_evidence_state": "process_tree_stopped",
                "receipt_state": "incomplete_missing_finish_receipt",
            }
            gate = controller.RunGate()
            with patch.object(controller.subprocess, "Popen", return_value=process), patch.object(
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller, "verify_data_source_identity", return_value=True
            ), patch.object(
                controller,
                "capture_helper_identity",
                return_value={"pid": 1234, "pgid": 1234, "sid": 1234, "start_time_ticks": 99},
            ), patch.object(
                controller,
                "cleanup_process_tree",
                return_value=cleanup_result,
            ) as cleanup:
                with self.assertRaisesRegex(RuntimeError, "清理不完整"):
                    controller.run_job(
                        args=SimpleNamespace(
                            python=Path(sys.executable),
                            commit="a" * 40,
                            launch_manifest_payload={},
                            python_runtime_identity={},
                            data_source=root,
                            data_runtime_identity={},
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
            failure_record = warehouse / "RUN-001" / "launch_failure.json"
            self.assertTrue(failure_record.is_file())
            payload = json.loads(failure_record.read_text(encoding="utf-8"))
            self.assertEqual(1234, payload["helper_pid"])
            self.assertFalse(payload["cleanup"]["cleanup_complete"])

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
                        launch_manifest_payload={},
                        python_runtime_identity={},
                        data_source=root,
                        data_runtime_identity={},
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
                            launch_manifest_payload={},
                            python_runtime_identity={},
                            data_source=root,
                            data_runtime_identity={},
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
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller, "verify_data_source_identity", return_value=True
            ), patch.object(
                controller,
                "capture_helper_identity",
                return_value={"pid": 1234, "pgid": 1234, "sid": 1234, "start_time_ticks": 99},
            ), patch.object(
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
                            launch_manifest_payload={},
                            python_runtime_identity={},
                            data_source=root,
                            data_runtime_identity={},
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
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller, "verify_data_source_identity", return_value=True
            ), patch.object(
                controller,
                "capture_helper_identity",
                return_value={"pid": 1234, "pgid": 1234, "sid": 1234, "start_time_ticks": 99},
            ), patch.object(
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

    def test_incomplete_cleanup_blocks_other_queue_before_status_write(self):
        cleanup_status_started = threading.Event()
        release_cleanup_status = threading.Event()

        class BlockingCleanupStatus:
            def update_job(self, _job_id, **values):
                if "cleanup_complete" in values:
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
            process.poll.return_value = 1
            process.wait.return_value = 1
            cleanup_result = {
                "training_pid": None,
                "training_termination": None,
                "helper_termination": None,
                "cleanup_complete": False,
                "errors": ["cleanup failed"],
                "finish_receipt": str(root / "finish.json"),
                "process_evidence_state": "incomplete_cleanup_error",
                "receipt_state": "incomplete_missing_finish_receipt",
            }
            gate = controller.RunGate()
            errors = []

            def execute_job():
                try:
                    controller.run_job(
                        args=SimpleNamespace(
                            python=Path(sys.executable),
                            commit="a" * 40,
                            launch_manifest_payload={},
                            python_runtime_identity={},
                            data_source=root,
                            data_runtime_identity={},
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
                controller, "verify_python_runtime", return_value={}
            ), patch.object(controller, "verify_data_source_identity", return_value=True), patch.object(
                controller,
                "capture_helper_identity",
                return_value={"pid": 1234, "pgid": 1234, "sid": 1234, "start_time_ticks": 99},
            ), patch.object(controller, "cleanup_process_tree", return_value=cleanup_result):
                worker = threading.Thread(target=execute_job)
                worker.start()
                self.assertTrue(cleanup_status_started.wait(1))
                later_launches = []
                self.assertIsNone(gate.launch_if_allowed(lambda: later_launches.append("started")))
                release_cleanup_status.set()
                worker.join(1)
            self.assertEqual([], later_launches)
            self.assertEqual(1, len(errors))

    def test_final_status_write_failure_blocks_other_queue_atomically(self):
        final_status_started = threading.Event()
        release_final_status = threading.Event()

        class FailOnCompletedStatus:
            def update_job(self, _job_id, **values):
                if values.get("status") == "completed":
                    final_status_started.set()
                    release_final_status.wait(2)
                    raise RuntimeError("final status write failed")

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
                "receipt_state": "verified",
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
                            launch_manifest_payload={},
                            python_runtime_identity={},
                            data_source=root,
                            data_runtime_identity={},
                        ),
                        group="FULL",
                        job_id="RUN-001",
                        code_root=root / "code",
                        ledger_root=ledger,
                        warehouse_root=warehouse,
                        stop_file=root / "STOP",
                        stop_requested=threading.Event(),
                        run_gate=gate,
                        status=FailOnCompletedStatus(),
                    )
                except Exception as exc:
                    errors.append(exc)

            with patch.object(
                controller.subprocess, "Popen", return_value=process
            ), patch.object(
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller, "verify_data_source_identity", return_value=True
            ), patch.object(
                controller,
                "capture_helper_identity",
                return_value={
                    "pid": 1234,
                    "pgid": 1234,
                    "sid": 1234,
                    "start_time_ticks": 99,
                },
            ), patch.object(
                controller, "cleanup_process_tree", return_value=cleanup_result
            ), patch.object(controller, "validate_finish_receipt"):
                worker = threading.Thread(target=execute_job)
                worker.start()
                self.assertTrue(final_status_started.wait(1))
                later = threading.Thread(
                    target=lambda: later_results.append(
                        gate.launch_if_allowed(lambda: "started")
                    )
                )
                later.start()
                later.join(0.05)
                self.assertTrue(later.is_alive())
                release_final_status.set()
                worker.join(1)
                later.join(1)
            self.assertEqual([None], later_results)
            self.assertEqual(1, len(errors))
            self.assertIn("final status write failed", str(errors[0]))

    def test_stop_observed_after_identity_check_prevents_helper_launch(self):
        class Status:
            def update_job(self, _job_id, **_values):
                return None

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
            stop_requested = threading.Event()
            gate = controller.RunGate()

            def observe_stop(*_args, **_kwargs):
                stop_requested.set()
                return True

            with patch.object(
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller,
                "verify_data_source_identity",
                side_effect=observe_stop,
            ), patch.object(controller.subprocess, "Popen") as popen:
                result = controller.run_job(
                    args=SimpleNamespace(
                        python=Path(sys.executable),
                        commit="a" * 40,
                        launch_manifest_payload={},
                        python_runtime_identity={},
                        data_source=root,
                        run_data_source=root,
                        data_runtime_identity={},
                    ),
                    group="FULL",
                    job_id="RUN-001",
                    code_root=root / "code",
                    ledger_root=ledger,
                    warehouse_root=warehouse,
                    stop_file=root / "STOP",
                    stop_requested=stop_requested,
                    run_gate=gate,
                    status=Status(),
                )
            self.assertIsNone(result)
            popen.assert_not_called()
            self.assertFalse(gate.claim_start())

    def test_stop_observed_during_launch_preparation_prevents_helper_launch(self):
        class Status:
            def update_job(self, _job_id, **_values):
                return None

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
            stop_requested = threading.Event()
            gate = controller.RunGate()
            original_environment = controller.os.environ.copy()

            def observe_stop_while_preparing():
                stop_requested.set()
                return original_environment.copy()

            helper_process = Mock(pid=1234)
            helper_process.poll.return_value = 0
            helper_process.wait.return_value = 0
            cleanup_result = {
                "cleanup_complete": True,
                "process_evidence_state": "confirmed_absent",
                "errors": [],
            }
            with patch.object(
                controller, "verify_python_runtime", return_value={}
            ), patch.object(
                controller, "verify_data_source_identity", return_value=True
            ), patch.object(
                controller.os.environ,
                "copy",
                side_effect=observe_stop_while_preparing,
            ), patch.object(
                controller.subprocess, "Popen", return_value=helper_process
            ) as popen, patch.object(
                controller,
                "capture_helper_identity",
                return_value={"start_time_ticks": 99},
            ), patch.object(
                controller, "cleanup_process_tree", return_value=cleanup_result
            ), patch.object(controller, "validate_finish_receipt"):
                controller.run_job(
                    args=SimpleNamespace(
                        python=Path(sys.executable),
                        commit="a" * 40,
                        launch_manifest_payload={},
                        python_runtime_identity={},
                        data_source=root,
                        run_data_source=root,
                        data_runtime_identity={},
                    ),
                    group="FULL",
                    job_id="RUN-001",
                    code_root=root / "code",
                    ledger_root=ledger,
                    warehouse_root=warehouse,
                    stop_file=root / "STOP",
                    stop_requested=stop_requested,
                    run_gate=gate,
                    status=Status(),
                )
            popen.assert_not_called()
            self.assertFalse(gate.claim_start())

    def test_runtime_uses_private_read_only_data_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, _, _, data_source = _create_evidence_bundle(root)
            manifest_path = (
                root
                / "source/experiments/v5/ablation/ABLATION-001_local_branch_effect/DATA_MANIFEST.json"
            )
            snapshot = root / "runtime" / "data_snapshot"
            with patch.object(controller, "SERVER_DATA_SOURCE", data_source.absolute()):
                source_identity = controller.verify_data_source(
                    data_source, manifest_path
                )
            snapshot_identity = controller.materialize_data_snapshot(
                data_source, snapshot, source_identity
            )
            first_relative = next(iter(controller.V5_REQUIRED_DATA_FILES.values()))
            snapshot_file = snapshot / first_relative
            snapshot_before = snapshot_file.read_bytes()
            source_file = data_source / first_relative
            source_file.write_bytes(b"changed-after-snapshot")

            self.assertEqual(snapshot_before, snapshot_file.read_bytes())
            self.assertTrue(
                controller.verify_snapshot_data_identity(
                    snapshot, snapshot_identity
                )
            )
            self.assertEqual(0, snapshot_file.stat().st_mode & 0o222)

    def test_atomic_claim_survives_temp_cleanup_failure_after_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim = root / "claim.json"
            original_unlink = Path.unlink

            def fail_temp_cleanup(path, *args, **kwargs):
                if Path(path).suffix == ".tmp":
                    raise OSError("temporary cleanup failed")
                return original_unlink(path, *args, **kwargs)

            with patch.object(Path, "unlink", new=fail_temp_cleanup):
                returned = controller._atomic_create_json(
                    claim, {"execution_id": "test"}
                )
            self.assertEqual(claim, returned)
            self.assertEqual(
                "test", json.loads(claim.read_text(encoding="utf-8"))["execution_id"]
            )

    def test_runtime_data_identity_rechecks_content_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, _, _, _, data_source = _create_evidence_bundle(root)
            manifest_path = (
                root
                / "source/experiments/v5/ablation/ABLATION-001_local_branch_effect/DATA_MANIFEST.json"
            )
            with patch.object(controller, "SERVER_DATA_SOURCE", data_source.absolute()):
                identity = controller.verify_data_source(data_source, manifest_path)
                first_relative = next(iter(controller.V5_REQUIRED_DATA_FILES.values()))
                changed = data_source / first_relative
                before = changed.stat()
                original = changed.read_bytes()
                changed.write_bytes(bytes([original[0] ^ 1]) + original[1:])
                os.utime(changed, ns=(before.st_atime_ns, before.st_mtime_ns))
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    controller.verify_data_source_identity(data_source, identity)

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
