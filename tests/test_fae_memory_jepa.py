"""V5 的 FGVD、ICSA、SGMP 数学路径和梯度测试。

文件名保留历史路径，正文和断言只使用 V5 规范名称。
"""

from types import SimpleNamespace
import unittest

import torch

from model.MyModel import GTPJ


def make_config(
    sgmp_context_mode="fgvd_memory",
    sgmp_text_mode="adapted",
    lambda_mpp=0.05,
    lambda_neg=0.0,
    use_fgvd_geometry=True,
    fgvd_select_k=8,
    use_icsa=False,
    icsa_ratio=0.008,
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
        pse_outer_ratio=0.65,
        tf_common_dim=512,
        tf_heads=4,
        tf_dropout=0.0,
        weight_s2v=0.5,
        use_fgvd_geometry=use_fgvd_geometry,
        local_weight=0.2,
        score_mode="add",
        use_sgmp=True,
        sgmp_context_mode=sgmp_context_mode,
        sgmp_text_mode=sgmp_text_mode,
        sgmp_topk=2,
        sgmp_hidden=512,
        sgmp_neg_margin=0.2,
        fgvd_select_k=fgvd_select_k,
        fgvd_select_sigma=0.0,
        fgvd_select_largest=True,
        fgvd_select_formula="v2_abs_mean",
        use_icsa=use_icsa,
        icsa_ratio=icsa_ratio,
        bvsa_text_mode=bvsa_text_mode,
        icsa_hidden=48,
        lambda_consist=0.0,
        consist_temp=2.0,
        consist_dynamic=True,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.0,
        lambda_bmdd=0.0,
        msdn_temp=2.0,
        lambda_mpp=lambda_mpp,
        lambda_neg=lambda_neg,
    )


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


class FgvdMemorySgmpTest(unittest.TestCase):
    def test_canonical_config_drives_model(self):
        model = make_model(
            make_config(
                "fgvd_main_memory",
                sgmp_text_mode="conditional",
                use_icsa=True,
                bvsa_text_mode="conditional",
                fgvd_select_k=3,
            )
        )

        self.assertTrue(model.use_pse_self_attention)
        self.assertEqual(model.fgvd_select_k, 3)
        self.assertEqual(model.sgmp_context_mode, "fgvd_main_memory")
        self.assertEqual(model.sgmp_text_mode, "conditional")
        self.assertTrue(model.use_icsa)
        self.assertEqual(model.bvsa_text_mode, "conditional")
        self.assertEqual(model.icsa_module[0].out_features, 48)

    def test_missing_canonical_config_key_fails_clearly(self):
        config = make_config()
        del config.sgmp_context_mode

        with self.assertRaisesRegex(AttributeError, "sgmp_context_mode"):
            make_model(config)

    def test_fixed_fusion_uses_point_two_local_weight(self):
        model = make_model(make_config())
        out = model(torch.randn(2, 577, 768), is_train=False)

        expected = out["global_logits"] + 0.2 * out["local_logits"]
        torch.testing.assert_close(out["final_logits"], expected)
        self.assertAlmostEqual(model.local_weight, 0.2)

    def test_fgvd_memory_positive_mpp_reaches_fgvd(self):
        model = make_model(make_config("fgvd_memory", lambda_mpp=0.05, lambda_neg=0.0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_mpp"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(tuple(out["final_logits"].shape), (2, 200))
        self.assertGreater(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.embed_cv.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.embed_text.parameters()), 0.0)
        self.assertGreater(grad_norm(model.pse_module.parameters()), 0.0)

    def test_eval_logits_shape_is_unchanged(self):
        model = make_model(make_config("fgvd_memory"))
        out = model(torch.randn(2, 577, 768), is_train=False)

        self.assertEqual(tuple(out["logits"].shape), (2, 200))
        self.assertEqual(tuple(out["final_logits"].shape), (2, 200))
        self.assertEqual(tuple(out["clip_S_pp"].shape), (2, 200))

    def test_fgvd_memory_requires_geometry(self):
        config = make_config("fgvd_memory", use_fgvd_geometry=False)

        with self.assertRaisesRegex(ValueError, "requires use_fgvd_geometry=True"):
            make_model(config)

    def test_fgvd_memory_supports_full_patch_set(self):
        model = make_model(make_config("fgvd_memory", fgvd_select_k=0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_mpp"].backward()

        self.assertEqual(tuple(out["sgmp_selected_patches"].shape), (2, 576, 768))
        self.assertGreater(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)

    def test_embed_positive_mpp_does_not_reach_fgvd_encoder(self):
        model = make_model(make_config("embed", lambda_mpp=0.05, lambda_neg=0.0))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_mpp"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)

    def test_negative_sgmp_detaches_visual_context(self):
        model = make_model(make_config("fgvd_memory", lambda_mpp=0.0, lambda_neg=0.01))
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_neg"].backward()

        self.assertEqual(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)

    def test_main_memory_conditional_sgmp_reaches_fgvd_and_icsa(self):
        model = make_model(
            make_config(
                "fgvd_main_memory",
                sgmp_text_mode="conditional",
                lambda_mpp=0.05,
                lambda_neg=0.0,
                use_icsa=True,
            )
        )
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_mpp"].backward()

        self.assertEqual(tuple(out["logits"].shape), (2, 150))
        self.assertEqual(tuple(out["final_logits"].shape), (2, 200))
        self.assertEqual(tuple(out["sgmp_memory"].shape), (2, 8, 512))
        self.assertEqual(tuple(out["all_text_cond"].shape), (2, 200, 768))
        self.assertGreater(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)
        self.assertGreater(grad_norm(model.icsa_module.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.embed_text.parameters()), 0.0)

    def test_adapted_bvsa_text_keeps_local_logits_off_icsa(self):
        model = make_model(
            make_config(
                "fgvd_main_memory",
                sgmp_text_mode="conditional",
                lambda_mpp=0.0,
                lambda_neg=0.0,
                use_icsa=True,
                bvsa_text_mode="adapted",
            )
        )
        out = model(torch.randn(2, 577, 768), is_train=True)

        model.zero_grad(set_to_none=True)
        (out["local_logits"] ** 2).sum().backward()

        self.assertEqual(tuple(out["local_logits"].shape), (2, 200))
        self.assertEqual(grad_norm(model.icsa_module.parameters()), 0.0)

    def test_conditional_bvsa_text_reaches_local_logits_and_icsa(self):
        model = make_model(
            make_config(
                "fgvd_main_memory",
                sgmp_text_mode="conditional",
                lambda_mpp=0.0,
                lambda_neg=0.0,
                use_icsa=True,
                bvsa_text_mode="conditional",
            )
        )
        out = model(torch.randn(2, 577, 768), is_train=True)

        model.zero_grad(set_to_none=True)
        (out["local_logits"] ** 2).sum().backward()

        self.assertEqual(tuple(out["all_text_cond"].shape), (2, 200, 768))
        self.assertEqual(tuple(out["score_v2s"].shape), (2, 200))
        self.assertEqual(tuple(out["score_s2v"].shape), (2, 200))
        self.assertEqual(tuple(out["local_logits"].shape), (2, 200))
        self.assertGreater(grad_norm(model.icsa_module.parameters()), 0.0)

    def test_conditional_sgmp_requires_icsa(self):
        with self.assertRaisesRegex(ValueError, "requires use_icsa=True"):
            make_model(
                make_config(
                    "fgvd_main_memory",
                    sgmp_text_mode="conditional",
                    use_icsa=False,
                )
            )

    def test_conditional_bvsa_requires_icsa(self):
        with self.assertRaisesRegex(ValueError, "requires use_icsa=True"):
            make_model(
                make_config(
                    "fgvd_main_memory",
                    use_icsa=False,
                    bvsa_text_mode="conditional",
                )
            )

    def test_conditional_negative_sgmp_detaches_visual_context(self):
        model = make_model(
            make_config(
                "fgvd_main_memory",
                sgmp_text_mode="conditional",
                lambda_mpp=0.0,
                lambda_neg=0.01,
                use_icsa=True,
            )
        )
        clip_features = torch.randn(2, 577, 768)
        labels = torch.tensor([0, 1])

        out = model(clip_features, is_train=True)
        pack = out.copy()
        pack["batch_label"] = labels
        loss_pack = model.compute_loss(pack)

        model.zero_grad(set_to_none=True)
        loss_pack["loss_neg"].backward()

        self.assertEqual(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)
        self.assertGreater(grad_norm(model.icsa_module.parameters()), 0.0)


if __name__ == "__main__":
    unittest.main()
