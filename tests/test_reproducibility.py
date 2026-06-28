import unittest

import torch

from tools.reproducibility import (
    configure_reproducibility,
    make_batch_generator,
    reproducibility_state,
)


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


if __name__ == "__main__":
    unittest.main()
