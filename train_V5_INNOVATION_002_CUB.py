"""V5-INNOVATION-002 的 CUB 专用训练入口。

训练与评估数学沿用冻结的 V5 母版；本入口只收紧实验身份、输入路径和
单个 RUN 目录内的固定证据文件。
"""

import argparse
import hashlib
import json
import math
import numbers
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace


EXPERIMENT_ID = "V5-INNOVATION-002"
MODEL_ID = "MODEL-V5-SCALE-FUSION-CANDIDATE-V1"
BASE_TEMPLATE_ID = "MODEL-V5-TEMPLATE-V1"
REPOSITORY_ROOT = Path(__file__).resolve().parent
MIN_AVAILABLE_MEMORY_BYTES = 14 * 1024**3

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
    "fusion_mode",
    "fusion_beta",
}


def _available_physical_memory_bytes():
    """Return currently available physical memory using only the standard library."""
    import os
    import sys

    if sys.platform == "win32":
        import ctypes

        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        query = ctypes.windll.kernel32.GlobalMemoryStatusEx
        query.argtypes = [ctypes.POINTER(MemoryStatusEx)]
        query.restype = ctypes.c_int
        if not query(ctypes.byref(status)):
            raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed")
        return int(status.ullAvailPhys)

    available_pages = os.sysconf("SC_AVPHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    return int(available_pages) * int(page_size)


def _require_minimum_available_memory():
    try:
        available = _available_physical_memory_bytes()
    except Exception as exc:
        raise RuntimeError(
            "无法读取可用物理内存，正式训练按失败关闭，拒绝创建 RUN。"
        ) from exc
    if (
        isinstance(available, bool)
        or not isinstance(available, numbers.Integral)
        or available <= 0
    ):
        raise RuntimeError("可用物理内存读数无效，正式训练拒绝创建 RUN。")
    available = int(available)
    if available < MIN_AVAILABLE_MEMORY_BYTES:
        raise MemoryError(
            "正式训练至少需要 14 GiB 可用物理内存，"
            f"当前只有 {available / 1024**3:.2f} GiB；拒绝创建 RUN。"
        )
    return available


def _parse_args():
    parser = argparse.ArgumentParser(
        description="训练 V5-INNOVATION-002 的 CUB 尺度一致融合候选。",
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def _validate_lr_stages(stages):
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages 必须是非空列表。")
    allowed = {"lr", "epochs", "eta_min"}
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict) or set(stage) != allowed:
            actual = sorted(stage) if isinstance(stage, dict) else type(stage).__name__
            raise ValueError(
                f"lr_stages 第 {index} 段只允许 {sorted(allowed)}，实际为 {actual}。"
            )
        lr = stage["lr"]
        epochs = stage["epochs"]
        eta_min = stage["eta_min"]
        if (
            isinstance(lr, bool)
            or not isinstance(lr, numbers.Real)
            or not math.isfinite(lr)
            or lr <= 0
        ):
            raise ValueError(f"lr_stages 第 {index} 段的 lr 必须是有限正数。")
        if isinstance(epochs, bool) or not isinstance(epochs, int) or epochs <= 0:
            raise ValueError(f"lr_stages 第 {index} 段的 epochs 必须是正整数。")
        if (
            isinstance(eta_min, bool)
            or not isinstance(eta_min, numbers.Real)
            or not math.isfinite(eta_min)
            or eta_min < 0
        ):
            raise ValueError(f"lr_stages 第 {index} 段的 eta_min 必须是有限非负数。")


def _load_config(path):
    import yaml

    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    config_bytes = config_path.read_bytes()
    config_text = config_bytes.decode("utf-8")
    raw = yaml.safe_load(config_text)
    if not isinstance(raw, dict):
        raise ValueError("V5 配置顶层必须是字典。")
    values = {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }
    missing = sorted(V5_CONFIG_KEYS - set(values))
    extra = sorted(set(values) - V5_CONFIG_KEYS)
    if missing or extra:
        raise ValueError(f"V5-INNOVATION-002 配置字段不匹配；缺少={missing}，多出={extra}。")
    if values["dataset"] != "CUB":
        raise ValueError("V5-INNOVATION-002 只接受 dataset='CUB'。")
    if values["text_source"] != "gpt55":
        raise ValueError("V5-INNOVATION-002 只接受 text_source='gpt55'。")
    _validate_lr_stages(values["lr_stages"])
    return SimpleNamespace(**values), values, config_path, config_text, config_bytes


def _require_expected_repository():
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    repository_text = result.stdout.strip()
    if not repository_text:
        raise RuntimeError("Git 未返回仓库根目录，拒绝正式训练。")
    actual_root = Path(repository_text).resolve()
    if actual_root != REPOSITORY_ROOT:
        raise RuntimeError(
            f"Git 仓库身份不匹配：期望 {REPOSITORY_ROOT}，实际 {actual_root}。"
        )


def _require_clean_code_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        raise RuntimeError("正式训练要求 Git 工作树完全干净，包括未跟踪文件。")


def _current_code_commit():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _load_training_cache(expected_dim, cls_path, patch_path, label_path):
    import torch

    required = [cls_path, patch_path, label_path]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "V5 正式训练缺少真实 CLS/局部块缓存：" + ", ".join(missing)
        )
    cls_features = torch.load(cls_path, map_location="cpu", weights_only=True)
    patches = torch.load(patch_path, map_location="cpu", weights_only=True)
    labels = torch.load(label_path, map_location="cpu", weights_only=True).long()
    if cls_features.dim() != 2 or cls_features.size(1) != expected_dim:
        raise ValueError(f"训练 CLS 必须是 [N, {expected_dim}]，实际为 {tuple(cls_features.shape)}。")
    if patches.dim() != 3 or tuple(patches.shape[1:]) != (576, expected_dim):
        raise ValueError(
            f"训练局部块必须是 [N, 576, {expected_dim}]，实际为 {tuple(patches.shape)}。"
        )
    if labels.dim() != 1 or not (len(cls_features) == len(patches) == len(labels)):
        raise ValueError("训练 CLS、局部块和标签的样本数量或形状不一致。")
    return cls_features, patches, labels


def _load_gpt55_sentences(path, expected_classes, expected_dim):
    import torch

    if not path.is_file():
        raise FileNotFoundError("V5 正式训练缺少 GPT-5.5 句子缓存：" + str(path))
    sentences = torch.load(path, map_location="cpu", weights_only=True)
    if (
        sentences.dim() != 3
        or sentences.size(0) != expected_classes
        or sentences.size(2) != expected_dim
    ):
        raise ValueError(
            f"GPT-5.5 句子缓存必须是 [{expected_classes}, M, {expected_dim}]，"
            f"实际为 {tuple(sentences.shape)}。"
        )
    return sentences.float()


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
    import torch.optim as optim

    return optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=int(stage["epochs"]),
        eta_min=float(stage["eta_min"]),
    )


def _make_logger(log_path):
    def print_log(message):
        text = str(message)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(text + "\n")

    return print_log


def _write_json(path, payload):
    target = Path(path)
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(serialized + "\n")
        temporary_path = Path(stream.name)
    temporary_path.replace(target)


def _atomic_torch_save(payload, path):
    import torch

    target = Path(path)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as stream:
        temporary_path = Path(stream.name)
    torch.save(payload, temporary_path)
    temporary_path.replace(target)


def _require_finite_tensor(name, tensor):
    import torch

    if not torch.is_tensor(tensor):
        raise TypeError(f"{name} 必须是 tensor。")
    if not bool(torch.isfinite(tensor.detach()).all().item()):
        raise FloatingPointError(f"{name} 含 NaN 或 Inf。")
    return tensor


def _require_finite_metrics(metrics):
    for name in ("U", "S", "H", "ZS"):
        if name not in metrics:
            raise ValueError(f"指标缺少 {name}。")
        value = metrics[name]
        if (
            isinstance(value, bool)
            or not isinstance(value, numbers.Real)
            or not math.isfinite(value)
        ):
            raise FloatingPointError(f"指标 {name} 不是有限数值。")
    return metrics


def _require_finite_gradients(model):
    import torch

    names = []
    flags = []
    for name, parameter in model.named_parameters():
        gradient = parameter.grad
        if gradient is not None and gradient.numel() > 0:
            names.append(name)
            flags.append(torch.isfinite(gradient.detach()).all())
    if not flags or torch.stack(flags).all().item():
        return
    bad_names = [name for name, flag in zip(names, flags) if not bool(flag)]
    raise FloatingPointError(
        "grad 含 NaN 或 Inf：" + ", ".join(bad_names)
    )


def _evaluate_with_finite_logits(model, evaluator, *args):
    def require_finite_output(_module, _inputs, output):
        if not isinstance(output, dict) or "logits" not in output:
            raise ValueError("评估 forward 必须返回包含 logits 的字典。")
        _require_finite_tensor("evaluation logits", output["logits"])

    hook = model.register_forward_hook(require_finite_output)
    try:
        values = evaluator(model, *args)
        if not isinstance(values, (tuple, list)) or len(values) != 4:
            raise ValueError("评估函数必须返回 S/U/H/ZS 四项指标。")
        seen_acc, unseen_acc, harmonic, zsl_acc = values
        _require_finite_metrics(
            {"U": unseen_acc, "S": seen_acc, "H": harmonic, "ZS": zsl_acc}
        )
        return values
    finally:
        hook.remove()


def _actual_logit_scale(model):
    raw_scale = model.logit_scale.detach()
    _require_finite_tensor("raw logit_scale", raw_scale)
    actual_scale = raw_scale.exp().clamp(max=100.0)
    _require_finite_tensor("actual logit_scale", actual_scale)
    return float(actual_scale.cpu().item())


def _is_new_best(harmonic, best_h, best_epoch):
    return best_epoch == 0 or harmonic > best_h


def main():
    args = _parse_args()

    data_root = args.data_root.resolve()
    if not data_root.is_dir():
        raise FileNotFoundError(f"数据根目录不存在：{data_root}")
    CACHE_DIR = data_root / "cache"
    TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"
    TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"
    TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"
    GPT55_SENTENCE_PATH = CACHE_DIR / "CUB_gpt55_sentence_embeds.pt"
    DATA_RES101_PATH = data_root / "xlsa17/data/CUB/res101.mat"
    DATA_SPLIT_PATH = data_root / "xlsa17/data/CUB/att_splits.mat"

    config, values, config_path, config_text, config_bytes = _load_config(args.config)
    from tools.v5_innovation_002_runtime import (
        prepare_run_directory,
        validate_experiment_config,
    )

    validate_experiment_config(values)
    _require_expected_repository()
    _require_clean_code_tree()
    _require_minimum_available_memory()
    code_commit = _current_code_commit()
    run_dir = prepare_run_directory(args.run_dir, args.run_id)

    log_path = run_dir / "training.log"
    model_path = run_dir / "model_best.pth"
    checkpoint_path = run_dir / "checkpoint_last.pth"
    metrics_path = run_dir / "metrics.json"
    config_snapshot_path = run_dir / "config_snapshot.yaml"
    identity_path = run_dir / "run_identity.json"
    config_snapshot_path.write_bytes(config_bytes)

    # 只有参数、配置、数据根目录和干净工作树都通过后，才加载模型与数据工具。
    import torch
    import torch.optim as optim

    from model.MyModel import GTPJ
    from tools.reproducibility import configure_reproducibility
    from tools.v5_cub_data import load_v5_cub_split
    from tools.v5_evaluation import (
        evaluate_cached_v5,
        load_v5_test_cache,
        v5_test_cache_paths,
    )
    from tools.v5_runtime import (
        capture_rng_state,
        input_fingerprints,
        input_record,
        validate_stable_input_records,
    )

    config_hash = _sha256_bytes(config_bytes)
    seed = int(config.random_seed)
    print_log = _make_logger(log_path)
    identity = {
        "run_id": args.run_id,
        "experiment_id": EXPERIMENT_ID,
        "model_id": MODEL_ID,
        "base_template_id": BASE_TEMPLATE_ID,
        "code_commit": code_commit,
        "config_path": str(config_path),
        "config_sha256": config_hash,
        "config_text_sha256": config_hash,
        "seed": seed,
        "fusion_mode": config.fusion_mode,
        "fusion_beta": float(config.fusion_beta),
        "data_root": str(data_root),
    }
    _write_json(identity_path, identity)

    repro_state = configure_reproducibility(
        seed,
        strict_determinism=False,
        deterministic_warn_only=True,
    )
    print_log("=" * 60)
    print_log(f"{EXPERIMENT_ID} | CUB GZSL 训练")
    print_log(f"run_id：{args.run_id}")
    print_log(f"model_id：{MODEL_ID}")
    print_log(f"base_template_id：{BASE_TEMPLATE_ID}")
    print_log(f"配置：{config_path}")
    print_log(f"配置 SHA-256：{config_hash}")
    print_log(f"代码 commit：{code_commit}")
    print_log(f"随机种子：{seed}")
    if config.fusion_mode == "scale_consistent":
        print_log(
            "融合公式：global + fusion_beta * clamp(exp(logit_scale), max=100) * local；"
            f"fusion_beta={float(config.fusion_beta):g}"
        )
    else:
        print_log(f"融合公式：global + {float(config.local_weight):g} * local")
    print_log(
        f"PyTorch/CUDA：{repro_state['torch_version']} / "
        f"{repro_state['cuda_version'] or 'cpu'}"
    )
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
    before_load_records = {
        name: input_record(path) for name, path in input_paths.items()
    }
    train_cls, train_patches, train_labels = _load_training_cache(
        int(config.dim_f_clip),
        TRAIN_CLS_PATH,
        TRAIN_PATCH_PATH,
        TRAIN_LABEL_PATH,
    )
    sentence_embeds = _load_gpt55_sentences(
        GPT55_SENTENCE_PATH,
        int(config.num_class),
        int(config.dim_f_clip),
    )
    test_cache = load_v5_test_cache(CACHE_DIR)
    seenclasses, unseenclasses = load_v5_cub_split(
        DATA_RES101_PATH,
        DATA_SPLIT_PATH,
        train_labels,
        test_cache["seen_labels"],
        test_cache["unseen_labels"],
        "cpu",
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

    seenclass_ids = seenclasses.detach().cpu().long().tolist()
    unseenclass_ids = unseenclasses.detach().cpu().long().tolist()
    identity.update(
        {
            "input_records": input_records,
            "input_fingerprints": run_input_fingerprints,
            "seenclasses": seenclass_ids,
            "unseenclasses": unseenclass_ids,
        }
    )
    _write_json(identity_path, identity)

    # 与冻结 V5 母版一致：数据准备完成后重置随机状态，再初始化模型。
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
    logit_scale_initial = _actual_logit_scale(model)
    logit_scale_best = logit_scale_initial

    stages = config.lr_stages
    boundaries = _stage_boundaries(stages)
    total_epochs = boundaries[-1]
    optimizer = optim.Adam(
        model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
    )
    scheduler = _new_scheduler(optimizer, stages[0])
    active_stage = 0
    best_h = 0.0
    best_metrics = {"U": 0.0, "S": 0.0, "H": 0.0, "ZS": 0.0, "epoch": 0}

    iters_per_epoch = len(train_labels) // int(config.batch_size)
    if iters_per_epoch <= 0:
        raise ValueError("训练样本数小于 batch_size，无法完成一个训练 step。")

    print_log(f"初始 logit_scale：{logit_scale_initial:.8f}")
    print_log(f"训练计划：{len(stages)} 段，共 {total_epochs} 个 epoch。")
    print_log(f"训练缓存：CLS={tuple(train_cls.shape)}，patch={tuple(train_patches.shape)}。")

    for epoch in range(1, total_epochs + 1):
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
            _require_finite_tensor("training logits", output["logits"])
            losses = model.compute_loss(dict(output, batch_label=batch_labels))
            _require_finite_tensor("training loss", losses["loss"])
            losses["loss"].backward()
            _require_finite_gradients(model)
            optimizer.step()
            epoch_loss += float(losses["loss"].item())

            if (step + 1) % 20 == 0 or step + 1 == iters_per_epoch:
                print_log(
                    f"epoch {epoch}/{total_epochs} step {step + 1}/{iters_per_epoch} "
                    f"loss={losses['loss'].item():.4f}"
                )

        scheduler.step()
        seen_acc, unseen_acc, harmonic, zsl_acc = _evaluate_with_finite_logits(
            model,
            evaluate_cached_v5,
            config.device,
            test_cache,
            seenclasses,
            unseenclasses,
        )
        current_scale = _actual_logit_scale(model)
        print_log(
            f"epoch {epoch}: S={seen_acc * 100:.2f}% U={unseen_acc * 100:.2f}% "
            f"H={harmonic * 100:.2f}% ZS={zsl_acc * 100:.2f}% "
            f"avg_loss={epoch_loss / iters_per_epoch:.4f} "
            f"logit_scale={current_scale:.8f}"
        )

        if _is_new_best(harmonic, best_h, best_metrics["epoch"]):
            best_h = harmonic
            best_metrics = {
                "U": unseen_acc,
                "S": seen_acc,
                "H": harmonic,
                "ZS": zsl_acc,
                "epoch": epoch,
            }
            logit_scale_best = current_scale
            _atomic_torch_save(model.state_dict(), model_path)
            print_log(f"保存新最佳模型：{model_path}")

        checkpoint_identity = {
            **identity,
            "metric_unit": "fraction",
            "epoch": epoch,
            "stage_index": active_stage,
            "best_H": best_h,
            "best_metrics": best_metrics,
            "logit_scale_initial": logit_scale_initial,
            "logit_scale_best": logit_scale_best,
            "logit_scale_current": current_scale,
            "config": values,
            "rng_state": capture_rng_state(),
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
        }
        _atomic_torch_save(checkpoint_identity, checkpoint_path)

    logit_scale_final = _actual_logit_scale(model)
    metrics = {
        **identity,
        "status": "completed",
        "metric_unit": "percent",
        "U": best_metrics["U"] * 100.0,
        "S": best_metrics["S"] * 100.0,
        "H": best_metrics["H"] * 100.0,
        "ZS": best_metrics["ZS"] * 100.0,
        "best_epoch": best_metrics["epoch"],
        "logit_scale_initial": logit_scale_initial,
        "logit_scale_best": logit_scale_best,
        "logit_scale_final": logit_scale_final,
    }
    _require_finite_metrics(metrics)
    print_log("训练完成。")
    print_log(
        f"最佳 epoch={best_metrics['epoch']}，U={metrics['U']:.2f}%，"
        f"S={metrics['S']:.2f}%，H={metrics['H']:.2f}%，ZS={metrics['ZS']:.2f}%。"
    )
    print_log(
        "logit_scale："
        f"initial={logit_scale_initial:.8f}，best={logit_scale_best:.8f}，"
        f"final={logit_scale_final:.8f}。"
    )
    _write_json(metrics_path, metrics)


if __name__ == "__main__":
    main()
