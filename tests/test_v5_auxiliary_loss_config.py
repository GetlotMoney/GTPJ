"""V5-ABLATION-006 纯配置冻结合同。"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ID = "V5-ABLATION-006"
EXPERIMENT_DIR = ROOT / "experiments" / "v5" / "ablation" / "ABLATION-006_auxiliary_loss_effect"
BASE_CONFIG = ROOT / "experiments" / "v5" / "config.yaml"
BASE_CONFIG_SHA256 = "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"
TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
REGISTRY_COMMIT = "4f29e99bb1a940afa66bb66f8150c379c2d0af7f"
BRANCH = "exp/v5/ablation/ablation-006-auxiliary-loss-effect"
KIND = "ablation"
PHYSICAL_GPU = "0"
CANDIDATES = [{"name":"CE-ONLY","changes":{"lambda_consist":0,"lambda_topo_pearson":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0},"preserved":{}},{"name":"BMDD-OFF","changes":{"lambda_bmdd":0},"preserved":{}},{"name":"CONSIST-OFF","changes":{"lambda_consist":0},"preserved":{}},{"name":"LOCAL-AUX-OFF","changes":{"lambda_consist":0,"lambda_bmdd":0,"lambda_mpp":0,"lambda_neg":0},"preserved":{"lambda_topo_pearson":0.1}}]
DOC_MARKERS = ["CE-ONLY","LOCAL-AUX-OFF","topology 保持 0.1"]
RUN_ORDER = [(5, 1), (5, 2), (17, 1), (17, 2)]
MATRIX_COLUMNS = [
    "job_id", "work_item_id", "job_kind", "status", "group", "name",
    "base_version", "base_config_sha256", "code_ref", "config_snapshot_ref",
    "seed", "changed_parameters", "config_fingerprint", "repeat_of",
    "duplicate_resolution", "purpose", "run_id", "run_start_receipt_ref",
    "run_start_receipt_sha256", "run_command_sha256", "run_log_sha256",
    "run_exit_code", "U", "S", "H", "ZS", "best_epoch", "decision",
    "artifact_ref", "artifact_manifest_sha256",
]
PRE_RUN_EMPTY_COLUMNS = MATRIX_COLUMNS[16:]
REQUIRED_FILES = {
    "DATA_MANIFEST.json", "EXPERIMENT.yaml", "PARAMETER_MATRIX.csv",
    "PARAMETER_MATRIX.md", "README.md", "SERVER_LAUNCH_PLAN.md",
    "implementation.md", "config.yaml", "evidence/README.md",
    "agent_runtime.yaml", "agent_summary.md", "quality_check.md",
    "AGENT_ACTIVITY.md", "agent_outputs/runner_monitor.md",
    "agent_outputs/interface_checker.md",
    "agent_outputs/evidence_quality_checker.md",
}
FORBIDDEN_FILES = {
    "manifest.yaml", "result.yaml", "result.md", "training.log",
}


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a YAML mapping")
    return data


def _config_values(path: Path) -> dict[str, object]:
    return {key: value["value"] for key, value in _yaml(path).items()}


class V5AuxiliaryLossConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            EXPERIMENT_DIR.is_dir(),
            f"frozen experiment directory is missing: {EXPERIMENT_DIR}",
        )

    def assert_utf8_lf_without_bom(self, path: Path) -> None:
        payload = path.read_bytes()
        self.assertFalse(payload.startswith(b"\xef\xbb\xbf"), path)
        self.assertNotIn(b"\r", payload, path)
        payload.decode("utf-8")

    def test_standard_pre_run_files_exist_without_fabricated_results(self) -> None:
        actual_files = {
            path.relative_to(EXPERIMENT_DIR).as_posix()
            for path in EXPERIMENT_DIR.rglob("*")
            if path.is_file()
        }
        self.assertTrue(REQUIRED_FILES <= actual_files)
        self.assertTrue(FORBIDDEN_FILES.isdisjoint(actual_files))
        run_count = len(CANDIDATES) * len(RUN_ORDER)
        self.assertEqual(
            [f"configs/RUN-{number:03d}.yaml" for number in range(1, run_count + 1)],
            sorted(path for path in actual_files if path.startswith("configs/")),
        )
        self.assertFalse(
            any(
                path.endswith((".log", ".pt", ".pth", ".ckpt"))
                or "checkpoint" in path.lower()
                for path in actual_files
            )
        )
        for path in EXPERIMENT_DIR.rglob("*"):
            if path.is_file() and path.suffix in {".yaml", ".json"}:
                self.assert_utf8_lf_without_bom(path)

    def test_experiment_binding_and_data_manifest_are_frozen(self) -> None:
        binding = _yaml(EXPERIMENT_DIR / "EXPERIMENT.yaml")
        expected = {
            "schema_version": "gtpj.experiment.v1",
            "experiment_id": EXPERIMENT_ID,
            "framework_id": "FRAMEWORK-V5",
            "kind": KIND,
            "base_identity_kind": "framework_template",
            "base_template_id": "MODEL-V5-TEMPLATE-V1",
            "base_template_tag": "model/v5-template-v1",
            "base_template_commit": TEMPLATE_COMMIT,
            "template_registry_commit": REGISTRY_COMMIT,
            "template_binding_status": "ready",
            "experiment_branch": BRANCH,
            "status": "pre_run_gated",
            "campaign_id": "CAMP-20260809-v5-ablation100",
            "formal_evidence": True,
            "not_confirmation_evidence": True,
            "implementation_status": "review_pending",
            "review_tier": "review-1",
            "activation_mode": "role_only",
            "formal_runtime_backend": "server_detached_role_only",
        }
        for key, value in expected.items():
            self.assertEqual(value, binding.get(key), key)
        self.assertNotIn("physical_gpu", binding)

        manifest = json.loads(
            (EXPERIMENT_DIR / "DATA_MANIFEST.json").read_text(encoding="utf-8")
        )
        self.assertEqual(EXPERIMENT_ID, manifest["experiment_id"])
        self.assertEqual("CUB", manifest["dataset"])
        self.assertEqual("v5", manifest["base_version"])
        self.assertEqual(BASE_CONFIG_SHA256, manifest["base_config_sha256"])
        self.assertEqual("server_preflight_required", manifest["data_identity_status"])
        self.assertTrue(manifest["formal_evidence"])
        self.assertTrue(manifest["not_confirmation_evidence"])

    def test_matrix_and_run_configs_match_the_exact_candidate_contract(self) -> None:
        self.assertEqual(BASE_CONFIG.read_bytes(), (EXPERIMENT_DIR / "config.yaml").read_bytes())
        self.assertEqual(
            BASE_CONFIG_SHA256,
            hashlib.sha256((EXPERIMENT_DIR / "config.yaml").read_bytes()).hexdigest(),
        )
        base_values = _config_values(BASE_CONFIG)
        with (EXPERIMENT_DIR / "PARAMETER_MATRIX.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(MATRIX_COLUMNS, reader.fieldnames)
            rows = list(reader)
        self.assertEqual(len(CANDIDATES) * len(RUN_ORDER), len(rows))

        expected_rows = [
            (candidate, seed, repeat)
            for candidate in CANDIDATES
            for seed, repeat in RUN_ORDER
        ]
        first_run_by_candidate_seed: dict[tuple[str, int], str] = {}
        for number, (row, expected_row) in enumerate(
            zip(rows, expected_rows, strict=True), start=1
        ):
            candidate, seed, repeat = expected_row
            candidate_name = candidate["name"]
            changes = candidate["changes"]
            job_id = f"RUN-{number:03d}"
            config_ref = f"configs/{job_id}.yaml"
            self.assertEqual(job_id, row["job_id"])
            self.assertEqual(EXPERIMENT_ID, row["work_item_id"])
            self.assertEqual(KIND, row["job_kind"])
            self.assertEqual("frozen", row["status"])
            self.assertEqual(candidate_name, row["group"])
            self.assertEqual(
                f"{candidate_name} seed={seed} repeat={repeat}", row["name"]
            )
            self.assertEqual("v5", row["base_version"])
            self.assertEqual(BASE_CONFIG_SHA256, row["base_config_sha256"])
            self.assertEqual(TEMPLATE_COMMIT, row["code_ref"])
            self.assertEqual(config_ref, row["config_snapshot_ref"])
            self.assertEqual(str(seed), row["seed"])
            self.assertEqual(changes, json.loads(row["changed_parameters"]))
            self.assertTrue(row["purpose"])
            self.assertTrue(all(row[column] == "" for column in PRE_RUN_EMPTY_COLUMNS))

            key = (candidate_name, seed)
            if repeat == 1:
                self.assertEqual("", row["repeat_of"])
                self.assertEqual("unique_config", row["duplicate_resolution"])
                first_run_by_candidate_seed[key] = job_id
            else:
                self.assertEqual(first_run_by_candidate_seed[key], row["repeat_of"])
                self.assertEqual("exact_repeat", row["duplicate_resolution"])

            config_path = EXPERIMENT_DIR / config_ref
            self.assert_utf8_lf_without_bom(config_path)
            run_values = _config_values(config_path)
            self.assertEqual(set(base_values), set(run_values))
            actual_changes = {
                key for key in base_values if base_values[key] != run_values[key]
            }
            self.assertTrue(actual_changes <= (set(changes) | {"random_seed"}))
            self.assertEqual(seed, run_values["random_seed"])
            self.assertEqual("cuda:0", run_values["device"])
            for field, value in changes.items():
                self.assertEqual(value, run_values[field])
            for field, value in candidate.get("preserved", {}).items():
                self.assertEqual(value, run_values[field])
            self.assertEqual(
                hashlib.sha256(
                    config_path.read_text(encoding="utf-8").encode("utf-8")
                ).hexdigest(),
                row["config_fingerprint"],
            )

    def test_human_ledgers_state_scope_and_limitations(self) -> None:
        combined = "\n".join(
            (EXPERIMENT_DIR / name).read_text(encoding="utf-8")
            for name in [
                "README.md", "SERVER_LAUNCH_PLAN.md", "implementation.md",
                "PARAMETER_MATRIX.md", "evidence/README.md",
            ]
        )
        for marker in [
            "CAMP-20260809-v5-ablation100",
            "server_detached_role_only",
            "review_pending",
            "review-1",
            "两种子双重复不是 confirmation",
            f"物理 GPU {PHYSICAL_GPU}",
            "cuda:0",
            *DOC_MARKERS,
        ]:
            self.assertIn(marker, combined)

        texts = [
            (ROOT / "experiments" / "EXPERIMENT_REGISTRY.md").read_text(encoding="utf-8"),
            (ROOT / "experiments" / "v5" / "ablation" / "INDEX.md").read_text(encoding="utf-8"),
            (ROOT / "experiments" / "v5" / "EXPERIMENTS.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "PROJECT_STRUCTURE.md").read_text(encoding="utf-8"),
        ]
        for text in texts:
            self.assertIn(EXPERIMENT_ID, text)
        for text in texts[:3]:
            self.assertIn("pre_run_gated", text)


if __name__ == "__main__":
    unittest.main()
