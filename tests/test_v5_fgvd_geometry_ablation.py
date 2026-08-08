"""V5 FGVD 几何编码旁路的行为契约。"""

from types import SimpleNamespace
from pathlib import Path
import unittest
from unittest import mock

import torch

from model.MyModel import GTPJ, fgvd_select_patches


ROOT = Path(__file__).resolve().parents[1]


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


if __name__ == "__main__":
    unittest.main()
