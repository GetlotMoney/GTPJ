"""V5 方案 5：只推理的全局 top-5 局部证据重排入口。"""

from __future__ import annotations

import argparse
import importlib.util
import math
from numbers import Integral, Real
from pathlib import Path
import sys
from collections.abc import Mapping

import torch


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from model.MyModel import GTPJ  # noqa: E402
from tools import v5_evaluation  # noqa: E402
from tools.v5_cub_data import load_v5_cub_split  # noqa: E402
from tools.v5_topk_local_rerank import (  # noqa: E402
    diagnose_topk_local_rerank,
    topk_local_rerank,
)


TRAINER_PATH = EXPERIMENT_DIR / "train.py"
_TRAINER_SPEC = importlib.util.spec_from_file_location(
    "v5_local_evidence_train_for_rerank",
    TRAINER_PATH,
)
if _TRAINER_SPEC is None or _TRAINER_SPEC.loader is None:
    raise ImportError(f"无法加载训练入口：{TRAINER_PATH}")
TRAINER = importlib.util.module_from_spec(_TRAINER_SPEC)
_TRAINER_SPEC.loader.exec_module(TRAINER)

FIXED_K = 5
FIXED_RESIDUAL_CAP = 0.25


def build_parser():
    parser = argparse.ArgumentParser(
        description="读取已训练 checkpoint，在全局 top-5 内用局部证据做有界重排。",
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-run-commit", required=True)
    parser.add_argument("--k", type=int, default=FIXED_K)
    parser.add_argument("--residual-cap", type=float, default=FIXED_RESIDUAL_CAP)
    return parser


def validate_fixed_rerank_parameters(k, residual_cap):
    if isinstance(k, bool) or not isinstance(k, Integral) or int(k) != FIXED_K:
        raise ValueError("本实验固定 k=5，拒绝其他值。")
    if (
        isinstance(residual_cap, bool)
        or not isinstance(residual_cap, Real)
        or not math.isfinite(float(residual_cap))
        or float(residual_cap) != FIXED_RESIDUAL_CAP
    ):
        raise ValueError("本实验固定 residual_cap=0.25，拒绝其他值。")
    return FIXED_K, FIXED_RESIDUAL_CAP


def require_new_run_dir(run_dir):
    return TRAINER.require_new_run_dir(run_dir)


def _validated_class_axis(class_ids, class_count, device):
    if class_ids is None:
        return torch.arange(class_count, dtype=torch.long, device=device)
    axis = torch.as_tensor(class_ids)
    integer_types = {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }
    if axis.dim() != 1 or axis.dtype not in integer_types:
        raise ValueError("class_ids 必须是一维整数全局类别编号。")
    axis = axis.to(device=device, dtype=torch.long)
    if axis.numel() < FIXED_K:
        raise ValueError("重排类别轴至少需要 5 个类别。")
    if axis.unique().numel() != axis.numel():
        raise ValueError("class_ids 不能包含重复类别。")
    if ((axis < 0) | (axis >= class_count)).any():
        raise ValueError("class_ids 超出全局类别轴。")
    return axis


def rerank_on_class_axis(
    global_logits,
    local_logits,
    *,
    class_ids=None,
    k=FIXED_K,
    residual_cap=FIXED_RESIDUAL_CAP,
):
    """先选择允许的类别轴，再重排并映回全局类别编号；不接收标签。"""

    k, residual_cap = validate_fixed_rerank_parameters(k, residual_cap)
    if not isinstance(global_logits, torch.Tensor) or global_logits.dim() != 2:
        raise ValueError("global_logits 必须是 [B, C] Tensor。")
    axis = _validated_class_axis(
        class_ids,
        global_logits.size(1),
        global_logits.device,
    )
    axis_prediction = topk_local_rerank(
        global_logits.index_select(1, axis),
        local_logits.index_select(1, axis),
        k=k,
        residual_cap=residual_cap,
    )
    return axis.index_select(0, axis_prediction)


def _normalise_checkpoint_ids(value, name):
    try:
        tensor = torch.as_tensor(value)
    except (TypeError, ValueError) as error:
        raise TypeError(f"checkpoint {name} 不是有效类别列表。") from error
    if tensor.dim() != 1 or tensor.dtype not in {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }:
        raise TypeError(f"checkpoint {name} 必须是一维整数类别列表。")
    return tensor.cpu().long().tolist()


def validate_checkpoint_identity(
    checkpoint,
    *,
    expected_code_commit,
    expected_config_sha256,
    expected_experiment_id,
    seenclasses,
    unseenclasses,
):
    if not isinstance(checkpoint, Mapping):
        raise TypeError("checkpoint 必须是字典。")
    expected_scalars = {
        "code_commit": str(expected_code_commit),
        "config_sha256": str(expected_config_sha256),
        "experiment_id": str(expected_experiment_id),
    }
    for name, expected in expected_scalars.items():
        actual = checkpoint.get(name)
        if actual != expected:
            raise ValueError(
                f"checkpoint {name}={actual!r}，与本次期望 {expected!r} 不一致。"
            )
    expected_axes = {
        "seenclasses": torch.as_tensor(seenclasses).cpu().long().tolist(),
        "unseenclasses": torch.as_tensor(unseenclasses).cpu().long().tolist(),
    }
    for name, expected in expected_axes.items():
        actual = _normalise_checkpoint_ids(checkpoint.get(name), name)
        if actual != expected:
            raise ValueError(
                f"checkpoint {name}={actual!r}，与真实划分 {expected!r} 不一致。"
            )
    if not isinstance(checkpoint.get("model_state_dict"), Mapping):
        raise TypeError("checkpoint model_state_dict 必须是参数字典。")
    return checkpoint


def load_model_state_strict(model, checkpoint):
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    return model


def _inference_input_paths(data_root):
    root = Path(data_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"数据根目录不存在：{root}")
    paths = {
        "xlsa17_res101": root / "xlsa17/data/CUB/res101.mat",
        "xlsa17_att_splits": root / "xlsa17/data/CUB/att_splits.mat",
        "train_labels": root / "cache/CUB_train_labels.pt",
        "gpt55_sentences": root / "cache/CUB_gpt55_sentence_embeds.pt",
        **{
            f"test_{name}": path
            for name, path in v5_evaluation.v5_test_cache_paths(
                root / "cache"
            ).items()
        },
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("重排推理缺少真实输入：" + ", ".join(missing))
    return paths


def _predict_global_local(model, cls_features, patches, device, batch_size):
    global_parts = []
    local_parts = []
    model.eval()
    with torch.no_grad():
        for start in range(0, cls_features.size(0), batch_size):
            cls_batch = cls_features[start : start + batch_size].to(device).float()
            patch_batch = patches[start : start + batch_size].to(device).float()
            output = model(
                torch.cat([cls_batch.unsqueeze(1), patch_batch], dim=1),
                is_train=False,
            )
            for name in ("global_logits", "local_logits"):
                logits = output.get(name)
                if not isinstance(logits, torch.Tensor):
                    raise ValueError(f"模型没有输出 {name} Tensor。")
                TRAINER.require_finite_tensor(name, logits)
            global_parts.append(output["global_logits"].cpu())
            local_parts.append(output["local_logits"].cpu())
    return torch.cat(global_parts), torch.cat(local_parts)


def _local_axis_labels(labels, axis, class_count):
    mapping = torch.full((class_count,), -1, dtype=torch.long)
    mapping[axis.cpu().long()] = torch.arange(axis.numel(), dtype=torch.long)
    local = mapping[labels.cpu().long()]
    if (local < 0).any():
        raise ValueError("标签不在所选类别轴内。")
    return local


def _merge_diagnostics(first, first_size, second, second_size):
    total = first_size + second_size
    return {
        "prediction_changed": first["prediction_changed"]
        + second["prediction_changed"],
        "rescue": first["rescue"] + second["rescue"],
        "harm": first["harm"] + second["harm"],
        "topk_coverage": (
            first["topk_coverage"] * first_size
            + second["topk_coverage"] * second_size
        )
        / total,
    }


def evaluate_reranked_logits(
    seen_global,
    seen_local,
    seen_labels,
    unseen_global,
    unseen_local,
    unseen_labels,
    seenclasses,
    unseenclasses,
    *,
    k=FIXED_K,
    residual_cap=FIXED_RESIDUAL_CAP,
):
    k, residual_cap = validate_fixed_rerank_parameters(k, residual_cap)
    class_count = seen_global.size(1)
    if unseen_global.size(1) != class_count:
        raise ValueError("seen/unseen logits 的全局类别轴不一致。")
    seenclasses = torch.as_tensor(seenclasses).cpu().long()
    unseenclasses = torch.as_tensor(unseenclasses).cpu().long()
    combined = torch.cat([seenclasses, unseenclasses]).sort().values
    if not torch.equal(combined, torch.arange(class_count)):
        raise ValueError("seen/unseen 类别必须完整覆盖全局类别轴。")

    seen_prediction = rerank_on_class_axis(
        seen_global, seen_local, k=k, residual_cap=residual_cap
    )
    unseen_prediction = rerank_on_class_axis(
        unseen_global, unseen_local, k=k, residual_cap=residual_cap
    )
    zsl_prediction = rerank_on_class_axis(
        unseen_global,
        unseen_local,
        class_ids=unseenclasses,
        k=k,
        residual_cap=residual_cap,
    )
    seen_accuracy = v5_evaluation._per_class_accuracy(
        seen_labels, seen_prediction, seenclasses
    )
    unseen_accuracy = v5_evaluation._per_class_accuracy(
        unseen_labels, unseen_prediction, unseenclasses
    )
    zsl_accuracy = v5_evaluation._per_class_accuracy(
        unseen_labels, zsl_prediction, unseenclasses
    )
    denominator = seen_accuracy + unseen_accuracy
    harmonic = (
        2.0 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    )

    seen_diag = diagnose_topk_local_rerank(
        seen_global, seen_local, seen_labels, k=k, residual_cap=residual_cap
    )
    unseen_diag = diagnose_topk_local_rerank(
        unseen_global, unseen_local, unseen_labels, k=k, residual_cap=residual_cap
    )
    unseen_axis_global = unseen_global.index_select(1, unseenclasses)
    unseen_axis_local = unseen_local.index_select(1, unseenclasses)
    zsl_diag = diagnose_topk_local_rerank(
        unseen_axis_global,
        unseen_axis_local,
        _local_axis_labels(unseen_labels, unseenclasses, class_count),
        k=k,
        residual_cap=residual_cap,
    )
    return {
        "metrics": {
            "U": unseen_accuracy,
            "S": seen_accuracy,
            "H": harmonic,
            "ZS": zsl_accuracy,
        },
        "diagnostics": _merge_diagnostics(
            seen_diag,
            int(seen_labels.numel()),
            unseen_diag,
            int(unseen_labels.numel()),
        ),
        "zs_diagnostics": zsl_diag,
    }


def run_rerank(
    config_path,
    data_root,
    checkpoint_path,
    run_dir,
    expected_run_commit,
    *,
    k=FIXED_K,
    residual_cap=FIXED_RESIDUAL_CAP,
):
    k, residual_cap = validate_fixed_rerank_parameters(k, residual_cap)
    config, config_values, resolved_config = TRAINER.load_config(config_path)
    output_dir = require_new_run_dir(run_dir)
    code_commit = TRAINER.require_expected_commit(ROOT, expected_run_commit)
    TRAINER.require_clean_git(ROOT)
    device = TRAINER.require_cuda_device(config.device)

    checkpoint_file = Path(checkpoint_path).resolve()
    if not checkpoint_file.is_file():
        raise FileNotFoundError(f"checkpoint 不存在：{checkpoint_file}")
    checkpoint = torch.load(checkpoint_file, map_location="cpu", weights_only=True)
    paths = _inference_input_paths(data_root)
    test_cache = v5_evaluation.load_v5_test_cache(Path(data_root).resolve() / "cache")
    train_labels = torch.load(
        paths["train_labels"], map_location="cpu", weights_only=True
    ).long()
    seenclasses, unseenclasses = load_v5_cub_split(
        paths["xlsa17_res101"],
        paths["xlsa17_att_splits"],
        train_labels,
        test_cache["seen_labels"],
        test_cache["unseen_labels"],
        "cpu",
    )
    config_hash = TRAINER.sha256_file(resolved_config)
    validate_checkpoint_identity(
        checkpoint,
        expected_code_commit=code_commit,
        expected_config_sha256=config_hash,
        expected_experiment_id=config.experiment_id,
        seenclasses=seenclasses,
        unseenclasses=unseenclasses,
    )
    sentences = TRAINER._load_sentences(
        paths["gpt55_sentences"],
        int(config.num_class),
        int(config.dim_f_clip),
        device,
    )
    text_embeds = sentences.mean(dim=1)
    model = GTPJ(
        config,
        seenclasses,
        unseenclasses,
        seen_text_embeds=text_embeds[seenclasses],
        unseen_text_embeds=text_embeds[unseenclasses],
        seen_sentence_embeds=sentences[seenclasses],
    ).to(device)
    load_model_state_strict(model, checkpoint)
    TRAINER.require_expected_commit(ROOT, expected_run_commit)
    TRAINER.require_clean_git(ROOT)

    output_dir.mkdir(parents=True, exist_ok=False)
    log = TRAINER.AtomicTrainingLog(output_dir / "training.log")
    metrics_path = output_dir / "metrics.json"
    payload = {
        "schema_version": "gtpj.v5_topk_local_rerank.metrics.v1",
        "status": "running",
        "experiment_id": config.experiment_id,
        "code_commit": code_commit,
        "config_sha256": config_hash,
        "checkpoint": str(checkpoint_file),
        "k": k,
        "residual_cap": residual_cap,
    }
    TRAINER.atomic_write_json(metrics_path, payload)
    log.write("这是方案 5 的只推理日志，不执行训练；文件名沿用 training.log。")
    log.write(f"checkpoint：{checkpoint_file}")
    log.write(f"run commit：{code_commit}；k={k}；residual_cap={residual_cap}")
    try:
        seen_global, seen_local = _predict_global_local(
            model,
            test_cache["seen_cls"],
            test_cache["seen_patches"],
            device,
            int(config.batch_size),
        )
        unseen_global, unseen_local = _predict_global_local(
            model,
            test_cache["unseen_cls"],
            test_cache["unseen_patches"],
            device,
            int(config.batch_size),
        )
        if seen_global.size(1) != 200 or unseen_global.size(1) != 200:
            raise ValueError("GZSL 重排必须使用完整 200 类全局轴。")
        result = evaluate_reranked_logits(
            seen_global,
            seen_local,
            test_cache["seen_labels"],
            unseen_global,
            unseen_local,
            test_cache["unseen_labels"],
            seenclasses,
            unseenclasses,
            k=k,
            residual_cap=residual_cap,
        )
        payload.update(result)
        payload["status"] = "completed"
        TRAINER.atomic_write_json(metrics_path, payload)
        metrics = result["metrics"]
        log.write(
            f"推理完成：U={metrics['U'] * 100:.2f}%；S={metrics['S'] * 100:.2f}%；"
            f"H={metrics['H'] * 100:.2f}%；ZS={metrics['ZS'] * 100:.2f}%"
        )
        log.write("只生成 training.log 和 metrics.json；没有生成或覆盖 checkpoint。")
        return result
    except Exception as error:
        payload["status"] = "failed"
        payload["error"] = f"{type(error).__name__}: {error}"
        TRAINER.atomic_write_json(metrics_path, payload)
        log.write(payload["error"])
        raise


def main(argv=None):
    args = build_parser().parse_args(argv)
    run_rerank(
        args.config,
        args.data_root,
        args.checkpoint,
        args.run_dir,
        args.expected_run_commit,
        k=args.k,
        residual_cap=args.residual_cap,
    )


if __name__ == "__main__":
    main()
