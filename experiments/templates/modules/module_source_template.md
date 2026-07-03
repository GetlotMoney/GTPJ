# Module Source

```text
idea_id:
trial_id:
module_name:
template_family:
module_scope:
trial_meta: trial_meta.yaml
base_version:
base_code_tag:
dataset: CUB xlsa17 att_splits
evaluation: standard GZSL U/S/H/ZS
training_entry_mode: existing_entry_equivalent | strict_template_entry
selected_training_entry:
legacy_module_migration: not_required | required | completed
```

## Source

```text
source_type: paper | official_code | user | observation | hybrid
paper_id:
source_ref:
source_status:
official_code_url:
official_code_path:
official_code_commit:
```

## Mechanism Claim

What the source claims:

```text
mechanism_claim:
target_signal:
expected_effect_on_gzsl:
```

## Adaptation To GTPJ

```text
what_is_copied:
what_is_adapted:
what_is_new:
why_fit_gtpj:
not_implemented_from_source:
```

## Template Mapping

```text
template_family:
module_scope: single_module | composite | architecture_change
components:
  - name:
    template_family:
    attachment_point:
    enabled_key:
composition_mode: none | sequential | parallel | gated | residual
affects:
  forward_main_flow:
  class_scoring:
  train_data_view:
  eval_input_output:
  split_or_label_mapping:
attachment_point:
input_tensors:
output_tensors:
config_switch:
baseline_off_explanation:
training_entry_mode:
selected_training_entry:
legacy_module_migration:
```

## Paper Writing Note

Use this section later when writing the paper:

```text
module_origin_sentence:
method_explanation:
difference_from_source:
ablation_needed:
limitations:
paper_writing_note:
```
