"""Run the frozen local strong-PSE comparisons on CUB CLIP features."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
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
EXPECTED_CONFIG_SHA256 = "dde54ce821e536a4a4617e517cac1dc13817495a070909c7c7356743dcaad840"
TRAINING_KEYS = ("sentence_embeds", "train_features", "train_labels", "res101", "att_splits")
OFFICIAL_KEYS = ("seen_features", "seen_labels", "unseen_features", "unseen_labels")


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
    if config.get("score_path") != "clip_cls_x_strong_pse_global_only":
        raise ValueError("score_path must keep the single clean global-only path.")
    conditions = config.get("conditions")
    expected_keys = {
        "PSE-A", "PSE-B", "PSE-C", "PSE-X1", "PSE-X2",
        "TG-VPR", "TG-VPR-H1", "TG-VPR-H3", "TG-VPR-H8",
    }
    if not isinstance(conditions, dict) or set(conditions) != expected_keys:
        raise ValueError("config must freeze exactly PSE-A/B/C, PSE-X1/X2, and TG-VPR.")
    expected = {
        "PSE-A": {"run_id": "RUN-001", "mode": "uniform", "topology_weight": 0.1},
        "PSE-B": {"run_id": "RUN-002", "mode": "uniform", "topology_weight": 0.0},
        "PSE-C": {"run_id": "RUN-003", "mode": "dcra", "topology_weight": 0.1},
        "PSE-X1": {
            "run_id": "RUN-004",
            "mode": "uniform",
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
        "PSE-X2": {
            "run_id": "RUN-005",
            "mode": "legacy_uniform",
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
        "TG-VPR": {
            "run_id": "RUN-006",
            "mode": "tg_vpr",
            "value_heads": 4,
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
        "TG-VPR-H1": {
            "run_id": "RUN-007",
            "mode": "tg_vpr",
            "value_heads": 1,
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
        "TG-VPR-H3": {
            "run_id": "RUN-008",
            "mode": "tg_vpr",
            "value_heads": 3,
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
        "TG-VPR-H8": {
            "run_id": "RUN-009",
            "mode": "tg_vpr",
            "value_heads": 8,
            "topology_weight": 0.1,
            "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
        },
    }
    if conditions != expected:
        raise ValueError("frozen PSE conditions differ from the paired plan.")
    return config, config_sha256


def verify_expected_commit(actual_commit: str, expected_commit: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise ValueError("--expected-commit must be one full lowercase Git SHA.")
    if actual_commit != expected_commit:
        raise ValueError(
            f"current clean commit {actual_commit} does not match "
            f"--expected-commit {expected_commit}."
        )


def verify_run_identity(condition: str, run_id: str, run_dir: Path, config: dict) -> None:
    if not re.fullmatch(r"RUN-[0-9]{3}", run_id):
        raise ValueError("--run-id must use the RUN-xxx format.")
    if condition not in config["conditions"]:
        raise ValueError("--condition is not frozen in config.")
    if run_id != config["conditions"][condition]["run_id"]:
        raise ValueError("--run-id does not match the selected frozen condition.")
    if run_dir.name != run_id:
        raise ValueError("--run-dir final directory name must equal --run-id.")


def resolve_input_paths(config: dict) -> dict[str, Path]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing PSE input: " + ", ".join(missing))
    return paths


def verify_input_contract(
    config: dict, paths: dict[str, Path], keys: tuple[str, ...]
) -> dict[str, str]:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every configured input exactly once.")
    actual = {name: sha256_file(paths[name]) for name in keys}
    mismatch = [name for name in keys if expected[name] != actual[name]]
    if mismatch:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatch))

    split_data = sio.loadmat(paths["att_splits"], variable_names=["allclasses_names"])
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


def legacy_batch_indices(
    sample_count: int, batch_size: int, generator: torch.Generator
) -> torch.Tensor:
    if not 0 < batch_size <= sample_count:
        raise ValueError("batch_size must be within the training sample count.")
    return torch.randperm(sample_count, generator=generator)[:batch_size]


def frozen_visual_centroids(
    features: torch.Tensor,
    labels: torch.Tensor,
    indices: torch.Tensor,
    classes: torch.Tensor,
) -> torch.Tensor:
    """Compute one train-only frozen CLIP centroid for every adapted class."""
    selected_features = F.normalize(features[indices].detach().float(), dim=-1)
    selected_labels = labels[indices].detach().cpu().long()
    centroids = []
    for class_id in classes.detach().cpu().long():
        mask = selected_labels == class_id
        if not mask.any():
            raise ValueError(f"no centroid samples for class {int(class_id)}.")
        centroids.append(F.normalize(selected_features[mask].mean(dim=0), dim=0))
    return torch.stack(centroids)


class StrongRolePSE(nn.Module):
    """Old strong uniform value path plus bounded discriminative role attention."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        adapted_classes: torch.Tensor,
        visual_centroids: torch.Tensor,
        mode: str,
        dropout: float,
        inner_ratio: float,
        outer_ratio: float,
        dcra_mix: float,
        temperature: float,
        value_heads: int = 4,
    ):
        super().__init__()
        if tuple(sentence_embeds.shape) != EXPECTED_SENTENCE_SHAPE:
            raise ValueError(
                f"sentence_embeds must be {EXPECTED_SENTENCE_SHAPE}, "
                f"got {tuple(sentence_embeds.shape)}."
            )
        if not torch.isfinite(sentence_embeds).all():
            raise ValueError("sentence_embeds contains a non-finite value.")
        classes = torch.as_tensor(adapted_classes).detach().cpu().long().sort().values
        if classes.ndim != 1 or classes.numel() < 2 or classes.unique().numel() != classes.numel():
            raise ValueError("adapted_classes must be a unique one-dimensional class set.")
        centroids = F.normalize(torch.as_tensor(visual_centroids).detach().float(), dim=-1)
        if tuple(centroids.shape) != (classes.numel(), 768):
            raise ValueError("visual_centroids must align with adapted_classes.")
        if mode not in {"uniform", "dcra", "legacy_uniform", "tg_vpr"}:
            raise ValueError("mode must be uniform, dcra, legacy_uniform, or tg_vpr.")
        if not 0.0 < float(inner_ratio) < 1.0 or not 0.0 < float(outer_ratio) < 1.0:
            raise ValueError("inner_ratio and outer_ratio must be in (0, 1).")
        if not 0.0 <= float(dcra_mix) <= 1.0:
            raise ValueError("dcra_mix must be in [0, 1].")
        if float(temperature) <= 0.0:
            raise ValueError("temperature must be positive.")
        if isinstance(value_heads, bool) or not isinstance(value_heads, int):
            raise ValueError("value_heads must be an integer.")
        if value_heads <= 0 or 768 % value_heads != 0:
            raise ValueError("value_heads must be a positive divisor of 768.")

        normalized = F.normalize(sentence_embeds.detach().float(), dim=-1)
        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.register_buffer("adapted_classes", classes, persistent=True)
        self.register_buffer("visual_centroids", centroids, persistent=True)
        if mode == "legacy_uniform":
            # Preserve the production Uniform-PSE parameter initialization and
            # attention-dropout path, including unused Q/K parameters.
            self.legacy_attention = nn.MultiheadAttention(
                embed_dim=768,
                num_heads=4,
                dropout=float(dropout),
                batch_first=True,
            )
            self.post_projection = nn.Linear(768, 768)
        elif mode == "tg_vpr":
            # Configurable equal-width Value subspaces; no Query/Key parameters.
            self.tg_value_projection = nn.Linear(768, 768)
            self.tg_output_projection = nn.Linear(768, 768)
            self.post_projection = nn.Linear(768, 768)
        else:
            self.value_projection = nn.Linear(768, 768)
            self.output_projection = nn.Linear(768, 768)
            self.post_projection = nn.Linear(768, 768)
        self.dropout = nn.Dropout(float(dropout))
        self.layer_norm = nn.LayerNorm(768)
        self.mode = mode
        self.inner_ratio = float(inner_ratio)
        self.outer_ratio = float(outer_ratio)
        self.dcra_mix = float(dcra_mix)
        self.temperature = float(temperature)
        self.value_heads = value_heads
        self.logit_scale = nn.Parameter(torch.tensor(math.log(1.0 / self.temperature)))
        if mode == "tg_vpr":
            # [local-six, unique, global], shared by every class.
            self.semantic_group_logits = nn.Parameter(torch.zeros(3))

    def scale(self) -> torch.Tensor:
        return self.logit_scale.exp().clamp(max=100.0)

    def base_vectors(self) -> torch.Tensor:
        return self.sentence_embeds.mean(dim=1)

    def semantic_group_weights(self) -> torch.Tensor:
        if self.mode != "tg_vpr":
            return self.sentence_embeds.new_full((3,), 1.0 / 3.0)
        return F.softmax(self.semantic_group_logits, dim=0)

    def semantic_group_vectors(self) -> torch.Tensor:
        local = F.normalize(self.sentence_embeds[:, :6].mean(dim=1), dim=-1)
        # Frozen cache order: six local roles, overall appearance, unique feature.
        unique = F.normalize(self.sentence_embeds[:, 7], dim=-1)
        global_appearance = F.normalize(self.sentence_embeds[:, 6], dim=-1)
        return torch.stack((local, unique, global_appearance), dim=1)

    def candidate_base_vectors(self) -> torch.Tensor:
        # Keep the same Mean8 base for X1/X2 so the paired result isolates the
        # PSE training operator rather than changing unseen text aggregation.
        base = self.base_vectors()
        if self.mode != "tg_vpr":
            return base
        group_weights = self.semantic_group_weights()
        groups = self.semantic_group_vectors()
        grouped = F.normalize((group_weights.view(1, 3, 1) * groups).sum(dim=1), dim=-1)
        candidate = base.clone()
        candidate[self.adapted_classes] = grouped.index_select(0, self.adapted_classes)
        return candidate

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.base_vectors(), dim=-1)

    def transformed_roles(self) -> torch.Tensor:
        if self.mode == "tg_vpr":
            x = self.semantic_group_vectors().index_select(0, self.adapted_classes)
            batch, groups, dim = x.shape
            heads = self.value_heads
            head_dim = dim // heads
            value = self.tg_value_projection(x)
            value = value.view(batch, groups, heads, head_dim).transpose(1, 2)
            group_weights = self.semantic_group_weights()
            mixing = group_weights.view(1, 1, 1, groups).expand(
                batch, heads, groups, groups
            )
            mixing = F.dropout(
                mixing,
                p=float(self.dropout.p),
                training=self.training,
            )
            context = torch.einsum("bhqg,bhgd->bhqd", mixing, value)
            context = context.transpose(1, 2).contiguous().view(batch, groups, dim)
            context = self.tg_output_projection(context)
            context = self.dropout(self.post_projection(context))
            mixed = self.inner_ratio * context + (1.0 - self.inner_ratio) * x
            return self.layer_norm(2.0 * mixed)
        if self.mode == "legacy_uniform":
            x = self.sentence_embeds.index_select(0, self.adapted_classes)
            batch, tokens, dim = x.shape
            heads = self.legacy_attention.num_heads
            head_dim = dim // heads
            _, _, value_weight = self.legacy_attention.in_proj_weight.chunk(3, dim=0)
            if self.legacy_attention.in_proj_bias is None:
                value_bias = None
            else:
                _, _, value_bias = self.legacy_attention.in_proj_bias.chunk(3, dim=0)
            value = F.linear(x, value_weight, value_bias)
            value = value.view(batch, tokens, heads, head_dim).transpose(1, 2)
            weights = x.new_full((batch, heads, tokens, tokens), 1.0 / tokens)
            weights = F.dropout(
                weights,
                p=float(self.legacy_attention.dropout),
                training=self.training,
            )
            context = torch.matmul(weights, value)
            context = context.transpose(1, 2).contiguous().view(batch, tokens, dim)
            attention_output = F.linear(
                context,
                self.legacy_attention.out_proj.weight,
                self.legacy_attention.out_proj.bias,
            )
            context = self.dropout(self.post_projection(attention_output))
            mixed = self.inner_ratio * context + (1.0 - self.inner_ratio) * x
            return self.layer_norm(2.0 * mixed)
        values = self.value_projection(self.sentence_embeds)
        context = self.output_projection(values.mean(dim=1))
        context = self.dropout(self.post_projection(context)).unsqueeze(1)
        mixed = self.inner_ratio * context + (1.0 - self.inner_ratio) * self.sentence_embeds
        return self.layer_norm(2.0 * mixed)

    def role_attention(self, transformed: torch.Tensor) -> tuple[torch.Tensor, dict]:
        count = transformed.shape[1]
        if self.mode in {"uniform", "legacy_uniform"}:
            weights = transformed.new_full((self.adapted_classes.numel(), count), 1.0 / count)
            return weights, {"margins": None, "rival_class_ids": None}
        if self.mode == "tg_vpr":
            group_weights = self.semantic_group_weights()
            if count != 3:
                raise RuntimeError("TG-VPR transformed roles must be [local, unique, global].")
            weights = group_weights.unsqueeze(0).expand(self.adapted_classes.numel(), -1)
            return weights, {
                "margins": None,
                "rival_class_ids": None,
                "semantic_group_weights": group_weights,
            }

        own_roles = transformed.index_select(0, self.adapted_classes)
        by_role = transformed.transpose(0, 1)
        scores = torch.einsum("ad,rcd->arc", self.visual_centroids, by_role)
        own_ids = self.adapted_classes.to(scores.device)
        row_ids = torch.arange(own_ids.numel(), device=scores.device)
        scores[row_ids[:, None], torch.arange(count, device=scores.device)[None, :], own_ids[:, None]] = float("-inf")
        rival_scores, rival_ids = scores.max(dim=-1)
        positive = torch.einsum("ad,ard->ar", self.visual_centroids, own_roles)
        margins = positive - rival_scores
        standardized = (margins - margins.mean(dim=1, keepdim=True)) / margins.std(
            dim=1, keepdim=True, unbiased=False
        ).clamp_min(1e-6)
        selective = F.softmax(standardized, dim=1)
        weights = (1.0 - self.dcra_mix) / count + self.dcra_mix * selective
        return weights, {"margins": margins, "rival_class_ids": rival_ids}

    def prototype_components(self) -> tuple[torch.Tensor, torch.Tensor, dict]:
        transformed = self.transformed_roles()
        role_weights, evidence = self.role_attention(transformed)
        base_vectors = self.candidate_base_vectors()
        base_scale = base_vectors.new_ones((base_vectors.shape[0],))
        base_scale[self.adapted_classes] = 1.0 - self.outer_ratio
        base_part = base_scale.unsqueeze(-1) * base_vectors
        role_part = transformed.new_zeros(
            self.sentence_embeds.shape[0], transformed.shape[1], transformed.shape[-1]
        )
        if self.mode == "tg_vpr":
            adapted_roles = F.normalize(transformed, dim=-1)
        elif self.mode == "legacy_uniform":
            adapted_roles = transformed
        else:
            adapted_roles = transformed.index_select(0, self.adapted_classes)
        role_part[self.adapted_classes] = (
            self.outer_ratio
            * role_weights.unsqueeze(-1)
            * adapted_roles
        )
        enhanced = base_part + role_part.sum(dim=1)
        evidence.update(
            {
                "role_weights": role_weights,
                "transformed_roles": transformed,
                "base_part": base_part,
                "role_part": role_part,
            }
        )
        return enhanced, role_weights, evidence

    def prototypes(self, return_diagnostics: bool = False):
        enhanced, role_weights, evidence = self.prototype_components()
        adapted = F.normalize(enhanced, dim=-1)
        if return_diagnostics:
            return adapted, {
                "base": self.base_prototypes(),
                "role_weights": role_weights,
                "margins": evidence["margins"],
                "rival_class_ids": evidence["rival_class_ids"],
                "transformed_roles": evidence["transformed_roles"],
                "semantic_group_weights": evidence.get("semantic_group_weights"),
            }
        return adapted

    def topology_loss(self) -> torch.Tensor:
        base = self.base_prototypes()
        adapted = self.prototypes()
        base_sim = base @ base.T
        adapted_sim = adapted @ adapted.T
        off_diag = ~torch.eye(base.shape[0], dtype=torch.bool, device=base.device)
        x = base_sim.detach()[off_diag]
        y = adapted_sim[off_diag]
        x = x - x.mean()
        y = y - y.mean()
        correlation = (x * y).sum() / (
            torch.sqrt((x.square()).sum() + 1e-8)
            * torch.sqrt((y.square()).sum() + 1e-8)
        )
        return 1.0 - correlation

    def logits(self, image_features: torch.Tensor, class_ids=None) -> torch.Tensor:
        prototypes = self.prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(0, class_ids.to(prototypes.device))
        return F.normalize(image_features.float(), dim=-1) @ prototypes.T * self.scale()

    def logit_components(self, image_features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Return exact base and role addends of the normalized final logits."""
        enhanced, _, evidence = self.prototype_components()
        denominator = enhanced.norm(dim=-1).clamp_min(1e-12)
        images = F.normalize(image_features.float(), dim=-1)
        base_logits = (images @ evidence["base_part"].T) / denominator.unsqueeze(0)
        role_logits = torch.einsum("bd,crd->bcr", images, evidence["role_part"])
        role_logits = role_logits / denominator.view(1, -1, 1)
        return base_logits * self.scale(), role_logits * self.scale()


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


def build_checkpoint(
    model: StrongRolePSE,
    config: dict,
    code_commit: str,
    best_epoch: int,
    run_id: str,
    condition: str,
) -> dict:
    return {
        "model": {name: value.detach().cpu() for name, value in model.state_dict().items()},
        "config": config,
        "code_commit": code_commit,
        "best_epoch": int(best_epoch),
        "run_id": run_id,
        "condition": condition,
        "value_heads": model.value_heads,
    }


@torch.no_grad()
def evaluate(
    model, tensors, seenclasses, unseenclasses, device, *, use_base: bool = False
) -> dict[str, float]:
    model.eval()
    prototypes = model.base_prototypes() if use_base else model.prototypes()
    seen_logits = F.normalize(tensors["seen_features"].to(device).float(), dim=-1) @ prototypes.T * model.scale()
    unseen_logits = F.normalize(tensors["unseen_features"].to(device).float(), dim=-1) @ prototypes.T * model.scale()
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


def run(
    config_path: Path,
    run_dir: Path,
    expected_commit: str,
    run_id: str,
    condition: str,
) -> dict:
    code_commit = get_clean_commit()
    verify_expected_commit(code_commit, expected_commit)
    config, config_sha256 = load_config(config_path)
    verify_run_identity(condition, run_id, run_dir, config)
    run_dir = run_dir.resolve()
    worktree_output = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"], text=True
    )
    for line in worktree_output.splitlines():
        if line.startswith("worktree "):
            worktree = Path(line.split(" ", 1)[1]).resolve()
            try:
                run_dir.relative_to(worktree)
            except ValueError:
                continue
            raise ValueError("run directory must stay outside every Git worktree.")
    paths = resolve_input_paths(config)
    input_sha256 = verify_input_contract(config, paths, TRAINING_KEYS)
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
        raise RuntimeError("PSE-A/B/C training requires a visible CUDA device.")

    tensors = {
        name: torch.load(path, map_location="cpu", weights_only=True)
        for name, path in paths.items()
        if name in {"sentence_embeds", "train_features", "train_labels"}
    }
    if tuple(tensors["sentence_embeds"].shape) != EXPECTED_SENTENCE_SHAPE:
        raise ValueError("sentence cache is not the frozen [200, 8, 768] tensor.")
    seenclasses = torch.unique(tensors["train_labels"].long(), sorted=True)
    allclasses = torch.arange(200, dtype=torch.long)
    unseenclasses = allclasses[~torch.isin(allclasses, seenclasses)]
    if seenclasses.numel() != 150 or unseenclasses.numel() != 50:
        raise ValueError("CUB must expose 150 seen and 50 unseen classes.")
    selected_condition = config["conditions"][condition]
    full_seen_protocol = (
        selected_condition.get("training_protocol")
        == "full_seen_fixed_epoch50_legacy_sampling"
    )
    if full_seen_protocol:
        train_indices = torch.arange(tensors["train_labels"].numel(), dtype=torch.long)
        validation_indices = torch.empty(0, dtype=torch.long)
    else:
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
    train_loader = None
    if not full_seen_protocol:
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
    centroids = frozen_visual_centroids(
        tensors["train_features"], tensors["train_labels"], train_indices, seenclasses
    )
    model = StrongRolePSE(
        tensors["sentence_embeds"],
        seenclasses,
        centroids,
        mode=selected_condition["mode"],
        dropout=float(config["pse_dropout"]),
        inner_ratio=float(config["pse_inner_ratio"]),
        outer_ratio=float(config["pse_outer_ratio"]),
        dcra_mix=float(config["dcra_mix"]),
        temperature=float(config["temperature"]),
        value_heads=int(selected_condition.get("value_heads", 4)),
    ).to(device)
    stages = config["lr_stages"]
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages must be a non-empty list.")
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=float(stages[0]["lr"]),
        weight_decay=float(config["weight_decay"]),
    )
    stage_boundaries = []
    total = 0
    for stage in stages:
        total += int(stage["epochs"])
        stage_boundaries.append(total)
    if full_seen_protocol and total != 50:
        raise ValueError("full-seen diagnostic protocol requires exactly 50 epochs.")
    active_stage = 0
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(stages[0]["epochs"]), eta_min=float(stages[0]["eta_min"])
    )

    validation_features = None
    validation_targets = None
    if not full_seen_protocol:
        validation_features = tensors["train_features"][validation_indices].to(device).float()
        validation_targets = global_to_seen[
            tensors["train_labels"][validation_indices].long()
        ].to(device)
    best_state = None
    best_validation_loss = float("inf")
    best_epoch = 0
    history = []
    sampling_generator = None
    if full_seen_protocol:
        sampling_generator = torch.Generator(device="cpu").manual_seed(seed)
    for epoch in range(1, total + 1):
        target_stage = next(i for i, boundary in enumerate(stage_boundaries) if epoch <= boundary)
        if target_stage != active_stage:
            active_stage = target_stage
            stage = stages[active_stage]
            for group in optimizer.param_groups:
                group["lr"] = float(stage["lr"])
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=int(stage["epochs"]),
                eta_min=float(stage["eta_min"]),
            )
        model.train()
        loss_sum = 0.0
        ce_sum = 0.0
        topology_sum = 0.0
        sample_count = 0
        if full_seen_protocol:
            steps = tensors["train_labels"].numel() // int(config["batch_size"])

            def batches():
                for _ in range(steps):
                    indices = legacy_batch_indices(
                        tensors["train_labels"].numel(),
                        int(config["batch_size"]),
                        sampling_generator,
                    )
                    yield (
                        tensors["train_features"][indices].float(),
                        global_to_seen[tensors["train_labels"][indices].long()],
                    )

            epoch_batches = batches()
        else:
            epoch_batches = train_loader
        for features, targets in epoch_batches:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model.logits(features, seenclasses)
            ce_loss = F.cross_entropy(logits, targets)
            topology_loss = model.topology_loss()
            loss = ce_loss + float(selected_condition["topology_weight"]) * topology_loss
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * features.size(0)
            ce_sum += float(ce_loss.detach()) * features.size(0)
            topology_sum += float(topology_loss.detach()) * features.size(0)
            sample_count += features.size(0)
        scheduler.step()

        model.eval()
        validation_loss = None
        if not full_seen_protocol:
            with torch.no_grad():
                validation_loss = float(
                    F.cross_entropy(
                        model.logits(validation_features, seenclasses), validation_targets
                    ).cpu()
                )
        training_loss = loss_sum / sample_count
        history.append(
            {
                "epoch": epoch,
                "train_loss": training_loss,
                "train_ce": ce_sum / sample_count,
                "train_topology": topology_sum / sample_count,
                "validation_loss": validation_loss,
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
            }
        )
        validation_text = (
            "none_fixed_epoch50"
            if validation_loss is None
            else f"{validation_loss:.6f}"
        )
        print(
            f"epoch={epoch} train_loss={training_loss:.6f} "
            f"validation_loss={validation_text} topology={topology_sum/sample_count:.6f}"
        )
        if full_seen_protocol and epoch == total:
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
        elif (
            not full_seen_protocol
            and validation_loss < best_validation_loss - float(config["min_delta"])
        ):
            best_validation_loss = validation_loss
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())

    if best_state is None:
        raise RuntimeError("training did not produce a validation checkpoint.")
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        adapted, diagnostics = model.prototypes(return_diagnostics=True)
        base = diagnostics["base"]
        cosine = F.cosine_similarity(base, adapted, dim=-1).cpu()
        role_weights = diagnostics["role_weights"].cpu()

    checkpoint_path = run_dir / "model_best.pth"
    torch.save(
        build_checkpoint(model, config, code_commit, best_epoch, run_id, condition),
        checkpoint_path,
    )
    # Official caches are first hashed and loaded only after checkpoint selection
    # and checkpoint publication are complete.
    input_sha256.update(verify_input_contract(config, paths, OFFICIAL_KEYS))
    tensors.update(
        {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in OFFICIAL_KEYS
        }
    )
    checked_seen, checked_unseen = load_v5_cub_split(
        paths["res101"],
        paths["att_splits"],
        tensors["train_labels"],
        tensors["seen_labels"],
        tensors["unseen_labels"],
        "cpu",
    )
    if not torch.equal(checked_seen, seenclasses) or not torch.equal(checked_unseen, unseenclasses):
        raise RuntimeError("official split differs from the frozen training class sets.")
    baseline_metrics = evaluate(
        model, tensors, seenclasses, unseenclasses, device, use_base=True
    )
    metrics = evaluate(model, tensors, seenclasses, unseenclasses, device)
    delta = {key: metrics[key] - baseline_metrics[key] for key in ("U", "S", "H", "ZS")}
    result = {
        "experiment_id": "LOCAL-DCRA-PSE-20260816",
        "run_id": run_id,
        "condition": condition,
        "value_heads": model.value_heads,
        "formal_evidence": False,
        "official_test_used_for_selection": False,
        "official_test_evaluations": {"mean8": 1, condition: 1},
        "code_commit": code_commit,
        "config_sha256": config_sha256,
        "seed": seed,
        "score_path": config["score_path"],
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "input_sha256": input_sha256,
        "class_order_sha256": config["class_order_sha256"],
        "validation_indices_sha256": split_sha256,
        "selection_protocol": (
            "fixed_epoch_50_no_validation"
            if full_seen_protocol
            else "seen_internal_validation_ce"
        ),
        "selected_epoch": best_epoch,
        "best_epoch_by_seen_validation_ce": None if full_seen_protocol else best_epoch,
        "best_validation_loss": None if full_seen_protocol else best_validation_loss,
        "baseline_metrics_percent": baseline_metrics,
        "metrics_percent": metrics,
        "delta_percent_points": delta,
        "diagnostics": {
            "role_weight_mean": role_weights.mean(dim=0).tolist(),
            "role_weight_std": role_weights.std(dim=0).tolist(),
            "role_weight_min": float(role_weights.min()),
            "role_weight_max": float(role_weights.max()),
            "logit_scale": float(model.scale().detach().cpu()),
            "base_adapted_cosine_seen_mean": float(cosine[seenclasses].mean()),
            "base_adapted_cosine_unseen_mean": float(cosine[unseenclasses].mean()),
            "topology_weight": float(selected_condition["topology_weight"]),
            "semantic_group_weights": (
                model.semantic_group_weights().detach().cpu().tolist()
                if selected_condition["mode"] == "tg_vpr"
                else None
            ),
            "value_heads": model.value_heads,
        },
        "history": history,
    }
    result["checkpoint_sha256"] = sha256_file(checkpoint_path)
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
    print(f"best_epoch={best_epoch} delta_H={delta['H']:.6f}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--condition",
        choices=(
            "PSE-A", "PSE-B", "PSE-C", "PSE-X1", "PSE-X2",
            "TG-VPR", "TG-VPR-H1", "TG-VPR-H3", "TG-VPR-H8",
        ),
        required=True,
    )
    args = parser.parse_args()
    run(
        args.config.resolve(),
        args.run_dir.resolve(),
        args.expected_commit,
        args.run_id,
        args.condition,
    )


if __name__ == "__main__":
    main()
