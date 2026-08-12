"""V5-INNOVATION-011 的最小模型与训练合同测试。"""

import importlib.util
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
import yaml

from model.MyModel import (
    EXPECTED_PATCH_COUNT,
    GLOBAL_SENTENCE_INDEX,
    LOCAL_SENTENCE_COUNT,
    UNIQUE_SENTENCE_INDEX,
    SENTENCE_ROLES,
    GTPJ,
)
from tools.v5_evaluation import evaluate_cached_v5


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiments/v5/innovation/INNOVATION-011_clean_v6_candidate/config.yaml"
MODEL_PATH = ROOT / "model/MyModel.py"
TRAIN_PATH = ROOT / "train_GTPJ_CUB.py"
OLD_MODULE_TOKENS = {
    "ProgressiveSemanticSelfAttention",
    "fgvd_select_patches",
    "BidirectionalVisualSemanticAlignment",
    "GeometryMultiHeadAttention",
    "icsa_module",
    "sgmp_predictor",
    "loss_topo",
    "loss_bmdd",
    "loss_mpp",
    "loss_neg",
    "lambda_consist",
}


def make_config(**overrides):
    values = dict(num_class=5, dim_f_clip=4, region_temperature=0.2)
    values.update(overrides)
    return SimpleNamespace(**values)


def make_model():
    torch.manual_seed(7)
    return GTPJ(
        make_config(),
        seenclass=torch.tensor([0, 2, 4]),
        unseenclass=torch.tensor([1, 3]),
        sentence_embeds=torch.randn(5, 8, 4),
    )


class CleanInnovation011Test(unittest.TestCase):
    def test_sentence_role_order_is_fixed(self):
        self.assertEqual(
            (
                "beak",
                "head_features",
                "body_plumage",
                "wings",
                "tail",
                "legs",
                "overall_appearance",
                "unique_discriminative_features",
            ),
            SENTENCE_ROLES,
        )
        self.assertEqual(6, LOCAL_SENTENCE_COUNT)
        self.assertEqual(6, GLOBAL_SENTENCE_INDEX)
        self.assertEqual(7, UNIQUE_SENTENCE_INDEX)

    def test_sentence_shape_and_class_partition_are_strict(self):
        with self.assertRaisesRegex(ValueError, "strict|严格|sentence_embeds"):
            GTPJ(
                make_config(),
                torch.tensor([0, 2, 4]),
                torch.tensor([1, 3]),
                torch.randn(5, 7, 4),
            )
        with self.assertRaisesRegex(ValueError, "覆盖|cover"):
            GTPJ(
                make_config(),
                torch.tensor([0, 2]),
                torch.tensor([1, 3]),
                torch.randn(5, 8, 4),
            )

    def test_projection_starts_as_identity(self):
        model = make_model()
        self.assertTrue(
            torch.equal(model.shared_projection.weight, torch.eye(model.dim_f))
        )

    def test_train_and_eval_shapes_and_aliases(self):
        model = make_model()
        features = torch.randn(2, EXPECTED_PATCH_COUNT + 1, 4)
        train_output = model(features, is_train=True)
        eval_output = model(features, is_train=False)
        self.assertEqual((2, 3), tuple(train_output["logits"].shape))
        self.assertEqual((2, 5), tuple(eval_output["logits"].shape))
        self.assertIs(train_output["logits"], train_output["final_logits"])
        self.assertIs(train_output["logits"], train_output["clip_S_pp"])
        for key in ("local_logits", "unique_logits", "global_logits"):
            self.assertEqual((2, 3), tuple(train_output[key].shape))

    def test_each_sentence_role_only_changes_its_own_score(self):
        model = make_model().eval()
        features = torch.randn(2, EXPECTED_PATCH_COUNT + 1, 4)
        baseline = model(features)
        with torch.no_grad():
            model.sentence_embeds[:, 0].add_(torch.tensor([3.0, 0.0, 0.0, 0.0]))
        local_changed = model(features)
        self.assertFalse(torch.allclose(baseline["local_logits"], local_changed["local_logits"]))
        self.assertTrue(torch.allclose(baseline["unique_logits"], local_changed["unique_logits"]))
        self.assertTrue(torch.allclose(baseline["global_logits"], local_changed["global_logits"]))

        with torch.no_grad():
            model.sentence_embeds[:, UNIQUE_SENTENCE_INDEX].add_(
                torch.tensor([0.0, 3.0, 0.0, 0.0])
            )
        unique_changed = model(features)
        self.assertTrue(torch.allclose(local_changed["local_logits"], unique_changed["local_logits"]))
        self.assertFalse(torch.allclose(local_changed["unique_logits"], unique_changed["unique_logits"]))
        self.assertTrue(torch.allclose(local_changed["global_logits"], unique_changed["global_logits"]))

        with torch.no_grad():
            model.sentence_embeds[:, GLOBAL_SENTENCE_INDEX].add_(
                torch.tensor([0.0, 0.0, 3.0, 0.0])
            )
        global_changed = model(features)
        self.assertTrue(torch.allclose(unique_changed["local_logits"], global_changed["local_logits"]))
        self.assertTrue(torch.allclose(unique_changed["unique_logits"], global_changed["unique_logits"]))
        self.assertFalse(torch.allclose(unique_changed["global_logits"], global_changed["global_logits"]))

    def test_all_576_regions_participate_without_topk(self):
        model = make_model().eval()
        features = torch.randn(1, EXPECTED_PATCH_COUNT + 1, 4)
        baseline = model(features)
        changed = features.clone()
        changed[:, -1] += torch.tensor([8.0, -3.0, 2.0, 1.0])
        output = model(changed)
        self.assertFalse(torch.allclose(baseline["local_logits"], output["local_logits"]))
        self.assertFalse(torch.allclose(baseline["unique_logits"], output["unique_logits"]))
        self.assertTrue(torch.allclose(baseline["global_logits"], output["global_logits"]))

    def test_only_ce_loss_and_gradient_reaches_shared_projection(self):
        model = make_model()
        output = model(torch.randn(2, EXPECTED_PATCH_COUNT + 1, 4), is_train=True)
        losses = model.compute_loss(
            dict(output, batch_label=torch.tensor([0, 4]))
        )
        self.assertEqual({"loss", "loss_ce"}, set(losses))
        self.assertIs(losses["loss"], losses["loss_ce"])
        losses["loss"].backward()
        self.assertIsNotNone(model.shared_projection.weight.grad)
        self.assertGreater(float(model.shared_projection.weight.grad.abs().sum()), 0.0)

    def test_checkpoint_roundtrip_preserves_outputs(self):
        model = make_model().eval()
        features = torch.randn(2, EXPECTED_PATCH_COUNT + 1, 4)
        expected = model(features)["clip_S_pp"]
        restored = make_model().eval()
        restored.load_state_dict(model.state_dict(), strict=True)
        actual = restored(features)["clip_S_pp"]
        self.assertTrue(torch.equal(expected, actual))

    def test_cpu_evaluation_uses_global_class_order(self):
        model = make_model().eval()
        cache = {
            "seen_cls": torch.randn(3, 4),
            "seen_patches": torch.randn(3, EXPECTED_PATCH_COUNT, 4),
            "seen_labels": torch.tensor([0, 2, 4]),
            "unseen_cls": torch.randn(2, 4),
            "unseen_patches": torch.randn(2, EXPECTED_PATCH_COUNT, 4),
            "unseen_labels": torch.tensor([1, 3]),
        }
        metrics = evaluate_cached_v5(
            model,
            "cpu",
            cache,
            torch.tensor([0, 2, 4]),
            torch.tensor([1, 3]),
            batch_size=2,
        )
        self.assertEqual(4, len(metrics))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in metrics))

    def test_config_rejects_old_fields_and_source_has_no_old_paths(self):
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "dataset",
                "num_class",
                "dim_f_clip",
                "device",
                "batch_size",
                "random_seed",
                "region_temperature",
                "lr_stages",
            },
            set(raw),
        )
        source = MODEL_PATH.read_text(encoding="utf-8") + TRAIN_PATH.read_text(encoding="utf-8")
        for token in OLD_MODULE_TOKENS:
            self.assertNotIn(token, source)
        self.assertNotRegex(source.lower(), r"topk\s*\(")

    def test_training_config_parser_rejects_a_legacy_module_field(self):
        source = TRAIN_PATH.read_text(encoding="utf-8").split("args = _parse_args()", 1)[0]
        spec = importlib.util.spec_from_loader("innovation_011_train_config", loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(compile(source, str(TRAIN_PATH), "exec"), module.__dict__)
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["fgvd_select_k"] = {"value": 32}
        temporary = ROOT / ".runtime" / "test_innovation_011_bad_config.yaml"
        temporary.parent.mkdir(parents=True, exist_ok=True)
        try:
            temporary.write_text(yaml.safe_dump(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "多出"):
                module._load_config(temporary)
        finally:
            temporary.unlink(missing_ok=True)

    def test_training_requires_a_new_run_output_directory(self):
        source = TRAIN_PATH.read_text(encoding="utf-8").split("args = _parse_args()", 1)[0]
        spec = importlib.util.spec_from_loader("innovation_011_output_dir", loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(compile(source, str(TRAIN_PATH), "exec"), module.__dict__)

        with mock.patch("sys.argv", ["train_GTPJ_CUB.py", "--config", str(CONFIG_PATH)]):
            with self.assertRaises(SystemExit):
                module._parse_args()

        with tempfile.TemporaryDirectory() as temporary_dir:
            existing = Path(temporary_dir)
            with self.assertRaisesRegex(FileExistsError, "输出目录已存在"):
                module._prepare_output_dir(existing)

    def test_first_zero_h_evaluation_is_still_saved(self):
        source = TRAIN_PATH.read_text(encoding="utf-8").split("args = _parse_args()", 1)[0]
        spec = importlib.util.spec_from_loader("innovation_011_best_save", loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(compile(source, str(TRAIN_PATH), "exec"), module.__dict__)

        self.assertTrue(module._should_save_best(0.0, 0.0, {"epoch": 0}))
        self.assertFalse(module._should_save_best(0.0, 0.0, {"epoch": 1}))
        self.assertTrue(module._should_save_best(0.1, 0.0, {"epoch": 1}))

    def test_training_schedule_is_locked_to_fifty_epochs(self):
        source = TRAIN_PATH.read_text(encoding="utf-8").split("args = _parse_args()", 1)[0]
        spec = importlib.util.spec_from_loader("innovation_011_schedule", loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(compile(source, str(TRAIN_PATH), "exec"), module.__dict__)
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        raw["lr_stages"]["value"][0]["epochs"] = 19
        temporary = ROOT / ".runtime" / "test_innovation_011_bad_schedule.yaml"
        temporary.parent.mkdir(parents=True, exist_ok=True)
        try:
            temporary.write_text(yaml.safe_dump(raw), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "总 epoch 必须等于 50"):
                module._load_config(temporary)
        finally:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
