# GTPJ 正式框架只读母版治理实施计划

> **给执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项实施。每一步使用复选框跟踪。

**目标：** 把每个正式框架的代码母版、实验准确起点和现有九个正式实验统一纳入机器可检查的只读母版规则。

**架构：** `framework.yaml` 继续只记录正式框架身份；新增每框架 `TEMPLATE.yaml` 记录可复制代码快照，新增每实验 `EXPERIMENT.yaml` 记录真实历史基点或干净母版基点。工作流在创建实验和启动运行前核对母版 Tag、commit、分支起点和只读状态；旧 Trial/Attempt 原地保留，只通过 `legacy_ref` 映射。

**技术栈：** Python 3 标准库、Git、JSON Schema 子集、YAML 浅层账本、`unittest/pytest`、Markdown/HTML。

---

## 文件职责

| 文件 | 职责 |
|---|---|
| `schemas/framework_template.schema.json` | 定义正式框架母版账本格式。 |
| `schemas/experiment.schema.json` | 定义正式实验代码起点账本格式。 |
| `experiments/templates/TEMPLATE_template.yaml` | 新正式框架建立母版账本时使用。 |
| `experiments/templates/EXPERIMENT_template.yaml` | 新实验建立代码起点账本时使用。 |
| `workflow/gtpj_workflow.py` | 校验母版、实验绑定、精确基点，并生成新实验元数据。 |
| `tests/test_gtpj_workflow.py` | 证明错误 Tag、错误 commit、错分支起点和缺账本会被拦截。 |
| `experiments/v1|v2|v3|v5/TEMPLATE.yaml` | 登记四个历史冻结快照；V0 表示新规范启用前的原始快照。 |
| 九个现有正式实验下的 `EXPERIMENT.yaml` | 如实区分历史只读实验、等待干净母版的计划实验。 |
| `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md` | 唯一正式规范，升级到 `SYS-WORKFLOW-V5`。 |
| `docs/workflow/START_HERE.md`、`WORKFLOW_KERNEL.md` | 日常入口和硬门同步。 |
| `docs/workflow/protocols/git_policy.md`、`versioning.md`、`experiment_protocol.md` | 分支、版本和实验细则同步。 |
| `docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html` | 人类可直接打开的当前母版和实验关系总览。 |
| `docs/TECH_STACK_HISTORY.md` | 把治理和数据版本从“计划中”更新为实际状态。 |

### Task 1：用失败测试锁定母版账本规则

**Files:**
- Modify: `tests/test_gtpj_workflow.py`

- [ ] **Step 1：在测试夹具中写入母版和实验 schema**

增加 `_write_framework_template_schema()` 与 `_write_experiment_schema()` 测试辅助函数，并在需要完整正式框架的测试中写入：

```python
def _write_legacy_template(self, version: str = "v1") -> str:
    commit = self._git("rev-parse", f"{version}^{{commit}}").stdout.strip()
    self._write(
        f"experiments/{version}/TEMPLATE.yaml",
        "schema_version: gtpj.framework_template.v1\n"
        f"framework_id: FRAMEWORK-{version.upper()}\n"
        f"template_id: MODEL-{version.upper()}-TEMPLATE-V0\n"
        "template_status: legacy_frozen\n"
        f"template_branch: framework/{version}\n"
        f"template_tag: {version}\n"
        f"template_commit: {commit}\n"
        f"source_framework_tag: {version}\n"
        f"source_framework_commit: {commit}\n"
        "behavior_contract: none\n",
    )
    return commit
```

- [ ] **Step 2：写三个会失败的母版测试**

```python
def test_framework_template_rejects_tag_commit_mismatch(self) -> None:
    self._write_legacy_template()
    path = self.repo / "experiments/v1/TEMPLATE.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace(
        "template_commit: ", "template_commit: " + "0" * 40 + " # "
    ), encoding="utf-8")
    errors = self.module.validate_framework_templates()
    self.assertTrue(any("template_commit does not match tag" in item for item in errors))

def test_frozen_template_branch_must_not_move_past_tag(self) -> None:
    self._write_legacy_template()
    self._write("marker.txt", "changed\n")
    self._commit_all("move template branch")
    self._git("branch", "-f", "framework/v1", "HEAD")
    errors = self.module.validate_framework_templates()
    self.assertTrue(any("frozen template branch must equal template_commit" in item for item in errors))

def test_active_standard_requires_template_yaml_for_every_framework(self) -> None:
    self._write("docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md", "standard_id: SYS-WORKFLOW-V5\nstatus: active\n")
    self._write("experiments/v1/framework.yaml", "framework_id: FRAMEWORK-V1\n")
    errors = self.module.validate_framework_templates()
    self.assertTrue(any("experiments/v1/TEMPLATE.yaml" in item for item in errors))
```

- [ ] **Step 3：运行测试并确认因功能不存在而失败**

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "framework_template"`

Expected: FAIL，失败原因包含 `validate_framework_templates` 尚不存在，而不是语法或夹具错误。

- [ ] **Step 4：提交测试红灯**

```powershell
git add tests/test_gtpj_workflow.py
git commit -m "test: define immutable framework template rules"
```

### Task 2：实现母版 schema、账本读取和 Git 身份校验

**Files:**
- Create: `schemas/framework_template.schema.json`
- Create: `experiments/templates/TEMPLATE_template.yaml`
- Modify: `workflow/gtpj_workflow.py`
- Test: `tests/test_gtpj_workflow.py`

- [ ] **Step 1：创建母版 schema**

schema 必须要求以下字段和取值：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://local.gtpj/schemas/framework_template.schema.json",
  "title": "GTPJ immutable framework template",
  "type": "object",
  "required": [
    "schema_version", "framework_id", "template_id", "template_status",
    "template_branch", "template_tag", "template_commit",
    "source_framework_tag", "source_framework_commit", "behavior_contract"
  ],
  "properties": {
    "schema_version": {"const": "gtpj.framework_template.v1"},
    "framework_id": {"pattern": "^FRAMEWORK-V[0-9]+$"},
    "template_id": {"pattern": "^MODEL-V[0-9]+-TEMPLATE-V[0-9]+$"},
    "template_status": {"enum": ["draft", "confirmed", "frozen", "retired", "legacy_frozen"]},
    "template_branch": {"pattern": "^framework/v[0-9]+(?:-template-v[0-9]+)?$"},
    "template_tag": {"pattern": "^(v[0-9]+|model/v[0-9]+-template-v[0-9]+)$"},
    "template_commit": {"pattern": "^[0-9a-f]{40}$"},
    "source_framework_tag": {"pattern": "^v[0-9]+$"},
    "source_framework_commit": {"pattern": "^[0-9a-f]{40}$"},
    "behavior_contract": {"type": "string"}
  },
  "additionalProperties": true
}
```

- [ ] **Step 2：增加母版常量和读取函数**

在 `FRAMEWORK_REQUIRED_KEYS` 后加入：

```python
FRAMEWORK_TEMPLATE_REQUIRED_KEYS = {
    "schema_version", "framework_id", "template_id", "template_status",
    "template_branch", "template_tag", "template_commit",
    "source_framework_tag", "source_framework_commit", "behavior_contract",
}

def framework_template_path(version: str) -> Path:
    return REPO_ROOT / "experiments" / version / "TEMPLATE.yaml"
```

- [ ] **Step 3：实现母版 Git 校验**

增加 `framework_template_git_ref_errors(data)`：

```python
def framework_template_git_ref_errors(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    tag = str(data.get("template_tag", ""))
    branch = str(data.get("template_branch", ""))
    expected = str(data.get("template_commit", ""))
    tag_commit = git(["rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], check=False)
    branch_commit = git(["rev-parse", "--verify", f"refs/heads/{branch}"], check=False)
    if not tag_commit:
        errors.append(f"missing template tag: {tag}")
    elif tag_commit != expected:
        errors.append(f"template_commit does not match tag {tag}")
    if not branch_commit:
        errors.append(f"missing template branch: {branch}")
    elif str(data.get("template_status", "")) in {"frozen", "legacy_frozen"} and branch_commit != expected:
        errors.append(f"frozen template branch must equal template_commit: {branch}")
    return errors
```

- [ ] **Step 4：实现 `validate_framework_templates()` 并接入总校验**

该函数遍历 `experiments/v[0-9]*/framework.yaml`，要求同目录存在 `TEMPLATE.yaml`，使用现有 `json_schema_subset_errors()` 校验格式，再核对框架编号、V0 只能是 `legacy_frozen`、V1 以上不能使用普通 `vX` Tag。`cmd_validate_framework_ledgers()` 和 `cmd_validate()` 都必须汇总其错误。

- [ ] **Step 5：运行母版测试变绿**

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "framework_template"`

Expected: PASS。

- [ ] **Step 6：提交母版校验**

```powershell
git add schemas/framework_template.schema.json experiments/templates/TEMPLATE_template.yaml workflow/gtpj_workflow.py tests/test_gtpj_workflow.py
git commit -m "feat: validate immutable framework templates"
```

### Task 3：用失败测试锁定实验绑定和准确分支起点

**Files:**
- Modify: `tests/test_gtpj_workflow.py`

- [ ] **Step 1：写实验缺少 `EXPERIMENT.yaml` 的失败测试**

创建一个正式 INDEX 行和完整实验目录，但不创建 `EXPERIMENT.yaml`，断言 `validate_framework_ledgers()` 返回 `missing EXPERIMENT.yaml`。

- [ ] **Step 2：写计划实验不得绑定历史代码的失败测试**

创建 `base_identity_kind: pending_clean_template` 且 `run_eligibility: historical_read_only`，断言校验器返回两字段关系错误。

- [ ] **Step 3：写新实验必须正好站在母版 commit 上的失败测试**

在母版后额外提交一个无关 commit，再切到正确命名的实验分支，调用：

```python
with self.assertRaisesRegex(self.module.WorkflowError, "must start exactly at template commit"):
    self.module.require_experiment_branch_base("v1")
```

- [ ] **Step 4：运行并确认红灯**

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "experiment_binding or template_commit"`

Expected: FAIL，原因是实验绑定校验和新基点行为尚未实现。

- [ ] **Step 5：提交测试红灯**

```powershell
git add tests/test_gtpj_workflow.py
git commit -m "test: require exact template binding for experiments"
```

### Task 4：实现实验 schema、生成器和精确起点检查

**Files:**
- Create: `schemas/experiment.schema.json`
- Create: `experiments/templates/EXPERIMENT_template.yaml`
- Modify: `workflow/gtpj_workflow.py`
- Test: `tests/test_gtpj_workflow.py`

- [ ] **Step 1：创建实验 schema**

字段固定为：

```yaml
schema_version: gtpj.experiment.v1
experiment_id: V5-ABLATION-001
framework_id: FRAMEWORK-V5
kind: ablation
base_identity_kind: framework_template | historical_code_ref | pending_clean_template
base_template_id: MODEL-V5-TEMPLATE-V1 | none
base_template_tag: model/v5-template-v1 | none
base_template_commit: 40位提交号 | none
historical_code_ref: 真实历史引用 | none
template_binding_status: ready | historical_read_only | blocked_pending_clean_template
experiment_branch: exp/v5/ablation/ablation-001-local-branch-effect | none
legacy_ref: 真实旧记录 | none
status: 与所属 INDEX 完全一致
```

schema 的 pattern 允许 `none`，跨字段关系由 Python 校验器负责。

- [ ] **Step 2：实现 `experiment_binding_errors()`**

关系必须是：

```python
EXPERIMENT_BINDING_RULES = {
    "framework_template": ("ready", True, False),
    "historical_code_ref": ("historical_read_only", False, True),
    "pending_clean_template": ("blocked_pending_clean_template", False, False),
}
```

第二项表示必须有完整母版三元组，第三项表示必须有 `historical_code_ref`。`framework_template` 还必须匹配所属框架当前 `TEMPLATE.yaml`，且当前母版状态必须是 `frozen`，不能用 `legacy_frozen` 开新实验。

- [ ] **Step 3：把实验绑定校验接入 `validate_framework_ledgers()`**

对每个 INDEX 实验目录要求 `EXPERIMENT.yaml`，核对：实验编号、框架、类型、状态、目录分支命名、INDEX 的 `legacy_ref` 与实验账本一致。

- [ ] **Step 4：把 `require_experiment_branch_base()` 改为精确母版起点**

读取 `TEMPLATE.yaml` 后要求：

```python
if template_status != "frozen":
    raise WorkflowError("new-experiment requires a frozen clean framework template")
if git(["rev-parse", "HEAD"]) != template_commit:
    raise WorkflowError("new-experiment branch must start exactly at template commit")
```

保留正确实验分支名和 clean worktree 两个原有检查。

- [ ] **Step 5：让 `cmd_new_experiment()` 生成实验账本**

在写 README 前写入 `EXPERIMENT.yaml`；参数矩阵首行的 `code_ref` 改为母版 Tag，README 顶部增加母版编号、Tag、commit。

- [ ] **Step 6：新增命令入口**

```text
validate-framework-templates
validate-experiment-base --path experiments/vX/<kind>/<experiment>
```

第一个校验所有母版；第二个核对当前 Git HEAD 是否包含实验登记的母版 commit，且实验分支没有改变母版账本。

- [ ] **Step 7：运行相关测试变绿**

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "experiment_binding or framework_template or new_experiment"`

Expected: PASS。

- [ ] **Step 8：提交实验绑定功能**

```powershell
git add schemas/experiment.schema.json experiments/templates/EXPERIMENT_template.yaml workflow/gtpj_workflow.py tests/test_gtpj_workflow.py
git commit -m "feat: bind experiments to exact framework templates"
```

### Task 5：迁移四个框架母版和九个现有实验

**Files:**
- Create: `experiments/v1/TEMPLATE.yaml`
- Create: `experiments/v2/TEMPLATE.yaml`
- Create: `experiments/v3/TEMPLATE.yaml`
- Create: `experiments/v5/TEMPLATE.yaml`
- Create: `experiments/v1/innovation/INNOVATION-001_clip_a_self/EXPERIMENT.yaml`
- Create: `experiments/v1/confirmation/CONFIRM-001_v1_seed5/EXPERIMENT.yaml`
- Create: `experiments/v2/innovation/INNOVATION-001_strict_conditional_jepa/EXPERIMENT.yaml`
- Create: `experiments/v3/tune/TUNE-001_local_v3_054/EXPERIMENT.yaml`
- Create: `experiments/v3/innovation/INNOVATION-001_conditional_bvsa/EXPERIMENT.yaml`
- Create: `experiments/v3/confirmation/CONFIRM-001_local_v3_054_min3/EXPERIMENT.yaml`
- Create: `experiments/v5/tune/TUNE-001_dynamic_routing_search/EXPERIMENT.yaml`
- Create: `experiments/v5/ablation/ABLATION-001_local_branch_effect/EXPERIMENT.yaml`
- Create: `experiments/v5/innovation/INNOVATION-001_dynamic_routing/EXPERIMENT.yaml`

- [ ] **Step 1：登记历史 V0 母版**

四份母版分别使用已核实的真实 Tag/commit：

```text
V1  d20d1882a88fc6d7be70d2f3b0b198fbc9f2444e
V2  ccc4a10ddd67308e28c40d6000216917a71bf472
V3  13529cb1d3ed8405e2f5cbb4832eff8d1c78db16
V5  08e5ecb1a5db6c6d589527cda35d8d4f7f437e07
```

统一使用 `MODEL-VX-TEMPLATE-V0`、`template_status: legacy_frozen`、历史 `framework/vX` 分支和 `vX` Tag，`behavior_contract: none`。V0 只用于解释旧结果，不能启动新实验。

- [ ] **Step 2：迁移八个已发生历史实验**

除 V5 局部分支消融外，其余八个实验使用：

```yaml
base_identity_kind: historical_code_ref
base_template_id: none
base_template_tag: none
base_template_commit: none
template_binding_status: historical_read_only
experiment_branch: none
```

`historical_code_ref` 必须复制 README、manifest 或旧映射中已有的真实引用；资料写“未保留”时照实写 `not_preserved`，不能替换成当前 V5。

- [ ] **Step 3：把 V5 局部分支消融锁到等待干净母版**

```yaml
base_identity_kind: pending_clean_template
base_template_id: none
base_template_tag: none
base_template_commit: none
historical_code_ref: codex/attempt019-local-ablation#ATTEMPT-019@954851b0d2dfd2d23f1efca10ba1bf142b3a6d68
template_binding_status: blocked_pending_clean_template
experiment_branch: none
status: planned
```

README 增加一句：原 15 行计划保留，但在 `MODEL-V5-TEMPLATE-V1` 冻结前不得启动；冻结后重新生成准确代码基点，不沿用旧 Attempt 分支代码。

- [ ] **Step 4：运行全部账本校验**

Run: `python workflow/gtpj_workflow.py validate-framework-templates`

Expected: `validate-framework-templates-ok`。

Run: `python workflow/gtpj_workflow.py validate-framework-ledgers`

Expected: `validate-framework-ledgers-ok`。

- [ ] **Step 5：提交迁移**

```powershell
git add experiments/v1 experiments/v2 experiments/v3 experiments/v5
git commit -m "data: bind current experiments to real code origins"
```

### Task 6：升级正式规范和所有活动入口

**Files:**
- Modify: `docs/workflow/FRAMEWORK_EXPERIMENT_STANDARD.md`
- Modify: `docs/workflow/START_HERE.md`
- Modify: `docs/workflow/WORKFLOW_KERNEL.md`
- Modify: `docs/workflow/core/QUICK_START.md`
- Modify: `docs/workflow/core/TASK_START_MINI.md`
- Modify: `docs/workflow/core/TASK_START_CARD.md`
- Modify: `docs/workflow/protocols/git_policy.md`
- Modify: `docs/workflow/protocols/versioning.md`
- Modify: `docs/workflow/protocols/experiment_protocol.md`
- Modify: `docs/workflow/WORKFLOW_MANIFEST.yaml`
- Modify: `experiments/README.md`
- Modify: `experiments/templates/experiment_README_template.md`
- Modify: `C:/Users/Administrator/.codex/skills/gtpj-workflow/SKILL.md`
- Test: `tests/test_gtpj_workflow.py`

- [ ] **Step 1：先写文档同步失败测试**

在 `validate_workflow_consistency()` 的同步文件和测试夹具中加入这些必须出现的短语：

```text
MODEL-VX-TEMPLATE-VN
TEMPLATE.yaml
EXPERIMENT.yaml
从准确母版提交独立分叉
实验代码不得并回母版
legacy_frozen 不能启动新实验
```

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "workflow_consistency"`

Expected: FAIL，指出活动文档尚未同步母版规则。

- [ ] **Step 2：把唯一正式规范升级为 V5**

`FRAMEWORK_EXPERIMENT_STANDARD.md` 顶部改为：

```yaml
standard_id: SYS-WORKFLOW-V5
ledger_id: DATA-FRAMEWORK-TEMPLATE-V1
status: active
effective_date: 2026-08-06
owner_approved: true
```

正文保留平级框架和四类实验规则，替换“从 `framework/vX` 开分支”为“从 `TEMPLATE.yaml` 登记的冻结 Tag 与准确 commit 开分支”，并加入 V0 历史快照、实验不回写母版、创新成功后新建同级框架的完整说明。

- [ ] **Step 3：同步入口、协议、模板和本地 Skill**

所有活动入口统一写明：

```text
framework.yaml = 方法身份
TEMPLATE.yaml = 可复制且不可修改的代码快照
EXPERIMENT.yaml = 一项实验的真实代码起点
PARAMETER_MATRIX.csv = 该实验每次运行的参数和结果
```

禁止继续写“新实验从可变化的 framework/vX 开始”。本地 Skill 只同步规则和入口，不复制项目文件。

- [ ] **Step 4：运行文档一致性测试变绿**

Run: `python -m pytest tests/test_gtpj_workflow.py -q -k "workflow_consistency or flat_framework_language"`

Expected: PASS。

- [ ] **Step 5：提交规范升级**

```powershell
git add docs/workflow experiments/README.md experiments/templates tests/test_gtpj_workflow.py
git commit -m "docs: adopt immutable framework template standard"
```

本地 Skill 文件不混入项目 Git commit；交付时单独验证其内容与项目规范一致。

### Task 7：更新人类总览页面和技术演进记录

**Files:**
- Create: `docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V3.html`
- Modify: `docs/diagrams/GTPJ_FRAMEWORK_REGISTRY_UI-V2.html`
- Modify: `docs/TECH_STACK_HISTORY.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/PROJECT_STRUCTURE.md`

- [ ] **Step 1：创建 UI-V3**

页面必须同时显示四个同级框架、历史来源箭头、各自 V0 母版状态、四类实验数量和 V5 消融的“等待干净母版”状态。V2 页面保留，在顶部标注“历史页面，当前入口为 UI-V3”。

- [ ] **Step 2：更新项目状态和目录说明**

用一张四层表解释 `framework.yaml → TEMPLATE.yaml → EXPERIMENT.yaml → PARAMETER_MATRIX.csv`。只列用户入口，不把缓存和内部测试目录当作正式入口。

- [ ] **Step 3：更新技术演进记录**

本阶段验证通过后，把 `SYS-WORKFLOW-V5`、`DATA-FRAMEWORK-TEMPLATE-V1` 改为“已完成”；`MODEL-V5-TEMPLATE-V1` 仍保持“计划中”，因为模型瘦身属于下一份计划。

- [ ] **Step 4：验证 HTML 内部链接**

运行 PowerShell 遍历 V3 页面中的本地相对链接，逐一确认目标存在；预期不存在链接数量为 0。

- [ ] **Step 5：提交人类入口**

```powershell
git add docs/diagrams docs/TECH_STACK_HISTORY.md docs/PROJECT_STATUS.md docs/PROJECT_STRUCTURE.md
git commit -m "docs: publish framework template registry view"
```

### Task 8：治理阶段全量验证和三轮审核

**Files:**
- Create: `docs/reviews/2026-08-06-framework-template-governance/`
- Modify: only files required to fix validated findings

- [ ] **Step 1：运行全量机器验证**

```powershell
python -m pytest tests/test_gtpj_workflow.py -q
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-framework-templates
python workflow/gtpj_workflow.py validate-framework-ledgers
python workflow/gtpj_workflow.py validate-workflow-consistency
python workflow/gtpj_workflow.py audit-boundary
python -m py_compile workflow/gtpj_workflow.py
git diff --check
```

Expected: 每条命令退出码 0；pytest 的通过数以实际新总数登记，不预写固定数字。

- [ ] **Step 2：进行第一轮独立审核**

审核范围：历史证据保护、母版/实验 schema、现有九个实验迁移。输出必须写明 `files_reviewed`、`decision`、阻断问题和未覆盖范围。

- [ ] **Step 3：进行第二轮独立审核**

审核范围：helper 的 Git ref、准确起点、错误分支、V0 禁止开新实验等负面路径。

- [ ] **Step 4：进行第三轮独立审核**

审核范围：活动文档、本地 Skill、UI、技术历史与机器规则是否一致，旧术语是否仍会把实验引向可变化分支。

- [ ] **Step 5：修复每轮有效问题并重跑全量验证**

审核超时、报错、空输出不计一轮；三个有效结论都必须留下真实审核实例和中文记录。

- [ ] **Step 6：提交治理阶段收口**

```powershell
git add docs/reviews workflow schemas experiments docs
git commit -m "chore: close immutable template governance review"
```

## 治理阶段完成定义

- 四个正式框架均有真实 V0 历史快照登记；
- 九个现有正式实验均有真实历史基点或等待干净母版状态；
- 新实验不能从 `legacy_frozen` 母版启动；
- 新实验必须正好从冻结母版 commit 开始；
- 母版分支和 Tag 一旦冻结不能向前移动；
- 旧 Trial/Attempt、Tag、成绩和大文件位置没有被移动、删除或改写；
- `SYS-WORKFLOW-V5` 与 `DATA-FRAMEWORK-TEMPLATE-V1` 通过机器验证和三轮有效审核。
