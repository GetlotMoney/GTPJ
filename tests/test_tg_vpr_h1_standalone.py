from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import tempfile

import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-024_tg_vpr_h1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODEL = load_module("tg_vpr_h1_model", MODULE_DIR / "tg_vpr_h1_model.py")
TRAIN = load_module("tg_vpr_h1_train", MODULE_DIR / "train.py")


def make_model(dropout: float = 0.0):
    generator = torch.Generator().manual_seed(2401)
    sentences = torch.randn(200, 8, 768, generator=generator)
    classes = torch.tensor([class_id for class_id in range(200) if class_id % 4 != 0])
    centroids = torch.randn(150, 768, generator=generator)
    return MODEL.TGVPRH1(
        sentences,
        classes,
        centroids,
        dropout=dropout,
        inner_ratio=0.35,
        outer_ratio=0.65,
        temperature=0.07,
    )


def test_standalone_shapes_groups_and_unseen_boundary():
    model = make_model()
    model.eval()
    groups = model.semantic_group_vectors()
    prototypes = model.prototypes()
    unseen = torch.arange(200)[~torch.isin(torch.arange(200), model.adapted_classes)]
    assert groups.shape == (200, 3, 768)
    assert prototypes.shape == (200, 768)
    assert torch.allclose(groups.norm(dim=-1), torch.ones(200, 3), atol=1e-6)
    assert torch.equal(
        prototypes.index_select(0, unseen),
        model.base_prototypes().index_select(0, unseen),
    )
    assert torch.allclose(model.semantic_group_weights().sum(), torch.tensor(1.0))


def test_standalone_loss_reaches_value_path_and_group_logits():
    model = make_model()
    images = torch.randn(8, 768, generator=torch.Generator().manual_seed(31))
    targets = torch.arange(8)
    loss = F.cross_entropy(model.logits(images, model.adapted_classes), targets)
    loss = loss + 0.1 * model.topology_loss()
    loss.backward()
    assert float(model.tg_value_projection.weight.grad.abs().sum()) > 0
    assert float(model.semantic_group_logits.grad.abs().sum()) > 0


def test_standalone_logit_components_reconstruct_logits():
    model = make_model()
    model.eval()
    images = torch.randn(4, 768, generator=torch.Generator().manual_seed(47))
    base, roles = model.logit_components(images)
    assert torch.allclose(base + roles.sum(dim=-1), model.logits(images), atol=2e-5)


def test_standalone_deterministic_train_path_and_config_contract():
    config, digest = TRAIN.load_config(MODULE_DIR / "config.yaml")
    assert digest == TRAIN.EXPECTED_CONFIG_SHA256
    assert config["seed"] == 7
    assert config["epochs"] == 50
    first = TRAIN.legacy_batch_indices(
        7057, 64, torch.Generator(device="cpu").manual_seed(7)
    )
    second = TRAIN.legacy_batch_indices(
        7057, 64, torch.Generator(device="cpu").manual_seed(7)
    )
    assert torch.equal(first, second)


def test_standalone_run_identity_is_fixed():
    TRAIN.verify_run_identity("RUN-001", Path("D:/warehouse/RUN-001"))
    for run_id, output in (
        ("RUN-002", Path("D:/warehouse/RUN-002")),
        ("RUN-001", Path("D:/warehouse/not-run-001")),
    ):
        try:
            TRAIN.verify_run_identity(run_id, output)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid standalone run identity must be rejected")


def test_tee_stream_writes_console_and_training_log():
    console = io.StringIO()
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "training.log"
        with path.open("x", encoding="utf-8") as handle:
            stream = TRAIN.TeeStream(console, handle)
            stream.write("epoch=1\n")
            stream.flush()
        assert console.getvalue() == "epoch=1\n"
        assert path.read_text(encoding="utf-8") == "epoch=1\n"
