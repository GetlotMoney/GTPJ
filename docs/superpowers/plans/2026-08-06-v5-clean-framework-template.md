# GTPJ V5 干净代码母版实施计划

> **给执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项实施。每一步使用复选框跟踪。

**目标：** 从历史 `v5` 的真实有效路径重新提取一份只包含 V5 正式能力、行为可对照、可被冻结为 `MODEL-V5-TEMPLATE-V1` 的干净代码母版。

**架构：** 历史 `v5` Tag 永远不动，作为旧实现参照。干净 V5 代码只在项目现有 `GTPJ_worktrees/` 下的独立工作树和 `codex/v5-clean-template` 分支修改，不直接改总管理分支；动态路由等后续实验代码不进入母版。固定输入对照旧 `v5` 输出、损失和梯度；旧 checkpoint 兼容放到独立转换工具，不在模型里保留旧字段别名。母版代码 commit 先产生，后续总管理提交再用 `TEMPLATE.yaml` 登记它，二者不能合成一个自指提交。

**技术栈：** Python 3、PyTorch、Git、pytest、现有 GTPJ 配置加载器、JSON checkpoint 转换收据。

---

## 计划加固结论

### 已核实事实

- 历史 `v5`、`framework/v5` 和本地 `main` 当前都指向 `08e5ecb1a5db6c6d589527cda35d8d4f7f437e07`，不能移动或改写；
- 已审核治理分支是 `codex/framework-ledger-redesign`，治理审核记录位于 `docs/reviews/2026-08-06-framework-template-governance/`；
- 项目已经统一使用同一个 `D:/backup/Documents/Myself/GTPJ_worktrees/` 父目录，不需要在磁盘根目录或项目外另建副本；
- `template_registry_commit` 必须属于最终本地 `main` 历史，因此治理登记没有并入 `main` 前，任何新正式实验都必须保持阻塞；
- 本阶段没有服务器训练授权，只能完成本地代码、CPU 小输入对照、测试、审核和本地 Git 身份。

### 三条路线比较

| 路线 | 隔离性 | 历史安全 | 可测试性 | 维护成本 | 结论 |
|---|---:|---:|---:|---:|---|
| 直接在治理分支清理模型 | 低 | 容易让总管理分支混入 V5 专用代码 | 高 | 表面低、长期高 | 拒绝 |
| 独立代码工作树 + 后续 registry 提交 | 高 | 历史 Tag、治理账本和实验代码各自独立 | 高 | 中 | 采用 |
| 复制第二个 GTPJ 项目目录 | 中 | 容易形成两个都像正式入口的副本 | 中 | 高 | 拒绝 |

### 固定数据流

```text
已审核治理 commit
  -> 独立 codex/v5-clean-template 工作树
  -> 行为合同 + 红灯测试
  -> 最小代码清理 + CPU 数值对照
  -> 三轮审核通过的母版代码 commit C
  -> framework/v5-template-v1 + model/v5-template-v1 指向 C
  -> 总管理分支后续提交 G 用 TEMPLATE.yaml 登记 C
  -> G 进入本地 main 后，实验分支才允许记录 template_registry_commit=G
```

### 失败预演与回退

| 阶段 | 可能失败 | 可见信号 | 收口与回退 |
|---|---|---|---|
| 配置清理 | 删除了仍在有效路径使用的键 | 静态测试或固定输入构建失败 | 只回退该最小提交，不动历史 `v5` |
| 模型清理 | 输出、损失或梯度改变 | parity 超过 `rtol=1e-5, atol=1e-6` | 停止冻结，逐项恢复实际有效代码 |
| checkpoint 转换 | 字段冲突或 shape 不符 | 转换器非零退出并写冲突 | 不覆盖旧文件，不生成可用新权重 |
| Git 冻结 | branch、Tag、commit 不一致 | `validate-framework-templates` 失败 | Tag 创建前直接停止；若已创建错误候选 Tag，保持原样并先请求用户确认清理 |
| registry 集成 | 治理提交尚未进入 `main` | registry ancestry 检查失败 | V5 消融继续 `blocked_pending_clean_template` |

### 不变的完成边界

- 不把模板代码合并回总管理分支的模型文件；
- 不把实验代码并回模板分支；
- 不移动历史 `v5`、旧框架分支或旧 Trial/Attempt；
- 不把 CPU 等价测试写成服务器精度结论；
- 没有用户当轮服务器授权时，停在服务器运行计划之前。

---

## 文件职责

| 文件 | 职责 |
|---|---|
| `docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md` | 明确 V5 输入、输出、模块、损失和不能变化的 GZSL 语义。 |
| `tests/test_v5_template_contract.py` | 锁定 V5 配置、模块边界和新旧有效路径数值行为。 |
| `tests/test_fae_memory_jepa.py` | 保留原有数学覆盖，但把测试输入和断言统一改成 FGVD/ICSA/SGMP 规范名称。 |
| `model/MyModel.py` | V5 唯一模型实现，只保留 PSE、FGVD、BVSA、ICSA、SGMP 和固定融合。 |
| `train_GTPJ_CUB.py` | V5 唯一正式训练/评估入口，去掉历史参数别名和废弃路径。 |
| `config/versions/v5.yaml` | V5 唯一规范参数表，只保留当前名字。 |
| `tools/convert_v5_checkpoint.py` | 把旧 V5 checkpoint 显式转换为新母版字段，不覆盖原文件。 |
| `tests/test_v5_checkpoint_converter.py` | 验证字段映射、冲突阻断、哈希收据和原文件保护。 |
| 治理工作树的 `experiments/v5/TEMPLATE.yaml` | 在母版代码 commit 完成后，从 V0 历史快照切换到 V1 登记；不写入母版代码 commit。 |
| 独立消融实验分支的 `EXPERIMENT.yaml` | 在 registry 提交进入本地 `main` 后，把待跑消融绑定到 V1 母版与准确 registry commit。 |
| `docs/TECH_STACK_HISTORY.md` | 记录 `MODEL-V5-TEMPLATE-V1` 从计划到完成的真实证据。 |

### Task 1：冻结 V5 行为合同和旧实现参照

**Files:**
- Create: `docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md`
- Create: `tests/test_v5_template_contract.py`

- [ ] **Step 1：记录不可变化的接口**

先在 `D:/backup/Documents/Myself/GTPJ_worktrees/` 下建立唯一独立工作树，分支名为
`codex/v5-clean-template`，起点为已经通过三轮审核的治理 commit。创建前确认目标路径不存在，
创建后确认没有在项目父目录留下第二个临时副本。

合同必须写明：

```text
输入 clip_features：训练和评估使用现有形状与 dtype，不改变样本顺序。
seenclass/unseenclass：类别 id、顺序、label mapping 保持现有 standard_v1 语义。
输出：最终 logits 的含义与类别轴、U/S/H/ZS 计算入口保持不变；训练内部 package 允许从旧 JEPA 名称改成 SGMP 规范名称。
模块：PSE、FGVD、BVSA、ICSA、SGMP、global/local 固定融合。
融合：score_mode=add，local_weight 来自规范配置，不引入动态门。
数据：CUB split、class order、metric contract 不改。
```

同时列出历史参照：Tag `v5`、commit `08e5ecb1a5db6c6d589527cda35d8d4f7f437e07`、`model/MyModel.py`、`train_GTPJ_CUB.py`、`config/versions/v5.yaml`。

- [ ] **Step 2：写配置边界红灯测试**

```python
LEGACY_V5_KEYS = {
    "adapter_ratio", "use_clip_a_self", "clip_a_self_apply_unseen",
    "clip_a_self_heads", "clip_a_self_dropout", "clip_a_self_inner_ratio",
    "clip_a_self_outer_ratio", "lastvit_select_k", "lastvit_select_sigma",
    "lastvit_select_largest", "lastvit_select_formula", "use_fae",
    "use_conditional_text", "conditional_text_ratio", "meta_net_hidden",
    "lambda_msdn", "use_ag_jepa", "jepa_context_mode", "jepa_text_mode",
    "jepa_topk", "jepa_hidden", "lambda_jepa", "lambda_jepa_neg",
    "jepa_neg_margin",
}

def test_v5_config_contains_no_legacy_aliases() -> None:
    text = Path("config/versions/v5.yaml").read_text(encoding="utf-8")
    for key in LEGACY_V5_KEYS:
        assert f"{key}:" not in text
```

- [ ] **Step 3：写模型边界红灯测试**

断言干净母版源码不包含 `_config_get`、`CrossModalTransformer`、`CLIPASelfAdapter`、`use_ag_jepa`、`jepa_`、`lastvit_`、`gate_alpha`、`gate_tau`、`use_dynamic_routing`、`dynamic_routing`。同时断言 PSE、FGVD、BVSA、ICSA、SGMP 和 `local_weight` 仍存在。

- [ ] **Step 4：写训练入口边界红灯测试**

断言训练入口不存在 `cfg_value(... legacy_key ...)`、`pool_method == 'lastvit'` 和旧权重静默兼容分支；仍保留 config、seed、dataset/split、evaluate、checkpoint policy 和 U/S/H/ZS 计算调用。

- [ ] **Step 5：运行并确认红灯**

Run: `python -m pytest tests/test_v5_template_contract.py -q`

Expected: FAIL，列出当前历史别名和后续实验代码仍存在。

- [ ] **Step 6：提交合同和红灯测试**

```powershell
git add docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md tests/test_v5_template_contract.py
git commit -m "test: freeze v5 clean template contract"
```

### Task 2：清理 V5 规范配置

**Files:**
- Modify: `config/versions/v5.yaml`
- Modify: `experiments/v5/config.yaml`
- Test: `tests/test_v5_template_contract.py`

- [ ] **Step 1：只保留规范键**

配置保留以下 V5 实际参数组：

```text
dataset/num_class/dim_f_clip/device/batch_size/epochs/random_seed/text_source
pse_adapter_ratio/use_pse_self_attention/pse_apply_unseen/pse_heads/pse_dropout/pse_inner_ratio/pse_outer_ratio
tf_common_dim/tf_heads/tf_dropout/weight_s2v/text_residual/visual_residual/local_weight
pool_method/fgvd_select_k/fgvd_select_sigma/fgvd_select_largest/fgvd_select_formula/use_fgvd_geometry
lambda_consist/consist_temp/consist_dynamic/consist_dynamic_gamma/lambda_topo_pearson
use_icsa/icsa_ratio/bvsa_text_mode/icsa_hidden/lambda_bmdd/msdn_temp
use_sgmp/sgmp_context_mode/sgmp_text_mode/sgmp_topk/sgmp_hidden/lambda_mpp/lambda_neg/sgmp_neg_margin
lr_stages
```

`pool_method` 固定允许 V5 现用值；动态路由专用参数不进入配置。

- [ ] **Step 2：同步实验基线配置**

`experiments/v5/config.yaml` 与 `config/versions/v5.yaml` 使用相同规范键和值；只允许实验参数矩阵通过独立快照覆盖，不在基线配置留实验开关。

- [ ] **Step 3：运行配置测试**

Run: `python -m pytest tests/test_v5_template_contract.py -q -k "config"`

Expected: PASS。

- [ ] **Step 4：提交配置清理**

```powershell
git add config/versions/v5.yaml experiments/v5/config.yaml tests/test_v5_template_contract.py
git commit -m "refactor: keep only canonical v5 configuration"
```

### Task 3：重新提取 V5 模型有效路径

**Files:**
- Modify: `model/MyModel.py`
- Modify: `tests/test_fae_memory_jepa.py`
- Test: `tests/test_v5_template_contract.py`

- [ ] **Step 1：从历史 Tag 逐段核对有效实现**

用只读命令保存对照，不把旧文件复制进项目：

```powershell
git show v5:model/MyModel.py
git show v5:config/versions/v5.yaml
```

提取的类和函数只包括：`fgvd_select_patches`、`SemanticPrototypeAdapter`、`ProgressiveSemanticSelfAttention`、几何编码、`BidirectionalVisualSemanticAlignment`、`GTPJ`。

- [ ] **Step 2：删除配置别名读取**

所有配置都直接读取规范键，例如：

```python
self.pse_adapter_ratio = float(config.pse_adapter_ratio)
self.use_pse_self_attention = bool(config.use_pse_self_attention)
self.use_fgvd_geometry = bool(config.use_fgvd_geometry)
self.use_icsa = bool(config.use_icsa)
self.use_sgmp = bool(config.use_sgmp)
```

缺少规范键时直接报清楚的配置错误，不回退到旧名字。

- [ ] **Step 3：删除类名、属性名和方法名兼容层**

移除 `CrossModalTransformer`、`CLIPASelfAdapter`、`bvsa` property、旧 PSE/ICSA/SGMP property、`_ag_jepa_loss`、`_ag_jepa_fae_context` 和所有 `jepa_* / lastvit_*` 镜像属性。内部统一使用 `bvsa_module`、`pse_module`、`icsa_module`、`sgmp_predictor` 这四组清楚名字。

- [ ] **Step 4：移除 checkpoint 占位参数**

模型不再声明 `gate_alpha`、`gate_tau` 等不参与 V5 forward 的占位参数。旧权重通过 Task 5 的转换器处理。

- [ ] **Step 5：保持固定融合公式**

forward 只保留：

```python
final_logits = global_logits + self.local_weight * local_logits
```

若历史有效路径还包含已核实的归一化或缩放，必须在同一表达式前明确保留并由数值对照覆盖；不得引入可学习门、动态权重或实验开关。

- [ ] **Step 6：运行模型静态边界测试变绿**

把 `tests/test_fae_memory_jepa.py` 的配置、属性和输出断言改为 PSE/FGVD/ICSA/SGMP 规范名称；测试的数学问题、shape、梯度可达性和 detach 断言保持原意。

Run: `python -m pytest tests/test_v5_template_contract.py tests/test_fae_memory_jepa.py -q -k "model or source or sgmp or fgvd or icsa"`

Expected: PASS。

- [ ] **Step 7：提交模型清理**

```powershell
git add model/MyModel.py tests/test_v5_template_contract.py tests/test_fae_memory_jepa.py
git commit -m "refactor: extract clean v5 model path"
```

### Task 4：清理训练和评估入口

**Files:**
- Modify: `train_GTPJ_CUB.py`
- Test: `tests/test_v5_template_contract.py`

- [ ] **Step 1：删除旧配置别名读取**

日志打印、模型构建、loss 权重和数据入口全部只用规范键。删除 `cfg_value(key, legacy_key, default)`，如需缺省值只允许 `cfg_value(key, default)`，且规范 V5 配置必须显式提供所有改变数学行为的字段。

- [ ] **Step 2：删除废弃训练路径**

移除只服务旧 `lastvit` 名称、旧 AG-JEPA 名称和不参与当前 V5 正式训练的分支。保留恢复训练所需的 optimizer/scheduler/full checkpoint 逻辑，但旧权重字段必须先经过转换器。

- [ ] **Step 3：锁定训练与评估语义**

保持随机种子设置顺序、dataloader split、class order、seen/unseen label mapping、best epoch 选择、U/S/H/ZS 计算和 checkpoint Top-3 规则不变。

- [ ] **Step 4：运行训练入口静态边界测试**

Run: `python -m pytest tests/test_v5_template_contract.py -q -k "training_entry"`

Expected: PASS。

- [ ] **Step 5：提交入口清理**

```powershell
git add train_GTPJ_CUB.py tests/test_v5_template_contract.py
git commit -m "refactor: slim v5 training entry"
```

### Task 5：建立旧 checkpoint 显式转换工具

**Files:**
- Create: `tools/convert_v5_checkpoint.py`
- Create: `tests/test_v5_checkpoint_converter.py`

- [ ] **Step 1：先写四个失败测试**

测试必须证明：

1. 旧前缀映射到规范前缀；
2. 规范键和旧键同时存在且张量不一致时阻断；
3. `gate_alpha/gate_tau` 等占位键被明确列为 dropped，而不是静默吞掉；
4. 输出使用新文件，原 checkpoint 的 sha256 不变，并生成 JSON 收据。

- [ ] **Step 2：运行并确认红灯**

Run: `python -m pytest tests/test_v5_checkpoint_converter.py -q`

Expected: FAIL，原因是转换工具尚不存在。

- [ ] **Step 3：实现纯函数字段转换**

```python
def convert_state_dict(
    source: dict[str, object],
    target_state: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """返回新 state_dict 和包含 renamed/dropped/conflicts 的收据。"""
```

映射表只包含本次实际删除的字段前缀；没有证据的键不得猜测。冲突、未知关键前缀和 shape 不一致均返回非零退出码。

- [ ] **Step 4：实现不可覆盖的命令行入口**

```powershell
python tools/convert_v5_checkpoint.py --input old.pth --target-schema clean_state.pth --output converted.pth --receipt converted.receipt.json
```

输入、输出、收据必须是三个不同路径；输出存在时拒绝覆盖。收据记录输入/输出 sha256、大小、renamed、dropped、conflicts 和工具 Git commit。

- [ ] **Step 5：运行转换器测试变绿**

Run: `python -m pytest tests/test_v5_checkpoint_converter.py -q`

Expected: PASS。

- [ ] **Step 6：提交转换工具**

```powershell
git add tools/convert_v5_checkpoint.py tests/test_v5_checkpoint_converter.py
git commit -m "feat: add explicit v5 checkpoint converter"
```

### Task 6：做旧新 V5 数值等价测试

**Files:**
- Modify: `tests/test_v5_template_contract.py`
- Create: `tests/fixtures/v5_template/README.md`

- [ ] **Step 1：构建固定小输入夹具**

使用 CPU、固定随机种子、缩小维度和固定 seen/unseen 文本，覆盖：PSE 开启、FGVD 选择、conditional ICSA、SGMP、训练 forward、评估 forward 和 `compute_loss()`。夹具只保存生成规则和预期形状，不保存大张量。

- [ ] **Step 2：在测试临时目录加载历史 v5**

测试运行时调用：

```powershell
git show v5:model/MyModel.py
```

把文本写入操作系统临时目录，以独立模块名导入；项目目录不保留第二份旧模型源码。旧模型使用只含规范键的配置对象，证明对照的是同一有效路径。

- [ ] **Step 3：复制旧模型有效权重到新模型**

使用 Task 5 的纯函数转换；不比较已删除占位参数。固定 `eval()` 时比较输出；固定 `train()` 和随机种子时比较损失及关键参数梯度。旧 package 中 `jepa_*` 与新 package 中 `sgmp_*` 使用一张显式对照表比较，不要求保留旧键名。

- [ ] **Step 4：设置明确误差**

CPU float32 使用：

```python
torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)
```

比较至少包括最终 logits、global logits、local logits、总 loss、PSE/拓扑/SGMP/BMDD 损失和一个 PSE、一个 BVSA、一个 ICSA、一个 SGMP 参数梯度。

- [ ] **Step 5：运行等价测试**

Run: `python -m pytest tests/test_v5_template_contract.py -q -k "parity"`

Expected: PASS；任一允许差异必须先回写行为合同并说明原因，不能放宽误差掩盖错误。

- [ ] **Step 6：提交等价证据**

```powershell
git add tests/test_v5_template_contract.py tests/fixtures/v5_template/README.md docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md
git commit -m "test: prove clean v5 path parity"
```

### Task 7：建立 `MODEL-V5-TEMPLATE-V1` 冻结候选

**Files:**
- Modify: `experiments/v5/TEMPLATE.yaml`
- Modify: `docs/TECH_STACK_HISTORY.md`

- [ ] **Step 1：在独立代码工作树建立冻结前确认 commit**

先完成本计划全部本地测试和三轮审核修复，把 `codex/v5-clean-template` 的干净代码提交记为准确 commit C。创建本地分支 `framework/v5-template-v1` 指向 C；在最终冻结门通过前不创建 Tag。总管理分支的模型文件不接收这些代码差异。

- [ ] **Step 2：回到治理工作树更新母版账本为 confirmed 候选**

```yaml
template_id: MODEL-V5-TEMPLATE-V1
template_status: confirmed
template_branch: framework/v5-template-v1
template_tag: model/v5-template-v1
template_commit: 准确40位commit
source_framework_tag: v5
source_framework_commit: 08e5ecb1a5db6c6d589527cda35d8d4f7f437e07
behavior_contract: docs/workflow/contracts/V5_BEHAVIOR_CONTRACT.md
```

这次账本更新产生独立治理提交 G，不能写进 C。在本地 Tag 创建前，`confirmed` 只允许审核候选内容，不允许新实验启动；G 没有进入本地 `main` 前，V5 局部分支消融继续保持 `blocked_pending_clean_template`。

- [ ] **Step 3：更新技术演进记录为审核中**

把 `MODEL-V5-TEMPLATE-V1` 保持“计划中”，补充候选 commit 和本地 parity 结果；不能提前写“已冻结”或“精度完全不变”。

- [ ] **Step 4：提交候选账本**

```powershell
git add experiments/v5 docs/TECH_STACK_HISTORY.md
git commit -m "data: register v5 clean template candidate"
```

### Task 8：全量验证、三轮审核和服务器运行前停点

**Files:**
- Create: `docs/reviews/2026-08-06-v5-clean-template/`
- Modify: `experiments/v5/TEMPLATE.yaml`
- Modify: `experiments/v5/ablation/ABLATION-001_local_branch_effect/EXPERIMENT.yaml`
- Modify: `experiments/v5/ablation/ABLATION-001_local_branch_effect/README.md`
- Modify: `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.csv`
- Modify: `experiments/v5/ablation/ABLATION-001_local_branch_effect/PARAMETER_MATRIX.md`
- Modify: `docs/TECH_STACK_HISTORY.md`
- Modify: only files required to fix validated findings

- [ ] **Step 1：运行本地机器验证**

```powershell
python -m pytest tests/test_v5_template_contract.py tests/test_v5_checkpoint_converter.py -q
python -m pytest tests/test_gtpj_workflow.py -q
python workflow/gtpj_workflow.py validate
python workflow/gtpj_workflow.py validate-framework-templates
python workflow/gtpj_workflow.py validate-framework-ledgers
python workflow/gtpj_workflow.py validate-workflow-consistency
python workflow/gtpj_workflow.py audit-boundary
python -m py_compile model/MyModel.py train_GTPJ_CUB.py tools/v5_evaluation.py tools/v5_runtime.py tools/v5_cub_data.py tools/convert_v5_checkpoint.py
git diff --check
```

Expected: 全部退出码 0；测试通过数按实际输出登记。

- [ ] **Step 2：第一轮独立审核数学和接口**

检查 forward、loss、张量形状、类别轴、seen/unseen mapping、U/S/H/ZS 语义和 parity 测试是否覆盖真实 V5 路径。

- [ ] **Step 3：第二轮独立审核瘦身边界**

检查旧别名、占位参数、废弃入口、动态路由代码是否真正离开母版，以及 checkpoint 转换是否可回退。

- [ ] **Step 4：第三轮独立审核实验可复现性**

检查 Tag/commit、母版只读规则、V5 消融重新绑定、参数矩阵哈希和服务器确认前置条件。

- [ ] **Step 5：修复问题并重跑全量验证**

三个有效审核结论、修复回应和最终机器输出写入中文审核记录。超时、错误和空结果不算一轮。

- [ ] **Step 6：创建本地冻结 Tag 并改为 frozen**

三个审核结论和全量机器验证通过后，把最终代码提交 C 作为 `framework/v5-template-v1` 分支头，创建本地 `model/v5-template-v1` Tag，再在治理工作树把 `TEMPLATE.yaml` 的 commit 更新为 C 并将状态改为 `frozen`。分支、Tag、账本 commit 必须三者一致；不 push。registry 治理提交进入本地 `main` 前仍不能启动实验。

- [ ] **Step 7：重新绑定 V5 局部分支消融**

把 `EXPERIMENT.yaml` 改为：

```yaml
base_identity_kind: framework_template
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 与冻结Tag一致
historical_code_ref: codex/attempt019-local-ablation#ATTEMPT-019@954851b0d2dfd2d23f1efca10ba1bf142b3a6d68
template_binding_status: ready
experiment_branch: exp/v5/ablation/ablation-001-local-branch-effect
status: planned
```

同时写入完整 `template_registry_commit: G`。只有 G 已进入本地 `main`，并且消融分支从 C 独立创建时才允许执行本步。旧 Attempt 只保留为规划来源；15 行参数表的 `code_ref` 改为新母版 Tag，配置快照和指纹必须根据新母版重新冻结，不能沿用旧哈希。

- [ ] **Step 8：更新技术历史并提交冻结账本**

把 `MODEL-V5-TEMPLATE-V1` 改为“本地已完成，服务器确认待运行”，并提交母版、消融绑定和参数表变化；不能写成服务器精度已经确认。

```powershell
git add experiments/v5 docs/TECH_STACK_HISTORY.md docs/reviews/2026-08-06-v5-clean-template
git commit -m "data: freeze v5 clean template identity"
```

- [ ] **Step 9：停在服务器确认安全边界**

本地工作完成后只生成服务器确认计划，不自动启动高成本训练。计划必须明确 exact config、seed、数据/cache、原 `v5` 比较边界、新母版 commit、最多运行次数、GPU 锁和 Warehouse 写入位置；获得 owner 对本轮服务器成本的明确授权后才启动。

## V5 母版本地完成定义

- 历史 `v5` Tag 和旧实验证据没有变化；
- 新 V5 配置只含规范键；
- 模型和训练入口无旧别名、占位参数、动态路由及实验专用开关；
- 固定小输入的新旧输出、损失和关键梯度在约定误差内一致；
- checkpoint 转换不覆盖原文件并生成可核验收据；
- `model/v5-template-v1` 本地 Tag、分支和 commit 完全一致；
- V5 局部分支消融从新母版重新绑定，旧 ATTEMPT-019 只作历史来源；
- 三轮有效审核与全部本地机器验证通过；
- 服务器确认未获当前明确授权时保持未启动，不把本地等价写成正式精度结论。
