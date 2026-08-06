"""历史 V5 checkpoint 显式转换工具测试。"""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch

from tools.convert_v5_checkpoint import (
    ConversionError,
    _exclusive_torch_save,
    convert_checkpoint_file,
    convert_state_dict,
)


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class V5CheckpointConverterTest(unittest.TestCase):
    def test_convert_state_dict_uses_explicit_target_schema(self):
        source = {
            "clip_a_self_adapter.proj.weight": torch.ones(2, 2),
            "cross_tf.embed_cv.weight": torch.full((2, 2), 2.0),
            "jepa_predictor.0.weight": torch.full((2, 2), 3.0),
            "meta_net.0.weight": torch.full((2, 2), 4.0),
            "logit_scale": torch.tensor(5.0),
        }
        target = {
            "pse_module.proj.weight": torch.empty(2, 2),
            "bvsa_module.embed_cv.weight": torch.empty(2, 2),
            "sgmp_predictor.0.weight": torch.empty(2, 2),
            "icsa_module.0.weight": torch.empty(2, 2),
            "logit_scale": torch.empty(()),
        }

        converted, receipt = convert_state_dict(source, target)

        self.assertEqual(set(converted), set(target))
        self.assertEqual(len(receipt["renamed"]), 4)
        self.assertEqual(receipt["dropped"], [])

    def test_known_prefix_with_unknown_suffix_is_rejected(self):
        with self.assertRaisesRegex(ConversionError, "母版没有"):
            convert_state_dict(
                {"cross_tf.dynamic_router.weight": torch.ones(1)},
                {"bvsa_module.embed_cv.weight": torch.empty(1)},
            )

    def test_wrong_shape_is_rejected(self):
        with self.assertRaisesRegex(ConversionError, "形状不匹配"):
            convert_state_dict(
                {"cross_tf.embed_cv.weight": torch.ones(1)},
                {"bvsa_module.embed_cv.weight": torch.empty(2, 2)},
            )

    def test_conflicting_old_and_new_keys_are_reported(self):
        source = {
            "cross_tf.embed_cv.weight": torch.ones(2, 2),
            "bvsa_module.embed_cv.weight": torch.zeros(2, 2),
        }
        target = {"bvsa_module.embed_cv.weight": torch.empty(2, 2)}

        with self.assertRaisesRegex(ConversionError, "字段转换冲突") as context:
            convert_state_dict(source, target)

        self.assertEqual(context.exception.conflicts[0]["target"], "bvsa_module.embed_cv.weight")

    def test_known_placeholders_are_dropped(self):
        source = {
            "gate_alpha": torch.tensor(1.0),
            "unseen_sentence_embeds": torch.ones(2, 3, 4),
            "logit_scale": torch.tensor(2.0),
        }
        converted, receipt = convert_state_dict(
            source, {"logit_scale": torch.empty(())}
        )

        self.assertEqual(set(converted), {"logit_scale"})
        self.assertEqual(
            set(receipt["dropped"]), {"gate_alpha", "unseen_sentence_embeds"}
        )

    def test_conversion_rejects_missing_target_fields(self):
        with self.assertRaisesRegex(ConversionError, "缺少干净母版字段"):
            convert_state_dict(
                {"logit_scale": torch.tensor(1.0)},
                {"logit_scale": torch.empty(()), "seen_text_embeds": torch.empty(2, 3)},
            )

    def test_file_conversion_preserves_source_and_writes_success_receipt(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source = root / "old.pth"
            schema = root / "schema.pth"
            output = root / "converted.pth"
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
                source,
            )
            torch.save(
                {"bvsa_module.embed_cv.weight": torch.empty(2, 2)}, schema
            )
            before_hash = _sha256(source)

            receipt = convert_checkpoint_file(source, schema, output, receipt_path)

            self.assertEqual(_sha256(source), before_hash)
            self.assertEqual(receipt["status"], "success")
            converted = torch.load(output, map_location="cpu", weights_only=False)
            self.assertEqual(
                set(converted["model_state_dict"]), {"bvsa_module.embed_cv.weight"}
            )
            self.assertNotIn("optimizer_state_dict", converted)
            self.assertNotIn("scheduler_state_dict", converted)
            saved = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(saved, receipt)
            self.assertEqual(saved["output"]["sha256"], _sha256(output))
            self.assertEqual(
                saved["checkpoint_fields_dropped"],
                ["optimizer_state_dict", "scheduler_state_dict"],
            )

    def test_file_conflict_writes_failure_receipt_without_output(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source = root / "old.pth"
            schema = root / "schema.pth"
            output = root / "converted.pth"
            receipt_path = root / "failed.receipt.json"
            torch.save(
                {
                    "cross_tf.embed_cv.weight": torch.ones(2, 2),
                    "bvsa_module.embed_cv.weight": torch.zeros(2, 2),
                },
                source,
            )
            torch.save(
                {"bvsa_module.embed_cv.weight": torch.empty(2, 2)}, schema
            )

            with self.assertRaisesRegex(ConversionError, "字段转换冲突"):
                convert_checkpoint_file(source, schema, output, receipt_path)

            self.assertFalse(output.exists())
            failed = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(
                failed["conflicts"][0]["target"], "bvsa_module.embed_cv.weight"
            )

    def test_exclusive_writer_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            output = Path(temporary) / "converted.pth"
            output.write_bytes(b"keep")

            with self.assertRaises(FileExistsError):
                _exclusive_torch_save({"x": torch.tensor(1)}, output)

            self.assertEqual(output.read_bytes(), b"keep")

    def test_receipt_failure_never_deletes_concurrent_replacement(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source = root / "old.pth"
            schema = root / "schema.pth"
            output = root / "converted.pth"
            receipt_path = root / "converted.receipt.json"
            torch.save({"logit_scale": torch.tensor(1.0)}, source)
            torch.save({"logit_scale": torch.empty(())}, schema)

            def replace_output_then_fail(*_args, **_kwargs):
                output.unlink()
                output.write_bytes(b"OTHER_PROCESS_FILE")
                raise RuntimeError("simulated receipt failure")

            with mock.patch(
                "tools.convert_v5_checkpoint._exclusive_json_save",
                side_effect=replace_output_then_fail,
            ):
                with self.assertRaisesRegex(RuntimeError, "simulated receipt failure"):
                    convert_checkpoint_file(source, schema, output, receipt_path)

            self.assertEqual(output.read_bytes(), b"OTHER_PROCESS_FILE")

    def test_file_conversion_requires_four_distinct_paths(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-converter-") as temporary:
            root = Path(temporary)
            source = root / "old.pth"
            schema = root / "schema.pth"
            output = root / "converted.pth"
            torch.save({"logit_scale": torch.tensor(1.0)}, source)
            torch.save({"logit_scale": torch.empty(())}, schema)

            with self.assertRaisesRegex(ValueError, "四个不同路径"):
                convert_checkpoint_file(source, schema, output, output)


if __name__ == "__main__":
    unittest.main()
