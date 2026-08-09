# V5-ABLATION-008：C/G/L/GL 四格贡献分解

本实验比较同一份 CUB、CLIP 缓存、gpt55 文本、类别顺序和评估口径下的四条明确路径。

- `C-FROZEN`：冻结 CLS 与未适配 gpt55 句子均值文本做余弦分类；不训练。
- `G-GLOBAL`：PSE、ICSA、全局分数；只计算 CE 与 topology。
- `L-LOCAL-SCORE`：PSE、ICSA、FGVD、BVSA、SGMP；最终只用 local score。没有 global 教师，因此 global-local consistency 在结构上不适用。
- `GL-FULL`：直接使用母版 `model.MyModel.GTPJ`。

每条路径使用种子 5、17，每个种子独立运行两次。本轮只作筛查与贡献分解，不是 confirmation。
