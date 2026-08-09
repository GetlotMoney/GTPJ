"""V5-INNOVATION-008 的 PSE 类别关系与校准边界测试。"""

import unittest
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import mock

import torch
import torch.nn.functional as F
import yaml

from model import MyModel as model_module
from tools import v5_evaluation
from tools import v5_runtime


def _config(*, mode="legacy_sentence", apply_unseen=False, lambda_cal=0.0):
    return SimpleNamespace(
        num_class=6,
        dim_f_clip=16,
        use_pse_self_attention=True,
        pse_mode=mode,
        pse_apply_unseen=apply_unseen,
        pse_heads=2,
        pse_dropout=0.0,
        pse_inner_ratio=0.35,
        pse_outer_ratio=0.65,
        pse_class_residual_ratio=0.1,
        pse_class_dropout=0.0,
        lambda_self_calibration=lambda_cal,
        tf_common_dim=8,
        tf_heads=2,
        tf_dropout=0.0,
        weight_s2v=0.5,
        local_weight=0.2,
        score_mode="add",
        fgvd_select_k=4,
        fgvd_select_sigma=0.0,
        fgvd_select_largest=True,
        fgvd_select_formula="v2_abs_mean",
        use_fgvd_geometry=True,
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic=True,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        use_icsa=True,
        icsa_ratio=0.008,
        bvsa_text_mode="conditional",
        icsa_hidden=8,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        use_sgmp=True,
        sgmp_context_mode="fgvd_main_memory",
        sgmp_text_mode="conditional",
        sgmp_topk=1,
        sgmp_hidden=8,
        lambda_mpp=0.05,
        lambda_neg=0.01,
        sgmp_neg_margin=0.2,
    )


def _model_inputs():
    torch.manual_seed(20260810)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    seen_sentences = torch.randn(4, 3, 16)
    unseen_text = torch.randn(2, 16)
    return (
        seen,
        unseen,
        seen_sentences.mean(dim=1),
        unseen_text,
        seen_sentences,
    )


class _RecordingClassRelation(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.class_counts = []

    def forward(self, prototypes):
        self.class_counts.append(prototypes.size(0))
        offset = torch.linspace(
            0.01,
            0.02,
            prototypes.size(0),
            device=prototypes.device,
            dtype=prototypes.dtype,
        ).unsqueeze(1)
        return F.normalize(prototypes + offset, dim=-1)


class ClassPrototypeRelationAdapterTest(unittest.TestCase):
    @unittest.skipUnless(torch.cuda.is_available(), "需要 CUDA 验证真实设备边界")
    def test_gtpj_accepts_cuda_class_ids_during_validation(self) -> None:
        seen, unseen, seen_text, unseen_text, seen_sentences = _model_inputs()
        model = model_module.GTPJ(
            _config(),
            seen.cuda(),
            unseen.cuda(),
            seen_text.cuda(),
            unseen_text.cuda(),
            seen_sentences.cuda(),
        )
        self.assertEqual(model.seenclass.device.type, "cuda")

    def test_one_class_change_affects_other_class_outputs(self) -> None:
        self.assertTrue(
            hasattr(model_module, "ClassPrototypeRelationAdapter"),
            "需要实现按 [1, 类别数, 特征维度] 运行的类别关系适配器。",
        )
        adapter = model_module.ClassPrototypeRelationAdapter(
            dim=16,
            heads=2,
            residual_ratio=0.1,
            dropout=0.0,
        ).eval()
        torch.manual_seed(20260810)
        prototypes = torch.randn(4, 16)

        with torch.no_grad():
            before = adapter(prototypes)
            changed = prototypes.clone()
            changed[0] += 5.0
            after = adapter(changed)

        self.assertGreater(float((before[0] - after[0]).abs().max()), 0.0)
        self.assertGreater(
            float((before[1:] - after[1:]).abs().max()),
            0.0,
            "类别 A 改变后，其他类别也必须通过 self-attention 感知到变化。",
        )
        torch.testing.assert_close(
            before.norm(dim=1),
            torch.ones(4),
            rtol=1e-5,
            atol=1e-6,
        )

    def test_gtpj_class_relation_mode_adapts_seen_class_prototypes(self) -> None:
        seen, unseen, seen_text, unseen_text, seen_sentences = _model_inputs()
        model = model_module.GTPJ(
            _config(mode="class_relation"),
            seen,
            unseen,
            seen_text,
            unseen_text,
            seen_sentence_embeds=seen_sentences,
        )
        self.assertTrue(
            hasattr(model, "class_pse_module"),
            "class_relation 模式必须拥有独立的类别关系适配器。",
        )
        adapted = model.get_adapted_seen_text()
        self.assertEqual(tuple(adapted.shape), (seen.numel(), 16))
        torch.testing.assert_close(
            adapted.norm(dim=1),
            torch.ones(seen.numel()),
            rtol=1e-5,
            atol=1e-6,
        )

    def test_shared_weights_process_seen_and_unseen_as_separate_groups(self) -> None:
        seen, unseen, seen_text, unseen_text, seen_sentences = _model_inputs()
        try:
            model = model_module.GTPJ(
                _config(mode="class_relation", apply_unseen=True),
                seen,
                unseen,
                seen_text,
                unseen_text,
                seen_sentence_embeds=seen_sentences,
            )
        except Exception as exc:  # pragma: no cover - 失败信息转成明确断言
            self.fail(f"class_relation 必须允许共享处理 unseen 原型：{exc}")

        recorder = _RecordingClassRelation()
        model.class_pse_module = recorder
        seen_adapted = model.get_adapted_seen_text()
        unseen_adapted = model.get_adapted_unseen_text()

        self.assertEqual(recorder.class_counts, [seen.numel(), unseen.numel()])
        self.assertEqual(tuple(seen_adapted.shape), (seen.numel(), 16))
        self.assertEqual(tuple(unseen_adapted.shape), (unseen.numel(), 16))


class SelfCalibrationLossTest(unittest.TestCase):
    def _model(self):
        seen, unseen, seen_text, unseen_text, seen_sentences = _model_inputs()
        config = _config(
            mode="class_relation",
            apply_unseen=True,
            lambda_cal=0.1,
        )
        config.self_calibration_target = 0.05
        return model_module.GTPJ(
            config,
            seen,
            unseen,
            seen_text,
            unseen_text,
            seen_sentence_embeds=seen_sentences,
        )

    def test_probability_floor_pushes_only_when_unseen_mass_is_too_low(self) -> None:
        model = self._model()
        self.assertTrue(
            hasattr(model, "self_calibration_loss"),
            "需要实现只在 unseen 总概率低于下限时生效的训练校准损失。",
        )
        low_unseen_logits = torch.tensor(
            [[4.0, -4.0, 3.0, 2.0, -5.0, 1.0]],
            requires_grad=True,
        )
        loss = model.self_calibration_loss(low_unseen_logits)
        self.assertGreater(float(loss.detach()), 0.0)
        loss.backward()
        self.assertTrue((low_unseen_logits.grad[0, model.seenclass] > 0).all())
        self.assertTrue((low_unseen_logits.grad[0, model.unseenclass] < 0).all())

        enough_unseen_logits = torch.tensor(
            [[0.0, 4.0, 0.0, 0.0, 4.0, 0.0]],
            requires_grad=True,
        )
        enough_loss = model.self_calibration_loss(enough_unseen_logits)
        torch.testing.assert_close(enough_loss, torch.tensor(0.0))

    def test_compute_loss_keeps_cross_entropy_seen_only_and_adds_calibration(self) -> None:
        model = self._model()
        model.config.lambda_consist = 0.0
        model.config.lambda_topo_pearson = 0.0
        model.config.lambda_mpp = 0.0
        model.config.lambda_neg = 0.0
        model.config.lambda_bmdd = 0.0

        seen_logits = torch.tensor(
            [[2.0, 1.0, 0.0, -1.0], [0.0, 1.0, 2.0, 3.0]],
            requires_grad=True,
        )
        all_logits = torch.tensor(
            [[2.0, -5.0, 1.0, 0.0, -5.0, -1.0],
             [0.0, -4.0, 1.0, 2.0, -4.0, 3.0]],
            requires_grad=True,
        )
        labels = torch.tensor([0, 5])

        losses = model.compute_loss(
            {
                "logits": seen_logits,
                "final_logits": all_logits,
                "batch_label": labels,
            }
        )
        expected_ce = F.cross_entropy(seen_logits, torch.tensor([0, 3]))
        expected_cal = model.self_calibration_loss(all_logits)

        torch.testing.assert_close(losses["loss_ce"], expected_ce)
        torch.testing.assert_close(
            losses["loss"],
            expected_ce + model.lambda_self_calibration * expected_cal,
        )
        torch.testing.assert_close(losses["loss_self_calibration"], expected_cal)


class CalibratedStackingTest(unittest.TestCase):
    def test_gamma_changes_only_seen_logits_without_mutating_input(self) -> None:
        self.assertTrue(
            hasattr(v5_evaluation, "apply_calibrated_stacking"),
            "需要实现只在推理期统一降低 seen logits 的 calibrated stacking。",
        )
        logits = torch.tensor([[4.0, 3.0, 2.0, 1.0]])
        original = logits.clone()
        seenclasses = torch.tensor([0, 2])

        unchanged = v5_evaluation.apply_calibrated_stacking(
            logits, seenclasses, gamma=0.0
        )
        shifted = v5_evaluation.apply_calibrated_stacking(
            logits, seenclasses, gamma=1.25
        )

        torch.testing.assert_close(unchanged, original, rtol=0.0, atol=0.0)
        torch.testing.assert_close(logits, original, rtol=0.0, atol=0.0)
        torch.testing.assert_close(shifted[:, seenclasses], original[:, seenclasses] - 1.25)
        torch.testing.assert_close(shifted[:, torch.tensor([1, 3])], original[:, torch.tensor([1, 3])])

    def test_evaluation_reports_raw_and_shifted_metrics_without_changing_zs(self) -> None:
        class ControlledModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.nclass = 4
                self.register_buffer("seenclass", torch.tensor([0, 2]))
                self.register_buffer("unseenclass", torch.tensor([1, 3]))

            def forward(self, features, is_train=False):
                del is_train
                rows = {
                    0: [10.0, 0.0, 0.0, 0.0],
                    1: [0.0, 0.0, 10.0, 0.0],
                    2: [10.0, 9.0, 0.0, 0.0],
                    3: [0.0, 0.0, 0.0, 10.0],
                }
                return {
                    "clip_S_pp": torch.tensor(
                        [rows[index] for index in features[:, 0, 0].long().tolist()],
                        device=features.device,
                    )
                }

        cache = {
            "seen_cls": torch.tensor([[0.0], [1.0]]),
            "seen_patches": torch.zeros(2, 576, 1),
            "seen_labels": torch.tensor([0, 2]),
            "unseen_cls": torch.tensor([[2.0], [3.0]]),
            "unseen_patches": torch.zeros(2, 576, 1),
            "unseen_labels": torch.tensor([1, 3]),
        }
        raw = v5_evaluation.evaluate_cached_v5(
            ControlledModel(), "cpu", cache, [0, 2], [1, 3], batch_size=2
        )
        shifted = v5_evaluation.evaluate_cached_v5(
            ControlledModel(),
            "cpu",
            cache,
            [0, 2],
            [1, 3],
            batch_size=2,
            calibrated_stacking_gamma=2.0,
        )
        self.assertEqual(raw, (1.0, 0.5, 2.0 / 3.0, 1.0))
        self.assertEqual(shifted, (1.0, 1.0, 1.0, 1.0))
        self.assertEqual(raw[3], shifted[3])

    def test_gamma_is_selected_only_from_validation_labels(self) -> None:
        self.assertTrue(
            hasattr(v5_evaluation, "select_calibrated_stacking_gamma"),
            "gamma 必须由验证划分选择，不能看测试标签。",
        )
        arguments = dict(
            seen_logits=torch.tensor([[2.0, 0.0], [1.0, 0.0]]),
            seen_labels=torch.tensor([0, 0]),
            unseen_logits=torch.tensor([[2.0, 1.0], [1.5, 1.0]]),
            unseen_labels=torch.tensor([1, 1]),
            seenclasses=torch.tensor([0]),
            unseenclasses=torch.tensor([1]),
            gamma_candidates=[0.0, 0.75, 1.1],
        )
        selection = v5_evaluation.select_calibrated_stacking_gamma(
            split_name="validation", **arguments
        )
        self.assertEqual(selection["gamma"], 0.75)
        self.assertAlmostEqual(selection["H"], 2.0 / 3.0)
        with self.assertRaisesRegex(ValueError, "validation"):
            v5_evaluation.select_calibrated_stacking_gamma(
                split_name="test", **arguments
            )


class TrainingEntryIsolationTest(unittest.TestCase):
    def test_batch_order_uses_a_dedicated_checkpointed_generator(self) -> None:
        source = (
            Path(__file__).resolve().parents[1] / "train_GTPJ_CUB.py"
        ).read_text(encoding="utf-8")
        self.assertIn("make_batch_generator", source)
        self.assertIn("generator=batch_generator", source)
        self.assertIn('"batch_generator_state"', source)
        self.assertIn("batch_generator.set_state", source)
        self.assertIn("data_fingerprint_manifest_record", source)
        self.assertIn('"data_fingerprint_manifest"', source)
        self.assertIn("V5_EXPERIMENT_CONFIG_DEFAULTS", source)
        for key in (
            "pse_mode",
            "pse_apply_unseen",
            "pse_class_residual_ratio",
            "pse_class_dropout",
            "lambda_self_calibration",
            "self_calibration_target",
        ):
            self.assertIn(f'"{key}"', source)
        self.assertIn('"--output-dir"', source)
        self.assertIn("FileExistsError", source)
        self.assertIn('"training.log"', source)
        self.assertIn('"model_final.pth"', source)
        self.assertIn('"metrics.yaml"', source)
        loop_start = source.index("for epoch in range(start_epoch, total_epochs + 1):")
        loop_end = source.index("seen_acc, unseen_acc, harmonic, zsl_acc", loop_start)
        self.assertNotIn("evaluate_cached_v5(", source[loop_start:loop_end])
        self.assertIn("evaluation_protocol", source)
        self.assertIn("test_once_after_training", source)

    def test_unchanged_input_reuses_atomic_fingerprint_manifest(self) -> None:
        self.assertTrue(
            hasattr(v5_runtime, "DATA_FINGERPRINT_MANIFEST"),
            "大文件需要项目内的可复用 SHA-256 清单。",
        )
        with tempfile.TemporaryDirectory(prefix="gtpj-fingerprint-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            data_path.write_bytes(b"first-version")
            manifest_path = root / ".runtime" / "data_fingerprints" / "inputs.json"
            original_manifest = v5_runtime.DATA_FINGERPRINT_MANIFEST
            original_hash = v5_runtime.sha256_file
            try:
                v5_runtime.DATA_FINGERPRINT_MANIFEST = manifest_path
                with mock.patch.object(
                    v5_runtime, "sha256_file", side_effect=original_hash
                ) as hash_spy:
                    first = v5_runtime.input_record(data_path)
                    second = v5_runtime.input_record(data_path)
                    self.assertEqual(hash_spy.call_count, 1)
                    self.assertEqual(first["sha256"], second["sha256"])

                    data_path.write_bytes(b"second-version-is-different")
                    third = v5_runtime.input_record(data_path)
                    self.assertEqual(hash_spy.call_count, 2)
                    self.assertNotEqual(second["sha256"], third["sha256"])
                self.assertTrue(manifest_path.is_file())
                self.assertEqual(list(manifest_path.parent.glob("*.tmp")), [])
            finally:
                v5_runtime.DATA_FINGERPRINT_MANIFEST = original_manifest

    def test_resume_checkpoint_must_stay_inside_its_run_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gtpj-resume-") as temporary:
            root = Path(temporary)
            run_a = root / "RUN-A"
            run_b = root / "RUN-B"
            run_a.mkdir()
            run_b.mkdir()
            checkpoint = run_a / "checkpoint_last.pth"
            checkpoint.touch()

            resolved = v5_runtime.validate_resume_output_directory(
                checkpoint, run_a
            )
            self.assertEqual(resolved, checkpoint.resolve())
            with self.assertRaisesRegex(ValueError, "禁止跨 RUN 混写"):
                v5_runtime.validate_resume_output_directory(checkpoint, run_b)


class ExperimentConfigTest(unittest.TestCase):
    def test_e0_to_e3_change_only_the_declared_variables(self) -> None:
        root = (
            Path(__file__).resolve().parents[1]
            / "experiments"
            / "v5"
            / "innovation"
            / "INNOVATION-008_pse_class_relation_calibration"
        )

        def values(path):
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
            return {
                key: value["value"] if isinstance(value, dict) and "value" in value else value
                for key, value in raw.items()
            }

        baseline = values(root / "config.yaml")
        cases = {
            "E1_fix_class_attention.yaml": {"pse_mode"},
            "E2_shared_unseen_pse.yaml": {"pse_mode", "pse_apply_unseen"},
            "E3_training_self_calibration.yaml": {
                "pse_mode",
                "pse_apply_unseen",
                "lambda_self_calibration",
            },
        }
        for name, expected_changes in cases.items():
            with self.subTest(name=name):
                candidate = values(root / "configs" / name)
                actual_changes = {
                    key for key in baseline if candidate[key] != baseline[key]
                }
                self.assertEqual(actual_changes, expected_changes)
                self.assertEqual(candidate["random_seed"], 5)
                self.assertEqual(candidate["lr_stages"], baseline["lr_stages"])

        e4 = yaml.safe_load(
            (root / "configs" / "E4_calibrated_stacking.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertIsNone(e4["gamma"])
        self.assertEqual(e4["gamma_source"], "class_disjoint_validation")
        self.assertFalse(e4["test_tuning_allowed"])


if __name__ == "__main__":
    unittest.main()
