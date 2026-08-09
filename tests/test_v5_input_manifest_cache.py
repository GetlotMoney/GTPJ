"""大缓存只在首次或文件变化时重新计算 SHA-256。"""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tools import v5_input_manifest_cache as manifest_cache


class V5InputManifestCacheTest(unittest.TestCase):
    def test_unchanged_file_reuses_first_full_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "large.bin"
            data.write_bytes(b"first-content")
            cache = root / "manifest.json"

            with mock.patch.object(
                manifest_cache,
                "_sha256_file",
                wraps=manifest_cache._sha256_file,
            ) as digest:
                first = manifest_cache.build_cached_records({"data": data}, cache)
                second = manifest_cache.build_cached_records({"data": data}, cache)

            self.assertEqual(1, digest.call_count)
            self.assertEqual(first["data"]["sha256"], second["data"]["sha256"])
            self.assertEqual("cache_reused", second["data"]["hash_source"])

    def test_same_size_with_changed_mtime_is_rehashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "large.bin"
            data.write_bytes(b"aaaa")
            cache = root / "manifest.json"
            first = manifest_cache.build_cached_records({"data": data}, cache)
            data.write_bytes(b"bbbb")
            stat = data.stat()
            changed_mtime = stat.st_mtime_ns + 1_000_000_000
            os.utime(data, ns=(changed_mtime, changed_mtime))

            second = manifest_cache.build_cached_records({"data": data}, cache)

            self.assertNotEqual(first["data"]["sha256"], second["data"]["sha256"])
            self.assertEqual("hashed", second["data"]["hash_source"])

    def test_load_window_detects_stat_change_without_second_full_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / "cache.pt"
            data.write_bytes(b"stable")
            before = manifest_cache.capture_input_stats({"data": data})
            data.write_bytes(b"changed")
            after = manifest_cache.capture_input_stats({"data": data})

            with self.assertRaisesRegex(RuntimeError, "data"):
                manifest_cache.validate_stable_input_stats(before, after)

    def test_manifest_is_strict_json_and_keeps_resolved_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data.bin"
            data.write_bytes(b"x")
            cache = root / "manifest.json"
            record = manifest_cache.build_cached_records({"data": data}, cache)["data"]
            payload = json.loads(cache.read_text(encoding="utf-8"))

            self.assertEqual(str(data.resolve()), record["path"])
            self.assertEqual(1, payload["schema_version"])


if __name__ == "__main__":
    unittest.main()
