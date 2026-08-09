"""大文件身份清单只哈希一次，并在快速身份变化时停止。"""

from pathlib import Path
import json
import tempfile
import unittest
from unittest import mock

from tools import v5_runtime


class V5RuntimeFingerprintTest(unittest.TestCase):
    def test_unchanged_file_reuses_cached_sha256(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "large.bin"
            manifest = root / "fingerprints.json"
            data.write_bytes(b"stable-input")
            first = v5_runtime.input_record(data, manifest_path=manifest)

            with mock.patch.object(
                v5_runtime, "sha256_file", side_effect=AssertionError("不应重复全哈希")
            ):
                second = v5_runtime.input_record(data, manifest_path=manifest)

            self.assertEqual(first, second)
            self.assertTrue(manifest.is_file())

    def test_non_hex_cached_digest_is_treated_as_corrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "large.bin"
            manifest = root / "fingerprints.json"
            data.write_bytes(b"stable-input")
            first = v5_runtime.input_record(data, manifest_path=manifest)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"][first["path"]]["sha256"] = "z" * 64
            manifest.write_text(json.dumps(payload), encoding="utf-8")

            repaired = v5_runtime.input_record(data, manifest_path=manifest)

            self.assertEqual(repaired["sha256"], first["sha256"])
            self.assertNotEqual(repaired["sha256"], "z" * 64)

    def test_changed_file_gets_new_identity_and_stability_check_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "input.bin"
            manifest = root / "fingerprints.json"
            data.write_bytes(b"first")
            before = {"data": v5_runtime.input_record(data, manifest_path=manifest)}
            data.write_bytes(b"second-value")
            after = {"data": v5_runtime.input_record(data, manifest_path=manifest)}

            self.assertNotEqual(before["data"]["sha256"], after["data"]["sha256"])
            with self.assertRaisesRegex(RuntimeError, "加载期间发生变化"):
                v5_runtime.validate_stable_input_records(before, after)


if __name__ == "__main__":
    unittest.main()
