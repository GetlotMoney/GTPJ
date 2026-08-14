from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-016_te_pse_vsc"
)
TRAIN_PATH = EXPERIMENT_DIR / "train.py"
CONFIG_PATH = EXPERIMENT_DIR / "config.yaml"
SPEC = importlib.util.spec_from_file_location("v5_te_pse_vsc_train", TRAIN_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_model():
    sentences = torch.randn(5, 8, 12, generator=torch.Generator().manual_seed(71))
    return MODULE.TransferableEvidencePSE(
        sentences,
        (0, 1, 2, 3, 4, 5, 7),
        temperature=0.05,
        evidence_cap=0.5,
        evidence_init=0.1,
    )


class VisualSemanticConsistencyTest(unittest.TestCase):
    def test_centroids_use_only_supplied_training_indices(self):
        features = torch.tensor(
            [
                [1.0, 0.0, 0.0],
                [0.8, 0.2, 0.0],
                [-100.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.2, 0.8, 0.0],
                [0.0, -100.0, 0.0],
            ]
        )
        labels = torch.tensor([0, 0, 0, 1, 1, 1])
        train_indices = torch.tensor([0, 1, 3, 4])
        centroids = MODULE.class_visual_centroids(
            features, labels, torch.tensor([0, 1]), train_indices
        )
        expected_zero = F.normalize(
            F.normalize(features[[0, 1]], dim=-1).mean(dim=0), dim=0
        )
        expected_one = F.normalize(
            F.normalize(features[[3, 4]], dim=-1).mean(dim=0), dim=0
        )
        torch.testing.assert_close(centroids, torch.stack([expected_zero, expected_one]))
        torch.testing.assert_close(centroids.norm(dim=1), torch.ones(2))

    def test_centroid_order_follows_explicit_class_order(self):
        features = torch.eye(3)
        labels = torch.tensor([2, 0, 1])
        centroids = MODULE.class_visual_centroids(
            features,
            labels,
            torch.tensor([1, 2, 0]),
            torch.tensor([0, 1, 2]),
        )
        torch.testing.assert_close(centroids, features[[2, 0, 1]])

    def test_vsc_is_exact_symmetric_class_matching(self):
        model = make_model()
        visual = F.normalize(
            torch.randn(5, 12, generator=torch.Generator().manual_seed(73)), dim=-1
        )
        classes = torch.arange(5)
        actual, actual_v2s, actual_s2v = MODULE.visual_semantic_consistency_loss(
            model, visual, classes
        )
        semantic = model.effective_class_vectors()
        matching = visual @ semantic.T / model.temperature
        targets = torch.arange(5)
        expected_v2s = F.cross_entropy(matching, targets)
        expected_s2v = F.cross_entropy(matching.T, targets)
        torch.testing.assert_close(actual_v2s, expected_v2s)
        torch.testing.assert_close(actual_s2v, expected_s2v)
        torch.testing.assert_close(actual, 0.5 * (expected_v2s + expected_s2v))

    def test_vsc_updates_only_the_parent_shared_scalar(self):
        model = make_model()
        trainable = [(name, value.numel()) for name, value in model.named_parameters()]
        self.assertEqual(trainable, [("evidence_logit", 1)])
        visual = F.normalize(torch.randn(5, 12), dim=-1)
        loss, _, _ = MODULE.visual_semantic_consistency_loss(
            model, visual, torch.arange(5)
        )
        loss.backward()
        self.assertIsNotNone(model.evidence_logit.grad)
        self.assertTrue(torch.isfinite(model.evidence_logit.grad))

    def test_frozen_config_binds_only_the_new_loss(self):
        config, config_sha256 = MODULE.load_config(CONFIG_PATH)
        self.assertEqual(config_sha256, MODULE.EXPECTED_CONFIG_SHA256)
        self.assertEqual(config["vsc_weight"], 0.1)
        self.assertEqual(
            config["parent_te_pse_commit"],
            "b7f060afdd6d42baeee25b4d3068389085d88286",
        )
        for forbidden in ("gamma", "adapter", "local_weight", "topology"):
            self.assertNotIn(forbidden, config)

    def test_parent_te_pse_implementation_is_byte_frozen(self):
        parent_model = (
            EXPERIMENT_DIR.parent / "INNOVATION-015_te_pse" / "te_pse.py"
        )
        digest = hashlib.sha256(parent_model.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "a4691448b6980dfb32934929235b9e2fd5f6fcec447569ac90d5730e8b7de940",
        )

    def test_official_tensors_are_loaded_after_checkpoint_selection(self):
        source = TRAIN_PATH.read_text(encoding="utf-8")
        selection = source.index("model.load_state_dict(best_state)")
        official_load = source.index("official_tensor_names = (", selection)
        official_eval = source.index(
            "evaluation = PARENT.evaluate_predeclared_pair(", official_load
        )
        self.assertLess(selection, official_load)
        self.assertLess(official_load, official_eval)
        epoch_loop = source[source.index("for epoch in range"):selection]
        self.assertNotIn('tensors["seen_features"]', epoch_loop)
        self.assertNotIn('tensors["unseen_features"]', epoch_loop)

    def test_vsc_centroids_are_built_from_train_indices(self):
        source = TRAIN_PATH.read_text(encoding="utf-8")
        call_start = source.index("visual_centroids = class_visual_centroids(")
        call_end = source.index(").to(device)", call_start)
        call = source[call_start:call_end]
        self.assertIn("train_indices", call)
        self.assertNotIn("validation_indices", call)


if __name__ == "__main__":
    unittest.main()
