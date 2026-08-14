from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import torch
import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-015_te_pse"
    / "te_pse.py"
)
SPEC = importlib.util.spec_from_file_location("v5_te_pse", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TransferableEvidencePSE = MODULE.TransferableEvidencePSE

TRAIN_PATH = MODULE_PATH.with_name("train.py")
TRAIN_SPEC = importlib.util.spec_from_file_location("v5_te_pse_train", TRAIN_PATH)
assert TRAIN_SPEC is not None and TRAIN_SPEC.loader is not None
TRAIN_MODULE = importlib.util.module_from_spec(TRAIN_SPEC)
TRAIN_SPEC.loader.exec_module(TRAIN_MODULE)
CONFIG_PATH = MODULE_PATH.with_name("config.yaml")


def make_sentence_embeds() -> torch.Tensor:
    generator = torch.Generator().manual_seed(23)
    return torch.randn(5, 8, 12, generator=generator)


def make_model() -> TransferableEvidencePSE:
    return TransferableEvidencePSE(
        make_sentence_embeds(),
        (0, 1, 2, 3, 4, 5, 7),
        temperature=0.05,
        evidence_cap=0.5,
        evidence_init=0.1,
    )


class TransferableEvidencePSETest(unittest.TestCase):
    def test_has_no_attention_and_only_one_trainable_scalar(self):
        model = make_model()
        trainable = [(name, value.numel()) for name, value in model.named_parameters()]
        self.assertEqual(trainable, [("evidence_logit", 1)])
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("MultiheadAttention", source)
        self.assertNotIn("self_attention", source)

    def test_rivals_are_other_classes_in_the_same_role(self):
        model = make_model()
        class_ids = torch.arange(5).view(-1, 1)
        self.assertTrue(torch.all(model.rival_class_ids.cpu() != class_ids))
        target = model.sentence_embeds[:, model.evidence_role_indices]
        role_ids = torch.arange(7).view(1, -1).expand(5, -1)
        rival = target[model.rival_class_ids, role_ids]
        actual = (target * rival).sum(dim=-1)
        torch.testing.assert_close(actual, model.rival_cosine)

    def test_role_weights_and_coherence_are_bounded(self):
        model = make_model()
        torch.testing.assert_close(model.role_weights.sum(dim=1), torch.ones(5))
        self.assertTrue(torch.all(model.role_weights >= 0.0))
        self.assertTrue(torch.all(model.evidence_coherence >= 0.0))
        self.assertTrue(torch.all(model.evidence_coherence <= 1.0 + 1e-6))

    def test_final_logit_is_exact_sum_of_reported_role_terms(self):
        model = make_model()
        images = torch.randn(4, 12, generator=torch.Generator().manual_seed(31))
        result = model.score_components(images)
        reconstructed = result["base_logits"] + result["role_contributions"].sum(-1)
        torch.testing.assert_close(result["final_logits"], reconstructed)

        deleted_role = 3
        without_role = result["final_logits"] - result["role_contributions"][
            :, :, deleted_role
        ]
        torch.testing.assert_close(
            result["final_logits"] - without_role,
            result["role_contributions"][:, :, deleted_role],
        )

    def test_class_selection_uses_the_identical_seen_unseen_formula(self):
        model = make_model()
        images = torch.randn(3, 12, generator=torch.Generator().manual_seed(37))
        selected = torch.tensor([0, 3, 4])
        full = model.score_components(images)
        subset = model.score_components(images, selected)
        torch.testing.assert_close(subset["final_logits"], full["final_logits"][:, selected])
        torch.testing.assert_close(
            subset["role_contributions"], full["role_contributions"][:, selected]
        )

    def test_strength_is_positive_bounded_and_receives_gradient(self):
        model = make_model()
        strength = float(model.evidence_strength.detach())
        self.assertGreater(strength, 0.0)
        self.assertLess(strength, model.evidence_cap)
        images = torch.randn(6, 12, generator=torch.Generator().manual_seed(41))
        loss = model.logits(images).square().mean()
        loss.backward()
        self.assertIsNotNone(model.evidence_logit.grad)
        self.assertTrue(torch.isfinite(model.evidence_logit.grad))
        self.assertNotEqual(float(model.evidence_logit.grad), 0.0)

    def test_rejects_invalid_shapes_roles_and_bounds(self):
        sentences = make_sentence_embeds()
        with self.assertRaisesRegex(ValueError, "shape"):
            TransferableEvidencePSE(
                sentences[0], (0,), temperature=0.05, evidence_cap=0.5, evidence_init=0.1
            )
        with self.assertRaisesRegex(ValueError, "unique"):
            TransferableEvidencePSE(
                sentences, (0, 0), temperature=0.05, evidence_cap=0.5, evidence_init=0.1
            )
        with self.assertRaisesRegex(ValueError, "require"):
            TransferableEvidencePSE(
                sentences, (0,), temperature=0.05, evidence_cap=0.5, evidence_init=0.5
            )
        model = make_model()
        with self.assertRaisesRegex(ValueError, "image_features"):
            model.logits(torch.randn(2, 11))

    def test_frozen_config_is_self_bound_and_has_no_attention_parameters(self):
        config, config_sha256 = TRAIN_MODULE.load_config(CONFIG_PATH)
        self.assertEqual(config_sha256, TRAIN_MODULE.EXPECTED_CONFIG_SHA256)
        self.assertEqual(config["baseline_H"], 64.16403868322334)
        self.assertEqual(config["evidence_cap"], 0.5)
        self.assertEqual(config["evidence_init"], 0.1)
        self.assertEqual(len(config["evidence_roles"]), 7)
        for forbidden in ("pse_heads", "pse_dropout", "role_hidden", "local_weight"):
            self.assertNotIn(forbidden, config)
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(raw, config)

    def test_checkpoint_selection_precedes_official_test_evaluation(self):
        source = TRAIN_PATH.read_text(encoding="utf-8")
        selection = source.index("model.load_state_dict(best_state)")
        official_load = source.index("official_tensor_names = (", selection)
        official_test = source.index(
            "\n    evaluation = evaluate_predeclared_pair(", official_load
        )
        self.assertLess(selection, official_load)
        self.assertLess(official_load, official_test)
        epoch_loop = source[source.index("for epoch in range"):selection]
        self.assertNotIn('tensors["seen_features"]', epoch_loop)
        self.assertNotIn('tensors["unseen_features"]', epoch_loop)

    def test_stratified_split_is_deterministic_and_disjoint(self):
        labels = torch.repeat_interleave(torch.arange(3), 10)
        classes = torch.arange(3)
        first = TRAIN_MODULE.stratified_train_validation_split(labels, classes, 0.2, 5)
        second = TRAIN_MODULE.stratified_train_validation_split(labels, classes, 0.2, 5)
        torch.testing.assert_close(first[0], second[0])
        torch.testing.assert_close(first[1], second[1])
        self.assertFalse(torch.isin(first[0], first[1]).any())
        self.assertEqual(first[0].numel() + first[1].numel(), labels.numel())

    def test_macro_accuracy_is_per_class_not_sample_weighted(self):
        labels = torch.tensor([0, 0, 0, 1])
        predictions = torch.tensor([0, 0, 1, 0])
        value = TRAIN_MODULE.per_class_accuracy(labels, predictions, torch.tensor([0, 1]))
        self.assertAlmostEqual(value, 1.0 / 3.0, places=6)


if __name__ == "__main__":
    unittest.main()
