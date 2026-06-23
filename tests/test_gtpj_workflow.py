from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "workflow" / "gtpj_workflow.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("gtpj_workflow_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load workflow helper")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WorkflowHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.module = load_helper()
        self.module.REPO_ROOT = self.repo
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Workflow Test")
        self._write_minimal_repo()
        self._git("add", ".")
        self._git("commit", "-m", "seed minimal governance repo")
        self._git("tag", "v1")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=cwd or self.repo,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def _write(self, relative: str, content: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_minimal_repo(self) -> None:
        self._write("experiments/v1/config.yaml", "version: v1\n")
        self._write(
            "experiments/EXPERIMENT_REGISTRY.md",
            "# Experiment Registry\n\n| Experiment | Version | Kind | Status | Directory | Note |\n"
            "|---|---|---|---|---|---|\n| 暂无 | - | - | - | - | - |\n",
        )
        self._write(
            "experiments/v1/confirmation/INDEX.md",
            "# Confirmation Index\n\n| 实验 | 状态 | 目录 | 说明 |\n"
            "|---|---|---|---|\n| 暂无 | - | - | - |\n",
        )

    def _run_main(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.module.main(list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def _registry_text(self) -> str:
        return (self.repo / "experiments/EXPERIMENT_REGISTRY.md").read_text(encoding="utf-8")

    def _confirmation_index_text(self) -> str:
        return (self.repo / "experiments/v1/confirmation/INDEX.md").read_text(encoding="utf-8")

    def test_new_experiment_rejects_main_branch(self) -> None:
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("expected branch exp/v1-confirm-001-v1-seed5", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_dirty_worktree(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-001-v1-seed5")
        self._write("scratch.txt", "dirty\n")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("Working tree must be clean", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_wrong_exp_branch(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-999-other")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("expected branch exp/v1-confirm-001-v1-seed5", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_rejects_expected_branch_not_based_on_main(self) -> None:
        self._git("checkout", "--orphan", "exp/v1-confirm-001-v1-seed5")
        self._git("commit", "-m", "orphan experiment branch")
        registry_before = self._registry_text()
        index_before = self._confirmation_index_text()

        code, _stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual(1, code)
        self.assertIn("new-experiment branch must contain current local main", stderr)
        self.assertFalse((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5").exists())
        self.assertEqual(registry_before, self._registry_text())
        self.assertEqual(index_before, self._confirmation_index_text())

    def test_new_experiment_succeeds_on_expected_clean_branch(self) -> None:
        self._git("switch", "-c", "exp/v1-confirm-001-v1-seed5")

        code, stdout, stderr = self._run_main(
            "new-experiment",
            "--version",
            "v1",
            "--kind",
            "confirmation",
            "--exp-id",
            "CONFIRM-001",
            "--slug",
            "v1_seed5",
        )

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("已创建 experiments/v1/confirmation/CONFIRM-001_v1_seed5", stdout)
        self.assertTrue((self.repo / "experiments/v1/confirmation/CONFIRM-001_v1_seed5/README.md").exists())

    def test_validate_remote_accepts_origin_refs_matching_local_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_accepts_annotated_v1_tag(self) -> None:
        self._git("tag", "-d", "v1")
        self._git("tag", "-a", "v1", "-m", "annotated v1")
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_accepts_main_ahead_of_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._write("governance.md", "main ledger update\n")
            self._git("add", "governance.md")
            self._git("commit", "-m", "add governance ledger")
            self._git("push", "origin", "main", "v1")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_uses_local_main_not_current_feature_head(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._git("switch", "-c", "feature/local-work")
            self._write("feature.txt", "feature-only commit\n")
            self._git("add", "feature.txt")
            self._git("commit", "-m", "feature-only work")

            code, stdout, stderr = self._run_main("validate-remote")

        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        self.assertIn("validate-remote-ok", stdout)

    def test_validate_remote_rejects_branch_named_v1_without_local_tag(self) -> None:
        self._git("tag", "-d", "v1")
        self._git("branch", "v1")

        code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("Missing local authoritative tag: v1", stderr)

    def test_validate_remote_rejects_remote_branch_named_v1_without_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main")
            self._git("push", "origin", "HEAD:refs/heads/v1")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("Missing remote ref: origin/v1 (refs/tags/v1)", stderr)

    def test_validate_remote_rejects_origin_main_ahead_of_local_main(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            local_main = self._git("rev-parse", "main").stdout.strip()
            self._write("remote-ahead.txt", "remote main ahead\n")
            self._git("add", "remote-ahead.txt")
            self._git("commit", "-m", "remote main ahead")
            self._git("push", "origin", "HEAD:refs/heads/main")
            self._git("reset", "--hard", local_main)

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/main", stderr)

    def test_validate_remote_rejects_origin_main_not_matching_local_main(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._write("marker.txt", "new commit\n")
            self._git("add", "marker.txt")
            self._git("commit", "-m", "local main not pushed")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/main", stderr)

    def test_validate_remote_rejects_misaligned_origin_v1_tag(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("push", "origin", "main", "v1")
            self._git("switch", "-c", "move-v1-tag-source")
            self._write("marker.txt", "remote tag moved\n")
            self._git("add", "marker.txt")
            self._git("commit", "-m", "move remote v1 tag only")
            self._git("push", "--force", "origin", "HEAD:refs/tags/v1")
            self._git("switch", "main")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("origin/v1", stderr)

    def test_validate_remote_rejects_local_main_not_containing_v1(self) -> None:
        with tempfile.TemporaryDirectory() as remote_tmp:
            remote = Path(remote_tmp)
            self._git("init", "--bare", cwd=remote)
            self._git("remote", "add", "origin", str(remote))
            self._git("checkout", "--orphan", "rewritten-main")
            self._write("replacement.txt", "replacement main without v1 history\n")
            self._git("add", ".")
            self._git("commit", "-m", "replace main history")
            self._git("branch", "-M", "main")
            self._git("push", "origin", "main", "v1")

            code, _stdout, stderr = self._run_main("validate-remote")

        self.assertEqual(1, code)
        self.assertIn("local main must contain local v1 tag", stderr)


if __name__ == "__main__":
    unittest.main()
