"""按路径、大小和修改时间复用大输入文件的 SHA-256。

首次遇到文件时完整读取；后续只有元数据变化才重新读取。训练加载前后只比较
轻量 stat，避免同一轮对约 10 GiB 缓存做两次额外全量扫描。
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import uuid


SCHEMA_VERSION = 1


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stat(path):
    resolved = Path(path).resolve()
    info = resolved.stat()
    return {
        "path": str(resolved),
        "size_bytes": int(info.st_size),
        "mtime_ns": int(info.st_mtime_ns),
    }


def capture_input_stats(paths):
    """获取训练加载窗口两端要比较的轻量元数据。"""

    return {name: _stat(path) for name, path in paths.items()}


def validate_stable_input_stats(before, after):
    if set(before) != set(after):
        raise RuntimeError("训练加载前后的输入清单发生变化。")
    for name in before:
        for field in ("path", "size_bytes", "mtime_ns"):
            if before[name][field] != after[name][field]:
                raise RuntimeError(f"输入 {name} 在训练加载期间发生变化。")


def _load_manifest(path):
    manifest_path = Path(path)
    if not manifest_path.exists():
        return {"schema_version": SCHEMA_VERSION, "entries": {}}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"不支持的输入哈希清单版本：{payload.get('schema_version')!r}")
    if not isinstance(payload.get("entries"), dict):
        raise ValueError("输入哈希清单 entries 必须是字典。")
    return payload


def _atomic_write_manifest(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def build_cached_records(paths, manifest_path):
    """返回含稳定 SHA-256 的记录，并只重哈希发生变化的文件。"""

    payload = _load_manifest(manifest_path)
    entries = payload["entries"]
    records = {}
    changed = False

    for name, path in paths.items():
        before = _stat(path)
        key = before["path"]
        cached = entries.get(key)
        cache_valid = (
            isinstance(cached, dict)
            and cached.get("size_bytes") == before["size_bytes"]
            and cached.get("mtime_ns") == before["mtime_ns"]
            and isinstance(cached.get("sha256"), str)
            and len(cached["sha256"]) == 64
        )
        if cache_valid:
            digest = cached["sha256"]
            source = "cache_reused"
        else:
            digest = _sha256_file(before["path"])
            after = _stat(path)
            validate_stable_input_stats({name: before}, {name: after})
            entries[key] = {
                "size_bytes": before["size_bytes"],
                "mtime_ns": before["mtime_ns"],
                "sha256": digest,
            }
            changed = True
            source = "hashed"
        records[name] = {
            **before,
            "sha256": digest,
            "hash_source": source,
        }

    if changed or not Path(manifest_path).exists():
        _atomic_write_manifest(manifest_path, payload)
    return records
