"""V5-TUNE-002 局部融合权重的代码与正式入口契约测试。"""

from __future__ import annotations

import ast
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType, SimpleNamespace
import unittest

import torch
import yaml

from model.MyModel import GTPJ


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
TRAINING_SOURCE = ROOT / "train_GTPJ_CUB.py"
TEMPLATE_CONFIG = ROOT / "config" / "GTPJ_cub_gzsl.yaml"


def make_config(**overrides):
    values = dict(
        dataset="CUB",
        num_class=6,
        dim_f_clip=16,
        device="cuda:0",
        batch_size=2,
        random_seed=5,
        text_source="gpt55",
        pse_heads=2,
        pse_dropout=0.0,
        pse_inner_ratio=0.35,
        pse_outer_ratio=0.65,
        tf_common_dim=8,
        tf_heads=2,
        tf_dropout=0.0,
        weight_s2v=0.5,
        local_weight=0.2,
        fgvd_select_k=4,
        score_mode="add",
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        icsa_ratio=0.008,
        icsa_hidden=8,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        sgmp_topk=1,
        sgmp_hidden=8,
        lambda_mpp=0.05,
        lambda_neg=0.01,
        sgmp_neg_margin=0.2,
        lr_stages=[{"lr": 1e-3, "epochs": 1, "eta_min": 1e-5}],
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def fixture_inputs():
    generator = torch.Generator().manual_seed(20260809)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    seen_text = torch.randn(4, 16, generator=generator)
    unseen_text = torch.randn(2, 16, generator=generator)
    seen_sentences = torch.randn(4, 3, 16, generator=generator)
    features = torch.randn(2, 577, 16, generator=generator)
    labels = torch.tensor([0, 3])
    return seen, unseen, seen_text, unseen_text, seen_sentences, features, labels


def build_model(model_class, local_weight, inputs, **config_overrides):
    seen, unseen, seen_text, unseen_text, seen_sentences, _, _ = inputs
    config_overrides["local_weight"] = local_weight
    return model_class(
        make_config(**config_overrides),
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )


def load_base_model_class():
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{BASE_COMMIT}:model/MyModel.py"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    module = ModuleType("gtpj_v5_local_weight_base_model")
    module.__file__ = f"{BASE_COMMIT}:model/MyModel.py"
    exec(compile(result.stdout, module.__file__, "exec"), module.__dict__)
    return module.GTPJ


def load_training_contract():
    source = TRAINING_SOURCE.read_text(encoding="utf-8")
    prefix, marker, _ = source.partition("\nargs = _parse_args()\n")
    if not marker:
        raise AssertionError("训练入口缺少可隔离的参数解析边界。")
    module = ModuleType("gtpj_v5_local_weight_training_contract")
    module.__file__ = str(TRAINING_SOURCE)
    exec(compile(prefix, str(TRAINING_SOURCE), "exec"), module.__dict__)
    return module


def write_config(path, local_weight, score_mode="add"):
    raw = yaml.safe_load(TEMPLATE_CONFIG.read_text(encoding="utf-8"))
    raw["local_weight"]["value"] = local_weight
    raw["score_mode"]["value"] = score_mode
    path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


class V5LocalWeightModelTest(unittest.TestCase):
    def test_point_one_and_point_three_control_only_the_fusion_coefficient(self):
        inputs = fixture_inputs()
        torch.manual_seed(17)
        try:
            low = build_model(GTPJ, 0.1, inputs)
            high = build_model(GTPJ, 0.3, inputs)
        except ValueError as error:
            self.fail(f"模型应接受范围内权重：{error}")
        high.load_state_dict(low.state_dict(), strict=True)
        low.eval()
        high.eval()
        features = inputs[-2]
        low_output = low(features, is_train=False)
        high_output = high(features, is_train=False)

        torch.testing.assert_close(low_output["global_logits"], high_output["global_logits"])
        torch.testing.assert_close(low_output["local_logits"], high_output["local_logits"])
        torch.testing.assert_close(
            low_output["final_logits"],
            low_output["global_logits"] + 0.1 * low_output["local_logits"],
        )
        torch.testing.assert_close(
            high_output["final_logits"],
            high_output["global_logits"] + 0.3 * high_output["local_logits"],
        )
        torch.testing.assert_close(
            high_output["final_logits"] - low_output["final_logits"],
            0.2 * low_output["local_logits"],
        )

    def test_point_two_is_numerically_equivalent_to_the_exact_base_commit(self):
        inputs = fixture_inputs()
        base_class = load_base_model_class()
        torch.manual_seed(23)
        base = build_model(base_class, 0.2, inputs)
        torch.manual_seed(29)
        candidate = build_model(GTPJ, 0.2, inputs)
        incompatible = candidate.load_state_dict(base.state_dict(), strict=True)
        self.assertEqual([], incompatible.missing_keys)
        self.assertEqual([], incompatible.unexpected_keys)
        base.eval()
        candidate.eval()

        features = inputs[-2]
        labels = inputs[-1]
        base_output = base(features, is_train=True)
        candidate_output = candidate(features, is_train=True)
        self.assertEqual(set(base_output), set(candidate_output))
        for key in base_output:
            torch.testing.assert_close(
                candidate_output[key], base_output[key], rtol=0.0, atol=0.0
            )

        base_losses = base.compute_loss(dict(base_output, batch_label=labels))
        candidate_losses = candidate.compute_loss(
            dict(candidate_output, batch_label=labels)
        )
        self.assertEqual(set(base_losses), set(candidate_losses))
        for key in base_losses:
            torch.testing.assert_close(
                candidate_losses[key], base_losses[key], rtol=0.0, atol=0.0
            )

        base_losses["loss"].backward()
        candidate_losses["loss"].backward()
        base_parameters = dict(base.named_parameters())
        candidate_parameters = dict(candidate.named_parameters())
        self.assertEqual(set(base_parameters), set(candidate_parameters))
        for name, base_parameter in base_parameters.items():
            candidate_gradient = candidate_parameters[name].grad
            base_gradient = base_parameter.grad
            self.assertEqual(base_gradient is None, candidate_gradient is None, name)
            if base_gradient is not None:
                torch.testing.assert_close(
                    candidate_gradient, base_gradient, rtol=0.0, atol=0.0
                )

    def test_model_accepts_closed_interval_and_rejects_nonfinite_or_out_of_range(self):
        inputs = fixture_inputs()
        for value in (0.0, 0.2, 1.0):
            with self.subTest(accepted=value):
                try:
                    model = build_model(GTPJ, value, inputs)
                except ValueError as error:
                    self.fail(f"模型应接受闭区间权重 {value!r}：{error}")
                self.assertEqual(value, model.local_weight)

        for value in (-1e-12, 1.0 + 1e-12, float("nan"), float("inf"), float("-inf")):
            with self.subTest(rejected=value):
                with self.assertRaisesRegex(ValueError, r"finite.*\[0, 1\]"):
                    build_model(GTPJ, value, inputs)

    def test_model_still_requires_add_score_mode(self):
        with self.assertRaisesRegex(ValueError, "score_mode='add'"):
            build_model(GTPJ, 0.1, fixture_inputs(), score_mode="multiply")


class V5LocalWeightTrainingEntryTest(unittest.TestCase):
    def test_formal_entry_accepts_exactly_the_four_frozen_weights(self):
        module = load_training_contract()
        expected = {0.05, 0.10, 0.30, 0.40}
        self.assertEqual(expected, getattr(module, "FORMAL_LOCAL_WEIGHTS", None))
        with tempfile.TemporaryDirectory(prefix="gtpj-local-weight-entry-") as temporary:
            path = Path(temporary) / "config.yaml"
            for value in sorted(expected):
                with self.subTest(value=value):
                    write_config(path, value)
                    try:
                        config, _, _ = module._load_config(path)
                    except ValueError as error:
                        self.fail(f"正式入口应接受冻结权重 {value!r}：{error}")
                    self.assertEqual(value, config.local_weight)
                    self.assertEqual(
                        f"add-local_weight-{value:.2f}", config.score_identity
                    )

    def test_formal_entry_rejects_point_two_and_every_sampled_nonfrozen_weight(self):
        module = load_training_contract()
        with tempfile.TemporaryDirectory(prefix="gtpj-local-weight-entry-") as temporary:
            path = Path(temporary) / "config.yaml"
            for value in (0.0, 0.2, 0.25, 0.5, 1.0, float("nan"), float("inf")):
                with self.subTest(value=value):
                    write_config(path, value)
                    with self.assertRaisesRegex(ValueError, "local_weight"):
                        module._load_config(path)

    def test_formal_entry_keeps_add_score_mode(self):
        module = load_training_contract()
        with tempfile.TemporaryDirectory(prefix="gtpj-local-weight-entry-") as temporary:
            path = Path(temporary) / "config.yaml"
            write_config(path, 0.1, score_mode="multiply")
            with self.assertRaisesRegex(ValueError, "score_mode='add'"):
                module._load_config(path)

    def test_class_identity_split_is_always_constructed_on_cpu(self):
        tree = ast.parse(TRAINING_SOURCE.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_v5_cub_split"
        ]
        self.assertEqual(1, len(calls))
        final_argument = calls[0].args[-1]
        self.assertIsInstance(final_argument, ast.Constant)
        self.assertEqual("cpu", final_argument.value)

    def test_log_identity_contains_score_mode_and_local_weight(self):
        source = TRAINING_SOURCE.read_text(encoding="utf-8")
        self.assertIn(
            'f"training_log_CUB_{config.score_identity}_{current_time}.txt"',
            source,
        )
        self.assertIn('print_log(f"计分身份：{config.score_identity}")', source)


if __name__ == "__main__":
    unittest.main()
