"""CONFIRM-002 五次同 seed GPU 诊断的服务器控制器测试。"""

import importlib.util
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "run_v5_seed_equivalence_server.py"
EXPERIMENT_DIR = REPO_ROOT / "experiments" / "v5" / "confirmation" / "CONFIRM-002_v5-seed-equivalence"


def load_controller_module():
    spec = importlib.util.spec_from_file_location("v5_seed_equivalence_server", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载 CONFIRM-002 服务器控制器")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class V5SeedEquivalenceServerTest(unittest.TestCase):
    def test_dedicated_server_controller_exists(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "CONFIRM-002 专用服务器控制器尚未实现")

    def test_controller_exposes_the_small_required_api(self) -> None:
        module = load_controller_module()
        required = {
            "LaunchError",
            "validate_plan",
            "validate_bundle",
            "validate_data_manifest",
            "require_tracked_runtime_file",
            "build_training_command",
            "parse_metrics",
            "run_waves",
            "Controller",
            "main",
        }
        missing = sorted(name for name in required if not hasattr(module, name))
        self.assertEqual([], missing)

    def test_plan_accepts_exactly_five_same_seed_jobs_in_three_waves(self) -> None:
        module = load_controller_module()
        jobs = [
            {
                "job_id": f"RUN-{index:03d}",
                "run_id": f"V5CONF002-R1-RUN-{index:03d}",
                "attempt": index,
                "gpu": 0 if index % 2 else 1,
                "seed": 5,
            }
            for index in range(1, 6)
        ]
        payload = {
            "schema_version": "gtpj.v5_confirmation_002.run_plan.v1",
            "experiment_id": "V5-CONFIRM-002",
            "jobs": jobs,
        }
        with tempfile.TemporaryDirectory() as temporary:
            plan_path = Path(temporary) / "RUN_PLAN.json"
            plan_path.write_text(json.dumps(payload), encoding="utf-8")
            try:
                actual = module.validate_plan(plan_path)
            except NotImplementedError:
                self.fail("validate_plan 尚未实现")
        self.assertEqual(payload, actual)

    def test_plan_and_data_manifest_must_come_from_the_final_checkout(self) -> None:
        module = load_controller_module()
        manifest_relative = module.EXPERIMENT_DIR / "DATA_MANIFEST.json"
        plan_relative = module.EXPERIMENT_DIR / "RUN_PLAN.json"
        self.assertEqual(
            REPO_ROOT / manifest_relative,
            module.require_tracked_runtime_file(
                REPO_ROOT,
                REPO_ROOT / manifest_relative,
                manifest_relative,
            ),
        )
        self.assertEqual(
            REPO_ROOT / plan_relative,
            module.require_tracked_runtime_file(
                REPO_ROOT,
                REPO_ROOT / plan_relative,
                plan_relative,
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary) / "DATA_MANIFEST.json"
            external.write_bytes((REPO_ROOT / manifest_relative).read_bytes())
            with self.assertRaises(module.LaunchError):
                module.require_tracked_runtime_file(REPO_ROOT, external, manifest_relative)

    def test_training_command_uses_read_only_data_and_private_train_log(self) -> None:
        module = load_controller_module()
        try:
            command = module.build_training_command(
                python=PurePosixPath("/fixed/python"),
                code_root=PurePosixPath("/runtime/code"),
                config=PurePosixPath("/runtime/code/experiments/v5/config.yaml"),
                job_root=PurePosixPath("/warehouse/RUN-001"),
                data_source=PurePosixPath("/trusted/data"),
            )
        except NotImplementedError:
            self.fail("build_training_command 尚未实现")
        self.assertEqual("/usr/bin/bwrap", command[0])
        self.assertIn("--die-with-parent", command)
        self.assertIn("--tmpfs", command)
        self.assertIn("/tmp", command)
        dev_index = command.index("/dev")
        self.assertEqual("--dev-bind", command[dev_index - 1])
        self.assertEqual("/dev", command[dev_index + 1])
        data_index = command.index("/trusted/data")
        self.assertEqual("--ro-bind", command[data_index - 1])
        self.assertEqual("/runtime/code/data", command[data_index + 1])
        log_index = command.index("/warehouse/RUN-001/train_log")
        self.assertEqual("--bind", command[log_index - 1])
        self.assertEqual("/runtime/code/train_log", command[log_index + 1])
        self.assertEqual(
            [
                "/fixed/python",
                "-B",
                "-u",
                "/runtime/code/train_GTPJ_CUB.py",
                "--config",
                "/runtime/code/experiments/v5/config.yaml",
            ],
            command[-6:],
        )
        self.assertNotIn("--resume-from", command)

    def test_metric_parser_reads_the_final_chinese_summary(self) -> None:
        module = load_controller_module()
        text = (
            "epoch 50: S=76.00% U=72.00% H=73.95% ZS=81.00%\n"
            "训练完成。\n"
            "最佳 epoch=31，U=72.36%，S=76.07%，H=74.17%，ZS=81.28%。\n"
        )
        try:
            metrics = module.parse_metrics(text)
        except NotImplementedError:
            self.fail("parse_metrics 尚未实现")
        self.assertEqual(
            {"best_epoch": 31, "U": 72.36, "S": 76.07, "H": 74.17, "ZS": 81.28},
            metrics,
        )

    def test_two_gpu_waves_never_dispatch_a_second_wave_after_failure(self) -> None:
        module = load_controller_module()
        jobs = [
            {"job_id": f"RUN-{index:03d}", "gpu": 0 if index % 2 else 1}
            for index in range(1, 6)
        ]
        started: list[str] = []

        def run_one(job):
            started.append(job["job_id"])
            return {"job_id": job["job_id"], "return_code": 1 if job["job_id"] == "RUN-001" else 0}

        try:
            results = module.run_waves(jobs, run_one, lambda: False)
        except NotImplementedError:
            self.fail("run_waves 尚未实现")
        self.assertEqual({"RUN-001", "RUN-002"}, set(started))
        self.assertEqual({"RUN-001", "RUN-002"}, {item["job_id"] for item in results})

    def test_data_manifest_checks_hash_size_shape_and_dtype(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "REQUIRED_INPUT_IDS"), "缺少固定输入文件清单")
        with tempfile.TemporaryDirectory() as temporary:
            data_root = Path(temporary) / "data"
            data_root.mkdir()
            mat_path = data_root / "meta.mat"
            mat_path.write_bytes(b"metadata")
            tensor_path = data_root / "features.pt"
            torch.save(torch.zeros((2, 3), dtype=torch.float16), tensor_path)

            def record(path: Path, *, shape=None, dtype=None):
                return {
                    "id": path.stem,
                    "relative_path": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size_bytes": path.stat().st_size,
                    "shape": shape,
                    "dtype": dtype,
                }

            manifest = {
                "schema_version": "gtpj.v5.data_manifest/v1",
                "dataset": "CUB",
                "files": [
                    record(mat_path),
                    record(tensor_path, shape=[2, 3], dtype="torch.float16"),
                ],
            }
            manifest_path = Path(temporary) / "DATA_MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with mock.patch.object(module, "REQUIRED_INPUT_IDS", {"meta", "features"}):
                try:
                    actual = module.validate_data_manifest(manifest_path, data_root)
                except NotImplementedError:
                    self.fail("validate_data_manifest 尚未实现")
        self.assertEqual(manifest, actual)

    def test_bundle_rejects_a_missing_historical_commit_before_gpu_use(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "EXPERIMENT_BRANCH"), "缺少实验分支身份")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "current.txt").write_text("current", encoding="utf-8")
            subprocess.run(["git", "add", "current.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "current"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "-M", module.EXPERIMENT_BRANCH], cwd=repo, check=True)
            current = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            missing = "0" * 40
            bundle = Path(temporary) / "current-only.bundle"
            subprocess.run(
                ["git", "bundle", "create", str(bundle), f"refs/heads/{module.EXPERIMENT_BRANCH}"],
                cwd=repo,
                check=True,
            )
            try:
                module.validate_bundle(bundle, repo, current, required_commits=[current, missing])
            except NotImplementedError:
                self.fail("validate_bundle 尚未实现")
            except module.LaunchError as exc:
                self.assertIn("缺少任务代码提交", str(exc))
            else:
                self.fail("缺少历史提交的 bundle 被错误放行")

    def test_each_job_gets_a_fresh_clean_detached_clone(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "clone_clean_checkout"), "缺少逐任务干净克隆")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / ".gitignore").write_text("data/\ntrain_log/\n", encoding="utf-8")
            (repo / "train.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", ".gitignore", "train.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "candidate"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "-M", module.EXPERIMENT_BRANCH], cwd=repo, check=True)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            bundle = Path(temporary) / "candidate.bundle"
            subprocess.run(
                ["git", "bundle", "create", str(bundle), f"refs/heads/{module.EXPERIMENT_BRANCH}"],
                cwd=repo,
                check=True,
            )
            destination = Path(temporary) / "job-code"
            module.clone_clean_checkout(bundle, destination, commit)
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=destination, check=True, capture_output=True, text=True
            ).stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain"], cwd=destination, check=True, capture_output=True, text=True
            ).stdout
            data_exists = (destination / "data").exists()
            train_log_exists = (destination / "train_log").exists()
        self.assertEqual(commit, head)
        self.assertEqual("", status)
        self.assertFalse(data_exists)
        self.assertFalse(train_log_exists)

    def test_physical_gpu_is_part_of_the_launch_identity(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "build_launch_spec"), "缺少完整启动身份")
        kwargs = {
            "python": PurePosixPath("/fixed/python"),
            "code_root": PurePosixPath("/runtime/code"),
            "config": PurePosixPath("/runtime/code/config.yaml"),
            "job_root": PurePosixPath("/warehouse/job"),
            "data_source": PurePosixPath("/trusted/data"),
        }
        gpu0 = module.build_launch_spec(physical_gpu=0, **kwargs)
        gpu1 = module.build_launch_spec(physical_gpu=1, **kwargs)
        self.assertEqual(gpu0["command_sha256"], gpu1["command_sha256"])
        self.assertNotEqual(gpu0["launch_identity_sha256"], gpu1["launch_identity_sha256"])
        self.assertEqual("0", gpu0["env_delta"]["CUDA_VISIBLE_DEVICES"])
        self.assertEqual("1", gpu1["env_delta"]["CUDA_VISIBLE_DEVICES"])

    def test_formal_probe_payload_must_bind_exact_commit_and_cuda(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "validate_formal_probe_payload"), "缺少正式零步探针硬门")
        commit = "1" * 40
        payload = {
            "status": "PASS",
            "git_head": commit,
            "git_branch": module.EXPERIMENT_BRANCH,
            "git_dirty": False,
            "formal_candidate_check_requested": True,
            "formal_candidate_identity_ok": True,
            "cuda_available": True,
            "cuda_device_count": 2,
            "active_state_mismatches": [],
            "post_model_cpu_rng_equal": True,
            "post_model_cuda_rng_equal": True,
            "first_three_batches_equal": True,
            "dead_parameter_names_present": False,
            "config_matches_expected_sha256": True,
            "candidate_model_matches_head": True,
        }
        self.assertEqual(payload, module.validate_formal_probe_payload(payload, commit))
        payload["git_head"] = "2" * 40
        with self.assertRaises(module.LaunchError):
            module.validate_formal_probe_payload(payload, commit)

    def test_prelaunch_failure_still_writes_finish_result_and_manifest(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module.Controller, "persist_early_failure"), "缺少启动前失败封存")
        with tempfile.TemporaryDirectory() as temporary:
            controller = object.__new__(module.Controller)
            controller.warehouse_execution = Path(temporary)
            controller.execution_id = "V5-CONFIRM-002-test"
            controller.commit = "1" * 40
            controller.config_sha256 = "2" * 64
            job = {
                "job_id": "RUN-001",
                "run_id": "V5CONF002-R1-RUN-001",
                "gpu": 0,
                "attempt": 1,
                "seed": 5,
            }
            result = controller.persist_early_failure(job, RuntimeError("probe failed"))
            job_root = Path(result["job_root"])
            finish = json.loads((job_root / "receipts" / "finish.json").read_text(encoding="utf-8"))
            stored_result = json.loads((job_root / "result.json").read_text(encoding="utf-8"))
            manifest = json.loads((job_root / "artifact_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(99, finish["evidence_return_code"])
        self.assertEqual(99, stored_result["return_code"])
        self.assertNotIn("artifact_manifest_sha256", stored_result)
        self.assertEqual(99, manifest["return_code"])
        self.assertNotIn("launch_receipt", manifest["artifacts"])

    def test_existing_but_unheld_gpu_lock_files_are_reused(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "acquire_gpu_locks"), "缺少 GPU 文件锁")
        calls = []
        fake_fcntl = SimpleNamespace(
            LOCK_EX=1,
            LOCK_NB=2,
            LOCK_UN=4,
            flock=lambda handle, operation: calls.append((handle, operation)),
        )
        with tempfile.TemporaryDirectory() as temporary:
            lock_root = Path(temporary)
            for gpu in (0, 1):
                (lock_root / f"gpu-{gpu}.lock").write_bytes(b"")
            with mock.patch.dict(sys.modules, {"fcntl": fake_fcntl}):
                handles = module.acquire_gpu_locks(lock_root, (0, 1))
                module.release_gpu_locks(handles)
            sizes = [(lock_root / f"gpu-{gpu}.lock").stat().st_size for gpu in (0, 1)]
        self.assertEqual([0, 0], sizes)
        self.assertEqual(4, len(calls))
        self.assertEqual([3, 3], [operation for _, operation in calls[:2]])
        self.assertEqual([4, 4], [operation for _, operation in calls[2:]])

    def test_execution_and_run_ids_are_permanently_claimed_without_overwrite(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "claim_execution_identity"), "缺少永久运行身份领取")
        fake_fcntl = SimpleNamespace(LOCK_EX=1, LOCK_UN=4, flock=lambda *_args: None)
        with tempfile.TemporaryDirectory() as temporary:
            claim_root = Path(temporary)
            kwargs = {
                "claim_root": claim_root,
                "execution_id": "V5-CONFIRM-002-abc",
                "commit": "1" * 40,
                "run_ids": ["V5CONF002-R1-RUN-001"],
                "bundle_sha256": "2" * 64,
            }
            with mock.patch.dict(sys.modules, {"fcntl": fake_fcntl}):
                claim = module.claim_execution_identity(**kwargs)
                original = claim.read_bytes()
                with self.assertRaises(module.LaunchError):
                    module.claim_execution_identity(**kwargs)
            unchanged = claim.read_bytes()
        self.assertEqual(original, unchanged)

    def test_gpu_preflight_rejects_any_active_compute_process(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "verify_server_gpu_preflight"), "缺少 GPU 空闲检查")
        completed = [
            subprocess.CompletedProcess([], 0, stdout="0, NVIDIA GeForce RTX 4090\n1, NVIDIA GeForce RTX 4090\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="GPU-uuid, 1234, python, 1024 MiB\n", stderr=""),
        ]
        with mock.patch.object(module.subprocess, "run", side_effect=completed):
            with self.assertRaises(module.LaunchError):
                module.verify_server_gpu_preflight()

    def test_post_review_freeze_rejects_controller_or_training_changes(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "verify_post_review_boundary"), "缺少审核后改动边界")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "controller.py").write_text("SAFE = True\n", encoding="utf-8")
            (repo / "model.py").write_text("MODEL = 1\n", encoding="utf-8")
            (repo / "agent_runtime.yaml").write_text("allowed: false\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "reviewed"], cwd=repo, check=True)
            reviewed = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            (repo / "agent_runtime.yaml").write_text("allowed: true\n", encoding="utf-8")
            subprocess.run(["git", "add", "agent_runtime.yaml"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "freeze"], cwd=repo, check=True)
            allowed = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            with mock.patch.object(module, "POST_REVIEW_ALLOWED_EXACT", {"agent_runtime.yaml"}), mock.patch.object(
                module, "POST_REVIEW_ALLOWED_PREFIXES", ()
            ):
                module.verify_post_review_boundary(repo, reviewed, allowed)
                (repo / "controller.py").write_text("SAFE = False\n", encoding="utf-8")
                subprocess.run(["git", "add", "controller.py"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-q", "-m", "tamper"], cwd=repo, check=True)
                tampered = subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
                ).stdout.strip()
                with self.assertRaises(module.LaunchError):
                    module.verify_post_review_boundary(repo, reviewed, tampered)

    def test_controller_must_execute_from_the_reviewed_commit_itself(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "verify_reviewed_controller_checkout"), "缺少控制器自身身份门")
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            controller_path = repo / "controller.py"
            controller_path.write_text("SAFE = True\n", encoding="utf-8")
            subprocess.run(["git", "add", "controller.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "reviewed"], cwd=repo, check=True)
            reviewed = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            module.verify_reviewed_controller_checkout(repo, reviewed, Path("controller.py"))
            controller_path.write_text("SAFE = False\n", encoding="utf-8")
            with self.assertRaises(module.LaunchError):
                module.verify_reviewed_controller_checkout(repo, reviewed, Path("controller.py"))

    def test_successful_process_writes_linked_receipts_result_and_artifacts(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module.Controller, "execute_prepared_job"), "缺少逐任务执行证据链")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            job_root = root / "warehouse" / "RUN-001"
            code_root = root / "code" / "RUN-001"
            for path in (job_root / "logs", job_root / "receipts", job_root / "train_log", code_root):
                path.mkdir(parents=True, exist_ok=True)
            (job_root / "config.yaml").write_text("seed: 5\n", encoding="utf-8")
            script = (
                "from pathlib import Path; "
                f"root=Path({str(job_root / 'train_log')!r})/'CUB'; root.mkdir(parents=True); "
                "(root/'training_log.txt').write_text('inner', encoding='utf-8'); "
                "(root/'best_model_H7417.pth').write_bytes(b'best'); "
                "(root/'ckpt_full.pth').write_bytes(b'full'); "
                "print('最佳 epoch=31，U=72.36%，S=76.07%，H=74.17%，ZS=81.28%。')"
            )
            launch_spec = {
                "argv": [sys.executable, "-c", script],
                "cwd": str(code_root),
                "env_delta": {"CUDA_VISIBLE_DEVICES": "0", "PYTHONUNBUFFERED": "1"},
                "command_sha256": "3" * 64,
                "launch_identity_sha256": "4" * 64,
            }
            controller = object.__new__(module.Controller)
            controller.execution_id = "V5-CONFIRM-002-test"
            controller.commit = "1" * 40
            controller.reviewed_controller_commit = "2" * 40
            controller.config_sha256 = hashlib.sha256((job_root / "config.yaml").read_bytes()).hexdigest()
            controller.bundle_sha256 = "5" * 64
            controller.data_manifest_sha256 = "6" * 64
            controller.probe_sha256 = "7" * 64
            controller.environment_evidence = {"torch": "test"}
            controller.stop_requested = __import__("threading").Event()
            controller.stop_path = root / "STOP"
            controller.running = {}
            controller.status_lock = __import__("threading").Lock()
            controller.launch_lock = __import__("threading").Lock()
            job = {
                "job_id": "RUN-001",
                "run_id": "V5CONF002-R1-RUN-001",
                "gpu": 0,
                "attempt": 1,
                "seed": 5,
            }
            result = controller.execute_prepared_job(job, job_root, code_root, launch_spec)
            start = json.loads((job_root / "receipts" / "start.json").read_text(encoding="utf-8"))
            finish = json.loads((job_root / "receipts" / "finish.json").read_text(encoding="utf-8"))
            manifest = json.loads((job_root / "artifact_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(0, result["return_code"], result)
        self.assertEqual(74.17, result["metrics"]["H"])
        self.assertEqual(hashlib.sha256((json.dumps(start, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest(), finish["start_receipt_sha256"])
        self.assertIn("best_model", manifest["artifacts"])
        self.assertIn("full_checkpoint", manifest["artifacts"])

    def test_frozen_matrix_matches_plan_and_declares_no_config_change(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "validate_matrix"), "缺少参数矩阵与运行计划交叉校验")
        plan = module.validate_plan(EXPERIMENT_DIR / "RUN_PLAN.json")
        with (EXPERIMENT_DIR / "PARAMETER_MATRIX.csv").open("r", encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
        for row in rows:
            row["status"] = "frozen"
        with tempfile.TemporaryDirectory() as temporary:
            matrix = Path(temporary) / "PARAMETER_MATRIX.csv"
            with matrix.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            actual = module.validate_matrix(matrix, plan, module.CONFIG_SHA256)
            self.assertEqual(5, len(actual))
            rows[0]["changed_parameters"] = '{"fake":1}'
            with matrix.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(module.LaunchError):
                module.validate_matrix(matrix, plan, module.CONFIG_SHA256)

    def test_preparation_failure_trips_global_stop_before_slow_evidence_write(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module.Controller, "run_one_safely"), "缺少失败总闸")
        controller = object.__new__(module.Controller)
        controller.stop_requested = __import__("threading").Event()
        controller.launch_lock = __import__("threading").Lock()
        controller.run_one = mock.Mock(side_effect=RuntimeError("clone failed"))

        def persist(job, error):
            self.assertTrue(controller.stop_requested.is_set())
            return {"job_id": job["job_id"], "return_code": 99}

        controller.persist_early_failure = persist
        result = controller.run_one_safely({"job_id": "RUN-001"})
        self.assertEqual(99, result["return_code"])

    def test_run_one_prepares_fresh_clone_and_ignored_mount_points(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module.Controller, "run_one"), "缺少逐任务准备")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            config_relative = module.EXPERIMENT_DIR / "config.yaml"
            (repo / config_relative.parent).mkdir(parents=True)
            (repo / config_relative).write_text("seed: 5\n", encoding="utf-8")
            (repo / ".gitignore").write_text("data/\ntrain_log/\n", encoding="utf-8")
            (repo / "train_GTPJ_CUB.py").write_text("print('unused')\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "candidate"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "-M", module.EXPERIMENT_BRANCH], cwd=repo, check=True)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
            bundle = root / "candidate.bundle"
            subprocess.run(
                ["git", "bundle", "create", str(bundle), f"refs/heads/{module.EXPERIMENT_BRANCH}"],
                cwd=repo,
                check=True,
            )
            controller = object.__new__(module.Controller)
            controller.commit = commit
            controller.training_candidate_commit = commit
            controller.execution_root = root / "runtime"
            controller.warehouse_execution = root / "warehouse"
            controller.execution_root.mkdir()
            controller.warehouse_execution.mkdir()
            controller.args = SimpleNamespace(
                bundle=bundle,
                python=Path(sys.executable),
                data_source=root / "data-source",
            )
            controller.args.data_source.mkdir()
            controller.config_sha256 = hashlib.sha256((repo / config_relative).read_bytes()).hexdigest()
            captured = {}

            def execute(job, job_root, code_root, launch_spec):
                captured.update(job_root=job_root, code_root=code_root, launch_spec=launch_spec)
                return {"job_id": job["job_id"], "return_code": 0}

            controller.execute_prepared_job = execute
            job = {"job_id": "RUN-001", "run_id": "V5CONF002-R1-RUN-001", "attempt": 1, "gpu": 0, "seed": 5}
            with mock.patch.object(
                module,
                "SCIENTIFIC_PATHS",
                (".gitignore", "train_GTPJ_CUB.py", config_relative.as_posix()),
            ):
                result = controller.run_one(job)
            status = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=captured["code_root"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        self.assertEqual(0, result["return_code"])
        self.assertEqual("", status)

    def test_controller_completes_only_after_all_five_jobs_succeed(self) -> None:
        module = load_controller_module()
        plan = module.validate_plan(EXPERIMENT_DIR / "RUN_PLAN.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "candidate.bundle"
            bundle.write_bytes(b"bundle")
            data_manifest = root / "DATA_MANIFEST.json"
            data_manifest.write_text("{}", encoding="utf-8")
            probe = root / "probe.json"
            probe.write_text("{}", encoding="utf-8")
            data_source = root / "data"
            data_source.mkdir()
            args = SimpleNamespace(
                final_commit="1" * 40,
                reviewed_controller_commit="2" * 40,
                bundle=bundle,
                data_manifest=data_manifest,
                python=Path(sys.executable),
                data_source=data_source,
                runtime_root=root / "runtime",
                warehouse_root=root / "warehouse",
                claim_root=root / "claims",
            )
            try:
                controller = module.Controller(args, root, plan, probe, {"torch": "test"})
            except TypeError:
                self.fail("Controller 初始化与完整五次收口尚未实现")
            controller.run_one_safely = lambda job: {
                "job_id": job["job_id"],
                "run_id": job["run_id"],
                "return_code": 0,
            }
            claim_path = root / "claims" / "claim.json"
            with mock.patch.object(module, "claim_execution_identity", return_value=claim_path):
                exit_code = controller.run()
            status = json.loads(controller.status_path.read_text(encoding="utf-8"))
        self.assertEqual(0, exit_code)
        self.assertEqual("completed", status["status"])
        self.assertEqual(5, len(status["results"]))

    def test_formal_probe_is_executed_and_saved_for_the_exact_commit(self) -> None:
        module = load_controller_module()
        self.assertTrue(hasattr(module, "run_formal_probe"), "缺少服务器正式 probe 执行")
        commit = "1" * 40
        payload = {
            "status": "PASS",
            "git_head": commit,
            "git_branch": module.EXPERIMENT_BRANCH,
            "git_dirty": False,
            "formal_candidate_check_requested": True,
            "formal_candidate_identity_ok": True,
            "cuda_available": True,
            "cuda_device_count": 2,
            "active_state_mismatches": [],
            "post_model_cpu_rng_equal": True,
            "post_model_cuda_rng_equal": True,
            "first_three_batches_equal": True,
            "dead_parameter_names_present": False,
            "config_matches_expected_sha256": True,
            "candidate_model_matches_head": True,
        }
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            probe_script = repo / "probe.py"
            probe_script.write_text(
                "import json\nprint(json.dumps(" + repr(payload) + "))\n",
                encoding="utf-8",
            )
            evidence = repo / "evidence.json"
            actual = module.run_formal_probe(
                python=Path(sys.executable),
                repo_root=repo,
                commit=commit,
                evidence_path=evidence,
                probe_path=probe_script,
            )
            stored = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(payload, actual)
        self.assertEqual(payload, stored)


if __name__ == "__main__":
    unittest.main()
