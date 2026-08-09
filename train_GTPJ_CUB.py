"""V5 干净母版的 CUB 训练入口。

这份入口只接受正式 V5 配置、真实 CLS/局部块缓存和 GPT-5.5 句子缓存。
它不根据机器上“碰巧存在什么文件”切换算法路线。
"""

import argparse
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

import torch
import torch.optim as optim
import yaml

from model.MyModel import GTPJ
from tools.reproducibility import configure_reproducibility
from tools.v5_cub_data import load_v5_cub_split
from tools.v5_runtime import (
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


MODEL_TEMPLATE_ID = "model/v5-template-v1"
EXPERIMENT_ID = "V5-INNOVATION-009"
CACHE_DIR = Path("./data/cache")
TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"
TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"
TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"
EIGHT_SENTENCE_PATH = CACHE_DIR / "CUB_gpt56_8sent_sentence_embeds.pt"
EIGHT_SENTENCE_SHA256 = "8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3"
DATA_RES101_PATH = Path("./data/xlsa17/data/CUB/res101.mat")
DATA_SPLIT_PATH = Path("./data/xlsa17/data/CUB/att_splits.mat")

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


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Train the immutable V5 template on CUB GZSL.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        default="./config/GTPJ_cub_gzsl.yaml",
        help="正式母版或实验副本中的 config.yaml。",
    )
    parser.add_argument(
        "--resume-from",
        type=Path,
        default=None,
        help="同一 V5 母版产生的完整 checkpoint；不支持 auto、重启或微调猜测。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./train_log/CUB"),
        help="本次 RUN 独占的模型与指标输出目录。",
    )
    parser.add_argument(
        "--fingerprint-manifest",
        type=Path,
        default=Path("./.runtime/data_fingerprints/v5_8sent_inputs.json"),
        help="A/B 共用的大文件身份清单；后续运行只做快速身份核验。",
    )
    return parser.parse_args()


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
        raise ValueError("V5 干净母版只接受 dataset='CUB'。")
    if values["text_source"] != "gpt56_8sent":
        raise ValueError("本实验只接受 text_source='gpt56_8sent'。")
    if values["interaction_mode"] != "image_conditioned_pse":
        raise ValueError("实验 A 固定 interaction_mode='image_conditioned_pse'。")
    if float(values["local_weight"]) != 0.2 or values["score_mode"] != "add":
        raise ValueError("V5 固定使用 global + 0.2 * local。")
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
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _require_clean_code_tree(config_path):
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
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
            "正式训练只允许 helper 更新本实验参数表；其余工作树改动为："
            + " | ".join(unexpected)
        )


def _load_training_cache(expected_dim):
    required = [TRAIN_CLS_PATH, TRAIN_PATCH_PATH, TRAIN_LABEL_PATH]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "V5 正式训练缺少真实 CLS/局部块缓存：" + ", ".join(missing)
        )
    cls_features = torch.load(TRAIN_CLS_PATH, map_location="cpu", weights_only=True)
    patches = torch.load(TRAIN_PATCH_PATH, map_location="cpu", weights_only=True)
    labels = torch.load(TRAIN_LABEL_PATH, map_location="cpu", weights_only=True).long()
    if cls_features.dim() != 2 or cls_features.size(1) != expected_dim:
        raise ValueError(f"训练 CLS 必须是 [N, {expected_dim}]，实际为 {tuple(cls_features.shape)}。")
    if patches.dim() != 3 or tuple(patches.shape[1:]) != (576, expected_dim):
        raise ValueError(
            f"训练局部块必须是 [N, 576, {expected_dim}]，实际为 {tuple(patches.shape)}。"
        )
    if labels.dim() != 1 or not (len(cls_features) == len(patches) == len(labels)):
        raise ValueError("训练 CLS、局部块和标签的样本数量或形状不一致。")
    return cls_features, patches, labels


def _load_eight_sentences(expected_classes, expected_dim, device):
    if not EIGHT_SENTENCE_PATH.is_file():
        raise FileNotFoundError(
            "正式训练缺少固定 8 句缓存：" + str(EIGHT_SENTENCE_PATH)
        )
    sentences = torch.load(EIGHT_SENTENCE_PATH, map_location="cpu", weights_only=True)
    if (
        sentences.dim() != 3
        or sentences.size(0) != expected_classes
        or sentences.size(1) != 8
        or sentences.size(2) != expected_dim
    ):
        raise ValueError(
            f"8 句缓存必须是 [{expected_classes}, 8, {expected_dim}]，"
            f"实际为 {tuple(sentences.shape)}。"
        )
    return sentences.to(device).float()


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
        optimizer,
        T_max=int(stage["epochs"]),
        eta_min=float(stage["eta_min"]),
    )


args = _parse_args()
config, config_values, config_path = _load_config(args.config)
config_hash = sha256_file(config_path)
_require_clean_code_tree(config_path)
code_commit = _current_code_commit()

log_dir = args.output_dir.resolve()
log_dir.mkdir(parents=True, exist_ok=args.resume_from is not None)
log_path = log_dir / "model_training.log"
fingerprint_manifest_path = args.fingerprint_manifest.resolve()


def print_log(message):
    text = str(message)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(text + "\n")


seed = int(config.random_seed)
repro_state = configure_reproducibility(
    seed,
    strict_determinism=False,
    deterministic_warn_only=True,
)

print_log("=" * 60)
print_log("V5 实验 A | 图像条件 PSE 句子选择")
print_log(f"实验：{EXPERIMENT_ID}")
print_log(f"母版：{MODEL_TEMPLATE_ID}")
print_log(f"配置：{config_path}")
print_log(f"配置 SHA-256：{config_hash}")
print_log(f"代码 commit：{code_commit}")
print_log(f"随机种子：{seed}")
print_log("固定句子槽位：喙/头部/身体羽毛/翅膀/尾巴/腿部/整体/独特判别特征")
print_log(f"局部分支融合：global + {config.local_weight} * local")
print_log(f"PyTorch/CUDA：{repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
print_log("=" * 60)

input_paths = {
    "xlsa17_res101": DATA_RES101_PATH,
    "xlsa17_att_splits": DATA_SPLIT_PATH,
    "train_cls": TRAIN_CLS_PATH,
    "train_patches": TRAIN_PATCH_PATH,
    "train_labels": TRAIN_LABEL_PATH,
    "gpt56_8sent_sentences": EIGHT_SENTENCE_PATH,
    **{f"test_{name}": path for name, path in v5_test_cache_paths().items()},
}
before_load_records = {
    name: input_record(path, manifest_path=fingerprint_manifest_path)
    for name, path in input_paths.items()
}
train_cls, train_patches, train_labels = _load_training_cache(int(config.dim_f_clip))
sentence_embeds = _load_eight_sentences(
    int(config.num_class), int(config.dim_f_clip), config.device
)
test_cache = load_v5_test_cache()
seenclasses, unseenclasses = load_v5_cub_split(
    DATA_RES101_PATH,
    DATA_SPLIT_PATH,
    train_labels,
    test_cache["seen_labels"],
    test_cache["unseen_labels"],
    config.device,
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
        path,
        input_tensors.get(name),
        manifest_path=fingerprint_manifest_path,
    )
    for name, path in input_paths.items()
}
validate_stable_input_records(before_load_records, input_records)
run_input_fingerprints = input_fingerprints(input_records)
fingerprint_manifest_record = data_fingerprint_manifest_record(
    fingerprint_manifest_path
)
if fingerprint_manifest_record is None:
    raise RuntimeError("数据身份清单没有成功写入，拒绝正式训练。")
if input_records["gpt56_8sent_sentences"]["sha256"] != EIGHT_SENTENCE_SHA256:
    raise RuntimeError("固定 8 句缓存 SHA-256 与实验设计不一致。")
print_log(
    f"数据身份清单：{fingerprint_manifest_record['path']} | "
    f"sha256={fingerprint_manifest_record['sha256']}"
)
for name, record in input_records.items():
    tensor_summary = ""
    if "shape" in record:
        tensor_summary = f" | shape={record['shape']} | dtype={record['dtype']}"
    print_log(
        f"输入 {name}: {record['path']} | sha256={record['sha256']} | "
        f"size={record['size_bytes']}{tensor_summary}"
    )

# 与历史 V5 一致：数据与缓存准备完成后重置随机状态，再初始化模型。
repro_state = configure_reproducibility(
    seed,
    strict_determinism=False,
    deterministic_warn_only=True,
)
text_embeds = sentence_embeds.mean(dim=1)

model = GTPJ(
    config,
    seenclasses,
    unseenclasses,
    seen_text_embeds=text_embeds[seenclasses],
    unseen_text_embeds=text_embeds[unseenclasses],
    seen_sentence_embeds=sentence_embeds[seenclasses],
    unseen_sentence_embeds=sentence_embeds[unseenclasses],
).to(config.device)

parameter_count = sum(parameter.numel() for parameter in model.parameters())
trainable_parameter_count = sum(
    parameter.numel() for parameter in model.parameters() if parameter.requires_grad
)
state_bytes = sum(
    tensor.numel() * tensor.element_size() for tensor in model.state_dict().values()
)
print_log(
    f"模型规模：parameters={parameter_count}，trainable={trainable_parameter_count}，"
    f"state_bytes={state_bytes} ({state_bytes / (1024 ** 2):.2f} MiB)"
)
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
    checkpoint = torch.load(resume_path, map_location=config.device, weights_only=False)
    required = {
        "template_id",
        "code_commit",
        "epoch",
        "stage_index",
        "best_H",
        "best_metrics",
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
        raise ValueError(f"续训只接受同一母版的完整 checkpoint；缺少 {missing}。")
    if checkpoint["template_id"] != MODEL_TEMPLATE_ID:
        raise ValueError(
            f"checkpoint 来自 {checkpoint['template_id']!r}，不是 {MODEL_TEMPLATE_ID!r}。"
        )
    seenclass_ids = seenclasses.detach().cpu().long().tolist()
    unseenclass_ids = unseenclasses.detach().cpu().long().tolist()
    validate_resume_identity(
        checkpoint,
        template_id=MODEL_TEMPLATE_ID,
        code_commit=code_commit,
        config_values=config_values,
        config_sha256=config_hash,
        fingerprints=run_input_fingerprints,
        fingerprint_manifest=fingerprint_manifest_record,
        seenclasses=seenclass_ids,
        unseenclasses=unseenclass_ids,
    )
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
    active_stage = int(checkpoint["stage_index"])
    checkpoint_epoch = int(checkpoint["epoch"])
    expected_stage = _stage_for_epoch(checkpoint_epoch, boundaries)
    if active_stage != expected_stage:
        raise ValueError(
            f"checkpoint 的 stage_index={active_stage} 与 epoch={checkpoint_epoch} "
            f"应处阶段 {expected_stage} 不一致。"
        )
    start_epoch = checkpoint_epoch + 1
    best_h = float(checkpoint["best_H"])
    best_metrics = dict(checkpoint["best_metrics"])
    restore_rng_state(checkpoint["rng_state"])
    print_log(f"从 epoch {start_epoch} 继续；历史最佳 H={best_h * 100:.2f}%。")

iters_per_epoch = len(train_labels) // int(config.batch_size)
if iters_per_epoch <= 0:
    raise ValueError("训练样本数小于 batch_size，无法完成一个训练 step。")

print_log(f"训练计划：{len(stages)} 段，共 {total_epochs} 个 epoch。")
print_log(f"训练缓存：CLS={tuple(train_cls.shape)}，patch={tuple(train_patches.shape)}。")
best_model_path = log_dir / "model_best.pth"
checkpoint_path = log_dir / "checkpoint_best_full.pth"
if torch.cuda.is_available():
    torch.cuda.reset_peak_memory_stats()
    torch.cuda.synchronize()
training_started_at = time.perf_counter()
last_epoch_diagnostics = None

for epoch in range(start_epoch, total_epochs + 1):
    target_stage = _stage_for_epoch(epoch, boundaries)
    if target_stage != active_stage:
        active_stage = target_stage
        stage = stages[active_stage]
        for group in optimizer.param_groups:
            group["lr"] = float(stage["lr"])
        scheduler = _new_scheduler(optimizer, stage)
        print_log(f"进入第 {active_stage + 1} 段：lr={float(stage['lr']):g}。")

    model.train()
    epoch_loss = 0.0
    sentence_weight_sum = torch.zeros(8)
    sentence_diagnostic_count = 0
    uniform_deviation_sum = 0.0
    prototype_cosine_sum = 0.0
    global_score_abs_sum = 0.0
    local_score_abs_sum = 0.0
    final_score_abs_sum = 0.0
    for step in range(iters_per_epoch):
        optimizer.zero_grad(set_to_none=True)
        indices = torch.randperm(len(train_labels))[: int(config.batch_size)]
        batch_labels = train_labels[indices].to(config.device)
        cls_batch = train_cls[indices].to(config.device).float().unsqueeze(1)
        patch_batch = train_patches[indices].to(config.device).float()
        features = torch.cat([cls_batch, patch_batch], dim=1)

        output = model(features, is_train=True)
        losses = model.compute_loss(dict(output, batch_label=batch_labels))
        losses["loss"].backward()
        optimizer.step()
        epoch_loss += float(losses["loss"].item())

        batch_index = torch.arange(batch_labels.size(0), device=batch_labels.device)
        gt_sentence_weights = output["sentence_weights"][batch_index, batch_labels]
        sentence_weight_sum += gt_sentence_weights.detach().sum(dim=0).cpu()
        sentence_diagnostic_count += batch_labels.size(0)
        uniform_deviation_sum += float(
            output["sentence_weight_uniform_deviation"][
                batch_index, batch_labels
            ].detach().sum().item()
        )
        prototype_cosine_sum += float(
            output["prototype_cosine_to_uniform"][
                batch_index, batch_labels
            ].detach().sum().item()
        )
        global_score_abs_sum += float(output["global_logits"].detach().abs().mean().item())
        local_score_abs_sum += float(output["local_logits"].detach().abs().mean().item())
        final_score_abs_sum += float(output["final_logits"].detach().abs().mean().item())

        if (step + 1) % 20 == 0 or step + 1 == iters_per_epoch:
            print_log(
                f"epoch {epoch}/{total_epochs} step {step + 1}/{iters_per_epoch} "
                f"loss={losses['loss'].item():.4f}"
            )

    mean_weights = sentence_weight_sum / max(sentence_diagnostic_count, 1)
    mean_uniform_deviation = uniform_deviation_sum / max(
        sentence_diagnostic_count, 1
    )
    mean_prototype_cosine = prototype_cosine_sum / max(
        sentence_diagnostic_count, 1
    )
    mean_global_score = global_score_abs_sum / iters_per_epoch
    mean_local_score = local_score_abs_sum / iters_per_epoch
    mean_final_score = final_score_abs_sum / iters_per_epoch
    last_epoch_diagnostics = {
        "sentence_weight_mean_by_slot": mean_weights.tolist(),
        "sentence_weight_uniform_abs_deviation": mean_uniform_deviation,
        "prototype_cosine_to_uniform": mean_prototype_cosine,
        "global_score_abs_mean": mean_global_score,
        "local_score_abs_mean": mean_local_score,
        "final_score_abs_mean": mean_final_score,
    }
    print_log(
        "epoch {} 真实类别平均8句权重=[{}] | 与1/8平均偏差={:.6f} | "
        "条件/均匀原型cos={:.6f}".format(
            epoch,
            ", ".join(f"{value:.6f}" for value in mean_weights.tolist()),
            mean_uniform_deviation,
            mean_prototype_cosine,
        )
    )
    print_log(
        "epoch {} 分数绝对均值：global={:.6f} local={:.6f} final={:.6f}".format(
            epoch,
            mean_global_score,
            mean_local_score,
            mean_final_score,
        )
    )

    scheduler.step()
    seen_acc, unseen_acc, harmonic, zsl_acc = evaluate_cached_v5(
        model,
        config.device,
        test_cache,
        seenclasses,
        unseenclasses,
    )
    print_log(
        f"epoch {epoch}: S={seen_acc * 100:.2f}% U={unseen_acc * 100:.2f}% "
        f"H={harmonic * 100:.2f}% ZS={zsl_acc * 100:.2f}% "
        f"avg_loss={epoch_loss / iters_per_epoch:.4f}"
    )

    if harmonic > best_h:
        best_h = harmonic
        best_diagnostics = dict(last_epoch_diagnostics)
        best_metrics = {
            "U": unseen_acc,
            "S": seen_acc,
            "H": harmonic,
            "ZS": zsl_acc,
            "epoch": epoch,
        }
        torch.save(model.state_dict(), best_model_path)
        torch.save(
            {
                "template_id": MODEL_TEMPLATE_ID,
                "code_commit": code_commit,
                "epoch": epoch,
                "stage_index": active_stage,
                "best_H": best_h,
                "best_metrics": best_metrics,
                "config": config_values,
                "config_sha256": config_hash,
                "input_files": input_records,
                "input_fingerprints": run_input_fingerprints,
                "data_fingerprint_manifest": fingerprint_manifest_record,
                "rng_state": capture_rng_state(),
                "seenclasses": seenclasses.detach().cpu().long().tolist(),
                "unseenclasses": unseenclasses.detach().cpu().long().tolist(),
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
            },
            checkpoint_path,
        )
        print_log(
            f"保存新最佳模型：{best_model_path} | "
            f"size={best_model_path.stat().st_size / (1024 ** 2):.2f} MiB"
        )

if torch.cuda.is_available():
    torch.cuda.synchronize()
training_seconds = time.perf_counter() - training_started_at
peak_allocated = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
peak_reserved = torch.cuda.max_memory_reserved() if torch.cuda.is_available() else 0
print_log("训练完成。")
print_log(
    f"最佳 epoch={best_metrics['epoch']}，U={best_metrics['U'] * 100:.2f}%，"
    f"S={best_metrics['S'] * 100:.2f}%，H={best_metrics['H'] * 100:.2f}%，"
    f"ZS={best_metrics['ZS'] * 100:.2f}%。"
)
print_log(
    f"训练耗时={training_seconds:.2f}s | CUDA峰值allocated="
    f"{peak_allocated / (1024 ** 2):.2f}MiB reserved={peak_reserved / (1024 ** 2):.2f}MiB"
)
final_metrics = {
    "schema_version": 1,
    "experiment_id": EXPERIMENT_ID,
    "code_commit": code_commit,
    "config_sha256": config_hash,
    "data_fingerprint_manifest": fingerprint_manifest_record,
    "seed": seed,
    "best_epoch": int(best_metrics["epoch"]),
    "U": float(best_metrics["U"]),
    "S": float(best_metrics["S"]),
    "H": float(best_metrics["H"]),
    "ZS": float(best_metrics["ZS"]),
    "training_seconds": training_seconds,
    "parameter_count": parameter_count,
    "trainable_parameter_count": trainable_parameter_count,
    "state_bytes": state_bytes,
    "model_file": str(best_model_path),
    "model_file_bytes": best_model_path.stat().st_size if best_model_path.is_file() else 0,
    "cuda_peak_allocated_bytes": peak_allocated,
    "cuda_peak_reserved_bytes": peak_reserved,
    "last_epoch_mean_sentence_weights": mean_weights.tolist(),
    "diagnostics": best_diagnostics,
    "last_epoch_diagnostics": last_epoch_diagnostics,
    "model": {
        "parameter_count": parameter_count,
        "trainable_parameter_count": trainable_parameter_count,
        "state_bytes": state_bytes,
        "model_best_path": str(best_model_path),
        "model_best_file_bytes": (
            best_model_path.stat().st_size if best_model_path.is_file() else 0
        ),
    },
    "cuda_memory": {
        "peak_allocated_bytes": peak_allocated,
        "peak_reserved_bytes": peak_reserved,
    },
}
metrics_path = log_dir / "final_metrics.json"
metrics_temp = log_dir / ".final_metrics.json.tmp"
metrics_temp.write_text(
    json.dumps(final_metrics, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
metrics_temp.replace(metrics_path)
print_log(f"最终指标：{metrics_path}")
