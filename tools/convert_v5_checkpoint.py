"""把历史 V5 checkpoint 显式转换为干净母版字段。

转换必须同时提供干净母版 state_dict 作为字段与形状清单。工具永远另存新文件，
不覆盖输入、目标清单、既有输出或既有收据。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys

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

DROPPED_KEYS = {"gate_alpha", "gate_tau", "unseen_sentence_embeds"}
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

    def __init__(self, message, conflicts=None):
        super().__init__(message)
        self.conflicts = list(conflicts or [])


def _same_value(left, right):
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return left.shape == right.shape and left.dtype == right.dtype and torch.equal(left, right)
    return left == right


def _target_key(source_key):
    if source_key in DROPPED_KEYS or source_key.startswith(DROPPED_PREFIXES):
        return None, "drop"
    for old_prefix, new_prefix in PREFIX_RENAMES:
        if source_key.startswith(old_prefix):
            return new_prefix + source_key[len(old_prefix) :], "rename"
    if source_key in CANONICAL_EXACT_KEYS or source_key.startswith(CANONICAL_PREFIXES):
        return source_key, "keep"
    raise ConversionError(f"未知 V5 checkpoint 字段，拒绝猜测转换：{source_key}")


def _validate_target_value(target_key, value, target_value):
    if isinstance(target_value, torch.Tensor):
        if not isinstance(value, torch.Tensor):
            raise ConversionError(f"字段 {target_key} 应为 Tensor，实际为 {type(value).__name__}。")
        if value.shape != target_value.shape:
            raise ConversionError(
                f"字段 {target_key} 形状不匹配：历史={tuple(value.shape)}，"
                f"母版={tuple(target_value.shape)}。"
            )
        if value.dtype != target_value.dtype:
            raise ConversionError(
                f"字段 {target_key} 类型不匹配：历史={value.dtype}，母版={target_value.dtype}。"
            )
    elif type(value) is not type(target_value):
        raise ConversionError(
            f"字段 {target_key} 类型不匹配：历史={type(value).__name__}，"
            f"母版={type(target_value).__name__}。"
        )


def convert_state_dict(source, target_state):
    """按明确目标字段与形状返回规范 state_dict 和转换记录。"""

    if not isinstance(source, dict) or not isinstance(target_state, dict):
        raise ConversionError("历史 state_dict 和母版 state_dict 都必须是字典。")
    converted = {}
    renamed = []
    dropped = []
    target_sources = {}

    for source_key, value in source.items():
        if not isinstance(source_key, str):
            raise ConversionError(f"checkpoint 字段名必须是字符串：{source_key!r}")
        target_key, action = _target_key(source_key)
        if action == "drop":
            dropped.append(source_key)
            continue
        if target_key not in target_state:
            raise ConversionError(
                f"字段 {source_key} 映射为 {target_key}，但干净母版没有这个字段。"
            )
        _validate_target_value(target_key, value, target_state[target_key])

        if target_key in converted:
            previous_source = target_sources[target_key]
            if not _same_value(converted[target_key], value):
                conflict = {
                    "target": target_key,
                    "sources": [previous_source, source_key],
                }
                raise ConversionError(
                    f"字段转换冲突：{previous_source} 与 {source_key} 都映射到 "
                    f"{target_key}，但值不同。",
                    conflicts=[conflict],
                )
            if action == "rename":
                renamed.append(
                    {"from": source_key, "to": target_key, "deduplicated": True}
                )
            continue

        converted[target_key] = value
        target_sources[target_key] = source_key
        if action == "rename":
            renamed.append({"from": source_key, "to": target_key})

    missing = sorted(set(target_state) - set(converted))
    if missing:
        raise ConversionError(f"转换后缺少干净母版字段：{missing}")

    return converted, {
        "renamed": sorted(renamed, key=lambda item: (item["from"], item["to"])),
        "dropped": sorted(dropped),
        "conflicts": [],
    }


def _sha256_bytes(content):
    return hashlib.sha256(content).hexdigest()


def _git_commit():
    result = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "log",
            "-1",
            "--format=%H",
            "--",
            "tools/convert_v5_checkpoint.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _exclusive_torch_save(value, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    torch.save(value, buffer)
    created = False
    try:
        with destination.open("xb") as stream:
            created = True
            stream.write(buffer.getvalue())
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if created and destination.exists():
            destination.unlink()
        raise


def _exclusive_json_save(value, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    created = False
    try:
        with destination.open("xb") as stream:
            created = True
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if created and destination.exists():
            destination.unlink()
        raise


def _resolve_distinct_paths(*paths):
    resolved = tuple(Path(path).expanduser().resolve() for path in paths)
    if len(set(resolved)) != len(resolved):
        raise ValueError("输入、目标清单、输出和收据必须是四个不同路径。")
    return resolved


def _extract_state_dict(value, label):
    if isinstance(value, dict) and "model_state_dict" in value:
        state = value["model_state_dict"]
    else:
        state = value
    if not isinstance(state, dict):
        raise ConversionError(f"{label} 必须是 state_dict 或包含 model_state_dict 的字典。")
    return state


def _base_receipt(source, source_bytes, target_schema, target_bytes, output):
    return {
        "schema_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(source),
            "sha256": _sha256_bytes(source_bytes),
            "size_bytes": len(source_bytes),
        },
        "target_schema": {
            "path": str(target_schema),
            "sha256": _sha256_bytes(target_bytes),
            "size_bytes": len(target_bytes),
        },
        "output_path": str(output),
        "tool_git_commit": _git_commit(),
    }


def convert_checkpoint_file(input_path, target_schema_path, output_path, receipt_path):
    """转换 checkpoint；成功或字段冲突时均留下不覆盖旧文件的 JSON 收据。"""

    source, target_schema, output, receipt_file = _resolve_distinct_paths(
        input_path, target_schema_path, output_path, receipt_path
    )
    if not source.is_file():
        raise FileNotFoundError(source)
    if not target_schema.is_file():
        raise FileNotFoundError(target_schema)
    if output.exists():
        raise FileExistsError(output)
    if receipt_file.exists():
        raise FileExistsError(receipt_file)

    source_bytes = source.read_bytes()
    target_bytes = target_schema.read_bytes()
    receipt = _base_receipt(source, source_bytes, target_schema, target_bytes, output)
    checkpoint_fields_dropped = []
    created_output = False

    try:
        checkpoint = torch.load(io.BytesIO(source_bytes), map_location="cpu", weights_only=False)
        target_value = torch.load(io.BytesIO(target_bytes), map_location="cpu", weights_only=False)
        target_state = _extract_state_dict(target_value, "目标清单")

        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            converted_state, state_receipt = convert_state_dict(
                _extract_state_dict(checkpoint, "历史 checkpoint"), target_state
            )
            converted_checkpoint = dict(checkpoint)
            converted_checkpoint["model_state_dict"] = converted_state
            for field in ("optimizer_state_dict", "scheduler_state_dict"):
                if field in converted_checkpoint:
                    converted_checkpoint.pop(field)
                    checkpoint_fields_dropped.append(field)
            output_value = converted_checkpoint
            checkpoint_format = "full_checkpoint_without_optimizer_state"
        else:
            converted_state, state_receipt = convert_state_dict(
                _extract_state_dict(checkpoint, "历史 checkpoint"), target_state
            )
            output_value = converted_state
            checkpoint_format = "model_state_dict"

        _exclusive_torch_save(output_value, output)
        created_output = True
        output_bytes = output.read_bytes()
        receipt.update(
            {
                "status": "success",
                "checkpoint_format": checkpoint_format,
                "output": {
                    "path": str(output),
                    "sha256": _sha256_bytes(output_bytes),
                    "size_bytes": len(output_bytes),
                },
                "renamed": state_receipt["renamed"],
                "dropped": state_receipt["dropped"],
                "conflicts": state_receipt["conflicts"],
                "checkpoint_fields_dropped": checkpoint_fields_dropped,
            }
        )
        _exclusive_json_save(receipt, receipt_file)
        return receipt
    except Exception as error:
        if created_output and output.exists():
            output.unlink()
        if isinstance(error, ConversionError):
            receipt.update(
                {
                    "status": "failed",
                    "error": str(error),
                    "conflicts": error.conflicts,
                }
            )
            _exclusive_json_save(receipt, receipt_file)
        raise


def build_parser():
    parser = argparse.ArgumentParser(description="显式转换历史 V5 checkpoint 字段。")
    parser.add_argument("--input", required=True, type=Path, help="历史 checkpoint 路径")
    parser.add_argument(
        "--target-schema",
        required=True,
        type=Path,
        help="干净 V5 母版 state_dict 或完整 checkpoint，用来核对字段和形状",
    )
    parser.add_argument("--output", required=True, type=Path, help="新 checkpoint 路径")
    parser.add_argument("--receipt", required=True, type=Path, help="JSON 转换收据路径")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        receipt = convert_checkpoint_file(
            args.input, args.target_schema, args.output, args.receipt
        )
    except Exception as error:
        print(f"V5 checkpoint 转换失败：{error}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
