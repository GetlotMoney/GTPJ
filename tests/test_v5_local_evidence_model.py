"""V5 local-evidence rescue model behavior tests."""

from types import SimpleNamespace
from unittest.mock import Mock
import unittest

import torch
import torch.nn.functional as F

from model.MyModel import GTPJ, fgvd_select_patches


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
        icsa_ratio=0.008,
        icsa_hidden=8,
        sgmp_topk=1,
        sgmp_hidden=8,
        sgmp_neg_margin=0.2,
        lambda_consist=0.0,
        consist_temp=2.0,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.0,
        lambda_bmdd=0.0,
        msdn_temp=2.0,
        lambda_mpp=0.0,
        lambda_neg=0.0,
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
        torch.randn(4, 16),
        torch.randn(2, 16),
        seen_sentence_embeds=torch.randn(4, 3, 16),
    )


def make_loss_package(*, requires_grad=False):
    logits = torch.tensor(
        [[0.3, -0.2, 0.1, 0.7], [0.5, 0.4, -0.3, 0.2]],
        dtype=torch.float32,
        requires_grad=requires_grad,
    )
    global_logits = torch.tensor(
        [
            [3.0, -4.0, 9.0, 8.0, -3.0, 10.0],
            [10.0, -4.0, 7.0, 5.0, -3.0, 4.0],
        ],
        dtype=torch.float32,
        requires_grad=requires_grad,
    )
    local_logits = torch.tensor(
        [
            [0.0, -2.0, 0.4, 0.1, -1.0, 0.2],
            [0.6, -2.0, 0.2, 0.7, -1.0, 0.1],
        ],
        dtype=torch.float32,
        requires_grad=requires_grad,
    )
    return {
        "logits": logits,
        "global_logits": global_logits,
        "local_logits": local_logits,
        "batch_label": torch.tensor([5, 0]),
    }


class V5LocalEvidenceModelTest(unittest.TestCase):
    def test_fgvd_bypass_keeps_selection_and_embedding_but_skips_geometry(self):
        model = make_model(
            make_config(ablation_disable_fgvd_geometry=True)
        ).eval()
        features = torch.randn(2, 577, 16)
        geometry_spy = Mock(wraps=model.bvsa_module.geometry_for_indices)
        encoder_spy = Mock(wraps=model.bvsa_module.fgvd_encoder.forward)
        model.bvsa_module.geometry_for_indices = geometry_spy
        model.bvsa_module.fgvd_encoder.forward = encoder_spy

        with torch.no_grad():
            output = model(features, is_train=False)

        geometry_spy.assert_not_called()
        encoder_spy.assert_not_called()
        selected_indices, _ = fgvd_select_patches(
            features[:, 1:, :], K=model.fgvd_select_k
        )
        expanded = selected_indices.unsqueeze(-1).expand(-1, -1, 16)
        expected_patches = torch.gather(features[:, 1:, :], 1, expanded)
        expected_patch_z = model.bvsa_module.embed_cv(expected_patches)
        torch.testing.assert_close(output["sgmp_selected_patches"], expected_patches)
        torch.testing.assert_close(output["sgmp_patch_z"], expected_patch_z)
        torch.testing.assert_close(output["sgmp_memory"], expected_patch_z)

    def test_missing_or_false_fgvd_bypass_keeps_geometry_path(self):
        for config in (
            make_config(),
            make_config(ablation_disable_fgvd_geometry=False),
        ):
            with self.subTest(has_explicit_flag=hasattr(config, "ablation_disable_fgvd_geometry")):
                model = make_model(config).eval()
                geometry_spy = Mock(wraps=model.bvsa_module.geometry_for_indices)
                encoder_spy = Mock(wraps=model.bvsa_module.fgvd_encoder.forward)
                model.bvsa_module.geometry_for_indices = geometry_spy
                model.bvsa_module.fgvd_encoder.forward = encoder_spy
                with torch.no_grad():
                    model(torch.randn(1, 577, 16), is_train=False)
                geometry_spy.assert_called_once()
                encoder_spy.assert_called_once()

    def test_local_ce_uses_global_to_seen_label_mapping(self):
        weight = 0.7
        model = make_model(make_config(lambda_local_ce=weight))
        package = make_loss_package()

        losses = model.compute_loss(package)

        self.assertIn("loss_local_ce", losses)
        expected_local_ce = F.cross_entropy(
            package["local_logits"][:, torch.tensor([0, 2, 3, 5])],
            torch.tensor([3, 0]),
        )
        expected_legacy_ce = F.cross_entropy(
            package["logits"], torch.tensor([3, 0])
        )
        torch.testing.assert_close(losses["loss_local_ce"], expected_local_ce)
        torch.testing.assert_close(
            losses["loss"], expected_legacy_ce + weight * expected_local_ce
        )

    def test_zero_new_weights_preserve_legacy_loss_and_return_zero_terms(self):
        legacy_model = make_model(make_config())
        zero_model = make_model(
            make_config(
                lambda_local_ce=0.0,
                lambda_confusion_contrast=0.0,
                lambda_crop_distill=0.0,
            )
        )
        package = make_loss_package()

        legacy = legacy_model.compute_loss(package)
        zeroed = zero_model.compute_loss(package)

        torch.testing.assert_close(zeroed["loss"], legacy["loss"])
        for key in (
            "loss_local_ce",
            "loss_confusion_contrast",
            "loss_crop_distill",
        ):
            self.assertIn(key, zeroed)
            torch.testing.assert_close(zeroed[key], torch.tensor(0.0))

    def test_confusion_contrast_excludes_truth_and_detaches_global_selector(self):
        weight = 0.6
        margin = 0.3
        model = make_model(
            make_config(
                lambda_confusion_contrast=weight,
                confusion_topk=2,
                confusion_margin=margin,
            )
        )
        package = make_loss_package(requires_grad=True)

        losses = model.compute_loss(package)

        self.assertIn("loss_confusion_contrast", losses)
        # Global hard negatives are seen classes [2, 3] for both rows.  The
        # ground-truth class is deliberately the largest and must be excluded.
        expected = torch.tensor((0.5 + 0.2 + 0.0 + 0.4) / 4.0)
        torch.testing.assert_close(losses["loss_confusion_contrast"], expected)
        losses["loss"].backward()
        self.assertIsNone(package["global_logits"].grad)
        self.assertGreater(
            float(package["local_logits"].grad.abs().sum().item()), 0.0
        )

    def test_crop_distillation_uses_seen_logits_and_detaches_teacher(self):
        weight = 0.4
        temperature = 2.0
        model = make_model(
            make_config(
                lambda_crop_distill=weight,
                crop_distill_temp=temperature,
            )
        )
        package = make_loss_package(requires_grad=True)
        teacher = torch.tensor(
            [
                [0.1, 5.0, 0.8, -0.4, 7.0, 1.2],
                [1.0, 8.0, -0.3, 0.7, 9.0, 0.4],
            ],
            requires_grad=True,
        )
        package["crop_teacher_logits"] = teacher

        losses = model.compute_loss(package)

        self.assertIn("loss_crop_distill", losses)
        seen = torch.tensor([0, 2, 3, 5])
        expected = F.kl_div(
            F.log_softmax(package["local_logits"][:, seen] / temperature, dim=-1),
            F.softmax(teacher[:, seen].detach() / temperature, dim=-1),
            reduction="batchmean",
        ) * (temperature * temperature)
        torch.testing.assert_close(losses["loss_crop_distill"], expected)
        losses["loss"].backward()
        self.assertIsNone(teacher.grad)
        self.assertGreater(
            float(package["local_logits"].grad.abs().sum().item()), 0.0
        )

    def test_crop_distillation_averages_per_view_teacher_probabilities(self):
        temperature = 2.0
        model = make_model(
            make_config(
                lambda_crop_distill=0.4,
                crop_distill_temp=temperature,
            )
        )
        package = make_loss_package(requires_grad=True)
        teacher_views = torch.tensor(
            [
                [
                    [0.1, 5.0, 0.8, -0.4, 7.0, 1.2],
                    [1.0, 8.0, -0.3, 0.7, 9.0, 0.4],
                ],
                [
                    [1.4, 6.0, -0.5, 0.9, 8.0, 0.0],
                    [-0.2, 7.0, 1.1, 0.3, 6.0, 0.8],
                ],
            ],
            requires_grad=True,
        )
        package["crop_teacher_logits"] = teacher_views

        losses = model.compute_loss(package)

        self.assertIn("loss_crop_distill", losses)
        seen = torch.tensor([0, 2, 3, 5])
        expected_probability = F.softmax(
            teacher_views[:, :, seen].detach() / temperature, dim=-1
        ).mean(dim=0)
        expected = F.kl_div(
            F.log_softmax(package["local_logits"][:, seen] / temperature, dim=-1),
            expected_probability,
            reduction="batchmean",
        ) * (temperature * temperature)
        torch.testing.assert_close(losses["loss_crop_distill"], expected)
        losses["loss"].backward()
        self.assertIsNone(teacher_views.grad)

    def test_global_logits_helper_matches_forward_in_eval(self):
        model = make_model().eval()
        features = torch.randn(2, 577, 16)

        self.assertTrue(hasattr(model, "global_logits_from_cls"))
        with torch.no_grad():
            output = model(features, is_train=False)
            helper_logits = model.global_logits_from_cls(features[:, 0, :])

        torch.testing.assert_close(helper_logits, output["global_logits"])


if __name__ == "__main__":
    unittest.main()
