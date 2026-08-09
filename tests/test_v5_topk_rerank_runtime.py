"""V5 top-k 局部证据重排推理入口的行为测试。"""

import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest

import torch


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "experiments/v5/local_evidence_runtime/rerank.py"
SPEC = importlib.util.spec_from_file_location("v5_topk_rerank_runtime", RUNTIME_PATH)
RUNTIME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNTIME)


class V5TopkRerankRuntimeTest(unittest.TestCase):
    def test_import_is_safe_and_rerank_api_has_no_labels_argument(self):
        self.assertTrue(callable(RUNTIME.main))
        parameters = inspect.signature(RUNTIME.rerank_on_class_axis).parameters
        self.assertNotIn("labels", parameters)

    def test_fixed_rerank_parameters_accept_only_registered_values(self):
        self.assertEqual((5, 0.25), RUNTIME.validate_fixed_rerank_parameters(5, 0.25))
        for k, residual_cap in ((4, 0.25), (5, 0.2), (True, 0.25), (5, True)):
            with self.subTest(k=k, residual_cap=residual_cap):
                with self.assertRaisesRegex(ValueError, "k=5|residual_cap=0.25"):
                    RUNTIME.validate_fixed_rerank_parameters(k, residual_cap)

    def test_zs_axis_is_sliced_before_rerank_and_maps_back_to_global_ids(self):
        global_logits = torch.tensor([[0.80, 9.00, 0.70, 0.60, 0.50, 0.40]])
        local_logits = torch.tensor([[0.00, 0.00, 10.00, 0.00, 0.00, 0.00]])
        unseenclasses = torch.tensor([0, 2, 3, 4, 5])

        gzsl_prediction = RUNTIME.rerank_on_class_axis(
            global_logits,
            local_logits,
            class_ids=None,
            k=5,
            residual_cap=0.25,
        )
        zsl_prediction = RUNTIME.rerank_on_class_axis(
            global_logits,
            local_logits,
            class_ids=unseenclasses,
            k=5,
            residual_cap=0.25,
        )

        torch.testing.assert_close(gzsl_prediction, torch.tensor([1]))
        torch.testing.assert_close(zsl_prediction, torch.tensor([2]))

    def test_checkpoint_identity_rejects_every_required_mismatch(self):
        expected_commit = "a" * 40
        config_hash = "b" * 64
        seenclasses = torch.tensor([0, 2])
        unseenclasses = torch.tensor([1, 3])
        good = {
            "code_commit": expected_commit,
            "config_sha256": config_hash,
            "experiment_id": "V5-INNOVATION-004",
            "seenclasses": [0, 2],
            "unseenclasses": [1, 3],
            "model_state_dict": {"weight": torch.ones(1)},
        }
        cases = {
            "code_commit": "c" * 40,
            "config_sha256": "d" * 64,
            "experiment_id": "V5-INNOVATION-999",
            "seenclasses": [0, 1],
            "unseenclasses": [2, 3],
            "model_state_dict": None,
        }
        for key, bad_value in cases.items():
            checkpoint = dict(good)
            checkpoint[key] = bad_value
            with self.subTest(key=key):
                with self.assertRaisesRegex((ValueError, TypeError), key):
                    RUNTIME.validate_checkpoint_identity(
                        checkpoint,
                        expected_code_commit=expected_commit,
                        expected_config_sha256=config_hash,
                        expected_experiment_id="V5-INNOVATION-004",
                        seenclasses=seenclasses,
                        unseenclasses=unseenclasses,
                    )

    def test_model_state_is_loaded_strictly(self):
        model = torch.nn.Linear(2, 1)
        checkpoint = {"model_state_dict": {"wrong.weight": torch.ones(1)}}
        with self.assertRaises(RuntimeError):
            RUNTIME.load_model_state_strict(model, checkpoint)

    def test_existing_output_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "RUN-001"
            output.mkdir()
            marker = output / "keep.txt"
            marker.write_text("用户已有结果", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                RUNTIME.require_new_run_dir(output)

            self.assertEqual("用户已有结果", marker.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
