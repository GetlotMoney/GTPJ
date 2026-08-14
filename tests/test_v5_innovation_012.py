import importlib.util
from pathlib import Path

import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-012_global8_clip_baseline" / "evaluate.py"
SPEC = importlib.util.spec_from_file_location("global8_baseline", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_global8_prototype_normalizes_each_role_before_equal_mean():
    sentences = torch.zeros(200, 8, 768)
    for index in range(8):
        sentences[:, index, index] = float(index + 1)
    prototypes = MODULE.build_global8_prototypes(sentences)
    expected = torch.zeros(768)
    expected[:8] = 1.0
    expected = torch.nn.functional.normalize(expected, dim=0)
    assert torch.allclose(prototypes[0], expected)
    assert torch.allclose(prototypes.norm(dim=1), torch.ones(200))
    wrong_order = torch.nn.functional.normalize(sentences.mean(dim=1), dim=-1)
    assert not torch.allclose(prototypes, wrong_order)


def test_global8_prototype_rejects_seven_sentence_cache():
    with pytest.raises(ValueError, match="shape"):
        MODULE.build_global8_prototypes(torch.ones(200, 7, 768))


def test_evaluate_global8_reports_per_class_metrics():
    prototypes = torch.eye(200, 768)
    seenclasses = torch.tensor([0, 1])
    unseenclasses = torch.tensor([2, 3])
    seen_features = torch.stack([prototypes[0], prototypes[1]])
    unseen_features = torch.stack([prototypes[2], prototypes[3]])
    metrics = MODULE.evaluate_global8(
        seen_features,
        seenclasses,
        unseen_features,
        unseenclasses,
        seenclasses,
        unseenclasses,
        prototypes,
    )
    assert metrics == {"U": 100.0, "S": 100.0, "H": 100.0, "ZS": 100.0}


def test_verify_input_hashes_rejects_wrong_content(tmp_path):
    path = tmp_path / "input.pt"
    path.write_bytes(b"wrong")
    config = {"expected_sha256": {"sentence_embeds": "0" * 64}}
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        MODULE.verify_input_hashes(config, {"sentence_embeds": path})


def test_run_directory_and_result_are_exclusive(tmp_path):
    output = tmp_path / "RUN-001" / "metrics.json"
    MODULE.create_run_directory(output)
    MODULE.write_result_exclusive(output, {"H": 1.0})
    with pytest.raises(FileExistsError):
        MODULE.create_run_directory(output)
    with pytest.raises(FileExistsError):
        MODULE.write_result_exclusive(output, {"H": 2.0})
