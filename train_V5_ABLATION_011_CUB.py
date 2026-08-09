"""V5-ABLATION-011 当前母版 global-only 的独立 CUB 训练入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
from types import SimpleNamespace
import subprocess

import torch
import torch.optim as optim
import yaml

from tools.reproducibility import configure_reproducibility
from tools.v5_cub_data import load_v5_cub_split
from tools.v5_runtime import (
    capture_rng_state,
    input_fingerprints,
    input_record,
    sha256_file,
    validate_stable_input_records,
)


ROOT = Path(__file__).resolve().parent
MODEL_TEMPLATE_ID = "MODEL-V5-TEMPLATE-V1@2f5fa5e"
EXPERIMENT_ID = "V5-ABLATION-011"
CANONICAL_CONFIG_PATH = ROOT / "experiments" / "v5" / "config.yaml"
MODEL_SOURCE_PATH = ROOT / "model" / "V5GlobalOnly.py"
CANONICAL_MODEL_SOURCE_PATH = ROOT / "model" / "MyModel.py"
ENTRY_SOURCE_PATH = ROOT / "train_V5_ABLATION_011_CUB.py"

V5_TEMPLATE_CONFIG_KEYS = {
    "dataset",
    "num_class",
    "dim_f_clip",
    "device",
    "batch_size",
    "random_seed",
    "text_source",
    "pse_heads",
    "pse_dropout",
    "pse_inner_ratio",
    "pse_outer_ratio",
    "tf_common_dim",
    "tf_heads",
    "tf_dropout",
    "weight_s2v",
    "local_weight",
    "fgvd_select_k",
    "score_mode",
    "lambda_consist",
    "consist_temp",
    "consist_dynamic_gamma",
    "lambda_topo_pearson",
    "icsa_ratio",
    "icsa_hidden",
    "lambda_bmdd",
    "msdn_temp",
    "sgmp_topk",
    "sgmp_hidden",
    "lambda_mpp",
    "lambda_neg",
    "sgmp_neg_margin",
    "lr_stages",
}
V5_ABLATION_011_CONFIG_KEYS = V5_TEMPLATE_CONFIG_KEYS | {"score_path"}


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="训练 V5-ABLATION-011 current global-only CUB GZSL。",
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-run-commit", required=True)
    return parser.parse_args(argv)


def _unwrap_config(path):
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"配置文件不存在：{resolved}")
    raw_bytes = resolved.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    raw = yaml.safe_load(raw_bytes.decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("配置顶层必须是字典。")
    values = {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }
    return values, resolved, digest


def _load_config(path):
    values, resolved, digest = _unwrap_config(path)
    missing = sorted(V5_ABLATION_011_CONFIG_KEYS - set(values))
    extra = sorted(set(values) - V5_ABLATION_011_CONFIG_KEYS)
    if missing or extra:
        raise ValueError(f"消融配置字段不匹配；缺少={missing}，多出={extra}。")
    canonical, _, _ = _unwrap_config(CANONICAL_CONFIG_PATH)
    if set(canonical) != V5_TEMPLATE_CONFIG_KEYS:
        raise ValueError("仓库 current V5 配置字段已偏离冻结母版。")
    candidate_canonical = {key: value for key, value in values.items() if key != "score_path"}
    if candidate_canonical != canonical:
        changed = sorted(
            key for key in canonical if candidate_canonical.get(key) != canonical[key]
        )
        raise ValueError(f"global-only 只允许改变 score_path；其余差异={changed}。")
    if values["score_path"] != "global_only":
        raise ValueError("V5-ABLATION-011 只接受 score_path='global_only'。")
    if values["dataset"] != "CUB" or values["text_source"] != "gpt55":
        raise ValueError("V5-ABLATION-011 只接受 CUB 与 gpt55 文本。")
    _validate_lr_stages(values["lr_stages"])
    return SimpleNamespace(**values), values, resolved, digest


def _validate_lr_stages(stages):
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages 必须是非空列表。")
    allowed = {"lr", "epochs", "eta_min"}
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict) or set(stage) != allowed:
            raise ValueError(f"lr_stages 第 {index} 段字段必须是 {sorted(allowed)}。")
        if float(stage["lr"]) <= 0 or int(stage["epochs"]) <= 0:
            raise ValueError(f"lr_stages 第 {index} 段的 lr/epochs 必须大于 0。")
        if float(stage["eta_min"]) < 0:
            raise ValueError(f"lr_stages 第 {index} 段的 eta_min 不能小于 0。")


def _data_paths(data_root):
    root = Path(data_root).resolve()
    cache = root / "cache"
    cub = root / "xlsa17" / "data" / "CUB"
    return {
        "xlsa17_res101": cub / "res101.mat",
        "xlsa17_att_splits": cub / "att_splits.mat",
        "train_cls": cache / "CUB_train_features.pt",
        "train_labels": cache / "CUB_train_labels.pt",
        "gpt55_sentences": cache / "CUB_gpt55_sentence_embeds.pt",
        "test_seen_cls": cache / "CUB_test_seen_features.pt",
        "test_seen_labels": cache / "CUB_test_seen_labels.pt",
        "test_unseen_cls": cache / "CUB_test_unseen_features.pt",
        "test_unseen_labels": cache / "CUB_test_unseen_labels.pt",
    }


def _require_input_files(paths):
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("global-only 输入不完整：" + ", ".join(missing))


def _load_training_cache(paths, expected_dim, torch_module=torch):
    cls_features = torch_module.load(
        paths["train_cls"], map_location="cpu", weights_only=True
    )
    labels = torch_module.load(
        paths["train_labels"], map_location="cpu", weights_only=True
    ).long()
    if cls_features.dim() != 2 or cls_features.size(1) != int(expected_dim):
        raise ValueError(
            f"训练 CLS 必须是 [N, {int(expected_dim)}]，实际为 {tuple(cls_features.shape)}。"
        )
    if labels.dim() != 1 or labels.size(0) != cls_features.size(0):
        raise ValueError("训练 CLS 与标签的数量或形状不一致。")
    return cls_features, labels


def _load_test_cache(paths, expected_dim, torch_module=torch):
    cache = {
        "seen_cls": torch_module.load(
            paths["test_seen_cls"], map_location="cpu", weights_only=True
        ),
        "seen_labels": torch_module.load(
            paths["test_seen_labels"], map_location="cpu", weights_only=True
        ).long(),
        "unseen_cls": torch_module.load(
            paths["test_unseen_cls"], map_location="cpu", weights_only=True
        ),
        "unseen_labels": torch_module.load(
            paths["test_unseen_labels"], map_location="cpu", weights_only=True
        ).long(),
    }
    for split in ("seen", "unseen"):
        features = cache[f"{split}_cls"]
        labels = cache[f"{split}_labels"]
        if features.dim() != 2 or features.size(1) != int(expected_dim):
            raise ValueError(f"{split} CLS 必须是 [N, {int(expected_dim)}]。")
        if labels.dim() != 1 or labels.size(0) != features.size(0):
            raise ValueError(f"{split} CLS 与标签的数量或形状不一致。")
    return cache


def _load_sentences(path, expected_classes, expected_dim, torch_module=torch):
    sentences = torch_module.load(path, map_location="cpu", weights_only=True)
    if (
        sentences.dim() != 3
        or sentences.size(0) != int(expected_classes)
        or sentences.size(2) != int(expected_dim)
    ):
        raise ValueError(
            f"gpt55 句子必须是 [{int(expected_classes)}, M, {int(expected_dim)}]。"
        )
    return sentences.float()


def _record_inputs(paths, tensors):
    return {
        name: input_record(path, tensors.get(name)) for name, path in paths.items()
    }


def _validate_cuda(config, cuda_is_available=None):
    available = torch.cuda.is_available() if cuda_is_available is None else cuda_is_available
    if not str(config.device).startswith("cuda"):
        raise RuntimeError("正式 global-only 运行只允许 CUDA device。")
    if not available:
        raise RuntimeError("正式 global-only 运行要求 CUDA 可见。")


def _validate_git_state(expected_run_commit, *, actual_commit, status_text):
    expected = str(expected_run_commit).strip().lower()
    actual = str(actual_commit).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError("--expected-run-commit 必须是完整 40 位 Git commit。")
    if actual != expected:
        raise RuntimeError(f"当前 commit 与 expected-run-commit 不一致：{actual} != {expected}。")
    if str(status_text).strip():
        raise RuntimeError("正式 global-only 运行要求 clean git 工作区。")


def _validate_absent_run_dir(run_dir):
    resolved = Path(run_dir).resolve()
    if resolved.exists():
        raise FileExistsError(f"run-dir 已存在，禁止覆盖：{resolved}")
    return resolved


def _git_text(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _atomic_write_text(path, text):
    destination = Path(path)
    temporary = destination.with_name(destination.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, destination)


class AtomicLogger:
    def __init__(self, path):
        self.path = Path(path)
        self._lines = []

    def __call__(self, message):
        text = str(message)
        self._lines.append(text)
        _atomic_write_text(self.path, "\n".join(self._lines) + "\n")
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))


def _atomic_write_json(path, payload):
    _atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _atomic_torch_save(path, payload, torch_module=torch):
    destination = Path(path)
    temporary = destination.with_name(destination.name + ".tmp")
    torch_module.save(payload, temporary)
    os.replace(temporary, destination)


def _require_finite_tensor(name, tensor):
    if not bool(torch.isfinite(tensor).all().item()):
        raise FloatingPointError(f"{name} 出现非有限数。")


def _metric_payload(metrics, epoch):
    seen, unseen, harmonic, zsl = (float(value) for value in metrics)
    values = {"S": seen, "U": unseen, "H": harmonic, "ZS": zsl}
    if not all(math.isfinite(value) for value in values.values()):
        raise FloatingPointError("评估指标出现非有限数。")
    if not all(0.0 <= value <= 1.0 for value in values.values()):
        raise ValueError("评估指标必须位于 [0, 1]。")
    return {**values, "epoch": int(epoch), "metric_unit": "fraction_0_to_1"}


def _per_class_accuracy(labels, predictions, classes):
    values = []
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"评估缓存缺少类别 {int(class_id)}。")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean().item())


def _predict_cls(model, cls_features, device, batch_size):
    predictions = []
    model.eval()
    with torch.inference_mode():
        for start in range(0, cls_features.size(0), int(batch_size)):
            batch = cls_features[start : start + int(batch_size)].to(device).float()
            logits = model(batch, is_train=False)["clip_S_pp"]
            _require_finite_tensor("评估 logits", logits)
            predictions.append(logits.detach().cpu())
    return torch.cat(predictions, dim=0)


def _evaluate_cls_only(model, device, cache, seenclasses, unseenclasses, batch_size):
    seenclasses = torch.as_tensor(seenclasses).detach().cpu().long()
    unseenclasses = torch.as_tensor(unseenclasses).detach().cpu().long()
    seen_logits = _predict_cls(model, cache["seen_cls"], device, batch_size)
    unseen_logits = _predict_cls(model, cache["unseen_cls"], device, batch_size)
    seen_prediction = seen_logits.argmax(dim=1)
    unseen_prediction = unseen_logits.argmax(dim=1)
    unseen_only_prediction = unseenclasses[unseen_logits[:, unseenclasses].argmax(dim=1)]
    seen = _per_class_accuracy(cache["seen_labels"], seen_prediction, seenclasses)
    unseen = _per_class_accuracy(cache["unseen_labels"], unseen_prediction, unseenclasses)
    zsl = _per_class_accuracy(
        cache["unseen_labels"], unseen_only_prediction, unseenclasses
    )
    denominator = seen + unseen
    harmonic = 2.0 * seen * unseen / denominator if denominator else 0.0
    return seen, unseen, harmonic, zsl


def _stage_boundaries(stages):
    boundaries = []
    total = 0
    for stage in stages:
        total += int(stage["epochs"])
        boundaries.append(total)
    return boundaries


def _stage_for_epoch(epoch, boundaries):
    for index, boundary in enumerate(boundaries):
        if int(epoch) <= boundary:
            return index
    raise ValueError(f"epoch {epoch} 超过训练计划。")


def _new_scheduler(optimizer, stage):
    return optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=int(stage["epochs"]),
        eta_min=float(stage["eta_min"]),
    )


def _source_hashes():
    return {
        str(CANONICAL_MODEL_SOURCE_PATH.relative_to(ROOT)).replace(
            "\\", "/"
        ): sha256_file(CANONICAL_MODEL_SOURCE_PATH),
        str(MODEL_SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"): sha256_file(
            MODEL_SOURCE_PATH
        ),
        str(ENTRY_SOURCE_PATH.relative_to(ROOT)).replace("\\", "/"): sha256_file(
            ENTRY_SOURCE_PATH
        ),
    }


def _validate_execution_identity(config_path, config_sha256, source_hashes):
    if sha256_file(config_path) != config_sha256:
        raise RuntimeError("配置在读取后发生变化，拒绝创建模型或启动训练。")
    if _source_hashes() != source_hashes:
        raise RuntimeError("源码在 clean 检查后发生变化，拒绝创建模型或启动训练。")


def main(argv=None):
    args = _parse_args(argv)
    config, config_values, config_path, config_sha256 = _load_config(args.config)
    _validate_cuda(config)
    run_dir = _validate_absent_run_dir(args.run_dir)
    actual_commit = _git_text("rev-parse", "HEAD")
    status_text = _git_text("status", "--porcelain")
    _validate_git_state(
        args.expected_run_commit,
        actual_commit=actual_commit,
        status_text=status_text,
    )
    source_hashes = _source_hashes()
    _validate_execution_identity(config_path, config_sha256, source_hashes)

    paths = _data_paths(args.data_root)
    _require_input_files(paths)
    before_records = _record_inputs(paths, {})
    dim_f = int(config.dim_f_clip)
    train_cls, train_labels = _load_training_cache(paths, dim_f)
    test_cache = _load_test_cache(paths, dim_f)
    sentences = _load_sentences(paths["gpt55_sentences"], config.num_class, dim_f)
    seenclasses, unseenclasses = load_v5_cub_split(
        paths["xlsa17_res101"],
        paths["xlsa17_att_splits"],
        train_labels,
        test_cache["seen_labels"],
        test_cache["unseen_labels"],
        "cpu",
    )
    tensors = {
        "train_cls": train_cls,
        "train_labels": train_labels,
        "gpt55_sentences": sentences,
        "test_seen_cls": test_cache["seen_cls"],
        "test_seen_labels": test_cache["seen_labels"],
        "test_unseen_cls": test_cache["unseen_cls"],
        "test_unseen_labels": test_cache["unseen_labels"],
    }
    input_records = _record_inputs(paths, tensors)
    validate_stable_input_records(before_records, input_records)
    fingerprints = input_fingerprints(input_records)

    # 项目模型延迟到 clean/身份检查之后导入；导入前后都复核磁盘内容。
    _validate_execution_identity(config_path, config_sha256, source_hashes)
    from model.MyModel import GTPJ
    from model.V5GlobalOnly import GlobalOnlyGTPJ

    _validate_execution_identity(config_path, config_sha256, source_hashes)

    run_dir.mkdir(parents=True, exist_ok=False)
    log = AtomicLogger(run_dir / "training.log")
    seed = int(config.random_seed)
    repro_state = configure_reproducibility(
        seed, strict_determinism=False, deterministic_warn_only=True
    )
    log(f"{EXPERIMENT_ID} | current V5 global-only")
    log(f"母版：{MODEL_TEMPLATE_ID}")
    log(f"run_commit：{actual_commit}")
    log(f"配置：{config_path} | sha256={config_sha256}")
    log(f"data_root：{Path(args.data_root).resolve()}")
    log(f"随机种子：{seed} | device={config.device}")
    for name, record in input_records.items():
        shape = f" | shape={record['shape']} | dtype={record['dtype']}" if "shape" in record else ""
        log(
            f"输入 {name}: {record['path']} | sha256={record['sha256']} | "
            f"size={record['size_bytes']}{shape}"
        )

    text_embeds = sentences.mean(dim=1)
    configure_reproducibility(
        seed, strict_determinism=False, deterministic_warn_only=True
    )
    donor = GTPJ(
        config,
        seenclasses,
        unseenclasses,
        text_embeds[seenclasses],
        text_embeds[unseenclasses],
        seen_sentence_embeds=sentences[seenclasses],
    )
    model = GlobalOnlyGTPJ.from_canonical(donor).to(config.device)
    del donor
    _validate_execution_identity(config_path, config_sha256, source_hashes)

    stages = config.lr_stages
    boundaries = _stage_boundaries(stages)
    total_epochs = boundaries[-1]
    optimizer = optim.Adam(
        model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
    )
    scheduler = _new_scheduler(optimizer, stages[0])
    active_stage = 0
    batch_size = int(config.batch_size)
    steps_per_epoch = len(train_labels) // batch_size
    if steps_per_epoch <= 0:
        raise ValueError("训练样本数小于 batch_size。")

    best_h = -1.0
    best_metrics = None
    for epoch in range(1, total_epochs + 1):
        target_stage = _stage_for_epoch(epoch, boundaries)
        if target_stage != active_stage:
            active_stage = target_stage
            stage = stages[active_stage]
            for group in optimizer.param_groups:
                group["lr"] = float(stage["lr"])
            scheduler = _new_scheduler(optimizer, stage)
            log(f"进入第 {active_stage + 1} 段：lr={float(stage['lr']):g}。")

        model.train()
        epoch_loss = 0.0
        for step in range(steps_per_epoch):
            optimizer.zero_grad(set_to_none=True)
            indices = torch.randperm(len(train_labels))[:batch_size]
            cls_batch = train_cls[indices].to(config.device).float()
            labels = train_labels[indices].to(config.device)
            output = model(cls_batch, is_train=True)
            _require_finite_tensor("训练 logits", output["logits"])
            losses = model.compute_loss(dict(output, batch_label=labels))
            _require_finite_tensor("训练 loss", losses["loss"])
            losses["loss"].backward()
            optimizer.step()
            epoch_loss += float(losses["loss"].item())
            if (step + 1) % 20 == 0 or step + 1 == steps_per_epoch:
                log(
                    f"epoch {epoch}/{total_epochs} step {step + 1}/{steps_per_epoch} "
                    f"loss={losses['loss'].item():.4f}"
                )
        scheduler.step()

        metrics_tuple = _evaluate_cls_only(
            model,
            config.device,
            test_cache,
            seenclasses,
            unseenclasses,
            batch_size,
        )
        current_metrics = _metric_payload(metrics_tuple, epoch)
        log(
            f"epoch {epoch}: S={current_metrics['S'] * 100:.2f}% "
            f"U={current_metrics['U'] * 100:.2f}% "
            f"H={current_metrics['H'] * 100:.2f}% "
            f"ZS={current_metrics['ZS'] * 100:.2f}% "
            f"avg_loss={epoch_loss / steps_per_epoch:.4f}"
        )

        common_checkpoint = {
            "experiment_id": EXPERIMENT_ID,
            "template_id": MODEL_TEMPLATE_ID,
            "run_commit": actual_commit,
            "epoch": epoch,
            "stage_index": active_stage,
            "config": config_values,
            "config_sha256": config_sha256,
            "input_files": input_records,
            "input_fingerprints": fingerprints,
            "seenclasses": seenclasses.tolist(),
            "unseenclasses": unseenclasses.tolist(),
            "source_sha256": source_hashes,
            "model_state_dict": model.state_dict(),
        }
        if current_metrics["H"] > best_h:
            best_h = current_metrics["H"]
            best_metrics = current_metrics
            _atomic_torch_save(
                run_dir / "model_best.pth",
                {**common_checkpoint, "best_metrics": best_metrics},
            )

        _atomic_torch_save(
            run_dir / "checkpoint_last.pth",
            {
                **common_checkpoint,
                "best_metrics": best_metrics,
                "rng_state": capture_rng_state(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
            },
        )

    assert best_metrics is not None
    metrics_document = {
        **best_metrics,
        "experiment_id": EXPERIMENT_ID,
        "template_id": MODEL_TEMPLATE_ID,
        "run_commit": actual_commit,
        "config_path": str(config_path),
        "config_sha256": config_sha256,
        "data_root": str(Path(args.data_root).resolve()),
        "input_files": input_records,
        "input_fingerprints": fingerprints,
        "seenclasses": seenclasses.tolist(),
        "unseenclasses": unseenclasses.tolist(),
        "source_sha256": source_hashes,
        "reproducibility": repro_state,
    }
    _atomic_write_json(run_dir / "metrics.json", metrics_document)
    log(
        f"最佳 epoch={best_metrics['epoch']}，U={best_metrics['U'] * 100:.2f}%，"
        f"S={best_metrics['S'] * 100:.2f}%，H={best_metrics['H'] * 100:.2f}%，"
        f"ZS={best_metrics['ZS'] * 100:.2f}%。"
    )
    return metrics_document


if __name__ == "__main__":
    main()
