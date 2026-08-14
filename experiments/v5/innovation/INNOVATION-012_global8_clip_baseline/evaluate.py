"""Evaluate frozen CLIP CLS features against fixed 8-sentence prototypes.

This is the zero-module baseline: no trainable projection, PSE, local image
branch, auxiliary loss, or calibration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
import yaml


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_global8_prototypes(sentence_embeds: torch.Tensor) -> torch.Tensor:
    """Build one class prototype by equally averaging eight normalized roles."""
    if tuple(sentence_embeds.shape) != EXPECTED_SENTENCE_SHAPE:
        raise ValueError(
            "8-sentence cache must have shape "
            f"{EXPECTED_SENTENCE_SHAPE}, got {tuple(sentence_embeds.shape)}."
        )
    if not torch.isfinite(sentence_embeds).all():
        raise ValueError("8-sentence cache contains a non-finite value.")
    normalized_sentences = F.normalize(sentence_embeds.float(), dim=-1)
    return F.normalize(normalized_sentences.mean(dim=1), dim=-1)


def cosine_logits(
    image_features: torch.Tensor, text_prototypes: torch.Tensor
) -> torch.Tensor:
    if image_features.dim() != 2 or image_features.size(1) != 768:
        raise ValueError(
            f"CLIP CLS features must be [N, 768], got {tuple(image_features.shape)}."
        )
    if tuple(text_prototypes.shape) != (200, 768):
        raise ValueError(
            "text prototypes must be [200, 768], got "
            f"{tuple(text_prototypes.shape)}."
        )
    return F.normalize(image_features.float(), dim=-1) @ text_prototypes.T


def per_class_accuracy(
    labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor
) -> float:
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"evaluation cache has no sample for class {int(class_id)}.")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean().item())


def evaluate_global8(
    seen_features: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_features: torch.Tensor,
    unseen_labels: torch.Tensor,
    seenclasses: torch.Tensor,
    unseenclasses: torch.Tensor,
    text_prototypes: torch.Tensor,
) -> dict[str, float]:
    seen_logits = cosine_logits(seen_features, text_prototypes)
    unseen_logits = cosine_logits(unseen_features, text_prototypes)
    seen_predictions = seen_logits.argmax(dim=1)
    unseen_predictions = unseen_logits.argmax(dim=1)
    zsl_predictions = unseenclasses[unseen_logits[:, unseenclasses].argmax(dim=1)]

    seen_accuracy = per_class_accuracy(seen_labels, seen_predictions, seenclasses)
    unseen_accuracy = per_class_accuracy(
        unseen_labels, unseen_predictions, unseenclasses
    )
    zsl_accuracy = per_class_accuracy(unseen_labels, zsl_predictions, unseenclasses)
    denominator = seen_accuracy + unseen_accuracy
    harmonic = (
        2.0 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    )
    return {
        "U": unseen_accuracy * 100.0,
        "S": seen_accuracy * 100.0,
        "H": harmonic * 100.0,
        "ZS": zsl_accuracy * 100.0,
    }


def load_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("config root must be a mapping.")
    if config.get("dataset") != "CUB":
        raise ValueError("this baseline only accepts dataset: CUB.")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order does not match the frozen 8-sentence contract.")
    if config.get("text_aggregation") != "normalized_sentence_mean":
        raise ValueError("text_aggregation must be normalized_sentence_mean.")
    return config


def resolve_input_paths(config: dict) -> dict[str, Path]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing baseline input: " + ", ".join(missing))
    return paths


def run(config_path: Path, output_path: Path) -> dict:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    config = load_config(config_path)
    paths = resolve_input_paths(config)
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
    prototypes = build_global8_prototypes(tensors["sentence_embeds"])
    metrics = evaluate_global8(
        tensors["seen_features"],
        tensors["seen_labels"],
        tensors["unseen_features"],
        tensors["unseen_labels"],
        seenclasses,
        unseenclasses,
        prototypes,
    )
    result = {
        "experiment_id": "V5-INNOVATION-012",
        "run_id": "RUN-001",
        "baseline": "frozen_clip_cls_x_equal_mean_of_8_normalized_sentences",
        "trainable_parameters": 0,
        "role_order": list(EXPECTED_ROLES),
        "input_sha256": {name: sha256_file(path) for name, path in paths.items()},
        "metrics_percent": metrics,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
    print(f"result_json={output_path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
