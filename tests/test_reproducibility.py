import copy
import hashlib
import json
import os
import random
import tempfile
import unittest
from unittest import mock
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
    file_quick_identity,
    input_fingerprints,
    input_record,
    load_or_create_fingerprint_manifest,
    restore_rng_state,
    validate_resume_identity,
    validate_stable_input_records,
    sha256_file,
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
            "data_manifest_sha256": "manifest-hash",
            "seenclasses": [0, 2],
            "unseenclasses": [1, 3],
        }
        arguments = dict(
            template_id="model/v5-template-v1",
            code_commit="abc123",
            config_values={"random_seed": 5},
            config_sha256="config-hash",
            fingerprints={"patch": {"sha256": "data-hash", "size_bytes": 4}},
            data_manifest_sha256="manifest-hash",
            seenclasses=[0, 2],
            unseenclasses=[1, 3],
        )
        validate_resume_identity(checkpoint, **arguments)

        for field, changed in (
            ("code_commit", "different-code"),
            ("config_sha256", "different-config"),
            ("fingerprints", {"patch": {"sha256": "different-data", "size_bytes": 4}}),
            ("data_manifest_sha256", "different-manifest"),
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
            self.assertNotIn("file_id", fingerprints["cache"])
            self.assertNotIn("mtime_ns", fingerprints["cache"])

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

    def test_v5_fingerprint_manifest_reuses_unchanged_hashes(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            source = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            source.write_bytes(b"v5-cache")

            first, first_hash = load_or_create_fingerprint_manifest(
                {"cache": source}, manifest_path
            )
            with mock.patch(
                "tools.v5_runtime.sha256_file",
                side_effect=AssertionError("cache hit must not hash the full file"),
            ):
                second, second_hash = load_or_create_fingerprint_manifest(
                    {"cache": source}, manifest_path
                )

            self.assertEqual(first, second)
            self.assertEqual(first_hash, second_hash)
            self.assertEqual(
                first_hash,
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )

    def test_v5_fingerprint_manifest_first_use_hashes_each_file_once(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            first_path = root / "first.pt"
            second_path = root / "second.pt"
            manifest_path = root / "fingerprints.json"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")

            with mock.patch(
                "tools.v5_runtime.sha256_file",
                wraps=sha256_file,
            ) as hash_file:
                manifest, manifest_hash = load_or_create_fingerprint_manifest(
                    {"first": first_path, "second": second_path}, manifest_path
                )

            self.assertEqual(hash_file.call_count, 2)
            self.assertEqual(set(manifest["files"]), {"first", "second"})
            self.assertEqual(
                manifest_hash,
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )

    def test_v5_fingerprint_manifest_rehashes_only_changed_file(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            first_path = root / "first.pt"
            second_path = root / "second.pt"
            manifest_path = root / "fingerprints.json"
            first_path.write_bytes(b"first")
            second_path.write_bytes(b"second")
            load_or_create_fingerprint_manifest(
                {"first": first_path, "second": second_path}, manifest_path
            )
            first_path.write_bytes(b"changed-first")

            with mock.patch(
                "tools.v5_runtime.sha256_file",
                wraps=sha256_file,
            ) as hash_file:
                manifest, _ = load_or_create_fingerprint_manifest(
                    {"first": first_path, "second": second_path}, manifest_path
                )

            self.assertEqual(hash_file.call_count, 1)
            self.assertEqual(Path(hash_file.call_args.args[0]), first_path.resolve())
            self.assertEqual(manifest["files"]["first"]["size_bytes"], 13)

    def test_v5_fingerprint_manifest_rebuilds_truncated_manifest(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            source = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            source.write_bytes(b"v5-cache")
            manifest_path.write_text('{"schema_version":', encoding="utf-8")

            manifest, manifest_hash = load_or_create_fingerprint_manifest(
                {"cache": source}, manifest_path
            )

            self.assertEqual(manifest["schema_version"], "gtpj.data_fingerprints.v1")
            self.assertEqual(
                manifest_hash,
                hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            )

    def test_v5_fingerprint_manifest_rebuilds_schema_or_field_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            source = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            source.write_bytes(b"v5-cache")
            identity = file_quick_identity(source)
            malformed_records = (
                {
                    "schema_version": "wrong-schema",
                    "files": {"cache": {**identity, "sha256": "0" * 64}},
                },
                {
                    "schema_version": "gtpj.data_fingerprints.v1",
                    "files": {"cache": {**identity, "sha256": "0" * 64, "extra": 1}},
                },
            )

            for index, malformed in enumerate(malformed_records):
                with self.subTest(index=index):
                    manifest_path.write_text(json.dumps(malformed), encoding="utf-8")
                    with mock.patch(
                        "tools.v5_runtime.sha256_file",
                        wraps=sha256_file,
                    ) as hash_file:
                        manifest, _ = load_or_create_fingerprint_manifest(
                            {"cache": source}, manifest_path
                        )
                    self.assertEqual(hash_file.call_count, 1)
                    self.assertEqual(
                        manifest["files"]["cache"]["sha256"], sha256_file(source)
                    )

    def test_v5_fingerprint_manifest_atomic_failure_preserves_old_file(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-manifest-") as temporary:
            root = Path(temporary)
            source = root / "cache.pt"
            manifest_path = root / "fingerprints.json"
            source.write_bytes(b"v5-cache")
            load_or_create_fingerprint_manifest({"cache": source}, manifest_path)
            old_payload = manifest_path.read_bytes()
            source.write_bytes(b"changed-cache")

            with mock.patch(
                "tools.v5_runtime.os.replace",
                side_effect=OSError("simulated atomic replace failure"),
            ):
                with self.assertRaisesRegex(OSError, "simulated atomic replace failure"):
                    load_or_create_fingerprint_manifest({"cache": source}, manifest_path)

            self.assertEqual(manifest_path.read_bytes(), old_payload)
            self.assertEqual(list(root.glob(".fingerprints.json.*.tmp")), [])

    def test_v5_stability_check_covers_quick_identity_fields(self):
        base = {
            "cache": {
                "path": "cache.pt",
                "file_id": "volume:file",
                "size_bytes": 8,
                "mtime_ns": 10,
            }
        }
        for field, changed in (
            ("file_id", "volume:replacement"),
            ("size_bytes", 9),
            ("mtime_ns", 11),
        ):
            with self.subTest(field=field):
                after = copy.deepcopy(base)
                after["cache"][field] = changed
                with self.assertRaisesRegex(RuntimeError, "加载期间发生变化"):
                    validate_stable_input_records(base, after)

    @unittest.skipUnless(os.name == "nt", "Windows 文件身份测试")
    def test_v5_windows_file_identity_changes_after_same_size_replacement(self):
        with tempfile.TemporaryDirectory(prefix="gtpj-v5-file-id-") as temporary:
            root = Path(temporary)
            path = root / "cache.pt"
            replacement = root / "replacement.pt"
            path.write_bytes(b"first")
            replacement.write_bytes(b"other")
            before = file_quick_identity(path)

            os.replace(replacement, path)
            after = file_quick_identity(path)

            self.assertEqual(before["size_bytes"], after["size_bytes"])
            self.assertNotEqual(before["file_id"], after["file_id"])

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
