from __future__ import annotations

import importlib.util
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-013_shared_pse_global8"
    / "train.py"
)
SPEC = importlib.util.spec_from_file_location("local_dcra_train", TRAIN_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def make_inputs():
    generator = torch.Generator().manual_seed(1705)
    sentences = torch.randn(200, 8, 768, generator=generator)
    classes = torch.arange(150)
    centroids = torch.randn(150, 768, generator=generator)
    return sentences, classes, centroids


def make_model(mode: str, dcra_mix: float = 0.2):
    sentences, classes, centroids = make_inputs()
    return MODULE.StrongRolePSE(
        sentences,
        classes,
        centroids,
        mode=mode,
        dropout=0.0,
        inner_ratio=0.35,
        outer_ratio=0.65,
        dcra_mix=dcra_mix,
        temperature=0.05,
    )


def test_dcra_weights_are_normalized_bounded_and_never_self_rivals():
    model = make_model("dcra")
    _, diagnostics = model.prototypes(return_diagnostics=True)
    weights = diagnostics["role_weights"]
    rivals = diagnostics["rival_class_ids"]
    assert torch.allclose(weights.sum(dim=1), torch.ones(150), atol=1e-6)
    assert float(weights.min().detach()) >= 0.1 - 1e-6
    assert float(weights.max().detach()) <= 0.3 + 1e-6
    assert not (rivals == torch.arange(150).view(-1, 1)).any()


def test_dcra_zero_mix_exactly_reduces_to_uniform_and_unseen_stays_mean8():
    uniform = make_model("uniform")
    dcra_zero = make_model("dcra", dcra_mix=0.0)
    dcra_zero.load_state_dict(uniform.state_dict(), strict=False)
    uniform.eval()
    dcra_zero.eval()
    assert torch.allclose(uniform.prototypes(), dcra_zero.prototypes(), atol=1e-6)
    assert torch.equal(
        uniform.prototypes()[150:], uniform.base_prototypes()[150:]
    )


def test_base_and_role_components_reconstruct_logits():
    model = make_model("dcra")
    model.eval()
    images = torch.randn(3, 768, generator=torch.Generator().manual_seed(9))
    base, roles = model.logit_components(images)
    assert torch.allclose(base + roles.sum(dim=-1), model.logits(images), atol=2e-5)


def test_topology_and_ce_reach_strong_value_path_but_not_centroids():
    model = make_model("dcra")
    images = torch.randn(4, 768, generator=torch.Generator().manual_seed(11))
    targets = torch.tensor([0, 1, 2, 3])
    loss = torch.nn.functional.cross_entropy(model.logits(images, torch.arange(150)), targets)
    loss = loss + 0.1 * model.topology_loss()
    loss.backward()
    assert model.value_projection.weight.grad is not None
    assert float(model.value_projection.weight.grad.abs().sum()) > 0.0
    assert model.visual_centroids.grad is None


def test_visual_centroids_use_only_supplied_training_indices():
    features = torch.eye(6, 768)
    labels = torch.tensor([0, 0, 1, 1, 0, 1])
    centroids = MODULE.frozen_visual_centroids(
        features, labels, torch.tensor([0, 2]), torch.tensor([0, 1])
    )
    assert torch.equal(centroids[0], features[0])
    assert torch.equal(centroids[1], features[2])
