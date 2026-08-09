"""V5 FGVD 几何编码旁路的行为与四次运行账本契约。"""

import ast
import csv
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path
import subprocess
import unittest
from unittest import mock

import torch
import yaml

from model.MyModel import GTPJ, fgvd_select_patches


ROOT = Path(__file__).resolve().parents[1]
TRAINING_SOURCE = ROOT / "train_GTPJ_CUB.py"
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "ablation"
    / "ABLATION-004_fgvd_geometry_effect"
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
CODE_COMMIT = "024474b12f3954355193dbcabd1905ba8218cda2"


def training_config_keys():
    module = ast.parse(TRAINING_SOURCE.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "V5_CONFIG_KEYS"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("V5_CONFIG_KEYS not found")


def config_values(path):
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }


def matrix_rows():
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def text_sha256(path):
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def make_config(**overrides):
    values = dict(
        num_class=6,
        dim_f_clip=16,
        pse_heads=2,
        pse_dropout=0.0,
        pse_inner_ratio=0.35,
        pse_outer_ratio=0.65,
        tf_common_dim=8,
        tf_heads=2,
        tf_dropout=0.0,
        weight_s2v=0.5,
        local_weight=0.2,
        score_mode="add",
        fgvd_select_k=4,
        ablation_disable_fgvd_geometry=True,
        icsa_ratio=0.008,
        icsa_hidden=8,
        sgmp_topk=1,
        sgmp_hidden=8,
        sgmp_neg_margin=0.2,
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        lambda_mpp=0.05,
        lambda_neg=0.01,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def make_model(config=None):
    torch.manual_seed(7)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    return GTPJ(
        config or make_config(),
        seen,
        unseen,
        torch.randn(seen.numel(), 16),
        torch.randn(unseen.numel(), 16),
        seen_sentence_embeds=torch.randn(seen.numel(), 3, 16),
    )


def grad_norm(parameters):
    return sum(
        float(parameter.grad.detach().abs().sum().item())
        for parameter in parameters
        if parameter.grad is not None
    )


class V5FgvdGeometryAblationTest(unittest.TestCase):
    def test_training_entry_requires_dedicated_true_flag(self):
        source = (ROOT / "train_GTPJ_CUB.py").read_text(encoding="utf-8")

        self.assertIn('"ablation_disable_fgvd_geometry",', source)
        self.assertIn(
            'if values["ablation_disable_fgvd_geometry"] is not True:',
            source,
        )

    def test_disabled_path_never_calls_geometry_or_encoder(self):
        model = make_model()
        features = torch.randn(2, 577, 16)

        with mock.patch.object(
            model.bvsa_module,
            "geometry_for_indices",
            side_effect=AssertionError("geometry_for_indices called"),
        ), mock.patch.object(
            model.bvsa_module.fgvd_encoder,
            "forward",
            side_effect=AssertionError("fgvd_encoder called"),
        ):
            output = model(features, is_train=False)

        self.assertEqual((2, 6), tuple(output["clip_S_pp"].shape))
        torch.testing.assert_close(output["sgmp_memory"], output["sgmp_patch_z"])

    def test_selected_patches_keep_original_topk_choice_and_count(self):
        model = make_model()
        features = torch.randn(2, 577, 16)
        patches = features[:, 1:, :]

        with torch.no_grad():
            expected_indices, _ = fgvd_select_patches(patches, K=4)
            gather_index = expected_indices.unsqueeze(-1).expand(-1, -1, patches.size(-1))
            expected_patches = torch.gather(patches, dim=1, index=gather_index)
            output = model(features, is_train=False)

        self.assertEqual((2, 4, 16), tuple(output["sgmp_selected_patches"].shape))
        torch.testing.assert_close(output["sgmp_selected_patches"], expected_patches)

    def test_output_contract_and_class_axes_are_unchanged(self):
        model = make_model()
        features = torch.randn(2, 577, 16)

        train_output = model(features, is_train=True)
        eval_output = model(features, is_train=False)

        self.assertEqual((2, 4), tuple(train_output["clip_S_pp"].shape))
        self.assertEqual((2, 6), tuple(eval_output["clip_S_pp"].shape))
        for name in (
            "final_logits",
            "global_logits",
            "local_logits",
            "score_s2v",
            "score_v2s",
            "sgmp_selected_patches",
            "sgmp_patch_z",
            "sgmp_memory",
            "all_text_cond",
        ):
            self.assertIn(name, train_output)

    def test_loss_gradients_bypass_only_fgvd_encoder(self):
        model = make_model()
        output = model(torch.randn(2, 577, 16), is_train=True)
        losses = model.compute_loss(
            dict(output, batch_label=torch.tensor([0, 3]))
        )

        model.zero_grad(set_to_none=True)
        losses["loss"].backward()

        self.assertGreater(grad_norm(model.bvsa_module.embed_cv.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.decoder_v2s.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.decoder_s2v.parameters()), 0.0)
        self.assertGreater(grad_norm(model.sgmp_predictor.parameters()), 0.0)
        self.assertEqual(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)

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
            EXPERIMENT_DIR / "evidence" / "README.md",
        ]
        required.extend(CONFIG_DIR / f"RUN-{index:03d}.yaml" for index in range(1, 5))
        self.assertEqual(
            [],
            [str(path.relative_to(ROOT)) for path in required if not path.is_file()],
        )

    def test_four_runs_use_two_seeds_and_two_exact_repeats(self):
        rows = matrix_rows()
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
        configs = [config_values(path) for path in config_paths]
        self.assertEqual([5, 5, 17, 17], [config["random_seed"] for config in configs])
        for config in configs:
            self.assertIs(config["ablation_disable_fgvd_geometry"], True)
            self.assertEqual(0.1, float(config["lambda_topo_pearson"]))
            self.assertEqual(set(config), training_config_keys())
        without_seed = [
            {key: value for key, value in config.items() if key != "random_seed"}
            for config in configs
        ]
        self.assertTrue(all(config == without_seed[0] for config in without_seed[1:]))
        expected_change = {"ablation_disable_fgvd_geometry": True}
        self.assertTrue(
            all(json.loads(row["changed_parameters"]) == expected_change for row in rows)
        )

    def test_matrix_uses_code_commit_and_actual_config_hashes(self):
        rows = matrix_rows()
        self.assertEqual({CODE_COMMIT}, {row["code_ref"] for row in rows})
        self.assertEqual({text_sha256(BASE_CONFIG)}, {row["base_config_sha256"] for row in rows})
        for row in rows:
            config_path = EXPERIMENT_DIR / row["config_snapshot_ref"]
            self.assertEqual(text_sha256(config_path), row["config_fingerprint"])
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
        self.assertIn("pending", str(experiment["implementation_status"]).lower())
        self.assertEqual("FGVD geometry encoding", experiment["disabled_subsystem"])
        self.assertIn("top-K", experiment["preserved_subsystem"])
        self.assertIn("BVSA", experiment["preserved_subsystem"])
        self.assertIn("SGMP", experiment["preserved_subsystem"])

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
