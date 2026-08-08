"""V5-INNOVATION-002 正式运行的最小边界检查。"""

import math
from pathlib import Path
import re


FORMAL_FUSION_BETA = 0.05
ALLOWED_FUSION_MODES = {"legacy", "scale_consistent"}
ALLOWED_SEEDS = {5, 17, 29}
_RUN_ID_PATTERN = re.compile(r"RUN-[0-9]{3}\Z")


def validate_experiment_config(values):
    """检查正式实验不能改变的融合、评分和随机种子边界。"""
    mode = values["fusion_mode"]
    beta = values["fusion_beta"]
    local_weight = values["local_weight"]
    score_mode = values["score_mode"]
    random_seed = values["random_seed"]

    if not isinstance(mode, str) or mode not in ALLOWED_FUSION_MODES:
        raise ValueError(f"fusion_mode 必须是 {sorted(ALLOWED_FUSION_MODES)}")
    try:
        beta_is_finite = math.isfinite(beta)
    except TypeError as error:
        raise ValueError(f"fusion_beta 必须恰为 {FORMAL_FUSION_BETA}") from error
    if not beta_is_finite or beta != FORMAL_FUSION_BETA:
        raise ValueError(f"fusion_beta 必须恰为 {FORMAL_FUSION_BETA}")
    if local_weight != 0.2:
        raise ValueError("local_weight 必须保持母版值 0.2")
    if score_mode != "add":
        raise ValueError("score_mode 必须保持母版值 add")
    if (
        not isinstance(random_seed, int)
        or isinstance(random_seed, bool)
        or random_seed not in ALLOWED_SEEDS
    ):
        raise ValueError(f"random_seed 必须是 {sorted(ALLOWED_SEEDS)}")
    return mode, FORMAL_FUSION_BETA


def prepare_run_directory(path, run_id):
    """只创建一个尚不存在且名称匹配的 RUN 目录，绝不覆盖已有目录。"""
    if not isinstance(run_id, str) or _RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise ValueError("run_id 必须符合 RUN-ddd 格式")

    run_directory = Path(path).resolve()
    if run_directory.name != run_id:
        raise ValueError("路径末级目录必须与 run_id 完全一致")
    if run_directory.exists():
        raise FileExistsError(f"RUN 目录已存在，拒绝覆盖: {run_directory}")

    run_directory.mkdir(parents=True)
    return run_directory
