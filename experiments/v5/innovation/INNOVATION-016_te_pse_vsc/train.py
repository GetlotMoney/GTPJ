"""Train frozen TE-PSE with one class-balanced visual-semantic consistency loss."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
import torch.nn.functional as F
import yaml
from torch.utils.data import DataLoader, TensorDataset


PROJECT_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_DIR = Path(__file__).resolve().parent
PARENT_TRAIN_PATH = (
    SCRIPT_DIR.parent / "INNOVATION-015_te_pse" / "train.py"
)
PARENT_SPEC = importlib.util.spec_from_file_location(
    "v5_innovation_015_train", PARENT_TRAIN_PATH
)
if PARENT_SPEC is None or PARENT_SPEC.loader is None:
    raise RuntimeError(f"cannot load frozen TE-PSE parent: {PARENT_TRAIN_PATH}")
PARENT = importlib.util.module_from_spec(PARENT_SPEC)
PARENT_SPEC.loader.exec_module(PARENT)
TransferableEvidencePSE = PARENT.TransferableEvidencePSE


EXPECTED_CONFIG_SHA256 = "3b60554d3dd493d738f1de839205fcf670bfd7ab33f38c2f0b9ab4de6c645d24"
EXPECTED_RUN_ID = "RUN-001"
EXPECTED_SCORE_PATH = "clip_cls_x_te_pse_role_rival_evidence_vsc"
EXPECTED_VSC_WEIGHT = 0.1


def load_config(path: Path) -> tuple[dict, str]:
    config_sha256 = PARENT.sha256_file(path)
    if config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError(
            "config SHA-256 does not match the reviewed frozen VSC config: "
            f"{config_sha256}."
        )
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping.")
    if config.get("dataset") != "CUB":
        raise ValueError("this experiment only accepts dataset: CUB.")
    if tuple(config.get("role_order", ())) != PARENT.EXPECTED_ROLES:
        raise ValueError("role_order does not match the frozen eight-sentence contract.")
    if tuple(config.get("evidence_roles", ())) != PARENT.EXPECTED_EVIDENCE_ROLES:
        raise ValueError("evidence_roles must be the six local roles plus unique.")
    if config.get("score_path") != EXPECTED_SCORE_PATH:
        raise ValueError("score_path does not identify the frozen TE-PSE+VSC path.")
    if config.get("text_source") != "gpt56_8sent":
        raise ValueError("text_source must remain GPT-5.6 eight-sentence.")
    if float(config.get("vsc_weight", -1.0)) != EXPECTED_VSC_WEIGHT:
        raise ValueError("vsc_weight must remain exactly 0.1 for this experiment.")
    return config, config_sha256


def class_visual_centroids(
    features: torch.Tensor,
    labels: torch.Tensor,
    classes: torch.Tensor,
    train_indices: torch.Tensor,
) -> torch.Tensor:
    """Return normalized class centroids using only the frozen 90% train split."""

    if features.ndim != 2 or labels.ndim != 1:
        raise ValueError("features and labels must have shapes [N,D] and [N].")
    if features.shape[0] != labels.shape[0]:
        raise ValueError("features and labels must contain the same sample count.")
    if train_indices.ndim != 1 or not train_indices.numel():
        raise ValueError("train_indices must be a non-empty vector.")
    selected_features = F.normalize(features[train_indices].float(), dim=-1)
    selected_labels = labels[train_indices].long()
    centroids = []
    for class_id in classes.detach().cpu().long():
        mask = selected_labels == class_id
        if not mask.any():
            raise ValueError(f"training split has no sample for class {int(class_id)}.")
        centroids.append(F.normalize(selected_features[mask].mean(dim=0), dim=0))
    result = torch.stack(centroids)
    if not torch.isfinite(result).all():
        raise ValueError("visual centroids contain a non-finite value.")
    return result


def visual_semantic_consistency_loss(
    model: TransferableEvidencePSE,
    visual_centroids: torch.Tensor,
    classes: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Symmetric class-centroid matching using the exact inference vectors."""

    device = model.base_prototypes.device
    classes = classes.to(device=device, dtype=torch.long)
    visual_centroids = visual_centroids.to(device=device, dtype=torch.float32)
    if visual_centroids.ndim != 2 or visual_centroids.shape[0] != classes.numel():
        raise ValueError("visual_centroids must have one row per class.")
    semantic_vectors = model.effective_class_vectors().index_select(0, classes)
    matching = visual_centroids @ semantic_vectors.T / model.temperature
    targets = torch.arange(classes.numel(), device=device)
    visual_to_semantic = F.cross_entropy(matching, targets)
    semantic_to_visual = F.cross_entropy(matching.T, targets)
    symmetric = 0.5 * (visual_to_semantic + semantic_to_visual)
    return symmetric, visual_to_semantic, semantic_to_visual


def run(config_path: Path, run_dir: Path, expected_commit: str, run_id: str) -> dict:
    code_commit = PARENT.get_clean_commit()
    PARENT.verify_expected_commit(code_commit, expected_commit)
    PARENT.verify_run_identity(run_id, run_dir)
    config, config_sha256 = load_config(config_path)
    paths = PARENT.resolve_input_paths(config)
    input_sha256 = PARENT.verify_input_contract(config, paths)

    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("formal TE-PSE+VSC training requires a visible CUDA device.")
    if run_dir.exists():
        raise FileExistsError(f"refusing to reuse run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    logger = PARENT.RunLogger(run_dir / "training.log")

    seed = int(config["seed"])
    logger.emit(f"代码 commit：{code_commit}")
    logger.emit(f"配置 SHA-256：{config_sha256}")
    logger.emit(f"随机种子：{seed}")
    PARENT.set_determinism(seed)

    training_tensor_names = ("sentence_embeds", "train_features", "train_labels")
    tensors = {
        name: torch.load(paths[name], map_location="cpu", weights_only=True)
        for name in training_tensor_names
    }
    if tuple(tensors["sentence_embeds"].shape) != PARENT.EXPECTED_SENTENCE_SHAPE:
        raise ValueError(
            f"sentence cache must be {PARENT.EXPECTED_SENTENCE_SHAPE}, "
            f"got {tuple(tensors['sentence_embeds'].shape)}."
        )
    seenclasses = PARENT.load_training_classes(
        paths["res101"], paths["att_splits"], tensors["train_labels"]
    )
    train_indices, validation_indices = PARENT.stratified_train_validation_split(
        tensors["train_labels"],
        seenclasses,
        float(config["validation_fraction"]),
        seed,
    )
    split_sha256 = hashlib.sha256(
        validation_indices.numpy().astype("int64").tobytes()
    ).hexdigest()
    visual_centroids = class_visual_centroids(
        tensors["train_features"],
        tensors["train_labels"],
        seenclasses,
        train_indices,
    ).to(device)

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
        PARENT.EXPECTED_ROLES.index(role) for role in config["evidence_roles"]
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
    vsc_weight = float(config["vsc_weight"])
    best_state = None
    best_validation_loss = float("inf")
    best_epoch = 0
    stale_epochs = 0
    history = []
    for epoch in range(1, int(config["max_epochs"]) + 1):
        model.train()
        classification_sum = 0.0
        vsc_sum = 0.0
        total_sum = 0.0
        sample_count = 0
        for features, targets in train_loader:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            classification_loss = F.cross_entropy(
                model.logits(features, seenclasses), targets
            )
            vsc_loss, _, _ = visual_semantic_consistency_loss(
                model, visual_centroids, seenclasses
            )
            total_loss = classification_loss + vsc_weight * vsc_loss
            total_loss.backward()
            optimizer.step()
            batch_size = features.size(0)
            classification_sum += float(classification_loss.detach()) * batch_size
            vsc_sum += float(vsc_loss.detach()) * batch_size
            total_sum += float(total_loss.detach()) * batch_size
            sample_count += batch_size

        model.eval()
        with torch.no_grad():
            validation_loss = float(
                F.cross_entropy(
                    model.logits(validation_features, seenclasses), validation_targets
                ).cpu()
            )
        classification_epoch = classification_sum / sample_count
        vsc_epoch = vsc_sum / sample_count
        total_epoch = total_sum / sample_count
        strength = float(model.evidence_strength.detach().cpu())
        history.append(
            {
                "epoch": epoch,
                "train_classification_loss": classification_epoch,
                "train_vsc_loss": vsc_epoch,
                "train_total_loss": total_epoch,
                "validation_loss": validation_loss,
                "evidence_strength": strength,
            }
        )
        logger.emit(
            f"epoch={epoch} train_ce={classification_epoch:.6f} "
            f"train_vsc={vsc_epoch:.6f} train_total={total_epoch:.6f} "
            f"validation_loss={validation_loss:.6f} "
            f"evidence_strength={strength:.6f}"
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
    verified_seenclasses, unseenclasses = PARENT.load_v5_cub_split(
        paths["res101"],
        paths["att_splits"],
        tensors["train_labels"],
        tensors["seen_labels"],
        tensors["unseen_labels"],
        "cpu",
    )
    if not torch.equal(seenclasses, verified_seenclasses):
        raise ValueError("training and official test split class identities differ.")
    evaluation = PARENT.evaluate_predeclared_pair(
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
        final_vsc, final_v2s, final_s2v = visual_semantic_consistency_loss(
            model, visual_centroids, seenclasses
        )
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
        "experiment_id": "V5-INNOVATION-016",
        "run_id": run_id,
        "code_commit": code_commit,
        "parent_te_pse_commit": "b7f060afdd6d42baeee25b4d3068389085d88286",
        "config_sha256": config_sha256,
        "seed": seed,
        "score_path": config["score_path"],
        "vsc_weight": vsc_weight,
        "trainable_parameters": sum(
            parameter.numel()
            for parameter in model.parameters()
            if parameter.requires_grad
        ),
        "input_sha256": input_sha256,
        "class_order_sha256": config["class_order_sha256"],
        "validation_indices_sha256": split_sha256,
        "best_epoch_by_seen_validation_ce": best_epoch,
        "best_validation_loss": best_validation_loss,
        "baseline_metrics_percent": baseline_metrics,
        "metrics_percent": metrics,
        "delta_H_from_b0": metrics["H"] - baseline_metrics["H"],
        "diagnostics": {
            "evidence_strength": float(model.evidence_strength.detach().cpu()),
            "final_vsc_loss": float(final_vsc.cpu()),
            "final_visual_to_semantic_loss": float(final_v2s.cpu()),
            "final_semantic_to_visual_loss": float(final_s2v.cpu()),
            "coherence_min": float(coherence.min()),
            "coherence_mean": float(coherence.mean()),
            "coherence_max": float(coherence.max()),
            "role_weight_mean": model.role_weights.detach().cpu().mean(dim=0).tolist(),
            "role_weight_std": model.role_weights.detach().cpu().std(dim=0).tolist(),
            "max_additive_decomposition_error": decomposition_error,
        },
        "history": history,
    }
    result["checkpoint_sha256"] = PARENT.sha256_file(checkpoint_path)
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (run_dir / "result.yaml").open("x", encoding="utf-8") as handle:
        yaml.safe_dump(result, handle, allow_unicode=True, sort_keys=False)

    logger.emit(
        "baseline U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(
            **baseline_metrics
        )
    )
    logger.emit(
        "TE-PSE+VSC U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(
            **metrics
        )
    )
    logger.emit(
        f"best_epoch={best_epoch} "
        f"delta_H_from_b0={result['delta_H_from_b0']:.6f}"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(
        args.config.resolve(),
        args.run_dir.resolve(),
        args.expected_commit,
        args.run_id,
    )


if __name__ == "__main__":
    main()
