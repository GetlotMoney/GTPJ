"""V5 干净代码母版的静态边界测试。"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
VERSION_CONFIG = ROOT / "config" / "versions" / "v5.yaml"
EXPERIMENT_CONFIG = ROOT / "experiments" / "v5" / "config.yaml"
MODEL_SOURCE = ROOT / "model" / "MyModel.py"
TRAINING_SOURCE = ROOT / "train_GTPJ_CUB.py"


LEGACY_V5_KEYS = {
    "adapter_ratio",
    "use_clip_a_self",
    "clip_a_self_apply_unseen",
    "clip_a_self_heads",
    "clip_a_self_dropout",
    "clip_a_self_inner_ratio",
    "clip_a_self_outer_ratio",
    "lastvit_select_k",
    "lastvit_select_sigma",
    "lastvit_select_largest",
    "lastvit_select_formula",
    "use_fae",
    "use_conditional_text",
    "conditional_text_ratio",
    "meta_net_hidden",
    "lambda_msdn",
    "use_ag_jepa",
    "jepa_context_mode",
    "jepa_text_mode",
    "jepa_topk",
    "jepa_hidden",
    "lambda_jepa",
    "lambda_jepa_neg",
    "jepa_neg_margin",
}

CANONICAL_V5_KEYS = {
    "dataset",
    "num_class",
    "dim_f_clip",
    "device",
    "batch_size",
    "epochs",
    "random_seed",
    "text_source",
    "pse_adapter_ratio",
    "use_pse_self_attention",
    "pse_apply_unseen",
    "pse_heads",
    "pse_dropout",
    "pse_inner_ratio",
    "pse_outer_ratio",
    "tf_common_dim",
    "tf_heads",
    "tf_dropout",
    "weight_s2v",
    "text_residual",
    "visual_residual",
    "local_weight",
    "pool_method",
    "fgvd_select_k",
    "fgvd_select_sigma",
    "fgvd_select_largest",
    "fgvd_select_formula",
    "score_mode",
    "use_fgvd_geometry",
    "lambda_consist",
    "consist_temp",
    "consist_dynamic",
    "consist_dynamic_gamma",
    "lambda_topo_pearson",
    "use_icsa",
    "icsa_ratio",
    "bvsa_text_mode",
    "icsa_hidden",
    "lambda_bmdd",
    "msdn_temp",
    "use_sgmp",
    "sgmp_context_mode",
    "sgmp_text_mode",
    "sgmp_topk",
    "sgmp_hidden",
    "lambda_mpp",
    "lambda_neg",
    "sgmp_neg_margin",
    "lr_stages",
}


def _top_level_keys(text: str) -> set[str]:
    return set(re.findall(r"^([a-zA-Z][a-zA-Z0-9_]*):\s*$", text, flags=re.MULTILINE))


def test_v5_config_contains_only_canonical_keys() -> None:
    version_text = VERSION_CONFIG.read_text(encoding="utf-8")
    experiment_text = EXPERIMENT_CONFIG.read_text(encoding="utf-8")

    for key in LEGACY_V5_KEYS:
        assert not re.search(rf"^{re.escape(key)}:\s*$", version_text, re.MULTILINE), key
        assert not re.search(rf"^{re.escape(key)}:\s*$", experiment_text, re.MULTILINE), key

    assert _top_level_keys(version_text) == CANONICAL_V5_KEYS
    assert experiment_text == version_text
    assert re.search(r"^local_weight:\s*\n\s+value:\s*0\.2\s*$", version_text, re.MULTILINE)
    assert re.search(r"^score_mode:\s*\n\s+value:\s*add\s*$", version_text, re.MULTILINE)


def test_v5_model_source_has_only_the_fixed_canonical_path() -> None:
    source = MODEL_SOURCE.read_text(encoding="utf-8")
    forbidden = {
        "_config_get",
        "CrossModalTransformer",
        "CLIPASelfAdapter",
        "use_ag_jepa",
        "jepa_",
        "lastvit_",
        "gate_alpha",
        "gate_tau",
        "use_dynamic_routing",
        "dynamic_routing",
        "DynamicRoutingGate",
    }
    for token in forbidden:
        assert token not in source, token

    required = {
        "SemanticPrototypeAdapter",
        "ProgressiveSemanticSelfAttention",
        "fgvd_select_patches",
        "BidirectionalVisualSemanticAlignment",
        "use_icsa",
        "use_sgmp",
        "local_weight",
    }
    for token in required:
        assert token in source, token

    assert re.search(
        r"final_logits\s*=\s*global_logits\s*\+\s*self\.local_weight\s*\*\s*local_logits",
        source,
    )


def test_v5_training_entry_uses_only_canonical_names() -> None:
    source = TRAINING_SOURCE.read_text(encoding="utf-8")
    forbidden = {
        "legacy_key",
        "pool_method == 'lastvit'",
        'pool_method == "lastvit"',
        "use_ag_jepa",
        "jepa_",
        "dynamic_route_stats",
    }
    for token in forbidden:
        assert token not in source, token

    for token in (
        "config",
        "random_seed",
        "DATA_LOADER",
        "seenclasses",
        "unseenclasses",
        "eval_zs_gzsl",
        "checkpoint",
        "best_metrics",
        "'U'",
        "'S'",
        "'H'",
        "'ZS'",
    ):
        assert token in source, token
