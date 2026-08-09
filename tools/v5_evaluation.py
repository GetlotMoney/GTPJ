"""V5 母版的严格缓存评估入口。

正式评估必须同时使用真实 CLS 和 576 个局部图像块；缺文件时直接停止，
不得复制 CLS 冒充局部特征，也不得悄悄切换到在线提取路线。
"""

import math
from pathlib import Path

import torch


_CACHE_FILES = {
    "seen_cls": "CUB_test_seen_features.pt",
    "seen_labels": "CUB_test_seen_labels.pt",
    "seen_patches": "CUB_test_seen_patch_features.pt",
    "unseen_cls": "CUB_test_unseen_features.pt",
    "unseen_labels": "CUB_test_unseen_labels.pt",
    "unseen_patches": "CUB_test_unseen_patch_features.pt",
}


def v5_test_cache_paths(cache_dir="./data/cache"):
    root = Path(cache_dir).resolve()
    return {name: root / filename for name, filename in _CACHE_FILES.items()}


def load_v5_test_cache(cache_dir="./data/cache"):
    paths = v5_test_cache_paths(cache_dir)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "V5 正式评估缺少真实 CLS/局部块缓存：" + ", ".join(missing)
        )
    cache = {
        name: torch.load(path, map_location="cpu", weights_only=True)
        for name, path in paths.items()
    }
    _validate_cache_split(
        "seen", cache["seen_cls"], cache["seen_patches"], cache["seen_labels"]
    )
    _validate_cache_split(
        "unseen",
        cache["unseen_cls"],
        cache["unseen_patches"],
        cache["unseen_labels"],
    )
    return cache


def _validate_cache_split(name, cls_features, patches, labels):
    if cls_features.dim() != 2:
        raise ValueError(f"{name} CLS 缓存必须是 [N, D]，实际为 {tuple(cls_features.shape)}。")
    if patches.dim() != 3 or patches.size(1) != 576:
        raise ValueError(
            f"{name} 局部块缓存必须是 [N, 576, D]，实际为 {tuple(patches.shape)}。"
        )
    if labels.dim() != 1:
        raise ValueError(f"{name} 标签缓存必须是 [N]，实际为 {tuple(labels.shape)}。")
    if cls_features.size(0) != patches.size(0) or labels.size(0) != patches.size(0):
        raise ValueError(f"{name} 的 CLS、局部块和标签数量不一致。")
    if cls_features.size(1) != patches.size(2):
        raise ValueError(f"{name} 的 CLS 与局部块特征维度不一致。")


def _predict(model, cls_features, patches, device, batch_size):
    predictions = []
    model.eval()
    with torch.no_grad():
        for start in range(0, cls_features.size(0), batch_size):
            cls_batch = cls_features[start : start + batch_size].to(device).float()
            patch_batch = patches[start : start + batch_size].to(device).float()
            features = torch.cat([cls_batch.unsqueeze(1), patch_batch], dim=1)
            logits = model(features, is_train=False)["clip_S_pp"]
            predictions.append(logits.cpu())
    return torch.cat(predictions, dim=0)


def _predict_indexed(
    model,
    cls_features,
    patches,
    positions,
    device,
    batch_size,
):
    """只为当前评估 batch 建立小张量，避免复制整份 5.8 GiB patch 缓存。"""
    positions = torch.as_tensor(positions, dtype=torch.long, device="cpu")
    predictions = []
    model.eval()
    with torch.no_grad():
        for start in range(0, positions.numel(), batch_size):
            batch_positions = positions[start : start + batch_size]
            cls_batch = cls_features.index_select(0, batch_positions).to(device).float()
            patch_batch = patches.index_select(0, batch_positions).to(device).float()
            features = torch.cat([cls_batch.unsqueeze(1), patch_batch], dim=1)
            logits = model(features, is_train=False)["clip_S_pp"]
            predictions.append(logits.cpu())
    return torch.cat(predictions, dim=0)


def _per_class_accuracy(labels, predictions, classes):
    values = []
    labels = labels.cpu().long()
    predictions = predictions.cpu().long()
    for class_id in classes.cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"评估缓存里缺少类别 {int(class_id)} 的样本。")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean().item())


def _validate_class_axis(model, seenclasses, unseenclasses):
    seenclasses = torch.as_tensor(seenclasses, dtype=torch.long, device="cpu")
    unseenclasses = torch.as_tensor(unseenclasses, dtype=torch.long, device="cpu")
    if seenclasses.dim() != 1 or unseenclasses.dim() != 1:
        raise ValueError("seenclasses 和 unseenclasses 必须是一维全局类别编号。")
    if seenclasses.unique().numel() != seenclasses.numel():
        raise ValueError("seenclasses 含有重复类别。")
    if unseenclasses.unique().numel() != unseenclasses.numel():
        raise ValueError("unseenclasses 含有重复类别。")
    if torch.isin(seenclasses, unseenclasses).any():
        raise ValueError("seenclasses 与 unseenclasses 不能重叠。")
    expected_classes = getattr(model, "nclass", None)
    if expected_classes is not None:
        combined = torch.cat([seenclasses, unseenclasses]).sort().values
        expected = torch.arange(int(expected_classes), dtype=torch.long)
        if not torch.equal(combined.cpu(), expected):
            raise ValueError("seen/unseen 类别没有完整覆盖模型的全局类别轴。")
    if hasattr(model, "seenclass") and not torch.equal(
        model.seenclass.detach().cpu().long(), seenclasses.cpu()
    ):
        raise ValueError("评估 seenclasses 顺序与模型不一致。")
    if hasattr(model, "unseenclass") and not torch.equal(
        model.unseenclass.detach().cpu().long(), unseenclasses.cpu()
    ):
        raise ValueError("评估 unseenclasses 顺序与模型不一致。")
    return seenclasses, unseenclasses


def _metrics_from_logits(
    *,
    seen_logits,
    unseen_logits,
    seen_labels,
    unseen_labels,
    seenclasses,
    unseenclasses,
    calibrated_stacking_gamma,
):
    calibrated_seen_logits = apply_calibrated_stacking(
        seen_logits, seenclasses, calibrated_stacking_gamma
    )
    calibrated_unseen_logits = apply_calibrated_stacking(
        unseen_logits, seenclasses, calibrated_stacking_gamma
    )
    seen_prediction = calibrated_seen_logits.argmax(dim=1)
    unseen_prediction = calibrated_unseen_logits.argmax(dim=1)
    unseen_only_prediction = unseenclasses[
        unseen_logits[:, unseenclasses].argmax(dim=1)
    ]

    seen_accuracy = _per_class_accuracy(
        seen_labels, seen_prediction, seenclasses
    )
    unseen_accuracy = _per_class_accuracy(
        unseen_labels, unseen_prediction, unseenclasses
    )
    zsl_accuracy = _per_class_accuracy(
        unseen_labels, unseen_only_prediction, unseenclasses
    )
    denominator = seen_accuracy + unseen_accuracy
    harmonic = 2.0 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    return seen_accuracy, unseen_accuracy, harmonic, zsl_accuracy


def apply_calibrated_stacking(logits, seenclasses, gamma):
    """推理期统一降低已见类分数，不改原始 logits。"""
    if logits.dim() != 2 or not logits.is_floating_point():
        raise ValueError("logits must be a floating tensor with shape [N, C].")
    seenclasses = torch.as_tensor(
        seenclasses, dtype=torch.long, device=logits.device
    )
    if seenclasses.dim() != 1 or seenclasses.unique().numel() != seenclasses.numel():
        raise ValueError("seenclasses must be one-dimensional and unique.")
    if seenclasses.numel() and (
        int(seenclasses.min()) < 0 or int(seenclasses.max()) >= logits.size(1)
    ):
        raise ValueError("seenclasses contains an out-of-range class id.")
    gamma = float(gamma)
    if not math.isfinite(gamma) or gamma < 0:
        raise ValueError("gamma must be a finite non-negative number.")

    adjusted = logits.clone()
    adjusted[:, seenclasses] = adjusted[:, seenclasses] - gamma
    return adjusted


def select_calibrated_stacking_gamma(
    *,
    split_name,
    seen_logits,
    seen_labels,
    unseen_logits,
    unseen_labels,
    seenclasses,
    unseenclasses,
    gamma_candidates,
):
    """只用类不重叠的验证划分选择使 H 最大的 gamma。"""
    if split_name != "validation":
        raise ValueError("gamma selection only accepts a validation split.")
    seenclasses = torch.as_tensor(seenclasses, dtype=torch.long)
    unseenclasses = torch.as_tensor(unseenclasses, dtype=torch.long)
    seen_labels = torch.as_tensor(seen_labels, dtype=torch.long)
    unseen_labels = torch.as_tensor(unseen_labels, dtype=torch.long)
    if seen_logits.dim() != 2 or unseen_logits.dim() != 2:
        raise ValueError("validation logits must have shape [N, C].")
    if seen_logits.size(1) != unseen_logits.size(1):
        raise ValueError("seen and unseen validation logits must share class columns.")
    if len(seen_labels) != len(seen_logits) or len(unseen_labels) != len(unseen_logits):
        raise ValueError("validation labels and logits have different sample counts.")
    candidates = sorted({float(value) for value in gamma_candidates})
    if not candidates:
        raise ValueError("gamma_candidates must not be empty.")

    rows = []
    for gamma in candidates:
        seen_prediction = apply_calibrated_stacking(
            seen_logits, seenclasses, gamma
        ).argmax(dim=1)
        unseen_prediction = apply_calibrated_stacking(
            unseen_logits, seenclasses, gamma
        ).argmax(dim=1)
        seen_accuracy = _per_class_accuracy(
            seen_labels, seen_prediction, seenclasses
        )
        unseen_accuracy = _per_class_accuracy(
            unseen_labels, unseen_prediction, unseenclasses
        )
        denominator = seen_accuracy + unseen_accuracy
        harmonic = (
            2.0 * seen_accuracy * unseen_accuracy / denominator
            if denominator
            else 0.0
        )
        rows.append(
            {"gamma": gamma, "S": seen_accuracy, "U": unseen_accuracy, "H": harmonic}
        )

    best = min(rows, key=lambda row: (-row["H"], row["gamma"]))
    return {**best, "candidates": rows, "selection_split": "validation"}


def evaluate_cached_v5(
    model,
    device,
    cache,
    seenclasses,
    unseenclasses,
    batch_size=64,
    calibrated_stacking_gamma=0.0,
):
    # `_predict` deliberately returns CPU logits, so keep the whole metric
    # boundary (class ids, labels and predictions) on CPU as well.
    seenclasses, unseenclasses = _validate_class_axis(
        model, seenclasses, unseenclasses
    )
    _validate_cache_split(
        "seen", cache["seen_cls"], cache["seen_patches"], cache["seen_labels"]
    )
    _validate_cache_split(
        "unseen",
        cache["unseen_cls"],
        cache["unseen_patches"],
        cache["unseen_labels"],
    )
    seen_logits = _predict(
        model, cache["seen_cls"], cache["seen_patches"], device, batch_size
    )
    unseen_logits = _predict(
        model, cache["unseen_cls"], cache["unseen_patches"], device, batch_size
    )

    return _metrics_from_logits(
        seen_logits=seen_logits,
        unseen_logits=unseen_logits,
        seen_labels=cache["seen_labels"],
        unseen_labels=cache["unseen_labels"],
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
        calibrated_stacking_gamma=calibrated_stacking_gamma,
    )


def evaluate_indexed_cached_v5(
    model,
    device,
    *,
    cls_features,
    patches,
    seen_positions,
    seen_labels,
    unseen_positions,
    unseen_labels,
    seenclasses,
    unseenclasses,
    batch_size=64,
    calibrated_stacking_gamma=0.0,
):
    """在一份共享缓存上按位置分批评估，避免生成三份大 patch 副本。"""
    if cls_features.dim() != 2:
        raise ValueError("共享 CLS 缓存必须是 [N, D]。")
    if patches.dim() != 3 or patches.size(1) != 576:
        raise ValueError("共享局部块缓存必须是 [N, 576, D]。")
    if cls_features.size(0) != patches.size(0):
        raise ValueError("共享 CLS 与局部块缓存样本数不一致。")
    if cls_features.size(1) != patches.size(2):
        raise ValueError("共享 CLS 与局部块特征维度不一致。")

    seen_positions = torch.as_tensor(seen_positions, dtype=torch.long, device="cpu")
    unseen_positions = torch.as_tensor(
        unseen_positions, dtype=torch.long, device="cpu"
    )
    seen_labels = torch.as_tensor(seen_labels, dtype=torch.long, device="cpu")
    unseen_labels = torch.as_tensor(unseen_labels, dtype=torch.long, device="cpu")
    if seen_positions.dim() != 1 or unseen_positions.dim() != 1:
        raise ValueError("验证位置必须是一维索引。")
    if seen_positions.numel() != seen_labels.numel():
        raise ValueError("seen 验证位置与标签数量不一致。")
    if unseen_positions.numel() != unseen_labels.numel():
        raise ValueError("unseen 验证位置与标签数量不一致。")
    all_positions = torch.cat([seen_positions, unseen_positions])
    if all_positions.numel() == 0 or (
        int(all_positions.min()) < 0
        or int(all_positions.max()) >= cls_features.size(0)
    ):
        raise ValueError("验证位置超出共享缓存范围。")
    if torch.isin(seen_positions, unseen_positions).any():
        raise ValueError("seen/unseen 验证位置不能重叠。")

    seenclasses, unseenclasses = _validate_class_axis(
        model, seenclasses, unseenclasses
    )
    seen_logits = _predict_indexed(
        model,
        cls_features,
        patches,
        seen_positions,
        device,
        batch_size,
    )
    unseen_logits = _predict_indexed(
        model,
        cls_features,
        patches,
        unseen_positions,
        device,
        batch_size,
    )
    return _metrics_from_logits(
        seen_logits=seen_logits,
        unseen_logits=unseen_logits,
        seen_labels=seen_labels,
        unseen_labels=unseen_labels,
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
        calibrated_stacking_gamma=calibrated_stacking_gamma,
    )
