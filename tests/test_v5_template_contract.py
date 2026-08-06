"""V5 干净代码母版的静态边界测试。"""

import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest

import torch

from model.MyModel import GTPJ
from tools.convert_v5_checkpoint import convert_state_dict


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


def _check_v5_config_contains_only_canonical_keys() -> None:
    version_text = VERSION_CONFIG.read_text(encoding="utf-8")
    experiment_text = EXPERIMENT_CONFIG.read_text(encoding="utf-8")

    for key in LEGACY_V5_KEYS:
        assert not re.search(rf"^{re.escape(key)}:\s*$", version_text, re.MULTILINE), key
        assert not re.search(rf"^{re.escape(key)}:\s*$", experiment_text, re.MULTILINE), key

    assert _top_level_keys(version_text) == CANONICAL_V5_KEYS
    assert experiment_text == version_text
    assert re.search(r"^local_weight:\s*\n\s+value:\s*0\.2\s*$", version_text, re.MULTILINE)
    assert re.search(r"^score_mode:\s*\n\s+value:\s*add\s*$", version_text, re.MULTILINE)


def _check_v5_model_source_has_only_the_fixed_canonical_path() -> None:
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


def _check_v5_training_entry_uses_only_canonical_names() -> None:
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
        "CUBDataLoader",
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


def _load_historical_v5_model_class():
    result = subprocess.run(
        ["git", "-C", str(ROOT), "show", "v5:model/MyModel.py"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    with tempfile.TemporaryDirectory(prefix="gtpj-v5-parity-") as temporary:
        source_path = Path(temporary) / "historical_v5_model.py"
        source_path.write_text(result.stdout, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("gtpj_historical_v5_model", source_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.GTPJ


def _parity_config() -> SimpleNamespace:
    return SimpleNamespace(
        num_class=6,
        dim_f_clip=16,
        pse_adapter_ratio=0.2,
        use_pse_self_attention=True,
        pse_apply_unseen=False,
        pse_heads=2,
        pse_dropout=0.0,
        pse_inner_ratio=0.35,
        pse_outer_ratio=0.65,
        tf_common_dim=8,
        tf_heads=2,
        tf_dropout=0.0,
        weight_s2v=0.5,
        local_weight=0.2,
        score_mode="add",
        pool_method="mean",
        fgvd_select_k=4,
        fgvd_select_sigma=0.0,
        fgvd_select_largest=True,
        fgvd_select_formula="v2_abs_mean",
        use_fgvd_geometry=True,
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic=True,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        use_icsa=True,
        icsa_ratio=0.008,
        bvsa_text_mode="conditional",
        icsa_hidden=8,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        use_sgmp=True,
        sgmp_context_mode="fgvd_main_memory",
        sgmp_text_mode="conditional",
        sgmp_topk=1,
        sgmp_hidden=8,
        lambda_mpp=0.05,
        lambda_neg=0.01,
        sgmp_neg_margin=0.2,
    )


def _assert_close(actual: torch.Tensor, expected: torch.Tensor) -> None:
    torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)


def _check_v5_clean_path_parity_with_historical_tag() -> None:
    historical_model_class = _load_historical_v5_model_class()
    config = _parity_config()
    torch.manual_seed(20260806)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    seen_text = torch.randn(4, 16)
    unseen_text = torch.randn(2, 16)
    seen_sentences = torch.randn(4, 3, 16)
    clip_features = torch.randn(2, 577, 16)
    labels = torch.tensor([0, 3])

    torch.manual_seed(17)
    historical_model = historical_model_class(
        config,
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )
    torch.manual_seed(17)
    clean_model = GTPJ(
        config,
        seen,
        unseen,
        seen_text,
        unseen_text,
        seen_sentence_embeds=seen_sentences,
    )

    converted_state, receipt = convert_state_dict(historical_model.state_dict())
    incompatible = clean_model.load_state_dict(converted_state, strict=True)
    assert incompatible.missing_keys == []
    assert incompatible.unexpected_keys == []
    assert {"gate_alpha", "gate_tau"}.issubset(set(receipt["dropped"]))

    historical_model.eval()
    clean_model.eval()
    with torch.no_grad():
        historical_eval = historical_model(clip_features, is_train=False)
        clean_eval = clean_model(clip_features, is_train=False)
    _assert_close(clean_eval["final_logits"], historical_eval["s_final"])
    _assert_close(clean_eval["global_logits"], historical_eval["s_global"])
    _assert_close(clean_eval["local_logits"], historical_eval["s_local"])

    historical_model.train()
    clean_model.train()
    torch.manual_seed(29)
    historical_train = historical_model(clip_features, is_train=True)
    historical_package = dict(historical_train, batch_label=labels)
    historical_loss = historical_model.compute_loss(historical_package)
    torch.manual_seed(29)
    clean_train = clean_model(clip_features, is_train=True)
    clean_package = dict(clean_train, batch_label=labels)
    clean_loss = clean_model.compute_loss(clean_package)

    _assert_close(clean_train["final_logits"], historical_train["s_final"])
    _assert_close(clean_train["global_logits"], historical_train["s_global"])
    _assert_close(clean_train["local_logits"], historical_train["s_local"])
    loss_pairs = {
        "loss": "loss",
        "loss_ce": "loss_CE",
        "loss_consist": "loss_consist",
        "loss_topo": "loss_topo",
        "loss_bmdd": "loss_bmdd",
        "loss_mpp": "loss_mpp",
        "loss_neg": "loss_neg",
    }
    for clean_key, historical_key in loss_pairs.items():
        _assert_close(clean_loss[clean_key], historical_loss[historical_key])

    historical_model.zero_grad(set_to_none=True)
    clean_model.zero_grad(set_to_none=True)
    historical_loss["loss"].backward()
    clean_loss["loss"].backward()
    gradient_pairs = {
        "pse_module.proj.weight": "clip_a_self_adapter.proj.weight",
        "bvsa_module.embed_cv.weight": "cross_tf.embed_cv.weight",
        "icsa_module.3.weight": "meta_net.3.weight",
        "sgmp_predictor.0.weight": "jepa_predictor.0.weight",
    }
    clean_parameters = dict(clean_model.named_parameters())
    historical_parameters = dict(historical_model.named_parameters())
    for clean_key, historical_key in gradient_pairs.items():
        clean_gradient = clean_parameters[clean_key].grad
        historical_gradient = historical_parameters[historical_key].grad
        assert clean_gradient is not None, clean_key
        assert historical_gradient is not None, historical_key
        _assert_close(clean_gradient, historical_gradient)


class V5TemplateContractTest(unittest.TestCase):
    def test_v5_config_contains_only_canonical_keys(self) -> None:
        _check_v5_config_contains_only_canonical_keys()

    def test_v5_model_source_has_only_the_fixed_canonical_path(self) -> None:
        _check_v5_model_source_has_only_the_fixed_canonical_path()

    def test_v5_training_entry_uses_only_canonical_names(self) -> None:
        _check_v5_training_entry_uses_only_canonical_names()

    def test_v5_clean_path_parity_with_historical_tag(self) -> None:
        _check_v5_clean_path_parity_with_historical_tag()


if __name__ == "__main__":
    unittest.main()
