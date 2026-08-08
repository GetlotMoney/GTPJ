"""V5-ABLATION-008 的 import-safe C/G/L/GL CUB 入口。

仓库内只保存冻结配置；日志、指标和 best model 全部写到显式给出的外部
``--output-dir``。模块导入本身不会解析参数、读取数据或启动训练。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace


MODEL_TEMPLATE_ID = "model/v5-template-v1"
VALID_SCORE_PATHS = {"frozen_clip", "global", "local", "full"}
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
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def _reserve_output_dir(path):
    output = Path(path).resolve()
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    return output


def _require_clean_code_tree():
    result = subprocess.run(
        ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
    )
    if result.stdout.strip():
        raise RuntimeError("正式运行要求完整 git status --porcelain 为空。")


def _current_code_commit():
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


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


def _paths(data_root):
    root = Path(data_root).resolve()
    return {
        "cache": root / "cache",
        "res101": root / "xlsa17" / "data" / "CUB" / "res101.mat",
        "split": root / "xlsa17" / "data" / "CUB" / "att_splits.mat",
        "train_cls": root / "cache" / "CUB_train_features.pt",
        "train_patches": root / "cache" / "CUB_train_patch_features.pt",
        "train_labels": root / "cache" / "CUB_train_labels.pt",
        "sentences": root / "cache" / "CUB_gpt55_sentence_embeds.pt",
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


def _eval_only_split(paths, test_cache, device, torch_module, scipy_io):
    """冻结路径不读 train label cache，只核对 xlsa17 的两个测试划分。"""
    res101 = scipy_io.loadmat(paths["res101"])
    splits = scipy_io.loadmat(paths["split"])
    labels = torch_module.from_numpy(res101["labels"].astype(int).squeeze() - 1).long()
    seen_indices = torch_module.from_numpy(splits["test_seen_loc"].squeeze() - 1).long()
    unseen_indices = torch_module.from_numpy(
        splits["test_unseen_loc"].squeeze() - 1
    ).long()
    if not torch_module.equal(labels[seen_indices], test_cache["seen_labels"].long()):
        raise ValueError("test_seen cache labels 与 xlsa17 不一致。")
    if not torch_module.equal(labels[unseen_indices], test_cache["unseen_labels"].long()):
        raise ValueError("test_unseen cache labels 与 xlsa17 不一致。")
    seen = torch_module.unique(labels[seen_indices], sorted=True)
    unseen = torch_module.unique(labels[unseen_indices], sorted=True)
    return seen.to(device), unseen.to(device)


def _metric_dict(values, *, epoch):
    seen, unseen, harmonic, zsl = values
    return {
        "U": float(unseen), "S": float(seen), "H": float(harmonic),
        "ZS": float(zsl), "epoch": int(epoch),
    }


def _write_metrics(output_dir, metrics, metadata):
    payload = dict(metadata)
    payload["metrics"] = metrics
    (output_dir / "metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _logger(output_dir):
    path = output_dir / "training.log"

    def log(message):
        text = str(message)
        print(text)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(text + "\n")

    return log


def _run_frozen_path(config, values, data_root, output_dir, runtime):
    torch = runtime.torch
    paths = _paths(data_root)
    sentences = _load_sentences(
        paths["sentences"], int(config.num_class), int(config.dim_f_clip), torch
    )
    test_cache = runtime.load_v5_test_cache(paths["cache"])
    seen, unseen = _eval_only_split(
        paths, test_cache, config.device, torch, runtime.scipy_io
    )
    text = sentences.mean(dim=1)
    model = runtime.build_score_path_model(
        "frozen_clip", config, seen, unseen, text[seen.cpu()], text[unseen.cpu()],
        sentences[seen.cpu()], initialization_seed=int(config.random_seed),
    ).to(config.device)
    with torch.inference_mode():
        values_out = runtime.evaluate_cached_v5(
            model, config.device, test_cache, seen, unseen
        )
    metrics = _metric_dict(values_out, epoch=0)
    runtime.log(
        f"冻结评估：S={metrics['S']*100:.2f}% U={metrics['U']*100:.2f}% "
        f"H={metrics['H']*100:.2f}% ZS={metrics['ZS']*100:.2f}%"
    )
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
    paths = _paths(data_root)
    train_cls, train_patches, train_labels = _load_training_cache(
        paths, int(config.dim_f_clip), torch
    )
    sentences = _load_sentences(
        paths["sentences"], int(config.num_class), int(config.dim_f_clip), torch
    )
    test_cache = runtime.load_v5_test_cache(paths["cache"])
    seen, unseen = runtime.load_v5_cub_split(
        paths["res101"], paths["split"], train_labels,
        test_cache["seen_labels"], test_cache["unseen_labels"], config.device,
    )
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
            losses["loss"].backward()
            optimizer.step()
            epoch_loss += float(losses["loss"].item())
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
            torch.save(model.state_dict(), output_dir / "best_model.pth")
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
    from tools.v5_evaluation import evaluate_cached_v5, load_v5_test_cache
    from tools.v5_runtime import sha256_file

    return SimpleNamespace(
        torch=torch, optim=optim, yaml=yaml, scipy_io=scipy_io,
        build_score_path_model=build_score_path_model,
        configure_reproducibility=configure_reproducibility,
        load_v5_cub_split=load_v5_cub_split,
        evaluate_cached_v5=evaluate_cached_v5,
        load_v5_test_cache=load_v5_test_cache,
        sha256_file=sha256_file, log=log,
    )


def main(argv=None):
    args = _parse_args(argv)
    output_candidate = args.output_dir.resolve()
    if output_candidate.exists():
        raise FileExistsError(f"output directory already exists: {output_candidate}")
    _require_clean_code_tree()
    code_commit = _current_code_commit()
    runtime = _load_runtime(lambda message: None)
    config, values, config_path = _load_config(args.config, runtime.yaml)
    _require_cuda(config, runtime.torch)
    output_dir = _reserve_output_dir(output_candidate)
    runtime.log = _logger(output_dir)
    shutil.copy2(config_path, output_dir / "config.yaml")
    runtime.configure_reproducibility(
        int(config.random_seed), strict_determinism=False, deterministic_warn_only=True
    )
    runtime.log(f"模板：{MODEL_TEMPLATE_ID}")
    runtime.log(f"代码 commit：{code_commit}")
    runtime.log(f"score_path：{config.score_path}")
    metrics = _dispatch_score_path(
        config, values, args.data_root, output_dir, runtime=runtime
    )
    metadata = {
        "template_id": MODEL_TEMPLATE_ID,
        "code_commit": code_commit,
        "config_sha256": runtime.sha256_file(config_path),
        "score_path": config.score_path,
        "random_seed": int(config.random_seed),
        "evaluation_only": config.score_path == "frozen_clip",
    }
    _write_metrics(output_dir, metrics, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
