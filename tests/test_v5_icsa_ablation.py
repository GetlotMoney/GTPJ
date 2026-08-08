"""ICSA-off 消融分支的最小行为检查。"""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch
import yaml

from model.MyModel import GTPJ


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_CONFIG = ROOT / "experiments" / "v5" / "ablation" / "ABLATION-003_icsa_effect" / "config.yaml"
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
        "ablation_disable_icsa": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _training_config_keys():
    module = ast.parse(TRAINING_SOURCE.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "V5_CONFIG_KEYS"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("V5_CONFIG_KEYS not found")


class IcsaAblationTest(unittest.TestCase):
    def test_experiment_config_is_accepted_by_branch_schema(self):
        raw = yaml.safe_load(EXPERIMENT_CONFIG.read_text(encoding="utf-8"))
        values = {
            key: value["value"] if isinstance(value, dict) and "value" in value else value
            for key, value in raw.items()
        }
        self.assertTrue(values["ablation_disable_icsa"])
        self.assertEqual(set(values), _training_config_keys())

    def test_icsa_is_not_constructed_or_applied_when_disabled(self):
        torch.manual_seed(11)
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
        self.assertFalse(model.icsa_enabled)
        self.assertFalse(hasattr(model, "icsa_module"))
        self.assertFalse(any(name.startswith("icsa_module.") for name in model.state_dict()))

        model.eval()
        features = torch.randn(2, 577, 16)
        expected_text = model._make_all_text(features.device, features.dtype)
        outputs = model(features, is_train=False)
        expected_cond = expected_text.unsqueeze(0).expand(2, -1, -1)
        torch.testing.assert_close(outputs["all_text_cond"], expected_cond)
        self.assertEqual(tuple(outputs["final_logits"].shape), (2, 6))


if __name__ == "__main__":
    unittest.main()
