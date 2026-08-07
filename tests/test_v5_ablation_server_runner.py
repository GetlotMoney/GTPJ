"""V5-ABLATION-001 服务器双卡执行器的静态行为测试。"""

from pathlib import Path
import tempfile
import unittest

from tools.run_v5_ablation_001_server_controller import (
    GROUP_JOBS,
    build_training_command,
)
from tools.run_v5_ablation_001_training import training_spec


class V5AblationServerRunnerTest(unittest.TestCase):
    def test_groups_are_fixed_to_two_distinct_gpus_and_entries(self):
        self.assertEqual(
            {"gpu": "0", "entry": "train_GTPJ_CUB.py"},
            training_spec("FULL"),
        )
        self.assertEqual(
            {"gpu": "1", "entry": "train_V5_ABLATION_001_CUB.py"},
            training_spec("GLOBAL_ONLY"),
        )

    def test_each_group_has_the_expected_three_job_queue(self):
        self.assertEqual(("RUN-001", "RUN-002", "RUN-003"), GROUP_JOBS["FULL"])
        self.assertEqual(
            ("RUN-004", "RUN-005", "RUN-006"), GROUP_JOBS["GLOBAL_ONLY"]
        )

    def test_receipt_command_names_exactly_one_python_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = build_training_command(
                Path("/data/lby/.conda/envs/dvsr_gpu/bin/python"),
                "GLOBAL_ONLY",
                root / "RUN-004.yaml",
                root / "code_GLOBAL_ONLY",
                "a" * 40,
            )
        self.assertEqual(1, sum(token.endswith(".py") for token in command.split()))
        self.assertIn("--group GLOBAL_ONLY", command)
        self.assertIn("--config", command)
        self.assertNotIn("&&", command)
        self.assertNotIn(";", command)


if __name__ == "__main__":
    unittest.main()
