"""V5 正式训练的输入身份和断点续训工具。"""

import hashlib
from pathlib import Path
import random

import numpy as np
import torch


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_record(path, tensor=None):
    source = Path(path)
    resolved = source if str(source).startswith("/proc/self/fd/") else source.resolve()
    record = {
        "path": str(resolved),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
    }
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
        for field in ("path", "sha256", "size_bytes"):
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
