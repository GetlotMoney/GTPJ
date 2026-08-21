from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
ABLATION = ROOT / "experiments" / "v5" / "ablation" / "ABLATION-014_tg_vpr_h1_components"
STANDALONE = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-024_tg_vpr_h1"
sys.path.insert(0, str(STANDALONE))
sys.path.insert(0, str(ABLATION))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODEL = load("h1_ablation_model", ABLATION / "ablation_model.py")
TRAIN = load("h1_ablation_train", ABLATION / "train.py")
BASE = load("h1_standalone_model", STANDALONE / "tg_vpr_h1_model.py")


def make(mode):
    generator = torch.Generator().manual_seed(1401)
    sentences = torch.randn(200, 8, 768, generator=generator)
    classes = torch.tensor([class_id for class_id in range(200) if class_id % 4 != 0])
    centroids = torch.randn(150, 768, generator=generator)
    return MODEL.TGVPRH1Ablation(
        sentences, classes, centroids,
        dropout=0.0, inner_ratio=0.35, outer_ratio=0.65, temperature=0.07,
        ablation_mode=mode,
    )


def test_all_four_conditions_preserve_shape_and_unseen_mean8():
    for mode in MODEL.TGVPRH1Ablation.MODES:
        model = make(mode)
        model.eval()
        unseen = torch.arange(200)[~torch.isin(torch.arange(200), model.adapted_classes)]
        assert model.prototypes().shape == (200, 768)
        assert torch.equal(
            model.prototypes().index_select(0, unseen),
            model.base_prototypes().index_select(0, unseen),
        )


def test_full_condition_is_exact_standalone_h1():
    full = make("full_h1_learned_weights")
    base = BASE.TGVPRH1(
        full.sentence_embeds, full.adapted_classes, full.visual_centroids,
        dropout=0.0, inner_ratio=0.35, outer_ratio=0.65, temperature=0.07,
    )
    base.load_state_dict(full.state_dict(), strict=True)
    full.eval(); base.eval()
    assert torch.equal(full.prototypes(), base.prototypes())


def test_fixed_equal_does_not_train_group_logits_and_differs_from_single_group():
    fixed = make("three_group_fixed_equal_value")
    single = make("single_group_value")
    single.load_state_dict(fixed.state_dict(), strict=True)
    images = torch.randn(6, 768, generator=torch.Generator().manual_seed(22))
    loss = torch.nn.functional.cross_entropy(
        fixed.logits(images, fixed.adapted_classes), torch.arange(6)
    )
    loss.backward()
    assert fixed.semantic_group_logits.grad is None
    fixed.eval(); single.eval()
    assert not torch.allclose(fixed.prototypes(), single.prototypes())


def test_no_value_bypasses_value_parameters():
    model = make("three_group_no_value")
    images = torch.randn(6, 768, generator=torch.Generator().manual_seed(23))
    loss = torch.nn.functional.cross_entropy(
        model.logits(images, model.adapted_classes), torch.arange(6)
    )
    loss.backward()
    assert model.tg_value_projection.weight.grad is None
    assert model.logit_scale.grad is not None


def test_single_and_three_group_value_use_equal_norm_outer_base():
    single = make("single_group_value")
    fixed = make("three_group_fixed_equal_value")
    _, single_base, _ = single.prototype_components()
    _, fixed_base, _ = fixed.prototype_components()
    classes = single.adapted_classes
    expected = torch.full((150,), 1.0 - single.outer_ratio)
    assert torch.allclose(single_base.index_select(0, classes).norm(dim=-1), expected)
    assert torch.allclose(fixed_base.index_select(0, classes).norm(dim=-1), expected)


def test_condition_run_mapping_and_config_hash():
    config, digest = TRAIN.load_config(ABLATION / "config.yaml")
    assert digest == TRAIN.EXPECTED_CONFIG_SHA256
    expected = {
        "SINGLE-GROUP-VALUE": "RUN-001",
        "THREE-GROUP-NO-VALUE": "RUN-002",
        "THREE-GROUP-FIXED-EQUAL-VALUE": "RUN-003",
        "FULL-H1-LEARNED-WEIGHTS": "RUN-004",
    }
    for condition, run_id in expected.items():
        TRAIN.verify_run_identity(config, condition, run_id, Path(f"D:/out/{run_id}"))
