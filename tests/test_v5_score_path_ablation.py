"""V5-ABLATION-008 的 C/G/L/GL 分数路径契约测试。"""

from __future__ import annotations

import importlib
import importlib.util
import csv
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
import torch.nn as nn
import torch.nn.functional as F
import yaml

from model.MyModel import GTPJ
from model.V5ScorePathAblation import (
    FrozenClipScorer,
    GlobalScoreModel,
    LocalScoreModel,
    build_score_path_model,
)


ROOT = Path(__file__).resolve().parents[1]
ENTRY_PATH = ROOT / "train_V5_ABLATION_008_CUB.py"
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "ablation"
    / "ABLATION-008_clip_global_local_factorial"
)


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
        score_path="full",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def fixture_inputs():
    generator = torch.Generator().manual_seed(20260809)
    seen = torch.tensor([5, 0, 3, 2])
    unseen = torch.tensor([4, 1])
    all_sentences = torch.randn(6, 3, 16, generator=generator)
    all_text = all_sentences.mean(dim=1)
    features = torch.randn(2, 577, 16, generator=generator)
    labels = torch.tensor([5, 2])
    return seen, unseen, all_sentences, all_text, features, labels


def build(path, seed=17):
    seen, unseen, sentences, text, _, _ = fixture_inputs()
    return build_score_path_model(
        path,
        make_config(score_path=path),
        seen,
        unseen,
        seen_text_embeds=text[seen],
        unseen_text_embeds=text[unseen],
        seen_sentence_embeds=sentences[seen],
        initialization_seed=seed,
    )


def canonical(seed=17):
    seen, unseen, sentences, text, _, _ = fixture_inputs()
    torch.manual_seed(seed)
    return GTPJ(
        make_config(score_path="full"),
        seen,
        unseen,
        text[seen],
        text[unseen],
        seen_sentence_embeds=sentences[seen],
    )


def grad_sum(parameters):
    return sum(
        float(parameter.grad.detach().abs().sum())
        for parameter in parameters
        if parameter.grad is not None
    )


class _ZeroIcsa(nn.Module):
    def forward(self, value):
        return torch.zeros_like(value)


class V5ScorePathModelTest(unittest.TestCase):
    def test_class_ids_are_explicitly_detached_to_cpu_long(self):
        source = inspect.getsource(importlib.import_module("model.V5ScorePathAblation")._validated_class_ids)
        self.assertGreaterEqual(source.count(".detach().cpu().long()"), 2)
        seen, unseen, _, text, _, _ = fixture_inputs()
        model = FrozenClipScorer(
            make_config(score_path="frozen_clip"),
            seen.float().requires_grad_(True),
            unseen.float().requires_grad_(True),
            text[seen],
            text[unseen],
        )
        self.assertEqual(torch.device("cpu"), model.seenclass.device)
        self.assertEqual(torch.long, model.seenclass.dtype)
        self.assertFalse(model.seenclass.requires_grad)

    def test_frozen_clip_is_manual_cosine_parameter_free_and_patch_independent(self):
        seen, unseen, sentences, text, features, _ = fixture_inputs()
        model = FrozenClipScorer(
            make_config(score_path="frozen_clip"), seen, unseen, text[seen], text[unseen]
        )
        self.assertEqual([], list(model.parameters()))
        expected_text = F.normalize(text, dim=1)
        expected = F.normalize(features[:, 0, :], dim=1) @ expected_text.T
        actual = model(features, is_train=False)
        torch.testing.assert_close(actual["clip_S_pp"], expected)
        changed = features.clone()
        changed[:, 1:, :] = torch.randn_like(changed[:, 1:, :])
        torch.testing.assert_close(
            actual["clip_S_pp"], model(changed, is_train=False)["clip_S_pp"], rtol=0, atol=0
        )
        with self.assertRaisesRegex(ValueError, "evaluation-only"):
            model(features, is_train=True)

    def test_global_path_has_only_pse_icsa_and_ce_topology(self):
        model = build("global")
        self.assertIsInstance(model, GlobalScoreModel)
        self.assertTrue(hasattr(model, "pse_module"))
        self.assertTrue(hasattr(model, "icsa_module"))
        for forbidden in ("bvsa_module", "sgmp_predictor"):
            self.assertFalse(hasattr(model, forbidden))
        _, _, _, _, features, labels = fixture_inputs()
        features.requires_grad_(True)
        output = model(features, is_train=True)
        losses = model.compute_loss(dict(output, batch_label=labels))
        self.assertEqual({"loss", "loss_ce", "loss_topo"}, set(losses))
        torch.testing.assert_close(
            losses["loss"],
            losses["loss_ce"] + model.config.lambda_topo_pearson * losses["loss_topo"],
        )
        losses["loss"].backward()
        self.assertEqual(0.0, float(features.grad[:, 1:, :].abs().sum()))

    def test_local_path_has_no_global_score_and_uses_patches_and_icsa(self):
        model = build("local")
        self.assertIsInstance(model, LocalScoreModel)
        self.assertFalse(hasattr(model, "logit_scale"))
        _, _, _, _, features, labels = fixture_inputs()
        features.requires_grad_(True)
        output = model(features, is_train=True)
        self.assertNotIn("global_logits", output)
        torch.testing.assert_close(output["final_logits"], output["local_logits"])
        losses = model.compute_loss(dict(output, batch_label=labels))
        self.assertEqual(
            {"loss", "loss_ce", "loss_topo", "loss_bmdd", "loss_mpp", "loss_neg"},
            set(losses),
        )
        self.assertNotIn("loss_consist", losses)
        losses["loss"].backward()
        self.assertGreater(float(features.grad[:, 1:, :].abs().sum()), 0.0)
        self.assertGreater(grad_sum(model.icsa_module.parameters()), 0.0)
        self.assertGreater(grad_sum(model.sgmp_predictor.parameters()), 0.0)

    def test_local_cls_can_affect_score_only_through_icsa(self):
        model = build("local")
        _, _, _, _, features, _ = fixture_inputs()
        model.icsa_module = _ZeroIcsa()
        a = model(features, is_train=False)["clip_S_pp"]
        changed = features.clone()
        changed[:, 0, :] = torch.randn_like(changed[:, 0, :])
        b = model(changed, is_train=False)["clip_S_pp"]
        torch.testing.assert_close(a, b, rtol=0, atol=0)

    def test_full_factory_returns_canonical_class_with_forward_loss_gradient_parity(self):
        reference = canonical()
        candidate = build("full")
        self.assertIs(type(candidate), GTPJ)
        candidate.load_state_dict(reference.state_dict(), strict=True)
        _, _, _, _, features, labels = fixture_inputs()
        reference.eval()
        candidate.eval()
        with torch.no_grad():
            ref_eval = reference(features, is_train=False)
            got_eval = candidate(features, is_train=False)
        for key in ref_eval:
            torch.testing.assert_close(got_eval[key], ref_eval[key])
        reference.train()
        candidate.train()
        torch.manual_seed(29)
        ref_train = reference(features, is_train=True)
        ref_loss = reference.compute_loss(dict(ref_train, batch_label=labels))
        torch.manual_seed(29)
        got_train = candidate(features, is_train=True)
        got_loss = candidate.compute_loss(dict(got_train, batch_label=labels))
        for key in ref_train:
            torch.testing.assert_close(got_train[key], ref_train[key])
        for key in ref_loss:
            torch.testing.assert_close(got_loss[key], ref_loss[key])
        ref_loss["loss"].backward()
        got_loss["loss"].backward()
        for name in (
            "pse_module.proj.weight",
            "bvsa_module.embed_cv.weight",
            "icsa_module.3.weight",
            "sgmp_predictor.0.weight",
        ):
            torch.testing.assert_close(
                dict(candidate.named_parameters())[name].grad,
                dict(reference.named_parameters())[name].grad,
            )

    def test_global_and_local_shared_state_equals_same_seed_canonical_donor(self):
        reference = canonical(seed=23)
        reference_state = reference.state_dict()
        for path in ("global", "local"):
            with self.subTest(path=path):
                candidate = build(path, seed=23)
                for name, value in candidate.state_dict().items():
                    self.assertIn(name, reference_state)
                    self.assertEqual(value.shape, reference_state[name].shape)
                    torch.testing.assert_close(value, reference_state[name], rtol=0, atol=0)

    def test_non_contiguous_class_order_and_label_mapping_are_preserved(self):
        _, _, _, _, features, _ = fixture_inputs()
        for path in ("frozen_clip", "global", "local", "full"):
            with self.subTest(path=path):
                model = build(path)
                if path == "frozen_clip":
                    with self.assertRaisesRegex(ValueError, "evaluation-only"):
                        model(features, is_train=True)
                else:
                    self.assertEqual((2, 4), tuple(model(features, is_train=True)["clip_S_pp"].shape))
                self.assertEqual((2, 6), tuple(model(features, is_train=False)["clip_S_pp"].shape))
        mapped = build("local")._global_to_seen_labels(torch.tensor([5, 0, 3, 2]))
        torch.testing.assert_close(mapped, torch.tensor([0, 1, 2, 3]))


class V5ScorePathEntryTest(unittest.TestCase):
    def _load_entry(self):
        spec = importlib.util.spec_from_file_location("v5_ablation_008_entry", ENTRY_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_entry_is_import_safe_and_has_main(self):
        module = self._load_entry()
        self.assertTrue(callable(module.main))

    def test_entry_requires_data_root_and_output_dir_and_rejects_existing_output(self):
        module = self._load_entry()
        with self.assertRaises(SystemExit):
            module._parse_args(["--config", "x.yaml"])
        parsed = module._parse_args(
            [
                "--config", "x.yaml",
                "--data-root", "data",
                "--data-manifest", "DATA_MANIFEST.json",
                "--output-dir", "output",
                "--expected-run-commit", "a" * 40,
            ]
        )
        self.assertEqual("a" * 40, parsed.expected_run_commit)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "already-there"
            output.mkdir()
            with self.assertRaisesRegex(FileExistsError, "output"):
                module._reserve_output_dir(output)

    def test_git_identity_is_anchored_to_entry_worktree_from_arbitrary_cwd(self):
        module = self._load_entry()
        expected = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path.cwd()
            try:
                os.chdir(temporary)
                self.assertEqual(expected, module._current_run_commit())
                self.assertEqual(expected, module._require_expected_run_commit(expected))
                with self.assertRaisesRegex(RuntimeError, "expected run commit"):
                    module._require_expected_run_commit("0" * 40)
            finally:
                os.chdir(previous)
        completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with mock.patch.object(module.subprocess, "run", return_value=completed) as run:
            module._require_clean_code_tree()
        self.assertEqual(module.REPO_ROOT, run.call_args.kwargs["cwd"])

    def test_cpu_class_axis_is_frozen_before_any_model_construction(self):
        module = self._load_entry()
        eval_source = inspect.getsource(module._eval_only_split)
        train_source = inspect.getsource(module._run_training_path)
        self.assertNotIn(".to(device)", eval_source)
        self.assertNotIn("device", inspect.signature(module._eval_only_split).parameters)
        self.assertIn('test_cache["unseen_labels"], "cpu",', train_source)

    def test_manifest_verification_is_dependency_exact_and_detects_tampering(self):
        module = self._load_entry()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_root = root / "data"
            files = {}
            for key in sorted(module.TRAINED_REQUIRED_DATA_KEYS):
                relative = Path("payload") / f"{key}.bin"
                path = data_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                content = f"verified:{key}".encode("utf-8")
                path.write_bytes(content)
                files[key] = {
                    "relative_path": relative.as_posix(),
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            manifest_path = root / "DATA_MANIFEST.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": module.DATA_MANIFEST_SCHEMA,
                        "dataset": "CUB",
                        "files": files,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            for key in module.TRAINED_REQUIRED_DATA_KEYS - module.FROZEN_REQUIRED_DATA_KEYS:
                (data_root / files[key]["relative_path"]).unlink()
            frozen = module._verify_data_manifest(manifest_path, data_root, "frozen_clip")
            self.assertEqual(
                module.FROZEN_REQUIRED_DATA_KEYS, set(frozen["fingerprints"])
            )
            self.assertEqual(
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                frozen["manifest_sha256"],
            )
            self.assertTrue(all(path.is_absolute() for path in frozen["paths"].values()))
            with self.assertRaises(FileNotFoundError):
                module._verify_data_manifest(manifest_path, data_root, "full")

            victim = next(iter(module.FROZEN_REQUIRED_DATA_KEYS))
            (data_root / files[victim]["relative_path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                module._verify_data_manifest(manifest_path, data_root, "frozen_clip")

    def test_frozen_cls_only_evaluator_does_not_require_patch_cache(self):
        module = self._load_entry()
        config = make_config(score_path="frozen_clip", num_class=2, dim_f_clip=2)
        seen = torch.tensor([0])
        unseen = torch.tensor([1])
        model = FrozenClipScorer(
            config,
            seen,
            unseen,
            torch.tensor([[1.0, 0.0]]),
            torch.tensor([[0.0, 1.0]]),
        )
        cache = {
            "seen_cls": torch.tensor([[1.0, 0.0]]),
            "seen_labels": torch.tensor([0]),
            "unseen_cls": torch.tensor([[0.0, 1.0]]),
            "unseen_labels": torch.tensor([1]),
        }
        self.assertEqual(
            (1.0, 1.0, 1.0, 1.0),
            module._evaluate_frozen_cls_only(
                model, "cpu", cache, seen, unseen, torch, batch_size=1
            ),
        )

    def test_metrics_are_finite_parseable_and_written_atomically(self):
        module = self._load_entry()
        from workflow.gtpj_workflow import parse_training_log_text

        for invalid in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "finite"):
                    module._metric_dict((0.1, 0.2, invalid, 0.3), epoch=1)

        metrics = module._metric_dict((0.61, 0.52, 0.56, 0.73), epoch=3)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            log = module._logger(output)
            module._log_best_results(log, metrics)
            parsed = parse_training_log_text(
                (output / "training.log").read_text(encoding="utf-8"), "unit-test"
            )
            self.assertEqual(
                {"U": "52.00", "S": "61.00", "H": "56.00", "ZS": "73.00", "best_epoch": "3"},
                parsed,
            )
            with mock.patch.object(module.os, "replace", wraps=os.replace) as replace:
                module._write_metrics(output, metrics, {"run_commit": "a" * 40})
            self.assertEqual(1, replace.call_count)
            payload = json.loads((output / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual("fraction_0_to_1", payload["metric_unit"])
            self.assertFalse((output / "metrics.json.tmp").exists())

            checkpoint = output / "best_model.pth"
            with mock.patch.object(module.os, "replace", wraps=os.replace) as replace:
                module._save_best_model_atomic(torch, {"weight": torch.tensor([1.0])}, checkpoint)
            self.assertEqual(1, replace.call_count)
            self.assertTrue(checkpoint.is_file())
            self.assertFalse((output / "best_model.pth.tmp").exists())

    def test_runtime_metadata_uses_run_commit_and_both_executable_hashes(self):
        module = self._load_entry()
        hashes = module._executable_source_sha256()
        self.assertEqual(
            {"model/V5ScorePathAblation.py", "train_V5_ABLATION_008_CUB.py"},
            set(hashes),
        )
        for relative, digest in hashes.items():
            self.assertEqual(
                hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest
            )
        main_source = inspect.getsource(module.main)
        self.assertIn('"run_commit"', main_source)
        self.assertNotIn('"code_commit"', main_source)
        self.assertIn('"data_manifest_sha256"', main_source)
        self.assertIn('"verified_input_fingerprints"', main_source)
        self.assertIn('"seenclass_ids"', main_source)
        self.assertIn('"unseenclass_ids"', main_source)

    def test_frozen_dispatch_never_calls_training_or_optimizer_path(self):
        module = self._load_entry()
        calls = []

        def frozen(*args, **kwargs):
            calls.append("frozen")
            return {"H": 0.0}

        def forbidden(*args, **kwargs):
            raise AssertionError("frozen path touched training/optimizer")

        result = module._dispatch_score_path(
            make_config(score_path="frozen_clip"),
            {},
            Path("data"),
            Path("output"),
            frozen_runner=frozen,
            training_runner=forbidden,
        )
        self.assertEqual({"H": 0.0}, result)
        self.assertEqual(["frozen"], calls)

    def test_config_accepts_exactly_four_score_paths_and_one_extra_key(self):
        module = self._load_entry()
        self.assertEqual(
            {"frozen_clip", "global", "local", "full"}, module.VALID_SCORE_PATHS
        )
        self.assertEqual(
            {"score_path"}, module.V5_ABLATION_008_CONFIG_KEYS - module.V5_TEMPLATE_CONFIG_KEYS
        )


class V5ScorePathLedgerContractTest(unittest.TestCase):
    SETTINGS = {
        "C-FROZEN": (range(1, 5), "frozen_clip"),
        "G-GLOBAL": (range(5, 9), "global"),
        "L-LOCAL-SCORE": (range(9, 13), "local"),
        "GL-FULL": (range(13, 17), "full"),
    }

    def _rows(self):
        with (EXPERIMENT_DIR / "PARAMETER_MATRIX.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            return list(csv.DictReader(stream))

    def _config(self, run_number):
        path = EXPERIMENT_DIR / "configs" / f"RUN-{run_number:03d}.yaml"
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return {
            key: value["value"] if isinstance(value, dict) and "value" in value else value
            for key, value in raw.items()
        }

    def test_pre_run_directory_has_only_required_evidence_files(self):
        required = {
            "DATA_MANIFEST.json",
            "EXPERIMENT.yaml",
            "README.md",
            "implementation.md",
            "SERVER_LAUNCH_PLAN.md",
            "config.yaml",
            "PARAMETER_MATRIX.csv",
            "PARAMETER_MATRIX.md",
        }
        self.assertTrue(EXPERIMENT_DIR.is_dir())
        self.assertTrue(required.issubset({path.name for path in EXPERIMENT_DIR.iterdir()}))
        self.assertTrue((EXPERIMENT_DIR / "evidence" / "README.md").is_file())
        for fabricated in ("manifest.yaml", "result.yaml", "result.md", "quality_check.md"):
            self.assertFalse((EXPERIMENT_DIR / fabricated).exists())

    def test_matrix_has_exactly_sixteen_frozen_rows_in_fixed_setting_order(self):
        rows = self._rows()
        self.assertEqual(16, len(rows))
        self.assertEqual([f"RUN-{index:03d}" for index in range(1, 17)], [row["job_id"] for row in rows])
        expected_pairs = [(5, 1), (5, 2), (17, 1), (17, 2)]
        for group, (indices, score_path) in self.SETTINGS.items():
            selected = [rows[index - 1] for index in indices]
            self.assertEqual([5, 5, 17, 17], [int(row["seed"]) for row in selected])
            self.assertEqual([group] * 4, [row["group"] for row in selected])
            self.assertEqual(["frozen"] * 4, [row["status"] for row in selected])
            self.assertEqual(expected_pairs, [(int(row["seed"]), int(row["name"].rsplit("-", 1)[-1])) for row in selected])
            self.assertTrue(all(score_path in row["changed_parameters"] for row in selected))

    def test_repeat_links_never_cross_setting_or_seed(self):
        rows = self._rows()
        by_id = {row["job_id"]: row for row in rows}
        for row in rows:
            repeat = row["repeat_of"]
            repeat_index = int(row["name"].rsplit("-", 1)[-1])
            if repeat_index == 1:
                self.assertEqual("", repeat)
            else:
                self.assertIn(repeat, by_id)
                source = by_id[repeat]
                self.assertEqual(row["group"], source["group"])
                self.assertEqual(row["seed"], source["seed"])
                self.assertTrue(source["name"].endswith("-1"))

    def test_each_config_only_changes_score_path_and_seed(self):
        template_raw = yaml.safe_load(
            (ROOT / "config" / "GTPJ_cub_gzsl.yaml").read_text(encoding="utf-8")
        )
        template = {
            key: value["value"] if isinstance(value, dict) and "value" in value else value
            for key, value in template_raw.items()
        }
        for group, (indices, score_path) in self.SETTINGS.items():
            for run_number in indices:
                with self.subTest(group=group, run=run_number):
                    candidate = self._config(run_number)
                    self.assertEqual(set(template) | {"score_path"}, set(candidate))
                    self.assertEqual(score_path, candidate.pop("score_path"))
                    seed = candidate.pop("random_seed")
                    expected = dict(template)
                    expected.pop("random_seed")
                    self.assertEqual(expected, candidate)
                    self.assertIn(seed, {5, 17})

    def test_matrix_binds_code_and_actual_config_hashes(self):
        rows = self._rows()
        code_refs = {row["code_ref"] for row in rows}
        self.assertEqual(1, len(code_refs))
        code_ref = next(iter(code_refs))
        self.assertRegex(code_ref, r"^[0-9a-f]{40}$")
        implementation = (EXPERIMENT_DIR / "implementation.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"`{code_ref}`", implementation)
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", code_ref, "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, ancestry.returncode, ancestry.stderr)
        for row in rows:
            config_path = EXPERIMENT_DIR / row["config_snapshot_ref"]
            digest = hashlib.sha256(config_path.read_bytes()).hexdigest()
            self.assertEqual(code_ref, row["code_ref"])
            self.assertEqual(digest, row["config_fingerprint"])
            self.assertEqual("V5-ABLATION-008", row["work_item_id"])

    def test_frozen_runs_are_determinism_checks_not_training_stability(self):
        frozen_rows = self._rows()[:4]
        for row in frozen_rows:
            self.assertEqual("determinism_check_not_training_stability", row["purpose"])

    def test_formal_campaign_gpu_and_review_boundaries_are_frozen(self):
        experiment = yaml.safe_load(
            (EXPERIMENT_DIR / "EXPERIMENT.yaml").read_text(encoding="utf-8")
        )
        self.assertIs(experiment["formal_evidence"], True)
        self.assertIs(experiment["not_confirmation_evidence"], True)
        self.assertEqual("server_detached_role_only", experiment["workflow_mode"])
        self.assertEqual("strict-3", experiment["review_tier"])
        self.assertEqual("review_pending", experiment["implementation_status"])
        launch = (EXPERIMENT_DIR / "SERVER_LAUNCH_PLAN.md").read_text(encoding="utf-8")
        self.assertIn("GPU 1", launch)
        self.assertIn("CAMP-20260809-v5-ablation100", launch)
        self.assertIn("禁止手工正式启动", launch)


if __name__ == "__main__":
    unittest.main()
