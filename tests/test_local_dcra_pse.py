from __future__ import annotations

import importlib.util
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-013_shared_pse_global8"
    / "train.py"
)
CONFIG_PATH = TRAIN_PATH.with_name("config.yaml")
SPEC = importlib.util.spec_from_file_location("local_dcra_train", TRAIN_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def make_inputs():
    generator = torch.Generator().manual_seed(1705)
    sentences = torch.randn(200, 8, 768, generator=generator)
    classes = torch.arange(150)
    centroids = torch.randn(150, 768, generator=generator)
    return sentences, classes, centroids


def make_model(
    mode: str, dcra_mix: float = 0.2, dropout: float = 0.0, value_heads: int = 4
):
    sentences, classes, centroids = make_inputs()
    return MODULE.StrongRolePSE(
        sentences,
        classes,
        centroids,
        mode=mode,
        dropout=dropout,
        inner_ratio=0.35,
        outer_ratio=0.65,
        dcra_mix=dcra_mix,
        temperature=0.05,
        value_heads=value_heads,
    )


def test_dcra_weights_are_normalized_bounded_and_never_self_rivals():
    model = make_model("dcra")
    _, diagnostics = model.prototypes(return_diagnostics=True)
    weights = diagnostics["role_weights"]
    rivals = diagnostics["rival_class_ids"]
    assert torch.allclose(weights.sum(dim=1), torch.ones(150), atol=1e-6)
    assert float(weights.min().detach()) >= 0.1 - 1e-6
    assert float(weights.max().detach()) <= 0.3 + 1e-6
    assert not (rivals == torch.arange(150).view(-1, 1)).any()


def test_dcra_zero_mix_exactly_reduces_to_uniform_and_unseen_stays_mean8():
    uniform = make_model("uniform")
    dcra_zero = make_model("dcra", dcra_mix=0.0)
    dcra_zero.load_state_dict(uniform.state_dict(), strict=False)
    uniform.eval()
    dcra_zero.eval()
    assert torch.allclose(uniform.prototypes(), dcra_zero.prototypes(), atol=1e-6)
    assert torch.equal(
        uniform.prototypes()[150:], uniform.base_prototypes()[150:]
    )


def test_base_and_role_components_reconstruct_logits():
    model = make_model("dcra")
    model.eval()
    images = torch.randn(3, 768, generator=torch.Generator().manual_seed(9))
    base, roles = model.logit_components(images)
    assert torch.allclose(base + roles.sum(dim=-1), model.logits(images), atol=2e-5)


def test_topology_and_ce_reach_strong_value_path_but_not_centroids():
    model = make_model("dcra")
    images = torch.randn(4, 768, generator=torch.Generator().manual_seed(11))
    targets = torch.tensor([0, 1, 2, 3])
    loss = torch.nn.functional.cross_entropy(model.logits(images, torch.arange(150)), targets)
    loss = loss + 0.1 * model.topology_loss()
    loss.backward()
    assert model.value_projection.weight.grad is not None
    assert float(model.value_projection.weight.grad.abs().sum()) > 0.0
    assert model.visual_centroids.grad is None


def test_visual_centroids_use_only_supplied_training_indices():
    features = torch.eye(6, 768)
    labels = torch.tensor([0, 0, 1, 1, 0, 1])
    centroids = MODULE.frozen_visual_centroids(
        features, labels, torch.tensor([0, 2]), torch.tensor([0, 1])
    )
    assert torch.equal(centroids[0], features[0])
    assert torch.equal(centroids[1], features[2])


class ReferenceLegacyUniform(torch.nn.Module):
    """Independent transcription of the reviewed ABLATION-012 PSE path."""

    def __init__(self, dropout: float):
        super().__init__()
        self.attn = torch.nn.MultiheadAttention(
            embed_dim=768, num_heads=4, dropout=dropout, batch_first=True
        )
        self.proj = torch.nn.Linear(768, 768)
        self.dropout = torch.nn.Dropout(dropout)
        self.layer_norm = torch.nn.LayerNorm(768)

    def forward(self, x):
        batch, tokens, dim = x.shape
        heads = self.attn.num_heads
        head_dim = dim // heads
        _, _, value_weight = self.attn.in_proj_weight.chunk(3, dim=0)
        _, _, value_bias = self.attn.in_proj_bias.chunk(3, dim=0)
        value = torch.nn.functional.linear(x, value_weight, value_bias)
        value = value.view(batch, tokens, heads, head_dim).transpose(1, 2)
        weights = x.new_full((batch, heads, tokens, tokens), 1.0 / tokens)
        weights = torch.nn.functional.dropout(
            weights, p=float(self.attn.dropout), training=self.training
        )
        context = torch.matmul(weights, value)
        context = context.transpose(1, 2).contiguous().view(batch, tokens, dim)
        attention_output = torch.nn.functional.linear(
            context, self.attn.out_proj.weight, self.attn.out_proj.bias
        )
        attention_output = self.dropout(self.proj(attention_output))
        mixed = 0.35 * attention_output + 0.65 * x
        return self.layer_norm(2.0 * mixed)


def test_legacy_uniform_matches_production_path_in_train_and_eval():
    sentences, _, _ = make_inputs()
    torch.manual_seed(31)
    model = make_model("legacy_uniform", dropout=0.5)
    torch.manual_seed(31)
    reference = ReferenceLegacyUniform(dropout=0.5)
    seen_sentences = torch.nn.functional.normalize(sentences[:150], dim=-1)

    model.eval()
    reference.eval()
    assert torch.allclose(
        model.transformed_roles(), reference(seen_sentences), atol=2e-6
    )

    model.train()
    reference.train()
    torch.manual_seed(1705)
    actual = model.transformed_roles()
    torch.manual_seed(1705)
    expected = reference(seen_sentences)
    assert torch.equal(actual, expected)


def test_legacy_uniform_only_transforms_seen_and_keeps_mean8_unseen():
    model = make_model("legacy_uniform", dropout=0.0)
    model.eval()
    assert model.transformed_roles().shape == (150, 8, 768)
    expected_unseen = model.base_prototypes()[150:]
    assert torch.equal(model.prototypes()[150:], expected_unseen)


def test_legacy_uniform_gradients_reach_value_not_query_or_key():
    model = make_model("legacy_uniform", dropout=0.0)
    images = torch.randn(4, 768, generator=torch.Generator().manual_seed(41))
    loss = torch.nn.functional.cross_entropy(
        model.logits(images, torch.arange(150)), torch.tensor([0, 1, 2, 3])
    )
    loss.backward()
    q_grad, k_grad, v_grad = model.legacy_attention.in_proj_weight.grad.chunk(3, dim=0)
    assert torch.count_nonzero(q_grad) == 0
    assert torch.count_nonzero(k_grad) == 0
    assert float(v_grad.abs().sum()) > 0.0


def test_tg_vpr_starts_group_equal_and_preserves_unseen_mean8():
    model = make_model("tg_vpr", dropout=0.0)
    model.eval()
    expected_groups = torch.full((3,), 1.0 / 3.0)
    assert torch.allclose(model.semantic_group_weights(), expected_groups)

    _, diagnostics = model.prototypes(return_diagnostics=True)
    assert model.transformed_roles().shape == (150, 3, 768)
    assert torch.allclose(diagnostics["role_weights"][0], expected_groups)
    group_vectors = model.semantic_group_vectors()
    assert torch.allclose(group_vectors.norm(dim=-1), torch.ones(200, 3), atol=1e-6)
    assert torch.equal(model.prototypes()[150:], model.base_prototypes()[150:])


def test_tg_vpr_group_weights_and_value_path_receive_gradient_but_qk_do_not():
    model = make_model("tg_vpr", dropout=0.0)
    images = torch.randn(4, 768, generator=torch.Generator().manual_seed(43))
    loss = torch.nn.functional.cross_entropy(
        model.logits(images, torch.arange(150)), torch.tensor([0, 1, 2, 3])
    )
    loss = loss + 0.1 * model.topology_loss()
    loss.backward()
    assert model.semantic_group_logits.grad is not None
    assert float(model.semantic_group_logits.grad.abs().sum()) > 0.0
    assert not hasattr(model, "legacy_attention")
    assert model.tg_value_projection.weight.grad is not None
    assert float(model.tg_value_projection.weight.grad.abs().sum()) > 0.0


def test_tg_vpr_group_weights_change_the_shared_value_context():
    model = make_model("tg_vpr", dropout=0.0)
    model.eval()
    baseline = model.transformed_roles().detach().clone()
    with torch.no_grad():
        model.semantic_group_logits.copy_(torch.tensor([2.0, -1.0, -1.0]))
    changed = model.transformed_roles().detach()
    assert not torch.allclose(baseline, changed)


def test_tg_vpr_supported_head_counts_preserve_shapes_and_qk_free_path():
    for heads in (1, 3, 4, 8):
        model = make_model("tg_vpr", dropout=0.0, value_heads=heads)
        model.eval()
        assert model.value_heads == heads
        assert model.transformed_roles().shape == (150, 3, 768)
        assert model.prototypes().shape == (200, 768)
        assert not hasattr(model, "legacy_attention")


def test_tg_vpr_rejects_head_count_that_does_not_divide_768():
    try:
        make_model("tg_vpr", value_heads=5)
    except ValueError as exc:
        assert "positive divisor of 768" in str(exc)
    else:
        raise AssertionError("value_heads=5 must be rejected")


def test_tg_vpr_rejects_non_integer_head_count():
    try:
        make_model("tg_vpr", value_heads=3.5)
    except ValueError as exc:
        assert "must be an integer" in str(exc)
    else:
        raise AssertionError("value_heads=3.5 must be rejected")


def test_checkpoint_is_self_describing_for_head_variant():
    model = make_model("tg_vpr", value_heads=3)
    payload = MODULE.build_checkpoint(
        model,
        {"conditions": {"TG-VPR-H3": {"value_heads": 3}}},
        "a" * 40,
        50,
        "RUN-008",
        "TG-VPR-H3",
        5,
    )
    assert payload["run_id"] == "RUN-008"
    assert payload["condition"] == "TG-VPR-H3"
    assert payload["value_heads"] == 3
    assert payload["best_epoch"] == 50
    assert payload["seed"] == 5


def test_modified_config_hash_and_frozen_tg_vpr_condition_load():
    config, digest = MODULE.load_config(CONFIG_PATH)
    assert digest == MODULE.EXPECTED_CONFIG_SHA256
    assert config["conditions"]["TG-VPR"] == {
        "run_id": "RUN-006",
        "mode": "tg_vpr",
        "value_heads": 4,
        "topology_weight": 0.1,
        "training_protocol": "full_seen_fixed_epoch50_legacy_sampling",
    }
    assert [config["conditions"][name]["value_heads"] for name in (
        "TG-VPR-H1", "TG-VPR-H3", "TG-VPR-H8"
    )] == [1, 3, 8]
    assert [config["conditions"][name]["seed"] for name in (
        "TG-VPR-H1-S6", "TG-VPR-H1-S7", "TG-VPR-H1-S8"
    )] == [6, 7, 8]


def test_full_seen_batch_schedule_is_independent_of_model_rng_consumption():
    first_generator = torch.Generator(device="cpu").manual_seed(5)
    second_generator = torch.Generator(device="cpu").manual_seed(5)
    first_schedule = [
        MODULE.legacy_batch_indices(7057, 64, first_generator) for _ in range(12)
    ]
    torch.manual_seed(999)
    _ = torch.randn(10000)
    second_schedule = [
        MODULE.legacy_batch_indices(7057, 64, second_generator) for _ in range(12)
    ]
    assert all(
        torch.equal(first, second)
        for first, second in zip(first_schedule, second_schedule, strict=True)
    )


def test_multi_seed_conditions_change_initialization_and_batch_schedule():
    torch.manual_seed(6)
    model_s6 = make_model("tg_vpr", value_heads=1)
    torch.manual_seed(7)
    model_s7 = make_model("tg_vpr", value_heads=1)
    assert not torch.equal(
        model_s6.tg_value_projection.weight,
        model_s7.tg_value_projection.weight,
    )
    batch_s6 = MODULE.legacy_batch_indices(
        7057, 64, torch.Generator(device="cpu").manual_seed(6)
    )
    batch_s7 = MODULE.legacy_batch_indices(
        7057, 64, torch.Generator(device="cpu").manual_seed(7)
    )
    assert not torch.equal(batch_s6, batch_s7)
