"""V5-ABLATION-001 干净无局部分支的行为测试。"""

import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

import torch
import torch.nn.functional as F

from model.V5GlobalOnly import GTPJ
from model.MyModel import GTPJ as FullGTPJ


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATHS = (
    ROOT / "experiments" / "v5" / "ablation" / "ABLATION-001_local_branch_effect" / "configs" / "RUN-004.yaml",
    ROOT / "experiments" / "v5" / "ablation" / "ABLATION-001_local_branch_effect" / "configs" / "RUN-005.yaml",
    ROOT / "experiments" / "v5" / "ablation" / "ABLATION-001_local_branch_effect" / "configs" / "RUN-006.yaml",
)
MODEL_SOURCE = ROOT / "model" / "V5GlobalOnly.py"
TRAIN_SOURCE = ROOT / "train_V5_ABLATION_001_CUB.py"
FULL_TRAIN_SOURCE = ROOT / "train_GTPJ_CUB.py"

GLOBAL_ONLY_CONFIG_KEYS = {
    "dataset",
    "num_class",
    "dim_f_clip",
    "device",
    "batch_size",
    "random_seed",
    "text_source",
    "pse_heads",
    "pse_dropout",
    "pse_inner_ratio",
    "pse_outer_ratio",
    "lambda_topo_pearson",
    "icsa_ratio",
    "icsa_hidden",
    "lr_stages",
}


def _config():
    return SimpleNamespace(
        dataset="CUB",
        num_class=4,
        dim_f_clip=8,
        device="cpu",
        batch_size=2,
        random_seed=5,
        text_source="gpt55",
        pse_heads=2,
        pse_dropout=0.0,
        pse_inner_ratio=0.5,
        pse_outer_ratio=0.65,
        lambda_topo_pearson=0.1,
        icsa_ratio=0.008,
        icsa_hidden=4,
        lr_stages=[{"lr": 0.001, "epochs": 1, "eta_min": 1e-5}],
    )


def _model():
    torch.manual_seed(5)
    return GTPJ(
        _config(),
        seenclass=torch.tensor([0, 2]),
        unseenclass=torch.tensor([1, 3]),
        seen_text_embeds=torch.randn(2, 8),
        unseen_text_embeds=torch.randn(2, 8),
        seen_sentence_embeds=torch.randn(2, 3, 8),
    )


def _top_level_keys(text):
    return set(re.findall(r"^([a-zA-Z][a-zA-Z0-9_]*):\s*$", text, re.MULTILINE))


class V5GlobalOnlyAblationTest(unittest.TestCase):
    def test_training_entries_keep_class_identity_tensors_on_cpu(self):
        for path in (FULL_TRAIN_SOURCE, TRAIN_SOURCE):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "load_v5_cub_split"
                ]
                self.assertEqual(1, len(calls))
                self.assertGreaterEqual(len(calls[0].args), 6)
                self.assertIsInstance(calls[0].args[5], ast.Constant)
                self.assertEqual("cpu", calls[0].args[5].value)

    @unittest.skipUnless(torch.cuda.is_available(), "需要真实 CUDA 验证类别编号设备边界")
    def test_cpu_class_ids_initialize_both_models_with_cuda_text(self):
        from tests.test_fae_memory_jepa import make_config

        full_seen = torch.tensor([0, 2, 3, 5])
        full_unseen = torch.tensor([1, 4])
        full_sentences = torch.randn(6, 3, 16, device="cuda")
        full = FullGTPJ(
            make_config(),
            full_seen,
            full_unseen,
            seen_text_embeds=full_sentences[full_seen].mean(dim=1),
            unseen_text_embeds=full_sentences[full_unseen].mean(dim=1),
            seen_sentence_embeds=full_sentences[full_seen],
        ).to("cuda")

        global_seen = torch.tensor([0, 2])
        global_unseen = torch.tensor([1, 3])
        global_sentences = torch.randn(4, 3, 8, device="cuda")
        global_only = GTPJ(
            _config(),
            global_seen,
            global_unseen,
            seen_text_embeds=global_sentences[global_seen].mean(dim=1),
            unseen_text_embeds=global_sentences[global_unseen].mean(dim=1),
            seen_sentence_embeds=global_sentences[global_seen],
        ).to("cuda")

        self.assertEqual("cuda", full.seenclass.device.type)
        self.assertEqual("cuda", global_only.seenclass.device.type)

    def test_local_subsystem_is_not_instantiated(self):
        model = _model()
        names = {name for name, _ in model.named_parameters()}
        self.assertTrue(hasattr(model.pse_module, "proj"))
        self.assertTrue(hasattr(model.pse_module, "layer_norm"))
        self.assertFalse(hasattr(model, "bvsa_module"))
        self.assertFalse(hasattr(model, "sgmp_predictor"))
        self.assertFalse(any("bvsa" in name or "fgvd" in name or "sgmp" in name for name in names))

    def test_patch_tokens_cannot_change_train_or_eval_logits(self):
        model = _model().eval()
        cls = torch.randn(2, 1, 8)
        features_a = torch.cat([cls, torch.randn(2, 576, 8)], dim=1)
        features_b = torch.cat([cls, torch.randn(2, 576, 8) * 1000.0], dim=1)

        with torch.no_grad():
            eval_a = model(features_a, is_train=False)
            eval_b = model(features_b, is_train=False)
            train_a = model(features_a, is_train=True)
            train_b = model(features_b, is_train=True)

        torch.testing.assert_close(eval_a["clip_S_pp"], eval_b["clip_S_pp"], rtol=0, atol=0)
        torch.testing.assert_close(train_a["clip_S_pp"], train_b["clip_S_pp"], rtol=0, atol=0)
        self.assertEqual((2, 4), tuple(eval_a["clip_S_pp"].shape))
        self.assertEqual((2, 2), tuple(train_a["clip_S_pp"].shape))
        self.assertNotIn("local_logits", eval_a)

    def test_patch_tokens_receive_no_gradient(self):
        model = _model().eval()
        features = torch.randn(2, 577, 8, requires_grad=True)
        output = model(features, is_train=True)
        output["clip_S_pp"].sum().backward()
        self.assertGreater(float(features.grad[:, 0, :].abs().sum()), 0.0)
        self.assertEqual(0.0, float(features.grad[:, 1:, :].abs().sum()))

    def test_loss_is_only_ce_plus_topology(self):
        model = _model().eval()
        features = torch.randn(2, 577, 8)
        package = model(features, is_train=True)
        package["batch_label"] = torch.tensor([0, 2])
        losses = model.compute_loss(package)

        self.assertEqual({"loss", "loss_ce", "loss_topo"}, set(losses))
        expected = losses["loss_ce"] + 0.1 * losses["loss_topo"]
        torch.testing.assert_close(losses["loss"], expected)
        manual_ce = F.cross_entropy(package["clip_S_pp"], torch.tensor([0, 1]))
        torch.testing.assert_close(losses["loss_ce"], manual_ce)

    def test_config_and_sources_contain_no_local_route_controls(self):
        texts = [path.read_text(encoding="utf-8") for path in CONFIG_PATHS]
        for text in texts:
            self.assertEqual(GLOBAL_ONLY_CONFIG_KEYS, _top_level_keys(text))
        for seed, text in zip((5, 17, 29), texts):
            self.assertRegex(text, rf"(?m)^random_seed:\s*\n\s+value:\s*{seed}\s*$")

        model_source = MODEL_SOURCE.read_text(encoding="utf-8")
        train_source = TRAIN_SOURCE.read_text(encoding="utf-8")
        for token in (
            "BidirectionalVisualSemanticAlignment",
            "fgvd_select_patches",
            "sgmp_predictor",
            "local_logits",
            "local_weight",
            "lambda_consist",
            "lambda_bmdd",
            "lambda_mpp",
            "lambda_neg",
        ):
            self.assertNotIn(token, model_source)
            self.assertNotIn(token, train_source)
        self.assertIn("V5-ABLATION-001", train_source)
        self.assertNotIn("--resume-from", train_source)
        self.assertNotIn("weights_only=False", train_source)


if __name__ == "__main__":
    unittest.main()
