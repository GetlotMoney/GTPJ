"""冻结的 MODEL-V5-TEMPLATE-V2 数学路径兼容性测试。

当前 canonical 框架是历史 ``v5`` commit 本身；这些测试继续守护另一份只读
干净母版，不能因 TEMPLATE.yaml 改指 canonical 框架而静默改变被测模型。
"""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import torch


ROOT = Path(__file__).resolve().parents[1]
LEGACY_V5_TEMPLATE_TAG = "model/v5-template-v2"
LEGACY_V5_TEMPLATE_COMMIT = "fb4b29b04087640890a532f105cb527d3a8c461b"


def _load_frozen_v5_model_class():
    tag_result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", f"{LEGACY_V5_TEMPLATE_TAG}^{{commit}}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if tag_result.stdout.strip() != LEGACY_V5_TEMPLATE_COMMIT:
        raise AssertionError("只读 MODEL-V5-TEMPLATE-V2 Tag 被移动")
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{LEGACY_V5_TEMPLATE_COMMIT}:model/MyModel.py",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    with tempfile.TemporaryDirectory(prefix="gtpj-v5-math-") as temporary:
        source_path = Path(temporary) / "active_v5_model.py"
        source_path.write_text(result.stdout, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("gtpj_v5_math_model", source_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.GTPJ


GTPJ = _load_frozen_v5_model_class()


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


def make_model(config=None, seen=None, unseen=None):
    torch.manual_seed(7)
    seen = torch.tensor([0, 2, 3, 5]) if seen is None else torch.as_tensor(seen)
    unseen = torch.tensor([1, 4]) if unseen is None else torch.as_tensor(unseen)
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


class V5FrozenTemplateMathPathTest(unittest.TestCase):
    def test_fixed_fusion_uses_point_two_local_weight(self):
        model = make_model()
        out = model(torch.randn(2, 577, 16), is_train=False)

        expected = out["global_logits"] + 0.2 * out["local_logits"]
        torch.testing.assert_close(out["final_logits"], expected)
        self.assertEqual(model.local_weight, 0.2)

    def test_noncanonical_local_weight_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "local_weight=0.2"):
            make_model(make_config(local_weight=0.3))

    def test_known_noncanonical_route_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "use_sgmp=True"):
            make_model(make_config(use_sgmp=False))

    def test_only_577_token_input_is_accepted(self):
        model = make_model()
        for invalid in (
            torch.randn(2, 576, 16),
            torch.randn(2, 1, 16),
            torch.randn(2, 16),
        ):
            with self.subTest(shape=tuple(invalid.shape)):
                with self.assertRaisesRegex(ValueError, r"\[B, 577, D\]"):
                    model(invalid)

    def test_feature_dimension_is_checked(self):
        with self.assertRaisesRegex(ValueError, "D=16"):
            make_model()(torch.randn(2, 577, 15))

    def test_train_and_eval_class_axes(self):
        model = make_model()
        features = torch.randn(2, 577, 16)

        train = model(features, is_train=True)
        evaluate = model(features, is_train=False)

        self.assertEqual(tuple(train["clip_S_pp"].shape), (2, 4))
        self.assertEqual(tuple(evaluate["clip_S_pp"].shape), (2, 6))

    def test_mpp_reaches_fgvd_icsa_and_text_alignment(self):
        model = make_model()
        out = model(torch.randn(2, 577, 16), is_train=True)
        losses = model.compute_loss(dict(out, batch_label=torch.tensor([0, 3])))

        model.zero_grad(set_to_none=True)
        losses["loss_mpp"].backward()

        self.assertEqual(tuple(out["sgmp_memory"].shape), (2, 4, 8))
        self.assertGreater(grad_norm(model.bvsa_module.fgvd_encoder.parameters()), 0.0)
        self.assertGreater(grad_norm(model.icsa_module.parameters()), 0.0)
        self.assertGreater(grad_norm(model.bvsa_module.embed_text.parameters()), 0.0)

    def test_local_logits_reach_icsa(self):
        model = make_model()
        out = model(torch.randn(2, 577, 16), is_train=True)

        model.zero_grad(set_to_none=True)
        out["local_logits"].square().sum().backward()

        self.assertEqual(tuple(out["local_logits"].shape), (2, 6))
        self.assertGreater(grad_norm(model.icsa_module.parameters()), 0.0)

    def test_global_seen_labels_map_by_declared_class_order(self):
        model = make_model()
        mapped = model._global_to_seen_labels(torch.tensor([5, 0, 3, 2]))
        torch.testing.assert_close(mapped, torch.tensor([3, 0, 2, 1]))

        with self.assertRaisesRegex(ValueError, "seen classes"):
            model._global_to_seen_labels(torch.tensor([1]))

    def test_class_split_must_be_disjoint_unique_and_complete(self):
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            make_model(seen=[0, 2, 3, 5], unseen=[1, 5])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            make_model(seen=[0, 0, 2, 3], unseen=[1, 4])
        with self.assertRaisesRegex(ValueError, "cover every global class"):
            make_model(seen=[0, 2, 3], unseen=[1, 4])


if __name__ == "__main__":
    unittest.main()
