"""Train the one-scalar TE-PSE evidence strength on frozen CUB CLIP caches."""

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
SCRIPT_DIR = Path(__file__).resolve().parent
for import_path in (PROJECT_ROOT, SCRIPT_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from te_pse import TransferableEvidencePSE  # noqa: E402
from tools.v5_cub_data import load_v5_cub_split  # noqa: E402


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
EXPECTED_EVIDENCE_ROLES = EXPECTED_ROLES[:6] + EXPECTED_ROLES[7:]
EXPECTED_SENTENCE_SHAPE = (200, 8, 768)
EXPECTED_CONFIG_SHA256 = "23d1a15060d09bbaab74df2294661d54172ff4c509c89e1ec24bc582a7deb91c"
EXPECTED_RUN_ID = "RUN-001"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"could not resolve one full run commit: {commit!r}.")
    dirty = subprocess.check_output(
        [
            "git",
            "-C",
            str(PROJECT_ROOT),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        text=True,
    ).strip()
    if dirty:
        raise ValueError("formal training requires a completely clean worktree.")
    return commit


def load_config(path: Path) -> tuple[dict, str]:
    config_sha256 = sha256_file(path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError(
            "config SHA-256 does not match the reviewed frozen config: "
            f"{config_sha256}."
        )
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping.")
    if config.get("dataset") != "CUB":
        raise ValueError("this experiment only accepts dataset: CUB.")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order does not match the frozen 8-sentence contract.")
    if tuple(config.get("evidence_roles", ())) != EXPECTED_EVIDENCE_ROLES:
        raise ValueError("evidence_roles must be the six local roles plus unique.")
    if config.get("score_path") != "clip_cls_x_te_pse_role_rival_evidence":
        raise ValueError("score_path does not identify the frozen TE-PSE path.")
    if config.get("text_source") != "gpt56_8sent":
        raise ValueError("text_source must remain the frozen GPT-5.6 eight-sentence cache.")
    return config, config_sha256


def verify_expected_commit(actual_commit: str, expected_commit: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise ValueError("--expected-commit must be one full lowercase Git SHA.")
    if actual_commit != expected_commit:
        raise ValueError(
            f"current clean commit {actual_commit} does not match "
            f"--expected-commit {expected_commit}."
        )


def verify_run_identity(run_id: str, run_dir: Path) -> None:
    if run_id != EXPECTED_RUN_ID:
        raise ValueError(f"--run-id must match the frozen plan {EXPECTED_RUN_ID}.")
    if run_dir.name != run_id:
        raise ValueError("--run-dir final directory name must equal --run-id.")


def resolve_input_paths(config: dict) -> dict[str, Path]:
    if not isinstance(config.get("inputs"), dict):
        raise ValueError("inputs must be a mapping.")
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing TE-PSE input: " + ", ".join(missing))
    return paths


def verify_input_contract(config: dict, paths: dict[str, Path]) -> dict[str, str]:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every configured input exactly once.")
    actual = {name: sha256_file(path) for name, path in paths.items()}
    mismatch = [name for name in paths if expected[name] != actual[name]]
    if mismatch:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatch))

    split_data = sio.loadmat(paths["att_splits"])
    raw_names = split_data.get("allclasses_names")
    if raw_names is None or tuple(raw_names.shape) != (200, 1):
        raise ValueError("att_splits allclasses_names must have shape [200, 1].")
    names = [str(item[0][0]) for item in raw_names]
    serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    class_order_sha256 = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if class_order_sha256 != config.get("class_order_sha256"):
        raise ValueError("xlsa17 class order SHA-256 mismatch.")
    return actual


def set_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def stratified_train_validation_split(
    labels: torch.Tensor, classes: torch.Tensor, fraction: float, seed: int
) -> tuple[torch.Tensor, torch.Tensor]:
    if not 0.0 < fraction < 0.5:
        raise ValueError("validation_fraction must be in (0, 0.5).")
    labels = labels.detach().cpu().long()
    generator = torch.Generator().manual_seed(seed)
    train_indices = []
    validation_indices = []
    for class_id in classes.detach().cpu().long():
        indices = torch.where(labels == class_id)[0]
        if indices.numel() < 2:
            raise ValueError(f"class {int(class_id)} needs at least two training samples.")
        permutation = indices[torch.randperm(indices.numel(), generator=generator)]
        validation_count = max(1, int(round(indices.numel() * fraction)))
        validation_count = min(validation_count, indices.numel() - 1)
        validation_indices.append(permutation[:validation_count])
        train_indices.append(permutation[validation_count:])
    return torch.cat(train_indices).sort().values, torch.cat(validation_indices).sort().values


def load_training_classes(
    res101_path: Path, split_path: Path, train_labels: torch.Tensor
) -> torch.Tensor:
    """Validate the training-label cache without loading official test tensors."""

    res101 = sio.loadmat(res101_path)
    splits = sio.loadmat(split_path)
    labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    train_indices = torch.from_numpy(splits["trainval_loc"].squeeze() - 1).long()
    expected = labels[train_indices]
    actual = train_labels.detach().cpu().long()
    if not torch.equal(expected, actual):
        raise ValueError("train label cache does not match the xlsa17 split.")
    return torch.unique(expected, sorted=True)


def per_class_accuracy(
    labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor
) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"evaluation cache has no class {int(class_id)}.")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean())


@torch.no_grad()
def evaluate_predeclared_pair(
    model: TransferableEvidencePSE,
    tensors: dict[str, torch.Tensor],
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    device: torch.device,
) -> dict[str, dict[str, float]]:
    """Evaluate the predeclared alpha=0 and TE-PSE paths in one test pass."""

    model.eval()
    seen_components = model.score_components(tensors["seen_features"].to(device))
    unseen_components = model.score_components(tensors["unseen_features"].to(device))

    def metrics_for(logit_key: str) -> dict[str, float]:
        seen_logits = seen_components[logit_key]
        unseen_logits = unseen_components[logit_key]
        seen_predictions = seen_logits.argmax(dim=1).cpu()
        unseen_predictions = unseen_logits.argmax(dim=1).cpu()
        zsl_predictions = unseenclasses[
            unseen_logits[:, unseenclasses.to(device)].argmax(dim=1).cpu()
        ]
        seen_accuracy = per_class_accuracy(
            tensors["seen_labels"], seen_predictions, seenclasses
        )
        unseen_accuracy = per_class_accuracy(
            tensors["unseen_labels"], unseen_predictions, unseenclasses
        )
        zsl_accuracy = per_class_accuracy(
            tensors["unseen_labels"], zsl_predictions, unseenclasses
        )
        denominator = seen_accuracy + unseen_accuracy
        harmonic = (
            2.0 * seen_accuracy * unseen_accuracy / denominator
            if denominator
            else 0.0
        )
        return {
            "U": unseen_accuracy * 100.0,
            "S": seen_accuracy * 100.0,
            "H": harmonic * 100.0,
            "ZS": zsl_accuracy * 100.0,
        }

    return {
        "baseline": metrics_for("base_logits"),
        "te_pse": metrics_for("final_logits"),
    }


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, message: str) -> None:
        print(message, flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")


def run(config_path: Path, run_dir: Path, expected_commit: str, run_id: str) -> dict:
    code_commit = get_clean_commit()
    verify_expected_commit(code_commit, expected_commit)
    verify_run_identity(run_id, run_dir)
    config, config_sha256 = load_config(config_path)
    paths = resolve_input_paths(config)
    input_sha256 = verify_input_contract(config, paths)

    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("formal TE-PSE training requires a visible CUDA device.")
    if run_dir.exists():
        raise FileExistsError(f"refusing to reuse run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    logger = RunLogger(run_dir / "training.log")

    seed = int(config["seed"])
    logger.emit(f"代码 commit：{code_commit}")
    logger.emit(f"配置 SHA-256：{config_sha256}")
    logger.emit(f"随机种子：{seed}")
    set_determinism(seed)

    training_tensor_names = ("sentence_embeds", "train_features", "train_labels")
    tensors = {
        name: torch.load(paths[name], map_location="cpu", weights_only=True)
        for name in training_tensor_names
    }
    if tuple(tensors["sentence_embeds"].shape) != EXPECTED_SENTENCE_SHAPE:
        raise ValueError(
            f"sentence cache must be {EXPECTED_SENTENCE_SHAPE}, "
            f"got {tuple(tensors['sentence_embeds'].shape)}."
        )
    seenclasses = load_training_classes(
        paths["res101"], paths["att_splits"], tensors["train_labels"]
    )
    train_indices, validation_indices = stratified_train_validation_split(
        tensors["train_labels"],
        seenclasses,
        float(config["validation_fraction"]),
        seed,
    )
    split_sha256 = hashlib.sha256(
        validation_indices.numpy().astype("int64").tobytes()
    ).hexdigest()

    global_to_seen = torch.full((200,), -1, dtype=torch.long)
    global_to_seen[seenclasses] = torch.arange(seenclasses.numel())
    train_dataset = TensorDataset(
        tensors["train_features"][train_indices].float(),
        global_to_seen[tensors["train_labels"][train_indices].long()],
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=int(config["batch_size"]),
        shuffle=True,
        num_workers=0,
        generator=torch.Generator().manual_seed(seed),
    )
    evidence_indices = tuple(
        EXPECTED_ROLES.index(role) for role in config["evidence_roles"]
    )
    model = TransferableEvidencePSE(
        tensors["sentence_embeds"],
        evidence_indices,
        temperature=float(config["temperature"]),
        evidence_cap=float(config["evidence_cap"]),
        evidence_init=float(config["evidence_init"]),
    ).to(device)
    optimizer = torch.optim.Adam(
        [model.evidence_logit], lr=float(config["learning_rate"])
    )

    validation_features = tensors["train_features"][validation_indices].to(device).float()
    validation_targets = global_to_seen[
        tensors["train_labels"][validation_indices].long()
    ].to(device)
    best_state = None
    best_validation_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history = []
    for epoch in range(1, int(config["max_epochs"]) + 1):
        model.train()
        loss_sum = 0.0
        sample_count = 0
        for features, targets in train_loader:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model.logits(features, seenclasses), targets)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * features.size(0)
            sample_count += features.size(0)

        model.eval()
        with torch.no_grad():
            validation_loss = float(
                F.cross_entropy(
                    model.logits(validation_features, seenclasses), validation_targets
                ).cpu()
            )
        training_loss = loss_sum / sample_count
        strength = float(model.evidence_strength.detach().cpu())
        history.append(
            {
                "epoch": epoch,
                "train_loss": training_loss,
                "validation_loss": validation_loss,
                "evidence_strength": strength,
            }
        )
        logger.emit(
            f"epoch={epoch} train_loss={training_loss:.6f} "
            f"validation_loss={validation_loss:.6f} evidence_strength={strength:.6f}"
        )
        if validation_loss < best_validation_loss - float(config["min_delta"]):
            best_validation_loss = validation_loss
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= int(config["patience"]):
                break

    if best_state is None:
        raise RuntimeError("training did not produce a validation checkpoint.")
    model.load_state_dict(best_state)

    official_tensor_names = (
        "seen_features",
        "seen_labels",
        "unseen_features",
        "unseen_labels",
    )
    tensors.update(
        {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in official_tensor_names
        }
    )
    verified_seenclasses, unseenclasses = load_v5_cub_split(
        paths["res101"],
        paths["att_splits"],
        tensors["train_labels"],
        tensors["seen_labels"],
        tensors["unseen_labels"],
        "cpu",
    )
    if not torch.equal(seenclasses, verified_seenclasses):
        raise ValueError("training and official test split class identities differ.")
    evaluation = evaluate_predeclared_pair(
        model,
        tensors,
        seenclasses,
        unseenclasses,
        device,
    )
    baseline_metrics = evaluation["baseline"]
    metrics = evaluation["te_pse"]
    model.eval()
    with torch.no_grad():
        probe = model.score_components(tensors["seen_features"][:64].to(device))
        decomposition_error = float(
            (
                probe["final_logits"]
                - probe["base_logits"]
                - probe["role_contributions"].sum(dim=-1)
            )
            .abs()
            .max()
            .cpu()
        )
        coherence = model.evidence_coherence.detach().cpu()
        effective_norm = model.effective_class_vectors().norm(dim=-1).detach().cpu()

    checkpoint_path = run_dir / "model_best.pth"
    torch.save(
        {
            "model": {
                name: value.detach().cpu() for name, value in model.state_dict().items()
            },
            "config": config,
            "code_commit": code_commit,
            "best_epoch": best_epoch,
        },
        checkpoint_path,
    )
    result = {
        "experiment_id": "V5-INNOVATION-015",
        "run_id": run_id,
        "code_commit": code_commit,
        "config_sha256": config_sha256,
        "seed": seed,
        "score_path": config["score_path"],
        "trainable_parameters": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "input_sha256": input_sha256,
        "class_order_sha256": config["class_order_sha256"],
        "validation_indices_sha256": split_sha256,
        "best_epoch_by_seen_validation_ce": best_epoch,
        "best_validation_loss": best_validation_loss,
        "baseline_metrics_percent": baseline_metrics,
        "metrics_percent": metrics,
        "delta_H": metrics["H"] - baseline_metrics["H"],
        "diagnostics": {
            "evidence_strength": float(model.evidence_strength.detach().cpu()),
            "coherence_min": float(coherence.min()),
            "coherence_mean": float(coherence.mean()),
            "coherence_max": float(coherence.max()),
            "effective_vector_norm_min": float(effective_norm.min()),
            "effective_vector_norm_mean": float(effective_norm.mean()),
            "effective_vector_norm_max": float(effective_norm.max()),
            "role_weight_mean": model.role_weights.detach().cpu().mean(dim=0).tolist(),
            "role_weight_std": model.role_weights.detach().cpu().std(dim=0).tolist(),
            "rival_class_ids": model.rival_class_ids.detach().cpu().tolist(),
            "max_additive_decomposition_error": decomposition_error,
        },
        "history": history,
    }
    result["checkpoint_sha256"] = sha256_file(checkpoint_path)
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (run_dir / "result.yaml").open("x", encoding="utf-8") as handle:
        yaml.safe_dump(result, handle, allow_unicode=True, sort_keys=False)

    logger.emit("baseline U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**baseline_metrics))
    logger.emit("TE-PSE U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
    logger.emit(f"best_epoch={best_epoch} delta_H={result['delta_H']:.6f}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.run_dir.resolve(), args.expected_commit, args.run_id)


if __name__ == "__main__":
    main()
