"""历史 V5 checkpoint 显式转换工具测试。"""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import torch

from tools.convert_v5_checkpoint import (
    ConversionError,
    convert_checkpoint_file,
    convert_state_dict,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class V5CheckpointConverterTest(unittest.TestCase):
    def test_convert_state_dict_renames_only_known_v5_prefixes(self) -> None:
        source = {
            "clip_a_self_adapter.proj.weight": torch.ones(2, 2),
            "cross_tf.embed_cv.weight": torch.full((2, 2), 2.0),
            "cross_tf.fae.ffn.0.weight": torch.full((2, 2), 3.0),
            "jepa_predictor.0.weight": torch.full((2, 2), 4.0),
            "meta_net.0.weight": torch.full((2, 2), 5.0),
            "logit_scale": torch.tensor(6.0),
        }

        converted, receipt = convert_state_dict(source)

        self.assertEqual(
            set(converted),
            {
                "pse_module.proj.weight",
                "bvsa_module.embed_cv.weight",
                "bvsa_module.fgvd_encoder.ffn.0.weight",
                "sgmp_predictor.0.weight",
                "icsa_module.0.weight",
                "logit_scale",
            },
        )
        self.assertEqual(len(receipt["renamed"]), 5)
        self.assertEqual(receipt["dropped"], [])
        self.assertEqual(receipt["conflicts"], [])

    def test_convert_state_dict_rejects_conflicting_old_and_new_keys(self) -> None:
        source = {
            "cross_tf.embed_cv.weight": torch.ones(2, 2),
            "bvsa_module.embed_cv.weight": torch.zeros(2, 2),
        }

        with self.assertRaisesRegex(ConversionError, "冲突"):
            convert_state_dict(source)

    def test_convert_state_dict_reports_dropped_placeholders(self) -> None:
        source = {
            "gate_alpha": torch.tensor(1.0),
            "gate_tau": torch.tensor(1.0),
            "cross_tf.proj_visual.weight": torch.ones(2, 2),
            "cross_tf.proj_visual.bias": torch.ones(2),
            "cross_tf.proj_text.weight": torch.ones(2, 2),
            "cross_tf.proj_text.bias": torch.ones(2),
            "logit_scale": torch.tensor(2.0),
        }

        converted, receipt = convert_state_dict(source)

        self.assertEqual(set(converted), {"logit_scale"})
        self.assertEqual(set(receipt["dropped"]), set(source) - {"logit_scale"})
        self.assertEqual(receipt["conflicts"], [])

    def test_convert_state_dict_rejects_unknown_experiment_prefix(self) -> None:
        source = {"dynamic_local_gate.net.0.weight": torch.ones(2, 2)}

        with self.assertRaisesRegex(ConversionError, "未知"):
            convert_state_dict(source)

    def test_file_conversion_preserves_source_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source_path = root / "old.pth"
            output_path = root / "converted.pth"
            receipt_path = root / "converted.receipt.json"
            torch.save(
                {
                    "epoch": 3,
                    "optimizer_state_dict": {"state": {}},
                    "scheduler_state_dict": {"last_epoch": 3},
                    "model_state_dict": {
                        "cross_tf.embed_cv.weight": torch.ones(2, 2),
                        "gate_alpha": torch.tensor(1.0),
                    },
                },
                source_path,
            )
            before_hash = _sha256(source_path)

            receipt = convert_checkpoint_file(source_path, output_path, receipt_path)

            self.assertEqual(_sha256(source_path), before_hash)
            self.assertTrue(output_path.exists())
            self.assertTrue(receipt_path.exists())
            converted = torch.load(output_path, map_location="cpu", weights_only=False)
            self.assertEqual(converted["epoch"], 3)
            self.assertEqual(
                set(converted["model_state_dict"]), {"bvsa_module.embed_cv.weight"}
            )
            self.assertNotIn("optimizer_state_dict", converted)
            self.assertNotIn("scheduler_state_dict", converted)
            saved_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_receipt, receipt)
            self.assertEqual(saved_receipt["input"]["sha256"], before_hash)
            self.assertEqual(saved_receipt["output"]["sha256"], _sha256(output_path))
            self.assertEqual(saved_receipt["input"]["path"], str(source_path.resolve()))
            self.assertEqual(saved_receipt["output"]["path"], str(output_path.resolve()))
            self.assertEqual(
                saved_receipt["checkpoint_fields_dropped"],
                ["optimizer_state_dict", "scheduler_state_dict"],
            )
            self.assertTrue(saved_receipt["tool_git_commit"])

    def test_file_conversion_never_overwrites_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source_path = root / "old.pth"
            output_path = root / "converted.pth"
            receipt_path = root / "converted.receipt.json"
            torch.save({"logit_scale": torch.tensor(1.0)}, source_path)
            output_path.write_bytes(b"keep")

            with self.assertRaises(FileExistsError):
                convert_checkpoint_file(source_path, output_path, receipt_path)
            self.assertEqual(output_path.read_bytes(), b"keep")

    def test_file_conversion_requires_three_distinct_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source_path = root / "old.pth"
            output_path = root / "converted.pth"
            torch.save({"logit_scale": torch.tensor(1.0)}, source_path)

            with self.assertRaisesRegex(ValueError, "三个不同路径"):
                convert_checkpoint_file(source_path, output_path, output_path)


if __name__ == "__main__":
    unittest.main()
