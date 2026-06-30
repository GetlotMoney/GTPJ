from types import SimpleNamespace
import unittest

import torch

from model.MyModel import GTPJ


def make_config(
    jepa_context_mode="fae_memory",
    jepa_text_mode="adapted",
    lambda_jepa=0.05,
    lambda_jepa_neg=0.0,
    use_fae=True,
    lastvit_select_k=8,
    use_conditional_text=False,
    conditional_text_ratio=0.008,
    bvsa_text_mode="adapted",
):
    return SimpleNamespace(
        num_class=200,
        dim_f_clip=768,
        pse_adapter_ratio=0.2,
        use_pse_self_attention=True,
        pse_apply_unseen=False,
        pse_heads=4,
        pse_dropout=0.0,
        pse_inner_ratio=0.35,
        pse_outer_ratio=0.15,
        adapter_ratio=0.2,
        use_clip_a_self=True,
        clip_a_self_apply_unseen=False,
        clip_a_self_heads=4,
        clip_a_self_dropout=0.0,
        clip_a_self_inner_ratio=0.35,
        clip_a_self_outer_ratio=0.15,
        tf_common_dim=512,
        tf_heads=4,
        tf_dropout=0.0,
        weight_s2v=0.5,
        use_fae=use_fae,
        use_fgvd_geometry=use_fae,
        local_weight=0.3,
        score_mode="add",
        use_ag_jepa=True,
        use_sgmp=True,
        jepa_context_mode=jepa_context_mode,
        sgmp_context_mode=jepa_context_mode,
        jepa_text_mode=jepa_text_mode,
        sgmp_text_mode=jepa_text_mode,
        jepa_topk=2,
        sgmp_topk=2,
        jepa_hidden=512,
        sgmp_hidden=512,
        jepa_neg_margin=0.2,
        sgmp_neg_margin=0.2,
        lastvit_select_k=lastvit_select_k,
        fgvd_select_k=lastvit_select_k,
        lastvit_select_sigma=0.0,
        fgvd_select_sigma=0.0,
        lastvit_select_largest=True,
        fgvd_select_largest=True,
        lastvit_select_formula="v2_abs_mean",
        fgvd_select_formula="v2_abs_mean",
        use_icsa=use_conditional_text,
        use_conditional_text=use_conditional_text,
        icsa_ratio=conditional_text_ratio,
        conditional_text_ratio=conditional_text_ratio,
        bvsa_text_mode=bvsa_text_mode,
        meta_net_hidden=48,
        icsa_hidden=48,
        lambda_consist=0.0,
        lambda_topo_pearson=0.0,
        lambda_msdn=0.0,
        lambda_bmdd=0.0,
        lambda_jepa=lambda_jepa,
        lambda_mpp=lambda_jepa,
        lambda_jepa_neg=lambda_jepa_neg,
        lambda_neg=lambda_jepa_neg,
    )


def drop_config_keys(config, keys):
    for key in keys:
        if hasattr(config, key):
            delattr(config, key)
    return config


def make_model(config):
    torch.manual_seed(7)
    seen = torch.arange(150)
    unseen = torch.arange(150, 200)
    seen_text = torch.randn(150, 768)
    unseen_text = torch.randn(50, 768)
    seen_sentences = torch.randn(150, 3, 768)
    return GTPJ(
        config,
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )


def grad_norm(parameters):
    total = 0.0
    for param in parameters:
        if param.grad is not None:
            total += float(param.grad.detach().abs().sum().item())
    return total


class FaeMemoryJepaTest(unittest.TestCase):
    def test_framework_only_config_keys_drive_model(self):
        config = make_config(
            "fgvd_main_memory",
            jepa_text_mode="conditional",
            use_conditional_text=True,
            bvsa_text_mode="conditional",
            lastvit_select_k=3,
        )
        drop_config_keys(
            config,
            [
                "adapter_ratio",
                "use_clip_a_self",
                "clip_a_self_apply_unseen",
                "clip_a_self_heads",
                "clip_a_self_dropout",
                "clip_a_self_inner_ratio",
                "clip_a_self_outer_ratio",
                "use_fae",
                "use_ag_jepa",
                "jepa_context_mode",
                "jepa_text_mode",
                "jepa_topk",
                "jepa_hidden",
                "jepa_neg_margin",
                "lastvit_select_k",
                "lastvit_select_sigma",
                "lastvit_select_largest",
                "lastvit_select_formula",
                "use_conditional_text",
                "conditional_text_ratio",
                "meta_net_hidden",
                "lambda_msdn",
                "lambda_jepa",
                "lambda_jepa_neg",
            ],
        )

        model = make_model(config)

        self.assertTrue(model.use_pse_self_attention)
        self.assertEqual(model.fgvd_select_k, 3)
        self.assertEqual(model.sgmp_context_mode, "fgvd_main_memory")
        self.assertEqual(model.sgmp_text_mode, "conditional")
        self.assertTrue(model.use_icsa)
        self.assertEqual(model.bvsa_text_mode, "conditional")

    def test_legacy_only_config_keys_still_work(self):
        config = make_config(
            "fae_main_memory",
            jepa_text_mode="conditional",
            use_conditional_text=True,
            bvsa_text_mode="conditional",
            lastvit_select_k=4,
        )
        drop_config_keys(
            config,
            [
                "pse_adapter_ratio",
                "use_pse_self_attention",
                "pse_apply_unseen",
                "pse_heads",
                "pse_dropout",
                "pse_inner_ratio",
                "pse_outer_ratio",
                "use_fgvd_geometry",
                "use_sgmp",
                "sgmp_context_mode",
                "sgmp_text_mode",
                "sgmp_topk",
                "sgmp_hidden",
                "sgmp_neg_margin",
                "fgvd_select_k",
                "fgvd_select_sigma",
                "fgvd_select_largest",
                "fgvd_select_formula",
                "use_icsa",
                "icsa_ratio",
                "icsa_hidden",
                "lambda_bmdd",
                "lambda_mpp",
                "lambda_neg",
            ],
        )

        model = make_model(config)

        self.assertTrue(model.use_clip_a_self)
        self.assertEqual(model.fgvd_select_k, 4)
        self.assertEqual(model.sgmp_context_mode, "fgvd_main_memory")
        self.assertEqual(model.sgmp_text_mode, "conditional")
        self.assertTrue(model.use_conditional_text)
        self.assertEqual(model.bvsa_text_mode, "conditional")

    def test_framework_keys_take_priority_over_legacy_aliases(self):
        config = make_config(
            "fgvd_main_memory",
            jepa_text_mode="conditional",
            use_conditional_text=True,
            bvsa_text_mode="conditional",
            lastvit_select_k=6,
        )
        config.pse_adapter_ratio = 0.25
        config.adapter_ratio = 0.75
        config.use_pse_self_attention = True
        config.use_clip_a_self = False
        config.use_fgvd_geometry = True
        config.use_fae = False
        config.sgmp_context_mode = "fgvd_main_memory"
        config.jepa_context_mode = "embed"
        config.sgmp_text_mode = "conditional"
        config.jepa_text_mode = "adapted"
        config.fgvd_select_k = 2
        config.lastvit_select_k = 6
        config.use_icsa = True
        config.use_conditional_text = False
        config.icsa_ratio = 0.02
        config.conditional_text_ratio = 0.0
        config.icsa_hidden = 32
        config.meta_net_hidden = 64

        model = make_model(config)

        self.assertAlmostEqual(model.adapter_ratio, 0.25)
        self.assertTrue(model.use_clip_a_self)
        self.assertEqual(model.sgmp_context_mode, "fgvd_main_memory")
        self.assertEqual(model.sgmp_text_mode, "conditional")
        self.assertEqual(model.fgvd_select_k, 2)
        self.assertTrue(model.use_icsa)
        self.assertAlmostEqual(model.icsa_ratio, 0.02)
        self.assertEqual(model.meta_net[0].out_features, 32)

    def test_fae_memory_positive_jepa_reaches_fae(self):
        model = make_model(make_config("fae_memory", lambda_jepa=0.05, lambda_jepa_neg=0.0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_jepa"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(tuple(out["logits_200"].shape), (2, 200))
        self.assertGreater(grad_norm(model.cross_tf.fae.parameters()), 0.0)
        self.assertGreater(grad_norm(model.cross_tf.embed_cv.parameters()), 0.0)
        self.assertGreater(grad_norm(model.cross_tf.embed_text.parameters()), 0.0)
        self.assertGreater(grad_norm(model.clip_a_self_adapter.parameters()), 0.0)

    def test_eval_logits_shape_is_unchanged(self):
        model = make_model(make_config("fae_memory"))
        clip_features = torch.randn(2, 577, 768)

        out = model(clip_features, is_train=False)

        self.assertEqual(tuple(out["logits"].shape), (2, 200))
        self.assertEqual(tuple(out["logits_200"].shape), (2, 200))

    def test_fae_memory_requires_fae(self):
        config = make_config("fae_memory", use_fae=False)

        with self.assertRaisesRegex(ValueError, "requires use_fgvd_geometry=True"):
            make_model(config)

    def test_fae_memory_supports_full_patch_set(self):
        model = make_model(make_config("fae_memory", lastvit_select_k=0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_mpp"].backward()

        self.assertEqual(tuple(out["jepa_selected_patches"].shape), (2, 576, 768))
        self.assertGreater(grad_norm(model.cross_tf.fae.parameters()), 0.0)

    def test_embed_positive_jepa_does_not_reach_fae(self):
        model = make_model(make_config("embed", lambda_jepa=0.05, lambda_jepa_neg=0.0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_jepa"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(grad_norm(model.cross_tf.fae.parameters()), 0.0)

    def test_negative_jepa_detaches_visual_context(self):
        model = make_model(make_config("fae_memory", lambda_jepa=0.0, lambda_jepa_neg=0.01))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_jepa_neg"].backward()

        self.assertEqual(grad_norm(model.cross_tf.fae.parameters()), 0.0)

    def test_fae_main_memory_conditional_jepa_reaches_main_fae_and_meta_net(self):
        model = make_model(
            make_config(
                "fae_main_memory",
                jepa_text_mode="conditional",
                lambda_jepa=0.05,
                lambda_jepa_neg=0.0,
                use_conditional_text=True,
            )
        )
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_jepa"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(tuple(out["logits_200"].shape), (2, 200))
        self.assertEqual(tuple(out["sgmp_memory"].shape), (2, 8, 512))
        self.assertEqual(tuple(out["all_text_cond"].shape), (2, 200, 768))
        self.assertGreater(grad_norm(model.cross_tf.fae.parameters()), 0.0)
        self.assertGreater(grad_norm(model.meta_net.parameters()), 0.0)
        self.assertGreater(grad_norm(model.cross_tf.embed_text.parameters()), 0.0)

    def test_default_bvsa_text_keeps_local_score_off_meta_net(self):
        model = make_model(
            make_config(
                "fae_main_memory",
                jepa_text_mode="conditional",
                lambda_jepa=0.0,
                lambda_jepa_neg=0.0,
                use_conditional_text=True,
                bvsa_text_mode="adapted",
            )
        )
        clip_features = torch.randn(2, 577, 768)

        out = model(clip_features, is_train=True)

        model.zero_grad(set_to_none=True)
        out["local_score"].sum().backward()

        self.assertEqual(tuple(out["local_score"].shape), (2, 200))
        self.assertEqual(grad_norm(model.meta_net.parameters()), 0.0)

    def test_conditional_bvsa_text_reaches_local_score_and_meta_net(self):
        model = make_model(
            make_config(
                "fae_main_memory",
                jepa_text_mode="conditional",
                lambda_jepa=0.0,
                lambda_jepa_neg=0.0,
                use_conditional_text=True,
                bvsa_text_mode="conditional",
            )
        )
        clip_features = torch.randn(2, 577, 768)

        out = model(clip_features, is_train=True)

        model.zero_grad(set_to_none=True)
        out["local_score"].sum().backward()

        self.assertEqual(tuple(out["all_text_cond"].shape), (2, 200, 768))
        self.assertEqual(tuple(out["score_v2s"].shape), (2, 200))
        self.assertEqual(tuple(out["score_s2v"].shape), (2, 200))
        self.assertEqual(tuple(out["local_score"].shape), (2, 200))
        self.assertGreater(grad_norm(model.meta_net.parameters()), 0.0)

    def test_conditional_jepa_requires_conditional_text(self):
        with self.assertRaisesRegex(ValueError, "requires use_icsa=True"):
            make_model(
                make_config(
                    "fae_main_memory",
                    jepa_text_mode="conditional",
                    use_conditional_text=False,
                )
            )

    def test_conditional_bvsa_requires_conditional_text(self):
        with self.assertRaisesRegex(ValueError, "requires use_icsa=True"):
            make_model(
                make_config(
                    "fae_main_memory",
                    use_conditional_text=False,
                    bvsa_text_mode="conditional",
                )
            )

    def test_conditional_negative_jepa_detaches_visual_context(self):
        model = make_model(
            make_config(
                "fae_main_memory",
                jepa_text_mode="conditional",
                lambda_jepa=0.0,
                lambda_jepa_neg=0.01,
                use_conditional_text=True,
            )
        )
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_jepa_neg"].backward()

        self.assertEqual(grad_norm(model.cross_tf.fae.parameters()), 0.0)
        self.assertGreater(grad_norm(model.meta_net.parameters()), 0.0)


if __name__ == "__main__":
    unittest.main()
