"""五组局部互补性实验的共享训练入口契约。"""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml
import torch


ROOT = Path(__file__).resolve().parents[1]
TRAINER_PATH = ROOT / "experiments/v5/local_evidence_runtime/train.py"
SPEC = importlib.util.spec_from_file_location("v5_local_evidence_train", TRAINER_PATH)
TRAINER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRAINER)


def canonical_values():
    raw = yaml.safe_load((ROOT / "experiments/v5/config.yaml").read_text(encoding="utf-8"))
    return {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }


def write_config(root, mode, **overrides):
    experiment_by_mode = {
        "full_baseline": ("V5-CONFIRM-004", "none"),
        "fgvd_off": ("V5-ABLATION-004", "none"),
        "local_ce": ("V5-INNOVATION-004", "IDEA-0006"),
        "confusion_contrast": ("V5-INNOVATION-005", "IDEA-0006"),
        "crop_distill": ("V5-INNOVATION-006", "IDEA-0006"),
    }
    experiment_id, idea_id = experiment_by_mode[mode]
    values = canonical_values()
    values.update(
        experiment_id=experiment_id,
        idea_id=idea_id,
        base_template_id="MODEL-V5-TEMPLATE-V1",
        base_template_tag="model/v5-template-v1",
        base_template_commit="2f5fa5e631ef82658d4bac587cdfd17f3534cb35",
        dataset_split="xlsa17/att_splits.mat",
        evaluation_protocol="standard_gzsl_u_s_h_zs",
        experiment_mode=mode,
        ablation_disable_fgvd_geometry=mode != "full_baseline",
        lambda_local_ce=0.0,
        lambda_confusion_contrast=0.0,
        confusion_topk=5,
        confusion_margin=0.1,
        lambda_crop_distill=0.0,
        crop_distill_temp=2.0,
        crop_teacher_views=0,
    )
    if mode == "local_ce":
        values["lambda_local_ce"] = 0.1
    elif mode == "confusion_contrast":
        values["lambda_local_ce"] = 0.1
        values["lambda_confusion_contrast"] = 0.1
    elif mode == "crop_distill":
        values["lambda_local_ce"] = 0.1
        values["lambda_crop_distill"] = 0.05
        values["crop_teacher_views"] = 2
    values.update(overrides)
    path = Path(root) / f"{mode}.yaml"
    path.write_text(yaml.safe_dump(values, sort_keys=False), encoding="utf-8")
    return path


class V5LocalEvidenceRuntimeTest(unittest.TestCase):
    def test_checked_in_seed5_configs_load_with_expected_modes(self):
        paths = {
            "full_baseline": ROOT / "experiments/v5/confirmation/CONFIRM-004_latest_code_best_framework/configs/RUN-001.yaml",
            "fgvd_off": ROOT / "experiments/v5/ablation/ABLATION-004_fgvd_geometry_effect/configs/RUN-001.yaml",
            "local_ce": ROOT / "experiments/v5/innovation/INNOVATION-004_local_ce_without_fgvd/configs/RUN-001.yaml",
            "confusion_contrast": ROOT / "experiments/v5/innovation/INNOVATION-005_confusion_attribute_contrast/configs/RUN-001.yaml",
            "crop_distill": ROOT / "experiments/v5/innovation/INNOVATION-006_crop_self_distillation/configs/RUN-001.yaml",
        }
        for mode, path in paths.items():
            config, _, _ = TRAINER.load_config(path)
            self.assertEqual(mode, config.experiment_mode)
            self.assertEqual(5, config.random_seed)

    def test_five_training_modes_have_exact_pre_registered_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in (
                "full_baseline",
                "fgvd_off",
                "local_ce",
                "confusion_contrast",
                "crop_distill",
            ):
                config, values, _ = TRAINER.load_config(write_config(tmp, mode))
                self.assertEqual(mode, config.experiment_mode)
                self.assertEqual(
                    mode != "full_baseline",
                    config.ablation_disable_fgvd_geometry,
                )
                self.assertEqual(values["random_seed"], 5)

    def test_full_baseline_disables_every_experimental_switch(self):
        with tempfile.TemporaryDirectory() as tmp:
            config, _, _ = TRAINER.load_config(write_config(tmp, "full_baseline"))
            self.assertFalse(config.ablation_disable_fgvd_geometry)
            self.assertEqual(0.0, config.lambda_local_ce)
            self.assertEqual(0.0, config.lambda_confusion_contrast)
            self.assertEqual(0.0, config.lambda_crop_distill)
            self.assertEqual(0, config.crop_teacher_views)

    def test_parameter_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_config(tmp, "local_ce", lambda_local_ce=0.2)
            with self.assertRaisesRegex(ValueError, "lambda_local_ce"):
                TRAINER.load_config(path)

    def test_seed_17_and_29_are_allowed_without_other_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for seed in (17, 29):
                config, _, _ = TRAINER.load_config(
                    write_config(tmp, "confusion_contrast", random_seed=seed)
                )
                self.assertEqual(seed, config.random_seed)

    def test_crop_cache_is_required_only_for_crop_distillation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache"
            cache.mkdir()
            config = root / "config.yaml"
            config.write_text("x: 1\n", encoding="utf-8")
            common = [
                root / "xlsa17/data/CUB/res101.mat",
                root / "xlsa17/data/CUB/att_splits.mat",
                cache / "CUB_train_features.pt",
                cache / "CUB_train_patch_features.pt",
                cache / "CUB_train_labels.pt",
                cache / "CUB_gpt55_sentence_embeds.pt",
                cache / "CUB_test_seen_features.pt",
                cache / "CUB_test_seen_patch_features.pt",
                cache / "CUB_test_seen_labels.pt",
                cache / "CUB_test_unseen_features.pt",
                cache / "CUB_test_unseen_patch_features.pt",
                cache / "CUB_test_unseen_labels.pt",
            ]
            for path in common:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")

            non_crop = TRAINER.build_input_paths(root, config, "local_ce")
            self.assertNotIn("crop_teacher_cls", non_crop)
            with self.assertRaisesRegex(FileNotFoundError, "CUB_train_features_aug"):
                TRAINER.build_input_paths(root, config, "crop_distill")
            (cache / "CUB_train_features_aug.pt").write_bytes(b"crop")
            (cache / "CUB_train_views.pt").write_bytes(b"2")
            crop = TRAINER.build_input_paths(root, config, "crop_distill")
            self.assertIn("crop_teacher_cls", crop)
            self.assertIn("crop_teacher_views", crop)

    def test_clean_check_is_bound_to_trainer_worktree(self):
        self.assertEqual(ROOT, TRAINER.ROOT)
        self.assertEqual(
            "exp/v5/innovation/local-evidence-rescue",
            TRAINER._run_git(TRAINER.ROOT, "branch", "--show-current"),
        )

    def test_memory_gate_fails_closed_below_14_gib(self):
        with mock.patch.object(
            TRAINER,
            "_available_physical_memory_bytes",
            return_value=13 * 1024**3,
        ):
            with self.assertRaisesRegex(MemoryError, "14"):
                TRAINER.require_available_memory()

    def test_default_hash_manifest_is_in_project_runtime(self):
        path = TRAINER.default_input_manifest_path()
        self.assertEqual("v5_cub_sha256.json", path.name)
        self.assertEqual("data_fingerprints", path.parent.name)
        self.assertEqual(".runtime", path.parent.parent.name)

    def test_identity_packet_records_data_manifest_sha256(self):
        packet = TRAINER._identity_packet(
            "a" * 40,
            {"experiment_id": "V5-CONFIRM-004", "idea_id": "none"},
            "b" * 64,
            {},
            {},
            torch.tensor([0]),
            torch.tensor([1]),
            Path("manifest.json"),
            "c" * 64,
        )
        self.assertEqual("c" * 64, packet["data_manifest_sha256"])
        self.assertTrue(packet["data_manifest_path"].endswith("manifest.json"))

    def test_atomic_write_retries_a_transient_windows_file_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "training.log"
            real_replace = TRAINER.os.replace
            attempts = 0

            def flaky_replace(source, destination):
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise PermissionError(5, "transient Windows file lock")
                return real_replace(source, destination)

            with mock.patch.object(TRAINER.os, "replace", side_effect=flaky_replace):
                TRAINER.atomic_write_text(target, "epoch 25\n")

            self.assertEqual(3, attempts)
            self.assertEqual("epoch 25\n", target.read_text(encoding="utf-8"))
            self.assertEqual([], list(target.parent.glob(".training.log.*.tmp")))

    def test_branch_metrics_use_per_class_gzsl_and_unseen_only_zs(self):
        seen_scores = torch.tensor([[5.0, 1.0, 0.0, 0.0], [4.0, 3.0, 0.0, 0.0]])
        unseen_scores = torch.tensor([[0.0, 0.0, 5.0, 1.0], [4.0, 0.0, 2.0, 3.0]])
        metrics, state = TRAINER.branch_metrics_from_scores(
            seen_scores,
            unseen_scores,
            torch.tensor([0, 1]),
            torch.tensor([2, 3]),
            torch.tensor([0, 1]),
            torch.tensor([2, 3]),
        )
        self.assertEqual({"U": 0.5, "S": 0.5, "H": 0.5, "ZS": 1.0}, metrics)
        self.assertEqual([True, False], state["seen_correct"].tolist())
        self.assertEqual([True, False], state["unseen_correct"].tolist())

    def test_transition_metrics_count_rescue_and_harm_after_prediction(self):
        transitions = TRAINER.transition_metrics(
            torch.tensor([True, False, True, False]),
            torch.tensor([False, True, True, False]),
        )
        self.assertEqual(1, transitions["rescue"])
        self.assertEqual(1, transitions["harm"])
        self.assertEqual(0.25, transitions["rescue_rate"])
        self.assertEqual(0.25, transitions["harm_rate"])


if __name__ == "__main__":
    unittest.main()
