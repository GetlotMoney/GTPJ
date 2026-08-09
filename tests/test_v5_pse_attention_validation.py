"""Targeted checks for V5-ABLATION-012."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import torch

from model.MyModel import (
    ProgressiveSemanticSelfAttention,
    cancel_pse_qk_weight_decay,
)
from tools import v5_runtime


class PSEAttentionValidationTest(unittest.TestCase):
    def test_learned_mode_preserves_original_forward(self) -> None:
        torch.manual_seed(5)
        module = ProgressiveSemanticSelfAttention(
            dim=8,
            heads=2,
            dropout=0.0,
            inner_ratio=0.35,
            attention_mode="learned",
        ).eval()
        x = torch.randn(3, 7, 8)
        with torch.no_grad():
            attention, _ = module.attn(x, x, x, need_weights=False)
            projected = module.dropout(module.proj(attention))
            expected = module.layer_norm(
                2.0 * (0.35 * projected + 0.65 * x)
            )
            actual = module(x)
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)

    def test_uniform_mode_is_independent_of_q_and_k(self) -> None:
        torch.manual_seed(17)
        module = ProgressiveSemanticSelfAttention(
            dim=8,
            heads=2,
            dropout=0.0,
            inner_ratio=0.35,
            attention_mode="uniform",
        ).eval()
        x = torch.randn(3, 7, 8)
        with torch.no_grad():
            before = module(x)
            module.attn.in_proj_weight[:16].normal_(mean=100.0, std=20.0)
            module.attn.in_proj_bias[:16].normal_(mean=-100.0, std=20.0)
            after = module(x)
        torch.testing.assert_close(after, before, rtol=0, atol=0)
        diagnostics = module.diagnostics(x)
        self.assertEqual(diagnostics["normalized_attention_entropy"], 1.0)
        self.assertAlmostEqual(
            diagnostics["mean_max_attention_weight"], 1.0 / 7.0
        )

    def test_qk_decay_cancellation_keeps_only_qk_unchanged(self) -> None:
        module = ProgressiveSemanticSelfAttention(
            dim=4,
            heads=1,
            dropout=0.0,
            attention_mode="learned",
        )
        with torch.no_grad():
            module.attn.in_proj_weight.fill_(0.5)
            module.attn.in_proj_bias.fill_(0.5)
        for parameter in module.parameters():
            parameter.grad = torch.zeros_like(parameter)
        optimizer = torch.optim.Adam(module.parameters(), lr=0.01, weight_decay=0.1)
        weight_before = module.attn.in_proj_weight.detach().clone()
        bias_before = module.attn.in_proj_bias.detach().clone()

        cancel_pse_qk_weight_decay(module, weight_decay=0.1)
        optimizer.step()

        torch.testing.assert_close(
            module.attn.in_proj_weight[:8], weight_before[:8], rtol=0, atol=0
        )
        torch.testing.assert_close(
            module.attn.in_proj_bias[:8], bias_before[:8], rtol=0, atol=0
        )
        self.assertFalse(
            torch.equal(module.attn.in_proj_weight[8:], weight_before[8:])
        )
        self.assertFalse(torch.equal(module.attn.in_proj_bias[8:], bias_before[8:]))

    def test_data_hash_is_reused_until_file_identity_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gtpj-pse-fingerprint-") as temporary:
            root = Path(temporary)
            data_path = root / "cache.pt"
            manifest_path = root / "manifest.json"
            data_path.write_bytes(b"first-v5-cache")
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "files": {str(data_path.resolve()): "broken-entry"},
                    }
                ),
                encoding="utf-8",
            )
            original_hash = v5_runtime.sha256_file
            with mock.patch.object(
                v5_runtime, "DATA_FINGERPRINT_MANIFEST", manifest_path
            ), mock.patch.object(
                v5_runtime, "sha256_file", wraps=original_hash
            ) as hash_call:
                first = v5_runtime.input_record(data_path)
                second = v5_runtime.input_record(data_path)
                self.assertEqual(first["sha256"], second["sha256"])
                self.assertEqual(hash_call.call_count, 1)

                data_path.write_bytes(b"changed-v5-data")
                third = v5_runtime.input_record(data_path)
                self.assertNotEqual(first["sha256"], third["sha256"])
                self.assertEqual(hash_call.call_count, 2)
                self.assertTrue(manifest_path.is_file())


if __name__ == "__main__":
    unittest.main()
