"""V5 的全局候选内局部证据重排工具。"""

import math
from numbers import Integral, Real

import torch


def _validate_rerank_inputs(global_logits, local_logits, k, residual_cap):
    if not isinstance(global_logits, torch.Tensor) or not isinstance(
        local_logits, torch.Tensor
    ):
        raise ValueError("global_logits 和 local_logits 必须是 Tensor。")
    if (
        global_logits.dim() != 2
        or local_logits.dim() != 2
        or global_logits.shape != local_logits.shape
        or global_logits.size(0) == 0
        or global_logits.size(1) == 0
    ):
        raise ValueError(
            "global_logits 和 local_logits 的形状必须相同且为非空 [B, C]。"
        )
    if global_logits.device != local_logits.device:
        raise ValueError("global_logits 和 local_logits 必须位于同一设备。")
    if (
        not global_logits.is_floating_point()
        or not local_logits.is_floating_point()
    ):
        raise ValueError("global_logits 和 local_logits 必须是浮点 Tensor。")
    if not torch.isfinite(global_logits).all() or not torch.isfinite(
        local_logits
    ).all():
        raise ValueError("global_logits 和 local_logits 必须全部是有限数。")
    if isinstance(k, bool) or not isinstance(k, Integral):
        raise ValueError("k 必须是整数。")
    k = int(k)
    if not 1 <= k <= global_logits.size(1):
        raise ValueError(f"k 必须位于 [1, {global_logits.size(1)}]。")
    if (
        isinstance(residual_cap, bool)
        or not isinstance(residual_cap, Real)
        or not math.isfinite(float(residual_cap))
        or float(residual_cap) < 0.0
    ):
        raise ValueError("residual_cap 必须是大于或等于 0 的有限实数。")
    return k, float(residual_cap)


def topk_local_rerank(global_logits, local_logits, *, k, residual_cap):
    """在全局 top-k 候选内加入有界局部残差，并返回 ``[B]`` 类别。

    函数不接收标签。局部分支只调整全局已经选出的候选，因此候选集外的
    类别即使拥有很高的局部分数，也不可能成为最终预测。
    """

    k, residual_cap = _validate_rerank_inputs(
        global_logits,
        local_logits,
        k,
        residual_cap,
    )
    global_prediction = global_logits.argmax(dim=1)
    if k == 1 or residual_cap == 0.0:
        return global_prediction

    candidate_global, candidate_indices = torch.topk(
        global_logits,
        k=k,
        dim=1,
        largest=True,
        sorted=True,
    )
    candidate_local = torch.gather(local_logits, 1, candidate_indices)
    centered_local = candidate_local - candidate_local.mean(dim=1, keepdim=True)
    max_abs = centered_local.abs().amax(dim=1, keepdim=True)
    normalized_local = torch.where(
        max_abs > 0,
        centered_local / max_abs.clamp_min(torch.finfo(centered_local.dtype).tiny),
        torch.zeros_like(centered_local),
    )
    residual = residual_cap * torch.tanh(normalized_local)
    winner_within_candidates = (candidate_global + residual).argmax(dim=1)
    prediction = torch.gather(
        candidate_indices,
        1,
        winner_within_candidates.unsqueeze(1),
    ).squeeze(1)
    # 局部候选分数完全相同时，严格退回原始全局预测，避免平分时改判。
    return torch.where(max_abs.squeeze(1) == 0, global_prediction, prediction)


def diagnose_topk_local_rerank(
    global_logits,
    local_logits,
    labels,
    *,
    k,
    residual_cap,
):
    """批量统计重排改判、救回、误伤和全局 top-k 真值覆盖率。

    ``prediction_changed``、``rescue``、``harm`` 是样本数；
    ``topk_coverage`` 是 ``[0, 1]`` 比例。标签只在预测完成后用于对照。
    """

    k, residual_cap = _validate_rerank_inputs(
        global_logits,
        local_logits,
        k,
        residual_cap,
    )
    global_prediction = global_logits.argmax(dim=1)
    reranked_prediction = topk_local_rerank(
        global_logits,
        local_logits,
        k=k,
        residual_cap=residual_cap,
    )
    candidate_indices = torch.topk(
        global_logits,
        k=k,
        dim=1,
        largest=True,
        sorted=True,
    ).indices

    if not isinstance(labels, torch.Tensor):
        raise ValueError("labels 必须是 Tensor。")
    integer_dtypes = {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }
    if (
        labels.dim() != 1
        or labels.numel() != global_logits.size(0)
        or labels.dtype not in integer_dtypes
    ):
        raise ValueError("labels 必须是一维整数 Tensor，长度等于批量大小。")
    labels_on_device = labels.to(device=global_logits.device, dtype=torch.long)
    if ((labels_on_device < 0) | (labels_on_device >= global_logits.size(1))).any():
        raise ValueError("labels 必须位于有效类别编号范围内。")

    changed = reranked_prediction != global_prediction
    global_correct = global_prediction == labels_on_device
    reranked_correct = reranked_prediction == labels_on_device
    covered = (candidate_indices == labels_on_device.unsqueeze(1)).any(dim=1)
    batch_size = labels_on_device.numel()
    return {
        "prediction_changed": int(changed.sum().item()),
        "rescue": int((~global_correct & reranked_correct).sum().item()),
        "harm": int((global_correct & ~reranked_correct).sum().item()),
        "topk_coverage": int(covered.sum().item()) / batch_size,
    }
