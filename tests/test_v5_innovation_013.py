import importlib.util
import tempfile
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-013_shared_pse_global8" / "train.py"
SPEC = importlib.util.spec_from_file_location("shared_pse", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sentence_cache():
    generator = torch.Generator().manual_seed(3)
    return torch.randn(200, 8, 768, generator=generator)


def test_zero_gate_is_exact_global8_baseline():
    model = MODULE.SharedPSE(sentence_cache(), 4, 0.0, 0.35, 0.05)
    model.eval()
    assert torch.allclose(model.prototypes(), model.base_prototypes(), atol=1e-6)


def test_shared_pse_adapts_seen_and_unseen_without_class_parameters():
    model = MODULE.SharedPSE(sentence_cache(), 4, 0.0, 0.35, 0.05)
    with torch.no_grad():
        model.residual_gate.fill_(0.5)
    adapted = model.prototypes()
    base = model.base_prototypes()
    assert not torch.allclose(adapted[:150], base[:150])
    assert not torch.allclose(adapted[150:], base[150:])
    assert all(tuple(parameter.shape)[:1] != (200,) for parameter in model.parameters())


def test_stratified_split_is_disjoint_and_keeps_every_class():
    labels = torch.arange(6).repeat_interleave(10)
    classes = torch.arange(6)
    train_indices, validation_indices = MODULE.stratified_train_validation_split(
        labels, classes, 0.2, 5
    )
    assert not torch.isin(train_indices, validation_indices).any()
    assert set(labels[train_indices].tolist()) == set(classes.tolist())
    assert set(labels[validation_indices].tolist()) == set(classes.tolist())


def test_frozen_config_and_expected_commit_are_enforced():
    config_path = SCRIPT.parent / "config.yaml"
    config, config_sha256 = MODULE.load_config(config_path)
    assert config_sha256 == MODULE.EXPECTED_CONFIG_SHA256
    assert config["max_epochs"] == 100

    with tempfile.TemporaryDirectory() as temporary_directory:
        changed_config = Path(temporary_directory) / "config.yaml"
        changed_config.write_text(
            config_path.read_text(encoding="utf-8").replace(
                "learning_rate: 0.0001", "learning_rate: 0.0002"
            ),
            encoding="utf-8",
        )
        try:
            MODULE.load_config(changed_config)
        except ValueError as error:
            assert "config SHA-256" in str(error)
        else:
            raise AssertionError("a changed config must be rejected")

    commit = "a" * 40
    MODULE.verify_expected_commit(commit, commit)
    try:
        MODULE.verify_expected_commit(commit, "b" * 40)
    except ValueError as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("a different commit must be rejected")
