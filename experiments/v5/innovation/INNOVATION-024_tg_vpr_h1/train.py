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


PROJECT_ROOT = Path(__file__).resolve().parents[4]
MODULE_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from tg_vpr_h1_model import TGVPRH1  # noqa: E402
from tools.v5_cub_data import load_v5_cub_split  # noqa: E402


EXPECTED_CONFIG_SHA256 = "db39e6890ca3f291a62713f0e30028a7023ed8d956342db0daebd809b1dd5f14"
TRAINING_KEYS = ("sentence_embeds", "train_features", "train_labels", "res101", "att_splits")
OFFICIAL_KEYS = ("seen_features", "seen_labels", "unseen_features", "unseen_labels")


class TeeStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or dirty:
        raise ValueError("training requires one clean committed worktree.")
    return commit


def load_config(path: Path) -> tuple[dict, str]:
    digest = sha256_file(path)
    if digest != EXPECTED_CONFIG_SHA256:
        raise ValueError(f"config SHA-256 mismatch: {digest}")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("dataset") != "CUB" or int(config.get("epochs", -1)) != 50:
        raise ValueError("standalone H1 only accepts CUB and fixed 50 epochs.")
    if int(config.get("batch_size", -1)) != 64:
        raise ValueError("standalone H1 fixes batch_size=64.")
    if tuple(config.get("role_order", ())) != (
        "beak", "head_features", "body_plumage", "wings", "tail", "legs",
        "overall_appearance", "unique_discriminative_features",
    ):
        raise ValueError("role_order differs from the frozen cache contract.")
    if [int(stage["epochs"]) for stage in config["lr_stages"]] != [20, 20, 10]:
        raise ValueError("standalone H1 fixes the 20/20/10 schedule.")
    return config, digest


def resolve_paths(config: dict) -> dict[str, Path]:
    paths = {name: (PROJECT_ROOT / value).resolve() for name, value in config["inputs"].items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing H1 input: " + ", ".join(missing))
    return paths


def verify_inputs(config: dict, paths: dict[str, Path], keys) -> dict[str, str]:
    actual = {name: sha256_file(paths[name]) for name in keys}
    mismatch = [name for name in keys if actual[name] != config["expected_sha256"][name]]
    if mismatch:
        raise ValueError("input SHA-256 mismatch: " + ", ".join(mismatch))
    names = sio.loadmat(paths["att_splits"], variable_names=["allclasses_names"])[
        "allclasses_names"
    ]
    serialized = json.dumps(
        [str(item[0][0]) for item in names], ensure_ascii=False, separators=(",", ":")
    )
    if hashlib.sha256(serialized.encode("utf-8")).hexdigest() != config["class_order_sha256"]:
        raise ValueError("CUB class order mismatch.")
    return actual


def set_determinism(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def legacy_batch_indices(count: int, batch_size: int, generator: torch.Generator):
    return torch.randperm(count, generator=generator)[:batch_size]


def verify_run_identity(run_id: str, output_dir: Path) -> None:
    if run_id != "RUN-001":
        raise ValueError("standalone migration run_id must be RUN-001.")
    if output_dir.name != run_id:
        raise ValueError("output-dir final directory name must equal run_id.")


def visual_centroids(features, labels, classes):
    normalized = F.normalize(features.detach().float(), dim=-1)
    return torch.stack(
        [F.normalize(normalized[labels == class_id].mean(dim=0), dim=0) for class_id in classes]
    )


def per_class_accuracy(labels, predictions, classes) -> float:
    values = []
    for class_id in classes.cpu().long():
        mask = labels.cpu().long() == class_id
        values.append((predictions.cpu().long()[mask] == labels.cpu().long()[mask]).float().mean())
    return float(torch.stack(values).mean())


@torch.no_grad()
def evaluate(model, tensors, seenclasses, unseenclasses, device):
    model.eval()
    prototypes = model.prototypes()
    seen_logits = F.normalize(tensors["seen_features"].to(device).float(), dim=-1) @ prototypes.T * model.scale()
    unseen_logits = F.normalize(tensors["unseen_features"].to(device).float(), dim=-1) @ prototypes.T * model.scale()
    seen_pred = seen_logits.argmax(dim=1).cpu()
    unseen_pred = unseen_logits.argmax(dim=1).cpu()
    zsl_pred = unseenclasses[unseen_logits[:, unseenclasses.to(device)].argmax(dim=1).cpu()]
    seen = per_class_accuracy(tensors["seen_labels"], seen_pred, seenclasses)
    unseen = per_class_accuracy(tensors["unseen_labels"], unseen_pred, unseenclasses)
    zsl = per_class_accuracy(tensors["unseen_labels"], zsl_pred, unseenclasses)
    harmonic = 2 * seen * unseen / (seen + unseen) if seen + unseen else 0.0
    return {"U": unseen * 100, "S": seen * 100, "H": harmonic * 100, "ZS": zsl * 100}


def run(config_path: Path, output_dir: Path, expected_commit: str, run_id: str):
    code_commit = clean_commit()
    if code_commit != expected_commit:
        raise ValueError("expected commit does not match the clean worktree.")
    config, config_sha = load_config(config_path)
    paths = resolve_paths(config)
    input_sha = verify_inputs(config, paths, TRAINING_KEYS)
    output_dir = output_dir.resolve()
    verify_run_identity(run_id, output_dir)
    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("standalone H1 requires a visible CUDA device.")
    for line in subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"], text=True
    ).splitlines():
        if line.startswith("worktree "):
            try:
                output_dir.relative_to(Path(line.split(" ", 1)[1]).resolve())
            except ValueError:
                continue
            raise ValueError("output-dir must stay outside every Git worktree.")
    if output_dir.exists():
        raise FileExistsError(f"refusing to reuse output-dir: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    log_handle = (output_dir / "training.log").open("x", encoding="utf-8", buffering=1)
    sys.stdout = TeeStream(sys.stdout, log_handle)

    seed = int(config["seed"])
    set_determinism(seed)
    print(f"代码 commit：{code_commit}")
    print(f"配置 SHA-256：{config_sha}")
    print(f"随机种子：{seed}")

    tensors = {
        name: torch.load(paths[name], map_location="cpu", weights_only=True)
        for name in ("sentence_embeds", "train_features", "train_labels")
    }
    labels = tensors["train_labels"].long()
    seenclasses = torch.unique(labels, sorted=True)
    allclasses = torch.arange(200)
    unseenclasses = allclasses[~torch.isin(allclasses, seenclasses)]
    if labels.numel() != 7057 or seenclasses.numel() != 150 or unseenclasses.numel() != 50:
        raise ValueError("CUB trainval contract must be 7057 samples and 150/50 classes.")
    centroids = visual_centroids(tensors["train_features"], labels, seenclasses)
    model = TGVPRH1(
        tensors["sentence_embeds"],
        seenclasses,
        centroids,
        dropout=config["dropout"],
        inner_ratio=config["inner_ratio"],
        outer_ratio=config["outer_ratio"],
        temperature=config["temperature"],
    ).to(device)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=config["lr_stages"][0]["lr"], weight_decay=config["weight_decay"]
    )
    stages = config["lr_stages"]
    boundaries = []
    total = 0
    for stage in stages:
        total += int(stage["epochs"])
        boundaries.append(total)
    active_stage = 0
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=stages[0]["epochs"], eta_min=stages[0]["eta_min"]
    )
    global_to_seen = torch.full((200,), -1, dtype=torch.long)
    global_to_seen[seenclasses] = torch.arange(150)
    generator = torch.Generator(device="cpu").manual_seed(seed)
    history = []
    best_state = None
    for epoch in range(1, 51):
        target_stage = next(index for index, boundary in enumerate(boundaries) if epoch <= boundary)
        if target_stage != active_stage:
            active_stage = target_stage
            stage = stages[active_stage]
            for group in optimizer.param_groups:
                group["lr"] = float(stage["lr"])
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=stage["epochs"], eta_min=stage["eta_min"]
            )
        model.train()
        loss_sum = ce_sum = topology_sum = 0.0
        sample_count = 0
        for _ in range(labels.numel() // int(config["batch_size"])):
            indices = legacy_batch_indices(labels.numel(), config["batch_size"], generator)
            features = tensors["train_features"][indices].to(device).float()
            targets = global_to_seen[labels[indices]].to(device)
            optimizer.zero_grad(set_to_none=True)
            ce = F.cross_entropy(model.logits(features, seenclasses), targets)
            topology = model.topology_loss()
            loss = ce + float(config["topology_weight"]) * topology
            if not torch.isfinite(loss):
                raise FloatingPointError("non-finite training loss.")
            loss.backward()
            if any(
                parameter.grad is not None and not torch.isfinite(parameter.grad).all()
                for parameter in model.parameters()
            ):
                raise FloatingPointError("non-finite model gradient.")
            optimizer.step()
            loss_sum += float(loss.detach()) * features.size(0)
            ce_sum += float(ce.detach()) * features.size(0)
            topology_sum += float(topology.detach()) * features.size(0)
            sample_count += features.size(0)
        scheduler.step()
        row = {
            "epoch": epoch,
            "train_loss": loss_sum / sample_count,
            "train_ce": ce_sum / sample_count,
            "train_topology": topology_sum / sample_count,
            "learning_rate": float(optimizer.param_groups[0]["lr"]),
        }
        history.append(row)
        print(
            f"epoch={epoch} train_loss={row['train_loss']:.6f} "
            f"topology={row['train_topology']:.6f}"
        )
        if epoch == 50:
            best_state = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_state)
    model.eval()
    checkpoint_path = output_dir / "model_best.pth"
    torch.save(
        {
            "model": {name: value.detach().cpu() for name, value in model.state_dict().items()},
            "config": config,
            "code_commit": code_commit,
            "config_sha256": config_sha,
            "seed": seed,
            "best_epoch": 50,
            "model_id": "TG-VPR-H1-standalone",
            "run_id": run_id,
            "condition": "TG-VPR-H1-standalone-migration",
        },
        checkpoint_path,
    )

    input_sha.update(verify_inputs(config, paths, OFFICIAL_KEYS))
    tensors.update(
        {
            name: torch.load(paths[name], map_location="cpu", weights_only=True)
            for name in OFFICIAL_KEYS
        }
    )
    checked_seen, checked_unseen = load_v5_cub_split(
        paths["res101"], paths["att_splits"], labels,
        tensors["seen_labels"], tensors["unseen_labels"], "cpu"
    )
    if not torch.equal(checked_seen, seenclasses) or not torch.equal(checked_unseen, unseenclasses):
        raise RuntimeError("official split differs from the frozen training split.")
    metrics = evaluate(model, tensors, seenclasses, unseenclasses, device)
    with torch.no_grad():
        weights = model.semantic_group_weights().cpu().tolist()
    result = {
        "model_id": "TG-VPR-H1-standalone",
        "run_id": run_id,
        "condition": "TG-VPR-H1-standalone-migration",
        "code_commit": code_commit,
        "config_sha256": config_sha,
        "seed": seed,
        "best_epoch": 50,
        "formal_evidence": False,
        "official_test_used_for_selection": False,
        "metrics_percent": metrics,
        "semantic_group_weights": weights,
        "input_sha256": input_sha,
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "history": history,
    }
    with (output_dir / "metrics.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print("U={U:.6f}% S={S:.6f}% H={H:.6f}% ZS={ZS:.6f}%".format(**metrics))
    sys.stdout.flush()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run(
        args.config.resolve(), args.output_dir.resolve(), args.expected_commit, args.run_id
    )


if __name__ == "__main__":
    main()
