"""Linux 上用无训练子进程验证 V5 消融控制器的真实进程组收口。"""

from pathlib import Path
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from tools import run_v5_ablation_001_server_controller as controller
from tools import run_v5_ablation_001_training as training
from tools.v5_runtime import input_record


@unittest.skipUnless(sys.platform == "linux", "正式进程组语义只在 Linux 验证")
class V5AblationLinuxProcessIntegrationTest(unittest.TestCase):
    def test_training_wrapper_executes_with_only_bound_roots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkout = root / "checkout"
            data_root = root / "data"
            train_log_root = root / "train_log"
            checkout.mkdir()
            data_root.mkdir()
            train_log_root.mkdir()
            (checkout / "model").mkdir()
            (checkout / "model" / "V5GlobalOnly.py").write_text(
                "# fixture model\n", encoding="utf-8"
            )
            (checkout / "train_V5_ABLATION_001_CUB.py").write_text(
                """import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--data-root", type=Path, required=True)
parser.add_argument("--train-log-root", type=Path, required=True)
args = parser.parse_args()
print((args.data_root / "identity.txt").read_text(), end="")
(args.train_log_root / "wrapper-probe.txt").write_text("ok\\n")
""",
                encoding="utf-8",
            )
            config = root / "RUN-004.yaml"
            config.write_text("fixture: true\n", encoding="utf-8")
            (data_root / "identity.txt").write_text("trusted\n", encoding="utf-8")
            subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=checkout,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=checkout,
                check=True,
            )
            subprocess.run(["git", "add", "--all"], cwd=checkout, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "fixture"],
                cwd=checkout,
                check=True,
            )
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=checkout,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            data_stat = data_root.stat()
            log_stat = train_log_root.stat()
            python_fd = os.open(sys.executable, os.O_RDONLY)
            environment = os.environ.copy()
            environment["GTPJ_BOUND_PYTHON_EXEC"] = (
                f"/proc/{os.getpid()}/fd/{python_fd}"
            )
            environment["GTPJ_BOUND_PYTHON_ARGV0"] = sys.executable
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(
                            Path(__file__).resolve().parents[1]
                            / "tools"
                            / "run_v5_ablation_001_training.py"
                        ),
                        "--config",
                        str(config),
                        "--code-root",
                        str(checkout),
                        "--commit",
                        commit,
                        "--group",
                        "GLOBAL_ONLY",
                        "--data-root",
                        str(data_root),
                        "--train-log-root",
                        str(train_log_root),
                        "--data-device",
                        str(data_stat.st_dev),
                        "--data-inode",
                        str(data_stat.st_ino),
                        "--train-log-device",
                        str(log_stat.st_dev),
                        "--train-log-inode",
                        str(log_stat.st_ino),
                    ],
                    cwd=Path(__file__).resolve().parents[1],
                    env=environment,
                    pass_fds=(python_fd,),
                    check=False,
                    capture_output=True,
                    text=True,
                )
            finally:
                os.close(python_fd)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("trusted\n", result.stdout)
            self.assertEqual(
                "ok\n",
                (train_log_root / "wrapper-probe.txt").read_text(encoding="utf-8"),
            )

    def test_bound_runtime_roots_survive_execve(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_root = root / "data"
            train_log_root = root / "train_log"
            data_root.mkdir()
            train_log_root.mkdir()
            (data_root / "identity.txt").write_text("trusted\n", encoding="utf-8")
            data_stat = data_root.stat()
            log_stat = train_log_root.stat()
            helper = """
import os
from pathlib import Path
import sys
from tools.run_v5_ablation_001_training import bind_runtime_roots

data_root = Path(sys.argv[1])
train_log_root = Path(sys.argv[2])
binding = bind_runtime_roots(
    data_root,
    train_log_root,
    data_device=int(sys.argv[3]),
    data_inode=int(sys.argv[4]),
    train_log_device=int(sys.argv[5]),
    train_log_inode=int(sys.argv[6]),
)
data_root.rename(data_root.with_name("moved_data"))
data_root.mkdir()
(data_root / "identity.txt").write_text("wrong\\n", encoding="utf-8")
probe = (
    "from pathlib import Path; import sys; "
    "print((Path(sys.argv[1])/'identity.txt').read_text(), end=''); "
    "(Path(sys.argv[2])/'execve-probe.txt').write_text('ok\\\\n')"
)
os.execve(
    sys.executable,
    [sys.executable, "-c", probe, binding["data_ref"], binding["train_log_ref"]],
    os.environ.copy(),
)
"""
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    helper,
                    str(data_root),
                    str(train_log_root),
                    str(data_stat.st_dev),
                    str(data_stat.st_ino),
                    str(log_stat.st_dev),
                    str(log_stat.st_ino),
                ],
                cwd=Path(__file__).resolve().parents[1],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("trusted\n", result.stdout)
            self.assertEqual(
                "ok\n",
                (train_log_root / "execve-probe.txt").read_text(encoding="utf-8"),
            )

    def test_bound_runtime_roots_survive_path_replacement(self):
        bind = getattr(training, "bind_runtime_roots", None)
        self.assertIsNotNone(bind)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_root = root / "data"
            train_log_root = root / "train_log"
            data_root.mkdir()
            train_log_root.mkdir()
            (data_root / "identity.txt").write_text("trusted\n", encoding="utf-8")
            data_stat = data_root.stat()
            log_stat = train_log_root.stat()

            with self.assertRaisesRegex(RuntimeError, "被替换"):
                bind(
                    data_root,
                    train_log_root,
                    data_device=data_stat.st_dev,
                    data_inode=data_stat.st_ino + 1,
                    train_log_device=log_stat.st_dev,
                    train_log_inode=log_stat.st_ino,
                )

            binding = bind(
                data_root,
                train_log_root,
                data_device=data_stat.st_dev,
                data_inode=data_stat.st_ino,
                train_log_device=log_stat.st_dev,
                train_log_inode=log_stat.st_ino,
            )
            try:
                moved = root / "moved_data"
                data_root.rename(moved)
                data_root.mkdir()
                (data_root / "identity.txt").write_text("wrong\n", encoding="utf-8")

                self.assertEqual(
                    "trusted\n",
                    (Path(binding["data_ref"]) / "identity.txt").read_text(
                        encoding="utf-8"
                    ),
                )
                self.assertTrue(
                    input_record(Path(binding["data_ref"]) / "identity.txt")[
                        "path"
                    ].startswith("/proc/self/fd/")
                )
                self.assertEqual(
                    train_log_root.stat().st_ino,
                    Path(binding["train_log_ref"]).stat().st_ino,
                )
            finally:
                os.close(binding["data_fd"])
                os.close(binding["train_log_fd"])

    def test_cleanup_stops_and_reaps_real_helper_and_child(self):
        helper = None
        child_pid = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training_log = root / "training.log"
            receipt = root / "run_start_receipt.json"
            helper_code = (
                "import subprocess,sys; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                "print(child.pid, flush=True); "
                "raise SystemExit(child.wait())"
            )
            try:
                helper = subprocess.Popen(
                    [sys.executable, "-c", helper_code],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
                helper_identity = controller.capture_helper_identity(helper)
                assert helper.stdout is not None
                child_pid = int(helper.stdout.readline().strip())
                training_log.write_text(
                    "GTPJ_RUN_START_RECEIPT_SHA256=" + "a" * 64 + "\n"
                    "GTPJ_TRAINING_PROCESS_STARTED command_sha256="
                    + "b" * 64
                    + f" pid={child_pid} started_at=2026-08-07T00:00:00+00:00\n",
                    encoding="utf-8",
                )
                outcome = controller.cleanup_process_tree(
                    helper_process=helper,
                    helper_identity=helper_identity,
                    training_log=training_log,
                    receipt=receipt,
                )
                self.assertTrue(outcome["cleanup_complete"])
                self.assertEqual("process_tree_stopped", outcome["process_evidence_state"])
                self.assertIsNotNone(helper.poll())
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)
            finally:
                if helper is not None and helper.poll() is None:
                    os.killpg(helper.pid, signal.SIGKILL)
                    helper.wait(timeout=5)
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if helper is not None:
                    if helper.stdout is not None:
                        helper.stdout.close()
                    if helper.stderr is not None:
                        helper.stderr.close()

    def test_cleanup_stops_orphan_child_after_helper_already_exited(self):
        helper = None
        child_pid = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            training_log = root / "training.log"
            receipt = root / "run_start_receipt.json"
            helper_code = (
                "import subprocess,sys; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                "print(child.pid, flush=True)"
            )
            try:
                helper = subprocess.Popen(
                    [sys.executable, "-c", helper_code],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
                helper_identity = controller.capture_helper_identity(helper)
                assert helper.stdout is not None
                child_pid = int(helper.stdout.readline().strip())
                helper.wait(timeout=5)
                training_log.write_text(
                    "GTPJ_TRAINING_PROCESS_STARTED command_sha256="
                    + "b" * 64
                    + f" pid={child_pid} started_at=2026-08-07T00:00:00+00:00\n",
                    encoding="utf-8",
                )
                outcome = controller.cleanup_process_tree(
                    helper_process=helper,
                    helper_identity=helper_identity,
                    training_log=training_log,
                    receipt=receipt,
                )
                self.assertTrue(outcome["cleanup_complete"])
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    try:
                        os.kill(child_pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(0.05)
                else:
                    self.fail("孤儿训练子进程没有被回收")
            finally:
                if helper is not None and helper.poll() is None:
                    os.killpg(helper.pid, signal.SIGKILL)
                    helper.wait(timeout=5)
                if child_pid is not None:
                    try:
                        os.kill(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if helper is not None:
                    if helper.stdout is not None:
                        helper.stdout.close()
                    if helper.stderr is not None:
                        helper.stderr.close()


if __name__ == "__main__":
    unittest.main()
