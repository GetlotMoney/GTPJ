"""Evaluate V5-INNOVATION-020 RACE without official-test selection."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import scipy.io as sio
import torch
import torch.nn.functional as F
import yaml

from race_model import CLASS_COUNT, RACE, normalized_sentences


EXPERIMENT_ID = "V5-INNOVATION-020"
RUN_ID = "RUN-001"
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
OFFICIAL_KEYS = ("seen_features", "seen_labels", "unseen_features", "unseen_labels")


@dataclass(frozen=True)
class ClassDisjointSplit:
    pseudo_seen: torch.Tensor
    pseudo_unseen: torch.Tensor
    pseudo_train_indices: torch.Tensor
    pseudo_seen_evaluation_indices: torch.Tensor
    pseudo_unseen_evaluation_indices: torch.Tensor


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_tensor(tensor: torch.Tensor) -> str:
    value = torch.as_tensor(tensor).detach().cpu().contiguous().numpy()
    return hashlib.sha256(value.tobytes()).hexdigest()


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_config(path: Path, expected_sha256: str) -> tuple[dict, str]:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(f"config SHA-256 mismatch: expected {expected_sha256}, got {actual}")
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("config must be a YAML mapping")
    if config.get("experiment_id") != EXPERIMENT_ID or config.get("run_id") != RUN_ID:
        raise ValueError("config experiment/run identity mismatch")
    if config.get("selection_protocol") != "xlsa17_100_50_validation_then_single_test":
        raise ValueError("selection protocol is not the frozen no-test protocol")
    if config.get("official_test_policy") != "load_once_after_checkpoint_no_selection":
        raise ValueError("official test policy is not frozen")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role order does not match the eight-role contract")
    expected_inputs = {
        "sentence_embeds",
        "train_features",
        "train_labels",
        "seen_features",
        "seen_labels",
        "unseen_features",
        "unseen_labels",
        "res101",
        "att_splits",
    }
    if set(config.get("inputs", {})) != expected_inputs:
        raise ValueError("config must bind exactly the nine frozen inputs")
    if set(config.get("expected_sha256", {})) != expected_inputs:
        raise ValueError("config must hash exactly the nine frozen inputs")
    return config, actual


def clean_commit(root: Path, expected_commit: str) -> str:
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=root, text=True
    ).strip()
    if status:
        raise RuntimeError("formal run requires a clean worktree")
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    if commit != expected_commit:
        raise RuntimeError(f"expected commit {expected_commit}, got {commit}")
    return commit


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def git_worktree_roots(root: Path) -> list[Path]:
    output = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"], cwd=root, text=True
    )
    return [
        Path(line.split(" ", 1)[1]).resolve()
        for line in output.splitlines()
        if line.startswith("worktree ")
    ]


def validate_run_dir(root: Path, run_dir: Path) -> Path:
    resolved = run_dir.resolve()
    for worktree in git_worktree_roots(root):
        if _is_within(resolved, worktree):
            raise ValueError("run directory must be outside every Git worktree")
    suffix = ("runs", "v5", "innovation", EXPERIMENT_ID, RUN_ID)
    if tuple(resolved.parts[-len(suffix) :]) != suffix:
        raise ValueError("run directory has the wrong Warehouse suffix")
    if resolved.exists():
        raise FileExistsError(f"run directory already exists: {resolved}")
    return resolved


def resolve_input_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"missing input: {path}")
    return path


def resolve_and_verify_inputs(
    root: Path, config: dict, keys: tuple[str, ...]
) -> tuple[dict[str, Path], dict[str, str]]:
    paths: dict[str, Path] = {}
    identities: dict[str, str] = {}
    for key in keys:
        path = resolve_input_path(root, config["inputs"][key])
        actual = sha256_file(path)
        expected = config["expected_sha256"][key]
        if actual != expected:
            raise ValueError(f"{key} SHA-256 mismatch")
        paths[key] = path
        identities[key] = actual
    return paths, identities


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def build_class_disjoint_split(
    all_labels: torch.Tensor,
    train_labels: torch.Tensor,
    trainval_loc: torch.Tensor,
    train_loc: torch.Tensor,
    val_loc: torch.Tensor,
    *,
    outer_fraction: float,
    seed: int,
) -> ClassDisjointSplit:
    all_labels = all_labels.detach().cpu().long()
    train_labels = train_labels.detach().cpu().long()
    if not torch.equal(train_labels, all_labels[trainval_loc]):
        raise ValueError("train cache labels do not match xlsa17 trainval_loc")
    pseudo_seen = torch.unique(all_labels[train_loc], sorted=True)
    pseudo_unseen = torch.unique(all_labels[val_loc], sorted=True)
    if pseudo_seen.numel() != 100 or pseudo_unseen.numel() != 50:
        raise ValueError("pseudo GZSL split must contain 100/50 classes")
    if torch.isin(pseudo_seen, pseudo_unseen).any():
        raise ValueError("pseudo seen/unseen classes overlap")
    if not 0.0 < outer_fraction < 0.5:
        raise ValueError("outer fraction must be in (0, 0.5)")

    pseudo_seen_all = torch.where(torch.isin(train_labels, pseudo_seen))[0]
    pseudo_unseen_all = torch.where(torch.isin(train_labels, pseudo_unseen))[0]
    if pseudo_seen_all.numel() != train_loc.numel():
        raise ValueError("pseudo-seen sample count differs from train_loc")
    if pseudo_unseen_all.numel() != val_loc.numel():
        raise ValueError("pseudo-unseen sample count differs from val_loc")

    generator = torch.Generator().manual_seed(seed)
    train_rows: list[torch.Tensor] = []
    evaluation_rows: list[torch.Tensor] = []
    for class_id in pseudo_seen:
        rows = torch.where(train_labels == class_id)[0]
        permutation = rows[torch.randperm(rows.numel(), generator=generator)]
        evaluation_count = max(1, int(round(rows.numel() * outer_fraction)))
        evaluation_rows.append(permutation[:evaluation_count])
        train_rows.append(permutation[evaluation_count:])
    pseudo_train = torch.cat(train_rows).sort().values
    pseudo_seen_evaluation = torch.cat(evaluation_rows).sort().values
    if torch.isin(pseudo_train, pseudo_seen_evaluation).any():
        raise RuntimeError("pseudo seen train/evaluation samples overlap")
    return ClassDisjointSplit(
        pseudo_seen=pseudo_seen,
        pseudo_unseen=pseudo_unseen,
        pseudo_train_indices=pseudo_train,
        pseudo_seen_evaluation_indices=pseudo_seen_evaluation,
        pseudo_unseen_evaluation_indices=pseudo_unseen_all,
    )


def load_protocol_split(paths: dict[str, Path], train_labels: torch.Tensor, config: dict):
    # Before checkpoint freeze, load only the variables required by the
    # class-disjoint validation protocol.  In particular, do not make the
    # res101 feature matrix or official test indices reachable in memory.
    res101 = sio.loadmat(paths["res101"], variable_names=["labels"])
    splits = sio.loadmat(
        paths["att_splits"],
        variable_names=["trainval_loc", "train_loc", "val_loc", "allclasses_names"],
    )
    all_labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    trainval_loc = torch.from_numpy(splits["trainval_loc"].squeeze() - 1).long()
    train_loc = torch.from_numpy(splits["train_loc"].squeeze() - 1).long()
    val_loc = torch.from_numpy(splits["val_loc"].squeeze() - 1).long()
    raw_names = splits.get("allclasses_names")
    if raw_names is None or tuple(raw_names.shape) != (CLASS_COUNT, 1):
        raise ValueError("att_splits allclasses_names must have shape [200, 1]")
    names = [str(item[0][0]) for item in raw_names]
    serialized_names = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    actual_class_order = hashlib.sha256(serialized_names.encode("utf-8")).hexdigest()
    if actual_class_order != config.get("class_order_sha256"):
        raise ValueError("xlsa17 class order SHA-256 mismatch")
    protocol = build_class_disjoint_split(
        all_labels,
        train_labels,
        trainval_loc,
        train_loc,
        val_loc,
        outer_fraction=float(config["pseudo_seen_evaluation_fraction"]),
        seed=int(config["split_seed"]),
    )
    formal_seen = torch.unique(train_labels.detach().cpu().long(), sorted=True)
    formal_unseen = torch.tensor(
        sorted(set(range(CLASS_COUNT)) - set(formal_seen.tolist())), dtype=torch.long
    )
    if formal_seen.numel() != 150 or formal_unseen.numel() != 50:
        raise ValueError("formal split must contain 150/50 classes")
    if torch.isin(protocol.pseudo_seen, formal_unseen).any() or torch.isin(
        protocol.pseudo_unseen, formal_unseen
    ).any():
        raise ValueError("pseudo validation classes overlap official unseen classes")
    pseudo_seen_global = trainval_loc[protocol.pseudo_seen_evaluation_indices]
    pseudo_seen_global = torch.cat(
        (pseudo_seen_global, trainval_loc[protocol.pseudo_train_indices])
    ).sort().values
    pseudo_unseen_global = trainval_loc[protocol.pseudo_unseen_evaluation_indices].sort().values
    if not torch.equal(pseudo_seen_global, train_loc.sort().values):
        raise ValueError("pseudo-seen cache rows do not exactly match train_loc")
    if not torch.equal(pseudo_unseen_global, val_loc.sort().values):
        raise ValueError("pseudo-unseen cache rows do not exactly match val_loc")
    return protocol, formal_seen, formal_unseen


def global_target_mapping(classes: torch.Tensor) -> torch.Tensor:
    mapping = torch.full((CLASS_COUNT,), -1, dtype=torch.long)
    mapping[classes.detach().cpu().long()] = torch.arange(classes.numel())
    return mapping


def per_class_accuracy(
    labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor
) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not bool(mask.any()):
            raise ValueError(f"evaluation data has no class {int(class_id)}")
        values.append((predictions[mask] == class_id).float().mean())
    return float(torch.stack(values).mean())


@torch.no_grad()
def evaluate_prototypes(
    prototypes: torch.Tensor,
    candidate_classes: torch.Tensor,
    seen_features: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_features: torch.Tensor,
    unseen_labels: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    device: torch.device,
) -> dict[str, float]:
    candidates = candidate_classes.detach().cpu().long()
    if prototypes.shape != (candidates.numel(), 768):
        raise ValueError("prototype shape does not match candidate classes")
    mapping = global_target_mapping(candidates)
    unseen_columns = mapping[unseenclasses.detach().cpu().long()]
    if (unseen_columns < 0).any():
        raise ValueError("unseen class is absent from candidate set")
    prototypes = prototypes.to(device)
    seen_logits = F.normalize(seen_features.to(device).float(), dim=-1) @ prototypes.T
    unseen_logits = F.normalize(unseen_features.to(device).float(), dim=-1) @ prototypes.T
    seen_predictions = candidates[seen_logits.argmax(dim=1).cpu()]
    unseen_predictions = candidates[unseen_logits.argmax(dim=1).cpu()]
    zsl_predictions = unseenclasses[
        unseen_logits[:, unseen_columns.to(device)].argmax(dim=1).cpu()
    ]
    s_value = per_class_accuracy(seen_labels, seen_predictions, seenclasses)
    u_value = per_class_accuracy(unseen_labels, unseen_predictions, unseenclasses)
    zsl_value = per_class_accuracy(unseen_labels, zsl_predictions, unseenclasses)
    harmonic = 2.0 * s_value * u_value / (s_value + u_value) if s_value + u_value else 0.0
    return {
        "U": 100.0 * u_value,
        "S": 100.0 * s_value,
        "H": 100.0 * harmonic,
        "ZS": 100.0 * zsl_value,
    }



@torch.no_grad()
def predict_logits(
    model: RACE,
    features: torch.Tensor,
    candidate_classes: torch.Tensor,
    *,
    strength: float,
    mode: str,
    batch_size: int = 512,
) -> torch.Tensor:
    outputs = []
    for start in range(0, features.shape[0], batch_size):
        outputs.append(
            model.logits(
                features[start : start + batch_size],
                candidate_classes,
                strength=strength,
                mode=mode,
            ).detach().cpu()
        )
    return torch.cat(outputs, dim=0)


@torch.no_grad()
def evaluate_race(
    model: RACE,
    candidate_classes: torch.Tensor,
    seen_features: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_features: torch.Tensor,
    unseen_labels: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    *,
    strength: float,
    mode: str,
) -> dict[str, float]:
    candidates = torch.as_tensor(candidate_classes).detach().cpu().long()
    mapping = global_target_mapping(candidates)
    unseen_columns = mapping[unseenclasses.detach().cpu().long()]
    if (unseen_columns < 0).any():
        raise ValueError("unseen class is absent from candidate set")
    seen_logits = predict_logits(
        model, seen_features, candidates, strength=strength, mode=mode
    )
    unseen_logits = predict_logits(
        model, unseen_features, candidates, strength=strength, mode=mode
    )
    seen_predictions = candidates[seen_logits.argmax(dim=1)]
    unseen_predictions = candidates[unseen_logits.argmax(dim=1)]
    zsl_predictions = unseenclasses[
        unseen_logits[:, unseen_columns].argmax(dim=1)
    ]
    s_value = per_class_accuracy(seen_labels, seen_predictions, seenclasses)
    u_value = per_class_accuracy(unseen_labels, unseen_predictions, unseenclasses)
    zsl_value = per_class_accuracy(unseen_labels, zsl_predictions, unseenclasses)
    harmonic = 2.0 * s_value * u_value / (s_value + u_value) if s_value + u_value else 0.0
    return {
        "U": 100.0 * u_value,
        "S": 100.0 * s_value,
        "H": 100.0 * harmonic,
        "ZS": 100.0 * zsl_value,
    }


def select_strength(
    model: RACE,
    grid: list[float],
    candidates: torch.Tensor,
    validation: tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor],
    emit: Callable[[str], None],
) -> tuple[float, dict[str, float], list[dict]]:
    if not grid or grid[0] != 0.0 or any(value < 0 for value in grid):
        raise ValueError("strength grid must start at 0 and contain non-negative values")
    if len(set(grid)) != len(grid) or grid != sorted(grid):
        raise ValueError("strength grid must be unique and sorted")
    history = []
    best = None
    for strength in grid:
        metrics = evaluate_race(
            model,
            candidates,
            *validation,
            strength=float(strength),
            mode="aligned",
        )
        row = {"strength": float(strength), "metrics_percent": metrics}
        history.append(row)
        key = (metrics["H"], -abs(metrics["U"] - metrics["S"]), -float(strength))
        if best is None or key > best["key"]:
            best = {"strength": float(strength), "metrics": metrics, "key": key}
        emit(
            f"pseudo strength={float(strength):.4f} "
            f"U={metrics['U']:.6f} S={metrics['S']:.6f} "
            f"H={metrics['H']:.6f} ZS={metrics['ZS']:.6f}"
        )
    if best is None:
        raise RuntimeError("strength selection produced no candidate")
    return best["strength"], best["metrics"], history


def run(args: argparse.Namespace) -> int:
    root = repository_root()
    config_path = Path(args.config).resolve()
    config, config_sha256 = load_config(config_path, args.expected_config_sha256)
    code_commit = clean_commit(root, args.expected_commit)
    run_dir = validate_run_dir(root, Path(args.run_dir))
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / "training.log"

    with log_path.open("x", encoding="utf-8", newline="\n") as log_handle:
        def emit(message: str) -> None:
            print(message, flush=True)
            log_handle.write(message + "\n")
            log_handle.flush()

        emit(f"code_commit={code_commit}")
        emit(f"config_sha256={config_sha256}")
        emit(f"seed={int(config['seed'])}")
        emit("module=RACE_no_trainable_prototype")
        emit("selection_protocol=xlsa17_100_50_validation_then_single_test")
        device = torch.device(config["device"])
        if device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("formal run requires a visible CUDA device")

        training_keys = ("sentence_embeds", "train_features", "train_labels", "res101", "att_splits")
        training_paths, input_identities = resolve_and_verify_inputs(root, config, training_keys)
        sentence_embeds = torch.load(training_paths["sentence_embeds"], map_location="cpu", weights_only=True)
        train_features = torch.load(training_paths["train_features"], map_location="cpu", weights_only=True)
        train_labels = torch.load(training_paths["train_labels"], map_location="cpu", weights_only=True).long()
        normalized_sentences(sentence_embeds)
        if train_features.ndim != 2 or train_features.shape[1] != 768:
            raise ValueError("train features must have shape [N, 768]")
        if train_labels.shape != (train_features.shape[0],):
            raise ValueError("train labels do not match train features")

        protocol, formal_seen, formal_unseen = load_protocol_split(
            training_paths, train_labels, config
        )
        pseudo_candidates = torch.cat(
            (protocol.pseudo_seen, protocol.pseudo_unseen)
        ).sort().values
        pseudo_validation = (
            train_features[protocol.pseudo_seen_evaluation_indices],
            train_labels[protocol.pseudo_seen_evaluation_indices],
            train_features[protocol.pseudo_unseen_evaluation_indices],
            train_labels[protocol.pseudo_unseen_evaluation_indices],
            protocol.pseudo_seen,
            protocol.pseudo_unseen,
        )
        model = RACE(
            sentence_embeds, temperature=float(config["temperature"])
        ).to(device)
        grid = [float(value) for value in config["strength_grid"]]
        selected_strength, selected_pseudo, pseudo_history = select_strength(
            model, grid, pseudo_candidates, pseudo_validation, emit
        )
        pseudo_baseline = next(
            row["metrics_percent"] for row in pseudo_history if row["strength"] == 0.0
        )
        pseudo_controls = {
            mode: evaluate_race(
                model,
                pseudo_candidates,
                *pseudo_validation,
                strength=selected_strength,
                mode=mode,
            )
            for mode in ("no_contrast", "wrong_role")
        }
        emit(
            f"selected_strength={selected_strength:.4f} "
            f"pseudo_H={selected_pseudo['H']:.6f}"
        )

        selection_path = run_dir / "selection_state.pth"
        torch.save(
            {
                "code_commit": code_commit,
                "config": config,
                "config_sha256": config_sha256,
                "selected_strength": selected_strength,
                "pseudo_baseline_metrics": pseudo_baseline,
                "pseudo_selected_metrics": selected_pseudo,
                "rival_indices": model.rivals.detach().cpu(),
                "rival_indices_sha256": sha256_tensor(model.rivals),
                "pseudo_split_identity": {
                    "pseudo_seen_classes_sha256": sha256_tensor(protocol.pseudo_seen),
                    "pseudo_unseen_classes_sha256": sha256_tensor(protocol.pseudo_unseen),
                    "pseudo_train_indices_sha256": sha256_tensor(protocol.pseudo_train_indices),
                    "pseudo_seen_eval_indices_sha256": sha256_tensor(protocol.pseudo_seen_evaluation_indices),
                    "pseudo_unseen_eval_indices_sha256": sha256_tensor(protocol.pseudo_unseen_evaluation_indices),
                },
            },
            selection_path,
        )
        selection_sha256 = sha256_file(selection_path)

        # Official test tensors and test indices first become reachable after
        # the strength and full 200-class rival table are frozen above.
        official_paths, official_identities = resolve_and_verify_inputs(
            root, config, OFFICIAL_KEYS
        )
        input_identities.update(official_identities)
        official_data = {
            key: torch.load(official_paths[key], map_location="cpu", weights_only=True)
            for key in OFFICIAL_KEYS
        }
        checked_seen, checked_unseen = load_official_split(
            {**training_paths, **official_paths},
            train_labels,
            official_data["seen_labels"],
            official_data["unseen_labels"],
        )
        if not torch.equal(checked_seen, formal_seen) or not torch.equal(
            checked_unseen, formal_unseen
        ):
            raise RuntimeError("official class sets differ from frozen formal split")

        all_candidates = torch.arange(CLASS_COUNT, dtype=torch.long)
        official_metrics = {
            "mean8": evaluate_race(
                model,
                all_candidates,
                official_data["seen_features"],
                official_data["seen_labels"],
                official_data["unseen_features"],
                official_data["unseen_labels"],
                formal_seen,
                formal_unseen,
                strength=0.0,
                mode="aligned",
            ),
            "race_aligned": evaluate_race(
                model,
                all_candidates,
                official_data["seen_features"],
                official_data["seen_labels"],
                official_data["unseen_features"],
                official_data["unseen_labels"],
                formal_seen,
                formal_unseen,
                strength=selected_strength,
                mode="aligned",
            ),
            "no_contrast": evaluate_race(
                model,
                all_candidates,
                official_data["seen_features"],
                official_data["seen_labels"],
                official_data["unseen_features"],
                official_data["unseen_labels"],
                formal_seen,
                formal_unseen,
                strength=selected_strength,
                mode="no_contrast",
            ),
            "wrong_role": evaluate_race(
                model,
                all_candidates,
                official_data["seen_features"],
                official_data["seen_labels"],
                official_data["unseen_features"],
                official_data["unseen_labels"],
                formal_seen,
                formal_unseen,
                strength=selected_strength,
                mode="wrong_role",
            ),
        }
        baseline = official_metrics["mean8"]
        aligned = official_metrics["race_aligned"]
        delta = {key: aligned[key] - baseline[key] for key in ("U", "S", "H", "ZS")}
        keeps_h = delta["H"] >= float(config["minimum_keep_delta_H"])
        keeps_groups = (
            delta["U"] >= -float(config["maximum_allowed_drop_U_or_S"])
            and delta["S"] >= -float(config["maximum_allowed_drop_U_or_S"])
        )
        decision = "keep_module" if keeps_h and keeps_groups else "stop_no_gain"
        audit_features = official_data["seen_features"][:32]
        decomposition_error = model.max_decomposition_error(
            audit_features,
            all_candidates,
            strength=selected_strength,
            mode="aligned",
        )
        if decomposition_error > 1e-6:
            raise RuntimeError(
                f"RACE additive decomposition error exceeds 1e-6: {decomposition_error}"
            )

        result = {
            "experiment_id": EXPERIMENT_ID,
            "run_id": RUN_ID,
            "status": "completed_single_test",
            "decision": decision,
            "selection_protocol": config["selection_protocol"],
            "official_test_policy": config["official_test_policy"],
            "official_test_used_for_selection": False,
            "official_test_evaluations": {
                "mean8": 1,
                "race_aligned": 1,
                "no_contrast": 1,
                "wrong_role": 1,
            },
            "code_commit": code_commit,
            "config_sha256": config_sha256,
            "seed": int(config["seed"]),
            "input_sha256": input_identities,
            "selected_strength": selected_strength,
            "rival_universe_class_count": CLASS_COUNT,
            "rival_indices_sha256": sha256_tensor(model.rivals),
            "selection_state_sha256": selection_sha256,
            "pseudo_validation": {
                "baseline_metrics_percent": pseudo_baseline,
                "selected_metrics_percent": selected_pseudo,
                "controls_percent": pseudo_controls,
                "grid_history": pseudo_history,
                "pseudo_seen_classes": int(protocol.pseudo_seen.numel()),
                "pseudo_unseen_classes": int(protocol.pseudo_unseen.numel()),
            },
            "official_metrics_percent": official_metrics,
            "delta_percent_points": delta,
            "max_additive_decomposition_error": decomposition_error,
        }
        with (run_dir / "metrics.json").open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        with (run_dir / "result.yaml").open("x", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(result, handle, allow_unicode=True, sort_keys=False)
        emit(
            "mean8 "
            f"U={baseline['U']:.6f}% S={baseline['S']:.6f}% "
            f"H={baseline['H']:.6f}% ZS={baseline['ZS']:.6f}%"
        )
        emit(
            "race "
            f"U={aligned['U']:.6f}% S={aligned['S']:.6f}% "
            f"H={aligned['H']:.6f}% ZS={aligned['ZS']:.6f}%"
        )
        emit(
            f"delta_U={delta['U']:.6f} delta_S={delta['S']:.6f} "
            f"delta_H={delta['H']:.6f} decision={decision}"
        )
    return 0


def load_official_split(
    paths: dict[str, Path], train_labels: torch.Tensor, seen_labels: torch.Tensor, unseen_labels: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor]:
    res101 = sio.loadmat(paths["res101"], variable_names=["labels"])
    splits = sio.loadmat(
        paths["att_splits"],
        variable_names=["trainval_loc", "test_seen_loc", "test_unseen_loc"],
    )
    labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    trainval = torch.from_numpy(splits["trainval_loc"].squeeze() - 1).long()
    test_seen = torch.from_numpy(splits["test_seen_loc"].squeeze() - 1).long()
    test_unseen = torch.from_numpy(splits["test_unseen_loc"].squeeze() - 1).long()
    if not torch.equal(train_labels.detach().cpu().long(), labels[trainval]):
        raise ValueError("official check: train labels mismatch")
    if not torch.equal(seen_labels.detach().cpu().long(), labels[test_seen]):
        raise ValueError("official check: seen labels mismatch")
    if not torch.equal(unseen_labels.detach().cpu().long(), labels[test_unseen]):
        raise ValueError("official check: unseen labels mismatch")
    seenclasses = torch.unique(labels[trainval], sorted=True)
    unseenclasses = torch.unique(labels[test_unseen], sorted=True)
    if not torch.equal(seenclasses, torch.unique(labels[test_seen], sorted=True)):
        raise ValueError("official seen class set mismatch")
    if torch.isin(seenclasses, unseenclasses).any():
        raise ValueError("official seen/unseen classes overlap")
    return seenclasses, unseenclasses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
