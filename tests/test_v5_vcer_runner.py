from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import scipy.io as sio
import torch
import torch.nn as nn
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "experiments" / "v5" / "innovation" / "INNOVATION-017_vcer"
SPEC = importlib.util.spec_from_file_location("v5_vcer_train", MODULE_DIR / "train.py")
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
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


class VCERRunnerTest(unittest.TestCase):
    def test_frozen_config_is_machine_readable_and_owner_direct(self):
        path = MODULE_DIR / "config.yaml"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        config, actual = RUNNER.load_config(path, digest)
        self.assertEqual(actual, digest)
        self.assertEqual(config["official_test_policy"], "direct_after_fixed_checkpoint_owner_20260816")
        self.assertEqual(sum(stage["epochs"] for stage in config["lr_stages"]), 50)
        self.assertEqual(config["role_shuffle_permutation"], [1, 2, 3, 4, 5, 0])
        self.assertEqual(
            config["class_order_sha256"],
            "7b6ffe26103bfeb73324f328fac499d6ea7cfadfb2b56448b0df295aca22df38",
        )

    def test_class_order_verifier_uses_exact_serialized_names(self):
        names = [f"class_{index:03d}" for index in range(200)]
        serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
        config = {"class_order_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest()}
        raw_names = np.empty((200, 1), dtype=object)
        for index, name in enumerate(names):
            raw_names[index, 0] = name
        with tempfile.TemporaryDirectory() as directory:
            split_path = Path(directory) / "att_splits.mat"
            sio.savemat(split_path, {"allclasses_names": raw_names})
            RUNNER.verify_class_order(config, split_path)
            config["class_order_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "class order"):
                RUNNER.verify_class_order(config, split_path)

    def test_x2_reconstruction_is_uniform_qk_invariant_and_preserves_unseen_mean8(self):
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
            first, scale, diagnostics = RUNNER.frozen_x2_from_checkpoint(
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
        self.assertTrue(torch.allclose(first.norm(dim=-1), torch.ones(200), atol=1e-6))
        self.assertAlmostEqual(float(scale), 1.0 / 0.07, places=5)
        self.assertEqual(diagnostics["checkpoint_best_epoch"], 50)

    def test_metrics_use_global_200_class_ids_and_unseen_only_zs(self):
        seenclasses = torch.tensor([0, 2])
        unseenclasses = torch.tensor([1, 3])
        seen_labels = torch.tensor([0, 0, 2, 2])
        unseen_labels = torch.tensor([1, 1, 3, 3])
        seen_logits = torch.tensor(
            [[4.0, 0.0, 1.0, 0.0], [4.0, 0.0, 1.0, 0.0], [0.0, 0.0, 4.0, 0.0], [0.0, 0.0, 4.0, 0.0]]
        )
        unseen_logits = torch.tensor(
            [[5.0, 4.0, 0.0, 1.0], [5.0, 4.0, 0.0, 1.0], [0.0, 1.0, 5.0, 4.0], [0.0, 1.0, 5.0, 4.0]]
        )
        metrics = RUNNER.metrics_from_logits(
            seen_logits,
            unseen_logits,
            seen_labels,
            unseen_labels,
            seenclasses,
            unseenclasses,
        )
        self.assertEqual(metrics["S"], 100.0)
        self.assertEqual(metrics["U"], 0.0)
        self.assertEqual(metrics["H"], 0.0)
        self.assertEqual(metrics["ZS"], 100.0)

    def test_output_inside_git_worktree_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            RUNNER.verify_output_boundary(ROOT / "forbidden-run-output")


if __name__ == "__main__":
    unittest.main()
