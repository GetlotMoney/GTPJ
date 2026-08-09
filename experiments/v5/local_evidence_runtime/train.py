"""V5 局部互补性五组实验共享的 import-safe、CUDA-only 训练入口。"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace
import uuid

import torch
import torch.optim as optim
import yaml


EXPERIMENT_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
for import_root in (ROOT, EXPERIMENT_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from model.MyModel import GTPJ  # noqa: E402
from tools.reproducibility import configure_reproducibility  # noqa: E402
from tools.v5_cub_data import load_v5_cub_split  # noqa: E402
from tools.v5_evaluation import load_v5_test_cache, v5_test_cache_paths  # noqa: E402
from tools.v5_input_manifest_cache import (  # noqa: E402
    build_cached_records,
    capture_input_stats,
    validate_stable_input_stats,
)
from tools.v5_runtime import (  # noqa: E402
    capture_rng_state,
    input_fingerprints,
    sha256_file,
)


IDEA_ID = "IDEA-0006"
MODEL_TEMPLATE_ID = "MODEL-V5-TEMPLATE-V1"
MODEL_TEMPLATE_TAG = "model/v5-template-v1"
MODEL_TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
EVALUATION_PROTOCOL = "standard_gzsl_u_s_h_zs"
MIN_AVAILABLE_MEMORY_BYTES = 14 * 1024**3

CANONICAL_CONFIG_KEYS = {
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
EXPERIMENT_CONFIG_KEYS = {
    "experiment_id",
    "idea_id",
    "base_template_id",
    "base_template_tag",
    "base_template_commit",
    "dataset_split",
    "evaluation_protocol",
    "experiment_mode",
    "ablation_disable_fgvd_geometry",
    "lambda_local_ce",
    "lambda_confusion_contrast",
    "confusion_topk",
    "confusion_margin",
    "lambda_crop_distill",
    "crop_distill_temp",
    "crop_teacher_views",
}

MODE_CONTRACTS = {
    "fgvd_off": {
        "experiment_id": "V5-ABLATION-004",
        "idea_id": "none",
        "lambda_local_ce": 0.0,
        "lambda_confusion_contrast": 0.0,
        "lambda_crop_distill": 0.0,
        "crop_teacher_views": 0,
    },
    "local_ce": {
        "experiment_id": "V5-INNOVATION-004",
        "idea_id": IDEA_ID,
        "lambda_local_ce": 0.1,
        "lambda_confusion_contrast": 0.0,
        "lambda_crop_distill": 0.0,
        "crop_teacher_views": 0,
    },
    "confusion_contrast": {
        "experiment_id": "V5-INNOVATION-005",
        "idea_id": IDEA_ID,
        "lambda_local_ce": 0.1,
        "lambda_confusion_contrast": 0.1,
        "lambda_crop_distill": 0.0,
        "crop_teacher_views": 0,
    },
    "crop_distill": {
        "experiment_id": "V5-INNOVATION-006",
        "idea_id": IDEA_ID,
        "lambda_local_ce": 0.1,
        "lambda_confusion_contrast": 0.0,
        "lambda_crop_distill": 0.05,
        "crop_teacher_views": 2,
    },
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="训练 V5 局部证据修复的四个预注册训练方案。",
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-run-commit", required=True)
    parser.add_argument(
        "--input-manifest-cache",
        type=Path,
        default=None,
        help="共享的大文件 SHA-256 清单；省略时放在项目 .runtime/input_manifests。",
    )
    return parser


def _run_git(repo_root, *arguments):
    return subprocess.run(
        ["git", "-C", str(Path(repo_root).resolve()), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def current_code_commit(repo_root=ROOT):
    return _run_git(repo_root, "rev-parse", "HEAD")


def require_expected_commit(repo_root, expected_commit):
    expected = str(expected_commit).strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise RuntimeError("--expected-run-commit 必须是完整 40 位 commit。")
    actual = current_code_commit(repo_root).lower()
    if actual != expected:
        raise RuntimeError(f"当前 commit={actual}，不等于预期 run commit={expected}。")
    return actual


def require_clean_git(repo_root=ROOT):
    status = _run_git(repo_root, "status", "--porcelain", "--untracked-files=all")
    if status:
        raise RuntimeError("正式运行要求 Git 工作树完全干净（含未跟踪文件）。")


def require_cuda_device(device_name):
    name = str(device_name)
    if not name.startswith("cuda"):
        raise RuntimeError("本入口只允许 CUDA，配置 device 必须是 cuda 或 cuda:N。")
    if not torch.cuda.is_available():
        raise RuntimeError("本入口只允许 CUDA，但当前 PyTorch 看不到 CUDA。")
    device = torch.device(name)
    index = device.index if device.index is not None else torch.cuda.current_device()
    if index < 0 or index >= torch.cuda.device_count():
        raise RuntimeError(f"CUDA 设备 {name} 不存在。")
    torch.cuda.set_device(index)
    return device


def _available_physical_memory_bytes():
    if os.name != "nt":
        if hasattr(os, "sysconf"):
            return int(os.sysconf("SC_AVPHYS_PAGES")) * int(
                os.sysconf("SC_PAGE_SIZE")
            )
        raise RuntimeError("当前平台无法读取可用物理内存。")

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
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise RuntimeError("Windows 可用物理内存查询失败。")
    return int(status.ullAvailPhys)


def require_available_memory(minimum_bytes=MIN_AVAILABLE_MEMORY_BYTES):
    available = _available_physical_memory_bytes()
    if available <= 0:
        raise RuntimeError("可用物理内存读数无效，拒绝正式训练。")
    if available < int(minimum_bytes):
        raise MemoryError(
            f"正式训练至少需要 14 GiB 可用物理内存；当前约 "
            f"{available / 1024**3:.2f} GiB。"
        )
    return available


def require_new_run_dir(run_dir):
    path = Path(run_dir).resolve()
    if path.exists():
        raise FileExistsError(f"输出目录必须尚不存在：{path}")
    return path


def require_finite_tensor(name, tensor):
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"{name} 必须是 Tensor。")
    if not torch.isfinite(tensor).all():
        raise FloatingPointError(f"{name} 出现 nonfinite 数值。")


def _temporary_sibling(path):
    return path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")


def atomic_write_text(path, text):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_sibling(target)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path, payload):
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    atomic_write_text(path, text + "\n")


def atomic_torch_save(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = _temporary_sibling(target)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


class AtomicTrainingLog:
    def __init__(self, path):
        self.path = Path(path)
        self._lines = []

    def write(self, message):
        text = str(message)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))
        self._lines.append(text)
        atomic_write_text(self.path, "\n".join(self._lines) + "\n")


def _flatten_yaml_values(raw):
    return {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }


def _validate_lr_stages(stages):
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages 必须是非空列表。")
    allowed = {"lr", "epochs", "eta_min"}
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict) or set(stage) != allowed:
            raise ValueError(f"lr_stages 第 {index} 段字段不完整。")
        if float(stage["lr"]) <= 0 or int(stage["epochs"]) <= 0:
            raise ValueError(f"lr_stages 第 {index} 段的 lr/epochs 必须大于 0。")
        if float(stage["eta_min"]) < 0:
            raise ValueError(f"lr_stages 第 {index} 段的 eta_min 不能小于 0。")


def load_config(path):
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("配置顶层必须是字典。")
    values = _flatten_yaml_values(raw)
    allowed = CANONICAL_CONFIG_KEYS | EXPERIMENT_CONFIG_KEYS
    missing = sorted(allowed - set(values))
    extra = sorted(set(values) - allowed)
    if missing or extra:
        raise ValueError(f"配置字段不匹配；缺少={missing}，多出={extra}。")

    fixed = {
        "base_template_id": MODEL_TEMPLATE_ID,
        "base_template_tag": MODEL_TEMPLATE_TAG,
        "base_template_commit": MODEL_TEMPLATE_COMMIT,
        "dataset": "CUB",
        "num_class": 200,
        "text_source": "gpt55",
        "local_weight": 0.2,
        "score_mode": "add",
        "dataset_split": "xlsa17/att_splits.mat",
        "evaluation_protocol": EVALUATION_PROTOCOL,
        "ablation_disable_fgvd_geometry": True,
        "confusion_topk": 5,
        "confusion_margin": 0.1,
        "crop_distill_temp": 2.0,
    }
    for name, expected in fixed.items():
        if values[name] != expected:
            raise ValueError(f"本创新固定 {name}={expected!r}，实际为 {values[name]!r}。")
    mode = str(values["experiment_mode"])
    if mode not in MODE_CONTRACTS:
        raise ValueError(f"未知 experiment_mode={mode!r}。")
    for name, expected in MODE_CONTRACTS[mode].items():
        if values[name] != expected:
            raise ValueError(f"{mode} 固定 {name}={expected!r}，实际为 {values[name]!r}。")
    if not isinstance(values["random_seed"], int) or values["random_seed"] < 0:
        raise ValueError("random_seed 必须是非负整数。")
    if not str(values["device"]).startswith("cuda"):
        raise ValueError("配置 device 必须是 cuda 或 cuda:N。")
    _validate_lr_stages(values["lr_stages"])
    return SimpleNamespace(**values), values, config_path


def build_input_paths(data_root, config_path, experiment_mode):
    root = Path(data_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"数据根目录不存在：{root}")
    cache = root / "cache"
    paths = {
        "config": Path(config_path).resolve(),
        "xlsa17_res101": root / "xlsa17" / "data" / "CUB" / "res101.mat",
        "xlsa17_att_splits": root / "xlsa17" / "data" / "CUB" / "att_splits.mat",
        "train_cls": cache / "CUB_train_features.pt",
        "train_patches": cache / "CUB_train_patch_features.pt",
        "train_labels": cache / "CUB_train_labels.pt",
        "gpt55_sentences": cache / "CUB_gpt55_sentence_embeds.pt",
        **{
            f"test_{name}": path
            for name, path in v5_test_cache_paths(cache).items()
        },
    }
    if experiment_mode == "crop_distill":
        paths["crop_teacher_cls"] = cache / "CUB_train_features_aug.pt"
        paths["crop_teacher_views"] = cache / "CUB_train_views.pt"
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("正式运行缺少输入：" + ", ".join(missing))
    return paths


def _load_training_cache(paths, expected_dim):
    cls_features = torch.load(
        paths["train_cls"], map_location="cpu", weights_only=True
    )
    patches = torch.load(
        paths["train_patches"], map_location="cpu", weights_only=True
    )
    labels = torch.load(
        paths["train_labels"], map_location="cpu", weights_only=True
    ).long()
    if cls_features.dim() != 2 or cls_features.size(1) != expected_dim:
        raise ValueError(f"训练 CLS 必须是 [N, {expected_dim}]。")
    if patches.dim() != 3 or tuple(patches.shape[1:]) != (576, expected_dim):
        raise ValueError(f"训练局部块必须是 [N, 576, {expected_dim}]。")
    if labels.dim() != 1 or not (len(cls_features) == len(patches) == len(labels)):
        raise ValueError("训练 CLS、局部块和标签的样本数量或形状不一致。")
    require_finite_tensor("train_cls", cls_features)
    require_finite_tensor("train_patches", patches)
    return cls_features, patches, labels


def _load_sentences(path, expected_classes, expected_dim, device):
    sentences = torch.load(path, map_location="cpu", weights_only=True)
    expected = (expected_classes, sentences.size(1), expected_dim)
    if sentences.dim() != 3 or tuple(sentences.shape) != expected:
        raise ValueError(
            f"GPT-5.5 句子缓存必须是 [{expected_classes}, M, {expected_dim}]。"
        )
    require_finite_tensor("gpt55_sentences", sentences)
    return sentences.to(device).float()


def _load_crop_teacher_cache(paths, expected_views, expected_samples, expected_dim):
    features = torch.load(
        paths["crop_teacher_cls"], map_location="cpu", weights_only=True
    )
    view_count = int(
        torch.load(
            paths["crop_teacher_views"], map_location="cpu", weights_only=True
        ).item()
    )
    expected = (int(expected_views), int(expected_samples), int(expected_dim))
    if view_count != int(expected_views) or tuple(features.shape) != expected:
        raise ValueError(
            f"裁剪 teacher 缓存必须是 {expected} 且 views={expected_views}，"
            f"实际 shape={tuple(features.shape)}、views={view_count}。"
        )
    require_finite_tensor("crop_teacher_cls", features)
    return features.float()


def default_input_manifest_path():
    common = Path(_run_git(ROOT, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = (ROOT / common).resolve()
    project_root = common.resolve().parent
    return project_root / ".runtime" / "input_manifests" / "v5_cub_sha256.json"


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
    raise ValueError(f"epoch {epoch} 超过训练计划。")


def _new_scheduler(optimizer, stage):
    return optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=int(stage["epochs"]),
        eta_min=float(stage["eta_min"]),
    )


def _require_finite_metrics(metrics):
    for name, value in metrics.items():
        if not math.isfinite(float(value)):
            raise FloatingPointError(f"指标 {name} 出现 nonfinite 数值。")


def _per_class_accuracy(labels, predictions, classes):
    values = []
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    for class_id in torch.as_tensor(classes).detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"评估缓存缺少类别 {int(class_id)}。")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch.stack(values).mean().item())


def branch_metrics_from_scores(
    seen_scores,
    unseen_scores,
    seen_labels,
    unseen_labels,
    seenclasses,
    unseenclasses,
):
    seen_scores = seen_scores.detach().cpu().float()
    unseen_scores = unseen_scores.detach().cpu().float()
    seen_labels = seen_labels.detach().cpu().long()
    unseen_labels = unseen_labels.detach().cpu().long()
    seenclasses = torch.as_tensor(seenclasses).detach().cpu().long()
    unseenclasses = torch.as_tensor(unseenclasses).detach().cpu().long()
    if seen_scores.dim() != 2 or unseen_scores.dim() != 2:
        raise ValueError("分支分数必须是 [N, C]。")
    if seen_scores.size(1) != unseen_scores.size(1):
        raise ValueError("seen/unseen 分支类别轴不一致。")

    seen_prediction = seen_scores.argmax(dim=1)
    unseen_prediction = unseen_scores.argmax(dim=1)
    unseen_only_prediction = unseenclasses[
        unseen_scores[:, unseenclasses].argmax(dim=1)
    ]
    seen_correct = seen_prediction == seen_labels
    unseen_correct = unseen_prediction == unseen_labels
    seen_accuracy = _per_class_accuracy(seen_labels, seen_prediction, seenclasses)
    unseen_accuracy = _per_class_accuracy(
        unseen_labels, unseen_prediction, unseenclasses
    )
    zsl_accuracy = _per_class_accuracy(
        unseen_labels, unseen_only_prediction, unseenclasses
    )
    denominator = seen_accuracy + unseen_accuracy
    harmonic = (
        2.0 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    )
    return (
        {"U": unseen_accuracy, "S": seen_accuracy, "H": harmonic, "ZS": zsl_accuracy},
        {"seen_correct": seen_correct, "unseen_correct": unseen_correct},
    )


def transition_metrics(global_correct, candidate_correct):
    global_correct = torch.as_tensor(global_correct, dtype=torch.bool).cpu()
    candidate_correct = torch.as_tensor(candidate_correct, dtype=torch.bool).cpu()
    if global_correct.shape != candidate_correct.shape or global_correct.dim() != 1:
        raise ValueError("正确性向量必须是一维且形状相同。")
    count = int(global_correct.numel())
    if count <= 0:
        raise ValueError("正确性向量不能为空。")
    rescue = int((~global_correct & candidate_correct).sum().item())
    harm = int((global_correct & ~candidate_correct).sum().item())
    return {
        "rescue": rescue,
        "harm": harm,
        "rescue_rate": rescue / count,
        "harm_rate": harm / count,
    }


def _predict_all_branches(model, cls_features, patches, device, batch_size=64):
    collected = {"final": [], "global": [], "local": []}
    model.eval()
    with torch.no_grad():
        for start in range(0, cls_features.size(0), batch_size):
            cls_batch = cls_features[start : start + batch_size].to(device).float()
            patch_batch = patches[start : start + batch_size].to(device).float()
            output = model(
                torch.cat([cls_batch.unsqueeze(1), patch_batch], dim=1),
                is_train=False,
            )
            for name, key in (
                ("final", "final_logits"),
                ("global", "global_logits"),
                ("local", "local_logits"),
            ):
                require_finite_tensor(key, output[key])
                collected[name].append(output[key].detach().cpu())
    return {name: torch.cat(parts, dim=0) for name, parts in collected.items()}


def _evaluate(model, device, cache, seenclasses, unseenclasses):
    seen_scores = _predict_all_branches(
        model, cache["seen_cls"], cache["seen_patches"], device
    )
    unseen_scores = _predict_all_branches(
        model, cache["unseen_cls"], cache["unseen_patches"], device
    )
    branch_metrics = {}
    branch_states = {}
    for branch in ("final", "global", "local"):
        branch_metrics[branch], branch_states[branch] = branch_metrics_from_scores(
            seen_scores[branch],
            unseen_scores[branch],
            cache["seen_labels"],
            cache["unseen_labels"],
            seenclasses,
            unseenclasses,
        )

    metrics = dict(branch_metrics["final"])
    for branch in ("global", "local"):
        for name, value in branch_metrics[branch].items():
            metrics[f"{branch}_{name}"] = value
    global_correct = torch.cat(
        [branch_states["global"]["seen_correct"], branch_states["global"]["unseen_correct"]]
    )
    for branch in ("final", "local"):
        candidate_correct = torch.cat(
            [branch_states[branch]["seen_correct"], branch_states[branch]["unseen_correct"]]
        )
        for name, value in transition_metrics(global_correct, candidate_correct).items():
            metrics[f"{branch}_{name}"] = value
    _require_finite_metrics(metrics)
    return metrics


def _identity_packet(
    code_commit,
    config_values,
    config_hash,
    input_records,
    fingerprints,
    seenclasses,
    unseenclasses,
):
    return {
        "experiment_id": config_values["experiment_id"],
        "idea_id": config_values["idea_id"],
        "template_id": MODEL_TEMPLATE_ID,
        "template_tag": MODEL_TEMPLATE_TAG,
        "template_commit": MODEL_TEMPLATE_COMMIT,
        "code_commit": code_commit,
        "config": config_values,
        "config_sha256": config_hash,
        "input_files": input_records,
        "input_fingerprints": fingerprints,
        "seenclasses": seenclasses.detach().cpu().long().tolist(),
        "unseenclasses": unseenclasses.detach().cpu().long().tolist(),
        "evaluation_protocol": EVALUATION_PROTOCOL,
    }


def run_training(
    config_path,
    data_root,
    run_dir,
    expected_run_commit,
    input_manifest_cache=None,
):
    config, config_values, resolved_config = load_config(config_path)
    output_dir = require_new_run_dir(run_dir)
    code_commit = require_expected_commit(ROOT, expected_run_commit)
    require_clean_git(ROOT)
    device = require_cuda_device(config.device)
    available_memory = require_available_memory()
    input_paths = build_input_paths(
        data_root, resolved_config, config.experiment_mode
    )
    manifest_path = (
        Path(input_manifest_cache).resolve()
        if input_manifest_cache is not None
        else default_input_manifest_path()
    )
    cached_records = build_cached_records(input_paths, manifest_path)
    before_load_stats = capture_input_stats(input_paths)

    output_dir.mkdir(parents=True, exist_ok=False)
    log = AtomicTrainingLog(output_dir / "training.log")
    metrics_path = output_dir / "metrics.json"
    metrics_payload = {
        "schema_version": "gtpj.v5_local_evidence.metrics.v1",
        "status": "preparing",
        "history": [],
    }
    try:
        seed = int(config.random_seed)
        repro_state = configure_reproducibility(
            seed,
            strict_determinism=False,
            deterministic_warn_only=True,
        )
        cache_dir = Path(data_root).resolve() / "cache"
        train_cls, train_patches, train_labels = _load_training_cache(
            input_paths, int(config.dim_f_clip)
        )
        crop_teacher_cls = None
        if config.experiment_mode == "crop_distill":
            crop_teacher_cls = _load_crop_teacher_cache(
                input_paths,
                int(config.crop_teacher_views),
                len(train_labels),
                int(config.dim_f_clip),
            )
        sentence_embeds = _load_sentences(
            input_paths["gpt55_sentences"],
            int(config.num_class),
            int(config.dim_f_clip),
            device,
        )
        test_cache = load_v5_test_cache(cache_dir)
        for name, tensor in test_cache.items():
            if tensor.is_floating_point():
                require_finite_tensor(f"test_{name}", tensor)
        seenclasses, unseenclasses = load_v5_cub_split(
            input_paths["xlsa17_res101"],
            input_paths["xlsa17_att_splits"],
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
        if crop_teacher_cls is not None:
            input_tensors["crop_teacher_cls"] = crop_teacher_cls
            input_tensors["crop_teacher_views"] = torch.tensor(
                int(config.crop_teacher_views)
            )
        after_load_stats = capture_input_stats(input_paths)
        validate_stable_input_stats(before_load_stats, after_load_stats)
        require_expected_commit(ROOT, expected_run_commit)
        require_clean_git(ROOT)
        input_records = {}
        for name, record in cached_records.items():
            stable_record = {
                key: value for key, value in record.items() if key != "hash_source"
            }
            tensor = input_tensors.get(name)
            if tensor is not None:
                stable_record["shape"] = list(tensor.shape)
                stable_record["dtype"] = str(tensor.dtype)
            input_records[name] = stable_record
        fingerprints = input_fingerprints(input_records)
        config_hash = sha256_file(resolved_config)
        identity = _identity_packet(
            code_commit,
            config_values,
            config_hash,
            input_records,
            fingerprints,
            seenclasses,
            unseenclasses,
        )
        metrics_payload.update(identity)
        metrics_payload["status"] = "running"
        atomic_write_json(metrics_path, metrics_payload)

        log.write(
            f"实验：{config.experiment_id}；idea：{config.idea_id}；"
            f"方案：{config.experiment_mode}"
        )
        log.write(f"母版：{MODEL_TEMPLATE_ID}@{MODEL_TEMPLATE_COMMIT}")
        log.write(f"run commit：{code_commit}")
        log.write(f"配置：{resolved_config}；SHA-256={config_hash}")
        log.write(f"数据根目录：{Path(data_root).resolve()}")
        log.write(f"随机种子：{seed}；设备：{device}")
        log.write(f"开跑前可用物理内存：{available_memory / 1024**3:.2f} GiB")
        log.write(
            "固定改动：关闭 FGVD 几何编码；其余训练日程与母版一致；"
            f"local_ce={config.lambda_local_ce}；"
            f"confusion={config.lambda_confusion_contrast}；"
            f"crop_distill={config.lambda_crop_distill}"
        )
        log.write(f"共享输入哈希清单：{manifest_path}")
        for name, record in input_records.items():
            shape = f"；shape={record['shape']}；dtype={record['dtype']}" if "shape" in record else ""
            log.write(
                f"输入 {name}：{record['path']}；sha256={record['sha256']}；"
                f"size={record['size_bytes']}；"
                f"hash={cached_records[name]['hash_source']}{shape}"
            )

        configure_reproducibility(
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
        ).to(device)

        stages = config.lr_stages
        boundaries = _stage_boundaries(stages)
        total_epochs = boundaries[-1]
        optimizer = optim.Adam(
            model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
        )
        scheduler = _new_scheduler(optimizer, stages[0])
        active_stage = 0
        best_h = -math.inf
        best_metrics = None
        iterations = len(train_labels) // int(config.batch_size)
        if iterations <= 0:
            raise ValueError("训练样本数小于 batch_size。")

        for epoch in range(1, total_epochs + 1):
            target_stage = _stage_for_epoch(epoch, boundaries)
            if target_stage != active_stage:
                active_stage = target_stage
                stage = stages[active_stage]
                for group in optimizer.param_groups:
                    group["lr"] = float(stage["lr"])
                scheduler = _new_scheduler(optimizer, stage)

            model.train()
            epoch_losses = {}
            for step in range(iterations):
                optimizer.zero_grad(set_to_none=True)
                indices = torch.randperm(len(train_labels))[: int(config.batch_size)]
                labels = train_labels[indices].to(device)
                cls_batch = train_cls[indices].to(device).float().unsqueeze(1)
                patch_batch = train_patches[indices].to(device).float()
                features = torch.cat([cls_batch, patch_batch], dim=1)

                output = model(features, is_train=True)
                for name in ("global_logits", "local_logits", "final_logits"):
                    require_finite_tensor(name, output[name])
                package = dict(output, batch_label=labels)
                if crop_teacher_cls is not None:
                    crop_batch = crop_teacher_cls[:, indices].to(device).float()
                    model.eval()
                    with torch.no_grad():
                        crop_teacher_logits = torch.stack(
                            [
                                model.global_logits_from_cls(crop_batch[view])
                                for view in range(crop_batch.size(0))
                            ],
                            dim=0,
                        )
                    model.train()
                    require_finite_tensor(
                        "crop_teacher_logits", crop_teacher_logits
                    )
                    package["crop_teacher_logits"] = crop_teacher_logits
                losses = model.compute_loss(package)
                for name, value in losses.items():
                    require_finite_tensor(name, value)
                losses["loss"].backward()
                optimizer.step()
                for name, value in losses.items():
                    epoch_losses[name] = epoch_losses.get(name, 0.0) + float(
                        value.detach().item()
                    )

                if (step + 1) % 20 == 0 or step + 1 == iterations:
                    log.write(
                        f"epoch {epoch}/{total_epochs} step {step + 1}/{iterations} "
                        f"loss={losses['loss'].item():.6f}"
                    )

            scheduler.step()
            metrics = _evaluate(
                model, device, test_cache, seenclasses, unseenclasses
            )
            metrics["epoch"] = epoch
            average_losses = {
                name: total / iterations for name, total in epoch_losses.items()
            }
            metrics["avg_loss"] = average_losses["loss"]
            _require_finite_metrics(metrics)
            epoch_record = {
                **metrics,
                "losses": average_losses,
            }
            metrics_payload["history"].append(epoch_record)

            if metrics["H"] > best_h:
                best_h = metrics["H"]
                best_metrics = dict(epoch_record)
                atomic_torch_save(
                    output_dir / "model_best.pt",
                    {
                        **identity,
                        "best_metrics": best_metrics,
                        "model_state_dict": model.state_dict(),
                    },
                )

            checkpoint = {
                **identity,
                "epoch": epoch,
                "stage_index": active_stage,
                "best_metrics": best_metrics,
                "rng_state": capture_rng_state(),
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
            }
            atomic_torch_save(output_dir / "checkpoint_last.pt", checkpoint)
            metrics_payload["best"] = best_metrics
            metrics_payload["latest"] = epoch_record
            atomic_write_json(metrics_path, metrics_payload)
            log.write(
                f"epoch {epoch}：S={metrics['S'] * 100:.2f}% "
                f"U={metrics['U'] * 100:.2f}% H={metrics['H'] * 100:.2f}% "
                f"ZS={metrics['ZS'] * 100:.2f}%"
            )
            log.write(
                "loss：" + "；".join(
                    f"{name}={value:.6f}"
                    for name, value in sorted(average_losses.items())
                )
            )

        require_expected_commit(ROOT, expected_run_commit)
        require_clean_git(ROOT)
        metrics_payload["status"] = "completed"
        metrics_payload["reproducibility"] = repro_state
        atomic_write_json(metrics_path, metrics_payload)
        log.write("训练完成；training.log、metrics.json、model_best.pt、checkpoint_last.pt 已原子落盘。")
        return best_metrics
    except Exception as error:
        metrics_payload["status"] = "failed"
        metrics_payload["error"] = f"{type(error).__name__}: {error}"
        atomic_write_json(metrics_path, metrics_payload)
        log.write(metrics_payload["error"])
        raise


def main(argv=None):
    args = build_parser().parse_args(argv)
    run_training(
        args.config,
        args.data_root,
        args.run_dir,
        args.expected_run_commit,
        args.input_manifest_cache,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
