"""Linux 上用无训练子进程验证 V5 消融控制器的真实进程组收口。"""

from pathlib import Path
import os
import signal
import subprocess
import sys
import tempfile
import unittest

from tools import run_v5_ablation_001_server_controller as controller


@unittest.skipUnless(sys.platform == "linux", "正式进程组语义只在 Linux 验证")
class V5AblationLinuxProcessIntegrationTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
