"""PSE 与 ICSA 同时关闭时的最小行为契约。"""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch
import torch.nn.functional as F

from model.MyModel import GTPJ


ROOT = Path(__file__).resolve().parents[1]
TRAINING_SOURCE = ROOT / "train_GTPJ_CUB.py"


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
        "lambda_topo_pearson": 0.1,
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


class PseIcsaInteractionTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
