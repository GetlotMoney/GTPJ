"""V5 正式训练的输入身份、共享哈希清单和断点续训工具。"""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time

import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FINGERPRINT_MANIFEST = (
    REPO_ROOT / ".runtime" / "data_fingerprints" / "v5_8sent_inputs.json"
)
_MANIFEST_SCHEMA_VERSION = 1
_LOCK_STALE_SECONDS = 6 * 60 * 60


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_identity(path):
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "file_id": f"{int(stat.st_dev)}:{int(stat.st_ino)}",
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _empty_manifest():
    return {"schema_version": _MANIFEST_SCHEMA_VERSION, "files": {}}


def _load_manifest(path):
    manifest_path = Path(path)
    if not manifest_path.is_file():
        return _empty_manifest()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_manifest()
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != _MANIFEST_SCHEMA_VERSION
        or not isinstance(payload.get("files"), dict)
    ):
        return _empty_manifest()
    return payload


def _atomic_write_manifest(path, payload):
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def _manifest_lock(manifest_path, timeout_seconds=_LOCK_STALE_SECONDS):
    """Serialize A/B updates so the shared manifest cannot lose an entry."""

    target = Path(manifest_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(target.name + ".lock")
    deadline = time.monotonic() + float(timeout_seconds)
    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
            finally:
                os.close(descriptor)
            break
        except FileExistsError:
            try:
                age = time.time() - lock_path.stat().st_mtime
                if age > _LOCK_STALE_SECONDS:
                    lock_path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"等待共享指纹清单锁超时：{lock_path}")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def input_record(path, tensor=None, manifest_path=None):
    """Return a stable file record, reusing SHA only for an identical file."""

    manifest_path = Path(manifest_path or DEFAULT_FINGERPRINT_MANIFEST).resolve()
    before = _file_identity(path)
    identity_fields = ("path", "file_id", "size_bytes", "mtime_ns")
    with _manifest_lock(manifest_path):
        payload = _load_manifest(manifest_path)
        cached = payload["files"].get(before["path"])
        cached_sha = cached.get("sha256") if isinstance(cached, dict) else None
        cache_valid = (
            isinstance(cached, dict)
            and isinstance(cached_sha, str)
            and len(cached_sha) == 64
            and all(character in "0123456789abcdef" for character in cached_sha.lower())
            and all(cached.get(field) == before[field] for field in identity_fields)
        )
        if cache_valid:
            digest = cached_sha.lower()
        else:
            digest = sha256_file(before["path"])
            after = _file_identity(path)
            if any(before[field] != after[field] for field in identity_fields):
                raise RuntimeError(f"输入 {before['path']} 在完整哈希期间发生变化。")
            payload["files"][before["path"]] = {**before, "sha256": digest}
            _atomic_write_manifest(manifest_path, payload)

    record = {**before, "sha256": digest}
    if tensor is not None:
        record["shape"] = list(tensor.shape)
        record["dtype"] = str(tensor.dtype)
    return record


def data_fingerprint_manifest_record(manifest_path=None):
    manifest_path = Path(manifest_path or DEFAULT_FINGERPRINT_MANIFEST).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(f"共享输入指纹清单不存在：{manifest_path}")
    return {
        "path": str(manifest_path),
        "sha256": sha256_file(manifest_path),
    }


def input_fingerprints(records):
    return {
        name: {
            key: value
            for key, value in record.items()
            if key not in {"path", "hash_source"}
        }
        for name, record in records.items()
    }


def validate_stable_input_records(before, after):
    if set(before) != set(after):
        raise ValueError("输入清单在加载前后不一致。")
    fields = ("path", "file_id", "size_bytes", "mtime_ns", "sha256")
    for name in before:
        if any(before[name][field] != after[name][field] for field in fields):
            raise RuntimeError(f"输入 {name} 在加载期间发生变化，拒绝继续正式训练。")


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
    for field, value in expected.items():
        if checkpoint.get(field) != value:
            raise ValueError(f"checkpoint 的 {field} 与当前正式运行身份不一致。")
