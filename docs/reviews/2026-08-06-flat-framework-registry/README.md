# 同级正式框架注册规范审核记录

## 结论

最终决定：`PASS`。

GTPJ 的正式框架关系已经统一为：V1、V2、V3、V5 全部平级；V2→V1、V3→V2、V5→V3 只表示历史来源。创新候选在确认和接纳前没有正式框架编号、长期框架分支或 Tag。

本次没有启动训练，没有修改参数矩阵、成绩、运行记录、模型代码或训练入口，也没有 push、合并、创建新 Tag 或切换当前运行版本。

## 为什么做三路审核

本次同时改变正式框架身份、Tag 校验、创新晋级和用户长期查看入口，属于会影响以后所有实验归档与版本判断的核心规则，因此采用三路独立审核：

1. 代码与校验器：检查平级关系、Tag、来源链和晋级门槛能否被绕过。
2. 文档与页面：检查现行入口和本地 Skill 是否仍残留父子框架或错误 v4 示例。
3. 数据完整性：检查成绩、参数表、旧 Attempt/Trial 证据、模型和训练入口是否被误改。

## 审核范围

- 起点提交：`c1f1b23fbd5cb0fe0771bc41518d202c0413f18b`
- 正式规范提交：`709df05f5d4711891ba90f2276290f51ff0cf480`
- 台账绑定提交：`61f9dce`
- 第一轮修复提交：`250cf10`
- 最终候选提交：`379d0e7`
- 分支：`codex/framework-ledger-redesign`

## 第一轮发现与修复

第一轮数据完整性审核通过；代码和文档审核要求修改，主要发现：

- 正式框架缺少真实 Tag 时可能漏报；
- 候选创新可以提前填写新框架号；
- 结果里的 `promote_to` 没有和目标框架核对；
- 除 V1 外可以伪装第二个起点；
- GITHUB 文档一度把 V3 来源写成 V1；
- Router、实验协议、Promotion、Quality、Task Card、项目结构和本地 Skill 仍有旧父子口径；
- Promotion 仍使用历史误分类 v4 和只建 `baseline/` 的旧示例。

修复后新增机器拦截，并把正式晋级流程改为必须建立四类账本、来源回链、长期分支和冻结 Tag。

## 第二轮发现与修复

第二轮发现两个更隐蔽的问题：

- 删除 Tag 后建立同名普通分支，可能冒充正式 Tag；最终改为只读取 `refs/tags/vX`。
- Git 策略和 Skill 顶层仍有 `parent-version`、父代码来源、formal framework tree 和错误 v4 晋级示例；最终补进自动防倒退扫描和回归测试。

## 最终三路结论

| 审核方向 | 最终结论 | 关键证据 |
|---|---|---|
| 代码与校验器 | `PASS` | 同名普通分支不能冒充 Tag；候选占号、错误目标、第二根节点、未知来源和循环均被拦截；正常来源链无误报。 |
| 文档与页面 | `PASS` | GITHUB、Git 策略、Router、实验协议、Promotion、项目结构、README 和本地 Skill 口径一致；旧术语防倒退测试通过。 |
| 数据完整性 | `PASS` | 参数矩阵、成绩、result、manifest、runs、attempts、配置、模型和训练入口零改动；四个正式 Tag/分支/提交一致；v4 仍为历史配置 Tag。 |

## 机器验证

```text
python -m unittest discover -s tests -p "test_*.py"
结果：Ran 250 tests，OK

python -m unittest discover -s tests -p "test_*.py" -k framework
结果：Ran 25 tests，OK

python workflow/gtpj_workflow.py validate-framework-ledgers
结果：validate-framework-ledgers-ok

python workflow/gtpj_workflow.py validate-workflow-consistency
结果：validate-workflow-consistency-ok

python workflow/gtpj_workflow.py validate
结果：validate-ok

python workflow/gtpj_workflow.py audit-boundary
结果：audit-boundary-ok

git diff --check
结果：通过
```

HTML 页面共 7 个内部链接，全部能找到对应文件。旧模块试验目录前后树哈希一致：`6e858397607f42c6c4b3ac870e24909e2aae14aa`。

## 保留风险与边界

- 旧审核包、旧 Trial/Attempt 和历史证据里的原字段不改写，避免伪造历史；现行入口已经停用这些口径。
- 本地 Skill 位于 `C:\Users\Administrator\.codex\skills\gtpj-workflow\`，已同步现行规范，但它不属于本仓库提交历史。
- 本次完成在独立工作树和分支上；未覆盖用户当前主工作树，也未推送远端。
