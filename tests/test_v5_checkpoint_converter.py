"""历史 V5 checkpoint 显式转换工具测试。"""

import hashlib
import json
from pathlib import Path

import pytest
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


def test_convert_state_dict_renames_only_known_v5_prefixes() -> None:
    source = {
        "clip_a_self_adapter.proj.weight": torch.ones(2, 2),
        "cross_tf.embed_cv.weight": torch.full((2, 2), 2.0),
        "cross_tf.fae.ffn.0.weight": torch.full((2, 2), 3.0),
        "jepa_predictor.0.weight": torch.full((2, 2), 4.0),
        "meta_net.0.weight": torch.full((2, 2), 5.0),
        "logit_scale": torch.tensor(6.0),
    }

    converted, receipt = convert_state_dict(source)

    assert set(converted) == {
        "pse_module.proj.weight",
        "bvsa_module.embed_cv.weight",
        "bvsa_module.fgvd_encoder.ffn.0.weight",
        "sgmp_predictor.0.weight",
        "icsa_module.0.weight",
        "logit_scale",
    }
    assert len(receipt["renamed"]) == 5
    assert receipt["dropped"] == []
    assert receipt["conflicts"] == []


def test_convert_state_dict_rejects_conflicting_old_and_new_keys() -> None:
    source = {
        "cross_tf.embed_cv.weight": torch.ones(2, 2),
        "bvsa_module.embed_cv.weight": torch.zeros(2, 2),
    }

    with pytest.raises(ConversionError, match="冲突"):
        convert_state_dict(source)


def test_convert_state_dict_reports_dropped_placeholders() -> None:
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

    assert set(converted) == {"logit_scale"}
    assert set(receipt["dropped"]) == set(source) - {"logit_scale"}
    assert receipt["conflicts"] == []


def test_convert_state_dict_rejects_unknown_experiment_prefix() -> None:
    source = {"dynamic_local_gate.net.0.weight": torch.ones(2, 2)}

    with pytest.raises(ConversionError, match="未知"):
        convert_state_dict(source)


def test_file_conversion_preserves_source_and_writes_receipt(tmp_path: Path) -> None:
    source_path = tmp_path / "old.pth"
    output_path = tmp_path / "converted.pth"
    receipt_path = tmp_path / "converted.receipt.json"
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

    assert _sha256(source_path) == before_hash
    assert output_path.exists()
    assert receipt_path.exists()
    converted = torch.load(output_path, map_location="cpu", weights_only=False)
    assert converted["epoch"] == 3
    assert set(converted["model_state_dict"]) == {"bvsa_module.embed_cv.weight"}
    assert "optimizer_state_dict" not in converted
    assert "scheduler_state_dict" not in converted
    saved_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert saved_receipt == receipt
    assert saved_receipt["input"]["sha256"] == before_hash
    assert saved_receipt["output"]["sha256"] == _sha256(output_path)
    assert saved_receipt["input"]["path"] == str(source_path.resolve())
    assert saved_receipt["output"]["path"] == str(output_path.resolve())
    assert saved_receipt["checkpoint_fields_dropped"] == [
        "optimizer_state_dict",
        "scheduler_state_dict",
    ]
    assert saved_receipt["tool_git_commit"]


def test_file_conversion_never_overwrites_existing_paths(tmp_path: Path) -> None:
    source_path = tmp_path / "old.pth"
    output_path = tmp_path / "converted.pth"
    receipt_path = tmp_path / "converted.receipt.json"
    torch.save({"logit_scale": torch.tensor(1.0)}, source_path)
    output_path.write_bytes(b"keep")

    with pytest.raises(FileExistsError):
        convert_checkpoint_file(source_path, output_path, receipt_path)
    assert output_path.read_bytes() == b"keep"


def test_file_conversion_requires_three_distinct_paths(tmp_path: Path) -> None:
    source_path = tmp_path / "old.pth"
    output_path = tmp_path / "converted.pth"
    torch.save({"logit_scale": torch.tensor(1.0)}, source_path)

    with pytest.raises(ValueError, match="三个不同路径"):
        convert_checkpoint_file(source_path, output_path, output_path)
