"""在不训练的情况下，核对修复版 V5 与老 V5 的同种子起点。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import torch
import yaml


HISTORICAL_COMMIT = "4b259379d99c1a791442ea9e2fac0bb22b2411a9"
TEMPLATE_COMMIT = "2f5fa5e631ef82658d4bac587cdfd17f3534cb35"
EXPECTED_PARAMETER_COUNT = 13_976_981
EXPECTED_CONFIG_SHA256 = "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"
EXPECTED_BRANCH = "exp/v5/confirmation/confirm-002-v5-seed-equivalence"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repository_root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_root), *args],
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _load_historical_model(repository_root: Path):
    """直接从固定 Git 提交读老模型，避免误读当前工作区里的文件。"""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "show",
            f"{HISTORICAL_COMMIT}:model/MyModel.py",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    module = ModuleType("gtpj_confirm_002_historical_model")
    module.__file__ = f"git:{HISTORICAL_COMMIT}:model/MyModel.py"
    exec(compile(result.stdout, module.__file__, "exec"), module.__dict__)
    return module.GTPJ


def _load_project_config(repository_root: Path) -> tuple[SimpleNamespace, str]:
    config_path = (
        repository_root
        / "experiments"
        / "v5"
        / "confirmation"
        / "CONFIRM-002_v5-seed-equivalence"
        / "config.yaml"
    )
    config_bytes = config_path.read_bytes()
    raw = yaml.safe_load(config_bytes.decode("utf-8"))
    values = {name: record["value"] for name, record in raw.items()}

    # 老代码仍保留许多兼容开关；这里把它们固定到干净 V5 唯一的活跃路线。
    values.update(
        pse_adapter_ratio=0.2,
        use_pse_self_attention=True,
        pse_apply_unseen=False,
        pool_method="mean",
        fgvd_select_sigma=0.0,
        fgvd_select_largest=True,
        fgvd_select_formula="v2_abs_mean",
        use_fgvd_geometry=True,
        use_icsa=True,
        bvsa_text_mode="conditional",
        use_sgmp=True,
        sgmp_context_mode="fgvd_main_memory",
        sgmp_text_mode="conditional",
        consist_dynamic=True,
    )
    return SimpleNamespace(**values), _sha256_bytes(config_bytes)


def _state_sha256(state: dict[str, torch.Tensor]) -> str:
    """把键名、形状、类型和数值一起做哈希，避免只比较参数数量。"""
    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _first_three_batches(rng_state: torch.Tensor) -> list[torch.Tensor]:
    generator = torch.Generator(device="cpu")
    generator.set_state(rng_state)
    return [torch.randperm(7057, generator=generator)[:64] for _ in range(3)]


def _batch_sha256(batch: torch.Tensor) -> str:
    return _sha256_bytes(batch.detach().cpu().contiguous().numpy().tobytes())


def run_probe(
    repository_root: Path,
    *,
    formal_candidate_commit: str = "",
) -> dict[str, object]:
    repository_root = repository_root.resolve()
    if str(repository_root) not in sys.path:
        sys.path.insert(0, str(repository_root))

    git_head = _git(repository_root, "rev-parse", "HEAD")
    git_branch = _git(repository_root, "branch", "--show-current")
    git_dirty = bool(_git(repository_root, "status", "--porcelain"))
    merge_base = _git(repository_root, "merge-base", git_head, TEMPLATE_COMMIT)
    candidate_model_path = repository_root / "model" / "MyModel.py"
    candidate_config_path = (
        repository_root
        / "experiments"
        / "v5"
        / "confirmation"
        / "CONFIRM-002_v5-seed-equivalence"
        / "config.yaml"
    )
    candidate_model_sha256 = _sha256_bytes(candidate_model_path.read_bytes())
    worktree_model_blob = _git(repository_root, "hash-object", "model/MyModel.py")
    head_model_blob = _git(
        repository_root,
        "rev-parse",
        "HEAD:model/MyModel.py",
        check=False,
    )
    worktree_config_blob = _git(
        repository_root,
        "hash-object",
        str(candidate_config_path.relative_to(repository_root)),
    )
    head_config_blob = _git(
        repository_root,
        "rev-parse",
        "HEAD:experiments/v5/confirmation/CONFIRM-002_v5-seed-equivalence/config.yaml",
        check=False,
    )
    formal_check_requested = bool(formal_candidate_commit)
    formal_candidate_identity_ok = (
        bool(re.fullmatch(r"[0-9a-f]{40}", formal_candidate_commit))
        and git_head == formal_candidate_commit
        and git_branch == EXPECTED_BRANCH
        and not git_dirty
        and merge_base == TEMPLATE_COMMIT
        and worktree_model_blob == head_model_blob
        and worktree_config_blob == head_config_blob
    ) if formal_check_requested else None

    # 在加入项目路径后再导入，确保读到的就是候选分支代码。
    from model.MyModel import GTPJ as CleanGTPJ
    from tools.convert_v5_checkpoint import convert_state_dict

    historical_model_class = _load_historical_model(repository_root)
    config, config_sha256 = _load_project_config(repository_root)

    # 这些是假数据，只用于创建模型；探针不会读 CUB，也不会进入 forward 或训练。
    torch.manual_seed(20260808)
    seen = torch.arange(150)
    unseen = torch.arange(150, 200)
    seen_text = torch.randn(150, 768)
    unseen_text = torch.randn(50, 768)
    seen_sentences = torch.randn(150, 7, 768)

    torch.manual_seed(5)
    historical_model = historical_model_class(
        config,
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )
    historical_cpu_rng = torch.get_rng_state().clone()
    historical_cuda_rng = (
        [item.clone() for item in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available()
        else []
    )

    torch.manual_seed(5)
    clean_model = CleanGTPJ(
        config,
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )
    clean_cpu_rng = torch.get_rng_state().clone()
    clean_cuda_rng = (
        [item.clone() for item in torch.cuda.get_rng_state_all()]
        if torch.cuda.is_available()
        else []
    )

    converted_historical_state, _ = convert_state_dict(
        historical_model.state_dict(), clean_model.state_dict()
    )
    clean_state = clean_model.state_dict()
    missing_state_keys = sorted(set(clean_state) - set(converted_historical_state))
    extra_state_keys = sorted(set(converted_historical_state) - set(clean_state))
    mismatches = [
        name
        for name in sorted(set(clean_state) & set(converted_historical_state))
        if not torch.equal(clean_state[name], converted_historical_state[name])
    ]
    mismatches.extend(f"missing:{name}" for name in missing_state_keys)
    mismatches.extend(f"extra:{name}" for name in extra_state_keys)

    historical_batches = _first_three_batches(historical_cpu_rng)
    clean_batches = _first_three_batches(clean_cpu_rng)
    batches_equal = all(
        torch.equal(clean_batch, historical_batch)
        for clean_batch, historical_batch in zip(clean_batches, historical_batches)
    )
    cuda_rng_equal = len(clean_cuda_rng) == len(historical_cuda_rng) and all(
        torch.equal(clean_item, historical_item)
        for clean_item, historical_item in zip(clean_cuda_rng, historical_cuda_rng)
    )

    parameter_names = list(dict(clean_model.named_parameters()))
    dead_names_present = any(
        "proj_visual" in name or "proj_text" in name for name in parameter_names
    )
    parameter_count = sum(parameter.numel() for parameter in clean_model.parameters())
    cpu_rng_equal = torch.equal(clean_cpu_rng, historical_cpu_rng)

    payload: dict[str, object] = {
        "schema_version": "gtpj.v5.seed_equivalence_probe/v1",
        "status": "PASS",
        "historical_commit": HISTORICAL_COMMIT,
        "template_commit": TEMPLATE_COMMIT,
        "git_head": git_head,
        "git_branch": git_branch,
        "git_dirty": git_dirty,
        "template_merge_base": merge_base,
        "formal_candidate_check_requested": formal_check_requested,
        "formal_candidate_commit": formal_candidate_commit,
        "formal_candidate_identity_ok": formal_candidate_identity_ok,
        "candidate_model_sha256": candidate_model_sha256,
        "candidate_model_matches_head": worktree_model_blob == head_model_blob,
        "candidate_config_matches_head": worktree_config_blob == head_config_blob,
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "dimensions": {"dim_com": int(config.tf_common_dim), "dim_f": int(config.dim_f_clip)},
        "seed": 5,
        "config_sha256": config_sha256,
        "config_matches_expected_sha256": config_sha256 == EXPECTED_CONFIG_SHA256,
        "active_state_mismatches": mismatches,
        "clean_active_state_sha256": _state_sha256(clean_state),
        "historical_active_state_sha256": _state_sha256(converted_historical_state),
        "post_model_cpu_rng_equal": cpu_rng_equal,
        "post_model_cpu_rng_sha256": _sha256_bytes(clean_cpu_rng.numpy().tobytes()),
        "post_model_cuda_rng_equal": cuda_rng_equal,
        "first_three_batches_equal": batches_equal,
        "first_three_batch_sha256": [_batch_sha256(batch) for batch in clean_batches],
        "dead_parameter_names_present": dead_names_present,
        "clean_parameter_count": parameter_count,
    }
    gates = (
        not mismatches,
        cpu_rng_equal,
        cuda_rng_equal,
        batches_equal,
        not dead_names_present,
        parameter_count == EXPECTED_PARAMETER_COUNT,
        config_sha256 == EXPECTED_CONFIG_SHA256,
    )
    if formal_check_requested:
        gates += (
            formal_candidate_identity_ok is True,
            torch.cuda.is_available(),
            torch.cuda.device_count() > 0,
        )
    if not all(gates):
        payload["status"] = "BLOCK"
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="核对修复版 V5 与历史 V5 的同 seed 初始化，不启动训练。"
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[4],
        help="GTPJ 仓库根目录；默认从本脚本位置向上推导。",
    )
    parser.add_argument(
        "--formal-candidate-commit",
        default="",
        help=(
            "正式服务器检查时必填的40位候选提交；填写后还会要求分支正确、"
            "工作树干净，并确认模型和配置都来自该提交。"
        ),
    )
    args = parser.parse_args()
    payload = run_probe(
        args.repository_root,
        formal_candidate_commit=args.formal_candidate_commit,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
