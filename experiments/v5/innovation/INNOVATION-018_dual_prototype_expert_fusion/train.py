"""Train and score-search split-aware dual prototype expert fusion on CUB."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import scipy.io as sio

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
import torch.nn.functional as F
import yaml
from torch.utils.data import DataLoader, TensorDataset


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.v5_cub_data import load_v5_cub_split  # noqa: E402

from dpef_model import (  # noqa: E402
    SharedPSE,
    UniformSeenPrototypeExpert,
    fused_prototypes,
    normalized_sentences,
)


EXPERIMENT_ID = "V5-INNOVATION-018"
RUN_ID = "RUN-001"
EXPECTED_CONFIG_SHA256 = "da2afe100306983b8f799be980790f9355068602c99d6c3c7d16fd719b264ca0"
EXPECTED_SOURCE_COMMIT = "acd5f6420f5260d9b2ace4885298930445eca4bf"
EXPECTED_SOURCE_CHECKPOINT_SHA256 = (
    "f83adac761d9a8e5f4df1864a38fd427dac7c1fe2cf215697155d959dd71035e"
)
EXPECTED_ROLES = (
    "beak",
    "head_features",
    "body_plumage",
    "wings",
    "tail",
    "legs",
    "overall_appearance",
    "unique_discriminative_features",
)
RUN_DIR_SUFFIX = ("runs", "v5", "innovation", EXPERIMENT_ID, RUN_ID)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tensor(tensor: torch.Tensor) -> str:
    payload = tensor.detach().cpu().contiguous().numpy().tobytes()
    return hashlib.sha256(payload).hexdigest()


def get_clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("could not resolve one full Git commit")
    dirty = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"], text=True
    ).strip()
    if dirty:
        raise ValueError("formal training requires a clean worktree")
    return commit


def verify_expected_commit(actual: str, expected: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError("--expected-commit must be one full lowercase SHA")
    if actual != expected:
        raise ValueError(f"current commit {actual} does not match {expected}")


def git_worktree_roots() -> tuple[Path, ...]:
    output = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"],
        text=True,
    )
    roots = tuple(
        Path(line.removeprefix("worktree ")).resolve()
        for line in output.splitlines()
        if line.startswith("worktree ")
    )
    if not roots:
        raise RuntimeError("git did not report a worktree root")
    return roots


def validate_run_dir(run_dir: Path) -> Path:
    resolved = run_dir.resolve()
    for root in git_worktree_roots():
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise ValueError("formal output must be outside every Git worktree")
    if tuple(resolved.parts[-len(RUN_DIR_SUFFIX) :]) != RUN_DIR_SUFFIX:
        raise ValueError(
            "--run-dir must end with runs/v5/innovation/"
            f"{EXPERIMENT_ID}/{RUN_ID}"
        )
    if resolved.exists():
        raise FileExistsError(f"refusing to reuse output directory: {resolved}")
    return resolved


def load_config(path: Path) -> tuple[dict, str]:
    actual_sha256 = sha256_file(path)
    if actual_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError(
            "config SHA-256 does not match the reviewed config: " + actual_sha256
        )
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping")
    if config.get("experiment_id") != EXPERIMENT_ID or config.get("run_id") != RUN_ID:
        raise ValueError("experiment/run identity mismatch")
    if config.get("dataset") != "CUB":
        raise ValueError("this entry only accepts CUB")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order does not match the frozen eight-role contract")
    if config.get("selection_protocol") != "official_test_score_search":
        raise ValueError("selection_protocol must disclose official test score search")
    if config.get("not_confirmation_evidence") is not True:
        raise ValueError("score search must be marked not_confirmation_evidence")
    return config, actual_sha256


def resolve_data_paths(config: dict) -> dict[str, Path]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing experiment input: " + ", ".join(missing))
    return paths


def verify_data_contract(config: dict, paths: dict[str, Path]) -> dict[str, str]:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every data input exactly once")
    actual = {name: sha256_file(path) for name, path in paths.items()}
    mismatches = [name for name in paths if actual[name] != expected[name]]
    if mismatches:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatches))
    split_data = sio.loadmat(paths["att_splits"])
    raw_names = split_data.get("allclasses_names")
    if raw_names is None or tuple(raw_names.shape) != (200, 1):
        raise ValueError("att_splits allclasses_names must have shape [200, 1]")
    names = [str(item[0][0]) for item in raw_names]
    serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    class_order_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if class_order_sha256 != config.get("class_order_sha256"):
        raise ValueError("xlsa17 class order SHA-256 mismatch")
    return actual


def load_training_class_split(
    paths: dict[str, Path], train_labels: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    res101 = sio.loadmat(paths["res101"])
    splits = sio.loadmat(paths["att_splits"])
    labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    train_indices = torch.from_numpy(splits["trainval_loc"].squeeze() - 1).long()
    seen_indices = torch.from_numpy(splits["test_seen_loc"].squeeze() - 1).long()
    unseen_indices = torch.from_numpy(splits["test_unseen_loc"].squeeze() - 1).long()
    expected_train = labels[train_indices]
    if not torch.equal(expected_train, train_labels.detach().cpu().long()):
        raise ValueError("train cache labels do not match xlsa17 trainval_loc")
    seenclasses = torch.unique(expected_train, sorted=True)
    if not torch.equal(
        seenclasses, torch.unique(labels[seen_indices], sorted=True)
    ):
        raise ValueError("train and test_seen class sets differ")
    unseenclasses = torch.unique(labels[unseen_indices], sorted=True)
    if torch.isin(seenclasses, unseenclasses).any():
        raise ValueError("seen and unseen class sets overlap")
    if seenclasses.numel() != 150 or unseenclasses.numel() != 50:
        raise ValueError("CUB split must contain 150 seen and 50 unseen classes")
    return seenclasses, unseenclasses


def load_source_shared_pse(
    checkpoint_path: Path,
    sentence_embeds: torch.Tensor,
    device: torch.device,
) -> tuple[SharedPSE, dict]:
    if not checkpoint_path.is_file():
        raise FileNotFoundError(f"source checkpoint is missing: {checkpoint_path}")
    actual_sha256 = sha256_file(checkpoint_path)
    if actual_sha256 != EXPECTED_SOURCE_CHECKPOINT_SHA256:
        raise ValueError("source SharedPSE checkpoint SHA-256 mismatch")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    required = {"model", "condition", "config", "code_commit", "best_epoch"}
    if not isinstance(checkpoint, dict) or not required.issubset(checkpoint):
        raise ValueError("source SharedPSE checkpoint is incomplete")
    if checkpoint["condition"] != "shared_pse":
        raise ValueError("source checkpoint is not the SharedPSE condition")
    if checkpoint["code_commit"] != EXPECTED_SOURCE_COMMIT:
        raise ValueError("source SharedPSE code commit mismatch")
    source_config = checkpoint["config"]
    if source_config.get("run_id") != "RUN-002" or source_config.get("condition") != "shared_pse":
        raise ValueError("source SharedPSE config identity mismatch")
    state = checkpoint["model"]
    expected_sentences = normalized_sentences(sentence_embeds)
    if not torch.equal(state["sentence_embeds"], expected_sentences):
        raise ValueError("source SharedPSE used different sentence embeddings")
    model = SharedPSE(
        state["sentence_embeds"],
        temperature=float(source_config["temperature"]),
        heads=int(source_config["shared_pse_heads"]),
        dropout=float(source_config["shared_pse_dropout"]),
        residual_cap=float(source_config["shared_pse_residual_cap"]),
    ).to(device)
    model.load_state_dict(state, strict=True)
    model.eval()
    return model, {
        "path": str(checkpoint_path.resolve()),
        "sha256": actual_sha256,
        "code_commit": checkpoint["code_commit"],
        "best_epoch": int(checkpoint["best_epoch"]),
    }


def set_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def stratified_split(
    labels: torch.Tensor, classes: torch.Tensor, fraction: float, seed: int
) -> tuple[torch.Tensor, torch.Tensor]:
    labels = labels.detach().cpu().long()
    generator = torch.Generator().manual_seed(seed)
    train_rows: list[torch.Tensor] = []
    validation_rows: list[torch.Tensor] = []
    for class_id in classes.detach().cpu().long():
        indices = torch.where(labels == class_id)[0]
        permutation = indices[torch.randperm(indices.numel(), generator=generator)]
        count = max(1, int(round(indices.numel() * fraction)))
        count = min(count, indices.numel() - 1)
        validation_rows.append(permutation[:count])
        train_rows.append(permutation[count:])
    return torch.cat(train_rows).sort().values, torch.cat(validation_rows).sort().values


def label_map(seenclasses: torch.Tensor) -> torch.Tensor:
    mapping = torch.full((200,), -1, dtype=torch.long)
    mapping[seenclasses] = torch.arange(seenclasses.numel())
    return mapping


def make_loader(
    features: torch.Tensor,
    labels: torch.Tensor,
    indices: torch.Tensor,
    seenclasses: torch.Tensor,
    batch_size: int,
    seed: int,
) -> DataLoader:
    mapping = label_map(seenclasses)
    dataset = TensorDataset(
        features[indices].float(), mapping[labels[indices].long()]
    )
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        generator=generator,
    )


def train_expert(
    config: dict,
    sentence_embeds: torch.Tensor,
    features: torch.Tensor,
    labels: torch.Tensor,
    seenclasses: torch.Tensor,
    train_indices: torch.Tensor,
    device: torch.device,
    *,
    epochs: int,
    validation_indices: torch.Tensor | None,
    emit,
) -> tuple[UniformSeenPrototypeExpert, dict]:
    seed = int(config["seed"])
    set_determinism(seed)
    model = UniformSeenPrototypeExpert(
        sentence_embeds,
        seenclasses,
        heads=int(config["uniform_heads"]),
        dropout=float(config["uniform_dropout"]),
        inner_ratio=float(config["uniform_inner_ratio"]),
        outer_ratio=float(config["uniform_outer_ratio"]),
        temperature_init=float(config["temperature_init"]),
    ).to(device)
    loader = make_loader(
        features,
        labels,
        train_indices,
        seenclasses,
        int(config["batch_size"]),
        seed,
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(config["lr_stages"][0]["lr"]),
        weight_decay=float(config["weight_decay"]),
    )
    mapping = label_map(seenclasses)
    if validation_indices is not None:
        validation_features = features[validation_indices].to(device).float()
        validation_targets = mapping[labels[validation_indices].long()].to(device)
    else:
        validation_features = None
        validation_targets = None
    history: list[dict] = []
    best_loss = float("inf")
    best_epoch = 0
    best_state = None
    current_epoch = 0
    for stage in config["lr_stages"]:
        if current_epoch >= epochs:
            break
        for group in optimizer.param_groups:
            group["lr"] = float(stage["lr"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=int(stage["epochs"]),
            eta_min=float(stage["eta_min"]),
        )
        for _ in range(int(stage["epochs"])):
            if current_epoch >= epochs:
                break
            current_epoch += 1
            model.train()
            loss_sum = 0.0
            sample_count = 0
            for batch_features, batch_targets in loader:
                batch_features = batch_features.to(device)
                batch_targets = batch_targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                ce = F.cross_entropy(
                    model.logits(batch_features, seenclasses), batch_targets
                )
                topology = model.topology_loss()
                loss = ce + float(config["topology_weight"]) * topology
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.detach().cpu()) * batch_features.size(0)
                sample_count += batch_features.size(0)
            scheduler.step()
            row = {
                "epoch": current_epoch,
                "train_loss": loss_sum / sample_count,
            }
            if validation_features is not None:
                model.eval()
                with torch.no_grad():
                    validation_loss = float(
                        F.cross_entropy(
                            model.logits(validation_features, seenclasses),
                            validation_targets,
                        ).cpu()
                    )
                row["validation_ce"] = validation_loss
                if validation_loss < best_loss:
                    best_loss = validation_loss
                    best_epoch = current_epoch
                    best_state = copy.deepcopy(model.state_dict())
                emit(
                    f"select epoch={current_epoch} train={row['train_loss']:.6f} "
                    f"val_ce={validation_loss:.6f}"
                )
            else:
                emit(
                    f"refit epoch={current_epoch}/{epochs} "
                    f"train={row['train_loss']:.6f}"
                )
            history.append(row)
    if validation_indices is not None:
        if best_state is None:
            raise RuntimeError("validation selection produced no checkpoint")
        model.load_state_dict(best_state)
    return model, {
        "history": history,
        "best_epoch": best_epoch,
        "best_validation_ce": None if best_state is None else best_loss,
    }


def per_class_accuracy(
    labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor
) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not bool(mask.any()):
            raise ValueError(f"evaluation cache has no class {int(class_id)}")
        values.append((predictions[mask] == class_id).float().mean())
    return float(torch.stack(values).mean())


@torch.no_grad()
def evaluate_prototypes(
    prototypes: torch.Tensor,
    seen_features: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_features: torch.Tensor,
    unseen_labels: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    device: torch.device,
) -> dict[str, float]:
    prototypes = prototypes.to(device)
    seen_logits = F.normalize(seen_features.to(device).float(), dim=-1) @ prototypes.T
    unseen_logits = F.normalize(unseen_features.to(device).float(), dim=-1) @ prototypes.T
    seen_predictions = seen_logits.argmax(dim=1).cpu()
    unseen_predictions = unseen_logits.argmax(dim=1).cpu()
    unseen_ids = unseenclasses.to(device)
    zsl_predictions = unseenclasses[
        unseen_logits[:, unseen_ids].argmax(dim=1).cpu()
    ]
    seen_accuracy = per_class_accuracy(seen_labels, seen_predictions, seenclasses)
    unseen_accuracy = per_class_accuracy(
        unseen_labels, unseen_predictions, unseenclasses
    )
    zsl_accuracy = per_class_accuracy(unseen_labels, zsl_predictions, unseenclasses)
    harmonic = (
        2.0 * seen_accuracy * unseen_accuracy / (seen_accuracy + unseen_accuracy)
        if seen_accuracy + unseen_accuracy
        else 0.0
    )
    return {
        "U": 100.0 * unseen_accuracy,
        "S": 100.0 * seen_accuracy,
        "H": 100.0 * harmonic,
        "ZS": 100.0 * zsl_accuracy,
    }


def score_search(
    config: dict,
    strong: torch.Tensor,
    shared: torch.Tensor,
    raw: torch.Tensor,
    official: dict[str, torch.Tensor],
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    device: torch.device,
) -> tuple[dict, list[dict]]:
    rows: list[dict] = []
    for seen_blend in config["seen_blend_grid"]:
        for unseen_blend in config["unseen_blend_grid"]:
            prototypes = fused_prototypes(
                strong,
                shared,
                raw,
                seenclasses,
                unseenclasses,
                seen_blend=float(seen_blend),
                unseen_blend=float(unseen_blend),
            )
            metrics = evaluate_prototypes(
                prototypes,
                official["seen_features"],
                official["seen_labels"],
                official["unseen_features"],
                official["unseen_labels"],
                seenclasses,
                unseenclasses,
                device,
            )
            rows.append(
                {
                    "seen_blend": float(seen_blend),
                    "unseen_blend": float(unseen_blend),
                    "metrics_percent": metrics,
                }
            )
    best = max(
        rows,
        key=lambda row: (
            row["metrics_percent"]["H"],
            -abs(row["metrics_percent"]["U"] - row["metrics_percent"]["S"]),
            -row["seen_blend"],
            -row["unseen_blend"],
        ),
    )
    return best, rows


def run(
    config_path: Path,
    run_dir: Path,
    expected_commit: str,
    source_checkpoint: Path,
) -> dict:
    run_dir = validate_run_dir(run_dir)
    code_commit = get_clean_commit()
    verify_expected_commit(code_commit, expected_commit)
    config, config_sha256 = load_config(config_path)
    paths = resolve_data_paths(config)
    input_sha256 = verify_data_contract(config, paths)

    run_dir.mkdir(parents=True, exist_ok=False)
    log_handle = (run_dir / "training.log").open(
        "x", encoding="utf-8", buffering=1
    )

    def emit(message: str) -> None:
        print(message, flush=True)
        log_handle.write(message + "\n")

    try:
        emit(f"code_commit={code_commit}")
        emit(f"config_sha256={config_sha256}")
        emit(f"seed={int(config['seed'])}")
        emit("official_test_policy=score_search_after_training_checkpoint_freeze")
        device = torch.device(config["device"])
        if device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("formal experiment requires a visible CUDA device")

        training = {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in ("sentence_embeds", "train_features", "train_labels")
        }
        seenclasses, unseenclasses = load_training_class_split(
            paths, training["train_labels"]
        )
        source_model, source_identity = load_source_shared_pse(
            source_checkpoint, training["sentence_embeds"], device
        )

        train_indices, validation_indices = stratified_split(
            training["train_labels"],
            seenclasses,
            float(config["validation_fraction"]),
            int(config["seed"]),
        )
        selection_model, selection = train_expert(
            config,
            training["sentence_embeds"],
            training["train_features"],
            training["train_labels"],
            seenclasses,
            train_indices,
            device,
            epochs=int(config["max_epochs"]),
            validation_indices=validation_indices,
            emit=emit,
        )
        selected_epoch = int(selection["best_epoch"])
        if selected_epoch <= 0:
            raise RuntimeError("selected epoch is invalid")
        del selection_model
        full_indices = torch.arange(training["train_labels"].numel())
        strong_model, refit = train_expert(
            config,
            training["sentence_embeds"],
            training["train_features"],
            training["train_labels"],
            seenclasses,
            full_indices,
            device,
            epochs=selected_epoch,
            validation_indices=None,
            emit=emit,
        )
        strong_model.eval()
        source_model.eval()
        with torch.no_grad():
            strong = strong_model.prototypes()
            shared = source_model.prototypes()
            raw = strong_model.base_prototypes()
            strong_seen_cosine = float(
                F.cosine_similarity(strong[seenclasses.to(device)], raw[seenclasses.to(device)], dim=-1)
                .mean()
                .cpu()
            )
            shared_unseen_cosine = float(
                F.cosine_similarity(shared[unseenclasses.to(device)], raw[unseenclasses.to(device)], dim=-1)
                .mean()
                .cpu()
            )

        checkpoint_path = run_dir / "model_best.pth"
        torch.save(
            {
                "strong_model": {
                    name: value.detach().cpu()
                    for name, value in strong_model.state_dict().items()
                },
                "strong_prototypes": strong.detach().cpu(),
                "raw_prototypes": raw.detach().cpu(),
                "shared_source_identity": source_identity,
                "code_commit": code_commit,
                "config": config,
                "selected_epoch_by_internal_validation": selected_epoch,
            },
            checkpoint_path,
        )

        # Official test tensors are loaded only after training selection, full refit,
        # source binding, diagnostics, and checkpoint publication are complete.
        official = {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in (
                "seen_features",
                "seen_labels",
                "unseen_features",
                "unseen_labels",
            )
        }
        checked_seenclasses, checked_unseenclasses = load_v5_cub_split(
            paths["res101"],
            paths["att_splits"],
            training["train_labels"],
            official["seen_labels"],
            official["unseen_labels"],
            "cpu",
        )
        if not torch.equal(seenclasses, checked_seenclasses) or not torch.equal(
            unseenclasses, checked_unseenclasses
        ):
            raise RuntimeError("official class sets differ from the training split")
        best, grid = score_search(
            config,
            strong,
            shared,
            raw,
            official,
            seenclasses,
            unseenclasses,
            device,
        )
        metrics = best["metrics_percent"]
        result = {
            "experiment_id": EXPERIMENT_ID,
            "run_id": RUN_ID,
            "status": "completed_score_search",
            "decision": "keep_score_search" if metrics["H"] >= 75.0 else "stop_no_gain",
            "not_confirmation_evidence": True,
            "selection_protocol": "official_test_score_search",
            "code_commit": code_commit,
            "config_sha256": config_sha256,
            "seed": int(config["seed"]),
            "input_sha256": input_sha256,
            "source_shared_pse": source_identity,
            "validation_indices_sha256": sha256_tensor(validation_indices.long()),
            "selected_epoch_by_seen_internal_validation_ce": selected_epoch,
            "best_validation_ce": selection["best_validation_ce"],
            "best_fusion": best,
            "metrics_percent": metrics,
            "score_search_grid": grid,
            "diagnostics": {
                "strong_seen_base_cosine_mean": strong_seen_cosine,
                "shared_unseen_base_cosine_mean": shared_unseen_cosine,
                "score_grid_size": len(grid),
            },
            "selection_history": selection["history"],
            "refit_history": refit["history"],
            "checkpoint_sha256": sha256_file(checkpoint_path),
        }
        with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        with (run_dir / "result.yaml").open("x", encoding="utf-8") as handle:
            yaml.safe_dump(result, handle, allow_unicode=True, sort_keys=False)
        emit(
            "U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(
                **metrics
            )
        )
        emit(
            f"best_seen_blend={best['seen_blend']:.2f} "
            f"best_unseen_blend={best['unseen_blend']:.2f}"
        )
        return result
    finally:
        log_handle.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    args = parser.parse_args()
    run(
        args.config.resolve(),
        args.run_dir.resolve(),
        args.expected_commit,
        args.source_checkpoint.resolve(),
    )


if __name__ == "__main__":
    main()
