"""Standard GZSL training-entry template for GTPJ module trials.

This is a trial-local scaffold, not runnable baseline evidence by itself.
Copy it into a trial branch only after the owner has named the base version
and `module_source.md` explains the paper/source-to-code mapping.

Protected semantics:
- dataset split stays xlsa17/att_splits.mat by default
- train uses seen classes only
- evaluation uses seen + unseen classes
- logits stay [B (image/sample count), C (class count)]
- metrics stay U, S, H, ZS under standard_gzsl_u_s_h_zs
- best_observed_H is a run-local observation until confirmation evidence exists
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import torch
import torch.nn as nn
import yaml


@dataclass(frozen=True)
class StandardGZSLTrainingRun:
    """Owner-visible run contract for one formal module-trial training entry."""

    trial_id: str
    base_version: str
    base_code_tag: str
    config_path: Path
    output_dir: Path
    seed: int = 5
    device: str = "cuda:0"
    dataset_name: str = "CUB"
    split_name: str = "xlsa17/att_splits.mat"
    evaluation_protocol: str = "standard_gzsl_u_s_h_zs"
    module_source_path: str = "module_source.md"
    module_template_family: str = ""
    max_epochs: int = 0
    eval_every_epochs: int = 1
    top_k_checkpoints: int = 3

    def assert_static_contract(self) -> None:
        if not self.base_version or not self.base_code_tag:
            raise ValueError("formal paper-to-experiment runs require base_version and base_code_tag")
        if self.evaluation_protocol != "standard_gzsl_u_s_h_zs":
            raise ValueError("normal module trials must keep standard_gzsl_u_s_h_zs")
        if self.dataset_name != "CUB" or self.split_name != "xlsa17/att_splits.mat":
            raise ValueError("non-CUB or non-xlsa17 runs need an explicit high-risk dataset note")
        if self.max_epochs <= 0:
            raise ValueError("max_epochs must be recorded before Runner starts")


@dataclass
class GZSLMetrics:
    """Standard metric packet returned by evaluation."""

    U: float
    S: float
    H: float
    ZS: float
    epoch: int


@dataclass(frozen=True)
class LossPack:
    """Training-step output with an explicit scalar optimization loss."""

    loss: torch.Tensor
    extras: Mapping[str, torch.Tensor] | None = None

    def assert_valid(self) -> None:
        if not isinstance(self.loss, torch.Tensor):
            raise TypeError("LossPack.loss must be a torch.Tensor")
        if self.loss.ndim != 0:
            raise ValueError("LossPack.loss must be a scalar tensor")


def flatten_yaml_values(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Accept both plain YAML and GTPJ `{key: {value: ...}}` config style."""
    flat: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping) and "value" in value:
            flat[key] = value["value"]
        else:
            flat[key] = value
    return flat


def load_trial_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, Mapping):
        raise ValueError(f"config must be a mapping: {path}")
    return flatten_yaml_values(loaded)


def build_run_from_config(config_path: str | Path, output_dir: str | Path) -> StandardGZSLTrainingRun:
    """Build the owner-visible run contract from trial-local config."""
    path = Path(config_path)
    cfg = load_trial_config(path)
    run = StandardGZSLTrainingRun(
        trial_id=str(cfg.get("trial_id", "")),
        base_version=str(cfg.get("base_version", "")),
        base_code_tag=str(cfg.get("base_code_tag", "")),
        config_path=path,
        output_dir=Path(output_dir),
        seed=int(cfg.get("random_seed", cfg.get("seed", 5))),
        device=str(cfg.get("device", "cuda:0")),
        dataset_name=str(cfg.get("dataset", "CUB")),
        split_name=str(cfg.get("dataset_split", "xlsa17/att_splits.mat")),
        evaluation_protocol=str(cfg.get("evaluation_protocol", "standard_gzsl_u_s_h_zs")),
        module_source_path=str(cfg.get("module_source", "module_source.md")),
        module_template_family=str(cfg.get("module_template_family", "")),
        max_epochs=int(cfg.get("epochs", cfg.get("max_epochs", 0))),
        eval_every_epochs=int(cfg.get("eval_every_epochs", 1)),
        top_k_checkpoints=int(cfg.get("top_k_checkpoints", 3)),
    )
    run.assert_static_contract()
    return run


def set_reproducibility(seed: int) -> None:
    """Set minimum reproducibility knobs; use stricter project helpers when available."""
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)


def harmonic_mean(seen_acc: float, unseen_acc: float) -> float:
    denom = float(seen_acc) + float(unseen_acc)
    return 0.0 if denom <= 0 else (2.0 * float(seen_acc) * float(unseen_acc)) / denom


def require_1d_long_tensor(value: Any, name: str) -> torch.Tensor:
    """Protected class lists must already be torch tensors from the approved dataloader."""
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor; convert numpy arrays in the dataloader adapter")
    tensor = value.long().flatten()
    if tensor.ndim != 1:
        raise ValueError(f"{name} must flatten to a 1-D class-index tensor")
    return tensor


def assert_standard_gzsl_state(dataloader: Any) -> None:
    """Read protected state from dataloader; do not hand-write class order."""
    required = ["seenclasses", "unseenclasses", "ntrain_class", "ntest_class"]
    missing = [name for name in required if not hasattr(dataloader, name)]
    if missing:
        raise ValueError(f"dataloader missing GZSL protected fields: {missing}")
    seen = require_1d_long_tensor(dataloader.seenclasses, "dataloader.seenclasses")
    unseen = require_1d_long_tensor(dataloader.unseenclasses, "dataloader.unseenclasses")
    if seen.numel() == 0 or unseen.numel() == 0:
        raise ValueError("GZSL requires both seen and unseen classes")
    if set(seen.detach().cpu().tolist()) & set(unseen.detach().cpu().tolist()):
        raise ValueError("seen/unseen class sets must be disjoint")


def assert_logits_shape(logits: torch.Tensor, batch_size: int, class_count: int) -> None:
    expected = (int(batch_size), int(class_count))
    actual = tuple(logits.shape)
    if actual != expected:
        raise ValueError(
            f"logits must be [B (image/sample count), C (class count)]={expected}, got {actual}"
        )


def assert_standard_gzsl_eval(metrics: Mapping[str, float], dataloader: Any) -> None:
    required_metrics = {"U", "S", "H", "ZS"}
    missing = sorted(required_metrics.difference(metrics.keys()))
    if missing:
        raise ValueError(f"standard GZSL eval missing metrics: {missing}")
    assert_standard_gzsl_state(dataloader)


def load_standard_gzsl_data(run: StandardGZSLTrainingRun, cfg: Mapping[str, Any]) -> Any:
    """TODO: instantiate the existing project dataloader without changing split semantics."""
    raise NotImplementedError("wire to tools.dataset.CUBDataLoader or the approved dataset adapter")


def build_frozen_clip(run: StandardGZSLTrainingRun, cfg: Mapping[str, Any]) -> nn.Module:
    """TODO: load CLIP/backbone, set eval mode, and freeze all backbone parameters."""
    raise NotImplementedError("wire to the project backbone loader")


def build_trial_model(
    run: StandardGZSLTrainingRun,
    cfg: Mapping[str, Any],
    dataloader: Any,
    frozen_backbone: nn.Module,
) -> nn.Module:
    """TODO: build the base model plus one selected trial module family."""
    raise NotImplementedError("wire to model builder; default switch must be off")


def build_optimizer(run: StandardGZSLTrainingRun, cfg: Mapping[str, Any], model: nn.Module) -> torch.optim.Optimizer:
    """TODO: keep optimizer config trial-local and record it in implementation.md."""
    raise NotImplementedError("wire to the approved optimizer and scheduler setup")


def iter_train_batches(run: StandardGZSLTrainingRun, dataloader: Any, cfg: Mapping[str, Any]) -> Any:
    """TODO: yield seen-class training batches only."""
    raise NotImplementedError("wire to dataloader.next_batch or DataLoader iteration")


def train_one_step(
    run: StandardGZSLTrainingRun,
    batch: Any,
    model: nn.Module,
    frozen_backbone: nn.Module,
    cfg: Mapping[str, Any],
) -> LossPack:
    """TODO: compute one scalar training loss; lambda=0 must match base loss.

    Do not call backward or optimizer.step here. `run_training_entry` owns the
    shared optimization order so strict-template trials cannot silently skip it.
    """
    raise NotImplementedError("wire to model.compute_loss and return LossPack(loss=...)")


def evaluate_standard_gzsl(
    run: StandardGZSLTrainingRun,
    dataloader: Any,
    model: nn.Module,
    frozen_backbone: nn.Module,
) -> GZSLMetrics:
    """TODO: call the existing standard eval path and return U/S/H/ZS."""
    raise NotImplementedError("wire to tools.helper_func.eval_zs_gzsl")


def record_checkpoint_reference(
    run: StandardGZSLTrainingRun,
    epoch: int,
    metrics: GZSLMetrics,
    model: nn.Module,
) -> None:
    """TODO: write checkpoint/artifact pointers; enforce run.top_k_checkpoints retention outside Git."""
    raise NotImplementedError("wire to warehouse artifact registration")


def build_owner_visible_summary(run: StandardGZSLTrainingRun, best: GZSLMetrics) -> dict[str, Any]:
    """Build the minimal owner-visible payload that the concrete writer must persist."""
    return {
        "run": asdict(run),
        "best_observed_H": float(best.H),
        "best_observed": asdict(best),
        "confirmation_status": "unconfirmed",
    }


def write_owner_visible_summary(run: StandardGZSLTrainingRun, best: GZSLMetrics) -> None:
    """TODO: persist result.yaml/result.md/quality_check.md from build_owner_visible_summary()."""
    summary = build_owner_visible_summary(run, best)
    raise NotImplementedError(f"write trial-local summary files from: {summary}")


def run_training_entry(config_path: str | Path, output_dir: str | Path) -> GZSLMetrics:
    """Complete formal training skeleton: config -> data -> model -> train -> eval -> artifacts."""
    run = build_run_from_config(config_path, output_dir)
    cfg = load_trial_config(run.config_path)
    set_reproducibility(run.seed)

    dataloader = load_standard_gzsl_data(run, cfg)
    assert_standard_gzsl_state(dataloader)
    frozen_backbone = build_frozen_clip(run, cfg)
    model = build_trial_model(run, cfg, dataloader, frozen_backbone).to(run.device)
    optimizer = build_optimizer(run, cfg, model)

    best = GZSLMetrics(U=0.0, S=0.0, H=0.0, ZS=0.0, epoch=0)
    for epoch in range(1, run.max_epochs + 1):
        model.train()
        for batch in iter_train_batches(run, dataloader, cfg):
            optimizer.zero_grad(set_to_none=True)
            loss_pack = train_one_step(run, batch, model, frozen_backbone, cfg)
            loss_pack.assert_valid()
            loss_pack.loss.backward()
            optimizer.step()

        if epoch % run.eval_every_epochs == 0:
            metrics = evaluate_standard_gzsl(run, dataloader, model, frozen_backbone)
            assert_standard_gzsl_eval(asdict(metrics), dataloader)
            if metrics.H > best.H:
                best = metrics
                record_checkpoint_reference(run, epoch, metrics, model)

    write_owner_visible_summary(run, best)
    return best
