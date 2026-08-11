commands_run:
- python -m unittest discover -s tests
- python -m unittest tests.test_v5_seed_equivalence_server -v
- python -m unittest tests.test_v5_seed_equivalence_probe tests.test_v5_template_contract -v
- python workflow/gtpj_workflow.py validate
- python workflow/gtpj_workflow.py validate-framework-ledgers
- python workflow/gtpj_workflow.py audit-boundary
- server bwrap torch.cuda.is_available/device_count probe
results:
- 全量 313/313 PASS（控制器首个冻结候选）
- 最终控制器增量 27/27 PASS
- 模型修复与零步探针 10/10 PASS
- 服务器 bwrap 内 CUDA=True，device_count=2
machine_gates_passed: true
