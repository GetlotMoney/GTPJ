"""V5 干净母版的 CUB 训练入口。

这份入口只接受正式 V5 配置、真实 CLS/局部块缓存和 GPT-5.5 句子缓存。
它不根据机器上“碰巧存在什么文件”切换算法路线。
"""

import argparse
from datetime import datetime
import hashlib
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.optim as optim
import yaml

from model.MyModel import GTPJ
from tools.dataset import CUBDataLoader
from tools.reproducibility import configure_reproducibility
from tools.v5_evaluation import eval_zs_gzsl


MODEL_TEMPLATE_ID = "model/v5-template-v1"
CACHE_DIR = Path("./data/cache")
TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"
TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"
TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"
GPT55_SENTENCE_PATH = CACHE_DIR / "CUB_gpt55_sentence_embeds.pt"

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


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_dir = Path("./train_log/CUB")
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
print_log("V5 干净母版 | CUB GZSL 训练")
print_log(f"母版：{MODEL_TEMPLATE_ID}")
print_log(f"配置：{config_path}")
print_log(f"配置 SHA-256：{_sha256(config_path)}")
print_log(f"随机种子：{seed}")
print_log(f"局部分支融合：global + {config.local_weight} * local")
print_log(f"PyTorch/CUDA：{repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
print_log("=" * 60)

dataloader = CUBDataLoader(".", config.device, is_balance=False)
train_cls, train_patches, train_labels = _load_training_cache(int(config.dim_f_clip))
sentence_embeds = _load_gpt55_sentences(
    int(config.num_class), int(config.dim_f_clip), config.device
)
text_embeds = sentence_embeds.mean(dim=1)

model = GTPJ(
    config,
    dataloader.seenclasses,
    dataloader.unseenclasses,
    seen_text_embeds=text_embeds[dataloader.seenclasses],
    unseen_text_embeds=text_embeds[dataloader.unseenclasses],
    seen_sentence_embeds=sentence_embeds[dataloader.seenclasses],
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

if args.resume_from is not None:
    resume_path = args.resume_from.resolve()
    if not resume_path.is_file():
        raise FileNotFoundError(f"续训 checkpoint 不存在：{resume_path}")
    checkpoint = torch.load(resume_path, map_location=config.device, weights_only=False)
    required = {
        "template_id",
        "epoch",
        "stage_index",
        "best_H",
        "best_metrics",
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
    print_log(f"从 epoch {start_epoch} 继续；历史最佳 H={best_h * 100:.2f}%。")

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
    seen_acc, unseen_acc, harmonic, zsl_acc = eval_zs_gzsl(
        dataloader, None, model, config.device
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
                "epoch": epoch,
                "stage_index": active_stage,
                "best_H": best_h,
                "best_metrics": best_metrics,
                "config": config_values,
                "config_sha256": _sha256(config_path),
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
