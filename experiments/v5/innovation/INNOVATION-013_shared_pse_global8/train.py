"""Train one shared PSE on the frozen 8-sentence global CLIP baseline."""

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
import torch.nn as nn
import torch.nn.functional as F
import yaml
from torch.utils.data import DataLoader, TensorDataset


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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
EXPECTED_SENTENCE_SHAPE = (200, 8, 768)
EXPECTED_CONFIG_SHA256 = "e38bd1f760b0106b617cc5fad7d1dbca040460dc8bb4966f639da327958e3413"


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
            "--untracked-files=no",
        ],
        text=True,
    ).strip()
    if dirty:
        raise ValueError("formal training requires a clean tracked worktree.")
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
    if config.get("score_path") != "clip_cls_x_shared_pse_global_only":
        raise ValueError("score_path must keep the single global-only path.")
    return config, config_sha256


def verify_expected_commit(actual_commit: str, expected_commit: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise ValueError("--expected-commit must be one full lowercase Git SHA.")
    if actual_commit != expected_commit:
        raise ValueError(
            f"current clean commit {actual_commit} does not match "
            f"--expected-commit {expected_commit}."
        )


def resolve_input_paths(config: dict) -> dict[str, Path]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing PSE input: " + ", ".join(missing))
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


class SharedPSE(nn.Module):
    """One class-agnostic sentence self-attention and role pooling module."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        heads: int,
        dropout: float,
        residual_cap: float,
        temperature: float,
    ):
        super().__init__()
        if tuple(sentence_embeds.shape) != EXPECTED_SENTENCE_SHAPE:
            raise ValueError(
                f"sentence_embeds must be {EXPECTED_SENTENCE_SHAPE}, "
                f"got {tuple(sentence_embeds.shape)}."
            )
        if not torch.isfinite(sentence_embeds).all():
            raise ValueError("sentence_embeds contains a non-finite value.")
        if 768 % int(heads):
            raise ValueError("PSE heads must divide 768.")
        if not 0.0 < float(residual_cap) <= 1.0:
            raise ValueError("residual_cap must be in (0, 1].")
        if float(temperature) <= 0.0:
            raise ValueError("temperature must be positive.")

        normalized = F.normalize(sentence_embeds.detach().float(), dim=-1)
        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.attention = nn.MultiheadAttention(
            768, int(heads), dropout=float(dropout), batch_first=True
        )
        self.context_projection = nn.Linear(768, 768)
        self.role_scorer = nn.Sequential(
            nn.Linear(768, 192), nn.GELU(), nn.Linear(192, 1)
        )
        nn.init.zeros_(self.role_scorer[-1].weight)
        nn.init.zeros_(self.role_scorer[-1].bias)
        self.residual_gate = nn.Parameter(torch.zeros(()))
        self.residual_cap = float(residual_cap)
        self.temperature = float(temperature)

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.sentence_embeds.mean(dim=1), dim=-1)

    def prototypes(self, return_diagnostics: bool = False):
        attended, attention_weights = self.attention(
            self.sentence_embeds,
            self.sentence_embeds,
            self.sentence_embeds,
            need_weights=True,
            average_attn_weights=False,
        )
        contextual = F.normalize(
            self.sentence_embeds + self.context_projection(attended), dim=-1
        )
        role_weights = F.softmax(self.role_scorer(contextual).squeeze(-1), dim=1)
        pooled = (role_weights.unsqueeze(-1) * contextual).sum(dim=1)
        base = self.base_prototypes()
        gate = self.residual_cap * torch.tanh(self.residual_gate)
        adapted = F.normalize(base + gate * (pooled - base), dim=-1)
        if return_diagnostics:
            return adapted, {
                "base": base,
                "role_weights": role_weights,
                "attention_weights": attention_weights,
                "gate": gate,
            }
        return adapted

    def logits(self, image_features: torch.Tensor, class_ids=None) -> torch.Tensor:
        prototypes = self.prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(0, class_ids.to(prototypes.device))
        return F.normalize(image_features.float(), dim=-1) @ prototypes.T / self.temperature


def per_class_accuracy(labels, predictions, classes) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"evaluation cache has no class {int(class_id)}.")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean().item())


@torch.no_grad()
def evaluate(model, tensors, seenclasses, unseenclasses, device) -> dict[str, float]:
    model.eval()
    seen_logits = model.logits(tensors["seen_features"].to(device))
    unseen_logits = model.logits(tensors["unseen_features"].to(device))
    seen_predictions = seen_logits.argmax(dim=1).cpu()
    unseen_predictions = unseen_logits.argmax(dim=1).cpu()
    zsl_predictions = unseenclasses[
        unseen_logits[:, unseenclasses.to(device)].argmax(dim=1).cpu()
    ]
    seen_accuracy = per_class_accuracy(tensors["seen_labels"], seen_predictions, seenclasses)
    unseen_accuracy = per_class_accuracy(
        tensors["unseen_labels"], unseen_predictions, unseenclasses
    )
    zsl_accuracy = per_class_accuracy(tensors["unseen_labels"], zsl_predictions, unseenclasses)
    denominator = seen_accuracy + unseen_accuracy
    harmonic = 2 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    return {
        "U": unseen_accuracy * 100.0,
        "S": seen_accuracy * 100.0,
        "H": harmonic * 100.0,
        "ZS": zsl_accuracy * 100.0,
    }


def run(config_path: Path, run_dir: Path, expected_commit: str) -> dict:
    code_commit = get_clean_commit()
    verify_expected_commit(code_commit, expected_commit)
    config, config_sha256 = load_config(config_path)
    paths = resolve_input_paths(config)
    input_sha256 = verify_input_contract(config, paths)
    if run_dir.exists():
        raise FileExistsError(f"refusing to reuse run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)

    seed = int(config["seed"])
    print(f"代码 commit：{code_commit}")
    print(f"配置 SHA-256：{config_sha256}")
    print(f"随机种子：{seed}")
    set_determinism(seed)
    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("formal Shared PSE training requires a visible CUDA device.")

    tensors = {
        name: torch.load(path, map_location="cpu", weights_only=True)
        for name, path in paths.items()
        if name not in {"res101", "att_splits"}
    }
    seenclasses, unseenclasses = load_v5_cub_split(
        paths["res101"],
        paths["att_splits"],
        tensors["train_labels"],
        tensors["seen_labels"],
        tensors["unseen_labels"],
        "cpu",
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
    loader_generator = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(
        train_dataset,
        batch_size=int(config["batch_size"]),
        shuffle=True,
        num_workers=0,
        generator=loader_generator,
    )

    model = SharedPSE(
        tensors["sentence_embeds"],
        heads=int(config["pse_heads"]),
        dropout=float(config["pse_dropout"]),
        residual_cap=float(config["residual_cap"]),
        temperature=float(config["temperature"]),
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
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
            logits = model.logits(features, seenclasses)
            loss = F.cross_entropy(logits, targets)
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
        gate = float(
            (model.residual_cap * torch.tanh(model.residual_gate)).detach().cpu()
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": training_loss,
                "validation_loss": validation_loss,
                "gate": gate,
            }
        )
        print(
            f"epoch={epoch} train_loss={training_loss:.6f} "
            f"validation_loss={validation_loss:.6f} gate={gate:.6f}"
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
    metrics = evaluate(model, tensors, seenclasses, unseenclasses, device)
    model.eval()
    with torch.no_grad():
        adapted, diagnostics = model.prototypes(return_diagnostics=True)
        base = diagnostics["base"]
        cosine = F.cosine_similarity(base, adapted, dim=-1).cpu()
        role_weights = diagnostics["role_weights"].cpu()
        attention = diagnostics["attention_weights"].mean(dim=(0, 1)).cpu()

    checkpoint_path = run_dir / "model_best.pth"
    torch.save(
        {
            "model": {name: value.detach().cpu() for name, value in model.state_dict().items()},
            "config": config,
            "code_commit": code_commit,
            "best_epoch": best_epoch,
        },
        checkpoint_path,
    )
    result = {
        "experiment_id": "V5-INNOVATION-013",
        "run_id": "RUN-001",
        "code_commit": code_commit,
        "config_sha256": config_sha256,
        "seed": seed,
        "score_path": config["score_path"],
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "input_sha256": input_sha256,
        "class_order_sha256": config["class_order_sha256"],
        "validation_indices_sha256": split_sha256,
        "best_epoch_by_seen_validation_ce": best_epoch,
        "best_validation_loss": best_validation_loss,
        "metrics_percent": metrics,
        "baseline_H": 64.16403868322334,
        "delta_H": metrics["H"] - 64.16403868322334,
        "diagnostics": {
            "residual_gate": float(diagnostics["gate"].cpu()),
            "role_weight_mean": role_weights.mean(dim=0).tolist(),
            "role_weight_std": role_weights.std(dim=0).tolist(),
            "attention_mean_8x8": attention.tolist(),
            "base_adapted_cosine_seen_mean": float(cosine[seenclasses].mean()),
            "base_adapted_cosine_unseen_mean": float(cosine[unseenclasses].mean()),
        },
        "history": history,
    }
    result["checkpoint_sha256"] = sha256_file(checkpoint_path)
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
    print(f"best_epoch={best_epoch} delta_H={result['delta_H']:.6f}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.run_dir.resolve(), args.expected_commit)


if __name__ == "__main__":
    main()
