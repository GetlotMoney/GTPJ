# V5 全局—局部分数尺度一致融合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不改变冻结母版分支的前提下，为 V5 实验分支增加可关闭的尺度一致融合路线，并按“同 seed 各三次，通过后补两个 seed”的预注册计划完成本地实验。

**Architecture:** `model/MyModel.py` 在实验分支内保留旧公式作为默认路径，只在配置明确选择 `scale_consistent` 时用共同 `logit_scale` 重算最终 logits；母版配置和 `train_GTPJ_CUB.py` 不改。新增实验专用训练入口，显式接收只读数据根目录和不可覆盖的 RUN 输出目录。实验记录全部写入 `V5-INNOVATION-002`，第一阶段六次交替串行执行。

**Tech Stack:** Python 3.10、PyTorch、标准库 `unittest`、YAML、Git worktree、CUB 缓存特征、RTX 5070 Ti。

---

## 文件结构

### 新建

- `tests/test_v5_scale_consistent_fusion.py`：尺度公式、模型接线、配置和输出隔离测试。
- `tools/v5_innovation_002_runtime.py`：实验配置校验、数据路径和不可覆盖 RUN 目录辅助函数。
- `train_V5_INNOVATION_002_CUB.py`：本实验唯一训练入口；训练和评估数学沿用母版。
- `idea_tree/ideas/IDEA-0004_scale_consistent_fusion/IDEA.md`：本地代码诊断产生的候选创意。
- `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/`：实验身份、矩阵、配置、实现、可本地打开的 `framework_diagram.html` 和结果记录。

### 修改

- `model/MyModel.py`：增加默认关闭的尺度一致融合路径；旧公式原样保留。
- `idea_tree/idea_tree.json`、`idea_tree/versions/v5.md`：登记 IDEA-0004。
- `experiments/v5/innovation/INDEX.md`、`experiments/v5/EXPERIMENTS.md`、`experiments/PARAMETER_MATRIX_CATALOG.md`、`experiments/EXPERIMENT_REGISTRY.md`：登记 V5-INNOVATION-002；以本地 `main@4f29e99` 的已完成消融台账为底做定点追加，不能用冻结母版中的旧视图覆盖。
- `docs/TECH_STACK_HISTORY.md`：新增 `MODEL-V5-SCALE-FUSION-CANDIDATE-V1`，开跑前标为计划中，结果完成后更新状态。
- `docs/PROJECT_STRUCTURE.md`：登记新训练入口、新运行保护工具和计划目录职责。

### 明确不修改

- `config/versions/v5.yaml`
- `config/GTPJ_cub_gzsl.yaml`
- `experiments/v5/config.yaml`
- `experiments/v5/baseline/config.yaml`
- `experiments/v5/TEMPLATE.yaml`（保持冻结代码提交内的 V0 历史登记原样；实验身份另记 V1 登记提交 `7da3c72`）
- `train_GTPJ_CUB.py`
- 当前主工作区及其他 worktree 的任何文件

## Task 1：建立尺度公式的 RED 测试

**Files:**
- Create: `tests/test_v5_scale_consistent_fusion.py`
- Read: `tests/test_v5_template_contract.py:234`
- Read: `model/MyModel.py:554`

- [ ] **Step 1: 写模型行为失败测试**

先只导入现有 `GTPJ`，不给生产代码添加新符号。使用现有小维度配置构造模型：

```python
import copy
import unittest

import torch

from model.MyModel import GTPJ
from tests.test_v5_template_contract import _parity_config


class V5ScaleConsistentFusionTest(unittest.TestCase):
    def _make_model(self, mode):
        config = copy.deepcopy(_parity_config())
        config.fusion_mode = mode
        config.fusion_beta = 0.05
        torch.manual_seed(17)
        return GTPJ(
            config,
            torch.tensor([0, 2, 3, 5]),
            torch.tensor([1, 4]),
            torch.randn(4, 16),
            torch.randn(2, 16),
            seen_sentence_embeds=torch.randn(4, 3, 16),
        )

    def test_scale_consistent_model_uses_shared_temperature(self):
        model = self._make_model("scale_consistent")
        features = torch.randn(2, 577, 16)
        output = model(features, is_train=False)
        scale = torch.clamp(model.logit_scale.exp(), max=100.0)
        expected = (
            output["global_logits"]
            + 0.05 * scale * output["local_logits"]
        )
        torch.testing.assert_close(output["final_logits"], expected)
```

- [ ] **Step 2: 运行并确认正确失败**

Run:

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_scale_consistent_fusion.V5ScaleConsistentFusionTest.test_scale_consistent_model_uses_shared_temperature -v
```

Expected: `FAIL`，实际仍是 `global + 0.2 * local`，与共同温度公式不一致；不能是导入、shape 或设备错误。

## Task 2：最小实现尺度一致融合

**Files:**
- Modify: `model/MyModel.py:1`
- Modify: `model/MyModel.py:371`
- Modify: `model/MyModel.py:586`
- Test: `tests/test_v5_scale_consistent_fusion.py`

- [ ] **Step 1: 增加纯函数和默认字段**

在 `model/MyModel.py` 增加：

```python
import math


LEGACY_FUSION_MODE = "legacy"
SCALE_CONSISTENT_FUSION_MODE = "scale_consistent"
FORMAL_SCALE_FUSION_BETA = 0.05


def fuse_global_local_logits(
    global_logits,
    local_logits,
    *,
    logit_scale,
    fusion_mode=LEGACY_FUSION_MODE,
    fusion_beta=FORMAL_SCALE_FUSION_BETA,
):
    if fusion_mode == LEGACY_FUSION_MODE:
        return global_logits + 0.2 * local_logits
    if fusion_mode == SCALE_CONSISTENT_FUSION_MODE:
        return global_logits + fusion_beta * logit_scale * local_logits
    raise ValueError(f"不支持的 fusion_mode：{fusion_mode!r}")
```

在 `GTPJ.__init__` 中读取但不要求母版配置提供新字段：

```python
self.fusion_mode = str(getattr(config, "fusion_mode", LEGACY_FUSION_MODE))
self.fusion_beta = float(
    getattr(config, "fusion_beta", FORMAL_SCALE_FUSION_BETA)
)
```

在 forward 中保留母版原句，再只对新模式覆盖：

```python
final_logits = global_logits + 0.2 * local_logits
if self.fusion_mode == SCALE_CONSISTENT_FUSION_MODE:
    final_logits = fuse_global_local_logits(
        global_logits,
        local_logits,
        logit_scale=logit_scale,
        fusion_mode=self.fusion_mode,
        fusion_beta=self.fusion_beta,
    )
```

- [ ] **Step 2: 运行刚才的测试并确认变绿**

Run: 与 Task 1 Step 2 相同。

Expected: `OK`。

- [ ] **Step 3: 立即回归母版公式与历史等价测试**

Run:

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_fae_memory_jepa tests.test_v5_template_contract -v
```

Expected: 原测试全部 `OK`；特别是母版缺少新字段时仍走原始公式。

## Task 3：补齐公式边界与梯度的 RED/GREEN

**Files:**
- Modify: `tests/test_v5_scale_consistent_fusion.py`
- Modify: `model/MyModel.py`

- [ ] **Step 1: 添加纯函数、梯度和错误输入测试**

追加以下独立测试：

```python
from model.MyModel import fuse_global_local_logits


def test_scale_consistent_formula_uses_shared_temperature(self):
    global_logits = torch.tensor([[3.0, -1.0]])
    local_logits = torch.tensor([[2.0, 4.0]])
    scale = torch.tensor(10.0)
    actual = fuse_global_local_logits(
        global_logits,
        local_logits,
        logit_scale=scale,
        fusion_mode="scale_consistent",
        fusion_beta=0.05,
    )
    torch.testing.assert_close(actual, torch.tensor([[4.0, 1.0]]))

def test_scale_consistent_gradient_reaches_local_and_temperature(self):
    global_logits = torch.tensor([[3.0, -1.0]])
    local_logits = torch.tensor([[2.0, 4.0]], requires_grad=True)
    scale = torch.tensor(10.0, requires_grad=True)
    result = fuse_global_local_logits(
        global_logits,
        local_logits,
        logit_scale=scale,
        fusion_mode="scale_consistent",
        fusion_beta=0.05,
    )
    result.sum().backward()
    torch.testing.assert_close(local_logits.grad, torch.full_like(local_logits, 0.5))
    torch.testing.assert_close(scale.grad, torch.tensor(0.3))

def test_scale_consistent_model_preserves_train_eval_slicing(self):
    model = self._make_model("scale_consistent")
    model.eval()
    features = torch.randn(2, 577, 16)
    with torch.no_grad():
        eval_output = model(features, is_train=False)
        train_output = model(features, is_train=True)
    self.assertEqual(eval_output["logits"].shape, (2, 6))
    torch.testing.assert_close(
        train_output["logits"],
        train_output["final_logits"][:, model.seenclass],
    )
    torch.testing.assert_close(train_output["clip_S_pp"], train_output["logits"])
    self.assertEqual(train_output["global_logits"].shape, (2, 6))
    self.assertEqual(train_output["local_logits"].shape, (2, 6))

def test_zero_local_logits_make_both_modes_equal(self):
    global_logits = torch.tensor([[3.0, -1.0]])
    local_logits = torch.zeros_like(global_logits)
    legacy = fuse_global_local_logits(
        global_logits,
        local_logits,
        logit_scale=torch.tensor(10.0),
        fusion_mode="legacy",
        fusion_beta=0.05,
    )
    aligned = fuse_global_local_logits(
        global_logits,
        local_logits,
        logit_scale=torch.tensor(10.0),
        fusion_mode="scale_consistent",
        fusion_beta=0.05,
    )
    torch.testing.assert_close(legacy, aligned)

def test_invalid_fusion_mode_is_rejected(self):
    with self.assertRaisesRegex(ValueError, "fusion_mode"):
        fuse_global_local_logits(
            torch.zeros(1, 2),
            torch.zeros(1, 2),
            logit_scale=torch.tensor(10.0),
            fusion_mode="unknown",
            fusion_beta=0.05,
        )

def test_invalid_beta_is_rejected(self):
    for beta in (float("nan"), float("inf"), 0.0, -0.1):
        with self.subTest(beta=beta):
            with self.assertRaisesRegex(ValueError, "fusion_beta"):
                fuse_global_local_logits(
                    torch.zeros(1, 2),
                    torch.zeros(1, 2),
                    logit_scale=torch.tensor(10.0),
                    fusion_mode="scale_consistent",
                    fusion_beta=beta,
                )
```

- [ ] **Step 2: 运行并确认 beta 边界测试失败**

Run:

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_scale_consistent_fusion -v
```

Expected: 非法 beta 测试 `FAIL`，因为 Task 2 只完成最小公式，还没有 beta 校验；已有公式测试保持通过。

- [ ] **Step 3: 添加最小校验**

在纯函数最前面加入：

```python
if fusion_mode not in {LEGACY_FUSION_MODE, SCALE_CONSISTENT_FUSION_MODE}:
    raise ValueError(f"不支持的 fusion_mode：{fusion_mode!r}")
if not math.isfinite(float(fusion_beta)) or float(fusion_beta) <= 0:
    raise ValueError("fusion_beta 必须是有限正数。")
```

并在 `GTPJ.__init__` 调用一次纯函数校验所需字段，或抽出相同的 `validate_fusion_settings`，避免非法配置等到首个 batch 才失败。

- [ ] **Step 4: 重跑新测试与母版回归**

Run:

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_scale_consistent_fusion tests.test_fae_memory_jepa tests.test_v5_template_contract -v
```

Expected: 全部 `OK`。

## Task 4：为配置和不可覆盖输出写 RED 测试

**Files:**
- Modify: `tests/test_v5_scale_consistent_fusion.py`
- Create: `tools/v5_innovation_002_runtime.py`

- [ ] **Step 1: 写运行时辅助函数的失败测试**

测试希望使用下面的 API：

```python
from tools.v5_innovation_002_runtime import (
    prepare_run_directory,
    validate_experiment_config,
)
```

测试内容：

```python
def test_formal_config_locks_beta(self):
    values = {
        "fusion_mode": "scale_consistent",
        "fusion_beta": 0.1,
        "local_weight": 0.2,
        "score_mode": "add",
        "random_seed": 5,
    }
    with self.assertRaisesRegex(ValueError, "0.05"):
        validate_experiment_config(values)

def test_existing_run_directory_is_rejected_without_writing(self):
    with tempfile.TemporaryDirectory() as temporary:
        run_dir = Path(temporary) / "RUN-001"
        run_dir.mkdir()
        marker = run_dir / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            prepare_run_directory(run_dir, "RUN-001")
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

def test_new_run_directory_must_match_run_id(self):
    with tempfile.TemporaryDirectory() as temporary:
        with self.assertRaisesRegex(ValueError, "RUN-001"):
            prepare_run_directory(Path(temporary) / "RUN-002", "RUN-001")
```

- [ ] **Step 2: 运行并确认导入错误**

Run: 新测试模块完整命令。

Expected: `ModuleNotFoundError: tools.v5_innovation_002_runtime`。

- [ ] **Step 3: 实现运行时辅助文件**

文件必须包含：

```python
from pathlib import Path


FORMAL_FUSION_BETA = 0.05
ALLOWED_FUSION_MODES = {"legacy", "scale_consistent"}


def validate_experiment_config(values):
    mode = str(values["fusion_mode"])
    beta = float(values["fusion_beta"])
    if mode not in ALLOWED_FUSION_MODES:
        raise ValueError(f"fusion_mode 必须是 {sorted(ALLOWED_FUSION_MODES)}。")
    if beta != FORMAL_FUSION_BETA:
        raise ValueError("正式实验的 fusion_beta 必须固定为 0.05。")
    if float(values["local_weight"]) != 0.2 or values["score_mode"] != "add":
        raise ValueError("母版 local_weight=0.2 和 score_mode=add 不得改变。")
    if int(values["random_seed"]) not in {5, 17, 29}:
        raise ValueError("本实验 seed 只允许 5、17、29。")
    return mode, beta


def prepare_run_directory(path, run_id):
    run_dir = Path(path).resolve()
    if run_dir.name != run_id:
        raise ValueError(f"输出目录末级必须是 {run_id}。")
    if run_dir.exists():
        raise FileExistsError(f"RUN 目录已存在，拒绝覆盖：{run_dir}")
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir()
    return run_dir
```

- [ ] **Step 4: 重跑并确认运行时测试通过**

Expected: `OK`，原目录内 marker 未被修改。

## Task 5：增加实验专用训练入口

**Files:**
- Create: `train_V5_INNOVATION_002_CUB.py`
- Modify: `tests/test_v5_scale_consistent_fusion.py`
- Reference only: `train_GTPJ_CUB.py`

- [ ] **Step 1: 先写入口静态边界测试**

测试读取新入口源码并断言：

```python
source = (ROOT / "train_V5_INNOVATION_002_CUB.py").read_text(encoding="utf-8")
self.assertIn('parser.add_argument("--data-root"', source)
self.assertIn('parser.add_argument("--run-dir"', source)
self.assertIn('parser.add_argument("--run-id"', source)
self.assertIn('load_v5_cub_split(DATA_RES101_PATH, DATA_SPLIT_PATH, "cpu")', source)
self.assertIn('log_path = run_dir / "training.log"', source)
self.assertIn('model_path = run_dir / "model_best.pth"', source)
self.assertNotIn('Path("./train_log/CUB")', source)
```

- [ ] **Step 2: 运行并确认文件不存在而失败**

Expected: `FileNotFoundError` 指向实验专用入口。

- [ ] **Step 3: 从母版入口创建实验专用入口并只做以下差异**

- 标题和 checkpoint 身份改为 `MODEL-V5-SCALE-FUSION-CANDIDATE-V1`。
- 配置键在母版集合上只新增 `fusion_mode`、`fusion_beta`。
- 调用 `validate_experiment_config(values)`；不允许其他额外键。
- 参数必须包含 `--config`、`--data-root`、`--run-dir`、`--run-id`；本轮不提供续训。
- 数据文件全部由 `--data-root` 拼出，禁止创建或写入数据目录。
- `load_v5_cub_split` 的 device 参数固定为 `"cpu"`，模型构造后再迁移到 `config.device`。
- 调用 `prepare_run_directory` 后，固定输出：

```python
log_path = run_dir / "training.log"
model_path = run_dir / "model_best.pth"
checkpoint_path = run_dir / "checkpoint_last.pth"
metrics_path = run_dir / "metrics.json"
```

- 每次更好 H 只覆盖当前 RUN 内的 `model_best.pth`；不生成一串历史 best 文件。
- `metrics.json` 最终包含 `run_id`、`experiment_id`、`model_id`、`code_commit`、`config_sha256`、`seed`、`fusion_mode`、`fusion_beta`、`U/S/H/ZS`、`best_epoch`、初始/最佳 epoch/最终 `logit_scale`。
- 日志打印同样身份；不修改训练 batch、优化器、学习率、损失、评估函数和 U/S/H/ZS 计算。

- [ ] **Step 4: 运行入口边界测试和 `--help`**

Run:

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_scale_consistent_fusion -v
F:\Anaconda\envs\dvsr_gpu\python.exe train_V5_INNOVATION_002_CUB.py --help
```

Expected: 测试 `OK`；帮助输出包含四个必需参数且不加载数据或 GPU。

## Task 6：创建实验配置和逐 RUN 参数表

**Files:**
- Create: `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/configs/RUN-001.yaml` through `RUN-010.yaml`
- Create: `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/PARAMETER_MATRIX.csv`
- Create: `experiments/v5/innovation/INNOVATION-002_scale_consistent_fusion/PARAMETER_MATRIX.md`
- Modify: `tests/test_v5_scale_consistent_fusion.py`

- [ ] **Step 1: 先写配置差异测试**

读取 10 份 YAML，要求：

```text
RUN-001/003/005: seed=5, fusion_mode=legacy
RUN-002/004/006: seed=5, fusion_mode=scale_consistent
RUN-007: seed=17, fusion_mode=legacy
RUN-008: seed=17, fusion_mode=scale_consistent
RUN-009: seed=29, fusion_mode=legacy
RUN-010: seed=29, fusion_mode=scale_consistent
全部 fusion_beta=0.05
```

同一对配置在展开 `value` 后只允许 `fusion_mode` 不同；不同 seed 对只再允许 `random_seed` 不同。四份母版配置的 SHA-256 必须保持与任务开始时一致。

- [ ] **Step 2: 运行并确认缺配置而失败**

Expected: `FileNotFoundError` 指向 RUN-001 配置。

- [ ] **Step 3: 从 `experiments/v5/config.yaml` 逐份复制科学参数**

每份只新增：

```yaml
fusion_mode:
  value: legacy  # SCALE 行改为 scale_consistent
fusion_beta:
  value: 0.05
```

并按矩阵设置 `random_seed`。不新增输出路径到科学配置。

- [ ] **Step 4: 建立 10 行矩阵并预登记条件行**

RUN 顺序固定：

```text
RUN-001 legacy seed5 repeat1
RUN-002 scale  seed5 repeat1
RUN-003 legacy seed5 repeat2 repeat_of RUN-001
RUN-004 scale  seed5 repeat2 repeat_of RUN-002
RUN-005 legacy seed5 repeat3 repeat_of RUN-001
RUN-006 scale  seed5 repeat3 repeat_of RUN-002
RUN-007 legacy seed17 stage1_gate_passed 后启动
RUN-008 scale  seed17 stage1_gate_passed 后启动
RUN-009 legacy seed29 stage1_gate_passed 后启动
RUN-010 scale  seed29 stage1_gate_passed 后启动
```

十行初始状态都使用矩阵 schema 已允许的 `planned`；后四行在 `decision` 写 `blocked_by_stage1_gate`，表示只有第一阶段过门后才会启动。这里不调用旧的 `freeze-parameter-matrix` 或 `--require-ready`，而是按 2026-08-08 五步短流程由唯一运行前提交冻结代码与配置。

- [ ] **Step 5: 重跑配置测试**

Expected: `OK`，母版四配置哈希未变。

## Task 7：登记 IDEA、实验身份和方法说明

**Files:**
- Create/Modify: 本计划“文件结构”列出的 idea、experiment、index 和技术演进文件。

- [ ] **Step 1: 写 IDEA-0004**

来源字段固定为：

```yaml
source_type: observation
source_status: local_heuristic
source_ref: model/v5-template-v1:model/MyModel.py score-scale audit
base_version: v5
hypothesis: 将局部分数转换到全局分数相同温度尺度后，局部分支可能产生稳定 H 增益
```

不得写成论文来源或 verified novelty。

- [ ] **Step 2: 写 EXPERIMENT.yaml**

必须同时记录：

```yaml
experiment_id: V5-INNOVATION-002
framework_id: FRAMEWORK-V5
kind: innovation
base_identity_kind: framework_template
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
template_registry_commit: 7da3c72a060510ad35dd66d839cbe22569b3d8cf
experiment_branch: exp/v5/innovation/innovation-002-scale-consistent-fusion
idea_id: IDEA-0004
status: pre_run
not_confirmation_evidence: true
```

同一文件注明 `2f5fa5e` 内嵌 `TEMPLATE.yaml` 仍是 V0，V1 由 `7da3c72` 后登记；这不改变 Tag 指向的代码身份。

- [ ] **Step 3: 写方法与代码流**

- `module_source.md`：区分继承的 CLIP/PSE/ICSA/FGVD/BVSA/SGMP 与本实验新增的一行尺度融合。
- `implementation.md`：列出文件、输入输出、legacy 关闭行为、公式和测试。
- `framework_diagram.md`：画清 `global cosine × scale` 与 `local cosine × beta × scale` 汇合。
- `README.md`：包含 `## Code Flow Diagram`，解释训练 logits 和评估 logits 的出口。
- `result.md`、`quality_check.md` 初始只写 `not_started`，不能提前填写结论。

- [ ] **Step 4: 更新索引与技术历史**

`docs/TECH_STACK_HISTORY.md` 增加“计划中”的 `MODEL-V5-SCALE-FUSION-CANDIDATE-V1`；结果完成后只能更新状态和实测结果，不删除失败记录。

## Task 8：机器验证和独立只读审核

**Files:**
- All changed files

- [ ] **Step 1: 运行相关测试**

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe -m unittest tests.test_v5_scale_consistent_fusion tests.test_fae_memory_jepa tests.test_v5_template_contract tests.test_reproducibility -v
```

Expected: 全部 `OK`。

- [ ] **Step 2: 运行结构和差异检查**

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe workflow\gtpj_workflow.py validate
F:\Anaconda\envs\dvsr_gpu\python.exe workflow\gtpj_workflow.py validate-framework-ledgers
git diff --check
git status --short
```

Expected: 结构检查通过；`git diff --check` 无输出；status 只含本实验预期文件。

- [ ] **Step 3: 做一次独立只读审核**

Reviewer 必须检查：公式、legacy 等价、梯度、seen/unseen 切片、类别顺序、CPU/GPU 边界、输出不可覆盖、十份配置差异和停止门。发现模型或评估语义争议才升级第二轮；没有争议不为凑轮数重复审核。

- [ ] **Step 4: 回应审核并重跑机器验证**

所有阻断问题修复后，重新执行 Step 1 和 Step 2。

## Task 9：创建唯一运行前提交

**Files:**
- All pre-run files

- [ ] **Step 1: 确认不存在意外文件和输出目录**

检查当前 worktree、当前主工作区和计划中的 10 个 RUN 目录。不得删除任何已存在目录；若某个目标存在，改用新的实验 RUN 身份并同步矩阵。

- [ ] **Step 2: 更新技术历史为“实现完成、尚未训练”**

记录验证命令、测试数、已知限制和回退方式。

- [ ] **Step 3: 只暂存本实验文件并提交一次**

```powershell
git add <本实验明确文件清单>
git commit -m "feat: prepare v5 scale-consistent fusion experiment"
```

这是本实验唯一运行前提交；不得把训练结果提前写入。提交后 `git status --short` 必须为空。

## Task 10：运行第一阶段六次训练

**Files:**
- Runtime outputs only under `D:/Backup/Documents/Myself/GTPJ/.runtime/runs/v5/innovation/V5-INNOVATION-002_scale_consistent_fusion/`

- [ ] **Step 1: 一次开跑检查**

记录分支、提交、clean 状态、10 份配置哈希、数据文件身份、CUDA/GPU、系统可用内存、类别顺序、评估函数和所有目标目录不存在。入口会一次载入约 9.84 GiB 缓存，因此可用物理内存低于 14 GiB 时不得启动；若有其他 Python 训练进程占 GPU，不终止它，等待或停止本轮。

- [ ] **Step 2: 串行交替运行**

每个 RUN 使用同一模板：

```powershell
F:\Anaconda\envs\dvsr_gpu\python.exe train_V5_INNOVATION_002_CUB.py `
  --config experiments\v5\innovation\INNOVATION-002_scale_consistent_fusion\configs\RUN-001.yaml `
  --data-root C:\Users\Administrator\Desktop\cv-work\DVSR\data `
  --run-dir D:\Backup\Documents\Myself\GTPJ\.runtime\runs\v5\innovation\V5-INNOVATION-002_scale_consistent_fusion\RUN-001 `
  --run-id RUN-001
```

按 `RUN-001 → 002 → 003 → 004 → 005 → 006` 执行；前一个结束且结果完整后才启动下一个。

- [ ] **Step 3: 应用第一阶段门**

先检查 legacy 三次均值是否落在 `74.17 ± 0.30`。随后同时要求：三对 ΔH 全正、平均 ΔH 至少 `+0.50`、`min(H_scale) > max(H_legacy)`、平均 U/S 任一项下降不超过 `0.30`。

未通过时不启动 RUN-007…010；记录 `stage1_gate_failed_not_started`，保留所有历史。

## Task 11：条件第二阶段与结果回填

**Files:**
- Modify: `PARAMETER_MATRIX.csv/.md`、`result.yaml/md`、`quality_check.md`、`implementation.md`、`docs/TECH_STACK_HISTORY.md`

- [ ] **Step 1: 仅在第一阶段通过后运行 RUN-007…010**

顺序：`RUN-007 → 008 → 009 → 010`，命令只替换 RUN 配置、目录和编号。

- [ ] **Step 2: 按 seed 等权汇总**

seed 5 先取三次均值形成一个 seed 级数值，再与 seed 17、29 等权平均；不让 seed 5 因重复三次获得三倍权重。

- [ ] **Step 3: 写结论**

通过条件：seed 17/29 两对 ΔH 均为正，三个 seed 的等权平均 ΔH 至少 `+0.50`，方向一致，完整报告 U/S/H/ZS。

未通过只写“尺度假设未获稳定支持、停止作为当前论文主线”；不删除局部分支。通过只写“尺度一致融合候选获得支持”；不自动声称所有局部子模块有效，也不自动 promotion。

- [ ] **Step 4: 结果提交**

只提交轻量账本、配置、结果、质量检查和日志/模型引用；raw checkpoint 不进入 Git。最终再次运行相关测试、结构校验和 `git diff --check`。
