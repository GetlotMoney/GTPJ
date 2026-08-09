"""V5 低置信度局部增强创新的专项契约测试。"""

from __future__ import annotations

import ast
import importlib.util
import csv
from contextlib import redirect_stdout
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch
import torch.nn.functional as F
import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_DIR = (
    ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-003_confidence_local_gate"
)
MODEL_PATH = EXPERIMENT_DIR / "confidence_local_gate.py"
ENTRY_PATH = EXPERIMENT_DIR / "train.py"
CONFIG_PATHS = [
    EXPERIMENT_DIR / "configs" / f"RUN-{index:03d}.yaml"
    for index in range(1, 4)
]


def load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"缺少待实现文件：{path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"无法创建模块加载器：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_config(**overrides):
    values = dict(
        num_class=6,
        dim_f_clip=16,
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
        icsa_ratio=0.008,
        icsa_hidden=8,
        sgmp_topk=1,
        sgmp_hidden=8,
        sgmp_neg_margin=0.2,
        lambda_consist=0.05,
        consist_temp=2.0,
        consist_dynamic_gamma=0.1,
        lambda_topo_pearson=0.1,
        lambda_bmdd=0.05,
        msdn_temp=2.0,
        lambda_mpp=0.05,
        lambda_neg=0.01,
        gate_beta=0.05,
        gate_bias_init=-1.0,
        gate_slope_init=1.0,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def make_model():
    module = load_module(MODEL_PATH, "v5_confidence_local_gate_model_test")
    torch.manual_seed(7)
    seen = torch.tensor([0, 2, 3, 5])
    unseen = torch.tensor([1, 4])
    model = module.ConfidenceLocalGateGTPJ(
        make_config(),
        seen,
        unseen,
        torch.randn(seen.numel(), 16),
        torch.randn(unseen.numel(), 16),
        seen_sentence_embeds=torch.randn(seen.numel(), 3, 16),
    )
    return module, model


class ConfidenceLocalGateModelTest(unittest.TestCase):
    def test_initial_effective_gate_parameters_and_fixed_beta(self):
        _module, model = make_model()

        self.assertAlmostEqual(float(model.gate_bias.detach()), -1.0, places=7)
        self.assertAlmostEqual(
            float(F.softplus(model.gate_slope_raw.detach())), 1.0, places=7
        )
        self.assertEqual(model.gate_beta, 0.05)
        self.assertTrue(model.gate_bias.requires_grad)
        self.assertTrue(model.gate_slope_raw.requires_grad)

    def test_training_margin_uses_seen_only_and_eval_margin_uses_all_classes(self):
        _module, model = make_model()
        global_logits = torch.tensor(
            [[5.0, 100.0, 4.0, 1.0, 90.0, 0.0]], requires_grad=True
        )

        train_gate, train_margin = model._compute_confidence_gate(
            global_logits, is_train=True
        )
        eval_gate, eval_margin = model._compute_confidence_gate(
            global_logits, is_train=False
        )

        torch.testing.assert_close(train_margin, torch.tensor([1.0]))
        torch.testing.assert_close(eval_margin, torch.tensor([10.0]))
        self.assertGreater(float(train_gate.detach()), float(eval_gate.detach()))

        train_gate.sum().backward()
        self.assertIsNone(global_logits.grad)
        self.assertIsNotNone(model.gate_bias.grad)
        self.assertIsNotNone(model.gate_slope_raw.grad)

    def test_gate_is_nonincreasing_as_margin_grows(self):
        _module, model = make_model()
        margins = []
        gates = []
        for second_best in (5.0, 4.0, 2.0):
            logits = torch.tensor([[5.0, second_best, 0.0, -1.0, -2.0, -3.0]])
            gate, margin = model._compute_confidence_gate(logits, is_train=False)
            margins.append(float(margin))
            gates.append(float(gate.detach()))

        self.assertEqual(margins, sorted(margins))
        self.assertGreaterEqual(gates[0], gates[1])
        self.assertGreaterEqual(gates[1], gates[2])

    def test_forward_recomputes_only_final_logits_and_preserves_auxiliaries(self):
        _module, model = make_model()
        features = torch.randn(2, 577, 16)

        train_output = model(features, is_train=True)
        eval_output = model(features, is_train=False)

        scale = torch.clamp(model.logit_scale.exp(), max=100.0)
        expected = (
            train_output["global_logits"]
            + 0.05
            * scale
            * train_output["gate"].unsqueeze(-1)
            * train_output["local_logits"]
        )
        torch.testing.assert_close(train_output["final_logits"], expected)
        torch.testing.assert_close(
            train_output["clip_S_pp"], expected[:, model.seenclass]
        )
        torch.testing.assert_close(train_output["logits"], train_output["clip_S_pp"])
        self.assertEqual(tuple(train_output["clip_S_pp"].shape), (2, 4))
        self.assertEqual(tuple(eval_output["clip_S_pp"].shape), (2, 6))

        expected_auxiliaries = {
            "global_logits",
            "local_logits",
            "score_s2v",
            "score_v2s",
            "sgmp_selected_patches",
            "sgmp_patch_z",
            "sgmp_memory",
            "all_text_cond",
        }
        self.assertTrue(expected_auxiliaries.issubset(train_output))
        for statistic in ("gate", "gate_margin", "gate_mean", "gate_min", "gate_max"):
            self.assertIn(statistic, train_output)

        losses = model.compute_loss(
            dict(train_output, batch_label=torch.tensor([0, 3]))
        )
        losses["loss"].backward()
        for parameter in (model.gate_bias, model.gate_slope_raw):
            self.assertIsNotNone(parameter.grad)
            self.assertTrue(torch.isfinite(parameter.grad).all())
            self.assertGreater(float(parameter.grad.detach().abs().sum()), 0.0)


class ConfidenceLocalGateEntryTest(unittest.TestCase):
    def test_split_ids_stay_on_cpu_until_model_device_transfer(self):
        tree = ast.parse(ENTRY_PATH.read_text(encoding="utf-8"))
        calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_v5_cub_split"
        ]
        self.assertEqual(len(calls), 1)
        self.assertGreaterEqual(len(calls[0].args), 6)
        self.assertIsInstance(calls[0].args[5], ast.Constant)
        self.assertEqual(calls[0].args[5].value, "cpu")

    def test_entry_is_import_safe_and_four_runtime_arguments_are_required(self):
        module = load_module(ENTRY_PATH, "v5_confidence_local_gate_entry_test")

        parser = module.build_parser()
        required = {
            action.dest
            for action in parser._actions
            if getattr(action, "required", False)
        }
        self.assertEqual(
            required,
            {"config", "data_root", "run_dir", "expected_run_commit"},
        )
        self.assertTrue(callable(module.main))

    def test_three_seed_five_configs_are_byte_identical_and_fixed(self):
        for path in CONFIG_PATHS:
            self.assertTrue(path.is_file(), f"缺少配置副本：{path.relative_to(ROOT)}")
        payloads = [path.read_bytes() for path in CONFIG_PATHS]
        self.assertEqual(payloads[0], payloads[1])
        self.assertEqual(payloads[1], payloads[2])

        config = yaml.safe_load(payloads[0].decode("utf-8"))
        flat = {
            key: value["value"] if isinstance(value, dict) and "value" in value else value
            for key, value in config.items()
        }
        self.assertEqual(flat["random_seed"], 5)
        self.assertEqual(flat["idea_id"], "IDEA-0005")
        self.assertEqual(flat["base_template_id"], "MODEL-V5-TEMPLATE-V1")
        self.assertEqual(
            flat["base_template_commit"],
            "2f5fa5e631ef82658d4bac587cdfd17f3534cb35",
        )
        self.assertEqual(flat["gate_beta"], 0.05)
        self.assertEqual(flat["gate_bias_init"], -1.0)
        self.assertEqual(flat["gate_slope_init"], 1.0)

    def test_experiment_ledger_and_parameter_matrix_bind_exact_base(self):
        experiment_path = EXPERIMENT_DIR / "EXPERIMENT.yaml"
        matrix_path = EXPERIMENT_DIR / "PARAMETER_MATRIX.csv"
        self.assertTrue(experiment_path.is_file(), "缺少 EXPERIMENT.yaml")
        self.assertTrue(matrix_path.is_file(), "缺少 PARAMETER_MATRIX.csv")

        helper_path = ROOT / "workflow" / "gtpj_workflow.py"
        helper_commands = (
            (
                "validate-experiment-base",
                ["validate-experiment-base", "--path", str(EXPERIMENT_DIR)],
            ),
            (
                "validate-parameter-matrix --require-ready",
                [
                    "validate-parameter-matrix",
                    "--path",
                    str(matrix_path),
                    "--expected-jobs",
                    "3",
                    "--require-ready",
                ],
            ),
        )
        helper_failures = []
        for label, arguments in helper_commands:
            result = subprocess.run(
                [sys.executable, str(helper_path), *arguments],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                helper_failures.append(
                    f"{label} 失败（exit={result.returncode}）\n"
                    f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
        self.assertFalse(helper_failures, "\n\n".join(helper_failures))

        experiment = yaml.safe_load(experiment_path.read_text(encoding="utf-8"))
        self.assertEqual(experiment["experiment_id"], "V5-INNOVATION-003")
        self.assertEqual(experiment["idea_id"], "IDEA-0005")
        self.assertEqual(experiment["idea_binding_status"], "ready")
        self.assertEqual(
            experiment["idea_registry_commit"],
            "6e42dfcff09a87c14aba807e4bb0fd7ab0d73350",
        )
        self.assertEqual(experiment["legacy_ref"], "IDEA-0005")
        self.assertEqual(experiment["status"], "pre_run")
        self.assertTrue(experiment["formal_run_allowed"])
        self.assertEqual(experiment["base_template_id"], "MODEL-V5-TEMPLATE-V1")
        self.assertEqual(experiment["base_template_tag"], "model/v5-template-v1")
        self.assertEqual(
            experiment["base_template_commit"],
            "2f5fa5e631ef82658d4bac587cdfd17f3534cb35",
        )
        self.assertEqual(
            experiment["template_registry_commit"],
            "4f29e99bb1a940afa66bb66f8150c379c2d0af7f",
        )

        with matrix_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["job_id"] for row in rows], ["RUN-001", "RUN-002", "RUN-003"])
        self.assertEqual({row["seed"] for row in rows}, {"5"})
        self.assertEqual({row["status"] for row in rows}, {"frozen"})
        self.assertEqual({row["base_version"] for row in rows}, {"v5"})
        self.assertEqual(
            {row["base_config_sha256"] for row in rows},
            {"def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"},
        )
        self.assertEqual({row["code_ref"] for row in rows}, {"model/v5-template-v1"})
        self.assertEqual(
            {row["config_fingerprint"] for row in rows},
            {"cba09034a3b773b78d51cb3c28f35f0fee95ce7536f41be617b7bc04c98cf2ee"},
        )
        self.assertEqual(rows[0]["repeat_of"], "")
        self.assertEqual(rows[1]["repeat_of"], "RUN-001")
        self.assertEqual(rows[2]["repeat_of"], "RUN-001")

        idea_path = (
            ROOT
            / "idea_tree"
            / "ideas"
            / "IDEA-0005_confidence_conditioned_local_gate"
            / "IDEA.md"
        )
        self.assertTrue(idea_path.is_file(), "缺少 IDEA-0005 共享登记文件")
        self.assertIn(
            "IDEA-0005",
            (ROOT / "idea_tree" / "INDEX.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "V5-INNOVATION-003",
            (ROOT / "experiments" / "v5" / "innovation" / "INDEX.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_preflight_rejects_cpu_dirty_git_wrong_commit_and_existing_output(self):
        module = load_module(ENTRY_PATH, "v5_confidence_local_gate_preflight_test")
        with mock.patch.object(module.torch.cuda, "is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "CUDA"):
                module.require_cuda_device("cuda:0")

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Test"], check=True
            )
            tracked = repo / "tracked.txt"
            tracked.write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True
            )
            commit = module.current_code_commit(repo)
            module.require_expected_commit(repo, commit)
            module.require_clean_git(repo)

            with self.assertRaisesRegex(RuntimeError, "commit"):
                module.require_expected_commit(repo, "0" * 40)
            tracked.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "工作树"):
                module.require_clean_git(repo)

            existing = Path(temp_dir) / "existing-run"
            existing.mkdir()
            with self.assertRaisesRegex(FileExistsError, "输出目录"):
                module.require_new_run_dir(existing)

    def test_atomic_outputs_finite_guard_and_gate_accumulator(self):
        module = load_module(ENTRY_PATH, "v5_confidence_local_gate_output_test")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            json_path = root / "metrics.json"
            tensor_path = root / "model_best.pt"
            log = module.AtomicTrainingLog(root / "training.log")

            module.atomic_write_json(json_path, {"H": 0.75})
            module.atomic_torch_save(tensor_path, {"weight": torch.tensor([1.0])})
            with redirect_stdout(io.StringIO()):
                log.write("line-one")
                log.write("line-two")

            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["H"], 0.75)
            self.assertEqual(
                torch.load(tensor_path, map_location="cpu", weights_only=True)[
                    "weight"
                ].item(),
                1.0,
            )
            self.assertEqual(
                (root / "training.log").read_text(encoding="utf-8"),
                "line-one\nline-two\n",
            )
            self.assertFalse(any(root.glob("*.tmp")))

        module.require_finite_tensor("finite", torch.tensor([1.0, -2.0]))
        with self.assertRaisesRegex(FloatingPointError, "nonfinite"):
            module.require_finite_tensor("nonfinite", torch.tensor([math.nan]))

        stats = module.GateStatsAccumulator()
        stats.update(torch.tensor([0.1, 0.4]))
        stats.update(torch.tensor([0.2]))
        summary = stats.summary()
        self.assertAlmostEqual(summary["mean"], (0.1 + 0.4 + 0.2) / 3, places=7)
        self.assertAlmostEqual(summary["min"], 0.1, places=7)
        self.assertAlmostEqual(summary["max"], 0.4, places=7)
        self.assertEqual(summary["count"], 3)


if __name__ == "__main__":
    unittest.main()
