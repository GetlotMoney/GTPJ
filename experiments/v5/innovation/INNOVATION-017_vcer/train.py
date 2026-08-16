"""Train VCER on 150 CUB seen classes, then evaluate the frozen checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
import yaml
import scipy.io as sio


os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
MODULE_DIR = Path(__file__).resolve().parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

from tools.v5_cub_data import load_v5_cub_split  # noqa: E402
from vcer import VisibilityAwareCounterfactualEvidenceRouter  # noqa: E402


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
EXPECTED_SENTENCE_SHAPE = (200, 8, 768)
TRAINING_KEYS = (
    "sentence_embeds",
    "train_features",
    "train_labels",
    "train_patches",
    "res101",
    "att_splits",
    "x2_checkpoint",
)
OFFICIAL_KEYS = (
    "seen_features",
    "seen_labels",
    "seen_patches",
    "unseen_features",
    "unseen_labels",
    "unseen_patches",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def set_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("cannot resolve one full Git commit.")
    dirty = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"], text=True
    ).strip()
    if dirty:
        raise ValueError("formal VCER training requires a clean worktree.")
    return commit


def load_config(path: Path, expected_sha256: str) -> tuple[dict, str]:
    digest = sha256_file(path)
    if digest != expected_sha256:
        raise ValueError(f"config SHA-256 mismatch: {digest}.")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping.")
    if config.get("experiment_id") != "V5-INNOVATION-017":
        raise ValueError("experiment_id must be V5-INNOVATION-017.")
    if config.get("run_id") != "RUN-001":
        raise ValueError("this frozen run must use RUN-001.")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order violates the 6 local + global + unique contract.")
    if config.get("official_test_policy") != "direct_after_fixed_checkpoint_owner_20260816":
        raise ValueError("official test policy differs from the owner-authorized protocol.")
    stages = config.get("lr_stages")
    if not isinstance(stages, list) or sum(int(stage["epochs"]) for stage in stages) != 50:
        raise ValueError("VCER requires the frozen 50-epoch schedule.")
    if config.get("role_shuffle_permutation") != [1, 2, 3, 4, 5, 0]:
        raise ValueError("role shuffle must be the frozen six-local cyclic permutation.")
    return config, digest


def resolve_paths(config: dict, data_root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, value in config["inputs"].items():
        candidate = Path(value)
        paths[name] = (
            candidate.resolve()
            if candidate.is_absolute()
            else (data_root / candidate).resolve()
        )
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing VCER input: " + ", ".join(missing))
    return paths


def verify_hashes(config: dict, paths: dict[str, Path], keys: tuple[str, ...]) -> dict:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every configured input exactly once.")
    actual = {name: sha256_file(paths[name]) for name in keys}
    mismatch = [name for name in keys if actual[name] != expected[name]]
    if mismatch:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatch))
    return actual


def verify_class_order(config: dict, split_path: Path) -> None:
    split = sio.loadmat(split_path, variable_names=["allclasses_names"])
    raw_names = split.get("allclasses_names")
    if raw_names is None or tuple(raw_names.shape) != (200, 1):
        raise ValueError("att_splits allclasses_names must have shape [200, 1].")
    names = [str(item[0][0]) for item in raw_names]
    serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if digest != config["class_order_sha256"]:
        raise ValueError("xlsa17 class order SHA-256 mismatch.")


def verify_output_boundary(run_dir: Path) -> None:
    output = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"],
        text=True,
    )
    for line in output.splitlines():
        if not line.startswith("worktree "):
            continue
        worktree = Path(line.split(" ", 1)[1]).resolve()
        try:
            run_dir.relative_to(worktree)
        except ValueError:
            continue
        raise ValueError("run directory must stay outside every Git worktree.")


def frozen_x2_from_checkpoint(
    sentence_embeds: torch.Tensor,
    seenclasses: torch.Tensor,
    checkpoint_path: Path,
    config: dict,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("code_commit") != config["x2_identity"]["code_commit"]:
        raise ValueError("X2 checkpoint code commit mismatch.")
    if int(checkpoint.get("best_epoch", -1)) != int(config["x2_identity"]["best_epoch"]):
        raise ValueError("X2 checkpoint epoch mismatch.")
    checkpoint_config = checkpoint.get("config", {})
    if checkpoint_config.get("conditions", {}).get("PSE-X2", {}).get("mode") != "legacy_uniform":
        raise ValueError("checkpoint is not the frozen PSE-X2 legacy-uniform condition.")
    state = checkpoint["model"]
    required = {
        "legacy_attention.in_proj_weight",
        "legacy_attention.in_proj_bias",
        "legacy_attention.out_proj.weight",
        "legacy_attention.out_proj.bias",
        "post_projection.weight",
        "post_projection.bias",
        "layer_norm.weight",
        "layer_norm.bias",
        "logit_scale",
        "sentence_embeds",
        "adapted_classes",
    }
    if not required.issubset(state):
        raise ValueError("X2 checkpoint misses a required legacy-uniform tensor.")

    expected_sentences = F.normalize(sentence_embeds.detach().float(), dim=-1)
    checkpoint_sentences = state["sentence_embeds"].detach().cpu().float()
    if not torch.equal(checkpoint_sentences, expected_sentences):
        raise ValueError("X2 checkpoint sentence buffer differs from the frozen cache.")
    checkpoint_classes = state["adapted_classes"].detach().cpu().long()
    if not torch.equal(checkpoint_classes, seenclasses.detach().cpu().long()):
        raise ValueError("X2 checkpoint adapted classes differ from the training split.")
    sentences = checkpoint_sentences.to(device)
    seen = checkpoint_classes.to(device)
    roles = sentences.index_select(0, seen)
    dim = roles.shape[-1]
    heads = 4
    head_dim = dim // heads
    in_weight = state["legacy_attention.in_proj_weight"].to(device)
    in_bias = state["legacy_attention.in_proj_bias"].to(device)
    _, _, value_weight = in_weight.chunk(3, dim=0)
    _, _, value_bias = in_bias.chunk(3, dim=0)
    value = F.linear(roles, value_weight, value_bias)
    value = value.view(roles.shape[0], 8, heads, head_dim).transpose(1, 2)
    uniform = value.new_full((roles.shape[0], heads, 8, 8), 1.0 / 8.0)
    context = torch.matmul(uniform, value)
    context = context.transpose(1, 2).contiguous().view(roles.shape[0], 8, dim)
    context = F.linear(
        context,
        state["legacy_attention.out_proj.weight"].to(device),
        state["legacy_attention.out_proj.bias"].to(device),
    )
    context = F.linear(
        context,
        state["post_projection.weight"].to(device),
        state["post_projection.bias"].to(device),
    )
    mixed = 0.35 * context + 0.65 * roles
    transformed = F.layer_norm(
        2.0 * mixed,
        (dim,),
        state["layer_norm.weight"].to(device),
        state["layer_norm.bias"].to(device),
        1e-5,
    )

    base_vectors = sentences.mean(dim=1)
    base_scale = base_vectors.new_ones((base_vectors.shape[0],))
    base_scale[seen] = 0.35
    base_part = base_scale.unsqueeze(-1) * base_vectors
    role_part = transformed.new_zeros((200, 8, dim))
    role_part[seen] = 0.65 * transformed / 8.0
    enhanced = base_part + role_part.sum(dim=1)
    prototypes = F.normalize(enhanced, dim=-1)
    scale = state["logit_scale"].to(device).exp().clamp(max=100.0)
    diagnostics = {
        "checkpoint_code_commit": checkpoint["code_commit"],
        "checkpoint_best_epoch": int(checkpoint["best_epoch"]),
        "scale": float(scale.detach().cpu()),
    }
    return prototypes.detach().cpu(), scale.detach().cpu(), diagnostics


def per_class_accuracy(
    labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor
) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"evaluation has no class {int(class_id)}.")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean())


def metrics_from_logits(
    seen_logits: torch.Tensor,
    unseen_logits: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_labels: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
) -> dict[str, float]:
    seen_prediction = seen_logits.argmax(dim=1)
    unseen_prediction = unseen_logits.argmax(dim=1)
    zsl_prediction = unseenclasses[
        unseen_logits[:, unseenclasses].argmax(dim=1)
    ]
    seen = per_class_accuracy(seen_labels, seen_prediction, seenclasses)
    unseen = per_class_accuracy(unseen_labels, unseen_prediction, unseenclasses)
    zsl = per_class_accuracy(unseen_labels, zsl_prediction, unseenclasses)
    harmonic = 2.0 * seen * unseen / (seen + unseen) if seen + unseen else 0.0
    return {"U": unseen * 100.0, "S": seen * 100.0, "H": harmonic * 100.0, "ZS": zsl * 100.0}


@torch.no_grad()
def batched_logits(
    model: VisibilityAwareCounterfactualEvidenceRouter,
    cls_features: torch.Tensor,
    patch_features: torch.Tensor | None,
    device: torch.device,
    batch_size: int,
    *,
    evidence_enabled: bool,
    unique_swap_with_rival: bool = False,
    role_evidence_permutation: torch.Tensor | None = None,
) -> torch.Tensor:
    rows = []
    classes = torch.arange(model.class_count, device=device)
    model.eval()
    for start in range(0, cls_features.shape[0], batch_size):
        images = cls_features[start : start + batch_size].to(device)
        patches = (
            None
            if patch_features is None
            else patch_features[start : start + batch_size].to(device)
        )
        rows.append(
            model.logits(
                images,
                classes,
                patch_features=patches,
                evidence_enabled=evidence_enabled,
                unique_swap_with_rival=unique_swap_with_rival,
                role_evidence_permutation=role_evidence_permutation,
            ).cpu()
        )
    return torch.cat(rows)


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, message: str) -> None:
        print(message, flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")


def run(
    config_path: Path,
    data_root: Path,
    run_dir: Path,
    expected_commit: str,
    expected_config_sha256: str,
) -> dict:
    commit = clean_commit()
    if commit != expected_commit:
        raise ValueError(f"run commit mismatch: {commit}.")
    config, config_sha256 = load_config(config_path, expected_config_sha256)
    if run_dir.name != config["run_id"]:
        raise ValueError("run directory name must equal RUN-001.")
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite {run_dir}.")
    verify_output_boundary(run_dir)
    paths = resolve_paths(config, data_root)
    input_sha256 = verify_hashes(config, paths, TRAINING_KEYS)
    verify_class_order(config, paths["att_splits"])

    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("formal VCER training requires a visible CUDA device.")
    run_dir.mkdir(parents=True, exist_ok=False)
    logger = RunLogger(run_dir / "training.log")
    seed = int(config["seed"])
    set_determinism(seed)
    logger.emit(f"code_commit={commit}")
    logger.emit(f"config_sha256={config_sha256}")
    logger.emit(f"seed={seed}")

    sentence_embeds = torch.load(paths["sentence_embeds"], map_location="cpu", weights_only=True)
    train_features = torch.load(paths["train_features"], map_location="cpu", weights_only=True)
    train_labels = torch.load(paths["train_labels"], map_location="cpu", weights_only=True).long()
    train_patches = torch.load(paths["train_patches"], map_location="cpu", weights_only=True)
    if tuple(sentence_embeds.shape) != EXPECTED_SENTENCE_SHAPE:
        raise ValueError("sentence cache must have shape [200, 8, 768].")
    if tuple(train_features.shape) != (7057, 768) or tuple(train_patches.shape) != (7057, 576, 768):
        raise ValueError("training CLS/patch cache shape mismatch.")
    if tuple(train_labels.shape) != (7057,):
        raise ValueError("training label shape mismatch.")
    seenclasses = torch.unique(train_labels, sorted=True)
    unseenclasses = torch.arange(200)[~torch.isin(torch.arange(200), seenclasses)]
    if seenclasses.numel() != 150 or unseenclasses.numel() != 50:
        raise ValueError("CUB must expose 150 seen and 50 unseen classes.")

    x2_prototypes, x2_scale, x2_diagnostics = frozen_x2_from_checkpoint(
        sentence_embeds, seenclasses, paths["x2_checkpoint"], config, device
    )
    model = VisibilityAwareCounterfactualEvidenceRouter(
        sentence_embeds,
        x2_prototypes,
        x2_scale,
        rank=int(config["rank"]),
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["lr_stages"][0]["lr"]),
        weight_decay=float(config["weight_decay"]),
    )
    generator = torch.Generator(device="cpu").manual_seed(seed)
    batch_size = int(config["batch_size"])
    stages = config["lr_stages"]
    history = []
    epoch = 0
    for stage in stages:
        for group in optimizer.param_groups:
            group["lr"] = float(stage["lr"])
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=int(stage["epochs"]),
            eta_min=float(stage["eta_min"]),
        )
        for _ in range(int(stage["epochs"])):
            epoch += 1
            model.train()
            permutation = torch.randperm(train_labels.numel(), generator=generator)
            sums = {"loss": 0.0, "classification_loss": 0.0, "unique_causal_loss": 0.0, "preservation_loss": 0.0}
            count = 0
            for start in range(0, permutation.numel(), batch_size):
                indices = permutation[start : start + batch_size]
                images = train_features[indices].to(device)
                patches = train_patches[indices].to(device)
                labels = train_labels[indices].to(device)
                optimizer.zero_grad(set_to_none=True)
                losses = model.training_loss(
                    images,
                    patches,
                    labels,
                    seenclasses.to(device),
                    unique_margin=float(config["unique_margin"]),
                    unique_causal_weight=float(config["unique_causal_weight"]),
                    preserve_weight=float(config["preserve_weight"]),
                )
                if not torch.isfinite(losses["loss"]):
                    raise FloatingPointError(
                        f"non-finite VCER loss at epoch {epoch}, batch {start // batch_size}."
                    )
                losses["loss"].backward()
                for name, parameter in model.named_parameters():
                    if parameter.grad is not None and not torch.isfinite(parameter.grad).all():
                        raise FloatingPointError(f"non-finite VCER gradient: {name}.")
                optimizer.step()
                for name, parameter in model.named_parameters():
                    if not torch.isfinite(parameter).all():
                        raise FloatingPointError(f"non-finite VCER parameter: {name}.")
                size = indices.numel()
                for name in sums:
                    sums[name] += float(losses[name].detach()) * size
                count += size
            scheduler.step()
            row = {"epoch": epoch, **{name: value / count for name, value in sums.items()}, "learning_rate": float(optimizer.param_groups[0]["lr"])}
            history.append(row)
            logger.emit(
                "epoch={epoch} loss={loss:.6f} ce={classification_loss:.6f} "
                "unique={unique_causal_loss:.6f} preserve={preservation_loss:.6f} lr={learning_rate:.8f}".format(**row)
            )

    checkpoint_path = run_dir / "model_best.pth"
    torch.save(
        {
            "model": {name: value.detach().cpu() for name, value in model.state_dict().items()},
            "config": config,
            "code_commit": commit,
            "selected_epoch": epoch,
            "selection_protocol": "fixed_epoch_50_no_official_selection",
        },
        checkpoint_path,
    )
    checkpoint_sha256 = sha256_file(checkpoint_path)
    logger.emit(f"checkpoint_sha256={checkpoint_sha256}")

    input_sha256.update(verify_hashes(config, paths, OFFICIAL_KEYS))
    seen_features = torch.load(paths["seen_features"], map_location="cpu", weights_only=True)
    seen_labels = torch.load(paths["seen_labels"], map_location="cpu", weights_only=True).long()
    seen_patches = torch.load(paths["seen_patches"], map_location="cpu", weights_only=True)
    unseen_features = torch.load(paths["unseen_features"], map_location="cpu", weights_only=True)
    unseen_labels = torch.load(paths["unseen_labels"], map_location="cpu", weights_only=True).long()
    unseen_patches = torch.load(paths["unseen_patches"], map_location="cpu", weights_only=True)
    if tuple(seen_features.shape) != (1764, 768) or tuple(seen_patches.shape) != (1764, 576, 768):
        raise ValueError("official seen cache shape mismatch.")
    if tuple(unseen_features.shape) != (2967, 768) or tuple(unseen_patches.shape) != (2967, 576, 768):
        raise ValueError("official unseen cache shape mismatch.")
    if tuple(seen_labels.shape) != (1764,) or tuple(unseen_labels.shape) != (2967,):
        raise ValueError("official label cache shape mismatch.")
    checked_seen, checked_unseen = load_v5_cub_split(
        paths["res101"], paths["att_splits"], train_labels, seen_labels, unseen_labels, "cpu"
    )
    if not torch.equal(checked_seen, seenclasses) or not torch.equal(checked_unseen, unseenclasses):
        raise ValueError("official split differs from the frozen training class sets.")

    eval_batch = int(config["evaluation_batch_size"])
    baseline_seen = batched_logits(model, seen_features, None, device, eval_batch, evidence_enabled=False)
    baseline_unseen = batched_logits(model, unseen_features, None, device, eval_batch, evidence_enabled=False)
    vcer_seen = batched_logits(model, seen_features, seen_patches, device, eval_batch, evidence_enabled=True)
    vcer_unseen = batched_logits(model, unseen_features, unseen_patches, device, eval_batch, evidence_enabled=True)
    shuffle = torch.tensor(config["role_shuffle_permutation"], device=device)
    shuffled_seen = batched_logits(model, seen_features, seen_patches, device, eval_batch, evidence_enabled=True, role_evidence_permutation=shuffle)
    shuffled_unseen = batched_logits(model, unseen_features, unseen_patches, device, eval_batch, evidence_enabled=True, role_evidence_permutation=shuffle)
    swapped_seen = batched_logits(model, seen_features, seen_patches, device, eval_batch, evidence_enabled=True, unique_swap_with_rival=True)
    swapped_unseen = batched_logits(model, unseen_features, unseen_patches, device, eval_batch, evidence_enabled=True, unique_swap_with_rival=True)
    conditions = {
        "x2": (baseline_seen, baseline_unseen),
        "vcer": (vcer_seen, vcer_unseen),
        "role_shuffle": (shuffled_seen, shuffled_unseen),
        "unique_swap": (swapped_seen, swapped_unseen),
    }
    metrics = {
        name: metrics_from_logits(
            seen_logits,
            unseen_logits,
            seen_labels,
            unseen_labels,
            seenclasses,
            unseenclasses,
        )
        for name, (seen_logits, unseen_logits) in conditions.items()
    }
    expected_x2 = config["x2_identity"]["metrics_percent"]
    if any(abs(metrics["x2"][key] - float(expected_x2[key])) > 1e-4 for key in ("U", "S", "H", "ZS")):
        raise RuntimeError(f"reconstructed X2 metrics mismatch: {metrics['x2']}.")

    result = {
        "experiment_id": config["experiment_id"],
        "run_id": config["run_id"],
        "status": "completed",
        "formal_evidence": False,
        "evidence_label": "official-test-guided development",
        "official_test_used_for_selection": False,
        "official_test_evaluations": {
            "x2": 1,
            "vcer": 1,
            "role_shuffle": 1,
            "unique_swap": 1,
        },
        "official_test_policy": config["official_test_policy"],
        "code_commit": commit,
        "config_sha256": config_sha256,
        "seed": seed,
        "selected_epoch": epoch,
        "selection_protocol": "fixed_epoch_50_no_official_selection",
        "input_sha256": input_sha256,
        "checkpoint_sha256": checkpoint_sha256,
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "x2_diagnostics": x2_diagnostics,
        "metrics_percent": metrics,
        "delta_vs_x2_H": metrics["vcer"]["H"] - metrics["x2"]["H"],
        "delta_vs_role_shuffle_H": metrics["vcer"]["H"] - metrics["role_shuffle"]["H"],
        "delta_vs_unique_swap_H": metrics["vcer"]["H"] - metrics["unique_swap"]["H"],
        "history": history,
    }
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    logger.emit("X2 U={U:.6f} S={S:.6f} H={H:.6f} ZS={ZS:.6f}".format(**metrics["x2"]))
    logger.emit("VCER U={U:.6f} S={S:.6f} H={H:.6f} ZS={ZS:.6f}".format(**metrics["vcer"]))
    logger.emit(f"delta_vs_x2_H={result['delta_vs_x2_H']:.6f}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    args = parser.parse_args()
    run(
        args.config.resolve(),
        args.data_root.resolve(),
        args.run_dir.resolve(),
        args.expected_commit,
        args.expected_config_sha256,
    )


if __name__ == "__main__":
    main()
