# 参数矩阵：INNOVATION-013_shared_pse_global8

这张表一行对应一个实际训练任务；它不是批次摘要。完整原始日志和模型仍在 Warehouse。

来源：只加共享PSE的全局分支

| 任务 | 名称 | 类别 | 状态 | 本次改动 | 随机种子 | 复跑对象 | 旧任务/批次号 | 用途 | H | 决定 | 证据清单 SHA256 |
|---|---|---|---|---|---:|---|---|---|---:|---|---|
| RUN-002 | 共享PSE全局分支 | innovation | frozen | {"batch_size":256,"class_order_sha256":"7b6ffe26103bfeb73324f328fac499d6ea7cfadfb2b56448b0df295aca22df38","consist_dynamic_gamma":"<removed>","consist_temp":"<removed>","dim_f_clip":"<removed>","expected_sha256":{"att_splits":"d7f5b4c2cb7853acdce43a9e87607ceed30bdf18c60344be3a266de29b6751e3","res101":"9a97c71951f9ac9f5c3708e6e55386e53f3d433289ed5e87a18b4af2a1a0fca1","seen_features":"5af75c696c8d285e35a35cc41eb538017f5452d1eaf13e34fe3ee978e72983c5","seen_labels":"06f3f7057b6847fd912544ddb921d0ca3fca96d0888503f3fc87a52f98d3de14","sentence_embeds":"8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3","train_features":"a18cefc50ec541027598d742698622f7ddd2ec8687ba797ab1eeeacb743a4fe9","train_labels":"b1cbf2c128a3a09979852ec5906161a737be58bf4517b18b4f7d16beec06b666","unseen_features":"32c1b89edb72a94e27585060ac968f1afc99000a9bd8c42acee8469971fb107e","unseen_labels":"7fadd63d51f69cf09cc8107a132d28036b838649b75227a17656eac8640b9c59"},"fgvd_select_k":"<removed>","icsa_hidden":"<removed>","icsa_ratio":"<removed>","inputs":{"att_splits":"data/xlsa17/data/CUB/att_splits.mat","res101":"data/xlsa17/data/CUB/res101.mat","seen_features":"data/cache/CUB_test_seen_features.pt","seen_labels":"data/cache/CUB_test_seen_labels.pt","sentence_embeds":"data/cache/CUB_gpt56_8sent_sentence_embeds.pt","train_features":"data/cache/CUB_train_features.pt","train_labels":"data/cache/CUB_train_labels.pt","unseen_features":"data/cache/CUB_test_unseen_features.pt","unseen_labels":"data/cache/CUB_test_unseen_labels.pt"},"lambda_bmdd":"<removed>","lambda_consist":"<removed>","lambda_mpp":"<removed>","lambda_neg":"<removed>","lambda_topo_pearson":"<removed>","learning_rate":0.0001,"local_weight":"<removed>","lr_stages":"<removed>","max_epochs":100,"min_delta":0.0001,"msdn_temp":"<removed>","num_class":"<removed>","patience":10,"pse_dropout":0.1,"pse_inner_ratio":"<removed>","pse_outer_ratio":"<removed>","residual_cap":0.35,"role_order": ["beak","head_features","body_plumage","wings","tail","legs","overall_appearance","unique_discriminative_features"],"score_mode":"<removed>","score_path":"clip_cls_x_shared_pse_global_only","seed":5,"sgmp_hidden":"<removed>","sgmp_neg_margin":"<removed>","sgmp_topk":"<removed>","temperature":0.05,"text_source":"<removed>","tf_common_dim":"<removed>","tf_dropout":"<removed>","tf_heads":"<removed>","validation_fraction":0.1,"weight_decay":0.0001,"weight_s2v":"<removed>"} | 5 |  | RUN-002 | 共享PSE正式确定性复跑并与H=64.164039零号基线比较 |  | pending |  |

## 查重说明

- `config_fingerprint` 相同的行必须写明 `repeat_of`，否则它被视为误重复。
- 复跑必须保持同一配置；若只是接近，不得写成复跑成功。
- 机器使用同目录的 `PARAMETER_MATRIX.csv` 做校验；本 Markdown 只负责让人快速阅读。
