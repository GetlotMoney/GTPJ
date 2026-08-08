"""CONFIRM-002 真实 V5 尺寸零步探针测试。"""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = (
    ROOT
    / "experiments"
    / "v5"
    / "confirmation"
    / "CONFIRM-002_v5-seed-equivalence"
    / "verify_seed_equivalence.py"
)


class V5SeedEquivalenceProbeTest(unittest.TestCase):
    def test_full_size_probe_matches_historical_v5_without_dead_parameters(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PROBE),
                "--repository-root",
                str(ROOT),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["dimensions"], {"dim_com": 512, "dim_f": 768})
        self.assertEqual(payload["active_state_mismatches"], [])
        self.assertTrue(payload["post_model_cpu_rng_equal"])
        self.assertTrue(payload["first_three_batches_equal"])
        self.assertFalse(payload["dead_parameter_names_present"])
        self.assertEqual(payload["clean_parameter_count"], 13_976_981)
        self.assertEqual(
            payload["config_sha256"],
            "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e",
        )
        self.assertTrue(payload["config_matches_expected_sha256"])
        self.assertEqual(len(payload["candidate_model_sha256"]), 64)
        self.assertEqual(len(payload["git_head"]), 40)
        self.assertIsInstance(payload["git_dirty"], bool)
        self.assertFalse(payload["formal_candidate_check_requested"])

    def test_formal_probe_rejects_the_wrong_candidate_commit(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(PROBE),
                "--repository-root",
                str(ROOT),
                "--formal-candidate-commit",
                "0" * 40,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCK")
        self.assertTrue(payload["formal_candidate_check_requested"])
        self.assertFalse(payload["formal_candidate_identity_ok"])


if __name__ == "__main__":
    unittest.main()
