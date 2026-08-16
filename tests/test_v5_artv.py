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
    / "INNOVATION-022_artv"
    / "artv.py"
)
SPEC = importlib.util.spec_from_file_location("v5_artv", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
ARTV = MODULE.AnatomyAnchoredRoleTransportVerifier


class ARTVTest(unittest.TestCase):
    def make_model(self, class_count: int = 12, dim: int = 16):
        generator = torch.Generator().manual_seed(71)
        sentences = F.normalize(torch.randn(class_count, 8, dim, generator=generator), dim=-1)
        prototypes = F.normalize(torch.randn(class_count, dim, generator=generator), dim=-1)
        anchors = F.normalize(torch.randn(6, dim, generator=generator), dim=-1)
        return ARTV(sentences, prototypes.float(), 13.0, anchors), generator

    def test_off_is_bitwise_frozen_x2_and_reads_no_crops(self):
        model, generator = self.make_model()
        images = torch.randn(5, model.feature_dim, generator=generator) * 3.0
        expected = F.normalize(images.float(), dim=-1) @ model.x2_prototypes.T * model.x2_scale
        actual = model.logits(images, artv_enabled=False)
        self.assertTrue(torch.equal(actual, expected))
        self.assertEqual(sum(parameter.numel() for parameter in model.parameters()), 0)

    def test_enabled_path_only_swaps_frozen_top_two_values(self):
        model, generator = self.make_model()
        images = torch.randn(9, model.feature_dim, generator=generator)
        crops = torch.randn(9, 15, model.feature_dim, generator=generator)
        components = model.score_components(images, crops)
        base = components["base_logits"]
        final = components["final_logits"]
        rows = torch.arange(images.shape[0])
        first = components["top_one_positions"]
        second = components["runner_up_positions"]
        certificate = components["certificate"]
        for row in rows.tolist():
            if bool(certificate[row]):
                self.assertEqual(float(final[row, first[row]]), float(base[row, second[row]]))
                self.assertEqual(float(final[row, second[row]]), float(base[row, first[row]]))
            else:
                self.assertTrue(torch.equal(final[row], base[row]))
            mask = torch.ones(model.class_count, dtype=torch.bool)
            mask[first[row]] = False
            mask[second[row]] = False
            self.assertTrue(torch.equal(final[row, mask], base[row, mask]))

    def test_role_shuffle_misaligns_fixed_slots_and_unique_swap_only_reverses_unique(self):
        model, generator = self.make_model()
        images = torch.randn(7, model.feature_dim, generator=generator)
        crops = torch.randn(7, 15, model.feature_dim, generator=generator)
        aligned = model.score_components(images, crops)
        shuffled = model.score_components(
            images, crops, role_description_permutation=torch.tensor([1, 2, 3, 4, 5, 0])
        )
        swapped = model.score_components(images, crops, unique_swap_with_runner_up=True)
        self.assertFalse(torch.equal(aligned["local_evidence"], shuffled["local_evidence"]))
        self.assertTrue(torch.equal(aligned["role_slots"], shuffled["role_slots"]))
        self.assertTrue(torch.equal(aligned["local_evidence"], swapped["local_evidence"]))
        self.assertTrue(torch.equal(aligned["unique_evidence"], -swapped["unique_evidence"]))

    def test_candidate_reordering_is_equivariant(self):
        model, generator = self.make_model()
        images = torch.randn(4, model.feature_dim, generator=generator)
        crops = torch.randn(4, 15, model.feature_dim, generator=generator)
        classes = torch.tensor([0, 2, 4, 6, 8, 10])
        order = torch.tensor([3, 0, 5, 2, 1, 4])
        direct = model.logits(images, classes, crop_features=crops)
        reordered = model.logits(images, classes[order], crop_features=crops)
        inverse = torch.argsort(order)
        self.assertTrue(torch.equal(direct, reordered[:, inverse]))

    def test_exact_runner_up_tie_uses_smallest_global_class_id(self):
        generator = torch.Generator().manual_seed(99)
        sentences = F.normalize(torch.randn(4, 8, 8, generator=generator), dim=-1)
        prototypes = torch.tensor(
            [
                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ],
            dtype=torch.float32,
        )
        anchors = F.normalize(torch.randn(6, 8, generator=generator), dim=-1)
        model = ARTV(sentences, prototypes, 1.0, anchors)
        images = torch.tensor([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        crops = torch.randn(1, 15, 8, generator=generator)
        direct_classes = torch.tensor([0, 1, 2, 3])
        reordered_classes = torch.tensor([3, 2, 0, 1])
        direct = model.score_components(images, crops, direct_classes)
        reordered = model.score_components(images, crops, reordered_classes)
        self.assertEqual(int(direct["top_one_classes"]), 0)
        self.assertEqual(int(direct["runner_up_classes"]), 1)
        self.assertEqual(int(reordered["top_one_classes"]), 0)
        self.assertEqual(int(reordered["runner_up_classes"]), 1)
        inverse = torch.argsort(reordered_classes)
        self.assertTrue(torch.equal(direct["final_logits"], reordered["final_logits"][:, inverse]))

    def test_input_guards(self):
        model, generator = self.make_model()
        images = torch.randn(2, model.feature_dim, generator=generator)
        crops = torch.randn(2, 15, model.feature_dim, generator=generator)
        with self.assertRaisesRegex(ValueError, "requires crop_features"):
            model.logits(images)
        with self.assertRaisesRegex(ValueError, r"\[batch, 15, dim\]"):
            model.logits(images, crop_features=crops[:, :5])
        with self.assertRaisesRegex(ValueError, "permute 0..5"):
            model.logits(
                images,
                crop_features=crops,
                role_description_permutation=torch.tensor([0, 0, 1, 2, 3, 4]),
            )


if __name__ == "__main__":
    unittest.main()
