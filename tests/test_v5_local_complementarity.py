import ast
import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import torch


class LocalComplementarityTests(unittest.TestCase):
    def _example(self):
        # 类别 0/1 为 seen，2/3 为 unseen；每类两个样本。
        labels_seen = torch.tensor([0, 0, 1, 1])
        labels_unseen = torch.tensor([2, 2, 3, 3])

        def logits(predictions):
            value = torch.full((len(predictions), 4), -2.0)
            for row, class_id in enumerate(predictions):
                value[row, class_id] = 2.0
            return value

        return {
            "global_seen": logits([0, 1, 1, 1]),
            "local_seen": logits([0, 0, 0, 1]),
            "final_seen": logits([0, 0, 1, 0]),
            "global_unseen": logits([2, 0, 3, 3]),
            "local_unseen": logits([1, 2, 3, 2]),
            "final_unseen": logits([2, 2, 0, 3]),
            "seen_labels": labels_seen,
            "unseen_labels": labels_unseen,
            "seenclasses": torch.tensor([0, 1]),
            "unseenclasses": torch.tensor([2, 3]),
        }

    def test_reports_branch_metrics_rescues_harms_and_oracle(self):
        from tools.v5_local_complementarity import analyze_complementarity

        report = analyze_complementarity(**self._example())

        self.assertAlmostEqual(report["branches"]["global"]["S"], 75.0)
        self.assertAlmostEqual(report["branches"]["global"]["U"], 75.0)
        self.assertAlmostEqual(report["branches"]["global"]["H"], 75.0)
        self.assertAlmostEqual(report["branches"]["local"]["S"], 75.0)
        self.assertAlmostEqual(report["branches"]["local"]["U"], 50.0)
        self.assertAlmostEqual(report["branches"]["global"]["ZS"], 100.0)
        self.assertAlmostEqual(report["branches"]["local"]["ZS"], 75.0)
        self.assertAlmostEqual(report["branches"]["oracle_global_local"]["S"], 100.0)
        self.assertAlmostEqual(report["branches"]["oracle_global_local"]["U"], 100.0)
        self.assertAlmostEqual(report["branches"]["oracle_global_local"]["H"], 100.0)
        self.assertAlmostEqual(report["branches"]["oracle_global_local"]["ZS"], 100.0)
        self.assertEqual(
            report["transitions"]["seen"]["global_wrong_local_correct_count"], 1
        )
        self.assertEqual(
            report["transitions"]["seen"]["global_correct_local_wrong_count"], 1
        )
        self.assertEqual(
            report["transitions"]["unseen"]["global_wrong_local_correct_count"], 1
        )
        self.assertEqual(
            report["transitions"]["unseen"]["global_correct_local_wrong_count"], 2
        )
        self.assertEqual(
            report["transitions"]["all"]["global_wrong_local_correct_count"], 2
        )
        self.assertEqual(
            report["transitions"]["all"]["global_correct_local_wrong_count"], 3
        )
        self.assertEqual(
            report["transitions"]["all"]["global_wrong_final_correct_count"], 2
        )
        self.assertEqual(
            report["transitions"]["all"]["global_correct_final_wrong_count"], 2
        )
        self.assertGreaterEqual(
            report["branches"]["oracle_global_local"]["H"],
            report["branches"]["global"]["H"],
        )
        self.assertEqual(report["schema_version"], "gtpj.v5.local_complementarity.v1")

    def test_zsl_restricts_predictions_to_unseen_classes(self):
        from tools.v5_local_complementarity import analyze_complementarity

        values = self._example()
        report = analyze_complementarity(**values)

        # 第二个 unseen 样本的 GZSL 全局预测落到 seen 类 0，ZSL 时应回到 unseen 类。
        self.assertGreater(
            report["branches"]["global"]["ZS"],
            report["branches"]["global"]["U"],
        )

    def test_rejects_nonfinite_scores_and_bad_class_axis(self):
        from tools.v5_local_complementarity import analyze_complementarity

        values = self._example()
        values["local_seen"] = values["local_seen"].clone()
        values["local_seen"][0, 0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            analyze_complementarity(**values)

        values = self._example()
        values["unseenclasses"] = torch.tensor([2, 4])
        with self.assertRaisesRegex(ValueError, "class axis"):
            analyze_complementarity(**values)

    def test_confidence_bins_cover_every_sample_once(self):
        from tools.v5_local_complementarity import analyze_complementarity

        report = analyze_complementarity(**self._example())
        bins = report["global_confidence_quartiles"]
        self.assertEqual(sum(item["sample_count"] for item in bins), 8)
        self.assertEqual(len(bins), 4)

    def test_aggregate_reports_mean_min_max_and_range(self):
        from tools.v5_local_complementarity import aggregate_reports

        first = __import__(
            "tools.v5_local_complementarity", fromlist=["analyze_complementarity"]
        ).analyze_complementarity(**self._example())
        second = json.loads(json.dumps(first))
        second["branches"]["global"]["H"] = 73.0

        aggregate = aggregate_reports([first, second])

        summary = aggregate["branches"]["global"]["H"]
        self.assertEqual(summary["mean"], 74.0)
        self.assertEqual(summary["min"], 73.0)
        self.assertEqual(summary["max"], 75.0)
        self.assertEqual(summary["range"], 2.0)
        self.assertEqual(aggregate["run_count"], 2)

    def test_atomic_json_writer_rejects_nan(self):
        from tools.v5_local_complementarity import write_json_atomic

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.json"
            with self.assertRaises(ValueError):
                write_json_atomic(target, {"bad": math.nan})
            self.assertFalse(target.exists())

    def test_atomic_json_writer_does_not_overwrite_existing_evidence(self):
        from tools.v5_local_complementarity import write_json_atomic

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.json"
            target.write_text('{"old": true}\n', encoding="utf-8")
            with self.assertRaises(FileExistsError):
                write_json_atomic(target, {"new": True})
            self.assertEqual(target.read_text(encoding="utf-8"), '{"old": true}\n')

    def test_direct_cli_help_works_from_repo_root(self):
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "tools/v5_local_complementarity.py", "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--checkpoint", completed.stdout)

    def test_git_identity_requires_exact_head_and_clean_tree(self):
        from tools.v5_local_complementarity import validate_git_state

        commit = "a" * 40
        validate_git_state(commit, "", commit)
        with self.assertRaises(ValueError):
            validate_git_state("b" * 40, "", commit)
        with self.assertRaises(RuntimeError):
            validate_git_state(commit, "?? changed.py\n", commit)

    def test_checkpoint_identity_rejects_every_bound_field_mismatch(self):
        from tools.v5_local_complementarity import validate_checkpoint_identity

        fingerprints = {
            "test_seen_cls": {"sha256": "1" * 64, "size_bytes": 123},
        }
        checkpoint = {
            "template_id": "model/v5-template-v1",
            "code_commit": "a" * 40,
            "config": {"random_seed": 5},
            "config_sha256": "2" * 64,
            "seenclasses": [0, 1],
            "unseenclasses": [2, 3],
            "input_fingerprints": {
                "test_seen_cls": {
                    "sha256": "1" * 64,
                    "size_bytes": 123,
                    "shape": [2, 4],
                    "dtype": "torch.float32",
                }
            },
        }
        arguments = {
            "expected_run_commit": "a" * 40,
            "config_values": {"random_seed": 5},
            "config_sha256": "2" * 64,
            "seenclasses": torch.tensor([0, 1]),
            "unseenclasses": torch.tensor([2, 3]),
            "actual_fingerprints": fingerprints,
        }
        validate_checkpoint_identity(checkpoint, **arguments)

        mutations = (
            ("code_commit", "b" * 40),
            ("config_sha256", "3" * 64),
            ("seenclasses", [1, 0]),
            ("unseenclasses", [3, 2]),
            (
                "input_fingerprints",
                {"test_seen_cls": {"sha256": "4" * 64, "size_bytes": 123}},
            ),
        )
        for field, value in mutations:
            broken = copy.deepcopy(checkpoint)
            broken[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_checkpoint_identity(broken, **arguments)

    def test_canonical_trainer_keeps_split_ids_on_cpu_during_construction(self):
        training_path = Path(__file__).resolve().parents[1] / "train_GTPJ_CUB.py"
        tree = ast.parse(training_path.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_v5_cub_split"
        ]
        self.assertEqual(len(calls), 1)
        device_argument = calls[0].args[5]
        self.assertIsInstance(device_argument, ast.Constant)
        self.assertEqual(device_argument.value, "cpu")

    @unittest.skipUnless(torch.cuda.is_available(), "CUDA is required")
    def test_cpu_split_ids_construct_with_cuda_text_then_move_as_one_model(self):
        from model.MyModel import GTPJ
        from tests.test_v5_template_contract import _parity_config

        config = _parity_config()
        seenclasses = torch.tensor([0, 1, 2, 3])
        unseenclasses = torch.tensor([4, 5])
        sentences = torch.randn(6, 3, 16, device="cuda:0")
        text = sentences.mean(dim=1)
        model = GTPJ(
            config,
            seenclasses,
            unseenclasses,
            seen_text_embeds=text[seenclasses],
            unseen_text_embeds=text[unseenclasses],
            seen_sentence_embeds=sentences[seenclasses],
        ).to("cuda:0")

        self.assertEqual(model.seenclass.device.type, "cuda")
        self.assertEqual(model.unseenclass.device.type, "cuda")


if __name__ == "__main__":
    unittest.main()
