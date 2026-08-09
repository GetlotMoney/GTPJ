"""只读取 V5 正式训练需要的 CUB/xlsa17 划分信息。"""

from pathlib import Path

import scipy.io as sio
import torch


def load_v5_cub_split(
    res101_path,
    split_path,
    train_labels,
    test_seen_labels,
    test_unseen_labels,
    device,
):
    res101 = sio.loadmat(Path(res101_path))
    splits = sio.loadmat(Path(split_path))
    labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    train_indices = torch.from_numpy(splits["trainval_loc"].squeeze() - 1).long()
    seen_indices = torch.from_numpy(splits["test_seen_loc"].squeeze() - 1).long()
    unseen_indices = torch.from_numpy(splits["test_unseen_loc"].squeeze() - 1).long()

    expected = {
        "train": labels[train_indices],
        "test_seen": labels[seen_indices],
        "test_unseen": labels[unseen_indices],
    }
    actual = {
        "train": train_labels.detach().cpu().long(),
        "test_seen": test_seen_labels.detach().cpu().long(),
        "test_unseen": test_unseen_labels.detach().cpu().long(),
    }
    for name in expected:
        if not torch.equal(expected[name], actual[name]):
            raise ValueError(f"{name} 缓存标签与 xlsa17 划分不一致。")

    seenclasses = torch.unique(expected["train"], sorted=True)
    test_seenclasses = torch.unique(expected["test_seen"], sorted=True)
    unseenclasses = torch.unique(expected["test_unseen"], sorted=True)
    if not torch.equal(seenclasses, test_seenclasses):
        raise ValueError("训练 seen 类与 test_seen 类集合不一致。")
    return seenclasses.to(device), unseenclasses.to(device)


def build_v5_class_disjoint_validation_split(
    res101_path,
    split_path,
    train_cache_labels,
    *,
    holdout_fraction=0.2,
    split_seed=20260810,
):
    """从 xlsa17 的 train/val 类划分构造不接触正式测试集的 GZSL 验证集。"""
    holdout_fraction = float(holdout_fraction)
    if not 0.0 < holdout_fraction < 1.0:
        raise ValueError("holdout_fraction 必须位于 (0, 1)。")

    res101 = sio.loadmat(Path(res101_path))
    splits = sio.loadmat(Path(split_path))
    required = {"trainval_loc", "train_loc", "val_loc"}
    missing = sorted(required - set(splits))
    if missing:
        raise ValueError(f"xlsa17 验证划分缺少字段：{missing}。")

    labels = torch.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    trainval_indices = torch.from_numpy(
        splits["trainval_loc"].squeeze() - 1
    ).long()
    train_indices = torch.from_numpy(splits["train_loc"].squeeze() - 1).long()
    val_indices = torch.from_numpy(splits["val_loc"].squeeze() - 1).long()
    cache_labels = torch.as_tensor(train_cache_labels).detach().cpu().long()
    if not torch.equal(cache_labels, labels[trainval_indices]):
        raise ValueError("训练缓存标签与 xlsa17 trainval_loc 顺序不一致。")

    cache_position = torch.full((labels.numel(),), -1, dtype=torch.long)
    cache_position[trainval_indices] = torch.arange(trainval_indices.numel())
    train_positions_all = cache_position[train_indices]
    unseen_val_positions = cache_position[val_indices]
    if (train_positions_all < 0).any() or (unseen_val_positions < 0).any():
        raise ValueError("train_loc/val_loc 必须都包含在 trainval_loc 中。")

    original_seenclasses = torch.unique(labels[train_indices], sorted=True)
    original_unseenclasses = torch.unique(labels[val_indices], sorted=True)
    if torch.isin(original_seenclasses, original_unseenclasses).any():
        raise ValueError("xlsa17 train_loc 与 val_loc 的类别必须完全不重叠。")

    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(split_seed))
    train_parts = []
    seen_val_parts = []
    for class_id in original_seenclasses:
        class_positions = train_positions_all[
            cache_labels[train_positions_all] == class_id
        ]
        if class_positions.numel() < 2:
            raise ValueError(f"pseudo-seen 类别 {int(class_id)} 少于 2 个样本。")
        order = torch.randperm(class_positions.numel(), generator=generator)
        holdout_count = int(round(class_positions.numel() * holdout_fraction))
        holdout_count = min(
            class_positions.numel() - 1,
            max(1, holdout_count),
        )
        seen_val_parts.append(class_positions[order[:holdout_count]])
        train_parts.append(class_positions[order[holdout_count:]])

    train_positions = torch.cat(train_parts).sort().values
    seen_val_positions = torch.cat(seen_val_parts).sort().values
    unseen_val_positions = unseen_val_positions.sort().values
    if torch.isin(train_positions, seen_val_positions).any():
        raise ValueError("pseudo-seen 训练图片与留出验证图片发生重叠。")
    if torch.isin(
        torch.cat([train_positions, seen_val_positions]), unseen_val_positions
    ).any():
        raise ValueError("pseudo-seen 与 pseudo-unseen 图片发生重叠。")

    original_class_order = torch.cat(
        [original_seenclasses, original_unseenclasses]
    )
    original_to_local = torch.full(
        (int(labels.max().item()) + 1,), -1, dtype=torch.long
    )
    original_to_local[original_class_order] = torch.arange(
        original_class_order.numel()
    )
    seenclasses = torch.arange(original_seenclasses.numel(), dtype=torch.long)
    unseenclasses = torch.arange(
        original_seenclasses.numel(), original_class_order.numel(), dtype=torch.long
    )

    def remap(positions):
        mapped = original_to_local[cache_labels[positions]]
        if (mapped < 0).any():
            raise ValueError("验证划分出现未登记类别。")
        return mapped

    return {
        "train_positions": train_positions,
        "seen_val_positions": seen_val_positions,
        "unseen_val_positions": unseen_val_positions,
        "train_labels": remap(train_positions),
        "seen_val_labels": remap(seen_val_positions),
        "unseen_val_labels": remap(unseen_val_positions),
        "seenclasses": seenclasses,
        "unseenclasses": unseenclasses,
        "original_seenclasses": original_seenclasses,
        "original_unseenclasses": original_unseenclasses,
        "original_class_order": original_class_order,
        "holdout_fraction": holdout_fraction,
        "split_seed": int(split_seed),
    }
