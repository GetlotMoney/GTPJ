import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "run_v5_code_equivalence_server.py"
PLAN_PATH = (
    REPO_ROOT
    / "experiments"
    / "v5"
    / "confirmation"
    / "CONFIRM-001_v5-code-equivalence"
    / "RUN_PLAN.json"
)
SPEC = importlib.util.spec_from_file_location("v5_confirmation_server", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class V5CodeEquivalenceServerTests(unittest.TestCase):
    def test_fixed_server_paths_compare_resolved_targets(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertIn("args.python.resolve() != SERVER_PYTHON.resolve()", source)
        self.assertIn("args.data_source.resolve() != SERVER_DATA_SOURCE.resolve()", source)
        self.assertIn("args.runtime_root.resolve() != SERVER_RUNTIME_ROOT.resolve()", source)
        self.assertIn("args.warehouse_root.resolve() != SERVER_WAREHOUSE_ROOT.resolve()", source)

    def test_legacy_command_uses_read_only_bubblewrap(self) -> None:
        command = ["/python", "/code/train_GTPJ_CUB.py", "--config", "/job/config.yaml"]
        wrapped = MODULE.wrap_legacy_command_read_only(
            command,
            code_root=Path("/code"),
            job_root=Path("/job"),
            data_source=Path("/trusted-data"),
        )
        self.assertEqual("/usr/bin/bwrap", wrapped[0])
        self.assertIn("--ro-bind", wrapped)
        trusted_data = str(Path("/trusted-data"))
        data_index = wrapped.index(trusted_data)
        self.assertEqual(str(Path("/code") / "data"), wrapped[data_index + 1])
        self.assertEqual(command, wrapped[-len(command):])

    def test_worker_stops_batch_after_first_hard_failure(self) -> None:
        controller = object.__new__(MODULE.Controller)
        controller.stop_requested = threading.Event()
        controller.stop_path = Path("Z:/path-that-does-not-exist/STOP")
        controller.results = []
        controller.status_lock = threading.Lock()
        controller.launch_lock = threading.Lock()
        controller.write_status = mock.Mock()
        controller.run_one = mock.Mock(return_value={"job_id": "RUN-001", "return_code": 1})
        jobs = [
            {"job_id": "RUN-001", "group": "CURRENT_TEMPLATE", "attempt": 1},
            {"job_id": "RUN-002", "group": "CURRENT_TEMPLATE", "attempt": 2},
        ]
        controller.worker(0, jobs)
        self.assertEqual(1, controller.run_one.call_count)
        self.assertTrue(controller.stop_requested.is_set())

    def test_two_gpu_wave_does_not_dispatch_a_second_wave_after_failure(self) -> None:
        controller = object.__new__(MODULE.Controller)
        controller.stop_requested = threading.Event()
        controller.stop_path = Path("Z:/path-that-does-not-exist/STOP")
        calls: list[str] = []

        def fake_worker(gpu: int, jobs: list[dict]) -> None:
            calls.append(str(jobs[0]["job_id"]))
            if gpu == 0:
                controller.stop_requested.set()

        controller.worker = fake_worker
        controller.run_waves(
            {
                0: [{"job_id": "GPU0-W1"}, {"job_id": "GPU0-W2"}],
                1: [{"job_id": "GPU1-W1"}, {"job_id": "GPU1-W2"}],
            }
        )
        self.assertNotIn("GPU0-W2", calls)
        self.assertNotIn("GPU1-W2", calls)

    def test_early_failure_still_produces_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            controller = object.__new__(MODULE.Controller)
            controller.warehouse_execution = Path(temporary)
            controller.execution_id = "V5-CONFIRM-001-test"
            controller.commit = "1" * 40
            job = {
                "job_id": "RUN-001",
                "run_id": "V5CONF001-CURRENT-001",
                "group": "CURRENT_TEMPLATE",
                "gpu": 0,
                "attempt": 1,
            }
            result = controller.persist_early_failure(job, RuntimeError("probe failure"))
            job_root = Path(result["job_root"])
            MODULE.atomic_json(job_root / "result.json", result)
            manifest = MODULE.write_manifest(job_root, result)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual("1" * 40, payload["code_commit"])
            self.assertEqual(MODULE.CURRENT_V5_CONFIG_SHA256, payload["config_sha256"])
            self.assertEqual(99, payload["return_code"])

    def test_bundle_missing_legacy_commit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "file.txt").write_text("current", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "current"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "-M", MODULE.EXPERIMENT_BRANCH], cwd=repo, check=True)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            bundle = Path(temporary) / "current-only.bundle"
            subprocess.run(
                ["git", "bundle", "create", str(bundle), f"refs/heads/{MODULE.EXPERIMENT_BRANCH}"],
                cwd=repo,
                check=True,
            )
            specs = {
                "CURRENT_TEMPLATE": {"code_commit": "launcher_commit"},
                "LEGACY_V5": {"code_commit": "0" * 40},
            }
            with mock.patch.object(MODULE, "GROUP_SPECS", specs):
                with self.assertRaisesRegex(MODULE.LaunchError, "bundle 缺少任务代码提交"):
                    MODULE.validate_bundle(bundle, repo, commit)

    def _write_plan(self, directory: Path, payload: dict) -> Path:
        path = directory / "plan.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_real_plan_has_three_balanced_groups(self) -> None:
        payload = MODULE.validate_plan(PLAN_PATH)
        self.assertEqual(15, len(payload["jobs"]))
        for group in MODULE.GROUP_SPECS:
            jobs = [job for job in payload["jobs"] if job["group"] == group]
            self.assertEqual(5, len(jobs))
            self.assertEqual([2, 3], sorted([sum(job["gpu"] == 0 for job in jobs), sum(job["gpu"] == 1 for job in jobs)]))
            self.assertEqual({1, 2, 3, 4, 5}, {job["attempt"] for job in jobs})
        self.assertEqual(15, len({job["run_id"] for job in payload["jobs"]}))

    def test_plan_rejects_gpu_confounded_group(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        for job in payload["jobs"]:
            if job["group"] == "LEGACY_V5":
                job["gpu"] = 0
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_plan(Path(temporary), payload)
            with self.assertRaisesRegex(MODULE.LaunchError, "2/3"):
                MODULE.validate_plan(path)

    def test_plan_rejects_missing_job(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        payload["jobs"].pop()
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_plan(Path(temporary), payload)
            with self.assertRaisesRegex(MODULE.LaunchError, "15"):
                MODULE.validate_plan(path)

    def test_plan_rejects_formal_job_mapped_to_legacy_group(self) -> None:
        payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        payload["jobs"][1]["group"] = "LEGACY_V5"
        payload["jobs"][0]["group"] = "CURRENT_TEMPLATE"
        with tempfile.TemporaryDirectory() as temporary:
            path = self._write_plan(Path(temporary), payload)
            with self.assertRaisesRegex(MODULE.LaunchError, "必须属于"):
                MODULE.validate_plan(path)

    def test_metric_parser_supports_current_chinese_summary(self) -> None:
        metrics = MODULE.parse_metrics("训练完成。\n最佳 epoch=31，U=72.36%，S=76.07%，H=74.17%，ZS=81.28%。\n")
        self.assertEqual({"best_epoch": 31, "U": 72.36, "S": 76.07, "H": 74.17, "ZS": 81.28}, metrics)

    def test_metric_parser_supports_legacy_summary(self) -> None:
        text = """
        Best Results @ Epoch 48
        │ GZSL-U : 73.00%
        │ GZSL-S : 77.36%
        │ GZSL-H : 75.11%
        │ ZSL    : 82.12%
        """
        metrics = MODULE.parse_metrics(text)
        self.assertEqual({"best_epoch": 48, "U": 73.0, "S": 77.36, "H": 75.11, "ZS": 82.12}, metrics)

    def test_current_command_uses_explicit_roots(self) -> None:
        command = MODULE.command_for_job(
            python=Path("/python"),
            code_root=Path("/code"),
            config=Path("/config.yaml"),
            job_root=Path("/warehouse/job"),
            data_source=Path("/data"),
            execution_mode="bound_root_arguments",
        )
        self.assertIn("--data-root", command)
        self.assertIn("--train-log-root", command)

    def test_legacy_command_keeps_exact_old_cli(self) -> None:
        command = MODULE.command_for_job(
            python=Path("/python"),
            code_root=Path("/code"),
            config=Path("/config.yaml"),
            job_root=Path("/warehouse/job"),
            data_source=Path("/data"),
            execution_mode="legacy_relative_roots",
        )
        self.assertEqual(
            [str(Path("/python")), str(Path("/code") / "train_GTPJ_CUB.py"), "--config", str(Path("/config.yaml"))],
            command,
        )

    def test_exact_source_and_config_identities_are_pinned(self) -> None:
        self.assertEqual("4b259379d99c1a791442ea9e2fac0bb22b2411a9", MODULE.LEGACY_V5_COMMIT)
        self.assertEqual("d505e992492eb6fe7272edf0f0dc1d15a5932434", MODULE.DYNAMIC_7511_COMMIT)
        self.assertEqual("a11706a51657bedec949f612aed2063dfe57807c5bc1a5c81219e4ce5b162aca", MODULE.V5_CONFIG_SHA256)
        self.assertEqual("def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e", MODULE.CURRENT_V5_CONFIG_SHA256)
        self.assertEqual("aec5ed6aa4c9ec872cd39383af5796b8daefde93d109c387b12df9363ca6953e", MODULE.DR095_SOURCE_CONFIG_SHA256)
        self.assertEqual("f4d95017cc884adb9a2549df4d88ee666e29c1e2b21e5395f5c4804a5eb83218", MODULE.DR095_CONFIG_SHA256)

    def test_all_real_config_files_match_frozen_hashes(self) -> None:
        for spec in MODULE.GROUP_SPECS.values():
            path = MODULE.validate_config(REPO_ROOT, spec)
            self.assertTrue(path.is_file())

    def test_current_config_is_old_v5_active_behavior_projection(self) -> None:
        experiment = PLAN_PATH.parent
        legacy = yaml.safe_load((experiment / "configs" / "V5-069.yaml").read_text(encoding="utf-8"))
        current = yaml.safe_load((experiment / "configs" / "CURRENT-V5.yaml").read_text(encoding="utf-8"))

        def unwrap(payload: dict) -> dict:
            return {
                key: value["value"] if isinstance(value, dict) and "value" in value else value
                for key, value in payload.items()
            }

        legacy_values = unwrap(legacy)
        current_values = unwrap(current)
        self.assertTrue(set(current_values) <= set(legacy_values))
        for key, current_value in current_values.items():
            legacy_value = legacy_values[key]
            if key == "lr_stages":
                legacy_value = [
                    {name: stage[name] for name in ("lr", "epochs", "eta_min")}
                    for stage in legacy_value
                ]
            self.assertEqual(current_value, legacy_value, key)

    def test_current_training_files_match_audited_today_blobs(self) -> None:
        for relative_path, expected_blob in MODULE.CURRENT_TRAINING_BLOBS.items():
            actual = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "hash-object", relative_path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(expected_blob, actual, relative_path)


if __name__ == "__main__":
    unittest.main()
