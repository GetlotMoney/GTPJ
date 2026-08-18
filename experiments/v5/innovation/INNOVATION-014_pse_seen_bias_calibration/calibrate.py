"""Search one seen-logit bias directly on the final CUB test split."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PSE_SCRIPT = PROJECT_ROOT / "experiments/v5/innovation/INNOVATION-013_shared_pse_global8/train.py"
PSE_SPEC = importlib.util.spec_from_file_location("shared_pse_run002", PSE_SCRIPT)
PSE = importlib.util.module_from_spec(PSE_SPEC)
PSE_SPEC.loader.exec_module(PSE)

EXPECTED_RUN_ID = "RUN-001"
EXPECTED_CONFIG_SHA256 = "7de9706decc23a475d6017afb28811cf75f8b456a74551d73033e0c0ed96b122"


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
    dirty = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or dirty:
        raise ValueError("score search requires one clean Git commit.")
    return commit


def load_config(path: Path) -> tuple[dict, str]:
    config_sha256 = sha256_file(path)
    if EXPECTED_CONFIG_SHA256 and config_sha256 != EXPECTED_CONFIG_SHA256:
        raise ValueError("config SHA-256 does not match the frozen score-search config.")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("dataset") != "CUB":
        raise ValueError("score-search config must be a CUB mapping.")
    if config.get("score_path") != "clip_cls_x_shared_pse_x_seen_bias_calibration":
        raise ValueError("unexpected score_path.")
    if int(config.get("gamma_steps", 0)) < 2:
        raise ValueError("gamma_steps must be at least 2.")
    return config, config_sha256


def resolve_and_verify_inputs(config: dict) -> tuple[dict[str, Path], dict[str, str]]:
    paths = {
        name: (PROJECT_ROOT / value).resolve()
        for name, value in config["inputs"].items()
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing score-search input: " + ", ".join(missing))
    expected = config.get("expected_sha256")
    if not isinstance(expected, dict) or set(expected) != set(paths):
        raise ValueError("expected_sha256 must bind every score-search input.")
    actual = {name: sha256_file(path) for name, path in paths.items()}
    mismatch = [name for name in paths if actual[name] != expected[name]]
    if mismatch:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatch))
    return paths, actual


def verify_identity(actual_commit: str, expected_commit: str, run_id: str, run_dir: Path) -> None:
    if expected_commit != actual_commit:
        raise ValueError("--expected-commit does not match clean HEAD.")
    if run_id != EXPECTED_RUN_ID or run_dir.name != run_id:
        raise ValueError("run id and run directory must match frozen RUN-001.")


def make_model(sentence_embeds, pse_config, checkpoint, device):
    model = PSE.SharedPSE(
        sentence_embeds,
        heads=int(pse_config["pse_heads"]),
        dropout=float(pse_config["pse_dropout"]),
        residual_cap=float(pse_config["residual_cap"]),
        temperature=float(pse_config["temperature"]),
    ).to(device)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()
    return model


@torch.no_grad()
def search_test_gamma(model, tensors, seenclasses, unseenclasses, config, device):
    seen_logits = model.logits(tensors["seen_features"].float().to(device))
    unseen_logits = model.logits(tensors["unseen_features"].float().to(device))
    seen_columns = seenclasses.to(device)
    zsl_predictions = unseenclasses[
        unseen_logits[:, unseenclasses.to(device)].argmax(dim=1).cpu()
    ]
    zsl = PSE.per_class_accuracy(
        tensors["unseen_labels"], zsl_predictions, unseenclasses
    ) * 100.0
    curve = []
    for gamma in torch.linspace(
        float(config["gamma_min"]),
        float(config["gamma_max"]),
        int(config["gamma_steps"]),
    ):
        adjusted_seen = seen_logits.clone()
        adjusted_unseen = unseen_logits.clone()
        adjusted_seen[:, seen_columns] -= gamma.to(device)
        adjusted_unseen[:, seen_columns] -= gamma.to(device)
        seen_predictions = adjusted_seen.argmax(dim=1).cpu()
        unseen_predictions = adjusted_unseen.argmax(dim=1).cpu()
        s_value = PSE.per_class_accuracy(
            tensors["seen_labels"], seen_predictions, seenclasses
        ) * 100.0
        u_value = PSE.per_class_accuracy(
            tensors["unseen_labels"], unseen_predictions, unseenclasses
        ) * 100.0
        h_value = 0.0 if s_value + u_value == 0.0 else 2.0 * s_value * u_value / (s_value + u_value)
        curve.append(
            {"gamma": float(gamma), "U": u_value, "S": s_value, "H": h_value, "ZS": zsl}
        )
    selected = max(
        curve,
        key=lambda row: (row["H"], -abs(row["U"] - row["S"]), -row["gamma"]),
    )
    return selected, curve


def run(config_path: Path, run_dir: Path, expected_commit: str, run_id: str):
    code_commit = get_clean_commit()
    verify_identity(code_commit, expected_commit, run_id, run_dir)
    config, config_sha256 = load_config(config_path)
    paths, input_sha256 = resolve_and_verify_inputs(config)
    if run_dir.exists():
        raise FileExistsError(f"refusing to reuse run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("score search requires CUDA.")
    pse_config, _ = PSE.load_config(paths["pse_config"])
    tensors = {
        name: torch.load(path, map_location="cpu", weights_only=True)
        for name, path in paths.items()
        if name not in {"pse_config", "pse_checkpoint", "res101", "att_splits"}
    }
    seenclasses, unseenclasses = PSE.load_v5_cub_split(
        paths["res101"],
        paths["att_splits"],
        tensors["train_labels"],
        tensors["seen_labels"],
        tensors["unseen_labels"],
        "cpu",
    )
    checkpoint = torch.load(paths["pse_checkpoint"], map_location="cpu", weights_only=True)
    model = make_model(tensors["sentence_embeds"], pse_config, checkpoint, device)
    selected, curve = search_test_gamma(
        model, tensors, seenclasses, unseenclasses, config, device
    )
    result = {
        "experiment_id": "V5-INNOVATION-014",
        "run_id": run_id,
        "code_commit": code_commit,
        "config_sha256": config_sha256,
        "seed": int(config["seed"]),
        "selection_protocol": "test_score_search",
        "not_confirmation_evidence": True,
        "input_sha256": input_sha256,
        "selected_gamma": selected["gamma"],
        "metrics_percent": {key: selected[key] for key in ("U", "S", "H", "ZS")},
        "score_curve": curve,
        "baseline_pse_H": 68.61325308925366,
        "delta_H": selected["H"] - 68.61325308925366,
    }
    with (run_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"代码 commit：{code_commit}")
    print(f"配置 SHA-256：{config_sha256}")
    print(f"随机种子：{config['seed']}")
    print("selection_protocol=test_score_search not_confirmation_evidence=true")
    print(f"selected_gamma={selected['gamma']:.6f}")
    print("Best Results @ Epoch 0")
    print(f"GZSL-U: {selected['U']:.6f}%")
    print(f"GZSL-S: {selected['S']:.6f}%")
    print(f"GZSL-H: {selected['H']:.6f}%")
    print(f"ZSL: {selected['ZS']:.6f}%")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(args.config.resolve(), args.run_dir.resolve(), args.expected_commit, args.run_id)


if __name__ == "__main__":
    main()
