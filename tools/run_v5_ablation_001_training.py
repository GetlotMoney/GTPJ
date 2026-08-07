"""在独立干净代码副本里启动 V5-ABLATION-001 的一项训练。"""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


GROUP_SPECS = {
    "FULL": {"gpu": "0", "entry": "train_GTPJ_CUB.py"},
    "GLOBAL_ONLY": {"gpu": "1", "entry": "train_V5_ABLATION_001_CUB.py"},
}
EXPERIMENT_BRANCH = "exp/v5/ablation/ablation-001-local-branch-effect"
TEMPLATE_TAG = "model/v5-template-v1"


def training_spec(group):
    try:
        return dict(GROUP_SPECS[group])
    except KeyError as exc:
        raise ValueError(f"不支持的实验组：{group}") from exc


def _git(code_root, *args):
    result = subprocess.run(
        ["git", "-C", str(code_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_code_checkout(code_root, commit, group):
    code_root = Path(code_root).resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("--commit 必须是 40 位小写 Git 提交号。")
    if _git(code_root, "rev-parse", "HEAD") != commit:
        raise RuntimeError("训练代码副本 HEAD 与运行前冻结提交不一致。")
    if _git(code_root, "status", "--porcelain"):
        raise RuntimeError("训练代码副本不是干净工作树。")

    spec = training_spec(group)
    entry = code_root / spec["entry"]
    if not entry.is_file():
        raise FileNotFoundError(f"训练入口不存在：{entry}")
    if group == "FULL":
        result = subprocess.run(
            [
                "git",
                "-C",
                str(code_root),
                "diff",
                "--quiet",
                TEMPLATE_TAG,
                "--",
                "model/MyModel.py",
                "train_GTPJ_CUB.py",
                "config/versions/v5.yaml",
            ]
        )
        if result.returncode != 0:
            raise RuntimeError("完整组的母版模型、训练入口或配置已偏离冻结 Tag。")
    else:
        required = [
            code_root / "model" / "V5GlobalOnly.py",
            code_root / "train_V5_ABLATION_001_CUB.py",
        ]
        if any(not path.is_file() for path in required):
            raise FileNotFoundError("无局部组缺少专属模型或训练入口。")
    return entry


def parse_args():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--group", choices=sorted(GROUP_SPECS), required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    config = args.config.resolve()
    code_root = args.code_root.resolve()
    if not config.is_file():
        raise FileNotFoundError(f"冻结配置不存在：{config}")
    entry = validate_code_checkout(code_root, args.commit, args.group)
    spec = training_spec(args.group)

    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = spec["gpu"]
    environment["PYTHONUNBUFFERED"] = "1"
    bound_python = environment.get("GTPJ_BOUND_PYTHON_EXEC", "").strip()
    bound_argv0 = environment.get("GTPJ_BOUND_PYTHON_ARGV0", "").strip()
    if not re.fullmatch(r"/proc/[1-9][0-9]*/fd/[1-9][0-9]*", bound_python):
        raise RuntimeError("正式训练缺少受信 Python 文件描述符。")
    if bound_argv0 != sys.executable:
        raise RuntimeError("受信 Python argv0 与当前解释器不一致。")
    if not Path(bound_python).is_file():
        raise RuntimeError("受信 Python 文件描述符已经失效。")
    os.chdir(code_root)
    os.execve(
        bound_python,
        [sys.executable, str(entry), "--config", str(config)],
        environment,
    )


if __name__ == "__main__":
    main()
