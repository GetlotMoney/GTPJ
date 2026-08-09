"""V5 PSE 在未见类上的共享应用边界。"""

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

from model.MyModel import GTPJ
from tools import v5_runtime


def _config(apply_unseen: bool) -> SimpleNamespace:
    return SimpleNamespace(
        num_class=6,
        dim_f_clip=16,
        use_pse_self_attention=True,
        pse_apply_unseen=apply_unseen,
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


def _inputs():
    torch.manual_seed(20260809)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    seen_sentences = torch.randn(4, 3, 16)
    unseen_sentences = torch.randn(2, 3, 16)
    seen_text = seen_sentences.mean(dim=1)
    unseen_text = unseen_sentences.mean(dim=1)
    return seen, unseen, seen_text, unseen_text, seen_sentences, unseen_sentences


class _RecordingPSE(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.class_counts = []

    def forward(self, sentences):
        self.class_counts.append(sentences.size(0))
        weights = torch.arange(
            1,
            sentences.size(1) + 1,
            device=sentences.device,
            dtype=sentences.dtype,
        ).view(1, -1, 1)
        return sentences * weights


class TestPSESharedUnseen(unittest.TestCase):
    def test_seen_only_keeps_original_unseen_prototypes(self):
        seen, unseen, seen_text, unseen_text, seen_sentences, _ = _inputs()
        model = GTPJ(
            _config(False),
            seen,
            unseen,
            seen_text,
            unseen_text,
            seen_sentence_embeds=seen_sentences,
        )

        torch.testing.assert_close(
            model.get_adapted_unseen_text(),
            torch.nn.functional.normalize(unseen_text, dim=1),
        )

    def test_shared_pse_is_seen_trained_and_eval_applied_to_unseen(self):
        seen, unseen, seen_text, unseen_text, seen_sentences, unseen_sentences = _inputs()
        model = GTPJ(
            _config(True),
            seen,
            unseen,
            seen_text,
            unseen_text,
            seen_sentence_embeds=seen_sentences,
            unseen_sentence_embeds=unseen_sentences,
        )
        recorder = _RecordingPSE()
        model.pse_module = recorder
        features = torch.randn(1, 577, 16)

        model.train()
        model(features, is_train=True)
        self.assertEqual(recorder.class_counts, [seen.numel()])

        recorder.class_counts.clear()
        model.eval()
        with torch.no_grad():
            model(features, is_train=False)
        self.assertEqual(recorder.class_counts, [seen.numel(), unseen.numel()])
        self.assertFalse(
            torch.allclose(
                model.get_adapted_unseen_text(),
                torch.nn.functional.normalize(unseen_text, dim=1),
            )
        )

    def test_shared_pse_requires_unseen_sentence_embeddings(self):
        seen, unseen, seen_text, unseen_text, seen_sentences, _ = _inputs()
        with self.assertRaisesRegex(ValueError, "requires unseen_sentence_embeds"):
            GTPJ(
                _config(True),
                seen,
                unseen,
                seen_text,
                unseen_text,
                seen_sentence_embeds=seen_sentences,
            )

    def test_large_data_hash_is_reused_until_file_identity_changes(self):
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
