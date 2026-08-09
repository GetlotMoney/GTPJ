"""V5 干净母版的 CUB 训练入口。

这份入口只接受正式 V5 配置、真实 CLS/局部块缓存和 GPT-5.5 句子缓存。
它不根据机器上“碰巧存在什么文件”切换算法路线。
"""

import argparse
from pathlib import Path
import subprocess
from types import SimpleNamespace

import torch
import torch.optim as optim
import yaml

from model.MyModel import GTPJ
from tools.reproducibility import configure_reproducibility, make_batch_generator
from tools.v5_cub_data import (
    build_v5_class_disjoint_validation_split,
    load_v5_cub_split,
)
from tools.v5_runtime import (
    capture_rng_state,
    data_fingerprint_manifest_record,
    input_fingerprints,
    input_record,
    restore_rng_state,
    sha256_file,
    validate_resume_output_directory,
    validate_resume_identity,
    validate_stable_input_records,
)
from tools.v5_evaluation import (
    evaluate_cached_v5,
    evaluate_indexed_cached_v5,
    load_v5_test_cache,
    v5_test_cache_paths,
)


MODEL_TEMPLATE_ID = "model/v5-template-v1"
CACHE_DIR = Path("./data/cache")
TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"
TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"
TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"
GPT55_SENTENCE_PATH = CACHE_DIR / "CUB_gpt55_sentence_embeds.pt"
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

V5_EXPERIMENT_CONFIG_DEFAULTS = {
    "pse_mode": "legacy_sentence",
    "pse_apply_unseen": False,
    "pse_class_residual_ratio": 0.1,
    "pse_class_dropout": 0.0,
    "lambda_self_calibration": 0.0,
    "self_calibration_target": 0.05,
    "evaluation_split": "test",
    "validation_seen_holdout_fraction": 0.2,
    "validation_split_seed": 20260810,
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
        required=True,
        help="本次 RUN 的唯一输出目录；新运行要求目录尚不存在。",
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
    allowed = V5_CONFIG_KEYS | set(V5_EXPERIMENT_CONFIG_DEFAULTS)
    extra = sorted(set(values) - allowed)
    if missing or extra:
        raise ValueError(f"V5 配置字段不匹配；缺少={missing}，多出={extra}。")
    values = {**V5_EXPERIMENT_CONFIG_DEFAULTS, **values}
    if values["dataset"] != "CUB":
        raise ValueError("V5 干净母版只接受 dataset='CUB'。")
    if values["text_source"] != "gpt55":
        raise ValueError("V5 干净母版只接受 text_source='gpt55'。")
    if float(values["local_weight"]) != 0.2 or values["score_mode"] != "add":
        raise ValueError("V5 固定使用 global + 0.2 * local。")
    if values["evaluation_split"] not in {"test", "class_disjoint_validation"}:
        raise ValueError(
            "evaluation_split 只能是 'test' 或 'class_disjoint_validation'。"
        )
    if not 0.0 < float(values["validation_seen_holdout_fraction"]) < 1.0:
        raise ValueError("validation_seen_holdout_fraction 必须位于 (0, 1)。")
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


def _require_clean_code_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise RuntimeError("正式 V5 训练要求代码工作树无已跟踪改动。")


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


def _load_gpt55_sentences(expected_classes, expected_dim, device):
    if not GPT55_SENTENCE_PATH.is_file():
        raise FileNotFoundError(
            "V5 正式训练缺少 GPT-5.5 句子缓存：" + str(GPT55_SENTENCE_PATH)
        )
    sentences = torch.load(GPT55_SENTENCE_PATH, map_location="cpu", weights_only=True)
    if (
        sentences.dim() != 3
        or sentences.size(0) != expected_classes
        or sentences.size(2) != expected_dim
    ):
        raise ValueError(
            f"GPT-5.5 句子缓存必须是 [{expected_classes}, M, {expected_dim}]，"
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
_require_clean_code_tree()
code_commit = _current_code_commit()

log_dir = args.output_dir.resolve()
if args.resume_from is None:
    if log_dir.exists():
        raise FileExistsError(f"新运行的输出目录已经存在：{log_dir}")
    log_dir.mkdir(parents=True)
elif not log_dir.is_dir():
    raise FileNotFoundError(f"续训输出目录不存在：{log_dir}")
else:
    validate_resume_output_directory(args.resume_from, log_dir)
log_path = log_dir / "training.log"


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
print_log("V5 干净母版 | CUB GZSL 训练")
print_log(f"母版：{MODEL_TEMPLATE_ID}")
print_log(f"配置：{config_path}")
print_log(f"配置 SHA-256：{config_hash}")
print_log(f"代码 commit：{code_commit}")
print_log(f"随机种子：{seed}")
print_log(f"评估划分：{config.evaluation_split}")
print_log(f"局部分支融合：global + {config.local_weight} * local")
print_log(f"PyTorch/CUDA：{repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
print_log("=" * 60)

input_paths = {
    "xlsa17_res101": DATA_RES101_PATH,
    "xlsa17_att_splits": DATA_SPLIT_PATH,
    "train_cls": TRAIN_CLS_PATH,
    "train_patches": TRAIN_PATCH_PATH,
    "train_labels": TRAIN_LABEL_PATH,
    "gpt55_sentences": GPT55_SENTENCE_PATH,
}
if config.evaluation_split == "test":
    input_paths.update(
        {f"test_{name}": path for name, path in v5_test_cache_paths().items()}
    )
before_load_records = {name: input_record(path) for name, path in input_paths.items()}
full_train_cls, full_train_patches, full_train_labels = _load_training_cache(
    int(config.dim_f_clip)
)
sentence_embeds = _load_gpt55_sentences(
    int(config.num_class), int(config.dim_f_clip), config.device
)
validation_split = None
if config.evaluation_split == "test":
    evaluation_cache = load_v5_test_cache()
    seenclasses, unseenclasses = load_v5_cub_split(
        DATA_RES101_PATH,
        DATA_SPLIT_PATH,
        full_train_labels,
        evaluation_cache["seen_labels"],
        evaluation_cache["unseen_labels"],
        config.device,
    )
    train_cls = full_train_cls
    train_patches = full_train_patches
    train_labels = full_train_labels
    train_sample_positions = None
    evaluation_index = None
    model_sentence_embeds = sentence_embeds
else:
    validation_split = build_v5_class_disjoint_validation_split(
        DATA_RES101_PATH,
        DATA_SPLIT_PATH,
        full_train_labels,
        holdout_fraction=float(config.validation_seen_holdout_fraction),
        split_seed=int(config.validation_split_seed),
    )
    train_positions = validation_split["train_positions"]
    seen_val_positions = validation_split["seen_val_positions"]
    unseen_val_positions = validation_split["unseen_val_positions"]
    # 保留一份共享大缓存；训练和验证只在每个 batch 临时按位置取数据。
    train_cls = full_train_cls
    train_patches = full_train_patches
    train_labels = validation_split["train_labels"]
    train_sample_positions = train_positions
    evaluation_cache = None
    evaluation_index = {
        "seen_positions": seen_val_positions,
        "seen_labels": validation_split["seen_val_labels"],
        "unseen_positions": unseen_val_positions,
        "unseen_labels": validation_split["unseen_val_labels"],
    }
    seenclasses = validation_split["seenclasses"].to(config.device)
    unseenclasses = validation_split["unseenclasses"].to(config.device)
    model_sentence_embeds = sentence_embeds[
        validation_split["original_class_order"].to(sentence_embeds.device)
    ]
    config.num_class = int(model_sentence_embeds.size(0))
    print_log(
        "类不重叠验证："
        f"pseudo-seen={seenclasses.numel()} 类，"
        f"pseudo-unseen={unseenclasses.numel()} 类，"
        f"训练图片={len(train_labels)}，seen 留出={len(evaluation_index['seen_labels'])}，"
        f"unseen 验证={len(evaluation_index['unseen_labels'])}。"
    )
input_tensors = {
    "train_cls": full_train_cls,
    "train_patches": full_train_patches,
    "train_labels": full_train_labels,
    "gpt55_sentences": sentence_embeds,
}
if config.evaluation_split == "test":
    input_tensors.update(
        {f"test_{name}": tensor for name, tensor in evaluation_cache.items()}
    )
input_records = {
    name: input_record(path, input_tensors.get(name))
    for name, path in input_paths.items()
}
validate_stable_input_records(before_load_records, input_records)
run_input_fingerprints = input_fingerprints(input_records)
fingerprint_manifest_record = data_fingerprint_manifest_record()
if fingerprint_manifest_record is None:
    raise RuntimeError("Data fingerprint manifest was not created.")
for name, record in input_records.items():
    tensor_summary = ""
    if "shape" in record:
        tensor_summary = f" | shape={record['shape']} | dtype={record['dtype']}"
    print_log(
        f"输入 {name}: {record['path']} | sha256={record['sha256']} | "
        f"size={record['size_bytes']}{tensor_summary}"
    )
print_log(
    "数据指纹清单: "
    f"{fingerprint_manifest_record['path']} | "
    f"sha256={fingerprint_manifest_record['sha256']}"
)
del input_tensors

# 与历史 V5 一致：数据与缓存准备完成后重置随机状态，再初始化模型。
repro_state = configure_reproducibility(
    seed,
    strict_determinism=False,
    deterministic_warn_only=True,
)
text_embeds = model_sentence_embeds.mean(dim=1)

model = GTPJ(
    config,
    seenclasses,
    unseenclasses,
    seen_text_embeds=text_embeds[seenclasses],
    unseen_text_embeds=text_embeds[unseenclasses],
    seen_sentence_embeds=model_sentence_embeds[seenclasses],
    unseen_sentence_embeds=model_sentence_embeds[unseenclasses],
).to(config.device)

stages = config.lr_stages
boundaries = _stage_boundaries(stages)
total_epochs = boundaries[-1]
optimizer = optim.Adam(
    model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
)
scheduler = _new_scheduler(optimizer, stages[0])
batch_generator = make_batch_generator(True, seed)
active_stage = 0
start_epoch = 1
reported_metrics = None
test_evaluated = False

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
        "test_evaluated",
        "config",
        "config_sha256",
        "input_files",
        "input_fingerprints",
        "data_fingerprint_manifest",
        "rng_state",
        "batch_generator_state",
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
    reported_metrics = dict(checkpoint["best_metrics"])
    test_evaluated = bool(checkpoint["test_evaluated"])
    restore_rng_state(checkpoint["rng_state"])
    batch_generator.set_state(checkpoint["batch_generator_state"].cpu())
    if test_evaluated:
        raise ValueError("该 RUN 已完成唯一一次测试评估，不允许作为续训入口重复评估。")
    print_log(f"从 epoch {start_epoch} 继续训练。")


def save_checkpoint(epoch, *, final_metrics=None, test_was_evaluated=False):
    metrics = final_metrics or {
        "U": 0.0,
        "S": 0.0,
        "H": 0.0,
        "ZS": 0.0,
        "epoch": 0,
    }
    torch.save(
        {
            "template_id": MODEL_TEMPLATE_ID,
            "code_commit": code_commit,
            "epoch": epoch,
            "stage_index": active_stage,
            "best_H": float(metrics["H"]),
            "best_metrics": metrics,
            "test_evaluated": bool(test_was_evaluated),
            "config": config_values,
            "config_sha256": config_hash,
            "input_files": input_records,
            "input_fingerprints": run_input_fingerprints,
            "data_fingerprint_manifest": fingerprint_manifest_record,
            "rng_state": capture_rng_state(),
            "batch_generator_state": batch_generator.get_state(),
            "seenclasses": seenclasses.detach().cpu().long().tolist(),
            "unseenclasses": unseenclasses.detach().cpu().long().tolist(),
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
        },
        log_dir / "checkpoint_last.pth",
    )

iters_per_epoch = len(train_labels) // int(config.batch_size)
if iters_per_epoch <= 0:
    raise ValueError("训练样本数小于 batch_size，无法完成一个训练 step。")

print_log(f"训练计划：{len(stages)} 段，共 {total_epochs} 个 epoch。")
print_log(
    f"共享训练缓存：CLS={tuple(train_cls.shape)}，patch={tuple(train_patches.shape)}；"
    f"本轮训练样本={len(train_labels)}。"
)

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
    for step in range(iters_per_epoch):
        optimizer.zero_grad(set_to_none=True)
        indices = torch.randperm(
            len(train_labels), generator=batch_generator
        )[: int(config.batch_size)]
        batch_labels = train_labels[indices].to(config.device)
        cache_indices = (
            indices
            if train_sample_positions is None
            else train_sample_positions[indices]
        )
        cls_batch = train_cls[cache_indices].to(config.device).float().unsqueeze(1)
        patch_batch = train_patches[cache_indices].to(config.device).float()
        features = torch.cat([cls_batch, patch_batch], dim=1)

        output = model(features, is_train=True)
        losses = model.compute_loss(dict(output, batch_label=batch_labels))
        losses["loss"].backward()
        optimizer.step()
        epoch_loss += float(losses["loss"].item())

        if (step + 1) % 20 == 0 or step + 1 == iters_per_epoch:
            print_log(
                f"epoch {epoch}/{total_epochs} step {step + 1}/{iters_per_epoch} "
                f"loss={losses['loss'].item():.4f}"
            )

    scheduler.step()
    print_log(
        f"epoch {epoch}: avg_loss={epoch_loss / iters_per_epoch:.4f}"
    )
    save_checkpoint(epoch)

if evaluation_index is None:
    seen_acc, unseen_acc, harmonic, zsl_acc = evaluate_cached_v5(
        model,
        config.device,
        evaluation_cache,
        seenclasses,
        unseenclasses,
    )
else:
    seen_acc, unseen_acc, harmonic, zsl_acc = evaluate_indexed_cached_v5(
        model,
        config.device,
        cls_features=train_cls,
        patches=train_patches,
        seen_positions=evaluation_index["seen_positions"],
        seen_labels=evaluation_index["seen_labels"],
        unseen_positions=evaluation_index["unseen_positions"],
        unseen_labels=evaluation_index["unseen_labels"],
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
    )
evaluation_protocol = (
    "test_once_after_training"
    if config.evaluation_split == "test"
    else "class_disjoint_validation_once_after_training"
)
reported_metrics = {
    "U": unseen_acc,
    "S": seen_acc,
    "H": harmonic,
    "ZS": zsl_acc,
    "epoch": total_epochs,
    "evaluation_protocol": evaluation_protocol,
    "evaluation_split": config.evaluation_split,
}
if validation_split is not None:
    reported_metrics["validation_split"] = {
        "pseudo_seen_classes": int(seenclasses.numel()),
        "pseudo_unseen_classes": int(unseenclasses.numel()),
        "seen_holdout_fraction": float(config.validation_seen_holdout_fraction),
        "split_seed": int(config.validation_split_seed),
        "train_images": int(len(train_labels)),
        "seen_validation_images": int(len(evaluation_index["seen_labels"])),
        "unseen_validation_images": int(len(evaluation_index["unseen_labels"])),
        "formal_test_cache_loaded": False,
        "large_patch_cache_copies": 0,
    }
prototype_diagnostics = model.prototype_relation_diagnostics()
if prototype_diagnostics is not None:
    reported_metrics["prototype_relation"] = prototype_diagnostics
torch.save(model.state_dict(), log_dir / "model_final.pth")
save_checkpoint(
    total_epochs,
    final_metrics=reported_metrics,
    test_was_evaluated=True,
)

print_log("训练完成。")
if prototype_diagnostics is not None:
    print_log(f"类别关系修正诊断：{prototype_diagnostics}")
print_log(
    f"最终 epoch={reported_metrics['epoch']}，U={reported_metrics['U'] * 100:.2f}%，"
    f"S={reported_metrics['S'] * 100:.2f}%，H={reported_metrics['H'] * 100:.2f}%，"
    f"ZS={reported_metrics['ZS'] * 100:.2f}%。"
)
(log_dir / "metrics.yaml").write_text(
    yaml.safe_dump(reported_metrics, allow_unicode=True, sort_keys=False),
    encoding="utf-8",
)
