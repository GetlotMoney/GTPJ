"""V5 全局/局部分支互补性诊断。

这个文件只做推理和统计，不训练、不调参，也不改变正式评估口径。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable

import torch
import torch.nn.functional as F
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from model.MyModel import GTPJ
from tools.v5_cub_data import load_v5_cub_split


SCHEMA_VERSION = "gtpj.v5.local_complementarity.v1"
MODEL_TEMPLATE_ID = "model/v5-template-v1"


def _long_vector(name, value):
    tensor = torch.as_tensor(value, dtype=torch.long).cpu()
    if tensor.dim() != 1:
        raise ValueError(f"{name} must be one-dimensional")
    return tensor


def _score_matrix(name, value, rows, classes):
    tensor = torch.as_tensor(value).detach().cpu().float()
    if tensor.dim() != 2 or tuple(tensor.shape) != (rows, classes):
        raise ValueError(
            f"{name} must have shape [{rows}, {classes}], got {tuple(tensor.shape)}"
        )
    if not torch.isfinite(tensor).all():
        raise ValueError(f"{name} must contain only finite values")
    return tensor


def _per_class_rate(labels, correct, classes):
    values = []
    for class_id in classes:
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"missing samples for class {int(class_id)}")
        values.append(correct[mask].float().mean())
    return float(torch.stack(values).mean().item() * 100.0)


def _harmonic(unseen, seen):
    denominator = unseen + seen
    return 2.0 * unseen * seen / denominator if denominator else 0.0


def _branch_metrics(
    seen_scores,
    unseen_scores,
    seen_labels,
    unseen_labels,
    seenclasses,
    unseenclasses,
):
    seen_prediction = seen_scores.argmax(dim=1)
    unseen_prediction = unseen_scores.argmax(dim=1)
    unseen_only_prediction = unseenclasses[
        unseen_scores[:, unseenclasses].argmax(dim=1)
    ]
    seen_correct = seen_prediction == seen_labels
    unseen_correct = unseen_prediction == unseen_labels
    unseen_only_correct = unseen_only_prediction == unseen_labels
    seen = _per_class_rate(seen_labels, seen_correct, seenclasses)
    unseen = _per_class_rate(unseen_labels, unseen_correct, unseenclasses)
    zsl = _per_class_rate(unseen_labels, unseen_only_correct, unseenclasses)
    return {
        "U": unseen,
        "S": seen,
        "H": _harmonic(unseen, seen),
        "ZS": zsl,
    }, {
        "seen_prediction": seen_prediction,
        "unseen_prediction": unseen_prediction,
        "seen_correct": seen_correct,
        "unseen_correct": unseen_correct,
        "unseen_only_correct": unseen_only_correct,
    }


def _oracle_metrics(global_state, local_state, seen_labels, unseen_labels, seenclasses, unseenclasses):
    seen_correct = global_state["seen_correct"] | local_state["seen_correct"]
    unseen_correct = global_state["unseen_correct"] | local_state["unseen_correct"]
    unseen_only_correct = (
        global_state["unseen_only_correct"] | local_state["unseen_only_correct"]
    )
    seen = _per_class_rate(seen_labels, seen_correct, seenclasses)
    unseen = _per_class_rate(unseen_labels, unseen_correct, unseenclasses)
    zsl = _per_class_rate(unseen_labels, unseen_only_correct, unseenclasses)
    return {"U": unseen, "S": seen, "H": _harmonic(unseen, seen), "ZS": zsl}


def _transition_block(global_correct, local_correct, final_correct):
    total = int(global_correct.numel())

    def count(mask):
        return int(mask.sum().item())

    def rate(value):
        return 100.0 * value / total if total else 0.0

    gl_rescue = count((~global_correct) & local_correct)
    gl_harm = count(global_correct & (~local_correct))
    gf_rescue = count((~global_correct) & final_correct)
    gf_harm = count(global_correct & (~final_correct))
    return {
        "sample_count": total,
        "global_wrong_local_correct_count": gl_rescue,
        "global_wrong_local_correct_rate": rate(gl_rescue),
        "global_correct_local_wrong_count": gl_harm,
        "global_correct_local_wrong_rate": rate(gl_harm),
        "global_wrong_final_correct_count": gf_rescue,
        "global_wrong_final_correct_rate": rate(gf_rescue),
        "global_correct_final_wrong_count": gf_harm,
        "global_correct_final_wrong_rate": rate(gf_harm),
    }


def _mean_row_correlation(left, right):
    left_centered = left - left.mean(dim=1, keepdim=True)
    right_centered = right - right.mean(dim=1, keepdim=True)
    correlation = F.cosine_similarity(left_centered, right_centered, dim=1, eps=1e-12)
    return float(correlation.mean().item())


def _scale_summary(global_scores, local_scores):
    global_abs = float(global_scores.abs().mean().item())
    local_abs = float(local_scores.abs().mean().item())
    return {
        "global_abs_mean": global_abs,
        "local_abs_mean": local_abs,
        "global_to_local_abs_mean_ratio": (
            global_abs / local_abs if local_abs > 0.0 else None
        ),
        "global_std": float(global_scores.std(unbiased=False).item()),
        "local_std": float(local_scores.std(unbiased=False).item()),
    }


def _confidence_quartiles(global_scores, global_correct, local_correct):
    top_two = global_scores.topk(k=2, dim=1).values
    margins = top_two[:, 0] - top_two[:, 1]
    boundaries = torch.quantile(margins, torch.tensor([0.25, 0.5, 0.75]))
    buckets = torch.bucketize(margins, boundaries, right=False)
    rows = []
    for bucket in range(4):
        mask = buckets == bucket
        sample_count = int(mask.sum().item())
        rescue_count = int(((~global_correct) & local_correct & mask).sum().item())
        rows.append(
            {
                "quartile": bucket + 1,
                "sample_count": sample_count,
                "margin_min": float(margins[mask].min().item()) if sample_count else None,
                "margin_max": float(margins[mask].max().item()) if sample_count else None,
                "global_wrong_local_correct_count": rescue_count,
                "global_wrong_local_correct_rate": (
                    100.0 * rescue_count / sample_count if sample_count else 0.0
                ),
            }
        )
    return rows


def analyze_complementarity(
    *,
    global_seen,
    local_seen,
    final_seen,
    global_unseen,
    local_unseen,
    final_unseen,
    seen_labels,
    unseen_labels,
    seenclasses,
    unseenclasses,
):
    """统计一个 checkpoint 的分支互补性，所有指标使用百分数。"""

    seen_labels = _long_vector("seen_labels", seen_labels)
    unseen_labels = _long_vector("unseen_labels", unseen_labels)
    seenclasses = _long_vector("seenclasses", seenclasses)
    unseenclasses = _long_vector("unseenclasses", unseenclasses)
    if seenclasses.unique().numel() != seenclasses.numel():
        raise ValueError("seenclasses contains duplicates")
    if unseenclasses.unique().numel() != unseenclasses.numel():
        raise ValueError("unseenclasses contains duplicates")
    if torch.isin(seenclasses, unseenclasses).any():
        raise ValueError("seenclasses and unseenclasses overlap")
    class_count = int(seenclasses.numel() + unseenclasses.numel())
    combined = torch.cat([seenclasses, unseenclasses]).sort().values
    if not torch.equal(combined, torch.arange(class_count)):
        raise ValueError("seen/unseen classes do not cover the complete class axis")

    scores = {}
    for branch, seen_value, unseen_value in (
        ("global", global_seen, global_unseen),
        ("local", local_seen, local_unseen),
        ("final", final_seen, final_unseen),
    ):
        scores[f"{branch}_seen"] = _score_matrix(
            f"{branch}_seen", seen_value, len(seen_labels), class_count
        )
        scores[f"{branch}_unseen"] = _score_matrix(
            f"{branch}_unseen", unseen_value, len(unseen_labels), class_count
        )

    branches = {}
    states = {}
    for branch in ("global", "local", "final"):
        branches[branch], states[branch] = _branch_metrics(
            scores[f"{branch}_seen"],
            scores[f"{branch}_unseen"],
            seen_labels,
            unseen_labels,
            seenclasses,
            unseenclasses,
        )
    branches["oracle_global_local"] = _oracle_metrics(
        states["global"],
        states["local"],
        seen_labels,
        unseen_labels,
        seenclasses,
        unseenclasses,
    )

    transitions = {
        "seen": _transition_block(
            states["global"]["seen_correct"],
            states["local"]["seen_correct"],
            states["final"]["seen_correct"],
        ),
        "unseen": _transition_block(
            states["global"]["unseen_correct"],
            states["local"]["unseen_correct"],
            states["final"]["unseen_correct"],
        ),
    }
    transitions["all"] = _transition_block(
        torch.cat([states["global"]["seen_correct"], states["global"]["unseen_correct"]]),
        torch.cat([states["local"]["seen_correct"], states["local"]["unseen_correct"]]),
        torch.cat([states["final"]["seen_correct"], states["final"]["unseen_correct"]]),
    )

    all_global = torch.cat([scores["global_seen"], scores["global_unseen"]])
    all_local = torch.cat([scores["local_seen"], scores["local_unseen"]])
    all_global_correct = torch.cat(
        [states["global"]["seen_correct"], states["global"]["unseen_correct"]]
    )
    all_local_correct = torch.cat(
        [states["local"]["seen_correct"], states["local"]["unseen_correct"]]
    )
    agreement = {
        "seen_prediction_agreement_rate": float(
            (states["global"]["seen_prediction"] == states["local"]["seen_prediction"])
            .float()
            .mean()
            .item()
            * 100.0
        ),
        "unseen_prediction_agreement_rate": float(
            (
                states["global"]["unseen_prediction"]
                == states["local"]["unseen_prediction"]
            )
            .float()
            .mean()
            .item()
            * 100.0
        ),
        "mean_per_sample_score_correlation": _mean_row_correlation(
            all_global, all_local
        ),
    }
    predicted_seen_bias = {}
    for branch in ("global", "local", "final"):
        predicted_seen_bias[branch] = {
            "seen_split_predicted_seen_rate": float(
                torch.isin(states[branch]["seen_prediction"], seenclasses)
                .float()
                .mean()
                .item()
                * 100.0
            ),
            "unseen_split_predicted_seen_rate": float(
                torch.isin(states[branch]["unseen_prediction"], seenclasses)
                .float()
                .mean()
                .item()
                * 100.0
            ),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "sample_count": int(len(seen_labels) + len(unseen_labels)),
        "class_count": class_count,
        "branches": branches,
        "transitions": transitions,
        "agreement": agreement,
        "predicted_seen_bias": predicted_seen_bias,
        "score_scale": _scale_summary(all_global, all_local),
        "global_confidence_quartiles": _confidence_quartiles(
            all_global, all_global_correct, all_local_correct
        ),
        "interpretation_boundary": (
            "post-hoc diagnostic only; test labels must not select gate parameters"
        ),
    }


def _numeric_summary(values: Iterable[float]):
    values = [float(value) for value in values]
    return {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
    }


def aggregate_reports(reports):
    reports = list(reports)
    if not reports:
        raise ValueError("at least one report is required")
    branches = {}
    for branch in ("global", "local", "final", "oracle_global_local"):
        branches[branch] = {
            metric: _numeric_summary(
                report["branches"][branch][metric] for report in reports
            )
            for metric in ("U", "S", "H", "ZS")
        }
    transitions = {
        key: _numeric_summary(
            report["transitions"]["all"][key] for report in reports
        )
        for key in (
            "global_wrong_local_correct_rate",
            "global_correct_local_wrong_rate",
            "global_wrong_final_correct_rate",
            "global_correct_final_wrong_rate",
        )
    }
    return {
        "schema_version": f"{SCHEMA_VERSION}.aggregate",
        "run_count": len(reports),
        "branches": branches,
        "all_sample_transition_rates": transitions,
    }


def write_json_atomic(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing evidence: {target}")
    temporary = target.with_name(target.name + ".tmp")
    temporary_created = False
    try:
        text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
        with temporary.open("x", encoding="utf-8") as stream:
            temporary_created = True
            stream.write(text + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, target)
    finally:
        if temporary_created and temporary.exists():
            temporary.unlink()


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_config(path):
    config_path = Path(path).resolve()
    payload = config_path.read_bytes()
    raw = yaml.safe_load(payload.decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config must be a mapping")
    values = {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }
    return (
        SimpleNamespace(**values),
        values,
        config_path,
        hashlib.sha256(payload).hexdigest(),
    )


def validate_git_state(head, status, expected_run_commit):
    if (
        len(expected_run_commit) != 40
        or any(character not in "0123456789abcdef" for character in expected_run_commit)
    ):
        raise ValueError("expected run commit must be a full lowercase Git SHA")
    if head != expected_run_commit:
        raise ValueError("current Git HEAD does not match the checkpoint run commit")
    if status.strip():
        raise RuntimeError("formal diagnosis requires a clean Git worktree")


def _require_current_git_identity(expected_run_commit):
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    validate_git_state(head, status, expected_run_commit)
    return head


def _all_input_paths(data_root):
    root = Path(data_root).resolve()
    cache = root / "cache"
    return {
        "xlsa17_res101": root / "xlsa17/data/CUB/res101.mat",
        "xlsa17_att_splits": root / "xlsa17/data/CUB/att_splits.mat",
        "train_cls": cache / "CUB_train_features.pt",
        "train_patches": cache / "CUB_train_patch_features.pt",
        "train_labels": cache / "CUB_train_labels.pt",
        "gpt55_sentences": cache / "CUB_gpt55_sentence_embeds.pt",
        "test_seen_cls": cache / "CUB_test_seen_features.pt",
        "test_seen_labels": cache / "CUB_test_seen_labels.pt",
        "test_seen_patches": cache / "CUB_test_seen_patch_features.pt",
        "test_unseen_cls": cache / "CUB_test_unseen_features.pt",
        "test_unseen_labels": cache / "CUB_test_unseen_labels.pt",
        "test_unseen_patches": cache / "CUB_test_unseen_patch_features.pt",
    }


DIAGNOSTIC_INPUT_KEYS = (
    "xlsa17_res101",
    "xlsa17_att_splits",
    "train_labels",
    "gpt55_sentences",
    "test_seen_cls",
    "test_seen_labels",
    "test_seen_patches",
    "test_unseen_cls",
    "test_unseen_labels",
    "test_unseen_patches",
)


def _disk_fingerprints(paths):
    missing = [str(path) for path in paths.values() if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError("missing bound V5 inputs: " + ", ".join(missing))
    return {
        name: {
            "sha256": _sha256(path),
            "size_bytes": Path(path).stat().st_size,
        }
        for name, path in paths.items()
    }


def _fingerprint_identity(fingerprints):
    if not isinstance(fingerprints, dict):
        raise ValueError("checkpoint input_fingerprints must be a mapping")
    result = {}
    for name, value in fingerprints.items():
        if not isinstance(value, dict):
            raise ValueError(f"checkpoint fingerprint {name} must be a mapping")
        try:
            result[name] = {
                "sha256": value["sha256"],
                "size_bytes": value["size_bytes"],
            }
        except KeyError as exc:
            raise ValueError(
                f"checkpoint fingerprint {name} is missing {exc.args[0]}"
            ) from exc
    return result


def validate_checkpoint_identity(
    checkpoint,
    *,
    expected_run_commit,
    config_values,
    config_sha256,
    seenclasses,
    unseenclasses,
    actual_fingerprints,
):
    expected = {
        "template_id": MODEL_TEMPLATE_ID,
        "code_commit": expected_run_commit,
        "config": config_values,
        "config_sha256": config_sha256,
        "seenclasses": torch.as_tensor(seenclasses).cpu().long().tolist(),
        "unseenclasses": torch.as_tensor(unseenclasses).cpu().long().tolist(),
    }
    for field, value in expected.items():
        if checkpoint.get(field) != value:
            raise ValueError(f"checkpoint {field} does not match formal diagnosis")
    recorded_fingerprints = _fingerprint_identity(
        checkpoint.get("input_fingerprints")
    )
    if recorded_fingerprints != actual_fingerprints:
        raise ValueError("checkpoint input fingerprints do not match current V5 data")


def _cache_paths(data_root, split):
    cache = Path(data_root).resolve() / "cache"
    return {
        "cls": cache / f"CUB_test_{split}_features.pt",
        "patches": cache / f"CUB_test_{split}_patch_features.pt",
        "labels": cache / f"CUB_test_{split}_labels.pt",
    }


def _infer_split(model, paths, device, batch_size):
    cls_features = torch.load(paths["cls"], map_location="cpu", weights_only=True)
    patches = torch.load(paths["patches"], map_location="cpu", weights_only=True)
    labels = torch.load(paths["labels"], map_location="cpu", weights_only=True).long()
    if cls_features.dim() != 2 or patches.dim() != 3 or labels.dim() != 1:
        raise ValueError("invalid cached split shape")
    if not (len(cls_features) == len(patches) == len(labels)):
        raise ValueError("cached split lengths differ")
    collected = {"global": [], "local": [], "final": []}
    model.eval()
    with torch.no_grad():
        for start in range(0, len(labels), batch_size):
            cls_batch = cls_features[start : start + batch_size].to(device).float()
            patch_batch = patches[start : start + batch_size].to(device).float()
            features = torch.cat([cls_batch.unsqueeze(1), patch_batch], dim=1)
            output = model(features, is_train=False)
            for key, output_key in (
                ("global", "global_logits"),
                ("local", "local_logits"),
                ("final", "final_logits"),
            ):
                value = output[output_key]
                if not torch.isfinite(value).all():
                    raise ValueError(f"{output_key} must contain only finite values")
                collected[key].append(value.detach().cpu())
    return {key: torch.cat(value) for key, value in collected.items()}, labels


def diagnose_checkpoint(config_path, data_root, checkpoint_path, expected_run_commit, device, batch_size):
    _require_current_git_identity(expected_run_commit)
    config, config_values, resolved_config, config_sha256 = _load_config(config_path)
    data_root = Path(data_root).resolve()
    input_paths = _all_input_paths(data_root)
    actual_fingerprints = _disk_fingerprints(input_paths)
    train_labels = torch.load(
        input_paths["train_labels"], map_location="cpu", weights_only=True
    ).long()
    seen_paths = _cache_paths(data_root, "seen")
    unseen_paths = _cache_paths(data_root, "unseen")
    seen_labels = torch.load(seen_paths["labels"], map_location="cpu", weights_only=True).long()
    unseen_labels = torch.load(
        unseen_paths["labels"], map_location="cpu", weights_only=True
    ).long()
    seenclasses, unseenclasses = load_v5_cub_split(
        data_root / "xlsa17/data/CUB/res101.mat",
        data_root / "xlsa17/data/CUB/att_splits.mat",
        train_labels,
        seen_labels,
        unseen_labels,
        "cpu",
    )
    sentences = torch.load(
        input_paths["gpt55_sentences"],
        map_location="cpu",
        weights_only=True,
    ).float()
    text_embeds = sentences.mean(dim=1)
    model = GTPJ(
        config,
        seenclasses,
        unseenclasses,
        seen_text_embeds=text_embeds[seenclasses],
        unseen_text_embeds=text_embeds[unseenclasses],
        seen_sentence_embeds=sentences[seenclasses],
    ).to(device)

    checkpoint_path = Path(checkpoint_path).resolve()
    checkpoint_sha256 = _sha256(checkpoint_path)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ValueError("diagnosis requires the full canonical checkpoint")
    validate_checkpoint_identity(
        checkpoint,
        expected_run_commit=expected_run_commit,
        config_values=config_values,
        config_sha256=config_sha256,
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
        actual_fingerprints=actual_fingerprints,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)

    seen_scores, seen_loaded_labels = _infer_split(
        model, seen_paths, device, batch_size
    )
    unseen_scores, unseen_loaded_labels = _infer_split(
        model, unseen_paths, device, batch_size
    )
    report = analyze_complementarity(
        global_seen=seen_scores["global"],
        local_seen=seen_scores["local"],
        final_seen=seen_scores["final"],
        global_unseen=unseen_scores["global"],
        local_unseen=unseen_scores["local"],
        final_unseen=unseen_scores["final"],
        seen_labels=seen_loaded_labels,
        unseen_labels=unseen_loaded_labels,
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
    )
    after_fingerprints = _disk_fingerprints(
        {name: input_paths[name] for name in DIAGNOSTIC_INPUT_KEYS}
    )
    if after_fingerprints != {
        name: actual_fingerprints[name] for name in DIAGNOSTIC_INPUT_KEYS
    }:
        raise RuntimeError("V5 diagnostic inputs changed while they were being read")
    if _sha256(resolved_config) != config_sha256:
        raise RuntimeError("diagnostic config changed while diagnosis was running")
    if _sha256(checkpoint_path) != checkpoint_sha256:
        raise RuntimeError("checkpoint changed while diagnosis was running")
    _require_current_git_identity(expected_run_commit)
    report["provenance"] = {
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_code_commit": checkpoint["code_commit"],
        "config": str(resolved_config),
        "config_sha256": config_sha256,
        "data_root": str(data_root),
        "input_fingerprints": actual_fingerprints,
    }
    return report


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Diagnose global/local complementarity for current V5 checkpoints.",
        allow_abbrev=False,
    )
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path, action="append")
    parser.add_argument("--expected-run-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", default=64, type=int)
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    if not torch.cuda.is_available() or not str(args.device).startswith("cuda"):
        raise RuntimeError("formal V5 diagnosis requires CUDA")
    reports = [
        diagnose_checkpoint(
            args.config,
            args.data_root,
            checkpoint,
            args.expected_run_commit,
            args.device,
            args.batch_size,
        )
        for checkpoint in args.checkpoint
    ]
    payload = {
        "schema_version": f"{SCHEMA_VERSION}.campaign",
        "reports": reports,
        "aggregate": aggregate_reports(reports),
    }
    write_json_atomic(args.output, payload)
    print(json.dumps(payload["aggregate"], ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
