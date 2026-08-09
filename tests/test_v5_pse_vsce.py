"""实验 B：PSE + VSCE 的模型行为边界。"""

from types import SimpleNamespace
import unittest

import torch
import torch.nn.functional as F

from model.MyModel import GTPJ


def _config():
    return SimpleNamespace(
        interaction_mode="pse_vsce",
        num_class=6,
        dim_f_clip=16,
        use_pse_self_attention=True,
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
        use_fgvd_geometry=True,
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        sgmp_topk=1,
        sgmp_hidden=8,
        lambda_mpp=0.05,
        lambda_neg=0.01,
        sgmp_neg_margin=0.2,
    )


def _inputs(sentence_count=8):
    torch.manual_seed(20260810)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    sentences = torch.randn(6, sentence_count, 16)
    means = sentences.mean(dim=1)
    return seen, unseen, means[seen], means[unseen], sentences


def _model(sentence_count=8):
    seen, unseen, seen_text, unseen_text, sentences = _inputs(sentence_count)
    return GTPJ(
        _config(),
        seen,
        unseen,
        seen_text,
        unseen_text,
        sentence_embeds=sentences,
    )


class _DoublePSE(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.class_counts = []

    def forward(self, sentences):
        self.class_counts.append(sentences.size(0))
        return 2.0 * sentences


class TestPSEVSCE(unittest.TestCase):
    def test_requires_exactly_eight_sentences_for_every_global_class(self):
        with self.assertRaisesRegex(ValueError, r"\[C, 8, D\]"):
            _model(sentence_count=7)

        config = _config()
        del config.interaction_mode
        seen, unseen, seen_text, unseen_text, sentences = _inputs()
        with self.assertRaisesRegex(ValueError, "interaction_mode='pse_vsce'"):
            GTPJ(
                config,
                seen,
                unseen,
                seen_text,
                unseen_text,
                sentence_embeds=sentences,
            )

    def test_pse_keeps_sentence_axis_and_uniform_path_matches_formula(self):
        _, _, _, _, raw_sentences = _inputs()
        model = _model()
        normalized_raw = F.normalize(raw_sentences, dim=-1)
        torch.testing.assert_close(model.sentence_embeds, normalized_raw)
        recorder = _DoublePSE()
        model.pse_module = recorder

        enhanced = model.get_enhanced_sentences()
        ratio = model.pse_outer_ratio
        expected = ratio * (2.0 * model.sentence_embeds) + (
            1.0 - ratio
        ) * model.sentence_embeds
        torch.testing.assert_close(enhanced, expected)
        torch.testing.assert_close(
            model.get_uniform_text(enhanced),
            F.normalize(expected.mean(dim=1), dim=-1),
        )
        self.assertEqual(recorder.class_counts, [model.nclass])

    def test_topology_keeps_seen_pse_and_unseen_original_class_text(self):
        model = _model().eval()
        enhanced = model.get_enhanced_sentences()
        uniform_pse = model.get_uniform_text(enhanced)
        topology_text = model.get_topology_text(enhanced)
        base_text = model._make_base_text(topology_text.device, topology_text.dtype)

        torch.testing.assert_close(
            topology_text[model.seenclass], uniform_pse[model.seenclass]
        )
        torch.testing.assert_close(
            topology_text[model.unseenclass], base_text[model.unseenclass]
        )
        self.assertEqual(tuple(topology_text.shape), (model.nclass, model.dim_f))

    def test_forward_uses_same_route_for_seen_and_unseen_and_normalizes_weights(self):
        model = _model().eval()
        recorder = _DoublePSE()
        model.pse_module = recorder
        features = torch.randn(2, 577, 16)

        with torch.no_grad():
            output = model(features, is_train=False)
            training_output = model(features, is_train=True)

        self.assertEqual(recorder.class_counts, [model.nclass, model.nclass])
        self.assertEqual(tuple(output["sentence_weights"].shape), (2, 6, 8))
        self.assertEqual(tuple(output["local_region_weights"].shape), (2, 6, 4))
        self.assertEqual(tuple(output["match_table"].shape), (2, 6, 8, 5))
        self.assertEqual(tuple(output["conditioned_prototypes"].shape), (2, 6, 16))
        self.assertEqual(tuple(output["class_local_visual"].shape), (2, 6, 16))
        torch.testing.assert_close(
            output["sentence_weights"].sum(dim=-1), torch.ones(2, 6)
        )
        torch.testing.assert_close(
            output["local_region_weights"].sum(dim=-1), torch.ones(2, 6)
        )
        for name in (
            "sentence_weights",
            "local_region_weights",
            "match_table",
            "conditioned_prototypes",
            "class_local_visual",
            "global_logits",
            "local_logits",
            "final_logits",
        ):
            torch.testing.assert_close(training_output[name], output[name])
        torch.testing.assert_close(
            training_output["logits"], output["final_logits"][:, model.seenclass]
        )

        enhanced = model.get_enhanced_sentences()
        regions = torch.cat(
            [features[:, :1], output["sgmp_selected_patches"]], dim=1
        )
        expected_match = torch.einsum(
            "brd,cmd->bcmr",
            F.normalize(regions, dim=-1),
            F.normalize(enhanced, dim=-1),
        ) * model.logit_scale.exp().clamp(max=100.0)
        torch.testing.assert_close(output["match_table"], expected_match)
        expected_sentence_weights = F.softmax(
            torch.logsumexp(expected_match, dim=-1), dim=-1
        )
        expected_region_weights = F.softmax(
            torch.logsumexp(expected_match, dim=-2)[..., 1:], dim=-1
        )
        torch.testing.assert_close(
            output["sentence_weights"], expected_sentence_weights
        )
        torch.testing.assert_close(
            output["local_region_weights"], expected_region_weights
        )
        expected_raw_match = expected_match / model.logit_scale.exp().clamp(max=100.0)
        torch.testing.assert_close(output["raw_match_table"], expected_raw_match)
        torch.testing.assert_close(
            output["score_s2v"],
            (
                expected_sentence_weights
                * expected_raw_match.mean(dim=-1)
            ).sum(dim=-1),
        )
        torch.testing.assert_close(
            output["score_v2s"],
            (
                expected_region_weights
                * expected_raw_match[..., 1:].mean(dim=-2)
            ).sum(dim=-1),
        )
        self.assertTrue((output["score_s2v"].abs() <= 1.0 + 1e-6).all())
        self.assertTrue((output["score_v2s"].abs() <= 1.0 + 1e-6).all())
        expected_prototypes = F.normalize(
            torch.einsum("bcm,cmd->bcd", expected_sentence_weights, enhanced),
            dim=-1,
        )
        torch.testing.assert_close(
            output["conditioned_prototypes"], expected_prototypes
        )
        self.assertFalse(hasattr(model, "icsa_module"))
        self.assertFalse(hasattr(model, "bvsa_module"))

    def test_scores_keep_class_axis_and_local_score_is_unscaled_cosine(self):
        model = _model().eval()
        features = torch.randn(2, 577, 16)
        with torch.no_grad():
            output = model(features, is_train=False)

        for name in ("global_logits", "local_logits", "final_logits", "clip_S_pp"):
            self.assertEqual(tuple(output[name].shape), (2, 6))
        expected_local = torch.einsum(
            "bcd,bcd->bc",
            F.normalize(output["class_local_visual"], dim=-1),
            F.normalize(output["conditioned_prototypes"], dim=-1),
        )
        torch.testing.assert_close(output["local_logits"], expected_local)
        torch.testing.assert_close(
            output["final_logits"],
            output["global_logits"] + 0.2 * output["local_logits"],
        )
        self.assertEqual(tuple(output["score_s2v"].shape), (2, 6))
        self.assertEqual(tuple(output["score_v2s"].shape), (2, 6))
        self.assertFalse(torch.allclose(output["score_s2v"], output["score_v2s"]))

    def test_all_existing_losses_are_finite_and_backward_reaches_pse_and_vsce(self):
        model = _model().train()
        features = torch.randn(2, 577, 16)
        output = model(features, is_train=True)
        self.assertEqual(tuple(output["logits"].shape), (2, 4))
        self.assertEqual(tuple(output["uniform_text"].shape), (6, 16))
        self.assertEqual(tuple(output["topology_text"].shape), (6, 16))

        observed_topology_inputs = []
        original_topology = model._topology_pearson_loss

        def checked_topology(enh_text=None):
            observed_topology_inputs.append(enh_text.detach().clone())
            return original_topology(enh_text)

        model._topology_pearson_loss = checked_topology
        losses = model.compute_loss(dict(output, batch_label=torch.tensor([0, 3])))
        self.assertEqual(
            set(losses),
            {
                "loss",
                "loss_ce",
                "loss_consist",
                "loss_topo",
                "loss_bmdd",
                "loss_mpp",
                "loss_neg",
            },
        )
        self.assertEqual(len(observed_topology_inputs), 1)
        torch.testing.assert_close(
            observed_topology_inputs[0], output["topology_text"]
        )
        for value in losses.values():
            self.assertTrue(torch.isfinite(value).item())

        losses["loss"].backward()
        self.assertIsNotNone(model.pse_module.proj.weight.grad)
        self.assertGreater(float(model.pse_module.proj.weight.grad.abs().sum()), 0.0)
        self.assertIsNotNone(model.vsce_module.embed_cv.weight.grad)
        self.assertGreater(float(model.vsce_module.embed_cv.weight.grad.abs().sum()), 0.0)

    def test_nonfinite_match_logits_and_total_loss_fail_fast(self):
        model = _model().eval()
        features = torch.randn(2, 577, 16)
        features[0, 0, 0] = float("nan")
        with self.assertRaisesRegex(FloatingPointError, "raw_match_table"):
            model(features, is_train=False)

        clean_output = model(torch.randn(2, 577, 16), is_train=True)
        clean_output["logits"] = clean_output["logits"].clone()
        clean_output["logits"][0, 0] = float("nan")
        with self.assertRaisesRegex(FloatingPointError, "total_loss"):
            model.compute_loss(
                dict(clean_output, batch_label=torch.tensor([0, 3]))
            )


if __name__ == "__main__":
    unittest.main()
