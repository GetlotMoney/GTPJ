import importlib.util
from pathlib import Path

import pytest
import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-012_global8_clip_baseline" / "evaluate.py"
SPEC = importlib.util.spec_from_file_location("global8_baseline", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_global8_prototype_uses_all_eight_roles_equally():
    sentences = torch.zeros(200, 8, 768)
    for index in range(8):
        sentences[:, index, index] = 1.0
    prototypes = MODULE.build_global8_prototypes(sentences)
    expected = torch.zeros(768)
    expected[:8] = 1.0
    expected = torch.nn.functional.normalize(expected, dim=0)
    assert torch.allclose(prototypes[0], expected)
    assert torch.allclose(prototypes.norm(dim=1), torch.ones(200))


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
