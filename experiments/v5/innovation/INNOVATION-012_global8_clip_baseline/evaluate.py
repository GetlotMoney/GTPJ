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
import scipy.io as sio


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


def verify_input_hashes(config: dict, paths: dict[str, Path]) -> dict[str, str]:
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every configured input exactly once.")
    actual = {name: sha256_file(path) for name, path in paths.items()}
    mismatches = [
        f"{name}: expected {expected[name]}, got {actual[name]}"
        for name in paths
        if expected[name] != actual[name]
    ]
    if mismatches:
        raise ValueError("input SHA-256 mismatch: " + "; ".join(mismatches))
    return actual


def verify_class_order(config: dict, split_path: Path) -> None:
    split_data = sio.loadmat(split_path)
    raw_names = split_data.get("allclasses_names")
    if raw_names is None or tuple(raw_names.shape) != (200, 1):
        raise ValueError("att_splits allclasses_names must have shape [200, 1].")
    names = [str(item[0][0]) for item in raw_names]
    serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    actual = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    expected = config.get("class_order_sha256")
    if actual != expected:
        raise ValueError(
            f"class order SHA-256 mismatch: expected {expected}, got {actual}."
        )


def create_run_directory(output_path: Path) -> None:
    if output_path.name != "metrics.json":
        raise ValueError("formal baseline output filename must be metrics.json.")
    output_path.parent.mkdir(parents=True, exist_ok=False)


def write_result_exclusive(output_path: Path, result: dict) -> None:
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run(config_path: Path, output_path: Path) -> dict:
    config = load_config(config_path)
    paths = resolve_input_paths(config)
    input_sha256 = verify_input_hashes(config, paths)
    verify_class_order(config, paths["att_splits"])
    create_run_directory(output_path)
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
        "class_order_sha256": config["class_order_sha256"],
        "input_sha256": input_sha256,
        "metrics_percent": metrics,
    }
    write_result_exclusive(output_path, result)
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
