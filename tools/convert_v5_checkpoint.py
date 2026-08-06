"""把历史 V5 checkpoint 显式转换为干净母版字段。

转换永远另存新文件，不覆盖输入、既有输出或既有收据。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import torch


REPO_ROOT = Path(__file__).resolve().parents[1]

PREFIX_RENAMES = (
    ("clip_a_self_adapter.", "pse_module."),
    ("text_adapter.", "pse_module."),
    ("cross_tf.fae.", "bvsa_module.fgvd_encoder."),
    ("cross_tf.", "bvsa_module."),
    ("jepa_predictor.", "sgmp_predictor."),
    ("meta_net.", "icsa_module."),
)

DROPPED_KEYS = {"gate_alpha", "gate_tau"}
DROPPED_PREFIXES = (
    "cross_tf.proj_visual.",
    "cross_tf.proj_text.",
    "bvsa_module.proj_visual.",
    "bvsa_module.proj_text.",
)

CANONICAL_EXACT_KEYS = {
    "seen_text_embeds",
    "unseen_text_embeds",
    "seen_sentence_embeds",
    "unseen_sentence_embeds",
    "logit_scale",
}
CANONICAL_PREFIXES = (
    "pse_module.",
    "bvsa_module.",
    "sgmp_predictor.",
    "icsa_module.",
)


class ConversionError(ValueError):
    """checkpoint 字段无法无歧义转换。"""


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return left.shape == right.shape and left.dtype == right.dtype and torch.equal(left, right)
    return left == right


def _target_key(source_key: str) -> tuple[str | None, str]:
    if source_key in DROPPED_KEYS or source_key.startswith(DROPPED_PREFIXES):
        return None, "drop"
    for old_prefix, new_prefix in PREFIX_RENAMES:
        if source_key.startswith(old_prefix):
            return new_prefix + source_key[len(old_prefix) :], "rename"
    if source_key in CANONICAL_EXACT_KEYS or source_key.startswith(CANONICAL_PREFIXES):
        return source_key, "keep"
    raise ConversionError(f"未知 V5 checkpoint 字段，拒绝猜测转换：{source_key}")


def convert_state_dict(
    source: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """返回规范 state_dict 和 renamed/dropped/conflicts 转换记录。"""

    converted: dict[str, object] = {}
    renamed: list[dict[str, str]] = []
    dropped: list[str] = []
    target_sources: dict[str, str] = {}

    for source_key, value in source.items():
        if not isinstance(source_key, str):
            raise ConversionError(f"checkpoint 字段名必须是字符串：{source_key!r}")
        target_key, action = _target_key(source_key)
        if action == "drop":
            dropped.append(source_key)
            continue
        assert target_key is not None

        if target_key in converted:
            previous_source = target_sources[target_key]
            if not _same_value(converted[target_key], value):
                raise ConversionError(
                    "字段转换冲突："
                    f"{previous_source} 与 {source_key} 都映射到 {target_key}，但值、形状或类型不同。"
                )
            if action == "rename":
                renamed.append({"from": source_key, "to": target_key, "deduplicated": "true"})
            continue

        converted[target_key] = value
        target_sources[target_key] = source_key
        if action == "rename":
            renamed.append({"from": source_key, "to": target_key})

    receipt: dict[str, object] = {
        "renamed": sorted(renamed, key=lambda item: (item["from"], item["to"])),
        "dropped": sorted(dropped),
        "conflicts": [],
    }
    return converted, receipt


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _atomic_torch_save(value: object, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent, delete=False
    )
    temporary = Path(handle.name)
    handle.close()
    try:
        torch.save(value, temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_json_save(value: dict[str, object], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
        encoding="utf-8",
        newline="\n",
    )
    temporary = Path(handle.name)
    try:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()
        os.replace(temporary, destination)
    finally:
        if not handle.closed:
            handle.close()
        if temporary.exists():
            temporary.unlink()


def _resolve_distinct_paths(*paths: Path) -> tuple[Path, ...]:
    resolved = tuple(path.expanduser().resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("输入、输出和收据必须是三个不同路径。")
    return resolved


def convert_checkpoint_file(
    input_path: str | Path,
    output_path: str | Path,
    receipt_path: str | Path,
) -> dict[str, Any]:
    """转换一个 checkpoint，并把新文件和 JSON 收据写到不同路径。"""

    source, output, receipt_file = _resolve_distinct_paths(
        Path(input_path), Path(output_path), Path(receipt_path)
    )
    if not source.is_file():
        raise FileNotFoundError(source)
    if output.exists():
        raise FileExistsError(output)
    if receipt_file.exists():
        raise FileExistsError(receipt_file)

    source_hash = _sha256(source)
    checkpoint = torch.load(source, map_location="cpu", weights_only=False)
    checkpoint_fields_dropped: list[str] = []

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model_state = checkpoint["model_state_dict"]
        if not isinstance(model_state, dict):
            raise ConversionError("model_state_dict 不是字典。")
        converted_state, state_receipt = convert_state_dict(model_state)
        converted_checkpoint = dict(checkpoint)
        converted_checkpoint["model_state_dict"] = converted_state
        # 参数数量和顺序已经变化，旧优化器与调度器状态不能安全续接。
        for field in ("optimizer_state_dict", "scheduler_state_dict"):
            if field in converted_checkpoint:
                converted_checkpoint.pop(field)
                checkpoint_fields_dropped.append(field)
        output_value: object = converted_checkpoint
        checkpoint_format = "full_checkpoint_without_optimizer_state"
    elif isinstance(checkpoint, dict):
        converted_state, state_receipt = convert_state_dict(checkpoint)
        output_value = converted_state
        checkpoint_format = "model_state_dict"
    else:
        raise ConversionError("checkpoint 必须是 state_dict 或包含 model_state_dict 的字典。")

    try:
        _atomic_torch_save(output_value, output)
        receipt: dict[str, Any] = {
            "schema_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "checkpoint_format": checkpoint_format,
            "input": {
                "path": str(source),
                "sha256": source_hash,
                "size_bytes": source.stat().st_size,
            },
            "output": {
                "path": str(output),
                "sha256": _sha256(output),
                "size_bytes": output.stat().st_size,
            },
            "renamed": state_receipt["renamed"],
            "dropped": state_receipt["dropped"],
            "conflicts": state_receipt["conflicts"],
            "checkpoint_fields_dropped": checkpoint_fields_dropped,
            "tool_git_commit": _git_commit(),
        }
        _atomic_json_save(receipt, receipt_file)
    except Exception:
        if output.exists() and not receipt_file.exists():
            output.unlink()
        raise

    if _sha256(source) != source_hash:
        raise RuntimeError("输入 checkpoint 在转换期间发生变化。")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="显式转换历史 V5 checkpoint 字段。")
    parser.add_argument("--input", required=True, type=Path, help="历史 checkpoint 路径")
    parser.add_argument("--output", required=True, type=Path, help="新 checkpoint 路径")
    parser.add_argument("--receipt", required=True, type=Path, help="JSON 转换收据路径")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt = convert_checkpoint_file(args.input, args.output, args.receipt)
    except Exception as error:
        print(f"V5 checkpoint 转换失败：{error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
