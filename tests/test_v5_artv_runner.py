from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import scipy.io as sio
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-022_artv"
sys.path.insert(0, str(MODULE_DIR))
SPEC = importlib.util.spec_from_file_location("v5_artv_evaluate", MODULE_DIR / "evaluate.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


def synthetic_x2_state(seed: int = 7) -> dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    attention = nn.MultiheadAttention(768, 4, dropout=0.5, batch_first=True)
    post = nn.Linear(768, 768)
    layer_norm = nn.LayerNorm(768)
    state = {
        f"legacy_attention.{name}": value.detach().clone()
        for name, value in attention.state_dict().items()
    }
    state.update(
        {f"post_projection.{name}": value.detach().clone() for name, value in post.state_dict().items()}
    )
    state.update(
        {f"layer_norm.{name}": value.detach().clone() for name, value in layer_norm.state_dict().items()}
    )
    state["logit_scale"] = torch.tensor(math.log(1.0 / 0.07))
    return state


class ARTVRunnerTest(unittest.TestCase):
    def test_frozen_config_contract(self):
        path = MODULE_DIR / "config.yaml"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        config, actual = RUNNER.load_config(path, digest)
        self.assertEqual(actual, digest)
        self.assertEqual(config["experiment_id"], "V5-INNOVATION-022")
        self.assertEqual(config["crop_scheme"], "deterministic_15")
        self.assertEqual(config["crops_per_scale"], [9, 5, 1])
        self.assertEqual(config["certificate_votes"], 5)
        self.assertFalse(config["formal_evidence"])
        self.assertEqual(
            config["class_order_sha256"],
            "7b6ffe26103bfeb73324f328fac499d6ea7cfadfb2b56448b0df295aca22df38",
        )
        self.assertEqual(
            config["expected_sha256"]["clip_weight"],
            "3035c92b350959924f9f00213499208652fc7ea050643e8b385c2dac08641f02",
        )
        self.assertEqual(
            config["official_image_content_sha256"],
            "66cfcc0407cf0b6012b0addcac2d74b644194d61b7da7e9a13ab8818d5460672",
        )
        self.assertEqual(
            config["role_anchor_tokens_sha256"],
            "ecfc07339502077cc79c7ac98cad421728b9e0957ec1299d2c76859c1ca22d8c",
        )
        self.assertEqual(
            config["runtime_identity"],
            {
                "torch_version": "2.5.1",
                "torch_cuda_version": "11.8",
                "torchvision_version": "0.20.1",
                "pillow_version": "12.2.0",
                "clip_package_sha256": "122109054be65c795609a37efc4e4ddd7c2321d58ab3b90c850974c52281d0ff",
                "preprocess_normalized_repr_sha256": "ce6af024b45c37520116f40908c942f1e564bb780eb0935cacca931448923e73",
            },
        )
        self.assertEqual(
            config["determinism"],
            {"enabled": True, "cublas_workspace_config": ":4096:8"},
        )

    def test_x2_reconstruction_ignores_qk_and_keeps_unseen_mean8(self):
        generator = torch.Generator().manual_seed(19)
        sentences = F.normalize(torch.randn(200, 8, 768, generator=generator), dim=-1)
        seen = torch.cat([torch.arange(0, 200, 2), torch.arange(1, 100, 2)]).sort().values
        state = synthetic_x2_state()
        state["sentence_embeds"] = F.normalize(sentences.float(), dim=-1)
        state["adapted_classes"] = seen.clone()
        alternate = {name: value.clone() for name, value in state.items()}
        alternate["legacy_attention.in_proj_weight"][: 2 * 768].normal_(100.0, 3.0)
        alternate["legacy_attention.in_proj_bias"][: 2 * 768].normal_(100.0, 3.0)
        config = {
            "x2_identity": {
                "code_commit": "a0ac9d8f82fef6022da5e823049b00760cd1fa2e",
                "best_epoch": 50,
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, model_state in enumerate((state, alternate)):
                path = Path(directory) / f"x2-{index}.pth"
                torch.save(
                    {
                        "model": model_state,
                        "config": {"conditions": {"PSE-X2": {"mode": "legacy_uniform"}}},
                        "code_commit": config["x2_identity"]["code_commit"],
                        "best_epoch": 50,
                    },
                    path,
                )
                paths.append(path)
            first, scale, _ = RUNNER.frozen_x2_from_checkpoint(
                sentences, seen, paths[0], config, torch.device("cpu")
            )
            second, _, _ = RUNNER.frozen_x2_from_checkpoint(
                sentences, seen, paths[1], config, torch.device("cpu")
            )
        unseen = torch.arange(200)[~torch.isin(torch.arange(200), seen)]
        expected_unseen = F.normalize(
            F.normalize(sentences, dim=-1).mean(dim=1), dim=-1
        ).index_select(0, unseen)
        self.assertTrue(torch.equal(first, second))
        self.assertTrue(torch.equal(first.index_select(0, unseen), expected_unseen))
        self.assertAlmostEqual(float(scale), 1.0 / 0.07, places=5)

    def test_class_order_verifier_reads_exact_names(self):
        names = [f"class_{index:03d}" for index in range(200)]
        serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
        config = {"class_order_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}
        raw = np.empty((200, 1), dtype=object)
        for index, name in enumerate(names):
            raw[index, 0] = name
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "att_splits.mat"
            sio.savemat(path, {"allclasses_names": raw})
            RUNNER.verify_class_order(config, path)
            config["class_order_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "class order"):
                RUNNER.verify_class_order(config, path)

    def test_crop_bank_is_deterministic_and_exactly_fifteen_square_regions(self):
        image = Image.new("RGB", (100, 80), color=(10, 20, 30))
        first = RUNNER.deterministic_crops(image)
        second = RUNNER.deterministic_crops(image)
        self.assertEqual(len(first), 15)
        self.assertEqual([crop.size for crop in first[:9]], [(40, 40)] * 9)
        self.assertEqual([crop.size for crop in first[9:14]], [(56, 56)] * 5)
        self.assertEqual(first[-1].size, (80, 80))
        for left, right in zip(first, second):
            self.assertEqual(left.tobytes(), right.tobytes())

    def test_ordered_image_digest_binds_content_and_position(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.jpg"
            second = Path(directory) / "second.jpg"
            first.write_bytes(b"first-image-bytes")
            second.write_bytes(b"second-image-bytes")
            baseline = RUNNER.ordered_image_content_sha256([first, second])
            self.assertEqual(baseline, RUNNER.ordered_image_content_sha256([first, second]))
            self.assertNotEqual(baseline, RUNNER.ordered_image_content_sha256([second, first]))
            second.write_bytes(b"changed-image-bytes")
            self.assertNotEqual(baseline, RUNNER.ordered_image_content_sha256([first, second]))

    def test_clip_package_digest_is_install_root_independent(self):
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / "left" / "clip", Path(directory) / "right" / "clip"]
            for root in roots:
                root.mkdir(parents=True)
                (root / "__init__.py").write_bytes(b"from .model import build\n")
                (root / "model.py").write_bytes(b"def build(): return 1\n")
                (root / "ignored.bin").write_bytes(b"not-python")
            (roots[0] / "vocab.gz").write_bytes(b"tokenizer-data")
            (roots[1] / "vocab.gz").write_bytes(b"tokenizer-data")
            left = RUNNER.clip_package_sha256(roots[0] / "__init__.py")
            right = RUNNER.clip_package_sha256(roots[1] / "__init__.py")
            self.assertEqual(left, right)
            (roots[1] / "model.py").write_bytes(b"def build(): return 2\n")
            self.assertNotEqual(left, RUNNER.clip_package_sha256(roots[1] / "__init__.py"))
            (roots[1] / "model.py").write_bytes(b"def build(): return 1\n")
            (roots[1] / "vocab.gz").write_bytes(b"changed-tokenizer-data")
            self.assertNotEqual(left, RUNNER.clip_package_sha256(roots[1] / "__init__.py"))

    def test_preprocess_signature_removes_only_process_address(self):
        class FakePreprocess:
            def __init__(self, address: str):
                self.address = address

            def __repr__(self) -> str:
                return f"Compose(<function convert at {self.address}>, Bicubic(336))"

        first = RUNNER.normalized_preprocess_repr(FakePreprocess("0x123abc"))
        second = RUNNER.normalized_preprocess_repr(FakePreprocess("0x9DEF00"))
        self.assertEqual(first, second)
        self.assertNotIn("0x", first)

    def test_role_token_digest_is_dtype_independent_but_order_sensitive(self):
        tokens = torch.arange(6 * 77, dtype=torch.int32).view(6, 77)
        baseline = RUNNER.role_token_sha256(tokens)
        self.assertEqual(baseline, RUNNER.role_token_sha256(tokens.long()))
        self.assertNotEqual(baseline, RUNNER.role_token_sha256(tokens.flip(0)))

    def test_metric_set_returns_zero_h_when_seen_and_unseen_are_both_zero(self):
        unseenclasses = torch.arange(150, 200)
        seen_labels = torch.arange(150)
        unseen_labels = unseenclasses.clone()
        seen_logits = torch.full((150, 200), -1.0)
        unseen_logits = torch.full((50, 200), -1.0)
        zs_logits = torch.full((50, 50), -1.0)
        seen_logits[torch.arange(150), (seen_labels + 1) % 150] = 1.0
        unseen_logits[torch.arange(50), (unseen_labels + 1) % 200] = 1.0
        zs_logits[torch.arange(50), (torch.arange(50) + 1) % 50] = 1.0
        values = RUNNER.metric_set(
            seen_logits,
            unseen_logits,
            zs_logits,
            seen_labels,
            unseen_labels,
            unseenclasses,
        )
        self.assertEqual(values, {"U": 0.0, "S": 0.0, "H": 0.0, "ZS": 0.0})

    def test_metric_and_change_diagnostics_use_global_class_ids(self):
        base = torch.tensor([[3.0, 2.0, 1.0], [1.0, 3.0, 2.0], [1.0, 2.0, 3.0]])
        variant = base.clone()
        variant[0, 0], variant[0, 1] = base[0, 1], base[0, 0]
        variant[1, 1], variant[1, 2] = base[1, 2], base[1, 1]
        labels = torch.tensor([1, 1, 0])
        values = RUNNER.change_diagnostics(base, variant, labels)
        self.assertEqual(values, {"changed": 2, "rescued": 1, "harmed": 1})


if __name__ == "__main__":
    unittest.main()
