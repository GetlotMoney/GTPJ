"""Run the six-condition GPT-5.5 eight-role RPR experiment."""

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


EXPERIMENT_ID = "V5-INNOVATION-017"
EXPECTED_CONFIG_SHA256_BY_RUN = {
    "RUN-001": "53d8f7f75ab297cd69a02a2c8895ead2a0009a203b3b30d017dd6abe4cf1b647",
    "RUN-002": "d1f07322193a51b6a2b2c14cef98bdf2ab412850e16aec8557aff35f7d7fa4e6",
    "RUN-003": "bfe55aac425db5ba7780120cb878c78a83d71f0c3819f11d81550e1f9930fe72",
    "RUN-004": "cc5f90447850a93427b156c19903c814c9336affc3e9468212a87caef5a5f1d4",
    "RUN-005": "1b11c072455ffd4b7ff1400f091dab3941dd3f2f58357f620c3ae819eb43c28f",
    "RUN-006": "f06ff992d6f07b1de68131d37018a156db6488bf1753c74e30a3f7a30f9567d9",
    "RUN-007": "725803853397d97e144dacf805858d6d2b1e943bc074a5bfdf3835112e357e16",
    "RUN-008": "83d17b55590d19a033b64c0977a5c3b61476ef0836c4e3a62635349946d0951d",
    "RUN-009": "5ae36891b8863d7c52c07e29aaec5c61a84a713d879a9050672df43c92dff963",
}
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
EXPECTED_ROLE_PERMUTATION_SHA256 = (
    "efbe765e3f8c37a4ddff187ce13802320c56855080de9f175f720d0058c5917f"
)
RUN_CONDITIONS = {
    "RUN-001": "clip_mean8",
    "RUN-002": "shared_pse",
    "RUN-003": "rpr_off",
    "RUN-004": "rpr_shared_transform",
    "RUN-005": "rpr_role_separated",
    "RUN-006": "rpr_classwise_shuffle",
    "RUN-007": "rpr_off",
    "RUN-008": "rpr_shared_transform",
    "RUN-009": "rpr_role_separated",
}
TRAINING_CONDITIONS = {
    "shared_pse",
    "rpr_shared_transform",
    "rpr_role_separated",
    "rpr_classwise_shuffle",
}
EXPECTED_RUN_DIR_PREFIX = ("runs", "v5", "innovation", EXPERIMENT_ID)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tensor(tensor: torch.Tensor) -> str:
    value = tensor.detach().cpu().contiguous().numpy().tobytes()
    return hashlib.sha256(value).hexdigest()


def get_clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"could not resolve one full run commit: {commit!r}")
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
        raise ValueError("formal training requires a clean tracked worktree")
    return commit


def verify_expected_commit(actual: str, expected: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError("--expected-commit must be one full lowercase Git SHA")
    if actual != expected:
        raise ValueError(f"current commit {actual} does not match {expected}")


def git_worktree_roots() -> tuple[Path, ...]:
    output = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"],
        text=True,
    )
    roots = []
    for line in output.splitlines():
        if line.startswith("worktree "):
            roots.append(Path(line.removeprefix("worktree ")).resolve())
    if not roots:
        raise RuntimeError("git did not report any worktree root")
    return tuple(roots)


def validate_run_dir(run_dir: Path, run_id: str) -> Path:
    resolved = run_dir.resolve()
    if resolved.name != run_id:
        raise ValueError("--run-dir final directory must equal --run-id")
    for worktree_root in git_worktree_roots():
        try:
            resolved.relative_to(worktree_root)
        except ValueError:
            continue
        raise ValueError("formal run output must be outside every Git worktree")
    expected_suffix = (*EXPECTED_RUN_DIR_PREFIX, run_id)
    if tuple(resolved.parts[-len(expected_suffix) :]) != expected_suffix:
        raise ValueError(
            "--run-dir must end with runs/v5/innovation/"
            f"{EXPERIMENT_ID}/{run_id}"
        )
    if resolved.exists():
        raise FileExistsError(f"refusing to reuse run directory: {resolved}")
    return resolved


def load_config(path: Path, run_id: str) -> tuple[dict, str]:
    expected_sha256 = EXPECTED_CONFIG_SHA256_BY_RUN[run_id]
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "config SHA-256 does not match the reviewed config: " + actual_sha256
        )
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping")
    if config.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("config experiment_id mismatch")
    if config.get("dataset") != "CUB":
        raise ValueError("this experiment only accepts CUB")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order does not match the eight-role contract")
    if config.get("run_id") != run_id:
        raise ValueError("config run_id mismatch")
    if config.get("condition") != RUN_CONDITIONS[run_id]:
        raise ValueError("config condition mismatch")
    if int(config.get("rpr_rank", 0)) != 32:
        raise ValueError("rpr_rank must be 32")
    if float(config.get("role_weight_floor", -1)) != 0.10:
        raise ValueError("role_weight_floor must be 0.10")
    if float(config.get("role_weight_span", -1)) != 0.20:
        raise ValueError("role_weight_span must be 0.20")
    return config, actual_sha256


def resolve_input_paths(config: dict) -> dict[str, Path]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing RPR input: " + ", ".join(missing))
    return paths


def verify_input_contract(config: dict, paths: dict[str, Path]) -> dict[str, str]:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every input exactly once")
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
        raise ValueError("train cache labels do not match the xlsa17 split")
    seenclasses = torch.unique(expected_train, sorted=True)
    if not torch.equal(seenclasses, torch.unique(labels[seen_indices], sorted=True)):
        raise ValueError("train and test_seen class sets differ")
    unseenclasses = torch.unique(labels[unseen_indices], sorted=True)
    if torch.isin(seenclasses, unseenclasses).any():
        raise ValueError("seen and unseen classes overlap")
    return seenclasses, unseenclasses


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
        raise ValueError("validation_fraction must be in (0, 0.5)")
    labels = labels.detach().cpu().long()
    generator = torch.Generator().manual_seed(seed)
    train_indices: list[torch.Tensor] = []
    validation_indices: list[torch.Tensor] = []
    for class_id in classes.detach().cpu().long():
        indices = torch.where(labels == class_id)[0]
        if indices.numel() < 2:
            raise ValueError(f"class {int(class_id)} needs at least two samples")
        permutation = indices[torch.randperm(indices.numel(), generator=generator)]
        count = max(1, int(round(indices.numel() * fraction)))
        count = min(count, indices.numel() - 1)
        validation_indices.append(permutation[:count])
        train_indices.append(permutation[count:])
    return torch.cat(train_indices).sort().values, torch.cat(validation_indices).sort().values


def validate_sentence_tensor(sentence_embeds: torch.Tensor) -> torch.Tensor:
    if tuple(sentence_embeds.shape) != EXPECTED_SENTENCE_SHAPE:
        raise ValueError(
            f"sentence_embeds must be {EXPECTED_SENTENCE_SHAPE}, got {tuple(sentence_embeds.shape)}"
        )
    if not torch.isfinite(sentence_embeds).all():
        raise ValueError("sentence_embeds contains a non-finite value")
    return F.normalize(sentence_embeds.detach().float(), dim=-1)


def mean8_components(sentence_embeds: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    mean = sentence_embeds.mean(dim=1, keepdim=True)
    return F.normalize(mean.squeeze(1), dim=-1), sentence_embeds - mean


class Mean8Classifier(nn.Module):
    def __init__(self, sentence_embeds: torch.Tensor, temperature: float):
        super().__init__()
        normalized = validate_sentence_tensor(sentence_embeds)
        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.temperature = float(temperature)

    def base_prototypes(self) -> torch.Tensor:
        return mean8_components(self.sentence_embeds)[0]

    def logits(self, image_features: torch.Tensor, class_ids=None) -> torch.Tensor:
        prototypes = self.base_prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(0, class_ids.to(prototypes.device))
        return F.normalize(image_features.float(), dim=-1) @ prototypes.T / self.temperature


class SharedPSE(nn.Module):
    """Frozen source-method reference; it is not the proposed module."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        temperature: float,
        heads: int,
        dropout: float,
        residual_cap: float,
    ):
        super().__init__()
        normalized = validate_sentence_tensor(sentence_embeds)
        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.attention = nn.MultiheadAttention(768, heads, dropout=dropout, batch_first=True)
        self.context_projection = nn.Linear(768, 768)
        self.role_scorer = nn.Sequential(nn.Linear(768, 192), nn.GELU(), nn.Linear(192, 1))
        nn.init.zeros_(self.role_scorer[-1].weight)
        nn.init.zeros_(self.role_scorer[-1].bias)
        self.residual_gate = nn.Parameter(torch.zeros(()))
        self.residual_cap = float(residual_cap)
        self.temperature = float(temperature)

    def base_prototypes(self) -> torch.Tensor:
        return F.normalize(self.sentence_embeds.mean(dim=1), dim=-1)

    def prototypes(self, return_diagnostics: bool = False):
        attended, attention = self.attention(
            self.sentence_embeds,
            self.sentence_embeds,
            self.sentence_embeds,
            need_weights=True,
            average_attn_weights=False,
        )
        contextual = F.normalize(
            self.sentence_embeds + self.context_projection(attended), dim=-1
        )
        weights = F.softmax(self.role_scorer(contextual).squeeze(-1), dim=1)
        pooled = (weights.unsqueeze(-1) * contextual).sum(dim=1)
        base = self.base_prototypes()
        gate = self.residual_cap * torch.tanh(self.residual_gate)
        adapted = F.normalize(base + gate * (pooled - base), dim=-1)
        if return_diagnostics:
            return adapted, {"base": base, "weights": weights, "attention": attention, "gate": gate}
        return adapted

    def logits(self, image_features: torch.Tensor, class_ids=None) -> torch.Tensor:
        prototypes = self.prototypes()
        if class_ids is not None:
            prototypes = prototypes.index_select(0, class_ids.to(prototypes.device))
        return F.normalize(image_features.float(), dim=-1) @ prototypes.T / self.temperature


def classwise_role_permutations(class_count: int, role_count: int, seed: int) -> torch.Tensor:
    if math.factorial(role_count) - 1 < class_count:
        raise ValueError("not enough non-identity permutations for every class")
    generator = torch.Generator().manual_seed(seed)
    identity = tuple(range(role_count))
    seen: set[tuple[int, ...]] = set()
    rows = []
    while len(rows) < class_count:
        row = torch.randperm(role_count, generator=generator)
        key = tuple(int(value) for value in row)
        if key == identity or key in seen:
            continue
        seen.add(key)
        rows.append(row)
    permutations = torch.stack(rows)
    if (class_count, role_count, seed) == (200, 8, 1705):
        if sha256_tensor(permutations) != EXPECTED_ROLE_PERMUTATION_SHA256:
            raise RuntimeError("class-wise role permutation identity changed")
    return permutations


class RPRClassifier(nn.Module):
    """Role-separated low-rank additive prototype residual classifier."""

    def __init__(
        self,
        sentence_embeds: torch.Tensor,
        *,
        condition: str,
        temperature: float,
        rank: int,
        gate_cap: float,
        gate_init: float,
        role_weight_floor: float,
        role_weight_span: float,
        role_shuffle_seed: int,
    ):
        super().__init__()
        if condition not in {
            "rpr_off",
            "rpr_shared_transform",
            "rpr_role_separated",
            "rpr_classwise_shuffle",
        }:
            raise ValueError(f"unsupported RPR condition: {condition}")
        if not 0.0 <= gate_init < gate_cap:
            raise ValueError("gate_init must be in [0, gate_cap)")
        if abs(8 * role_weight_floor + role_weight_span - 1.0) > 1e-9:
            raise ValueError("role weight floor/span must sum to one over eight roles")

        normalized = validate_sentence_tensor(sentence_embeds)
        _, deltas = mean8_components(normalized)
        if float(deltas.sum(dim=1).abs().max()) > 1e-5:
            raise RuntimeError("centered role residuals do not sum to zero")
        permutations = classwise_role_permutations(200, 8, role_shuffle_seed)

        self.register_buffer("sentence_embeds", normalized, persistent=True)
        self.register_buffer("role_permutations", permutations, persistent=True)
        self.condition = condition
        self.temperature = float(temperature)
        self.rank = int(rank)
        self.gate_cap = float(gate_cap)
        self.role_weight_floor = float(role_weight_floor)
        self.role_weight_span = float(role_weight_span)

        self.left_basis = nn.Parameter(torch.empty(768, rank))
        self.right_basis = nn.Parameter(torch.empty(768, rank))
        scale_rows = 1 if condition == "rpr_shared_transform" else 8
        self.role_scales = nn.Parameter(torch.ones(scale_rows, rank))
        self.role_logits = nn.Parameter(torch.zeros(8))
        gate_raw = math.atanh(gate_init / gate_cap) if gate_init else 0.0
        self.gate_raw = nn.Parameter(torch.tensor(gate_raw, dtype=torch.float32))
        nn.init.orthogonal_(self.left_basis)
        nn.init.orthogonal_(self.right_basis)

    def base_prototypes(self) -> torch.Tensor:
        return self.base

    @property
    def base(self) -> torch.Tensor:
        return mean8_components(self.sentence_embeds)[0]

    @property
    def deltas(self) -> torch.Tensor:
        deltas = mean8_components(self.sentence_embeds)[1]
        if self.condition == "rpr_classwise_shuffle":
            gather_index = self.role_permutations.unsqueeze(-1).expand(-1, -1, 768)
            return deltas.gather(1, gather_index)
        return deltas

    def role_weights(self) -> torch.Tensor:
        return self.role_weight_floor + self.role_weight_span * F.softmax(
            self.role_logits, dim=0
        )

    def gate(self) -> torch.Tensor:
        if self.condition == "rpr_off":
            return self.gate_raw * 0.0
        return self.gate_cap * torch.tanh(self.gate_raw)

    def expanded_scales(self) -> torch.Tensor:
        if self.role_scales.size(0) == 1:
            return self.role_scales.expand(8, -1)
        return self.role_scales

    def transformed_roles(self) -> torch.Tensor:
        projected = torch.einsum("crd,dk->crk", self.deltas, self.right_basis)
        projected = projected * self.expanded_scales().unsqueeze(0)
        return torch.einsum("crk,dk->crd", projected, self.left_basis)

    def class_role_residuals(self) -> torch.Tensor:
        weights = self.role_weights().view(1, 8, 1)
        return self.gate() * weights * self.transformed_roles()

    def logits_with_contributions(
        self, image_features: torch.Tensor, class_ids=None
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        images = F.normalize(image_features.float(), dim=-1)
        base = self.base
        residuals = self.class_role_residuals()
        if class_ids is not None:
            ids = class_ids.to(base.device)
            base = base.index_select(0, ids)
            residuals = residuals.index_select(0, ids)
        base_logits = images @ base.T / self.temperature
        contributions = torch.einsum("nd,crd->ncr", images, residuals) / self.temperature
        return base_logits + contributions.sum(dim=2), base_logits, contributions

    def logits(self, image_features: torch.Tensor, class_ids=None) -> torch.Tensor:
        return self.logits_with_contributions(image_features, class_ids)[0]

    def logits_without_role(
        self, image_features: torch.Tensor, role: int, class_ids=None
    ) -> torch.Tensor:
        if not 0 <= role < 8:
            raise ValueError("role must be in [0, 7]")
        _, base_logits, contributions = self.logits_with_contributions(
            image_features, class_ids
        )
        keep = torch.arange(8, device=contributions.device) != role
        return base_logits + contributions[:, :, keep].sum(dim=2)


def build_model(config: dict, sentence_embeds: torch.Tensor, condition: str) -> nn.Module:
    if condition == "clip_mean8":
        return Mean8Classifier(sentence_embeds, float(config["temperature"]))
    if condition == "shared_pse":
        return SharedPSE(
            sentence_embeds,
            float(config["temperature"]),
            int(config["shared_pse_heads"]),
            float(config["shared_pse_dropout"]),
            float(config["shared_pse_residual_cap"]),
        )
    return RPRClassifier(
        sentence_embeds,
        condition=condition,
        temperature=float(config["temperature"]),
        rank=int(config["rpr_rank"]),
        gate_cap=float(config["rpr_gate_cap"]),
        gate_init=float(config["rpr_gate_init"]),
        role_weight_floor=float(config["role_weight_floor"]),
        role_weight_span=float(config["role_weight_span"]),
        role_shuffle_seed=int(config["role_shuffle_seed"]),
    )


def per_class_accuracy(labels, predictions, classes) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not bool(mask.any()):
            raise ValueError(f"evaluation cache has no class {int(class_id)}")
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
    seen = per_class_accuracy(tensors["seen_labels"], seen_predictions, seenclasses)
    unseen = per_class_accuracy(tensors["unseen_labels"], unseen_predictions, unseenclasses)
    zsl = per_class_accuracy(tensors["unseen_labels"], zsl_predictions, unseenclasses)
    harmonic = 2 * seen * unseen / (seen + unseen) if seen + unseen else 0.0
    return {"U": unseen * 100, "S": seen * 100, "H": harmonic * 100, "ZS": zsl * 100}


@torch.no_grad()
def model_diagnostics(model: nn.Module, probe_features: torch.Tensor) -> dict:
    if isinstance(model, Mean8Classifier):
        return {"condition": "clip_mean8", "prototype_norm_mean": float(model.base_prototypes().norm(dim=1).mean())}
    if isinstance(model, SharedPSE):
        adapted, values = model.prototypes(return_diagnostics=True)
        cosine = F.cosine_similarity(values["base"], adapted, dim=-1)
        return {
            "condition": "shared_pse",
            "gate": float(values["gate"].cpu()),
            "role_weight_mean": values["weights"].mean(dim=0).cpu().tolist(),
            "base_adapted_cosine_mean": float(cosine.mean().cpu()),
        }

    logits, base_logits, contributions = model.logits_with_contributions(probe_features)
    observed_float32_decomposition_error = float(
        (logits - base_logits - contributions.sum(dim=2)).abs().max().cpu()
    )
    observed_float32_deletion_errors = []
    for role in range(8):
        without_role = model.logits_without_role(probe_features, role)
        observed_float32_deletion_errors.append(
            float((logits - without_role - contributions[:, :, role]).abs().max().cpu())
        )

    images64 = F.normalize(probe_features.float(), dim=-1).double()
    base64 = model.base.double()
    residuals64 = model.class_role_residuals().double()
    base_logits64 = images64 @ base64.T / model.temperature
    contributions64 = torch.einsum("nd,crd->ncr", images64, residuals64) / model.temperature
    logits64 = base_logits64 + contributions64.sum(dim=2)
    direct_logits64 = (
        images64 @ (base64 + residuals64.sum(dim=1)).T / model.temperature
    )
    decomposition_error64 = float(
        (direct_logits64 - logits64).abs().max().cpu()
    )
    deletion_errors64 = []
    for role in range(8):
        keep = torch.arange(8, device=residuals64.device) != role
        independently_deleted64 = (
            images64 @ base64.T
            + images64 @ residuals64[:, keep].sum(dim=1).T
        ) / model.temperature
        deletion_errors64.append(
            float(
                (
                    logits64
                    - independently_deleted64
                    - contributions64[:, :, role]
                )
                .abs()
                .max()
                .cpu()
            )
        )
    weights = model.role_weights()
    scales = model.expanded_scales()
    scale_cosine = F.normalize(scales, dim=1) @ F.normalize(scales, dim=1).T

    probe_deltas = model.deltas.reshape(-1, 768)[:512]
    projected = probe_deltas @ model.right_basis
    transformed = torch.einsum("nk,rk,dk->rnd", projected, scales, model.left_basis)
    flattened = F.normalize(transformed.flatten(1), dim=1)
    output_cosine = flattened @ flattened.T
    residual_norms = model.class_role_residuals().sum(dim=1).norm(dim=1)
    return {
        "condition": model.condition,
        "gate": float(model.gate().cpu()),
        "role_weights": weights.cpu().tolist(),
        "role_weight_min": float(weights.min().cpu()),
        "role_weight_max": float(weights.max().cpu()),
        "centered_sum_max_abs": float(model.deltas.sum(dim=1).abs().max().cpu()),
        "decomposition_max_abs_error": decomposition_error64,
        "decomposition_float32_observed_max_abs_error": (
            observed_float32_decomposition_error
        ),
        "decomposition_raw_cosine_max_abs_error": decomposition_error64
        * model.temperature,
        "role_deletion_max_abs_error": max(deletion_errors64),
        "role_deletion_float32_observed_max_abs_error": max(
            observed_float32_deletion_errors
        ),
        "role_deletion_raw_cosine_max_abs_error": max(deletion_errors64)
        * model.temperature,
        "role_scale_cosine_8x8": scale_cosine.cpu().tolist(),
        "common_probe_output_cosine_8x8": output_cosine.cpu().tolist(),
        "class_residual_norm_min": float(residual_norms.min().cpu()),
        "class_residual_norm_mean": float(residual_norms.mean().cpu()),
        "class_residual_norm_max": float(residual_norms.max().cpu()),
        "role_permutation_sha256": sha256_tensor(model.role_permutations),
    }


def run(config_path: Path, run_dir: Path, expected_commit: str, run_id: str) -> dict:
    if run_id not in RUN_CONDITIONS:
        raise ValueError("--run-id is not registered for this experiment")
    run_dir = validate_run_dir(run_dir, run_id)

    code_commit = get_clean_commit()
    verify_expected_commit(code_commit, expected_commit)
    config, config_sha256 = load_config(config_path, run_id)
    condition = RUN_CONDITIONS[run_id]
    paths = resolve_input_paths(config)
    input_sha256 = verify_input_contract(config, paths)
    run_dir.mkdir(parents=True, exist_ok=False)

    log_path = run_dir / "training.log"
    log_handle = log_path.open("x", encoding="utf-8", buffering=1)

    def emit(message: str) -> None:
        print(message, flush=True)
        log_handle.write(message + "\n")

    try:
        seed = int(config["seed"])
        emit(f"代码 commit：{code_commit}")
        emit(f"配置 SHA-256：{config_sha256}")
        emit(f"随机种子：{seed}")
        emit(f"实验条件：{condition}")
        set_determinism(seed)
        device = torch.device(config["device"])
        if device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("formal RPR experiment requires a visible CUDA device")

        tensors = {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in ("sentence_embeds", "train_features", "train_labels")
        }
        seenclasses, unseenclasses = load_training_class_split(
            paths, tensors["train_labels"]
        )
        train_indices = None
        validation_indices = None
        validation_sha256 = None
        if condition in TRAINING_CONDITIONS:
            train_indices, validation_indices = stratified_train_validation_split(
                tensors["train_labels"],
                seenclasses,
                float(config["validation_fraction"]),
                seed,
            )
            validation_sha256 = sha256_tensor(validation_indices.long())
        global_to_seen = torch.full((200,), -1, dtype=torch.long)
        global_to_seen[seenclasses] = torch.arange(seenclasses.numel())

        model = build_model(config, tensors["sentence_embeds"], condition).to(device)
        trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
        best_epoch = 0
        best_validation_loss = None
        history: list[dict] = []
        if condition in TRAINING_CONDITIONS:
            assert train_indices is not None and validation_indices is not None
            dataset = TensorDataset(
                tensors["train_features"][train_indices].float(),
                global_to_seen[tensors["train_labels"][train_indices].long()],
            )
            generator = torch.Generator().manual_seed(seed)
            loader = DataLoader(
                dataset,
                batch_size=int(config["batch_size"]),
                shuffle=True,
                num_workers=0,
                generator=generator,
            )
            validation_features = tensors["train_features"][validation_indices].to(device).float()
            validation_targets = global_to_seen[
                tensors["train_labels"][validation_indices].long()
            ].to(device)
            optimizer = torch.optim.AdamW(
                trainable,
                lr=float(config["learning_rate"]),
                weight_decay=float(config["weight_decay"]),
            )
            best_state = None
            best_loss = float("inf")
            stale_epochs = 0
            for epoch in range(1, int(config["max_epochs"]) + 1):
                model.train()
                loss_sum = 0.0
                sample_count = 0
                for features, targets in loader:
                    features = features.to(device)
                    targets = targets.to(device)
                    optimizer.zero_grad(set_to_none=True)
                    loss = F.cross_entropy(model.logits(features, seenclasses), targets)
                    loss.backward()
                    optimizer.step()
                    loss_sum += float(loss.detach().cpu()) * features.size(0)
                    sample_count += features.size(0)
                model.eval()
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
                        "validation_loss": validation_loss,
                    }
                )
                emit(
                    f"epoch={epoch} train_loss={training_loss:.6f} "
                    f"validation_loss={validation_loss:.6f}"
                )
                if validation_loss < best_loss - float(config["min_delta"]):
                    best_loss = validation_loss
                    best_epoch = epoch
                    best_state = copy.deepcopy(model.state_dict())
                    stale_epochs = 0
                else:
                    stale_epochs += 1
                    if stale_epochs >= int(config["patience"]):
                        break
            if best_state is None:
                raise RuntimeError("training did not produce a validation checkpoint")
            model.load_state_dict(best_state)
            best_validation_loss = best_loss

        probe_features = tensors["train_features"][:64].to(device)
        diagnostics = model_diagnostics(model, probe_features)
        if condition == "rpr_off":
            baseline = Mean8Classifier(
                tensors["sentence_embeds"], float(config["temperature"])
            ).to(device)
            residual_off_error = 0.0
            for features in tensors["train_features"].split(1024):
                features = features.to(device)
                residual_off_error = max(
                    residual_off_error,
                    float(
                        (model.logits(features) - baseline.logits(features))
                        .abs()
                        .max()
                        .cpu()
                    ),
                )
            diagnostics["residual_off_vs_b0_max_abs_error"] = residual_off_error
            if residual_off_error > 1e-6:
                raise RuntimeError("RPR off condition does not exactly match B0")
        if diagnostics.get("decomposition_max_abs_error", 0.0) > 1e-6:
            raise RuntimeError("RPR contribution decomposition exceeded 1e-6")
        if diagnostics.get("role_deletion_max_abs_error", 0.0) > 1e-6:
            raise RuntimeError("RPR role deletion check exceeded 1e-6")

        checkpoint_path = run_dir / "model_best.pth"
        torch.save(
            {
                "model": {
                    name: value.detach().cpu() for name, value in model.state_dict().items()
                },
                "condition": condition,
                "config": config,
                "code_commit": code_commit,
                "best_epoch": best_epoch,
            },
            checkpoint_path,
        )

        official = {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in (
                "seen_features",
                "seen_labels",
                "unseen_features",
                "unseen_labels",
            )
        }
        tensors.update(official)
        checked_seenclasses, checked_unseenclasses = load_v5_cub_split(
            paths["res101"],
            paths["att_splits"],
            tensors["train_labels"],
            tensors["seen_labels"],
            tensors["unseen_labels"],
            "cpu",
        )
        if not torch.equal(seenclasses, checked_seenclasses) or not torch.equal(
            unseenclasses, checked_unseenclasses
        ):
            raise RuntimeError("official class sets changed after checkpoint selection")

        metrics = evaluate(model, tensors, seenclasses, unseenclasses, device)
        result = {
            "experiment_id": EXPERIMENT_ID,
            "run_id": run_id,
            "condition": condition,
            "code_commit": code_commit,
            "config_sha256": config_sha256,
            "seed": seed,
            "input_sha256": input_sha256,
            "class_order_sha256": config["class_order_sha256"],
            "validation_indices_sha256": validation_sha256,
            "selection_protocol": (
                "seen_train_internal_10pct_validation_ce"
                if condition in TRAINING_CONDITIONS
                else "none_frozen_inference"
            ),
            "official_test_policy": "once_after_checkpoint_freeze",
            "technical_retry_of": {
                "RUN-007": "RUN-003",
                "RUN-008": "RUN-004",
                "RUN-009": "RUN-005",
            }.get(run_id),
            "prior_attempt_official_metrics_computed_but_unpersisted": run_id
            in {"RUN-007", "RUN-008", "RUN-009"},
            "prior_attempt_metrics_used_for_model_or_config_selection": False,
            "best_epoch_by_seen_validation_ce": best_epoch,
            "best_validation_loss": best_validation_loss,
            "model_parameter_count": sum(parameter.numel() for parameter in model.parameters()),
            "optimized_parameter_count": (
                sum(parameter.numel() for parameter in trainable)
                if condition in TRAINING_CONDITIONS
                else 0
            ),
            "metrics_percent": metrics,
            "diagnostics": diagnostics,
            "history": history,
            "checkpoint_sha256": sha256_file(checkpoint_path),
        }
        metrics_path = run_dir / "metrics.json"
        with metrics_path.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        with (run_dir / "result.yaml").open("x", encoding="utf-8") as handle:
            yaml.safe_dump(result, handle, allow_unicode=True, sort_keys=False)
        emit("U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
        emit(f"best_epoch={best_epoch}")
        return result
    finally:
        log_handle.close()


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
