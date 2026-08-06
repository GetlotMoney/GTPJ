import copy
import random
import tempfile
import unittest
from pathlib import Path

import numpy as np
import scipy.io as sio
import torch

from tools.reproducibility import (
    configure_reproducibility,
    make_batch_generator,
    reproducibility_state,
)
from tools.v5_runtime import (
    capture_rng_state,
    input_fingerprints,
    input_record,
    restore_rng_state,
    validate_resume_identity,
    validate_stable_input_records,
)
from tools.v5_cub_data import load_v5_cub_split


class ReproducibilityTest(unittest.TestCase):
    def test_batch_generator_replays_same_sampling_sequence(self):
        gen_a = make_batch_generator(True, 5)
        gen_b = make_batch_generator(True, 5)

        sample_a = torch.randperm(100, generator=gen_a)[:8]
        sample_b = torch.randperm(100, generator=gen_b)[:8]

        self.assertTrue(torch.equal(sample_a, sample_b))

    def test_batch_generator_is_independent_from_global_rng(self):
        gen_a = make_batch_generator(True, 5)
        gen_b = make_batch_generator(True, 5)

        _ = torch.rand(1024)
        sample_a = torch.randperm(100, generator=gen_a)[:8]

        _ = torch.rand(2048)
        sample_b = torch.randperm(100, generator=gen_b)[:8]

        self.assertTrue(torch.equal(sample_a, sample_b))

    def test_reproducibility_state_records_runtime_flags(self):
        state = configure_reproducibility(
            5,
            strict_determinism=False,
            deterministic_warn_only=True,
        )

        self.assertEqual(state["seed"], 5)
        self.assertFalse(state["strict_determinism"])
        self.assertFalse(state["cudnn_benchmark"])
        self.assertIn("torch_version", state)
        self.assertEqual(
            reproducibility_state(5, strict_determinism=False)["seed"],
            5,
        )

    def test_v5_resume_restores_same_cpu_training_trajectory(self):
        configure_reproducibility(
            17, strict_determinism=False, deterministic_warn_only=True
        )
        features = torch.arange(80, dtype=torch.float32).view(20, 4) / 80.0
        targets = torch.linspace(-1.0, 1.0, 20).view(-1, 1)

        def new_training_state():
            model = torch.nn.Sequential(
                torch.nn.Linear(4, 8),
                torch.nn.Dropout(p=0.25),
                torch.nn.Linear(8, 1),
            )
            optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
            scheduler = torch.optim.lr_scheduler.StepLR(
                optimizer, step_size=2, gamma=0.5
            )
            return model, optimizer, scheduler

        def step(model, optimizer, scheduler):
            indices = torch.randperm(len(features))[:6]
            scale = random.random() + float(np.random.rand())
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(
                model(features[indices]), targets[indices]
            ) * scale
            loss.backward()
            optimizer.step()
            scheduler.step()
            parameters = {
                name: value.detach().clone()
                for name, value in model.state_dict().items()
            }
            return loss.detach().clone(), parameters, scheduler.get_last_lr()

        continuous_model, continuous_optimizer, continuous_scheduler = (
            new_training_state()
        )
        step(continuous_model, continuous_optimizer, continuous_scheduler)
        step(continuous_model, continuous_optimizer, continuous_scheduler)
        checkpoint_model = copy.deepcopy(continuous_model.state_dict())
        checkpoint_optimizer = copy.deepcopy(continuous_optimizer.state_dict())
        checkpoint_scheduler = copy.deepcopy(continuous_scheduler.state_dict())
        checkpoint_rng = capture_rng_state()

        continuous_steps = [
            step(continuous_model, continuous_optimizer, continuous_scheduler)
            for _ in range(3)
        ]

        resumed_model, resumed_optimizer, resumed_scheduler = new_training_state()
        resumed_model.load_state_dict(checkpoint_model)
        resumed_optimizer.load_state_dict(checkpoint_optimizer)
        resumed_scheduler.load_state_dict(checkpoint_scheduler)
        restore_rng_state(checkpoint_rng)
        resumed_steps = [
            step(resumed_model, resumed_optimizer, resumed_scheduler)
            for _ in range(3)
        ]

        for continuous, resumed in zip(continuous_steps, resumed_steps):
            continuous_loss, continuous_parameters, continuous_lr = continuous
            resumed_loss, resumed_parameters, resumed_lr = resumed
            torch.testing.assert_close(continuous_loss, resumed_loss, rtol=0, atol=0)
            self.assertEqual(continuous_lr, resumed_lr)
            for name, value in continuous_parameters.items():
                torch.testing.assert_close(
                    value, resumed_parameters[name], rtol=0, atol=0
                )
        for name, value in continuous_model.state_dict().items():
            torch.testing.assert_close(
                value, resumed_model.state_dict()[name], rtol=0, atol=0
            )

    def test_v5_resume_identity_rejects_config_or_cache_change(self):
        checkpoint = {
            "template_id": "model/v5-template-v1",
            "code_commit": "abc123",
            "config": {"random_seed": 5},
            "config_sha256": "config-hash",
            "input_fingerprints": {"patch": {"sha256": "data-hash", "size_bytes": 4}},
            "seenclasses": [0, 2],
            "unseenclasses": [1, 3],
        }
        arguments = dict(
            template_id="model/v5-template-v1",
            code_commit="abc123",
            config_values={"random_seed": 5},
            config_sha256="config-hash",
            fingerprints={"patch": {"sha256": "data-hash", "size_bytes": 4}},
            seenclasses=[0, 2],
            unseenclasses=[1, 3],
        )
        validate_resume_identity(checkpoint, **arguments)

        for field, changed in (
            ("code_commit", "different-code"),
            ("config_sha256", "different-config"),
            ("fingerprints", {"patch": {"sha256": "different-data", "size_bytes": 4}}),
            ("seenclasses", [0, 3]),
        ):
            with self.subTest(field=field):
                rejected = dict(arguments)
                rejected[field] = changed
                with self.assertRaisesRegex(ValueError, "不一致"):
                    validate_resume_identity(checkpoint, **rejected)

    def test_v5_input_fingerprint_records_hash_and_size(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-input-") as temporary:
            path = Path(temporary) / "cache.pt"
            path.write_bytes(b"v5-cache")
            record = input_record(path, torch.zeros(2, 3, dtype=torch.float16))
            fingerprints = input_fingerprints({"cache": record})

            self.assertEqual(record["size_bytes"], 8)
            self.assertEqual(fingerprints["cache"]["sha256"], record["sha256"])
            self.assertEqual(fingerprints["cache"]["shape"], [2, 3])
            self.assertEqual(fingerprints["cache"]["dtype"], "torch.float16")
            self.assertNotIn("path", fingerprints["cache"])

    def test_v5_input_change_between_load_and_fingerprint_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-input-race-") as temporary:
            path = Path(temporary) / "cache.pt"
            torch.save(torch.tensor([1.0]), path)
            before = {"cache": input_record(path)}
            loaded = torch.load(path, map_location="cpu", weights_only=True)
            torch.save(torch.tensor([2.0]), path)
            after = {"cache": input_record(path, loaded)}

            with self.assertRaisesRegex(RuntimeError, "加载期间发生变化"):
                validate_stable_input_records(before, after)

    def test_v5_cub_split_uses_only_xlsa17_and_matches_cached_labels(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-split-") as temporary:
            root = Path(temporary)
            res101 = root / "res101.mat"
            splits = root / "att_splits.mat"
            sio.savemat(
                res101,
                {"labels": np.array([[1], [3], [1], [3], [2], [4]])},
            )
            sio.savemat(
                splits,
                {
                    "trainval_loc": np.array([[1], [2]]),
                    "test_seen_loc": np.array([[3], [4]]),
                    "test_unseen_loc": np.array([[5], [6]]),
                },
            )

            seen, unseen = load_v5_cub_split(
                res101,
                splits,
                torch.tensor([0, 2]),
                torch.tensor([0, 2]),
                torch.tensor([1, 3]),
                "cpu",
            )
            torch.testing.assert_close(seen, torch.tensor([0, 2]))
            torch.testing.assert_close(unseen, torch.tensor([1, 3]))

            with self.assertRaisesRegex(ValueError, "缓存标签"):
                load_v5_cub_split(
                    res101,
                    splits,
                    torch.tensor([2, 0]),
                    torch.tensor([0, 2]),
                    torch.tensor([1, 3]),
                    "cpu",
                )


if __name__ == "__main__":
    unittest.main()
