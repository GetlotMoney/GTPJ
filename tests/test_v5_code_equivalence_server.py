import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

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
        self.assertEqual("a884fea429a302fecc42ba8cddf9e6e66f5d07c8", MODULE.DYNAMIC_7511_COMMIT)
        self.assertEqual("a11706a51657bedec949f612aed2063dfe57807c5bc1a5c81219e4ce5b162aca", MODULE.V5_CONFIG_SHA256)
        self.assertEqual("def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e", MODULE.CURRENT_V5_CONFIG_SHA256)
        self.assertEqual("aec5ed6aa4c9ec872cd39383af5796b8daefde93d109c387b12df9363ca6953e", MODULE.DR095_CONFIG_SHA256)

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
