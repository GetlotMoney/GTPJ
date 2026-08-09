"""PSE 与 ICSA 同时关闭时的最小行为契约。"""

import ast
import csv
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

import torch
import torch.nn.functional as F
import yaml

from model.MyModel import GTPJ


ROOT = Path(__file__).resolve().parents[1]
TRAINING_SOURCE = ROOT / "train_GTPJ_CUB.py"
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "ablation"
    / "ABLATION-010_pse_icsa_interaction"
)
EXPERIMENT_SPEC = EXPERIMENT_DIR / "EXPERIMENT.yaml"
EXPERIMENT_CONFIG = EXPERIMENT_DIR / "config.yaml"
CONFIG_DIR = EXPERIMENT_DIR / "configs"
MATRIX = EXPERIMENT_DIR / "PARAMETER_MATRIX.csv"
README = EXPERIMENT_DIR / "README.md"
IMPLEMENTATION = EXPERIMENT_DIR / "implementation.md"
SERVER_PLAN = EXPERIMENT_DIR / "SERVER_LAUNCH_PLAN.md"
BASE_CONFIG = ROOT / "experiments" / "v5" / "config.yaml"
CAMPAIGN_ID = "CAMP-20260809-v5-ablation100"
CODE_COMMIT = "7e1592cf832546dd3ebb8a1d0331c12fbcbdd69e"


def _config(**overrides):
    values = {
        "num_class": 6,
        "dim_f_clip": 16,
        "pse_heads": 2,
        "pse_dropout": 0.0,
        "pse_inner_ratio": 0.35,
        "pse_outer_ratio": 0.65,
        "tf_common_dim": 8,
        "tf_heads": 2,
        "tf_dropout": 0.0,
        "weight_s2v": 0.5,
        "local_weight": 0.2,
        "fgvd_select_k": 4,
        "score_mode": "add",
        "lambda_consist": 0.05,
        "consist_temp": 2.0,
        "consist_dynamic_gamma": 0.1,
        "lambda_topo_pearson": 0.0,
        "icsa_ratio": 0.008,
        "icsa_hidden": 8,
        "lambda_bmdd": 0.05,
        "msdn_temp": 2.0,
        "sgmp_topk": 1,
        "sgmp_hidden": 8,
        "lambda_mpp": 0.05,
        "lambda_neg": 0.01,
        "sgmp_neg_margin": 0.2,
        "ablation_disable_pse": True,
        "ablation_disable_icsa": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _make_model():
    torch.manual_seed(23)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    model = GTPJ(
        _config(),
        seen,
        unseen,
        torch.randn(4, 16),
        torch.randn(2, 16),
        seen_sentence_embeds=torch.randn(4, 3, 16),
    )
    model.eval()
    return model


def _training_config_keys():
    module = ast.parse(TRAINING_SOURCE.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "V5_CONFIG_KEYS"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("V5_CONFIG_KEYS not found")


def _config_values(path):
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }


def _matrix_rows():
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _text_sha256(path):
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


class PseIcsaInteractionTest(unittest.TestCase):
    def test_run_ledger_files_exist(self):
        required = [
            EXPERIMENT_SPEC,
            EXPERIMENT_CONFIG,
            README,
            IMPLEMENTATION,
            SERVER_PLAN,
            MATRIX,
            EXPERIMENT_DIR / "PARAMETER_MATRIX.md",
            EXPERIMENT_DIR / "DATA_MANIFEST.json",
        ]
        required.extend(CONFIG_DIR / f"RUN-{index:03d}.yaml" for index in range(1, 5))
        self.assertEqual([], [str(path.relative_to(ROOT)) for path in required if not path.is_file()])

    def test_both_semantic_adapters_are_absent(self):
        model = _make_model()

        self.assertFalse(hasattr(model, "pse_module"))
        self.assertFalse(hasattr(model, "icsa_module"))
        self.assertFalse(any(name.startswith("pse_module.") for name in model.state_dict()))
        self.assertFalse(any(name.startswith("icsa_module.") for name in model.state_dict()))

        expected_seen = F.normalize(model.seen_sentence_embeds.mean(dim=1), dim=1)
        torch.testing.assert_close(model.get_adapted_seen_text(), expected_seen)

    def test_class_text_has_no_image_conditioned_icsa_offset(self):
        model = _make_model()
        features = torch.randn(2, 577, 16)

        expected = model._make_all_text(features.device, features.dtype)
        output = model(features, is_train=False)

        torch.testing.assert_close(
            output["all_text_cond"],
            expected.unsqueeze(0).expand(features.size(0), -1, -1),
        )

    def test_patch_path_and_output_contract_remain_active(self):
        model = _make_model()
        torch.manual_seed(29)
        cls = torch.randn(2, 1, 16)
        patches_a = torch.randn(2, 576, 16)
        patches_b = patches_a.clone()
        patches_b[:, :32, :] += 3.0

        output_a = model(torch.cat([cls, patches_a], dim=1), is_train=False)
        output_b = model(torch.cat([cls, patches_b], dim=1), is_train=False)

        expected_shapes = {
            "clip_S_pp": (2, 6),
            "local_logits": (2, 6),
            "sgmp_selected_patches": (2, 4, 16),
            "sgmp_patch_z": (2, 4, 8),
            "sgmp_memory": (2, 4, 8),
        }
        for key, shape in expected_shapes.items():
            self.assertIn(key, output_a)
            self.assertEqual(shape, tuple(output_a[key].shape))
        self.assertFalse(torch.allclose(output_a["local_logits"], output_b["local_logits"]))
        self.assertFalse(torch.allclose(output_a["final_logits"], output_b["final_logits"]))

    def test_train_and_eval_keep_declared_class_axes(self):
        model = _make_model()
        features = torch.randn(2, 577, 16)

        train_output = model(features, is_train=True)
        eval_output = model(features, is_train=False)

        self.assertEqual((2, 4), tuple(train_output["clip_S_pp"].shape))
        self.assertEqual((2, 6), tuple(eval_output["clip_S_pp"].shape))
        mapped = model._global_to_seen_labels(torch.tensor([5, 0, 3, 2]))
        torch.testing.assert_close(mapped, torch.tensor([3, 0, 2, 1]))

    def test_training_entry_requires_both_ablation_switches(self):
        source = TRAINING_SOURCE.read_text(encoding="utf-8")
        keys = _training_config_keys()

        self.assertIn("ablation_disable_pse", keys)
        self.assertIn("ablation_disable_icsa", keys)
        self.assertIn('values["ablation_disable_pse"] is not True', source)
        self.assertIn('values["ablation_disable_icsa"] is not True', source)

    def test_four_runs_use_two_seeds_and_two_exact_repeats(self):
        rows = _matrix_rows()
        self.assertEqual(
            [f"RUN-{index:03d}" for index in range(1, 5)],
            [row["job_id"] for row in rows],
        )
        self.assertEqual([5, 5, 17, 17], [int(row["seed"]) for row in rows])
        self.assertEqual(["", "RUN-001", "", "RUN-003"], [row["repeat_of"] for row in rows])
        for repeat_index, row in zip((1, 2, 1, 2), rows):
            self.assertIn(f"第{repeat_index}次", row["name"])
            self.assertIn(f"第{repeat_index}次", row["purpose"])

        config_paths = [CONFIG_DIR / f"RUN-{index:03d}.yaml" for index in range(1, 5)]
        configs = [_config_values(path) for path in config_paths]
        self.assertEqual([5, 5, 17, 17], [config["random_seed"] for config in configs])
        for config in configs:
            self.assertTrue(config["ablation_disable_pse"])
            self.assertTrue(config["ablation_disable_icsa"])
            self.assertEqual(0.0, float(config["lambda_topo_pearson"]))
            self.assertEqual(set(config), _training_config_keys())
        without_seed = [
            {key: value for key, value in config.items() if key != "random_seed"}
            for config in configs
        ]
        self.assertTrue(all(config == without_seed[0] for config in without_seed[1:]))
        expected_changes = {
            "ablation_disable_icsa": True,
            "ablation_disable_pse": True,
            "lambda_topo_pearson": 0.0,
        }
        self.assertTrue(
            all(json.loads(row["changed_parameters"]) == expected_changes for row in rows)
        )

    def test_topology_is_zero_while_local_training_gradients_remain_active(self):
        model = _make_model()
        model.train()
        torch.manual_seed(31)
        output = model(torch.randn(2, 577, 16), is_train=True)
        losses = model.compute_loss(
            dict(output, batch_label=torch.tensor([0, 3]))
        )

        model.zero_grad(set_to_none=True)
        losses["loss"].backward()

        self.assertEqual(0.0, float(losses["loss_topo"].item()))
        bvsa_grad = model.bvsa_module.embed_cv.weight.grad
        sgmp_grad = model.sgmp_predictor[0].weight.grad
        self.assertIsNotNone(bvsa_grad)
        self.assertIsNotNone(sgmp_grad)
        self.assertGreater(float(bvsa_grad.abs().sum().item()), 0.0)
        self.assertGreater(float(sgmp_grad.abs().sum().item()), 0.0)

    def test_matrix_uses_real_code_commit_and_actual_config_hashes(self):
        rows = _matrix_rows()
        self.assertEqual({CODE_COMMIT}, {row["code_ref"] for row in rows})
        self.assertEqual({_text_sha256(BASE_CONFIG)}, {row["base_config_sha256"] for row in rows})
        for row in rows:
            config_path = EXPERIMENT_DIR / row["config_snapshot_ref"]
            self.assertEqual(_text_sha256(config_path), row["config_fingerprint"])
        subprocess.run(
            ["git", "cat-file", "-e", f"{CODE_COMMIT}^{{commit}}"],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", CODE_COMMIT, "HEAD"],
            cwd=ROOT,
            check=True,
        )

    def test_screening_metadata_and_campaign_launch_boundary(self):
        experiment = yaml.safe_load(EXPERIMENT_SPEC.read_text(encoding="utf-8"))
        self.assertTrue(experiment["formal_evidence"])
        self.assertTrue(experiment["not_confirmation_evidence"])
        self.assertEqual("server_detached_role_only", experiment["workflow_mode"])
        self.assertEqual("strict-3", experiment["review_tier"])
        self.assertNotIn("complete", str(experiment["implementation_status"]).lower())
        self.assertNotIn("topology", experiment["preserved_subsystem"])
        self.assertIn(
            "PSE-dependent topology",
            experiment["disabled_dependent_subsystem"],
        )

        for path in (README, SERVER_PLAN):
            text = path.read_text(encoding="utf-8")
            self.assertIn(CAMPAIGN_ID, text)
            self.assertIn("GPU 1", text)
            self.assertTrue("不可手工正式启动" in text or "禁止手工正式启动" in text)
            self.assertNotIn("python train_GTPJ_CUB.py", text)

        forbidden = ["manifest.yaml", "result.yaml", "result.md"]
        self.assertEqual([], [name for name in forbidden if (EXPERIMENT_DIR / name).exists()])


if __name__ == "__main__":
    unittest.main()
