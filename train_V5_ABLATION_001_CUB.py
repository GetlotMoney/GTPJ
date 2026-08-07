"""V5-ABLATION-001 全局分支的 CUB 训练入口。

这份入口只接受本实验配置、真实 CLS/局部块缓存和 GPT-5.5 句子缓存。
模型保留原输入接口，但只读取 CLS；局部块只用于保证数据入口完全一致。
它不根据机器上“碰巧存在什么文件”切换算法路线。
"""

import argparse
from datetime import datetime
from pathlib import Path
import subprocess
from types import SimpleNamespace

import torch
import torch.optim as optim
import yaml

MODEL_TEMPLATE_ID = "V5-ABLATION-001-global-only@model/v5-template-v1"

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
    "lambda_topo_pearson",
    "icsa_ratio",
    "icsa_hidden",
    "lr_stages",
}


def _parse_args():
    parser = argparse.ArgumentParser(
        description="训练 V5-ABLATION-001 的全局分支版本。",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--config",
        default=(
            "./experiments/v5/ablation/ABLATION-001_local_branch_effect/"
            "configs/RUN-004.yaml"
        ),
        help="正式母版或实验副本中的 config.yaml。",
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--train-log-root", type=Path, required=True)
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
    if values["text_source"] != "gpt55":
        raise ValueError("V5 干净母版只接受 text_source='gpt55'。")
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
        ["git", "status", "--porcelain", "--untracked-files=no"],
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
if not args.data_root.is_dir() or not args.train_log_root.is_dir():
    raise FileNotFoundError("无局部组训练缺少已绑定的数据或结果根目录。")
CACHE_DIR = args.data_root / "cache"
TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"
TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"
TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"
GPT55_SENTENCE_PATH = CACHE_DIR / "CUB_gpt55_sentence_embeds.pt"
DATA_RES101_PATH = args.data_root / "xlsa17/data/CUB/res101.mat"
DATA_SPLIT_PATH = args.data_root / "xlsa17/data/CUB/att_splits.mat"
config, config_values, config_path = _load_config(args.config)
_require_clean_code_tree()
code_commit = _current_code_commit()

# 必须先确认工作树完全干净，再加载任何本地模型或工具代码。
from model.V5GlobalOnly import GTPJ
from tools.reproducibility import configure_reproducibility
from tools.v5_cub_data import load_v5_cub_split
from tools.v5_runtime import (
    capture_rng_state,
    input_fingerprints,
    input_record,
    sha256_file,
    validate_stable_input_records,
)
from tools.v5_evaluation import (
    evaluate_cached_v5,
    load_v5_test_cache,
    v5_test_cache_paths,
)
config_hash = sha256_file(config_path)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = args.train_log_root / "CUB"
log_dir.mkdir(parents=True, exist_ok=True)
log_path = log_dir / f"training_log_CUB_{current_time}.txt"


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
print_log("V5-ABLATION-001 | CUB GZSL 全局分支训练")
print_log(f"实验代码身份：{MODEL_TEMPLATE_ID}")
print_log(f"配置：{config_path}")
print_log(f"配置 SHA-256：{config_hash}")
print_log(f"代码 commit：{code_commit}")
print_log(f"随机种子：{seed}")
print_log("评分路径：只使用 CLS 与 PSE/ICSA 文本原型的全局余弦分数")
print_log("局部块影响：输入接口保留，但模型不读取 576 个局部块")
print_log(f"PyTorch/CUDA：{repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
print_log("=" * 60)

input_paths = {
    "xlsa17_res101": DATA_RES101_PATH,
    "xlsa17_att_splits": DATA_SPLIT_PATH,
    "train_cls": TRAIN_CLS_PATH,
    "train_patches": TRAIN_PATCH_PATH,
    "train_labels": TRAIN_LABEL_PATH,
    "gpt55_sentences": GPT55_SENTENCE_PATH,
    **{f"test_{name}": path for name, path in v5_test_cache_paths(CACHE_DIR).items()},
}
before_load_records = {name: input_record(path) for name, path in input_paths.items()}
train_cls, train_patches, train_labels = _load_training_cache(int(config.dim_f_clip))
sentence_embeds = _load_gpt55_sentences(
    int(config.num_class), int(config.dim_f_clip), config.device
)
test_cache = load_v5_test_cache(CACHE_DIR)
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
    "gpt55_sentences": sentence_embeds,
    **{f"test_{name}": tensor for name, tensor in test_cache.items()},
}
input_records = {
    name: input_record(path, input_tensors.get(name))
    for name, path in input_paths.items()
}
validate_stable_input_records(before_load_records, input_records)
run_input_fingerprints = input_fingerprints(input_records)
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
).to(config.device)

stages = config.lr_stages
boundaries = _stage_boundaries(stages)
total_epochs = boundaries[-1]
optimizer = optim.Adam(
    model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
)
scheduler = _new_scheduler(optimizer, stages[0])
active_stage = 0
start_epoch = 1
best_h = 0.0
best_metrics = {"U": 0.0, "S": 0.0, "H": 0.0, "ZS": 0.0, "epoch": 0}

iters_per_epoch = len(train_labels) // int(config.batch_size)
if iters_per_epoch <= 0:
    raise ValueError("训练样本数小于 batch_size，无法完成一个训练 step。")

print_log(f"训练计划：{len(stages)} 段，共 {total_epochs} 个 epoch。")
print_log(f"训练缓存：CLS={tuple(train_cls.shape)}，patch={tuple(train_patches.shape)}。")

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

        if (step + 1) % 20 == 0 or step + 1 == iters_per_epoch:
            print_log(
                f"epoch {epoch}/{total_epochs} step {step + 1}/{iters_per_epoch} "
                f"loss={losses['loss'].item():.4f}"
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
        best_metrics = {
            "U": unseen_acc,
            "S": seen_acc,
            "H": harmonic,
            "ZS": zsl_acc,
            "epoch": epoch,
        }
        score = int(round(harmonic * 10000))
        model_path = log_dir / f"best_model_CUB_{current_time}_H{score}.pth"
        checkpoint_path = log_dir / f"ckpt_full_CUB_{current_time}.pth"
        torch.save(model.state_dict(), model_path)
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
                "rng_state": capture_rng_state(),
                "seenclasses": seenclasses.detach().cpu().long().tolist(),
                "unseenclasses": unseenclasses.detach().cpu().long().tolist(),
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
            },
            checkpoint_path,
        )
        print_log(f"保存新最佳模型：{model_path}")

print_log("训练完成。")
print_log(
    f"最佳 epoch={best_metrics['epoch']}，U={best_metrics['U'] * 100:.2f}%，"
    f"S={best_metrics['S'] * 100:.2f}%，H={best_metrics['H'] * 100:.2f}%，"
    f"ZS={best_metrics['ZS'] * 100:.2f}%。"
)
