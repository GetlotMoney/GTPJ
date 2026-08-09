"""V5 全局 top-k 内局部证据重排的行为测试。"""

import unittest

import torch

from tools import v5_topk_local_rerank as rerank_module
from tools.v5_topk_local_rerank import topk_local_rerank


class V5TopkLocalRerankTest(unittest.TestCase):
    def test_local_only_reranks_inside_global_topk(self):
        global_logits = torch.tensor([[5.0, 4.8, 4.7]])
        # 类别 2 的局部分数最高，但它不在全局 top-2，不能被选中。
        local_logits = torch.tensor([[0.0, 4.0, 100.0]])

        prediction = topk_local_rerank(
            global_logits,
            local_logits,
            k=2,
            residual_cap=1.0,
        )

        torch.testing.assert_close(prediction, torch.tensor([1]))

    def test_constant_local_logits_strictly_keep_global_prediction(self):
        global_logits = torch.tensor(
            [
                [0.1, 0.9, 0.8, -2.0],
                [4.0, 1.0, 3.0, 2.0],
            ]
        )
        local_logits = torch.full_like(global_logits, 7.0)

        prediction = topk_local_rerank(
            global_logits,
            local_logits,
            k=3,
            residual_cap=100.0,
        )

        torch.testing.assert_close(prediction, global_logits.argmax(dim=1))

    def test_k_one_strictly_keeps_global_top1(self):
        global_logits = torch.tensor([[2.0, 1.9, -1.0], [0.1, 0.2, 0.3]])
        local_logits = torch.tensor([[-100.0, 100.0, 999.0], [8.0, 9.0, -9.0]])

        prediction = topk_local_rerank(
            global_logits,
            local_logits,
            k=1,
            residual_cap=1_000.0,
        )

        torch.testing.assert_close(prediction, global_logits.argmax(dim=1))

    def test_zero_residual_cap_keeps_global_prediction(self):
        global_logits = torch.tensor([[1.0, 0.9, 0.8]])
        local_logits = torch.tensor([[-5.0, 5.0, 100.0]])

        prediction = topk_local_rerank(
            global_logits,
            local_logits,
            k=2,
            residual_cap=0.0,
        )

        torch.testing.assert_close(prediction, torch.tensor([0]))

    def test_repeated_calls_are_deterministic_and_do_not_mutate_inputs(self):
        global_logits = torch.tensor([[2.0, 1.8, 1.7], [0.4, 0.9, 0.7]])
        local_logits = torch.tensor([[0.0, 3.0, 100.0], [5.0, 0.0, 2.0]])
        global_before = global_logits.clone()
        local_before = local_logits.clone()

        first = topk_local_rerank(
            global_logits,
            local_logits,
            k=2,
            residual_cap=0.8,
        )
        second = topk_local_rerank(
            global_logits,
            local_logits,
            k=2,
            residual_cap=0.8,
        )

        torch.testing.assert_close(first, second)
        torch.testing.assert_close(global_logits, global_before)
        torch.testing.assert_close(local_logits, local_before)

    def test_rejects_non_matrix_or_mismatched_logits(self):
        cases = (
            (torch.tensor([1.0, 2.0]), torch.tensor([1.0, 2.0])),
            (torch.ones(2, 3), torch.ones(2, 4)),
            (torch.ones(2, 3), torch.ones(1, 3)),
        )
        for global_logits, local_logits in cases:
            with self.subTest(
                global_shape=tuple(global_logits.shape),
                local_shape=tuple(local_logits.shape),
            ):
                with self.assertRaisesRegex(ValueError, "形状"):
                    topk_local_rerank(
                        global_logits,
                        local_logits,
                        k=1,
                        residual_cap=0.5,
                    )

    def test_rejects_non_finite_logits(self):
        finite = torch.tensor([[2.0, 1.0]])
        invalid_cases = (
            (torch.tensor([[float("nan"), 1.0]]), finite),
            (finite, torch.tensor([[float("inf"), 1.0]])),
        )
        for global_logits, local_logits in invalid_cases:
            with self.subTest(global_logits=global_logits, local_logits=local_logits):
                with self.assertRaisesRegex(ValueError, "有限"):
                    topk_local_rerank(
                        global_logits,
                        local_logits,
                        k=1,
                        residual_cap=0.5,
                    )

    def test_rejects_invalid_k(self):
        logits = torch.tensor([[3.0, 2.0, 1.0]])
        for invalid_k in (0, 4, 1.5, True):
            with self.subTest(k=invalid_k):
                with self.assertRaisesRegex(ValueError, "k"):
                    topk_local_rerank(
                        logits,
                        logits,
                        k=invalid_k,
                        residual_cap=0.5,
                    )

    def test_rejects_invalid_residual_cap(self):
        logits = torch.tensor([[3.0, 2.0, 1.0]])
        for invalid_cap in (-0.1, float("nan"), float("inf"), True):
            with self.subTest(residual_cap=invalid_cap):
                with self.assertRaisesRegex(ValueError, "residual_cap"):
                    topk_local_rerank(
                        logits,
                        logits,
                        k=2,
                        residual_cap=invalid_cap,
                    )

    def test_batch_diagnostics_count_rescue_harm_and_topk_coverage(self):
        global_logits = torch.tensor(
            [
                [5.0, 4.8, 0.0],
                [5.0, 4.8, 0.0],
                [5.0, 4.8, 0.0],
            ]
        )
        local_logits = torch.tensor(
            [
                [0.0, 4.0, 100.0],
                [0.0, 4.0, 100.0],
                [4.0, 0.0, 100.0],
            ]
        )
        labels = torch.tensor([1, 0, 2])

        diagnostics = rerank_module.diagnose_topk_local_rerank(
            global_logits,
            local_logits,
            labels,
            k=2,
            residual_cap=1.0,
        )

        self.assertEqual(
            diagnostics,
            {
                "prediction_changed": 2,
                "rescue": 1,
                "harm": 1,
                "topk_coverage": 2.0 / 3.0,
            },
        )

    def test_diagnostics_reject_invalid_labels(self):
        logits = torch.tensor([[3.0, 2.0, 1.0], [1.0, 2.0, 3.0]])
        invalid_labels = (
            torch.tensor([[0], [2]]),
            torch.tensor([0]),
            torch.tensor([0, 3]),
            torch.tensor([0.0, 2.0]),
        )
        for labels in invalid_labels:
            with self.subTest(labels=labels):
                with self.assertRaisesRegex(ValueError, "labels"):
                    rerank_module.diagnose_topk_local_rerank(
                        logits,
                        logits,
                        labels,
                        k=2,
                        residual_cap=0.5,
                    )


if __name__ == "__main__":
    unittest.main()
