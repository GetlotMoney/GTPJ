"""V5-ABLATION-011 当前母版 global-only 因果消融契约测试。"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
import yaml

from model.MyModel import GTPJ


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "model" / "V5GlobalOnly.py"
ENTRY_PATH = ROOT / "train_V5_ABLATION_011_CUB.py"
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "ablation"
    / "ABLATION-011_current_global_only"
)
CANONICAL_CONFIG = ROOT / "experiments" / "v5" / "config.yaml"


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
        score_path="global_only",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def fixture_inputs():
    generator = torch.Generator().manual_seed(20260809)
    seen = torch.tensor([5, 0, 3, 2])
    unseen = torch.tensor([4, 1])
    sentences = torch.randn(6, 3, 16, generator=generator)
    text = sentences.mean(dim=1)
    cls_features = torch.randn(2, 16, generator=generator)
    patches = torch.randn(2, 576, 16, generator=generator)
    labels = torch.tensor([5, 2])
    return seen, unseen, sentences, text, cls_features, patches, labels


def _load_module(path: Path, name: str, testcase: unittest.TestCase):
    testcase.assertTrue(path.is_file(), f"尚未实现：{path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    testcase.assertIsNotNone(spec)
    testcase.assertIsNotNone(spec.loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unwrap_config(path: Path):
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }


class V5GlobalOnlyModelTest(unittest.TestCase):
    def _module(self):
        return _load_module(MODEL_PATH, "v5_global_only_model_test", self)

    def _models(self):
        module = self._module()
        seen, unseen, sentences, text, _, _, _ = fixture_inputs()
        torch.manual_seed(23)
        donor = GTPJ(
            make_config(),
            seen,
            unseen,
            text[seen],
            text[unseen],
            seen_sentence_embeds=sentences[seen],
        )
        candidate = module.GlobalOnlyGTPJ.from_canonical(donor)
        return donor, candidate

    def test_same_canonical_donor_produces_bit_exact_global_logits(self):
        donor, candidate = self._models()
        _, _, _, _, cls_features, patches, _ = fixture_inputs()
        donor.eval()
        candidate.eval()
        with torch.inference_mode():
            expected = donor(
                torch.cat([cls_features.unsqueeze(1), patches], dim=1),
                is_train=False,
            )["global_logits"]
            candidate_output = candidate(cls_features, is_train=False)
            actual = candidate_output["global_logits"]
        self.assertTrue(torch.equal(actual, expected))
        self.assertTrue(torch.equal(actual, candidate_output["final_logits"]))

    def test_model_keeps_only_pse_icsa_global_score_and_text_topology(self):
        _, candidate = self._models()
        self.assertTrue(hasattr(candidate, "pse_module"))
        self.assertTrue(hasattr(candidate, "icsa_module"))
        self.assertTrue(hasattr(candidate, "logit_scale"))
        for forbidden in ("bvsa_module", "sgmp_predictor", "fgvd_select_k"):
            self.assertFalse(hasattr(candidate, forbidden))
        parameter_names = set(dict(candidate.named_parameters()))
        self.assertFalse(
            any("bvsa" in name.lower() or "sgmp" in name.lower() for name in parameter_names)
        )

        *_, cls_features, _, labels = fixture_inputs()
        output = candidate(cls_features, is_train=True)
        self.assertEqual(
            {"logits", "final_logits", "global_logits", "clip_S_pp"}, set(output)
        )
        losses = candidate.compute_loss(dict(output, batch_label=labels))
        self.assertEqual({"loss", "loss_ce", "loss_topo"}, set(losses))
        torch.testing.assert_close(
            losses["loss"],
            losses["loss_ce"]
            + candidate.config.lambda_topo_pearson * losses["loss_topo"],
        )
        losses["loss"].backward()

    def test_model_rejects_patch_tensor_input(self):
        _, candidate = self._models()
        *_, cls_features, patches, _ = fixture_inputs()
        with self.assertRaisesRegex(ValueError, r"\[B, D\]"):
            candidate(torch.cat([cls_features.unsqueeze(1), patches], dim=1))

    def test_donor_conversion_does_not_shift_the_training_rng_stream(self):
        module = self._module()
        seen, unseen, sentences, text, _, _, _ = fixture_inputs()
        torch.manual_seed(31)
        donor = GTPJ(
            make_config(),
            seen,
            unseen,
            text[seen],
            text[unseen],
            seen_sentence_embeds=sentences[seen],
        )
        expected_state = torch.get_rng_state().clone()
        module.GlobalOnlyGTPJ.from_canonical(donor)
        self.assertTrue(torch.equal(expected_state, torch.get_rng_state()))


class V5GlobalOnlyEntryTest(unittest.TestCase):
    def _entry(self):
        return _load_module(ENTRY_PATH, "v5_global_only_entry_test", self)

    def test_entry_is_import_safe_and_all_four_cli_arguments_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path.cwd()
            try:
                os.chdir(temporary)
                module = self._entry()
                self.assertEqual([], list(Path(temporary).iterdir()))
            finally:
                os.chdir(previous)

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            module._parse_args([])
        for option in (
            "--config",
            "--data-root",
            "--run-dir",
            "--expected-run-commit",
        ):
            self.assertIn(option, stderr.getvalue())

    def test_config_is_canonical_v5_plus_exact_global_only_key(self):
        module = self._entry()
        canonical = _unwrap_config(CANONICAL_CONFIG)
        candidate, values, config_path, config_sha256 = module._load_config(
            EXPERIMENT_DIR / "config.yaml"
        )
        self.assertEqual(hashlib.sha256(config_path.read_bytes()).hexdigest(), config_sha256)
        self.assertEqual(set(canonical) | {"score_path"}, set(values))
        self.assertEqual(canonical, {k: v for k, v in values.items() if k != "score_path"})
        self.assertEqual("global_only", candidate.score_path)

        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "invalid.yaml"
            raw = yaml.safe_load((EXPERIMENT_DIR / "config.yaml").read_text(encoding="utf-8"))
            raw["unexpected"] = {"value": True}
            invalid.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "多出"):
                module._load_config(invalid)

    def test_runtime_uses_cls_only_and_records_input_identity(self):
        module = self._entry()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = module._data_paths(root)
            self.assertFalse(any("patch" in key.lower() for key in paths))
            self.assertFalse(any("patch" in path.name.lower() for path in paths.values()))

            paths["train_cls"].parent.mkdir(parents=True, exist_ok=True)
            train_cls = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
            train_labels = torch.tensor([0, 1])
            torch.save(train_cls, paths["train_cls"])
            torch.save(train_labels, paths["train_labels"])
            loaded_cls, loaded_labels = module._load_training_cache(
                paths, expected_dim=2, torch_module=torch
            )
            self.assertTrue(torch.equal(train_cls, loaded_cls))
            self.assertTrue(torch.equal(train_labels, loaded_labels))

            records = module._record_inputs(
                {"train_cls": paths["train_cls"], "train_labels": paths["train_labels"]},
                {"train_cls": loaded_cls, "train_labels": loaded_labels},
            )
            self.assertEqual([2, 2], records["train_cls"]["shape"])
            self.assertEqual(str(train_cls.dtype), records["train_cls"]["dtype"])
            self.assertEqual(
                hashlib.sha256(paths["train_cls"].read_bytes()).hexdigest(),
                records["train_cls"]["sha256"],
            )

    def test_cuda_clean_commit_and_absent_output_gates_are_explicit(self):
        module = self._entry()
        module._validate_cuda(make_config(), cuda_is_available=True)
        with self.assertRaisesRegex(RuntimeError, "CUDA"):
            module._validate_cuda(make_config(device="cpu"), cuda_is_available=True)
        with self.assertRaisesRegex(RuntimeError, "CUDA"):
            module._validate_cuda(make_config(), cuda_is_available=False)

        commit = "a" * 40
        module._validate_git_state(commit, actual_commit=commit, status_text="")
        with self.assertRaisesRegex(RuntimeError, "不一致"):
            module._validate_git_state(commit, actual_commit="b" * 40, status_text="")
        with self.assertRaisesRegex(RuntimeError, "clean"):
            module._validate_git_state(commit, actual_commit=commit, status_text=" M file.py")

        absent = Path(tempfile.gettempdir()) / "gtpj-never-created-ablation-011"
        module._validate_absent_run_dir(absent)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(FileExistsError, "已存在"):
                module._validate_absent_run_dir(Path(temporary))

    def test_non_finite_values_are_rejected_and_outputs_are_atomic(self):
        module = self._entry()
        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(FloatingPointError, "有限"):
                    module._metric_payload((0.1, 0.2, invalid, 0.3), epoch=1)
        with self.assertRaisesRegex(FloatingPointError, "有限"):
            module._require_finite_tensor("logits", torch.tensor([float("nan")]))

        metrics = module._metric_payload((0.61, 0.52, 0.56, 0.73), epoch=3)
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            logger = module.AtomicLogger(run_dir / "training.log")
            with mock.patch.object(module.os, "replace", wraps=os.replace) as replace:
                logger("hello")
            self.assertEqual(1, replace.call_count)
            self.assertEqual("hello\n", (run_dir / "training.log").read_text(encoding="utf-8"))

            with mock.patch.object(module.os, "replace", wraps=os.replace) as replace:
                module._atomic_write_json(run_dir / "metrics.json", metrics)
                module._atomic_torch_save(
                    run_dir / "model_best.pth", {"weight": torch.tensor([1.0])}
                )
                module._atomic_torch_save(
                    run_dir / "checkpoint_last.pth", {"epoch": 3}
                )
            self.assertEqual(3, replace.call_count)
            for name in (
                "metrics.json",
                "model_best.pth",
                "checkpoint_last.pth",
                "training.log",
            ):
                self.assertTrue((run_dir / name).is_file(), name)
                self.assertFalse((run_dir / f"{name}.tmp").exists(), name)
            json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))

    def test_config_and_source_identity_changes_are_rejected_before_model_build(self):
        module = self._entry()
        self.assertTrue(
            hasattr(module, "_validate_execution_identity"),
            "尚未实现配置与源码的二次身份复核",
        )
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "config.yaml"
            original = b"score_path: global_only\n"
            config_path.write_bytes(original)
            config_sha256 = hashlib.sha256(original).hexdigest()
            source_hashes = {"model/V5GlobalOnly.py": "a" * 64}

            with mock.patch.object(module, "_source_hashes", return_value=source_hashes):
                module._validate_execution_identity(
                    config_path, config_sha256, source_hashes
                )
                config_path.write_bytes(b"score_path: changed\n")
                with self.assertRaisesRegex(RuntimeError, "配置.*变化"):
                    module._validate_execution_identity(
                        config_path, config_sha256, source_hashes
                    )

            config_path.write_bytes(original)
            with mock.patch.object(
                module,
                "_source_hashes",
                return_value={"model/V5GlobalOnly.py": "b" * 64},
            ):
                with self.assertRaisesRegex(RuntimeError, "源码.*变化"):
                    module._validate_execution_identity(
                        config_path, config_sha256, source_hashes
                    )


class V5GlobalOnlyLedgerTest(unittest.TestCase):
    def test_three_seed_five_configs_are_identical_and_matrix_is_planned(self):
        self.assertTrue(EXPERIMENT_DIR.is_dir(), "实验本地目录尚未创建")
        canonical = _unwrap_config(CANONICAL_CONFIG)
        configs = []
        for index in range(1, 4):
            path = EXPERIMENT_DIR / "configs" / f"RUN-{index:03d}.yaml"
            self.assertTrue(path.is_file(), path.name)
            values = _unwrap_config(path)
            self.assertEqual(set(canonical) | {"score_path"}, set(values))
            self.assertEqual(5, values["random_seed"])
            self.assertEqual("global_only", values["score_path"])
            self.assertEqual(canonical, {k: v for k, v in values.items() if k != "score_path"})
            configs.append(values)
        self.assertEqual(configs[0], configs[1])
        self.assertEqual(configs[1], configs[2])

        with (EXPERIMENT_DIR / "PARAMETER_MATRIX.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(["RUN-001", "RUN-002", "RUN-003"], [row["run_id"] for row in rows])
        self.assertEqual(["5", "5", "5"], [row["seed"] for row in rows])
        self.assertEqual(["global_only"] * 3, [row["score_path"] for row in rows])
        self.assertEqual(["planned"] * 3, [row["status"] for row in rows])

    def test_pre_run_directory_contains_no_result_artifacts(self):
        for name in (
            "metrics.json",
            "model_best.pth",
            "checkpoint_last.pth",
            "training.log",
            "result.yaml",
            "result.md",
        ):
            self.assertFalse((EXPERIMENT_DIR / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
