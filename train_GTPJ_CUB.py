"""实验 B：PSE + VSCE 的 CUB GZSL 正式训练入口。"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace

import torch
import torch.optim as optim
import yaml

from model.MyModel import GTPJ
from tools.reproducibility import configure_reproducibility
from tools.v5_cub_data import load_v5_cub_split
from tools.v5_runtime import (
    DEFAULT_FINGERPRINT_MANIFEST,
    capture_rng_state,
    data_fingerprint_manifest_record,
    input_fingerprints,
    input_record,
    restore_rng_state,
    sha256_file,
    validate_resume_identity,
    validate_stable_input_records,
)
from tools.v5_evaluation import (
    evaluate_cached_v5,
    load_v5_test_cache,
    v5_test_cache_paths,
)


MODEL_TEMPLATE_ID = "model/v5-template-v1:pse_vsce"
BASE_TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
INTERACTION_MODE = "pse_vsce"
GPT56_SENTENCE_FILENAME = "CUB_gpt56_8sent_sentence_embeds.pt"
GPT56_SENTENCE_SHA256 = (
    "8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3"
)

V5_CONFIG_KEYS = {
    "dataset",
    "num_class",
    "dim_f_clip",
    "device",
    "batch_size",
    "random_seed",
    "text_source",
    "interaction_mode",
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


def build_parser():
    parser = argparse.ArgumentParser(
        description="Train V5 experiment B (PSE + VSCE) on CUB GZSL.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("experiments/v5/innovation/INNOVATION-010_pse_vsce/config.yaml"),
    )
    parser.add_argument("--data-root", type=Path, default=Path("."))
    parser.add_argument("--resume-from", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("train_log/CUB/pse_vsce"))
    parser.add_argument(
        "--fingerprint-manifest",
        type=Path,
        default=DEFAULT_FINGERPRINT_MANIFEST,
        help="A/B 共用的原子数据指纹清单。",
    )
    return parser


def _load_config(path):
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("V5 配置顶层必须是字典。")
    values = {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }
    missing = sorted(V5_CONFIG_KEYS - set(values))
    extra = sorted(set(values) - V5_CONFIG_KEYS)
    if missing or extra:
        raise ValueError(f"V5 配置字段不匹配；缺少={missing}，多出={extra}。")
    if values["dataset"] != "CUB":
        raise ValueError("实验 B 只接受 dataset='CUB'。")
    if values["text_source"] != "gpt56_8sent":
        raise ValueError("实验 B 固定使用 text_source='gpt56_8sent'。")
    if values["interaction_mode"] != INTERACTION_MODE:
        raise ValueError(f"实验 B 固定使用 interaction_mode='{INTERACTION_MODE}'。")
    if float(values["local_weight"]) != 0.2 or values["score_mode"] != "add":
        raise ValueError("实验 B 固定使用 global + 0.2 * local。")
    _validate_lr_stages(values["lr_stages"])
    return SimpleNamespace(**values), values, config_path


def _validate_lr_stages(stages):
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages 必须是非空列表。")
    allowed = {"lr", "epochs", "eta_min"}
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict) or set(stage) != allowed:
            raise ValueError(
                f"lr_stages 第 {index} 段只允许 {sorted(allowed)}，实际为 "
                f"{sorted(stage) if isinstance(stage, dict) else type(stage).__name__}。"
            )
        if float(stage["lr"]) <= 0 or int(stage["epochs"]) <= 0:
            raise ValueError(f"lr_stages 第 {index} 段的 lr/epochs 必须大于 0。")
        if float(stage["eta_min"]) < 0:
            raise ValueError(f"lr_stages 第 {index} 段的 eta_min 不能小于 0。")


def _current_code_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def _require_clean_code_tree(config_path):
    result = subprocess.run(
        ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
    )
    allowed = {
        str((config_path.parent / "PARAMETER_MATRIX.csv").resolve()),
        str((config_path.parent / "PARAMETER_MATRIX.md").resolve()),
    }
    unexpected = []
    for line in result.stdout.splitlines():
        relative = line[3:].strip().strip('"')
        candidate = (Path.cwd() / relative).resolve()
        if str(candidate) not in allowed:
            unexpected.append(line)
    if unexpected:
        raise RuntimeError(
            "正式训练只允许启动收据 helper 更新本实验参数表；其余工作树改动为："
            + " | ".join(unexpected)
        )


def _paths(data_root):
    data_root = Path(data_root).resolve()
    cache_dir = data_root / "data" / "cache"
    return {
        "cache_dir": cache_dir,
        "train_cls": cache_dir / "CUB_train_features.pt",
        "train_patches": cache_dir / "CUB_train_patch_features.pt",
        "train_labels": cache_dir / "CUB_train_labels.pt",
        "sentences": cache_dir / GPT56_SENTENCE_FILENAME,
        "res101": data_root / "data" / "xlsa17" / "data" / "CUB" / "res101.mat",
        "splits": data_root / "data" / "xlsa17" / "data" / "CUB" / "att_splits.mat",
    }


def _load_training_cache(paths, expected_dim):
    required = [paths["train_cls"], paths["train_patches"], paths["train_labels"]]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("正式训练缺少真实 CLS/局部块缓存：" + ", ".join(missing))
    cls_features = torch.load(paths["train_cls"], map_location="cpu", weights_only=True)
    patches = torch.load(paths["train_patches"], map_location="cpu", weights_only=True)
    labels = torch.load(paths["train_labels"], map_location="cpu", weights_only=True).long()
    if cls_features.dim() != 2 or cls_features.size(1) != expected_dim:
        raise ValueError(f"训练 CLS 必须是 [N, {expected_dim}]，实际为 {tuple(cls_features.shape)}。")
    if patches.dim() != 3 or tuple(patches.shape[1:]) != (576, expected_dim):
        raise ValueError(
            f"训练局部块必须是 [N, 576, {expected_dim}]，实际为 {tuple(patches.shape)}。"
        )
    if labels.dim() != 1 or not (len(cls_features) == len(patches) == len(labels)):
        raise ValueError("训练 CLS、局部块和标签的样本数量或形状不一致。")
    return cls_features, patches, labels


def load_sentence_cache(
    path,
    *,
    expected_classes,
    expected_dim,
    device,
    expected_sha256=GPT56_SENTENCE_SHA256,
):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"实验 B 缺少 8 句缓存：{path}")
    actual_sha256 = sha256_file(path)
    if actual_sha256.lower() != str(expected_sha256).lower():
        raise ValueError(
            f"8 句缓存 SHA-256 不一致：expected={expected_sha256}, actual={actual_sha256}。"
        )
    sentences = torch.load(path, map_location="cpu", weights_only=True)
    expected_shape = (int(expected_classes), 8, int(expected_dim))
    if not isinstance(sentences, torch.Tensor) or tuple(sentences.shape) != expected_shape:
        actual = type(sentences).__name__
        if isinstance(sentences, torch.Tensor):
            actual = str(tuple(sentences.shape))
        raise ValueError(f"8 句缓存必须是 {list(expected_shape)} Tensor，实际为 {actual}。")
    if sentences.dtype != torch.float32:
        raise ValueError(f"8 句缓存必须是 torch.float32，实际为 {sentences.dtype}。")
    return sentences.to(device)


def _stage_boundaries(stages):
    boundaries = []
    total = 0
    for stage in stages:
        total += int(stage["epochs"])
        boundaries.append(total)
    return boundaries


def _stage_for_epoch(epoch, boundaries):
    for index, boundary in enumerate(boundaries):
        if epoch <= boundary:
            return index
    raise ValueError(f"epoch {epoch} 超过计划训练轮数 {boundaries[-1]}。")


def _new_scheduler(optimizer, stage):
    return optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(stage["epochs"]), eta_min=float(stage["eta_min"])
    )


def _atomic_write_json(path, payload):
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
            temporary = Path(stream.name)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _new_diagnostic_state(sentence_count, region_count):
    return {
        "count": 0,
        "sentence_sum": torch.zeros(sentence_count, dtype=torch.float64),
        "region_sum": torch.zeros(region_count, dtype=torch.float64),
        "sentence_entropy_sum": 0.0,
        "region_entropy_sum": 0.0,
        "sentence_max_sum": 0.0,
        "region_max_sum": 0.0,
        "global_true_sum": 0.0,
        "local_true_sum": 0.0,
        "final_true_sum": 0.0,
        "match_mean_sum": 0.0,
        "match_std_sum": 0.0,
        "batches": 0,
        "true_class_examples": [],
    }


def _update_diagnostics(state, output, labels, sample_indices=None):
    labels = labels.to(device=output["sentence_weights"].device, dtype=torch.long)
    batch = torch.arange(labels.numel(), device=labels.device)
    sentence = output["sentence_weights"][batch, labels].detach().double().cpu()
    region = output["local_region_weights"][batch, labels].detach().double().cpu()
    state["count"] += labels.numel()
    state["sentence_sum"] += sentence.sum(dim=0)
    state["region_sum"] += region.sum(dim=0)
    state["sentence_entropy_sum"] += float(
        (-(sentence * sentence.clamp_min(1e-12).log()).sum(dim=-1)).sum()
    )
    state["region_entropy_sum"] += float(
        (-(region * region.clamp_min(1e-12).log()).sum(dim=-1)).sum()
    )
    state["sentence_max_sum"] += float(sentence.max(dim=-1).values.sum())
    state["region_max_sum"] += float(region.max(dim=-1).values.sum())
    for key, target in (
        ("global_logits", "global_true_sum"),
        ("local_logits", "local_true_sum"),
        ("final_logits", "final_true_sum"),
    ):
        state[target] += float(output[key][batch, labels].detach().sum())
    state["match_mean_sum"] += float(output["match_diagnostics"]["match_mean"].detach())
    state["match_std_sum"] += float(output["match_diagnostics"]["match_std"].detach())
    state["batches"] += 1

    remaining = 8 - len(state["true_class_examples"])
    if remaining > 0:
        selected_indices = output["sgmp_selected_indices"].detach().cpu().long()
        labels_cpu = labels.detach().cpu().long()
        if sample_indices is None:
            sample_indices = torch.full_like(labels_cpu, -1)
        else:
            sample_indices = torch.as_tensor(sample_indices).detach().cpu().long()
        if sample_indices.numel() != labels_cpu.numel():
            raise ValueError("诊断样本索引数量与 batch 大小不一致。")
        global_scores = output["global_logits"][batch, labels].detach().cpu()
        local_scores = output["local_logits"][batch, labels].detach().cpu()
        final_scores = output["final_logits"][batch, labels].detach().cpu()
        for row in range(min(remaining, labels_cpu.numel())):
            sentence_row = sentence[row]
            region_row = region[row]
            top_sentence = int(sentence_row.argmax().item())
            top_region_rank = int(region_row.argmax().item())
            top_patch_index = int(selected_indices[row, top_region_rank].item())
            state["true_class_examples"].append(
                {
                    "train_sample_index": int(sample_indices[row].item()),
                    "class_id": int(labels_cpu[row].item()),
                    "sentence_weights": sentence_row.tolist(),
                    "local_region_weights": region_row.tolist(),
                    "top_sentence_slot": top_sentence,
                    "top_sentence_weight": float(sentence_row[top_sentence]),
                    "top_region_rank": top_region_rank,
                    "top_region_weight": float(region_row[top_region_rank]),
                    "top_patch_index": top_patch_index,
                    "top_patch_row_col": [top_patch_index // 24, top_patch_index % 24],
                    "global_score": float(global_scores[row]),
                    "local_score": float(local_scores[row]),
                    "final_score": float(final_scores[row]),
                }
            )


def _finalize_diagnostics(state):
    count = max(1, int(state["count"]))
    batches = max(1, int(state["batches"]))
    sentence_mean = (state["sentence_sum"] / count).tolist()
    region_mean = (state["region_sum"] / count).tolist()
    return {
        "samples": int(state["count"]),
        "sentence_weight_mean_by_slot": sentence_mean,
        "sentence_uniform_l1": float(sum(abs(value - 0.125) for value in sentence_mean)),
        "sentence_entropy_mean": state["sentence_entropy_sum"] / count,
        "sentence_max_weight_mean": state["sentence_max_sum"] / count,
        "local_region_weight_mean_by_rank": region_mean,
        "local_region_entropy_mean": state["region_entropy_sum"] / count,
        "local_region_max_weight_mean": state["region_max_sum"] / count,
        "global_true_score_mean": state["global_true_sum"] / count,
        "local_true_score_mean": state["local_true_sum"] / count,
        "final_true_score_mean": state["final_true_sum"] / count,
        "scaled_match_mean": state["match_mean_sum"] / batches,
        "scaled_match_std": state["match_std_sum"] / batches,
        "true_class_examples": list(state["true_class_examples"]),
        "true_class_example_note": (
            "最佳 epoch 训练态前 8 个受控样本；句槽、region rank 与 24x24 patch 坐标均从 0 开始。"
        ),
    }


def _cuda_sync(device):
    device = torch.device(device)
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(device)


def _model_size(model):
    return {
        "total_parameters": sum(parameter.numel() for parameter in model.parameters()),
        "trainable_parameters": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "parameter_bytes": sum(
            parameter.numel() * parameter.element_size() for parameter in model.parameters()
        ),
        "buffer_bytes": sum(buffer.numel() * buffer.element_size() for buffer in model.buffers()),
    }


def main(argv=None):
    args = build_parser().parse_args(argv)
    config, config_values, config_path = _load_config(args.config)
    config_hash = sha256_file(config_path)
    _require_clean_code_tree(config_path)
    code_commit = _current_code_commit()

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(f"本次 RUN 输出目录不是空目录：{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "training.log"

    def print_log(message):
        text = str(message)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")

    run_started = time.perf_counter()
    seed = int(config.random_seed)
    repro_state = configure_reproducibility(
        seed, strict_determinism=False, deterministic_warn_only=True
    )
    device = torch.device(config.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(f"配置要求 {device}，但当前 PyTorch 看不到 CUDA。")

    paths = _paths(args.data_root)
    input_paths = {
        "xlsa17_res101": paths["res101"],
        "xlsa17_att_splits": paths["splits"],
        "train_cls": paths["train_cls"],
        "train_patches": paths["train_patches"],
        "train_labels": paths["train_labels"],
        "gpt56_8sent_sentences": paths["sentences"],
        **{
            f"test_{name}": path
            for name, path in v5_test_cache_paths(paths["cache_dir"]).items()
        },
    }
    manifest_path = args.fingerprint_manifest.resolve()
    before_load_records = {
        name: input_record(path, manifest_path=manifest_path)
        for name, path in input_paths.items()
    }
    if before_load_records["gpt56_8sent_sentences"]["sha256"].lower() != GPT56_SENTENCE_SHA256:
        raise ValueError("共享指纹清单中的 8 句缓存 SHA-256 与实验合同不一致。")

    train_cls, train_patches, train_labels = _load_training_cache(
        paths, int(config.dim_f_clip)
    )
    sentence_embeds = load_sentence_cache(
        paths["sentences"],
        expected_classes=int(config.num_class),
        expected_dim=int(config.dim_f_clip),
        device=device,
    )
    test_cache = load_v5_test_cache(paths["cache_dir"])
    seenclasses, unseenclasses = load_v5_cub_split(
        paths["res101"],
        paths["splits"],
        train_labels,
        test_cache["seen_labels"],
        test_cache["unseen_labels"],
        device,
    )
    input_tensors = {
        "train_cls": train_cls,
        "train_patches": train_patches,
        "train_labels": train_labels,
        "gpt56_8sent_sentences": sentence_embeds,
        **{f"test_{name}": tensor for name, tensor in test_cache.items()},
    }
    input_records = {
        name: input_record(
            path, input_tensors.get(name), manifest_path=manifest_path
        )
        for name, path in input_paths.items()
    }
    validate_stable_input_records(before_load_records, input_records)
    run_input_fingerprints = input_fingerprints(input_records)
    manifest_record = data_fingerprint_manifest_record(manifest_path)

    print_log("=" * 68)
    print_log("V5-INNOVATION-010 | PSE + VSCE | CUB GZSL")
    print_log(f"母版：{BASE_TEMPLATE_COMMIT}；运行身份：{MODEL_TEMPLATE_ID}")
    print_log(f"代码 commit：{code_commit}；配置 SHA-256：{config_hash}")
    print_log(f"8句缓存：{paths['sentences']}；SHA-256={GPT56_SENTENCE_SHA256}")
    print_log(f"共享指纹清单：{manifest_record['path']}；SHA-256={manifest_record['sha256']}")
    print_log(f"随机种子：{seed}；设备：{device}")
    print_log(f"PyTorch/CUDA：{repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
    print_log("=" * 68)

    configure_reproducibility(
        seed, strict_determinism=False, deterministic_warn_only=True
    )
    text_embeds = sentence_embeds.mean(dim=1)
    model = GTPJ(
        config,
        seenclasses,
        unseenclasses,
        seen_text_embeds=text_embeds[seenclasses],
        unseen_text_embeds=text_embeds[unseenclasses],
        sentence_embeds=sentence_embeds,
    ).to(device)

    stages = config.lr_stages
    boundaries = _stage_boundaries(stages)
    total_epochs = boundaries[-1]
    optimizer = optim.Adam(
        model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
    )
    scheduler = _new_scheduler(optimizer, stages[0])
    active_stage = 0
    start_epoch = 1
    best_h = -1.0
    best_metrics = {"U": 0.0, "S": 0.0, "H": 0.0, "ZS": 0.0, "epoch": 0}
    best_diagnostics = None

    if args.resume_from is not None:
        resume_path = args.resume_from.resolve()
        if not resume_path.is_file():
            raise FileNotFoundError(f"续训 checkpoint 不存在：{resume_path}")
        checkpoint = torch.load(resume_path, map_location=device, weights_only=False)
        required = {
            "template_id",
            "code_commit",
            "epoch",
            "stage_index",
            "best_H",
            "best_metrics",
            "best_diagnostics",
            "config",
            "config_sha256",
            "input_files",
            "input_fingerprints",
            "data_fingerprint_manifest",
            "rng_state",
            "seenclasses",
            "unseenclasses",
            "model_state_dict",
            "optimizer_state_dict",
            "scheduler_state_dict",
        }
        if not isinstance(checkpoint, dict) or not required.issubset(checkpoint):
            missing = sorted(required - set(checkpoint if isinstance(checkpoint, dict) else {}))
            raise ValueError(f"续训 checkpoint 不完整；缺少 {missing}。")
        if checkpoint["template_id"] != MODEL_TEMPLATE_ID:
            raise ValueError("checkpoint 不是 PSE + VSCE 实验 B 的完整断点。")
        validate_resume_identity(
            checkpoint,
            template_id=MODEL_TEMPLATE_ID,
            code_commit=code_commit,
            config_values=config_values,
            config_sha256=config_hash,
            fingerprints=run_input_fingerprints,
            seenclasses=seenclasses.detach().cpu().long().tolist(),
            unseenclasses=unseenclasses.detach().cpu().long().tolist(),
        )
        if checkpoint["data_fingerprint_manifest"] != manifest_record:
            raise ValueError("checkpoint 的共享数据指纹清单与当前运行不一致。")
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        active_stage = int(checkpoint["stage_index"])
        checkpoint_epoch = int(checkpoint["epoch"])
        if active_stage != _stage_for_epoch(checkpoint_epoch, boundaries):
            raise ValueError("checkpoint 的训练阶段与 epoch 不一致。")
        start_epoch = checkpoint_epoch + 1
        best_h = float(checkpoint["best_H"])
        best_metrics = dict(checkpoint["best_metrics"])
        best_diagnostics = checkpoint["best_diagnostics"]
        restore_rng_state(checkpoint["rng_state"])

    iters_per_epoch = len(train_labels) // int(config.batch_size)
    if iters_per_epoch <= 0:
        raise ValueError("训练样本数小于 batch_size，无法完成一个训练 step。")

    model_size = _model_size(model)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    _cuda_sync(device)
    training_started = time.perf_counter()
    final_diagnostics = None
    model_path = output_dir / "model_best.pth"
    checkpoint_path = output_dir / "checkpoint_best.pth"

    for epoch in range(start_epoch, total_epochs + 1):
        target_stage = _stage_for_epoch(epoch, boundaries)
        if target_stage != active_stage:
            active_stage = target_stage
            stage = stages[active_stage]
            for group in optimizer.param_groups:
                group["lr"] = float(stage["lr"])
            scheduler = _new_scheduler(optimizer, stage)

        epoch_started = time.perf_counter()
        model.train()
        epoch_loss = 0.0
        diagnostic_state = _new_diagnostic_state(8, int(config.fgvd_select_k))
        for step in range(iters_per_epoch):
            optimizer.zero_grad(set_to_none=True)
            indices = torch.randperm(len(train_labels))[: int(config.batch_size)]
            batch_labels = train_labels[indices].to(device)
            cls_batch = train_cls[indices].to(device).float().unsqueeze(1)
            patch_batch = train_patches[indices].to(device).float()
            features = torch.cat([cls_batch, patch_batch], dim=1)

            output = model(features, is_train=True)
            losses = model.compute_loss(dict(output, batch_label=batch_labels))
            losses["loss"].backward()
            optimizer.step()
            epoch_loss += float(losses["loss"].item())
            _update_diagnostics(
                diagnostic_state,
                output,
                batch_labels,
                sample_indices=indices,
            )
            if (step + 1) % 20 == 0 or step + 1 == iters_per_epoch:
                print_log(
                    f"epoch {epoch}/{total_epochs} step {step + 1}/{iters_per_epoch} "
                    f"loss={losses['loss'].item():.4f}"
                )

        scheduler.step()
        seen_acc, unseen_acc, harmonic, zsl_acc = evaluate_cached_v5(
            model, device, test_cache, seenclasses, unseenclasses
        )
        final_diagnostics = _finalize_diagnostics(diagnostic_state)
        epoch_seconds = time.perf_counter() - epoch_started
        print_log(
            f"epoch {epoch}: S={seen_acc * 100:.2f}% U={unseen_acc * 100:.2f}% "
            f"H={harmonic * 100:.2f}% ZS={zsl_acc * 100:.2f}% "
            f"avg_loss={epoch_loss / iters_per_epoch:.4f} time={epoch_seconds:.1f}s"
        )
        print_log(
            "8句权重均值="
            + json.dumps(final_diagnostics["sentence_weight_mean_by_slot"], ensure_ascii=False)
        )
        print_log(
            f"区域权重：entropy={final_diagnostics['local_region_entropy_mean']:.4f} "
            f"max={final_diagnostics['local_region_max_weight_mean']:.4f}；"
            f"分数 global/local/final="
            f"{final_diagnostics['global_true_score_mean']:.4f}/"
            f"{final_diagnostics['local_true_score_mean']:.4f}/"
            f"{final_diagnostics['final_true_score_mean']:.4f}"
        )

        if harmonic > best_h:
            best_h = harmonic
            best_metrics = {
                "U": unseen_acc,
                "S": seen_acc,
                "H": harmonic,
                "ZS": zsl_acc,
                "epoch": epoch,
            }
            best_diagnostics = final_diagnostics
            torch.save(model.state_dict(), model_path)
            torch.save(
                {
                    "template_id": MODEL_TEMPLATE_ID,
                    "base_template_commit": BASE_TEMPLATE_COMMIT,
                    "interaction_mode": INTERACTION_MODE,
                    "code_commit": code_commit,
                    "epoch": epoch,
                    "stage_index": active_stage,
                    "best_H": best_h,
                    "best_metrics": best_metrics,
                    "best_diagnostics": best_diagnostics,
                    "config": config_values,
                    "config_sha256": config_hash,
                    "input_files": input_records,
                    "input_fingerprints": run_input_fingerprints,
                    "data_fingerprint_manifest": manifest_record,
                    "rng_state": capture_rng_state(),
                    "seenclasses": seenclasses.detach().cpu().long().tolist(),
                    "unseenclasses": unseenclasses.detach().cpu().long().tolist(),
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict(),
                },
                checkpoint_path,
            )

    _cuda_sync(device)
    training_seconds = time.perf_counter() - training_started
    cuda_memory = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0}
    if device.type == "cuda":
        cuda_memory = {
            "peak_allocated_bytes": int(torch.cuda.max_memory_allocated(device)),
            "peak_reserved_bytes": int(torch.cuda.max_memory_reserved(device)),
        }
    final_payload = {
        "status": "completed",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "interaction_mode": INTERACTION_MODE,
        "base_template_commit": BASE_TEMPLATE_COMMIT,
        "code_commit": code_commit,
        "config_path": str(config_path),
        "config_sha256": config_hash,
        "seed": seed,
        "U": best_metrics["U"],
        "S": best_metrics["S"],
        "H": best_metrics["H"],
        "ZS": best_metrics["ZS"],
        "best_metrics": best_metrics,
        "training_seconds": training_seconds,
        "total_run_seconds": time.perf_counter() - run_started,
        "model": {
            **model_size,
            "model_best_path": str(model_path),
            "model_best_file_bytes": model_path.stat().st_size if model_path.is_file() else 0,
        },
        "cuda_memory": cuda_memory,
        "diagnostics": best_diagnostics,
        "last_epoch_diagnostics": final_diagnostics,
        "data_fingerprint_manifest": manifest_record,
        "input_fingerprints": run_input_fingerprints,
    }
    _atomic_write_json(output_dir / "final_metrics.json", final_payload)
    print_log(
        f"训练完成：best H={best_metrics['H'] * 100:.2f}%，"
        f"训练耗时={training_seconds:.1f}s，模型文件={final_payload['model']['model_best_file_bytes']} bytes。"
    )
    return final_payload


if __name__ == "__main__":
    main()
