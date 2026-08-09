"""V5 正式训练的输入身份、哈希复用和断点续训工具。"""

import hashlib
import json
import os
from pathlib import Path
import random
import tempfile

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_FINGERPRINT_MANIFEST = (
    REPO_ROOT / ".runtime" / "data_fingerprints" / "v5_8sent_inputs.json"
)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest_path(path=None):
    return Path(path or DEFAULT_DATA_FINGERPRINT_MANIFEST).resolve()


def _file_identity(path):
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "file_id": f"{stat.st_dev}:{stat.st_ino}",
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _empty_fingerprint_manifest():
    return {"schema_version": 1, "files": {}}


def _valid_sha256(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def _load_fingerprint_manifest(path=None):
    manifest_path = _manifest_path(path)
    if not manifest_path.is_file():
        return _empty_fingerprint_manifest()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_fingerprint_manifest()
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != 1
        or not isinstance(manifest.get("files"), dict)
    ):
        return _empty_fingerprint_manifest()
    return manifest


def _write_fingerprint_manifest(manifest, path=None):
    manifest_path = _manifest_path(path)
    directory = manifest_path.parent
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=directory,
        prefix=f".{manifest_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
        temporary = Path(stream.name)
    os.replace(temporary, manifest_path)


def cached_data_sha256(path, manifest_path=None):
    """完整哈希一次；文件身份未变时只做快速身份核验。"""
    identity = _file_identity(path)
    manifest = _load_fingerprint_manifest(manifest_path)
    cached = manifest["files"].get(identity["path"])
    identity_fields = ("path", "file_id", "size_bytes", "mtime_ns")
    if (
        isinstance(cached, dict)
        and _valid_sha256(cached.get("sha256"))
        and all(cached.get(field) == identity[field] for field in identity_fields)
    ):
        return cached["sha256"]

    digest = sha256_file(identity["path"])
    manifest["files"][identity["path"]] = {**identity, "sha256": digest}
    _write_fingerprint_manifest(manifest, manifest_path)
    return digest


def data_fingerprint_manifest_record(manifest_path=None):
    path = _manifest_path(manifest_path)
    if not path.is_file():
        return None
    return {
        "path": str(path),
        "sha256": sha256_file(path),
    }


def input_record(path, tensor=None, manifest_path=None):
    record = _file_identity(path)
    record["sha256"] = cached_data_sha256(record["path"], manifest_path)
    if tensor is not None:
        record["shape"] = list(tensor.shape)
        record["dtype"] = str(tensor.dtype)
    return record


def input_fingerprints(records):
    return {
        name: {key: value for key, value in record.items() if key != "path"}
        for name, record in records.items()
    }


def validate_stable_input_records(before, after):
    if set(before) != set(after):
        raise ValueError("输入清单在加载前后不一致。")
    for name in before:
        for field in ("path", "file_id", "size_bytes", "mtime_ns", "sha256"):
            if before[name][field] != after[name][field]:
                raise RuntimeError(
                    f"输入 {name} 在加载期间发生变化，拒绝继续正式训练。"
                )


def capture_rng_state():
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def restore_rng_state(state):
    required = {"python", "numpy", "torch_cpu", "torch_cuda"}
    if not isinstance(state, dict) or set(state) != required:
        raise ValueError("checkpoint 的 rng_state 不完整。")
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch_cpu"].cpu())
    cuda_states = state["torch_cuda"]
    if torch.cuda.is_available():
        if len(cuda_states) != torch.cuda.device_count():
            raise ValueError("checkpoint 的 CUDA RNG 设备数量与当前机器不一致。")
        torch.cuda.set_rng_state_all([item.cpu() for item in cuda_states])
    elif cuda_states:
        raise ValueError("checkpoint 包含 CUDA RNG，但当前环境没有 CUDA。")


def validate_resume_identity(
    checkpoint,
    *,
    template_id,
    code_commit,
    config_values,
    config_sha256,
    fingerprints,
    fingerprint_manifest=None,
    seenclasses,
    unseenclasses,
):
    expected = {
        "template_id": template_id,
        "code_commit": code_commit,
        "config": config_values,
        "config_sha256": config_sha256,
        "input_fingerprints": fingerprints,
        "seenclasses": list(seenclasses),
        "unseenclasses": list(unseenclasses),
    }
    if fingerprint_manifest is not None:
        expected["data_fingerprint_manifest"] = fingerprint_manifest
    for field, value in expected.items():
        if checkpoint.get(field) != value:
            raise ValueError(f"checkpoint 的 {field} 与当前正式运行身份不一致。")
