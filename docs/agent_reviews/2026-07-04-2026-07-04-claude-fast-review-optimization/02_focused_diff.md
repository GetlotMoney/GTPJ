# Focused Diff

本文件是给 Claude Code 默认读取的精简 diff。完整证据仍保留在 `02_diff.patch`。

## Changed Files

- docs/workflow/protocols/ai_cross_review_protocol.md
- experiments/templates/ai_cross_review_template.md
- tests/test_gtpj_workflow.py
- workflow/gtpj_workflow.py
- CLAUDE.md
- docs/workflow/CLAUDE_CONTEXT.md

## Diff Stat

```text
 .../workflow/protocols/ai_cross_review_protocol.md |  34 ++++
 experiments/templates/ai_cross_review_template.md  |  17 ++
 tests/test_gtpj_workflow.py                        |  39 +++-
 workflow/gtpj_workflow.py                          | 199 ++++++++++++++++++++-
 4 files changed, 281 insertions(+), 8 deletions(-)
```

## Focused Patch

```diff
diff --git a/docs/workflow/protocols/ai_cross_review_protocol.md b/docs/workflow/protocols/ai_cross_review_protocol.md
index 905eb35..5d88a1b 100644
--- a/docs/workflow/protocols/ai_cross_review_protocol.md
+++ b/docs/workflow/protocols/ai_cross_review_protocol.md
@@ -141,12 +141,46 @@ python workflow\gtpj_workflow.py validate
 python workflow\gtpj_workflow.py validate-workflow-consistency
 python workflow\gtpj_workflow.py audit-boundary
 python -m py_compile workflow\gtpj_workflow.py
 ```
 
 如需加入额外验证命令，可重复传入：
 
 ```powershell
 --validation-command "python -m pytest tests\test_gtpj_workflow.py -q -p no:cacheprovider"
 ```
 
 如果只想生成证据包但不调用真实 Claude Code，可传入 `--skip-claude`；这种情况下最终状态必须是 blocked，不能当作正式通过。
+
+## 快速审核优化
+
+默认 Claude Code 审核不再直接读取完整 diff。`run-ai-cross-review` 必须同时生成：
+
+```text
+02_diff.patch
+02_focused_diff.md
+02_review_brief.md
+```
+
+字段规则：
+
+```text
+prompt_profile: focused | full
+review_mode: blocking-only | full
+```
+
+默认值：
+
+```text
+prompt_profile: focused
+review_mode: blocking-only
+```
+
+`focused` 模式下，Claude Code 默认只读 `CLAUDE.md`、`docs/workflow/CLAUDE_CONTEXT.md`、`02_review_brief.md`、`02_focused_diff.md`、`03_validation.md` 和 `04_claims.md`。完整 `02_diff.patch` 仍然必须保留在证据包中，但只作为追查备用证据。
+
+`blocking-only` 模式下，Claude Code 只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的 blocking issues。非阻断命名、风格和微小测试粒度建议不要展开。
+
+需要完整旧模式时，显式使用：
+
+```powershell
+python workflow\gtpj_workflow.py run-ai-cross-review --slug task-name --prompt-profile full --review-mode full
+```
diff --git a/experiments/templates/ai_cross_review_template.md b/experiments/templates/ai_cross_review_template.md
index f71fd36..5a2ca1f 100644
--- a/experiments/templates/ai_cross_review_template.md
+++ b/experiments/templates/ai_cross_review_template.md
@@ -20,24 +20,41 @@ codex_role: implementer
 changed_files:
 intended_behavior:
 out_of_scope:
 risk_notes:
 ```
 
 ## 02_diff.patch
 
 ```text
 填写 git diff 或 git diff --cached 输出。
 ```
 
+## 02_focused_diff.md
+
+```text
+prompt_profile: focused
+完整 diff 保留在 02_diff.patch；Claude Code 默认读取本文件。
+```
+
+## 02_review_brief.md
+
+```text
+prompt_profile: focused | full
+review_mode: blocking-only | full
+changed_files:
+machine_gates_passed:
+default_inputs:
+```
+
 ## 03_validation.md
 
 ```text
 commands_run:
 machine_gates_passed: true | false
 failed_commands:
 not_run:
 reason_if_not_run:
 ```
 
 ## 04_claims.md
 
diff --git a/tests/test_gtpj_workflow.py b/tests/test_gtpj_workflow.py
index bbfddd6..4130ada 100644
--- a/tests/test_gtpj_workflow.py
+++ b/tests/test_gtpj_workflow.py
@@ -470,25 +470,25 @@ baseline_off:
 audit:
   shape_audit: required
   switch_off_equivalence: required
   standard_gzsl_eval_audit: required
   split_integrity_audit: not_required
   class_order_audit: not_required
 """,
         )
 
         code, stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")
 
         self.assertEqual("", stderr)
-        self.assertEqual(0, code)
+        self.assertEqual(0, code, stdout + stderr)
         self.assertIn("validate-trial-meta-ok", stdout)
 
     def test_validate_trial_meta_rejects_single_module_scoring_change(self) -> None:
         self._write(
             "trial_meta.yaml",
             """schema_version: gtpj.trial_meta.v0
 trial_id: TRIAL-001
 module_scope: single_module
 template_family: feature_adapter
 risk: normal
 training_entry:
   mode: existing_entry_equivalent
@@ -582,25 +582,25 @@ baseline_off:
 audit:
   shape_audit: required
   switch_off_equivalence: required
   standard_gzsl_eval_audit: required
   split_integrity_audit: not_required
   class_order_audit: not_required
 """,
         )
 
         code, stdout, stderr = self._run_main("validate-trial-meta", "--path", "trial_meta.yaml")
 
         self.assertEqual("", stderr)
-        self.assertEqual(0, code)
+        self.assertEqual(0, code, stdout + stderr)
         self.assertIn("validate-trial-meta-ok", stdout)
 
     def test_scan_ignores_runtime_state(self) -> None:
         legacy_marker = "TUNE" + "-024"
         self._write(".gtpj_runtime/batches/old/summary.csv", f"legacy {legacy_marker} runtime evidence\n")
         self._write("docs/visible.md", "visible governance text\n")
 
         scanned = {path.relative_to(self.repo).as_posix() for path in self.module.list_files_for_scan()}
 
         self.assertIn("docs/visible.md", scanned)
         self.assertNotIn(".gtpj_runtime/batches/old/summary.csv", scanned)
 
@@ -2647,24 +2647,27 @@ decision:
             self._write(f"{pack_dir}/{filename}", "placeholder\n")
 
         code, stdout, stderr = self._run_main("validate-ai-cross-review", "--path", pack_dir)
 
         self.assertEqual("", stdout)
         self.assertEqual(1, code)
         self.assertIn("missing review file: 09_claude_review_round_3.md", stderr)
 
     def test_run_ai_cross_review_creates_three_round_pack_with_fake_claude(self) -> None:
         self._write(
             "fake_claude.py",
             "import sys\n"
+            "prompt = sys.stdin.read()\n"
+            "with open('captured_claude_prompt.txt', 'a', encoding='utf-8', errors='replace') as handle:\n"
+            "    handle.write(prompt + '\\n---PROMPT---\\n')\n"
             "print('round: fake')\n"
             "print('reviewer: claude_code')\n"
             "print('claude_code_read_only: true')\n"
             "print('verdict: pass')\n"
             "print('blocking_issues:')\n",
         )
         self._write("docs/example.md", "changed\n")
         validation_command = f'"{sys.executable}" -c "print(123)"'
 
         code, stdout, stderr = self._run_main(
             "run-ai-cross-review",
             "--path",
@@ -2673,31 +2676,55 @@ decision:
             "run-test",
             "--task-title",
             "测试三轮 AI 交叉审核",
             "--no-default-validation",
             "--validation-command",
             validation_command,
             "--claude-command",
             sys.executable,
             "--claude-command-arg",
             "fake_claude.py",
         )
 
+        pack = self.repo / "docs/agent_reviews/run-test"
+        debug_review = ""
+        if pack.exists():
+            debug_review = "\n".join(
+                (pack / name).read_text(encoding="utf-8")
+                for name in [
+                    "05_claude_review_round_1.md",
+                    "07_claude_review_round_2.md",
+                    "09_claude_review_round_3.md",
+                    "10_final_decision.md",
+                ]
+                if (pack / name).exists()
+            )
         self.assertEqual("", stderr)
-        self.assertEqual(0, code)
+        self.assertEqual(0, code, stdout + stderr + debug_review)
         self.assertIn("run-ai-cross-review-ok", stdout)
-        pack = self.repo / "docs/agent_reviews/run-test"
+        self.assertTrue((pack / "02_focused_diff.md").exists())
+        self.assertTrue((pack / "02_review_brief.md").exists())
         self.assertTrue((pack / "05_claude_review_round_1.md").exists())
         self.assertTrue((pack / "07_claude_review_round_2.md").exists())
         self.assertTrue((pack / "09_claude_review_round_3.md").exists())
+        prompt_text = (self.repo / "captured_claude_prompt.txt").read_text(encoding="utf-8")
+        brief_text = (pack / "02_review_brief.md").read_text(encoding="utf-8")
+        round_text = (pack / "05_claude_review_round_1.md").read_text(encoding="utf-8")
+        self.assertIn("02_review_brief.md", prompt_text)
+        self.assertIn("02_focused_diff.md", prompt_text)
+        self.assertIn("Do not read 02_diff.patch by default", prompt_text)
+        self.assertIn("review_mode: blocking-only", brief_text)
+        self.assertIn("prompt_profile: focused", brief_text)
+        self.assertIn("02_review_brief.md", round_text)
+        self.assertIn("02_focused_diff.md", round_text)
         final_text = (pack / "10_final_decision.md").read_text(encoding="utf-8")
         self.assertIn("ai_cross_review_status: pass", final_text)
         self.assertIn("unresolved_blocking_issues: 0", final_text)
 
     def test_run_ai_cross_review_skip_claude_blocks_pack(self) -> None:
         validation_command = f'"{sys.executable}" -c "print(123)"'
 
         code, stdout, stderr = self._run_main(
             "run-ai-cross-review",
             "--path",
             "docs/agent_reviews/skip-claude",
             "--slug",
@@ -2719,45 +2746,45 @@ decision:
         self._write("docs/workflow/README.md", "# Workflow\n")
         self._write("docs/workflow/START_HERE.md", "formal_runner_allowed\nmulti_agent_preflight\n")
         self._write("docs/workflow/WORKFLOW_KERNEL.md", "multi-agent-preflight\nformal_evidence_allowed\n")
         self._write("docs/workflow/core/QUICK_START.md", "repro-status\nbaseline_repro_status\n")
         self._write("docs/workflow/core/WORKFLOW_ROUTER.md", "# Router\n")
         self._write("docs/workflow/core/AGENT_RUNTIME_HARD_GATE.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n")
         self._write("docs/workflow/core/TASK_START_MINI.md", "runner_scope\nblocked_reason\n")
         self._write("docs/workflow/core/TASK_START_CARD.md", "multi_agent_preflight\nformal_evidence_allowed\nagent_status_refs\n")
         self._write("docs/workflow/protocols/agent_cleanup_protocol.md", "agent cleanup\n")
         self._write("docs/workflow/protocols/agent_orchestration.md", "multi_agent_preflight\nformal_runner_allowed\nagent_output_refs\nagent-cleanup-plan\n")
         self._write(
             "docs/workflow/protocols/ai_cross_review_protocol.md",
-            "owner_participation: not_required\nclaude_code_read_only: true\nrounds_completed: 3\nrun-ai-cross-review\nvalidate-ai-cross-review\n",
+            "owner_participation: not_required\nclaude_code_read_only: true\nrounds_completed: 3\nrun-ai-cross-review\nvalidate-ai-cross-review\n02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n",
         )
         self._write(
             "docs/workflow/protocols/module_template_selection.md",
             "feature_adapter_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nvalidate-trial-meta\nstandard GZSL U/S/H/ZS\nbase_code_tag\nstandard_gzsl_training_template.py\nstrict_template_entry\n",
         )
         self._write(
             "docs/workflow/playbooks/innovation.md",
             "START_HERE.md\nWORKFLOW_KERNEL.md\n探索 / 正式分界\nformal_evidence_allowed\nmodule_template_selection.md\nmodule_source.md\nvalidate-trial-meta\nstrict_template_entry\n",
         )
         self._write("docs/workflow/playbooks/tune.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/ablation.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/confirmation.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/promotion.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/mixed_campaign.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/paper_intake.md", "START_HERE.md\nWORKFLOW_KERNEL.md\n")
         self._write("docs/workflow/playbooks/paper_to_experiment.md", "START_HERE.md\nWORKFLOW_KERNEL.md\nbase_code_tag\nmodule_template_selection.md\nmodule_source.md\n")
         self._write("experiments/templates/agent_summary_template.md", "multi_agent_preflight:\nformal_runner_allowed:\nagent_output_refs:\nagent_cleanup:\nai_cross_review:\n")
         self._write(
             "experiments/templates/ai_cross_review_template.md",
-            "05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
+            "02_review_brief.md\n02_focused_diff.md\nprompt_profile\nblocking-only\n05_claude_review_round_1.md\n09_claude_review_round_3.md\n10_final_decision.md\nowner_participation: not_required\nunresolved_blocking_issues: 0\n",
         )
         self._write("experiments/templates/run_receipt_template.yaml", "schema_version: gtpj.run_receipt.v0\nmulti_agent_preflight:\nagent_output_refs:\n")
         self._write("experiments/templates/modules/README.md", "standard_gzsl_module_framework_template.py\nstandard_gzsl_training_template.py\ncomposite_module_template.py\narchitecture_change_template.md\nstrict_template_entry\nU, S, H, ZS\n")
 
         code, stdout, stderr = self._run_main("validate-workflow-consistency")
 
         self.assertEqual("", stderr)
         self.assertEqual(0, code)
         self.assertIn("validate-workflow-consistency-ok", stdout)
 
     def test_list_workflow_files_groups_manifest_entries(self) -> None:
         self._write_minimal_workflow_manifest()
diff --git a/workflow/gtpj_workflow.py b/workflow/gtpj_workflow.py
index 660f606..b05ff02 100644
--- a/workflow/gtpj_workflow.py
+++ b/workflow/gtpj_workflow.py
@@ -5894,24 +5894,28 @@ def workflow_consistency_errors() -> list[str]:
         "docs/workflow/protocols/agent_orchestration.md": [
             "multi_agent_preflight",
             "formal_runner_allowed",
             "agent_output_refs",
             "agent-cleanup-plan",
         ],
         "docs/workflow/protocols/ai_cross_review_protocol.md": [
             "owner_participation: not_required",
             "claude_code_read_only: true",
             "rounds_completed: 3",
             "run-ai-cross-review",
             "validate-ai-cross-review",
+            "02_review_brief.md",
+            "02_focused_diff.md",
+            "prompt_profile",
+            "blocking-only",
         ],
         "docs/workflow/protocols/module_template_selection.md": [
             "feature_adapter_template.py",
             "composite_module_template.py",
             "architecture_change_template.md",
             "validate-trial-meta",
             "standard GZSL U/S/H/ZS",
             "base_code_tag",
             "standard_gzsl_training_template.py",
             "strict_template_entry",
         ],
         "docs/workflow/playbooks/innovation.md": [
@@ -5926,24 +5930,28 @@ def workflow_consistency_errors() -> list[str]:
             "base_code_tag",
             "module_template_selection.md",
             "module_source.md",
         ],
         "experiments/templates/agent_summary_template.md": [
             "multi_agent_preflight:",
             "formal_runner_allowed:",
             "agent_output_refs:",
             "agent_cleanup:",
             "ai_cross_review:",
         ],
         "experiments/templates/ai_cross_review_template.md": [
+            "02_review_brief.md",
+            "02_focused_diff.md",
+            "prompt_profile",
+            "blocking-only",
             "05_claude_review_round_1.md",
             "09_claude_review_round_3.md",
             "10_final_decision.md",
             "owner_participation: not_required",
             "unresolved_blocking_issues: 0",
         ],
         "experiments/templates/run_receipt_template.yaml": ["schema_version: gtpj.run_receipt.v0", "multi_agent_preflight:", "agent_output_refs:"],
         "experiments/templates/modules/README.md": [
             "standard_gzsl_module_framework_template.py",
             "standard_gzsl_training_template.py",
             "composite_module_template.py",
             "architecture_change_template.md",
@@ -6139,24 +6147,124 @@ def build_ai_cross_review_diff(exclude_prefixes: list[str] | None = None) -> str
         "",
         "```diff",
         diff.rstrip(),
         "```",
     ]
     if snippet:
         header.extend(["", "# 未跟踪文件内容", snippet.rstrip()])
     if not diff.strip() and not snippet:
         header.extend(["", "```text", "当前没有 git diff 或未跟踪文本文件。", "```"])
     return "\n".join(header)
 
 
+def existing_claude_context_files() -> list[str]:
+    files = ["CLAUDE.md", "docs/workflow/CLAUDE_CONTEXT.md"]
+    return [path_text for path_text in files if (REPO_ROOT / path_text).is_file()]
+
+
+def build_ai_cross_review_focused_diff(
+    changed_files: list[str],
+    *,
+    exclude_prefixes: list[str] | None = None,
+    max_chars: int = 120_000,
+) -> str:
+    _changed, untracked = collect_changed_files(exclude_prefixes=exclude_prefixes)
+    diff_stat = git_capture("diff", "--stat", "--").rstrip()
+    diff = git_capture("diff", "--unified=12", "--").rstrip()
+    truncated = False
+    if len(diff) > max_chars:
+        diff = diff[:max_chars].rstrip()
+        truncated = True
+    snippet = read_untracked_review_snippets(untracked, max_bytes=40_000)
+    blocks = [
+        "# Focused Diff",
+        "",
+        "本文件是给 Claude Code 默认读取的精简 diff。完整证据仍保留在 `02_diff.patch`。",
+        "",
+        "## Changed Files",
+        "",
+        "\n".join(f"- {item}" for item in changed_files) if changed_files else "- 当前没有 git status 变化",
+        "",
+        "## Diff Stat",
+        "",
+        "```text",
+        diff_stat or "(empty)",
+        "```",
+        "",
+        "## Focused Patch",
+        "",
+        "```diff",
+        diff or "(empty)",
+        "```",
+    ]
+    if truncated:
+        blocks.extend(["", "> focused diff 已截断；需要追查完整上下文时再读取 `02_diff.patch`。"])
+    if snippet:
+        blocks.extend(["", "## Untracked Text Snippets", "", snippet.rstrip()])
+    return "\n".join(blocks)
+
+
+def build_ai_cross_review_brief(
+    *,
+    args: argparse.Namespace,
+    review_slug: str,
+    changed_files: list[str],
+    commands: list[str],
+    validation_passed: bool,
+) -> str:
+    context_files = existing_claude_context_files()
+    return f"""# Claude Code 快速审核 Brief
+
+```text
+task_id: {args.task_id or safe_review_slug(review_slug)}
+task_title: {args.task_title or review_slug}
+scope: {args.scope}
+risk_level: {args.risk_level}
+prompt_profile: {args.prompt_profile}
+review_mode: {args.review_mode}
+machine_gates_passed: {str(validation_passed).lower()}
+owner_participation: not_required
+claude_code_read_only: true
+```
+
+## 默认读取顺序
+
+{chr(10).join(f"- `{item}`" for item in context_files) if context_files else "- 未找到 Claude 项目上下文文件"}
+- `00_task.md`
+- `01_codex_actions.md`
+- `02_focused_diff.md`
+- `03_validation.md`
+- `04_claims.md`
+
+## 备用证据
+
+- `02_diff.patch` 是完整 diff，只在 focused diff 无法定位问题时读取。
+- 旧轮次的 Claude/Codex 文件只在第 2/3 轮需要比对剩余问题时读取。
+
+## Changed Files
+
+{chr(10).join(f"- `{item}`" for item in changed_files) if changed_files else "- 当前没有 git status 变化"}
+
+## Validation Commands
+
+{chr(10).join(f"- `{command}`" for command in commands) if commands else "- 未提供验证命令"}
+
+## 审核要求
+
+- 只读审核，不改文件，不启动训练，不 push，不删除用户数据。
+- `blocking-only` 模式只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
+- 非阻断命名、风格、微小测试建议不要展开；可写 `non_blocking_issues: omitted_by_blocking_only_mode`。
+"""
+
+
 def run_ai_cross_review_validations(commands: list[str]) -> tuple[bool, str]:
     if not commands:
         return False, "commands_run:\nnot_run:\n- 未提供验证命令。\nmachine_gates_passed: false\n"
     blocks: list[str] = ["commands_run:"]
     all_passed = True
     failed: list[str] = []
     for command in commands:
         code, stdout, stderr = run_command_capture(command)
         if code != 0:
             all_passed = False
             failed.append(command)
         blocks.append(
@@ -6199,26 +6307,88 @@ def build_claude_prompt(pack_dir: Path, round_number: int) -> str:
 round: {round_number}
 reviewer: claude_code
 claude_code_read_only: true
 verdict: pass | needs_fix | blocked
 blocking_issues:
 non_blocking_issues:
 unsupported_claims:
 missing_validation:
 ```
 """
 
 
+def build_claude_prompt_ascii(
+    pack_dir: Path,
+    round_number: int,
+    *,
+    prompt_profile: str,
+    review_mode: str,
+) -> str:
+    focused_inputs = [
+        *existing_claude_context_files(),
+        "00_task.md",
+        "01_codex_actions.md",
+        "02_review_brief.md",
+        "02_focused_diff.md",
+        "03_validation.md",
+        "04_claims.md",
+    ]
+    if round_number >= 2:
+        focused_inputs.extend(["05_claude_review_round_1.md", "06_codex_response_round_1.md"])
+    if round_number >= 3:
+        focused_inputs.extend(["07_claude_review_round_2.md", "08_codex_response_round_2.md"])
+    if prompt_profile == "full":
+        focused_inputs.insert(4, "02_diff.patch")
+    input_lines = "\n".join(f"- {item}" for item in focused_inputs)
+    if review_mode == "blocking-only":
+        review_note = "Review mode: blocking-only. Report only reproducible blocking issues. Do not expand style, naming, or minor test-granularity suggestions."
+    else:
+        review_note = "Review mode: full. You may report both blocking and non-blocking issues."
+    if prompt_profile == "focused":
+        patch_note = "Prompt profile: focused. Do not read 02_diff.patch by default; read it only when 02_focused_diff.md is insufficient to locate a blocking issue."
+    else:
+        patch_note = "Prompt profile: full. Read 02_diff.patch and use 02_review_brief.md to orient the review."
+    return f"""You are the read-only Claude Code reviewer for the GTPJ project.
+Review pack directory: {display_path(pack_dir)}
+Round: {round_number}
+
+Do not edit files. Do not start training. Do not push, delete, publish, or perform destructive actions.
+{review_note}
+{patch_note}
+
+Read these files first:
+{input_lines}
+
+Every blocking issue must cite a file path, line number or reproducible command/missing evidence.
+Output must contain these fields:
+```text
+round: {round_number}
+reviewer: claude_code
+claude_code_read_only: true
+verdict: pass | needs_fix | blocked
+blocking_issues:
+non_blocking_issues:
+unsupported_claims:
+missing_validation:
+```
+"""
+
+
 def run_claude_review(args: argparse.Namespace, pack_dir: Path, round_number: int) -> tuple[int, str, str]:
-    prompt = build_claude_prompt(pack_dir, round_number)
+    prompt = build_claude_prompt_ascii(
+        pack_dir,
+        round_number,
+        prompt_profile=args.prompt_profile,
+        review_mode=args.review_mode,
+    )
     if args.skip_claude:
         return 0, "verdict: blocked\nblocking_issues:\n- skip_claude enabled; 未调用 Claude Code。\n", ""
     executable = shutil.which(args.claude_command) or args.claude_command
     command = [
         executable,
         *args.claude_command_arg,
         "-p",
         "--bare",
         "--permission-mode",
         "plan",
         "--output-format",
         "json",
@@ -6249,29 +6419,34 @@ def extract_review_verdict(text: str, exit_code: int) -> str:
     if not match:
         return "blocked"
     return match.group(1).lower()
 
 
 def make_claude_review_md(round_number: int, exit_code: int, stdout: str, stderr: str) -> tuple[str, str]:
     verdict = extract_review_verdict(stdout + "\n" + stderr, exit_code)
     blocking_value = "" if verdict == "pass" else f"- Claude Code 第 {round_number} 轮未通过或未给出可接受输出。"
     content = f"""round: {round_number}
 reviewer: claude_code
 claude_code_read_only: true
 inputs_checked:
+- CLAUDE.md
+- docs/workflow/CLAUDE_CONTEXT.md
 - 00_task.md
 - 01_codex_actions.md
-- 02_diff.patch
+- 02_review_brief.md
+- 02_focused_diff.md
 - 03_validation.md
 - 04_claims.md
+fallback_available:
+- 02_diff.patch
 verdict: {verdict}
 blocking_issues:
 {blocking_value}
 non_blocking_issues:
 unsupported_claims:
 missing_validation:
 
 ## Claude Code 原始 stdout
 
 ```text
 {stdout.rstrip() or "(empty)"}
 ```
@@ -6355,26 +6530,44 @@ changed_files:
 {chr(10).join("- " + item for item in changed_files) if changed_files else "- 当前没有 git status 变化"}
 intended_behavior: {args.task_title or review_slug}
 out_of_scope:
 - 不启动训练
 - 不启动子 agents
 - 不 push
 - 不删除用户数据
 risk_notes: {args.risk_notes or "由 AI 交叉审核和机器验证共同控制风险。"}
 """,
         overwrite=args.overwrite,
     )
     write_review_file(pack_dir, "02_diff.patch", build_ai_cross_review_diff(exclude_prefixes=review_exclude_prefixes), overwrite=args.overwrite)
+    write_review_file(
+        pack_dir,
+        "02_focused_diff.md",
+        build_ai_cross_review_focused_diff(changed_files, exclude_prefixes=review_exclude_prefixes),
+        overwrite=args.overwrite,
+    )
     validation_passed, validation_text = run_ai_cross_review_validations(commands)
     write_review_file(pack_dir, "03_validation.md", validation_text, overwrite=args.overwrite)
+    write_review_file(
+        pack_dir,
+        "02_review_brief.md",
+        build_ai_cross_review_brief(
+            args=args,
+            review_slug=review_slug,
+            changed_files=changed_files,
+            commands=commands,
+            validation_passed=validation_passed,
+        ),
+        overwrite=args.overwrite,
+    )
     write_review_file(
         pack_dir,
         "04_claims.md",
         f"""claim: 本次改动已由 Codex 生成证据包，并将由 Claude Code 只读审核三轮。
 status: supported
 evidence_ref: 05_claude_review_round_1.md; 07_claude_review_round_2.md; 09_claude_review_round_3.md
 
 claim: 机器验证命令已运行。
 status: {"verified" if validation_passed else "false"}
 evidence_ref: 03_validation.md
 """,
         overwrite=args.overwrite,
@@ -9985,24 +10178,26 @@ def build_parser() -> argparse.ArgumentParser:
     validate_ai_cross_review.add_argument("--path", required=True)
     validate_ai_cross_review.set_defaults(func=cmd_validate_ai_cross_review)
 
     run_ai_cross_review = sub.add_parser("run-ai-cross-review", help="生成证据包并调用 Claude Code 三轮只读审核")
     run_ai_cross_review.add_argument("--slug", default="")
     run_ai_cross_review.add_argument("--path", default="")
     run_ai_cross_review.add_argument("--task-id", default="")
     run_ai_cross_review.add_argument("--task-title", default="")
     run_ai_cross_review.add_argument("--scope", default="current git diff")
     run_ai_cross_review.add_argument("--risk-level", default="medium", choices=["low", "medium", "high"])
     run_ai_cross_review.add_argument("--review-reason", default="")
     run_ai_cross_review.add_argument("--risk-notes", default="")
+    run_ai_cross_review.add_argument("--prompt-profile", default="focused", choices=["focused", "full"])
+    run_ai_cross_review.add_argument("--review-mode", default="blocking-only", choices=["blocking-only", "full"])
     run_ai_cross_review.add_argument("--validation-command", action="append", default=[])
     run_ai_cross_review.add_argument("--no-default-validation", action="store_true")
     run_ai_cross_review.add_argument("--claude-command", default="claude")
     run_ai_cross_review.add_argument("--claude-command-arg", action="append", default=[])
     run_ai_cross_review.add_argument("--skip-claude", action="store_true")
     run_ai_cross_review.add_argument("--overwrite", action="store_true")
     run_ai_cross_review.set_defaults(func=cmd_run_ai_cross_review)
 
     validate_trial_meta = sub.add_parser("validate-trial-meta", help="校验 module trial meta 的 scope/affects 分流")
     validate_trial_meta.add_argument("--path", default="")
     validate_trial_meta.set_defaults(func=cmd_validate_trial_meta)
```

## Untracked Text Snippets


## 未跟踪文件：CLAUDE.md

```text
# Claude Code 项目入口

本文件是 Claude Code 的项目级只读上下文。它用于让 Claude 快速理解 GTPJ 的稳定规则，不能替代当前 diff、测试、workflow validate 或实验 artifact 证据。

## 默认角色

- Claude Code 是只读审核者，不直接修改文件。
- Codex 负责实现、修复、反驳和重跑验证。
- 任何结论必须引用当前仓库文件、命令输出或 Warehouse artifact 记录，不能依赖隐藏聊天记忆。

## 默认读取

快速审核时优先读取：

1. `docs/workflow/CLAUDE_CONTEXT.md`
2. 当前审核包的 `02_review_brief.md`
3. 当前审核包的 `02_focused_diff.md`
4. 当前审核包的 `03_validation.md`
5. 当前审核包的 `04_claims.md`

完整 `02_diff.patch` 是备用证据。只有 focused diff 不足以定位阻断问题时再读取完整 patch。

## 审核边界

- 不启动训练。
- 不 push。
- 不删除用户数据。
- 不写入或编辑仓库文件。
- 默认只报告 blocking issues；非阻断风格、命名、微小测试建议不要展开。
```


## 未跟踪文件：docs/workflow/CLAUDE_CONTEXT.md

```text
# Claude Code 共享项目上下文

本文件是 GTPJ 给 Claude Code 的轻量共享上下文。它只记录稳定规则，当前事实仍以本次审核包、仓库文件、验证命令和实验 artifact 为准。

## 项目目标

GTPJ 是面向 GZSL（广义零样本学习）实验的研究 workflow。GitHub 仓库只保存轻量治理、配置、结果账本和证据索引；原始日志、checkpoint、生成图和大文件留在 Warehouse 或 Research 目录。

## 核心硬规则

- 机器验证优先于模型意见。
- Claude Code 只读审核，Codex 负责实现和修复。
- 正式实验不能绕过 `agent_runtime.yaml`、`validate-agent-runtime`、`multi-agent-preflight` 和 cleanup 记录。
- raw artifacts 不能进入 GitHub；GitHub 只记录 artifact id、URI、sha256、size、config、manifest、result 和 quality。
- exact repeat 必须固定原始 seed；多 seed 只能称为 seed sweep 或 stability，不算 exact repeat。
- `best_observed_H` 表示历史最高观察值；`confirmed_H` 表示确认复现实验的确认值，二者不能混用。
- promotion 必须有完整 result、quality、artifact、confirmation 和 promotion evidence；普通调参或未确认结果不能自动升版本。

## Claude 快速审核策略

默认使用 focused 审核：

- 先读 `CLAUDE.md` 和本文件。
- 再读审核包中的 `02_review_brief.md`、`02_focused_diff.md`、`03_validation.md`、`04_claims.md`。
- 只在 focused diff 不足以定位阻断问题时读取完整 `02_diff.patch`。

默认使用 blocking-only 审核：

- 只报告会导致行为错误、证据污染、验证失败、正式实验结论不可靠的问题。
- 命名、风格、非关键测试粒度建议可以省略，除非它会隐藏真实行为风险。

## 常见阻断问题

- 训练入口、评估语义、label mapping、seen/unseen split、class order、logits shape 或 U/S/H/ZS 指标语义不清。
- helper 生成的正式 evidence 与实际 run、attempt、artifact 或 warehouse 路由不一致。
- `agent_runtime.yaml` 中 agent id、UI 显示名、role 映射、output refs 或 cleanup 记录缺失。
- 将 debug/smoke 或 seed sweep 伪装成正式 confirmation。
- 用当前主会话或隐藏记忆冒充真实 `real_multi_agent` 证据。
```
