"""V5-ABLATION-008 的 import-safe C/G/L/GL CUB 入口。

仓库内只保存冻结配置；日志、指标和 best model 全部写到显式给出的外部
``--output-dir``。模块导入本身不会解析参数、读取数据或启动训练。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parent
MODEL_SOURCE_PATH = REPO_ROOT / "model" / "V5ScorePathAblation.py"
ENTRY_SOURCE_PATH = Path(__file__).resolve()
MODEL_TEMPLATE_ID = "model/v5-template-v1"
VALID_SCORE_PATHS = {"frozen_clip", "global", "local", "full"}
DATA_MANIFEST_SCHEMA = "gtpj.v5_ablation_008.data_manifest.v1"
FROZEN_REQUIRED_DATA_KEYS = frozenset(
    {
        "xlsa17_res101",
        "xlsa17_att_splits",
        "gpt55_sentences",
        "test_seen_cls",
        "test_seen_labels",
        "test_unseen_cls",
        "test_unseen_labels",
    }
)
TRAINED_REQUIRED_DATA_KEYS = FROZEN_REQUIRED_DATA_KEYS | frozenset(
    {
        "train_cls",
        "train_patches",
        "train_labels",
        "test_seen_patches",
        "test_unseen_patches",
    }
)
V5_TEMPLATE_CONFIG_KEYS = {
    "dataset", "num_class", "dim_f_clip", "device", "batch_size",
    "random_seed", "text_source", "pse_heads", "pse_dropout",
    "pse_inner_ratio", "pse_outer_ratio", "tf_common_dim", "tf_heads",
    "tf_dropout", "weight_s2v", "local_weight", "fgvd_select_k",
    "score_mode", "lambda_consist", "consist_temp", "consist_dynamic_gamma",
    "lambda_topo_pearson", "icsa_ratio", "icsa_hidden", "lambda_bmdd",
    "msdn_temp", "sgmp_topk", "sgmp_hidden", "lambda_mpp", "lambda_neg",
    "sgmp_neg_margin", "lr_stages",
}
V5_ABLATION_008_CONFIG_KEYS = V5_TEMPLATE_CONFIG_KEYS | {"score_path"}


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run one frozen V5-ABLATION-008 score-path configuration.",
        allow_abbrev=False,
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--data-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-run-commit", required=True)
    return parser.parse_args(argv)


def _reserve_output_dir(path):
    output = Path(path).resolve()
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    return output


def _require_clean_code_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise RuntimeError("正式运行要求完整 git status --porcelain 为空。")


def _current_run_commit():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_expected_run_commit(expected_run_commit):
    current = _current_run_commit()
    expected = str(expected_run_commit).strip()
    if current != expected:
        raise RuntimeError(
            f"current HEAD {current} does not match expected run commit {expected}."
        )
    return current


def _validate_lr_stages(stages):
    if not isinstance(stages, list) or not stages:
        raise ValueError("lr_stages 必须是非空列表。")
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict) or set(stage) != {"lr", "epochs", "eta_min"}:
            raise ValueError(f"lr_stages 第 {index} 段字段不完整。")
        if float(stage["lr"]) <= 0 or int(stage["epochs"]) <= 0:
            raise ValueError(f"lr_stages 第 {index} 段 lr/epochs 必须大于 0。")
        if float(stage["eta_min"]) < 0:
            raise ValueError(f"lr_stages 第 {index} 段 eta_min 不能小于 0。")


def _load_config(path, yaml_module):
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    raw = yaml_module.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("配置顶层必须是字典。")
    values = {
        key: value["value"] if isinstance(value, dict) and "value" in value else value
        for key, value in raw.items()
    }
    missing = sorted(V5_ABLATION_008_CONFIG_KEYS - set(values))
    extra = sorted(set(values) - V5_ABLATION_008_CONFIG_KEYS)
    if missing or extra:
        raise ValueError(f"配置字段不匹配；缺少={missing}，多出={extra}。")
    if values["score_path"] not in VALID_SCORE_PATHS:
        raise ValueError(f"score_path 必须是 {sorted(VALID_SCORE_PATHS)}。")
    if values["dataset"] != "CUB" or values["text_source"] != "gpt55":
        raise ValueError("本入口只接受 CUB 与 gpt55。")
    if float(values["local_weight"]) != 0.2 or values["score_mode"] != "add":
        raise ValueError("未明确改动的 V5 配置必须保持 local_weight=0.2、score_mode=add。")
    _validate_lr_stages(values["lr_stages"])
    return SimpleNamespace(**values), values, config_path


def _require_cuda(config, torch_module):
    if not str(config.device).startswith("cuda"):
        raise RuntimeError("正式 V5-ABLATION-008 只允许 CUDA，不提供 CPU 回退。")
    if not torch_module.cuda.is_available():
        raise RuntimeError("CUDA 不可用，拒绝静默退回 CPU。")


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _executable_source_sha256():
    return {
        "model/V5ScorePathAblation.py": _sha256_file(MODEL_SOURCE_PATH),
        "train_V5_ABLATION_008_CUB.py": _sha256_file(ENTRY_SOURCE_PATH),
    }


def _required_data_keys(score_path):
    if score_path not in VALID_SCORE_PATHS:
        raise ValueError(f"unknown score_path: {score_path}")
    return (
        FROZEN_REQUIRED_DATA_KEYS
        if score_path == "frozen_clip"
        else TRAINED_REQUIRED_DATA_KEYS
    )


def _verify_data_manifest(manifest_path, data_root, score_path):
    manifest_file = Path(manifest_path).resolve()
    if not manifest_file.is_file():
        raise FileNotFoundError(f"data manifest does not exist: {manifest_file}")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid data manifest JSON: {manifest_file}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("data manifest root must be an object.")
    if manifest.get("schema_version") != DATA_MANIFEST_SCHEMA:
        raise ValueError(
            f"data manifest schema must be {DATA_MANIFEST_SCHEMA}."
        )
    if manifest.get("dataset") != "CUB":
        raise ValueError("data manifest dataset must be CUB.")
    records = manifest.get("files")
    if not isinstance(records, dict):
        raise ValueError("data manifest files must be an object.")

    root = Path(data_root).resolve()
    paths = {}
    fingerprints = {}
    for key in sorted(_required_data_keys(score_path)):
        record = records.get(key)
        if not isinstance(record, dict):
            raise ValueError(f"data manifest is missing file record: {key}")
        relative_value = record.get("relative_path")
        if not isinstance(relative_value, str) or not relative_value.strip():
            raise ValueError(f"data manifest relative_path is invalid: {key}")
        relative = Path(relative_value)
        if relative.is_absolute():
            raise ValueError(f"data manifest relative_path must be relative: {key}")
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"data manifest relative_path escapes data root: {key}") from exc
        if not path.is_file():
            raise FileNotFoundError(f"required data file does not exist: {path}")
        actual_size = path.stat().st_size
        expected_size = record.get("size_bytes")
        expected_sha256 = record.get("sha256")
        actual_sha256 = _sha256_file(path)
        if (
            not isinstance(expected_size, int)
            or actual_size != expected_size
            or not isinstance(expected_sha256, str)
            or actual_sha256 != expected_sha256.lower()
        ):
            raise ValueError(f"data fingerprint mismatch: {key}")
        paths[key] = path
        fingerprints[key] = {
            "relative_path": relative.as_posix(),
            "size_bytes": actual_size,
            "sha256": actual_sha256,
        }
    return {
        "manifest_sha256": _sha256_file(manifest_file),
        "paths": paths,
        "fingerprints": fingerprints,
    }


def _load_sentences(path, expected_classes, expected_dim, torch_module):
    if not path.is_file():
        raise FileNotFoundError(f"缺少 GPT-5.5 句子缓存：{path}")
    value = torch_module.load(path, map_location="cpu", weights_only=True).float()
    if value.dim() != 3 or value.size(0) != expected_classes or value.size(2) != expected_dim:
        raise ValueError(
            f"GPT-5.5 句子缓存必须是 [{expected_classes}, M, {expected_dim}]。"
        )
    return value


def _load_test_cache(paths, expected_dim, include_patches, torch_module):
    cache = {}
    for split in ("seen", "unseen"):
        cls = torch_module.load(
            paths[f"test_{split}_cls"], map_location="cpu", weights_only=True
        )
        labels = torch_module.load(
            paths[f"test_{split}_labels"], map_location="cpu", weights_only=True
        ).long()
        if cls.dim() != 2 or cls.size(1) != expected_dim:
            raise ValueError(f"test_{split} CLS must have shape [N, {expected_dim}].")
        if labels.dim() != 1 or cls.size(0) != labels.size(0):
            raise ValueError(f"test_{split} CLS and labels do not align.")
        cache[f"{split}_cls"] = cls
        cache[f"{split}_labels"] = labels
        if include_patches:
            patches = torch_module.load(
                paths[f"test_{split}_patches"],
                map_location="cpu",
                weights_only=True,
            )
            if (
                patches.dim() != 3
                or tuple(patches.shape[1:]) != (576, expected_dim)
                or patches.size(0) != cls.size(0)
            ):
                raise ValueError(
                    f"test_{split} patches must have shape [N, 576, {expected_dim}]."
                )
            cache[f"{split}_patches"] = patches
    return cache


def _load_training_cache(paths, expected_dim, torch_module):
    required = [paths["train_cls"], paths["train_patches"], paths["train_labels"]]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("缺少训练缓存：" + ", ".join(missing))
    cls = torch_module.load(paths["train_cls"], map_location="cpu", weights_only=True)
    patches = torch_module.load(
        paths["train_patches"], map_location="cpu", weights_only=True
    )
    labels = torch_module.load(
        paths["train_labels"], map_location="cpu", weights_only=True
    ).long()
    if cls.dim() != 2 or cls.size(1) != expected_dim:
        raise ValueError(f"训练 CLS 必须为 [N, {expected_dim}]。")
    if patches.dim() != 3 or tuple(patches.shape[1:]) != (576, expected_dim):
        raise ValueError(f"训练 patch 必须为 [N, 576, {expected_dim}]。")
    if labels.dim() != 1 or not (len(cls) == len(patches) == len(labels)):
        raise ValueError("训练 CLS、patch、label 数量不一致。")
    return cls, patches, labels


def _eval_only_split(paths, test_cache, torch_module, scipy_io):
    """冻结路径不读 train label cache，只核对 xlsa17 的两个测试划分。"""
    res101 = scipy_io.loadmat(paths["xlsa17_res101"])
    splits = scipy_io.loadmat(paths["xlsa17_att_splits"])
    labels = torch_module.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    seen_indices = torch_module.from_numpy(splits["test_seen_loc"].squeeze() - 1).long()
    unseen_indices = torch_module.from_numpy(
        splits["test_unseen_loc"].squeeze() - 1
    ).long()
    if not torch_module.equal(
        labels[seen_indices], test_cache["seen_labels"].detach().cpu().long()
    ):
        raise ValueError("test_seen cache labels 与 xlsa17 不一致。")
    if not torch_module.equal(
        labels[unseen_indices], test_cache["unseen_labels"].detach().cpu().long()
    ):
        raise ValueError("test_unseen cache labels 与 xlsa17 不一致。")
    seen = torch_module.unique(labels[seen_indices], sorted=True)
    unseen = torch_module.unique(labels[unseen_indices], sorted=True)
    return seen.detach().cpu().long(), unseen.detach().cpu().long()


def _per_class_accuracy(labels, predictions, classes, torch_module):
    labels = labels.detach().cpu().long()
    predictions = predictions.detach().cpu().long()
    values = []
    for class_id in classes.detach().cpu().long():
        mask = labels == class_id
        if not mask.any():
            raise ValueError(f"evaluation cache has no samples for class {int(class_id)}.")
        values.append((predictions[mask] == labels[mask]).float().mean())
    return float(torch_module.stack(values).mean().item())


def _frozen_cls_logits(model, cls_features, device, torch_module, batch_size):
    logits = []
    model.eval()
    with torch_module.inference_mode():
        for start in range(0, cls_features.size(0), batch_size):
            cls_batch = cls_features[start : start + batch_size].to(device).float()
            zero_patches = torch_module.zeros(
                cls_batch.size(0),
                576,
                cls_batch.size(1),
                device=cls_batch.device,
                dtype=cls_batch.dtype,
            )
            features = torch_module.cat([cls_batch.unsqueeze(1), zero_patches], dim=1)
            logits.append(model(features, is_train=False)["clip_S_pp"].detach().cpu())
    if not logits:
        raise ValueError("frozen evaluation cache must not be empty.")
    return torch_module.cat(logits, dim=0)


def _evaluate_frozen_cls_only(
    model,
    device,
    cache,
    seenclasses,
    unseenclasses,
    torch_module,
    batch_size=64,
):
    seenclasses = torch_module.as_tensor(seenclasses).detach().cpu().long()
    unseenclasses = torch_module.as_tensor(unseenclasses).detach().cpu().long()
    seen_logits = _frozen_cls_logits(
        model, cache["seen_cls"], device, torch_module, batch_size
    )
    unseen_logits = _frozen_cls_logits(
        model, cache["unseen_cls"], device, torch_module, batch_size
    )
    seen_prediction = seen_logits.argmax(dim=1)
    unseen_prediction = unseen_logits.argmax(dim=1)
    unseen_only_prediction = unseenclasses[
        unseen_logits[:, unseenclasses].argmax(dim=1)
    ]
    seen_accuracy = _per_class_accuracy(
        cache["seen_labels"], seen_prediction, seenclasses, torch_module
    )
    unseen_accuracy = _per_class_accuracy(
        cache["unseen_labels"], unseen_prediction, unseenclasses, torch_module
    )
    zsl_accuracy = _per_class_accuracy(
        cache["unseen_labels"], unseen_only_prediction, unseenclasses, torch_module
    )
    denominator = seen_accuracy + unseen_accuracy
    harmonic = (
        2.0 * seen_accuracy * unseen_accuracy / denominator if denominator else 0.0
    )
    return seen_accuracy, unseen_accuracy, harmonic, zsl_accuracy


def _metric_dict(values, *, epoch):
    seen, unseen, harmonic, zsl = values
    metrics = {
        "U": float(unseen), "S": float(seen), "H": float(harmonic),
        "ZS": float(zsl), "epoch": int(epoch),
    }
    if not all(math.isfinite(metrics[name]) for name in ("U", "S", "H", "ZS")):
        raise ValueError("all evaluation metrics must be finite.")
    return metrics


def _write_metrics(output_dir, metrics, metadata):
    payload = dict(metadata)
    payload["metric_unit"] = "fraction_0_to_1"
    payload["metrics"] = metrics
    target = output_dir / "metrics.json"
    temporary = output_dir / "metrics.json.tmp"
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporary, target)


def _save_best_model_atomic(torch_module, state_dict, target):
    target = Path(target)
    temporary = target.with_name(target.name + ".tmp")
    torch_module.save(state_dict, temporary)
    os.replace(temporary, target)


def _logger(output_dir):
    path = output_dir / "training.log"

    def log(message):
        text = str(message)
        print(text)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(text + "\n")

    return log


def _log_best_results(log, metrics):
    log(f"Best Results @ Epoch {metrics['epoch']}")
    log(f"GZSL-U: {metrics['U'] * 100:.2f}%")
    log(f"GZSL-S: {metrics['S'] * 100:.2f}%")
    log(f"GZSL-H: {metrics['H'] * 100:.2f}%")
    log(f"ZSL: {metrics['ZS'] * 100:.2f}%")


def _run_frozen_path(config, values, data_root, output_dir, runtime):
    torch = runtime.torch
    paths = runtime.data_paths
    sentences = _load_sentences(
        paths["gpt55_sentences"],
        int(config.num_class),
        int(config.dim_f_clip),
        torch,
    )
    test_cache = _load_test_cache(
        paths,
        int(config.dim_f_clip),
        include_patches=False,
        torch_module=torch,
    )
    seen, unseen = _eval_only_split(
        paths, test_cache, torch, runtime.scipy_io
    )
    runtime.seenclass_ids = [int(value) for value in seen.tolist()]
    runtime.unseenclass_ids = [int(value) for value in unseen.tolist()]
    text = sentences.mean(dim=1)
    model = runtime.build_score_path_model(
        "frozen_clip", config, seen, unseen, text[seen.cpu()], text[unseen.cpu()],
        sentences[seen.cpu()], initialization_seed=int(config.random_seed),
    ).to(config.device)
    values_out = _evaluate_frozen_cls_only(
        model, config.device, test_cache, seen, unseen, torch
    )
    metrics = _metric_dict(values_out, epoch=0)
    runtime.log(
        f"冻结评估：S={metrics['S']*100:.2f}% U={metrics['U']*100:.2f}% "
        f"H={metrics['H']*100:.2f}% ZS={metrics['ZS']*100:.2f}%"
    )
    _log_best_results(runtime.log, metrics)
    return metrics


def _stage_boundaries(stages):
    result, total = [], 0
    for stage in stages:
        total += int(stage["epochs"])
        result.append(total)
    return result


def _stage_for_epoch(epoch, boundaries):
    for index, boundary in enumerate(boundaries):
        if epoch <= boundary:
            return index
    raise ValueError("epoch 超过冻结训练计划。")


def _run_training_path(config, values, data_root, output_dir, runtime):
    torch = runtime.torch
    paths = runtime.data_paths
    train_cls, train_patches, train_labels = _load_training_cache(
        paths, int(config.dim_f_clip), torch
    )
    sentences = _load_sentences(
        paths["gpt55_sentences"],
        int(config.num_class),
        int(config.dim_f_clip),
        torch,
    )
    test_cache = _load_test_cache(
        paths,
        int(config.dim_f_clip),
        include_patches=True,
        torch_module=torch,
    )
    seen, unseen = runtime.load_v5_cub_split(
        paths["xlsa17_res101"],
        paths["xlsa17_att_splits"],
        train_labels,
        test_cache["seen_labels"],
        test_cache["unseen_labels"], "cpu",
    )
    runtime.seenclass_ids = [int(value) for value in seen.tolist()]
    runtime.unseenclass_ids = [int(value) for value in unseen.tolist()]
    runtime.configure_reproducibility(
        int(config.random_seed), strict_determinism=False, deterministic_warn_only=True
    )
    text = sentences.mean(dim=1)
    model = runtime.build_score_path_model(
        config.score_path, config, seen, unseen, text[seen.cpu()], text[unseen.cpu()],
        sentences[seen.cpu()], initialization_seed=int(config.random_seed),
    ).to(config.device)
    stages = config.lr_stages
    boundaries = _stage_boundaries(stages)
    optimizer = runtime.optim.Adam(
        model.parameters(), lr=float(stages[0]["lr"]), weight_decay=1e-4
    )
    scheduler = runtime.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(stages[0]["epochs"]), eta_min=float(stages[0]["eta_min"])
    )
    active_stage = 0
    best_h = -1.0
    best = None
    per_epoch = len(train_labels) // int(config.batch_size)
    if per_epoch <= 0:
        raise ValueError("训练样本数小于 batch_size。")
    for epoch in range(1, boundaries[-1] + 1):
        target_stage = _stage_for_epoch(epoch, boundaries)
        if target_stage != active_stage:
            active_stage = target_stage
            stage = stages[active_stage]
            for group in optimizer.param_groups:
                group["lr"] = float(stage["lr"])
            scheduler = runtime.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=int(stage["epochs"]), eta_min=float(stage["eta_min"])
            )
        model.train()
        epoch_loss = 0.0
        for step in range(per_epoch):
            optimizer.zero_grad(set_to_none=True)
            indices = torch.randperm(len(train_labels))[: int(config.batch_size)]
            labels = train_labels[indices].to(config.device)
            features = torch.cat(
                [train_cls[indices].to(config.device).float().unsqueeze(1),
                 train_patches[indices].to(config.device).float()], dim=1,
            )
            output = model(features, is_train=True)
            losses = model.compute_loss(dict(output, batch_label=labels))
            loss_value = float(losses["loss"].detach().item())
            if not math.isfinite(loss_value):
                raise FloatingPointError(
                    f"non-finite training loss at epoch={epoch}, step={step + 1}."
                )
            losses["loss"].backward()
            optimizer.step()
            epoch_loss += loss_value
        scheduler.step()
        evaluated = runtime.evaluate_cached_v5(
            model, config.device, test_cache, seen, unseen
        )
        metrics = _metric_dict(evaluated, epoch=epoch)
        runtime.log(
            f"epoch {epoch}/{boundaries[-1]} loss={epoch_loss/per_epoch:.4f} "
            f"S={metrics['S']*100:.2f}% U={metrics['U']*100:.2f}% "
            f"H={metrics['H']*100:.2f}% ZS={metrics['ZS']*100:.2f}%"
        )
        if metrics["H"] > best_h:
            best_h, best = metrics["H"], metrics
            _save_best_model_atomic(
                torch, model.state_dict(), output_dir / "best_model.pth"
            )
    if best is None:
        raise RuntimeError("training finished without a finite best result.")
    _log_best_results(runtime.log, best)
    return best


def _dispatch_score_path(
    config, values, data_root, output_dir, *, frozen_runner=_run_frozen_path,
    training_runner=_run_training_path, runtime=None,
):
    runner = frozen_runner if config.score_path == "frozen_clip" else training_runner
    if runtime is None:
        return runner(config, values, data_root, output_dir)
    return runner(config, values, data_root, output_dir, runtime)


def _load_runtime(log):
    """只在 clean gate 之后调用，避免 import 时触发仓库本地运行依赖。"""
    import scipy.io as scipy_io
    import torch
    import torch.optim as optim
    import yaml

    from model.V5ScorePathAblation import build_score_path_model
    from tools.reproducibility import configure_reproducibility
    from tools.v5_cub_data import load_v5_cub_split
    from tools.v5_evaluation import evaluate_cached_v5
    from tools.v5_runtime import sha256_file

    return SimpleNamespace(
        torch=torch, optim=optim, yaml=yaml, scipy_io=scipy_io,
        build_score_path_model=build_score_path_model,
        configure_reproducibility=configure_reproducibility,
        load_v5_cub_split=load_v5_cub_split,
        evaluate_cached_v5=evaluate_cached_v5,
        sha256_file=sha256_file, log=log,
    )


def main(argv=None):
    args = _parse_args(argv)
    output_candidate = args.output_dir.resolve()
    if output_candidate.exists():
        raise FileExistsError(f"output directory already exists: {output_candidate}")
    _require_clean_code_tree()
    run_commit = _require_expected_run_commit(args.expected_run_commit)
    executable_source_sha256 = _executable_source_sha256()
    runtime = _load_runtime(lambda message: None)
    config, values, config_path = _load_config(args.config, runtime.yaml)
    _require_cuda(config, runtime.torch)
    data_identity = _verify_data_manifest(
        args.data_manifest, args.data_root, config.score_path
    )
    runtime.data_paths = data_identity["paths"]
    runtime.data_manifest_sha256 = data_identity["manifest_sha256"]
    runtime.verified_input_fingerprints = data_identity["fingerprints"]
    output_dir = _reserve_output_dir(output_candidate)
    runtime.log = _logger(output_dir)
    shutil.copy2(config_path, output_dir / "config.yaml")
    runtime.configure_reproducibility(
        int(config.random_seed), strict_determinism=False, deterministic_warn_only=True
    )
    runtime.log(f"模板：{MODEL_TEMPLATE_ID}")
    runtime.log(f"运行 commit：{run_commit}")
    runtime.log(f"score_path：{config.score_path}")
    metrics = _dispatch_score_path(
        config, values, args.data_root, output_dir, runtime=runtime
    )
    metadata = {
        "template_id": MODEL_TEMPLATE_ID,
        "run_commit": run_commit,
        "executable_source_sha256": executable_source_sha256,
        "config_sha256": runtime.sha256_file(config_path),
        "data_manifest_sha256": runtime.data_manifest_sha256,
        "verified_input_fingerprints": runtime.verified_input_fingerprints,
        "seenclass_ids": runtime.seenclass_ids,
        "unseenclass_ids": runtime.unseenclass_ids,
        "score_path": config.score_path,
        "random_seed": int(config.random_seed),
        "evaluation_only": config.score_path == "frozen_clip",
    }
    _write_metrics(output_dir, metrics, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
