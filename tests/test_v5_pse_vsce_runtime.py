"""实验 B 的输入指纹与训练入口边界。"""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch

from tools import v5_runtime
from tools.v5_evaluation import evaluate_cached_v5


class _CudaClassAxisModel(torch.nn.Module):
    nclass = 2

    def __init__(self):
        super().__init__()
        self.register_buffer("seenclass", torch.tensor([0], device="cuda"))
        self.register_buffer("unseenclass", torch.tensor([1], device="cuda"))

    def forward(self, features, is_train=False):
        labels = features[:, 0, 0].long()
        logits = torch.full((features.size(0), 2), -1.0, device=features.device)
        logits.scatter_(1, labels.unsqueeze(1), 1.0)
        return {"clip_S_pp": logits}


class TestV5PSEVSCERuntime(unittest.TestCase):
    def test_clean_gate_only_allows_helper_parameter_matrix_updates(self):
        import train_GTPJ_CUB as training

        config_path = Path("experiments/v5/innovation/INNOVATION-010_pse_vsce/config.yaml").resolve()
        allowed_status = (
            " M experiments/v5/innovation/INNOVATION-010_pse_vsce/PARAMETER_MATRIX.csv\n"
            " M experiments/v5/innovation/INNOVATION-010_pse_vsce/PARAMETER_MATRIX.md\n"
        )
        with mock.patch.object(
            training.subprocess,
            "run",
            return_value=mock.Mock(stdout=allowed_status),
        ):
            training._require_clean_code_tree(config_path)

        with mock.patch.object(
            training.subprocess,
            "run",
            return_value=mock.Mock(stdout=" M model/MyModel.py\n"),
        ):
            with self.assertRaisesRegex(RuntimeError, "其余工作树改动"):
                training._require_clean_code_tree(config_path)

    def test_manifest_reuses_hash_while_identity_is_unchanged(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-vsce-fingerprint-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            data_path.write_bytes(b"stable-v5-input")

            original_hash = v5_runtime.sha256_file
            with mock.patch.object(
                v5_runtime, "sha256_file", wraps=original_hash
            ) as hash_call:
                first = v5_runtime.input_record(
                    data_path, manifest_path=manifest_path
                )
                second = v5_runtime.input_record(
                    data_path, manifest_path=manifest_path
                )

            self.assertEqual(first, second)
            self.assertEqual(hash_call.call_count, 1)
            self.assertEqual(first["file_id"], second["file_id"])
            self.assertTrue(manifest_path.is_file())

    def test_changed_input_is_rehashed_and_load_window_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-vsce-changing-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            data_path.write_bytes(b"before")
            before = {
                "cache": v5_runtime.input_record(
                    data_path, manifest_path=manifest_path
                )
            }

            data_path.write_bytes(b"after-with-a-different-size")
            after = {
                "cache": v5_runtime.input_record(
                    data_path, manifest_path=manifest_path
                )
            }
            self.assertNotEqual(before["cache"]["sha256"], after["cache"]["sha256"])
            with self.assertRaisesRegex(RuntimeError, "发生变化"):
                v5_runtime.validate_stable_input_records(before, after)

    def test_corrupt_non_hex_manifest_sha_is_rehashed(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-vsce-corrupt-sha-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            data_path.write_bytes(b"stable-v5-input")
            first = v5_runtime.input_record(data_path, manifest_path=manifest_path)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["files"][str(data_path.resolve())]["sha256"] = "z" * 64
            manifest_path.write_text(json.dumps(payload), encoding="utf-8")

            original_hash = v5_runtime.sha256_file
            with mock.patch.object(
                v5_runtime, "sha256_file", wraps=original_hash
            ) as hash_call:
                repaired = v5_runtime.input_record(
                    data_path, manifest_path=manifest_path
                )

            self.assertEqual(hash_call.call_count, 1)
            self.assertEqual(repaired["sha256"], first["sha256"])

    def test_diagnostics_keep_bounded_true_class_patch_examples(self):
        import train_GTPJ_CUB as training

        state = training._new_diagnostic_state(8, 2)
        sentence_weights = torch.zeros(2, 6, 8)
        sentence_weights[0, 3, 5] = 1.0
        sentence_weights[1, 1, 2] = 1.0
        region_weights = torch.zeros(2, 6, 2)
        region_weights[0, 3, 1] = 1.0
        region_weights[1, 1, 0] = 1.0
        output = {
            "sentence_weights": sentence_weights,
            "local_region_weights": region_weights,
            "sgmp_selected_indices": torch.tensor([[8, 49], [575, 24]]),
            "global_logits": torch.zeros(2, 6),
            "local_logits": torch.zeros(2, 6),
            "final_logits": torch.zeros(2, 6),
            "match_diagnostics": {
                "match_mean": torch.tensor(0.0),
                "match_std": torch.tensor(0.0),
            },
        }
        training._update_diagnostics(
            state,
            output,
            torch.tensor([3, 1]),
            sample_indices=torch.tensor([101, 202]),
        )
        examples = training._finalize_diagnostics(state)["true_class_examples"]
        self.assertEqual(examples[0]["top_sentence_slot"], 5)
        self.assertEqual(examples[0]["top_patch_index"], 49)
        self.assertEqual(examples[0]["top_patch_row_col"], [2, 1])
        self.assertEqual(examples[1]["top_patch_index"], 575)
        self.assertEqual(examples[1]["top_patch_row_col"], [23, 23])

    def test_manifest_record_contains_absolute_path_and_manifest_sha(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-vsce-manifest-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            data_path.write_bytes(b"manifest-source")
            v5_runtime.input_record(data_path, manifest_path=manifest_path)

            record = v5_runtime.data_fingerprint_manifest_record(manifest_path)
            self.assertEqual(record["path"], str(manifest_path.resolve()))
            expected = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            self.assertEqual(record["sha256"], expected)

    def test_training_module_exposes_strict_eight_sentence_loader_and_cli_flags(self):
        import train_GTPJ_CUB as training

        self.assertEqual(training.GPT56_SENTENCE_SHA256, (
            "8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3"
        ))
        parser = training.build_parser()
        args = parser.parse_args(
            [
                "--output-dir",
                "run-output",
                "--fingerprint-manifest",
                "shared-fingerprints.json",
            ]
        )
        self.assertEqual(args.output_dir, Path("run-output"))
        self.assertEqual(args.fingerprint_manifest, Path("shared-fingerprints.json"))

        with tempfile.TemporaryDirectory(prefix="gtpj-vsce-sentences-") as temporary:
            cache_path = Path(temporary) / "sentences.pt"
            torch.save(torch.randn(6, 8, 16), cache_path)
            digest = hashlib.sha256(cache_path.read_bytes()).hexdigest()
            loaded = training.load_sentence_cache(
                cache_path,
                expected_classes=6,
                expected_dim=16,
                device="cpu",
                expected_sha256=digest,
            )
            self.assertEqual(tuple(loaded.shape), (6, 8, 16))

            torch.save(torch.randn(6, 7, 16), cache_path)
            digest = hashlib.sha256(cache_path.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, r"\[6, 8, 16\]"):
                training.load_sentence_cache(
                    cache_path,
                    expected_classes=6,
                    expected_dim=16,
                    device="cpu",
                    expected_sha256=digest,
                )

    @unittest.skipUnless(torch.cuda.is_available(), "需要 CUDA 验证跨设备类别轴")
    def test_evaluation_accepts_cuda_class_ids_without_cpu_cuda_comparison(self):
        model = _CudaClassAxisModel()
        cache = {
            "seen_cls": torch.tensor([[0.0]]),
            "seen_patches": torch.zeros(1, 576, 1),
            "seen_labels": torch.tensor([0]),
            "unseen_cls": torch.tensor([[1.0]]),
            "unseen_patches": torch.zeros(1, 576, 1),
            "unseen_labels": torch.tensor([1]),
        }
        metrics = evaluate_cached_v5(
            model,
            torch.device("cuda"),
            cache,
            model.seenclass,
            model.unseenclass,
            batch_size=1,
        )
        self.assertEqual(metrics, (1.0, 1.0, 1.0, 1.0))


if __name__ == "__main__":
    unittest.main()
