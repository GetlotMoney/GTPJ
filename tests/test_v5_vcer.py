from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-017_vcer"
    / "vcer.py"
)
SPEC = importlib.util.spec_from_file_location("v5_vcer", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VCER = MODULE.VisibilityAwareCounterfactualEvidenceRouter


def make_inputs(seed: int = 11):
    generator = torch.Generator().manual_seed(seed)
    sentences = F.normalize(torch.randn(5, 8, 12, generator=generator), dim=-1)
    prototypes = F.normalize(torch.randn(5, 12, generator=generator), dim=-1)
    images = F.normalize(torch.randn(3, 12, generator=generator), dim=-1)
    patches = F.normalize(torch.randn(3, 7, 12, generator=generator), dim=-1)
    return sentences, prototypes, images, patches


def make_model() -> VCER:
    sentences, prototypes, _, _ = make_inputs()
    return VCER(sentences, prototypes, 14.0, rank=4)


class VCERTest(unittest.TestCase):
    def test_contract_has_only_one_shared_low_rank_projector(self):
        model = make_model()
        self.assertEqual(
            set(dict(model.named_parameters())), {"down.weight", "up.weight"}
        )
        self.assertEqual(tuple(model.local_role_indices.tolist()), (0, 1, 2, 3, 4, 5))
        self.assertEqual(model.global_role_index, 6)
        self.assertEqual(model.unique_role_index, 7)

    def test_disabled_path_preserves_x2_positional_interface_and_class_order(self):
        sentences, prototypes, images, _ = make_inputs()
        model = VCER(sentences, prototypes, 14.0, rank=4)
        classes = torch.tensor([4, 1, 3])
        expected = (
            F.normalize(images, dim=-1)
            @ prototypes.index_select(0, classes).T
            * 14.0
        )
        actual = model.logits(images, classes, evidence_enabled=False)
        self.assertTrue(torch.equal(model.x2_prototypes, prototypes))
        self.assertTrue(torch.equal(actual, expected))

    def test_each_candidate_uses_the_best_other_baseline_class(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        components = model.score_components(images, patches)
        base = components["base_cosine"]
        rivals = components["rival_candidate_positions"]
        for batch in range(base.shape[0]):
            for candidate in range(base.shape[1]):
                allowed = [index for index in range(base.shape[1]) if index != candidate]
                expected = max(allowed, key=lambda index: float(base[batch, index]))
                self.assertEqual(int(rivals[batch, candidate]), expected)

    def test_score_terms_are_bounded_normalized_and_exact(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        components = model.score_components(images, patches)
        self.assertTrue(
            torch.allclose(
                components["role_weights"].sum(dim=-1),
                torch.ones(3, 5),
                atol=1e-6,
            )
        )
        self.assertTrue(
            torch.allclose(
                components["patch_weights"].sum(dim=2),
                torch.ones(3, 5, 6),
                atol=1e-6,
            )
        )
        self.assertGreaterEqual(
            float(components["visibility"].min().detach()), 0.0
        )
        self.assertLessEqual(
            float(components["visibility"].max().detach()), 1.0 + 1e-6
        )
        expected = (
            0.5
            * (components["base_cosine"] + components["evidence_correction"])
            * model.x2_scale
        )
        self.assertTrue(torch.allclose(components["final_logits"], expected))

    def test_unique_swap_changes_only_semantic_routing(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        normal = model.score_components(images, patches)
        swapped = model.score_components(
            images, patches, unique_swap_with_rival=True
        )
        for key in (
            "base_logits",
            "rival_class_ids",
            "patch_margins",
            "foreground",
            "evidence_strength",
        ):
            self.assertTrue(torch.equal(normal[key], swapped[key]), key)
        self.assertFalse(torch.equal(normal["role_weights"], swapped["role_weights"]))

    def test_cross_class_local_replacement_does_not_change_frozen_base(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        normal = model.score_components(images, patches)
        source_ids = torch.tensor([1, 2, 3, 4, 0])
        replaced = model.score_components(
            images, patches, local_source_ids=source_ids
        )
        self.assertTrue(torch.equal(normal["base_logits"], replaced["base_logits"]))
        self.assertTrue(
            torch.equal(normal["rival_class_ids"], replaced["rival_class_ids"])
        )
        self.assertFalse(torch.equal(normal["patch_margins"], replaced["patch_margins"]))

    def test_role_shuffle_breaks_router_to_evidence_correspondence(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        normal = model.score_components(images, patches)
        permutation = torch.tensor([1, 2, 3, 4, 5, 0])
        shuffled = model.score_components(
            images,
            patches,
            role_evidence_permutation=permutation,
        )
        for key in (
            "base_logits",
            "rival_class_ids",
            "role_weights",
            "patch_margins",
            "role_evidence",
        ):
            self.assertTrue(torch.equal(normal[key], shuffled[key]), key)
        self.assertTrue(
            torch.equal(
                shuffled["aligned_role_evidence"],
                normal["role_evidence"].index_select(-1, permutation),
            )
        )
        self.assertFalse(
            torch.allclose(
                normal["evidence_correction"],
                shuffled["evidence_correction"],
            )
        )

    def test_same_formula_handles_arbitrary_seen_unseen_candidate_ids(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        mixed_classes = torch.tensor([0, 2, 4])
        components = model.score_components(images, patches, mixed_classes)
        self.assertEqual(tuple(components["final_logits"].shape), (3, 3))
        self.assertTrue(torch.isin(components["rival_class_ids"], mixed_classes).all())
        for candidate_position, class_id in enumerate(mixed_classes):
            self.assertTrue(
                (components["rival_class_ids"][:, candidate_position] != class_id).all()
            )

    def test_training_loss_reaches_zero_initialized_up_projection(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        images = images.clone().requires_grad_(True)
        patches = patches.clone().requires_grad_(True)
        labels = torch.tensor([0, 1, 2])
        losses = model.training_loss(
            images, patches, labels, torch.arange(5)
        )
        losses["loss"].backward()
        self.assertTrue(torch.isfinite(losses["loss"]))
        self.assertIsNotNone(model.up.weight.grad)
        self.assertTrue(torch.isfinite(model.up.weight.grad).all())
        self.assertGreater(float(model.up.weight.grad.abs().sum()), 0.0)
        self.assertIsNone(images.grad)
        self.assertIsNone(patches.grad)

    def test_loss_and_visual_gradients_are_exactly_disabled_with_vcer_off(self):
        model = make_model()
        _, _, images, _ = make_inputs()
        images = images.clone().requires_grad_(True)
        classes = torch.tensor([0, 1, 2, 3])
        labels = torch.tensor([0, 1, 2])
        expected_logits = (
            F.normalize(images.detach(), dim=-1)
            @ model.x2_prototypes.index_select(0, classes).T
            * model.x2_scale
        )
        expected = F.cross_entropy(expected_logits, labels)
        losses = model.training_loss(
            images,
            None,
            labels,
            classes,
            evidence_enabled=False,
            unique_causal_weight=0.0,
            preserve_weight=0.0,
        )
        self.assertTrue(torch.equal(losses["loss"], expected))
        self.assertTrue(torch.equal(losses["loss"], losses["classification_loss"]))
        self.assertEqual(float(losses["unique_causal_loss"]), 0.0)
        self.assertEqual(float(losses["preservation_loss"]), 0.0)
        self.assertFalse(losses["loss"].requires_grad)
        self.assertIsNone(images.grad)

    def test_zero_auxiliary_weights_leave_enabled_classification_exact(self):
        model = make_model()
        _, _, images, patches = make_inputs()
        classes = torch.tensor([0, 1, 2, 3])
        labels = torch.tensor([0, 1, 2])
        expected = F.cross_entropy(
            model.score_components(images, patches, classes)["final_logits"],
            labels,
        )
        losses = model.training_loss(
            images,
            patches,
            labels,
            classes,
            unique_causal_weight=0.0,
            preserve_weight=0.0,
        )
        self.assertTrue(torch.equal(losses["loss"], expected))
        self.assertTrue(torch.equal(losses["loss"], losses["classification_loss"]))
        self.assertEqual(float(losses["unique_causal_loss"]), 0.0)
        self.assertEqual(float(losses["preservation_loss"]), 0.0)

    def test_rejects_invalid_shapes_roles_and_training_boundary(self):
        sentences, prototypes, images, patches = make_inputs()
        with self.assertRaisesRegex(ValueError, "partition"):
            VCER(
                sentences,
                prototypes,
                14.0,
                local_role_indices=(0, 1, 2, 3, 4, 6),
                global_role_index=6,
                unique_role_index=7,
            )
        with self.assertRaisesRegex(ValueError, "unit-normalized"):
            VCER(sentences, prototypes * 2.0, 14.0)
        model = make_model()
        with self.assertRaisesRegex(ValueError, "patch_features"):
            model.logits(images, patch_features=patches[:, :, :-1])
        with self.assertRaisesRegex(ValueError, "permute"):
            model.score_components(
                images,
                patches,
                role_evidence_permutation=torch.tensor([0, 1, 2, 3, 4, 4]),
            )
        with self.assertRaisesRegex(ValueError, "inside class_ids"):
            model.training_loss(
                images,
                patches,
                torch.tensor([0, 1, 4]),
                torch.tensor([0, 1, 2, 3]),
            )


if __name__ == "__main__":
    unittest.main()
