import ast
import csv
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import torch
import yaml

from model.MyModel import GTPJ, fuse_global_local_logits
from tests.test_v5_template_contract import _parity_config
from tools.v5_innovation_002_runtime import (
    prepare_run_directory,
    validate_experiment_config,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TRAINING_ENTRY = REPOSITORY_ROOT / "train_V5_INNOVATION_002_CUB.py"
CANONICAL_V5_CONFIG = REPOSITORY_ROOT / "config" / "versions" / "v5.yaml"
CANONICAL_V5_SHA256 = (
    "def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e"
)
INNOVATION_002_DIRECTORY = (
    REPOSITORY_ROOT
    / "experiments"
    / "v5"
    / "innovation"
    / "INNOVATION-002_scale_consistent_fusion"
)
INNOVATION_002_CONFIG_DIRECTORY = INNOVATION_002_DIRECTORY / "configs"
INNOVATION_002_MATRIX_CSV = INNOVATION_002_DIRECTORY / "PARAMETER_MATRIX.csv"
INNOVATION_002_MATRIX_MD = INNOVATION_002_DIRECTORY / "PARAMETER_MATRIX.md"
INNOVATION_002_RUN_SPECS = {
    "RUN-001": ("legacy", 5),
    "RUN-002": ("scale_consistent", 5),
    "RUN-003": ("legacy", 5),
    "RUN-004": ("scale_consistent", 5),
    "RUN-005": ("legacy", 5),
    "RUN-006": ("scale_consistent", 5),
    "RUN-007": ("legacy", 17),
    "RUN-008": ("scale_consistent", 17),
    "RUN-009": ("legacy", 29),
    "RUN-010": ("scale_consistent", 29),
}
INNOVATION_002_REPEAT_OF = {
    "RUN-003": "RUN-001",
    "RUN-004": "RUN-002",
    "RUN-005": "RUN-001",
    "RUN-006": "RUN-002",
}
PARAMETER_MATRIX_COLUMNS = [
    "job_id",
    "work_item_id",
    "job_kind",
    "status",
    "group",
    "name",
    "base_version",
    "base_config_sha256",
    "code_ref",
    "config_snapshot_ref",
    "seed",
    "changed_parameters",
    "config_fingerprint",
    "repeat_of",
    "duplicate_resolution",
    "purpose",
    "run_id",
    "run_start_receipt_ref",
    "run_start_receipt_sha256",
    "run_command_sha256",
    "run_log_sha256",
    "run_exit_code",
    "U",
    "S",
    "H",
    "ZS",
    "best_epoch",
    "decision",
    "artifact_ref",
    "artifact_manifest_sha256",
]


class V5Innovation002TrainingEntryTest(unittest.TestCase):
    def setUp(self):
        if not TRAINING_ENTRY.is_file():
            if self._testMethodName == "test_training_entry_exists":
                return
            self.skipTest("专用训练入口尚未创建")
        self.source = TRAINING_ENTRY.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    @staticmethod
    def _load_training_entry_module():
        spec = importlib.util.spec_from_file_location("v5_training_entry", TRAINING_ENTRY)
        if spec is None or spec.loader is None:
            raise RuntimeError("无法加载专用训练入口")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_training_entry_exists(self):
        self.assertTrue(
            TRAINING_ENTRY.is_file(),
            "缺少专用训练入口 train_V5_INNOVATION_002_CUB.py",
        )

    def test_import_is_safe_and_main_is_guarded(self):
        guarded_main = False
        for node in self.tree.body:
            if not isinstance(node, ast.If):
                continue
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)
                and len(node.test.comparators) == 1
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "__main__"
                and any(
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Call)
                    and isinstance(statement.value.func, ast.Name)
                    and statement.value.func.id == "main"
                    for statement in node.body
                )
            ):
                guarded_main = True
        self.assertTrue(guarded_main)

        with tempfile.TemporaryDirectory() as temporary_directory:
            command = (
                "import importlib.util; "
                f"p={str(TRAINING_ENTRY)!r}; "
                "s=importlib.util.spec_from_file_location('v5_entry', p); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m)"
            )
            result = subprocess.run(
                [sys.executable, "-c", command],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(temporary_directory).iterdir()), [])

    def test_cli_has_only_four_required_experiment_arguments(self):
        argument_calls = []
        for node in ast.walk(self.tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
                and node.args
                and isinstance(node.args[0], ast.Constant)
            ):
                argument_calls.append(node)

        arguments = {call.args[0].value: call for call in argument_calls}
        expected = {"--config", "--data-root", "--run-dir", "--run-id"}
        self.assertEqual(set(arguments), expected)
        for name, call in arguments.items():
            keywords = {keyword.arg: keyword.value for keyword in call.keywords}
            self.assertIn("required", keywords, name)
            self.assertIsInstance(keywords["required"], ast.Constant)
            self.assertIs(keywords["required"].value, True, name)
        self.assertNotIn("resume", self.source.lower())

        parser_calls = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "ArgumentParser"
        ]
        self.assertEqual(len(parser_calls), 1)
        parser_keywords = {
            keyword.arg: keyword.value for keyword in parser_calls[0].keywords
        }
        self.assertIs(parser_keywords["allow_abbrev"].value, False)

    def test_help_is_side_effect_free_and_lists_required_arguments(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = subprocess.run(
                [sys.executable, str(TRAINING_ENTRY), "--help"],
                cwd=temporary_directory,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("--config", "--data-root", "--run-dir", "--run-id"):
                self.assertIn(name, result.stdout)
            self.assertEqual(list(Path(temporary_directory).iterdir()), [])

    def test_entry_uses_runtime_guards_and_fixed_identity(self):
        self.assertIn('EXPERIMENT_ID = "V5-INNOVATION-002"', self.source)
        self.assertIn(
            'MODEL_ID = "MODEL-V5-SCALE-FUSION-CANDIDATE-V1"', self.source
        )
        self.assertIn('BASE_TEMPLATE_ID = "MODEL-V5-TEMPLATE-V1"', self.source)
        self.assertIn("validate_experiment_config(values)", self.source)
        self.assertIn(
            "prepare_run_directory(args.run_dir, args.run_id)", self.source
        )
        self.assertNotIn('Path("./train_log/CUB")', self.source)
        self.assertIn('["git", "status", "--porcelain"]', self.source)

    def test_available_memory_gate_is_fail_closed_at_fourteen_gib(self):
        module = self._load_training_entry_module()
        threshold = 14 * 1024**3
        self.assertEqual(module.MIN_AVAILABLE_MEMORY_BYTES, threshold)

        with mock.patch.object(
            module,
            "_available_physical_memory_bytes",
            return_value=threshold - 1,
        ):
            with self.assertRaisesRegex(MemoryError, "14 GiB"):
                module._require_minimum_available_memory()

        with mock.patch.object(
            module,
            "_available_physical_memory_bytes",
            return_value=threshold,
        ):
            self.assertEqual(module._require_minimum_available_memory(), threshold)

        with mock.patch.object(
            module,
            "_available_physical_memory_bytes",
            side_effect=OSError("unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "无法读取可用物理内存"):
                module._require_minimum_available_memory()

    def test_memory_gate_runs_before_run_directory_creation(self):
        main_node = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        )
        calls = [node for node in ast.walk(main_node) if isinstance(node, ast.Call)]
        memory_calls = [
            node
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "_require_minimum_available_memory"
        ]
        run_directory_calls = [
            node
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "prepare_run_directory"
        ]
        self.assertEqual(len(memory_calls), 1)
        self.assertEqual(len(run_directory_calls), 1)
        self.assertLess(memory_calls[0].lineno, run_directory_calls[0].lineno)

    def test_all_data_paths_derive_from_data_root_and_test_cache_is_explicit(self):
        expected_fragments = (
            'CACHE_DIR = data_root / "cache"',
            'TRAIN_CLS_PATH = CACHE_DIR / "CUB_train_features.pt"',
            'TRAIN_PATCH_PATH = CACHE_DIR / "CUB_train_patch_features.pt"',
            'TRAIN_LABEL_PATH = CACHE_DIR / "CUB_train_labels.pt"',
            'GPT55_SENTENCE_PATH = CACHE_DIR / "CUB_gpt55_sentence_embeds.pt"',
            'DATA_RES101_PATH = data_root / "xlsa17/data/CUB/res101.mat"',
            'DATA_SPLIT_PATH = data_root / "xlsa17/data/CUB/att_splits.mat"',
            "v5_test_cache_paths(CACHE_DIR)",
            "load_v5_test_cache(CACHE_DIR)",
        )
        for fragment in expected_fragments:
            self.assertIn(fragment, self.source)

    def test_cub_split_is_constructed_on_cpu(self):
        calls = [
            node
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "load_v5_cub_split"
        ]
        self.assertEqual(len(calls), 1)
        call = calls[0]
        self.assertEqual(len(call.args), 6)
        self.assertIsInstance(call.args[5], ast.Constant)
        self.assertEqual(call.args[5].value, "cpu")
        self.assertEqual(ast.unparse(call.args[0]), "DATA_RES101_PATH")
        self.assertEqual(ast.unparse(call.args[1]), "DATA_SPLIT_PATH")
        self.assertEqual(ast.unparse(call.args[2]), "train_labels")
        self.assertEqual(ast.unparse(call.args[3]), "test_cache['seen_labels']")
        self.assertEqual(ast.unparse(call.args[4]), "test_cache['unseen_labels']")

    def test_run_outputs_have_fixed_names(self):
        for assignment in (
            'log_path = run_dir / "training.log"',
            'model_path = run_dir / "model_best.pth"',
            'checkpoint_path = run_dir / "checkpoint_last.pth"',
            'metrics_path = run_dir / "metrics.json"',
        ):
            self.assertIn(assignment, self.source)

    def test_config_snapshot_preserves_original_bytes(self):
        self.assertIn(
            "config_snapshot_path.write_bytes(config_bytes)", self.source
        )

    def test_best_selection_accepts_first_zero_then_only_strict_improvement(self):
        module = self._load_training_entry_module()
        self.assertTrue(
            hasattr(module, "_is_new_best"),
            "训练入口缺少 _is_new_best 判定函数",
        )

        self.assertTrue(module._is_new_best(0.0, 0.0, 0))
        self.assertFalse(module._is_new_best(0.0, 0.0, 1))
        self.assertTrue(module._is_new_best(0.1, 0.0, 1))

    def test_training_best_branch_calls_best_selection_helper(self):
        helper_conditions = [
            node.test
            for node in ast.walk(self.tree)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Name)
            and node.test.func.id == "_is_new_best"
        ]
        self.assertEqual(len(helper_conditions), 1)
        self.assertEqual(
            [ast.unparse(argument) for argument in helper_conditions[0].args],
            ["harmonic", "best_h", "best_metrics['epoch']"],
        )

    def test_git_helpers_are_pinned_to_training_entry_repository(self):
        module = self._load_training_entry_module()
        self.assertTrue(
            hasattr(module, "REPOSITORY_ROOT"),
            "训练入口缺少固定仓库根目录",
        )
        self.assertTrue(
            hasattr(module, "_require_expected_repository"),
            "训练入口缺少仓库身份检查",
        )
        self.assertEqual(module.REPOSITORY_ROOT, REPOSITORY_ROOT)
        responses = [
            mock.Mock(stdout=str(REPOSITORY_ROOT) + "\n"),
            mock.Mock(stdout=""),
            mock.Mock(stdout="abc123\n"),
        ]
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                with mock.patch.object(
                    module.subprocess, "run", side_effect=responses
                ) as run:
                    module._require_expected_repository()
                    module._require_clean_code_tree()
                    self.assertEqual(module._current_code_commit(), "abc123")
            finally:
                os.chdir(original_cwd)

        expected_common = {
            "cwd": REPOSITORY_ROOT,
            "check": True,
            "capture_output": True,
            "text": True,
        }
        self.assertEqual(
            run.call_args_list,
            [
                mock.call(["git", "rev-parse", "--show-toplevel"], **expected_common),
                mock.call(["git", "status", "--porcelain"], **expected_common),
                mock.call(["git", "rev-parse", "HEAD"], **expected_common),
            ],
        )

    def test_wrong_git_repository_cannot_pass_identity_check(self):
        module = self._load_training_entry_module()
        self.assertTrue(
            hasattr(module, "_require_expected_repository"),
            "训练入口缺少仓库身份检查",
        )
        with tempfile.TemporaryDirectory() as other_repository:
            response = mock.Mock(stdout=str(Path(other_repository).resolve()) + "\n")
            with mock.patch.object(module.subprocess, "run", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "仓库"):
                    module._require_expected_repository()

    def test_lr_stages_reject_non_finite_bool_and_fractional_values(self):
        module = self._load_training_entry_module()
        module._validate_lr_stages([{"lr": 0.001, "epochs": 2, "eta_min": 0.0}])
        invalid_stages = (
            {"lr": True, "epochs": 2, "eta_min": 0.0},
            {"lr": float("nan"), "epochs": 2, "eta_min": 0.0},
            {"lr": float("inf"), "epochs": 2, "eta_min": 0.0},
            {"lr": 0.001, "epochs": True, "eta_min": 0.0},
            {"lr": 0.001, "epochs": 1.5, "eta_min": 0.0},
            {"lr": 0.001, "epochs": 2, "eta_min": True},
            {"lr": 0.001, "epochs": 2, "eta_min": float("nan")},
            {"lr": 0.001, "epochs": 2, "eta_min": float("inf")},
        )
        for stage in invalid_stages:
            with self.subTest(stage=stage):
                with self.assertRaises(ValueError):
                    module._validate_lr_stages([stage])

    def test_finite_tensor_metric_gradient_and_scale_guards(self):
        module = self._load_training_entry_module()
        for name in (
            "_require_finite_tensor",
            "_require_finite_metrics",
            "_require_finite_gradients",
        ):
            self.assertTrue(hasattr(module, name), f"训练入口缺少 {name}")

        module._require_finite_tensor("finite", torch.tensor([0.0, 1.0]))
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(tensor=value):
                with self.assertRaisesRegex(FloatingPointError, "bad_tensor"):
                    module._require_finite_tensor("bad_tensor", torch.tensor([value]))

        module._require_finite_metrics({"U": 1.0, "S": 2.0, "H": 3.0, "ZS": 4.0})
        with self.assertRaisesRegex(FloatingPointError, "H"):
            module._require_finite_metrics(
                {"U": 1.0, "S": 2.0, "H": float("nan"), "ZS": 4.0}
            )

        linear = torch.nn.Linear(1, 1, bias=False)
        linear.weight.grad = torch.tensor([[float("inf")]])
        with self.assertRaisesRegex(FloatingPointError, "grad"):
            module._require_finite_gradients(linear)

        non_finite_scale = mock.Mock(logit_scale=torch.tensor(float("inf")))
        with self.assertRaisesRegex(FloatingPointError, "logit_scale"):
            module._actual_logit_scale(non_finite_scale)

    def test_gradient_scan_aggregates_normal_path_and_preserves_gradients(self):
        module = self._load_training_entry_module()
        model = torch.nn.Sequential(
            torch.nn.Linear(2, 3),
            torch.nn.Linear(3, 1),
        )
        for index, (_name, parameter) in enumerate(model.named_parameters(), start=1):
            parameter.grad = torch.full_like(parameter, float(index))
        gradients_before = {
            name: parameter.grad.detach().clone()
            for name, parameter in model.named_parameters()
        }

        with mock.patch.object(
            module,
            "_require_finite_tensor",
            wraps=module._require_finite_tensor,
        ) as per_tensor_guard:
            module._require_finite_gradients(model)
        per_tensor_guard.assert_not_called()
        for name, parameter in model.named_parameters():
            torch.testing.assert_close(parameter.grad, gradients_before[name])

        model.zero_grad(set_to_none=True)
        module._require_finite_gradients(model)

        bad_name, bad_parameter = next(iter(model.named_parameters()))
        bad_parameter.grad = torch.zeros_like(bad_parameter)
        bad_parameter.grad.reshape(-1)[0] = float("nan")
        bad_gradient_before = bad_parameter.grad.detach().clone()
        with self.assertRaises(FloatingPointError) as context:
            module._require_finite_gradients(model)
        self.assertIn(bad_name, str(context.exception))
        torch.testing.assert_close(
            bad_parameter.grad,
            bad_gradient_before,
            equal_nan=True,
        )

    def test_gradient_scan_has_one_item_sync_outside_parameter_loops(self):
        functions = [
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_require_finite_gradients"
        ]
        self.assertEqual(len(functions), 1)
        function = functions[0]
        item_calls = [
            node
            for node in ast.walk(function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "item"
        ]
        self.assertEqual(len(item_calls), 1)
        for loop in [node for node in ast.walk(function) if isinstance(node, ast.For)]:
            loop_item_calls = [
                node
                for node in ast.walk(loop)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "item"
            ]
            self.assertEqual(loop_item_calls, [])

    def test_evaluation_guard_checks_each_forward_and_always_removes_hook(self):
        module = self._load_training_entry_module()
        self.assertTrue(hasattr(module, "_evaluate_with_finite_logits"))

        class DictModel(torch.nn.Module):
            def __init__(self, value):
                super().__init__()
                self.value = value

            def forward(self, _features):
                return {"logits": torch.tensor([[self.value]])}

        def evaluator(model, metrics):
            model(torch.ones(1, 1))
            return metrics

        bad_logits_model = DictModel(float("nan"))
        with self.assertRaisesRegex(FloatingPointError, "evaluation logits"):
            module._evaluate_with_finite_logits(
                bad_logits_model,
                evaluator,
                (0.1, 0.2, 0.3, 0.4),
            )
        self.assertEqual(len(bad_logits_model._forward_hooks), 0)

        bad_metrics_model = DictModel(1.0)
        with self.assertRaisesRegex(FloatingPointError, "H"):
            module._evaluate_with_finite_logits(
                bad_metrics_model,
                evaluator,
                (0.1, 0.2, float("nan"), 0.4),
            )
        self.assertEqual(len(bad_metrics_model._forward_hooks), 0)

    def test_training_loop_calls_all_non_finite_guards(self):
        for fragment in (
            '_require_finite_tensor("training logits", output["logits"])',
            '_require_finite_tensor("training loss", losses["loss"])',
            "_require_finite_gradients(model)",
            "_evaluate_with_finite_logits(",
            "_require_finite_metrics(metrics)",
        ):
            self.assertIn(fragment, self.source)

    def test_config_identity_uses_first_loaded_bytes_after_source_changes(self):
        module = self._load_training_entry_module()
        self.assertTrue(hasattr(module, "_sha256_bytes"))
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source = root / "config.yaml"
            snapshot = root / "snapshot.yaml"
            source.write_bytes(b"first config bytes\n")
            config_bytes = source.read_bytes()
            expected_hash = module._sha256_bytes(config_bytes)
            source.write_bytes(b"changed after first read\n")
            snapshot.write_bytes(config_bytes)

            self.assertEqual(snapshot.read_bytes(), b"first config bytes\n")
            self.assertEqual(module._sha256_bytes(config_bytes), expected_hash)
            self.assertNotEqual(module._sha256_bytes(source.read_bytes()), expected_hash)

        self.assertIn("config_hash = _sha256_bytes(config_bytes)", self.source)
        self.assertNotIn("sha256_file", self.source)

    def test_atomic_json_is_strict_and_preserves_existing_file_on_failure(self):
        module = self._load_training_entry_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "metrics.json"
            target.write_bytes(b"old metrics")
            with self.assertRaises(ValueError):
                module._write_json(target, {"H": float("nan")})
            self.assertEqual(target.read_bytes(), b"old metrics")

            replace_parents = []
            original_replace = Path.replace

            def recording_replace(source, destination):
                replace_parents.append((source.parent, Path(destination).parent))
                return original_replace(source, destination)

            with mock.patch.object(Path, "replace", recording_replace):
                module._write_json(target, {"status": "completed", "H": 1.0})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["H"], 1.0)
            self.assertEqual(replace_parents, [(target.parent, target.parent)])

    def test_atomic_torch_save_preserves_existing_file_on_failure(self):
        module = self._load_training_entry_module()
        self.assertTrue(hasattr(module, "_atomic_torch_save"))
        with tempfile.TemporaryDirectory() as temporary_directory:
            target = Path(temporary_directory) / "checkpoint.pth"
            target.write_bytes(b"old checkpoint")
            with mock.patch.object(torch, "save", side_effect=OSError("write failed")):
                with self.assertRaisesRegex(OSError, "write failed"):
                    module._atomic_torch_save({"epoch": 1}, target)
            self.assertEqual(target.read_bytes(), b"old checkpoint")

            module._atomic_torch_save({"epoch": 2}, target)
            self.assertEqual(
                torch.load(target, map_location="cpu", weights_only=True)["epoch"], 2
            )

        self.assertIn("_atomic_torch_save(model.state_dict(), model_path)", self.source)
        self.assertIn(
            "_atomic_torch_save(checkpoint_identity, checkpoint_path)", self.source
        )

    def test_completed_metrics_write_is_main_final_disk_action(self):
        main_functions = [
            node
            for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        ]
        self.assertEqual(len(main_functions), 1)
        final_statement = main_functions[0].body[-1]
        self.assertIsInstance(final_statement, ast.Expr)
        self.assertIsInstance(final_statement.value, ast.Call)
        self.assertIsInstance(final_statement.value.func, ast.Name)
        self.assertEqual(final_statement.value.func.id, "_write_json")
        self.assertEqual(
            [ast.unparse(argument) for argument in final_statement.value.args],
            ["metrics_path", "metrics"],
        )


class V5Innovation002ExperimentPlanTest(unittest.TestCase):
    @staticmethod
    def _expected_files():
        configs = [
            INNOVATION_002_CONFIG_DIRECTORY / f"{run_id}.yaml"
            for run_id in INNOVATION_002_RUN_SPECS
        ]
        return [*configs, INNOVATION_002_MATRIX_CSV, INNOVATION_002_MATRIX_MD]

    def setUp(self):
        missing = [path for path in self._expected_files() if not path.is_file()]
        if missing and self._testMethodName != "test_all_experiment_plan_files_exist":
            self.skipTest("V5-INNOVATION-002 实验配置与参数矩阵尚未创建")

    def test_all_experiment_plan_files_exist(self):
        missing = [str(path) for path in self._expected_files() if not path.is_file()]
        self.assertEqual(missing, [], "缺少 V5-INNOVATION-002 实验计划文件")

    def test_configs_are_canonical_plus_only_locked_fusion_fields(self):
        self.assertEqual(
            hashlib.sha256(CANONICAL_V5_CONFIG.read_bytes()).hexdigest(),
            CANONICAL_V5_SHA256,
        )
        canonical_raw = yaml.safe_load(CANONICAL_V5_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(len(canonical_raw), 32)
        training_entry = (
            V5Innovation002TrainingEntryTest._load_training_entry_module()
        )
        actual_names = sorted(
            path.name for path in INNOVATION_002_CONFIG_DIRECTORY.glob("RUN-*.yaml")
        )
        self.assertEqual(
            actual_names,
            [f"RUN-{index:03d}.yaml" for index in range(1, 11)],
        )

        raw_by_run = {}
        bytes_by_run = {}
        for run_id, (mode, seed) in INNOVATION_002_RUN_SPECS.items():
            path = INNOVATION_002_CONFIG_DIRECTORY / f"{run_id}.yaml"
            raw_bytes = path.read_bytes()
            raw = yaml.safe_load(raw_bytes.decode("utf-8"))
            raw_by_run[run_id] = raw
            bytes_by_run[run_id] = raw_bytes

            expected = deepcopy(canonical_raw)
            expected["random_seed"]["value"] = seed
            for stage in expected["lr_stages"]["value"]:
                stage["eta_min"] = float(stage["eta_min"])
            expected["fusion_mode"] = {"value": mode}
            expected["fusion_beta"] = {"value": 0.05}
            self.assertEqual(raw, expected, run_id)
            self.assertEqual(len(raw), 34, run_id)

            config, values, loaded_path, _text, loaded_bytes = (
                training_entry._load_config(path)
            )
            self.assertEqual(loaded_path, path.resolve())
            self.assertEqual(loaded_bytes, raw_bytes)
            self.assertEqual(set(values), training_entry.V5_CONFIG_KEYS)
            self.assertEqual(config.random_seed, seed)
            self.assertEqual(config.fusion_mode, mode)
            self.assertEqual(config.fusion_beta, 0.05)
            self.assertEqual(validate_experiment_config(values), (mode, 0.05))

        for repeated, source in INNOVATION_002_REPEAT_OF.items():
            self.assertEqual(bytes_by_run[repeated], bytes_by_run[source], repeated)
        for left, right in (
            ("RUN-001", "RUN-002"),
            ("RUN-003", "RUN-004"),
            ("RUN-005", "RUN-006"),
            ("RUN-007", "RUN-008"),
            ("RUN-009", "RUN-010"),
        ):
            differing = {
                key
                for key in raw_by_run[left]
                if raw_by_run[left][key] != raw_by_run[right][key]
            }
            self.assertEqual(differing, {"fusion_mode"}, (left, right))

    def test_parameter_matrix_csv_matches_locked_run_design(self):
        with INNOVATION_002_MATRIX_CSV.open(
            "r", encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            self.assertEqual(reader.fieldnames, PARAMETER_MATRIX_COLUMNS)
        self.assertEqual([row["job_id"] for row in rows], list(INNOVATION_002_RUN_SPECS))

        for row in rows:
            run_id = row["job_id"]
            mode, seed = INNOVATION_002_RUN_SPECS[run_id]
            config_path = INNOVATION_002_CONFIG_DIRECTORY / f"{run_id}.yaml"
            expected_config_ref = f"configs/{run_id}.yaml"
            expected_repeat = INNOVATION_002_REPEAT_OF.get(run_id, "")
            stage_two = run_id in {"RUN-007", "RUN-008", "RUN-009", "RUN-010"}

            self.assertEqual(row["work_item_id"], "V5-INNOVATION-002")
            self.assertEqual(row["job_kind"], "innovation")
            self.assertEqual(row["status"], "planned")
            self.assertEqual(row["group"], "stage2" if stage_two else "stage1")
            self.assertEqual(row["base_version"], "v5")
            self.assertEqual(row["base_config_sha256"], CANONICAL_V5_SHA256)
            self.assertEqual(row["code_ref"], "model/v5-template-v1")
            self.assertEqual(row["config_snapshot_ref"], expected_config_ref)
            self.assertEqual(row["seed"], str(seed))
            self.assertEqual(
                json.loads(row["changed_parameters"]),
                {"fusion_beta": 0.05, "fusion_mode": mode},
            )
            self.assertEqual(
                row["config_fingerprint"],
                hashlib.sha256(config_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(row["repeat_of"], expected_repeat)
            self.assertEqual(
                row["duplicate_resolution"],
                "exact_repeat" if expected_repeat else "unique_config",
            )
            self.assertTrue(row["name"])
            self.assertTrue(row["purpose"])
            self.assertEqual(
                row["decision"],
                "blocked_by_stage1_gate" if stage_two else "",
            )
            for field in (
                "run_id",
                "run_start_receipt_ref",
                "run_start_receipt_sha256",
                "run_command_sha256",
                "run_log_sha256",
                "run_exit_code",
                "U",
                "S",
                "H",
                "ZS",
                "best_epoch",
                "artifact_ref",
                "artifact_manifest_sha256",
            ):
                self.assertEqual(row[field], "", (run_id, field))

        rows_by_id = {row["job_id"]: row for row in rows}
        for repeated, source in INNOVATION_002_REPEAT_OF.items():
            self.assertEqual(
                rows_by_id[repeated]["config_fingerprint"],
                rows_by_id[source]["config_fingerprint"],
            )

    def test_parameter_matrix_markdown_is_complete_readable_view(self):
        text = INNOVATION_002_MATRIX_MD.read_text(encoding="utf-8")
        self.assertIn("# 参数矩阵：INNOVATION-002_scale_consistent_fusion", text)
        self.assertIn("同目录的 `PARAMETER_MATRIX.csv`", text)
        self.assertIn("来源：V5-INNOVATION-002 预注册十行计划", text)
        table_run_ids = [
            line.split("|")[1].strip()
            for line in text.splitlines()
            if line.startswith("| RUN-")
        ]
        self.assertEqual(table_run_ids, list(INNOVATION_002_RUN_SPECS))
        table_lines = [
            line for line in text.splitlines() if line.startswith("| RUN-")
        ]
        lines_by_run = {
            run_id: line for run_id, line in zip(table_run_ids, table_lines)
        }
        for run_id, (mode, seed) in INNOVATION_002_RUN_SPECS.items():
            line = lines_by_run[run_id]
            self.assertIn("| innovation | planned |", line)
            self.assertIn(
                json.dumps(
                    {"fusion_beta": 0.05, "fusion_mode": mode},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                line,
            )
            self.assertIn(f"| {seed} |", line)
        for repeated, source in INNOVATION_002_REPEAT_OF.items():
            self.assertIn(f"| {source} |", lines_by_run[repeated])
        self.assertEqual(
            sum("blocked_by_stage1_gate" in line for line in table_lines), 4
        )


class V5ScaleConsistentFusionTest(unittest.TestCase):
    @staticmethod
    def _formal_values(**overrides):
        values = {
            "fusion_mode": "legacy",
            "fusion_beta": 0.05,
            "local_weight": 0.2,
            "score_mode": "add",
            "random_seed": 5,
        }
        values.update(overrides)
        return values

    def test_runtime_guard_normalizes_every_allowed_formal_fusion_config(self):
        for mode in ("legacy", "scale_consistent"):
            for seed in (5, 17, 29):
                with self.subTest(mode=mode, seed=seed):
                    self.assertEqual(
                        validate_experiment_config(
                            self._formal_values(fusion_mode=mode, random_seed=seed)
                        ),
                        (mode, 0.05),
                    )

    def test_runtime_guard_rejects_beta_other_than_formal_value(self):
        for beta in (0.1, float("nan"), float("inf")):
            with self.subTest(beta=beta):
                with self.assertRaisesRegex(ValueError, "0.05"):
                    validate_experiment_config(self._formal_values(fusion_beta=beta))

    def test_runtime_guard_rejects_unknown_fusion_mode(self):
        for mode in ("unknown", ["legacy"]):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(ValueError, "fusion_mode"):
                    validate_experiment_config(self._formal_values(fusion_mode=mode))

    def test_runtime_guard_rejects_non_template_weight_or_score_mode(self):
        for overrides in ({"local_weight": 0.1}, {"score_mode": "mean"}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    validate_experiment_config(self._formal_values(**overrides))

    def test_runtime_guard_rejects_seed_outside_formal_set(self):
        for seed in (7, 5.0, True, [5]):
            with self.subTest(seed=seed):
                with self.assertRaisesRegex(ValueError, "random_seed"):
                    validate_experiment_config(self._formal_values(random_seed=seed))

    def test_prepare_run_directory_never_overwrites_existing_run(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = Path(temporary_directory) / "RUN-001"
            run_directory.mkdir()
            marker = run_directory / "marker.txt"
            marker.write_text("keep me", encoding="utf-8")
            members_before = sorted(path.name for path in run_directory.iterdir())

            with self.assertRaises(FileExistsError):
                prepare_run_directory(run_directory, "RUN-001")

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep me")
            self.assertEqual(
                sorted(path.name for path in run_directory.iterdir()), members_before
            )

            run_file = Path(temporary_directory) / "RUN-002"
            run_file.write_text("keep this file", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                prepare_run_directory(run_file, "RUN-002")

            self.assertEqual(run_file.read_text(encoding="utf-8"), "keep this file")

    def test_prepare_run_directory_rejects_path_with_other_run_id(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = Path(temporary_directory) / "RUN-002"

            with self.assertRaises(ValueError):
                prepare_run_directory(run_directory, "RUN-001")

            self.assertFalse(run_directory.exists())

    def test_prepare_run_directory_creates_only_missing_valid_run_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_directory = Path(temporary_directory) / "parent" / "RUN-001"

            result = prepare_run_directory(run_directory, "RUN-001")

            self.assertEqual(result, run_directory.resolve())
            self.assertTrue(run_directory.is_dir())
            self.assertEqual(list(run_directory.iterdir()), [])

    def test_prepare_run_directory_rejects_malformed_run_id_without_creating(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            for run_id in ("RUN-01", "RUN-１２３", "RUN-١٢٣"):
                with self.subTest(run_id=run_id):
                    run_directory = Path(temporary_directory) / "parent" / run_id

                    with self.assertRaises(ValueError):
                        prepare_run_directory(run_directory, run_id)

                    self.assertFalse(run_directory.exists())

    def _make_model(self, mode=None, beta=None):
        config = deepcopy(_parity_config())
        if mode is not None:
            config.fusion_mode = mode
        if beta is not None:
            config.fusion_beta = beta

        torch.manual_seed(17)
        seen = torch.tensor([0, 2, 3, 5])
        unseen = torch.tensor([1, 4])
        seen_text = torch.randn(4, 16)
        unseen_text = torch.randn(2, 16)
        seen_sentence_embeds = torch.randn(4, 3, 16)
        return GTPJ(
            config,
            seen,
            unseen,
            seen_text,
            unseen_text,
            seen_sentence_embeds=seen_sentence_embeds,
        )

    def test_scale_consistent_fusion_uses_shared_temperature_numerically(self):
        final_logits = fuse_global_local_logits(
            torch.tensor([[3.0, -1.0]]),
            torch.tensor([[2.0, 4.0]]),
            logit_scale=torch.tensor(10.0),
            fusion_mode="scale_consistent",
            fusion_beta=0.05,
        )

        torch.testing.assert_close(final_logits, torch.tensor([[4.0, 1.0]]))

    def test_scale_consistent_fusion_preserves_local_and_scale_gradients(self):
        local_logits = torch.tensor([[2.0, 4.0]], requires_grad=True)
        logit_scale = torch.tensor(10.0, requires_grad=True)
        final_logits = fuse_global_local_logits(
            torch.tensor([[3.0, -1.0]]),
            local_logits,
            logit_scale=logit_scale,
            fusion_mode="scale_consistent",
            fusion_beta=0.05,
        )

        final_logits.sum().backward()

        torch.testing.assert_close(local_logits.grad, torch.full((1, 2), 0.5))
        torch.testing.assert_close(logit_scale.grad, torch.tensor(0.3))

    def test_zero_local_logits_match_legacy_and_scale_consistent_modes(self):
        global_logits = torch.tensor([[3.0, -1.0]])
        local_logits = torch.zeros_like(global_logits)
        legacy_logits = fuse_global_local_logits(
            global_logits,
            local_logits,
            logit_scale=torch.tensor(10.0),
            fusion_mode="legacy",
            fusion_beta=0.05,
        )
        scale_logits = fuse_global_local_logits(
            global_logits,
            local_logits,
            logit_scale=torch.tensor(10.0),
            fusion_mode="scale_consistent",
            fusion_beta=0.05,
        )

        torch.testing.assert_close(scale_logits, legacy_logits)

    def test_fusion_function_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "fusion_mode"):
            fuse_global_local_logits(
                torch.tensor([[3.0, -1.0]]),
                torch.tensor([[2.0, 4.0]]),
                logit_scale=torch.tensor(10.0),
                fusion_mode="unknown",
                fusion_beta=0.05,
            )

    def test_fusion_function_rejects_invalid_beta(self):
        for beta in (float("nan"), float("inf"), 0.0, -0.1):
            with self.subTest(beta=beta):
                with self.assertRaisesRegex(ValueError, "fusion_beta"):
                    fuse_global_local_logits(
                        torch.tensor([[3.0, -1.0]]),
                        torch.tensor([[2.0, 4.0]]),
                        logit_scale=torch.tensor(10.0),
                        fusion_mode="scale_consistent",
                        fusion_beta=beta,
                    )

    def test_model_constructor_rejects_unknown_mode(self):
        with self.assertRaisesRegex(ValueError, "fusion_mode"):
            self._make_model("unknown")

    def test_model_constructor_rejects_invalid_beta(self):
        for beta in (float("nan"), float("inf"), 0.0, -0.1):
            with self.subTest(beta=beta):
                with self.assertRaisesRegex(ValueError, "fusion_beta"):
                    self._make_model("scale_consistent", beta)

    def test_missing_fusion_settings_default_to_legacy_formula(self):
        model = self._make_model()
        model.eval()
        torch.manual_seed(31)
        features = torch.randn(2, 577, 16)

        with torch.no_grad():
            outputs = model(features, is_train=False)

        expected = outputs["global_logits"] + 0.2 * outputs["local_logits"]
        torch.testing.assert_close(outputs["final_logits"], expected)

    def test_scale_consistent_train_and_eval_outputs_keep_contract(self):
        model = self._make_model("scale_consistent")
        model.eval()
        torch.manual_seed(37)
        features = torch.randn(2, 577, 16)

        with torch.no_grad():
            eval_outputs = model(features, is_train=False)
            train_outputs = model(features, is_train=True)

        self.assertEqual(tuple(eval_outputs["logits"].shape), (2, 6))
        torch.testing.assert_close(
            train_outputs["logits"],
            train_outputs["final_logits"][:, model.seenclass],
        )
        torch.testing.assert_close(eval_outputs["clip_S_pp"], eval_outputs["logits"])
        self.assertEqual(tuple(eval_outputs["global_logits"].shape), (2, 6))
        self.assertEqual(tuple(eval_outputs["local_logits"].shape), (2, 6))

    def test_scale_consistent_model_uses_shared_temperature(self):
        model = self._make_model("scale_consistent")
        model.eval()
        for target_scale in (20.0, 200.0):
            with self.subTest(target_scale=target_scale):
                torch.manual_seed(23)
                features = torch.randn(2, 577, 16)

                with torch.no_grad():
                    model.logit_scale.copy_(torch.tensor(math.log(target_scale)))
                    outputs = model(features, is_train=False)

                expected_scale = min(target_scale, 100.0)
                expected = (
                    outputs["global_logits"]
                    + 0.05 * expected_scale * outputs["local_logits"]
                )
                torch.testing.assert_close(outputs["final_logits"], expected)

    def test_legacy_mode_keeps_fixed_local_weight(self):
        model = self._make_model("legacy")
        torch.manual_seed(29)
        features = torch.randn(2, 577, 16)

        model.eval()
        with torch.no_grad():
            outputs = model(features, is_train=False)

        expected = outputs["global_logits"] + 0.2 * outputs["local_logits"]
        torch.testing.assert_close(outputs["final_logits"], expected)


if __name__ == "__main__":
    unittest.main()
