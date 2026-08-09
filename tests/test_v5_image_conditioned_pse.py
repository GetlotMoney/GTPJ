"""V5-INNOVATION-009 图像条件 PSE 的接口与梯度测试。"""

from types import SimpleNamespace
import unittest

import torch

from model.MyModel import GTPJ


def make_config(**overrides):
    values = dict(
        num_class=6,
        dim_f_clip=16,
        interaction_mode="image_conditioned_pse",
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


def make_model():
    torch.manual_seed(17)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    return GTPJ(
        make_config(),
        seen,
        unseen,
        torch.randn(4, 16),
        torch.randn(2, 16),
        seen_sentence_embeds=torch.randn(4, 8, 16),
        unseen_sentence_embeds=torch.randn(2, 8, 16),
    )


class ImageConditionedPSETest(unittest.TestCase):
    def test_shapes_weights_and_class_axes(self):
        model = make_model().eval()
        features = torch.randn(2, 577, 16)
        with torch.no_grad():
            evaluate = model(features, is_train=False)
            train = model(features, is_train=True)

        self.assertEqual(tuple(evaluate["sentence_weights"].shape), (2, 6, 8))
        self.assertEqual(tuple(evaluate["image_conditioned_text"].shape), (2, 6, 16))
        self.assertEqual(tuple(evaluate["uniform_text"].shape), (6, 16))
        self.assertEqual(tuple(evaluate["local_logits"].shape), (2, 6))
        self.assertEqual(tuple(evaluate["clip_S_pp"].shape), (2, 6))
        self.assertEqual(tuple(train["clip_S_pp"].shape), (2, 4))
        torch.testing.assert_close(
            evaluate["sentence_weights"].sum(dim=-1), torch.ones(2, 6)
        )
        torch.testing.assert_close(
            evaluate["final_logits"],
            evaluate["global_logits"] + 0.2 * evaluate["local_logits"],
        )

    def test_uniform_sentence_average_exactly_recovers_pse_prototype(self):
        model = make_model().eval()
        with torch.no_grad():
            enhanced = model._enhance_sentences(model.seen_sentence_embeds)
            expected = torch.nn.functional.normalize(enhanced.mean(dim=1), dim=-1)
            actual = model.get_adapted_seen_text()
        torch.testing.assert_close(actual, expected)

    def test_local_branch_does_not_depend_on_global_cls(self):
        model = make_model().eval()
        patches = torch.randn(2, 576, 16)
        first = torch.cat([torch.randn(2, 1, 16), patches], dim=1)
        second = torch.cat([torch.randn(2, 1, 16) * 4.0, patches], dim=1)
        with torch.no_grad():
            first_out = model(first)
            second_out = model(second)
        torch.testing.assert_close(first_out["local_logits"], second_out["local_logits"])
        self.assertFalse(
            torch.allclose(first_out["sentence_weights"], second_out["sentence_weights"])
        )

    def test_existing_losses_remain_finite_and_backward_reaches_pse(self):
        model = make_model().train()
        output = model(torch.randn(2, 577, 16), is_train=True)
        losses = model.compute_loss(
            dict(output, batch_label=torch.tensor([0, 3], dtype=torch.long))
        )
        expected_keys = {
            "loss",
            "loss_ce",
            "loss_consist",
            "loss_topo",
            "loss_bmdd",
            "loss_mpp",
            "loss_neg",
        }
        self.assertEqual(set(losses), expected_keys)
        self.assertTrue(all(torch.isfinite(value) for value in losses.values()))
        self.assertIsNone(model.icsa_module)
        losses["loss"].backward()
        self.assertIsNotNone(model.pse_module.proj.weight.grad)
        self.assertGreater(float(model.pse_module.proj.weight.grad.abs().sum()), 0.0)

    def test_active_mode_requires_exactly_eight_sentences_for_seen_and_unseen(self):
        seen = torch.tensor([0, 2, 3, 5])
        unseen = torch.tensor([1, 4])
        with self.assertRaisesRegex(ValueError, r"\[C_seen, 8, D\]"):
            GTPJ(
                make_config(),
                seen,
                unseen,
                torch.randn(4, 16),
                torch.randn(2, 16),
                seen_sentence_embeds=torch.randn(4, 7, 16),
                unseen_sentence_embeds=torch.randn(2, 8, 16),
            )

    def test_topology_keeps_template_seen_pse_and_raw_unseen_input(self):
        model = make_model().eval()
        with torch.no_grad():
            output = model(torch.randn(2, 577, 16))
            expected = model._make_all_text(
                output["topology_text"].device,
                output["topology_text"].dtype,
            )
        torch.testing.assert_close(output["topology_text"], expected)
        self.assertFalse(
            torch.allclose(
                output["topology_text"][model.unseenclass],
                output["uniform_text"][model.unseenclass],
            )
        )

    def test_nonfinite_input_fails_before_training_can_continue(self):
        model = make_model().eval()
        features = torch.randn(1, 577, 16)
        features[0, 0, 0] = float("nan")
        with self.assertRaisesRegex(FloatingPointError, "NaN or Inf"):
            model(features)


if __name__ == "__main__":
    unittest.main()
