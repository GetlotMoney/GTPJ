# PLVSE: Progressive Language-Guided Visual-Semantic Enhancement for Generalized Zero-Shot Learning

Version: `CONTENT-PAPER-V1`

Status: draft only

Writing boundary:

- This draft uses PLVSE project facts from the current GTPJ repository.
- DVSIE and DVSR are used only as local writing-style references.
- Verified numerical claims are limited to the CUB records already present in the repository.
- Cross-dataset comparison tables and module ablation tables must be filled only after verified results are synchronized.

---

# English Draft

## Abstract

Generalized Zero-Shot Learning (GZSL) aims to recognize images from seen or unseen classes by conducting cross-modal interactions to align visual-semantic representations. Recently, Contrastive Language-Image Pre-training (CLIP) models have shown remarkable global interaction capability in GZSL. However, CLIP models overlook local discriminative information for fine-grained classes.

To address these challenges, we propose Progressive Language-Guided Visual-Semantic Enhancement (PLVSE), a framework preserving the global interaction capability of CLIP while improving local visual-semantic interaction.

Specifically, first, we propose Progressive Semantic Enhancement (PSE) to model relationships among multiple textual descriptions and refine semantic representations with global visual features. Second, we propose Frequency-Guided Visual Disentanglement (FGVD) to select informative patch tokens and suppress noisy local evidence. Third, we propose Semantic-Guided Masked Prediction (SGMP) to reconstruct masked class-related representations and provide auxiliary supervision. These components form a global-to-local framework, in which refined semantic prototypes guide local evidence and complement the CLIP global prediction. Experiments on the CUB benchmark validate the effectiveness of PLVSE.

Keywords: Generalized zero-shot learning; CLIP; visual-semantic interaction; semantic enhancement; local discriminative information

## 1. Introduction

Deep learning has achieved remarkable success in traditional visual recognition tasks, relying on large-scale manually labeled datasets. However, these models often fail to generalize to unseen classes that are not present during training. Zero-Shot Learning (ZSL) and its more practical setting, Generalized Zero-Shot Learning (GZSL), are introduced to address the above challenge. Specifically, given auxiliary semantic information such as attribute annotations or textual descriptions, ZSL/GZSL constructs cross-modal interactions based on seen classes to align visual and semantic representations. This process enables knowledge transfer from seen classes to unseen classes.

According to the learning mechanism of GZSL, cross-modal interaction plays a critical role in improving zero-shot recognition performance. Early embedding-based methods learn a latent embedding space for visual-semantic interaction, including visual-to-semantic embedding, semantic-to-visual embedding, and shared embedding space learning. However, these methods often suffer from the domain shift problem. The classifier tends to assign unseen-class samples to seen classes, which limits generalized recognition. To address this issue, generative-based methods synthesize visual features for unseen classes and transform ZSL into a supervised learning problem. Despite their progress, these methods depend heavily on the quality of generated features.

Recently, large-scale vision-language models such as Contrastive Language-Image Pre-training (CLIP) have demonstrated strong global image-text alignment and zero-shot recognition capability. By learning from large-scale image-text pairs, CLIP provides a powerful global matching path between images and class texts. Prompt learning further adapts CLIP to downstream tasks. For example, CoOp replaces hand-crafted context words with learnable context vectors, while CoCoOp generates input-conditioned context tokens for each image. For GZSL, recent works introduce attribute prompts, visual-semantic adaptation, and local region modeling to improve cross-modal transfer.

However, existing CLIP-based GZSL methods still face two problems. First, global image-text matching may overlook local discriminative cues in fine-grained categories. For bird recognition, a small beak shape, wing bar, tail pattern, or head color may distinguish two categories with similar global appearance. Second, dense patch tokens contain background content and spatial redundancy. Directly using all patch tokens enlarges the interaction space and may introduce noisy local evidence. Therefore, a GZSL model should preserve the global recognition ability of CLIP while extracting compact and class-related local evidence.

To address these limitations, we propose Progressive Language-Guided Visual-Semantic Enhancement (PLVSE), a GZSL framework built on frozen CLIP image and text encoders. PLVSE keeps the global CLIP recognition path and introduces a complementary local visual-semantic path. The key idea is simple: class descriptions first become stronger semantic prototypes, then image features guide the refinement of seen-class semantics, and selected local visual tokens interact with the enhanced semantic prototypes.

Specifically, we design Progressive Semantic Enhancement (PSE) as the semantic core of the framework. PSE first models the relationships among multiple textual descriptions of each class. Its Image-Conditioned Semantic Adapter (ICSA) then uses global visual features to refine seen-class semantic representations. In parallel, Frequency-Guided Visual Disentanglement (FGVD) selects informative patch tokens and reduces geometry-dominated local interactions. Bidirectional Visual-Semantic Alignment (BVSA) uses the compact local memory and the enhanced semantic prototypes to produce local class scores. Finally, global and local scores are fused for GZSL prediction. During optimization, Semantic-Guided Masked Prediction (SGMP) reconstructs masked class-related representations and provides auxiliary supervision for the visual-semantic path.

The main contributions of this paper are summarized as follows:

1. We propose PLVSE, a progressive language-guided visual-semantic enhancement framework for generalized zero-shot recognition. PLVSE preserves the CLIP-based global path and introduces a complementary local visual-semantic path.

2. We design PSE as a unified semantic enhancement module. PSE models relationships among multiple textual descriptions and contains ICSA to refine seen-class semantic representations with global visual features.

3. We introduce FGVD, BVSA, and SGMP to improve local visual-semantic interaction. FGVD selects compact local visual evidence from CLIP patch tokens, BVSA produces local class scores, and SGMP provides auxiliary supervision by reconstructing masked class-related representations.

4. Verified CUB results show the effectiveness of the current PLVSE implementation. The verified V5 record obtains a best observed harmonic mean of 74.54 and a five-repeat mean harmonic value of 74.44.

## 2. Related Work

### 2.1 Generalized Zero-Shot Learning

Generalized zero-shot learning aims to recognize both seen and unseen classes in a shared label space. Compared with conventional ZSL, GZSL is more practical and more difficult because test images may belong to categories observed during training or categories never observed during training. This setting usually causes a bias towards seen classes, since the model learns visual classifiers only from seen-class images.

Existing GZSL methods can be broadly divided into embedding-based methods and generative-based methods. Embedding-based methods learn a mapping between visual features and semantic representations. Some methods map image features into the semantic space, some methods map semantic features into the visual space, and some methods learn a shared embedding space. These methods directly optimize visual-semantic compatibility, but they are sensitive to domain shift between seen and unseen classes.

Generative-based methods synthesize visual features for unseen classes under semantic guidance. After feature generation, ZSL can be converted into a supervised classification task. This route reduces the imbalance between seen and unseen classes. However, the final performance depends on whether the generated features are sufficiently realistic and discriminative.

PLVSE follows the embedding-based direction. Instead of generating unseen-class visual features, it uses frozen CLIP representations and strengthens visual-semantic interaction through progressive semantic enhancement and compact local evidence modeling.

### 2.2 Vision-Language Models for GZSL

Vision-language models provide a new route for zero-shot recognition. CLIP learns aligned image and text representations from large-scale image-text pairs. It can compare an image with class prompts and perform zero-shot classification without task-specific image labels. This global image-text alignment makes CLIP a strong backbone for GZSL.

Prompt learning adapts CLIP to downstream tasks by improving text representations. CoOp learns context vectors for class prompts. CoCoOp further generates input-conditioned prompts from image features, improving generalization to unseen classes. These methods show that semantic representations should not remain fixed when the downstream task changes.

For GZSL, recent methods use attribute prompts, class descriptions, or visual-semantic adaptation to improve transfer. These methods demonstrate that CLIP semantics can be adapted by learnable modules or image-conditioned signals. However, global CLIP matching still tends to emphasize holistic appearance. Fine-grained classes often need local evidence beyond the global token.

PLVSE uses CLIP as the frozen backbone and focuses on semantic enhancement plus local interaction. PSE strengthens class semantics from multiple textual descriptions. ICSA is placed inside PSE and uses the global visual token to refine seen-class semantic prototypes. This design lets the semantic side receive image-conditioned information while preserving the standard GZSL boundary.

### 2.3 Local Visual-Semantic Interaction

Local visual-semantic interaction is important for fine-grained recognition. Many GZSL methods attempt to discover discriminative regions and align them with semantic units. Region-based methods mine attribute-related regions. Transformer-based methods use attention to connect patch tokens with class attributes or textual descriptions. These methods improve classification when global features cannot separate similar categories.

However, dense local tokens are not always useful. CLIP patch tokens may contain object parts, background content, pose information, and spatial layout. If all local tokens are sent into cross-modal attention, the model may attend to redundant or geometry-dominated patterns instead of class-related visual evidence.

PLVSE addresses this issue with FGVD. It selects informative patch tokens by feature-frequency response and builds a compact local visual memory. The local memory then interacts with enhanced semantic prototypes. SGMP further constrains the local path by reconstructing masked class-related representations under semantic guidance.

## 3. Method

### 3.1 Problem Formulation

Let $\mathcal{Y}^{s}$ and $\mathcal{Y}^{u}$ denote the disjoint seen and unseen class sets. The full label space is $\mathcal{Y}=\mathcal{Y}^{s}\cup\mathcal{Y}^{u}$. The training set is defined as $\mathcal{D}^{s}=\{(x_i,y_i)\}_{i=1}^{N}$, where $y_i\in\mathcal{Y}^{s}$. During testing, an image may belong to a seen class or an unseen class.

For each class $c\in\mathcal{Y}$, we use a set of textual descriptions $\mathcal{T}_c=\{t_{c,m}\}_{m=1}^{M}$. The descriptions contain part-level cues and an overall class description. These descriptions are available for both seen and unseen classes and provide semantic information for transfer.

### 3.2 Overall Framework

PLVSE is built on frozen CLIP image and text encoders. Given an image $x$ and the textual descriptions of class $c$, the encoders produce the visual tokens and sentence embeddings:

$$
[g;P]=E_v(x), \quad T_c=[e_{c,1},e_{c,2},\ldots,e_{c,M}].
$$

The framework contains a global path and a local path. The global path keeps the original CLIP image-text matching ability. The local path selects compact patch tokens and interacts them with enhanced semantic prototypes. The framework has four main components. PSE enhances class semantics from multiple descriptions and includes ICSA for image-conditioned semantic refinement. FGVD selects informative patch tokens and builds a compact local memory. BVSA aligns the local memory with enhanced semantic prototypes and produces local class scores. SGMP provides auxiliary supervision for the local path during training.

### 3.3 Progressive Semantic Enhancement

Class descriptions contain richer information than class names. However, independent sentence embeddings do not automatically form a coherent class representation. PSE first models relationships among multiple textual descriptions, then uses the global visual token to refine seen-class semantic prototypes.

In the first stage, PSE applies a self-attention adapter to the sentence embeddings and obtains an image-independent semantic prototype. A mean-pooled prototype is first computed as the reference representation:

$$
p_c^{base}=\frac{1}{M}\sum_{m=1}^{M} e_{c,m}.
$$

Then, the relation among textual descriptions is modeled by the self-attention adapter:

$$
\hat{T}_c=\mathrm{LN}\left(2\left(\alpha_{in}A(T_c)+(1-\alpha_{in})T_c\right)\right).
$$

The attended descriptions are pooled and fused with the base prototype:

$$
p_c^{shared}=\mathrm{Norm}\left(\alpha_{out}\mathrm{Mean}(\hat{T}_c)+(1-\alpha_{out})p_c^{base}\right).
$$

In the second stage, ICSA projects the global visual token into a semantic residual and adds it to seen-class prototypes:

$$
r_x=\mathrm{Norm}(F_{icsa}(g)), \quad
p_{x,c}^{cond}=p_c^{shared}+\lambda_{icsa}\mathbf{1}[c\in\mathcal{Y}^{s}]r_x.
$$

Here $F_{icsa}(\cdot)$ is a two-layer projection network, $\lambda_{icsa}$ controls the residual strength, and $\mathbf{1}[\cdot]$ is an indicator function. The current implementation refines seen-class prototypes and keeps unseen-class prototypes unchanged. This setting does not use unseen-class images or unseen-class image labels during training. The same conditional prototype set is used by the global score path and the local interaction path.

### 3.4 Local Visual-Semantic Interaction

Dense CLIP patch tokens contain object parts, background content, pose information, and spatial redundancy. Directly sending all patch tokens into local interaction may introduce noisy evidence. FGVD therefore ranks patch tokens according to feature-frequency response and keeps only the top informative tokens.

$$
\mathcal{F}_i=\mathrm{FFTShift}(\mathrm{FFT}(p_i)), \quad
\tilde{p}_i=\mathrm{Re}\left(\mathrm{IFFT}(\mathrm{IFFTShift}(G_\sigma\odot\mathcal{F}_i))\right).
$$

The patch importance score is computed by comparing the feature response and the low-frequency reconstruction deviation:

$$
s_i=\frac{\frac{1}{d}\sum_{j=1}^{d}|p_{i,j}|}{\frac{1}{d}\sum_{j=1}^{d}|p_{i,j}-\tilde{p}_{i,j}|+\epsilon}.
$$

The top $K$ scoring tokens are retained:

$$
\mathcal{I}=\mathrm{TopK}(\{s_i\}_{i=1}^{N_p},K), \quad P_K=P[\mathcal{I}].
$$

The selected tokens are projected into a compact local memory:

$$
M_v=F_v(P_K).
$$

Based on this memory, BVSA performs two complementary interactions. In the visual-to-semantic direction, class prototypes query local visual memory and aggregate class-specific evidence. In the semantic-to-visual direction, selected local tokens query semantic prototypes and update local visual representations. The two directions produce complementary local scores:

$$
H_{v2s}=\mathrm{Decoder}_{v2s}(P^{cond},M_v), \quad
S_{v2s}(x,c)=\cos(H_{v2s,c},p_{x,c}^{cond}).
$$

$$
H_{s2v}=\mathrm{Decoder}_{s2v}(M_v,P^{cond}), \quad
\bar{h}_{s2v}=\frac{1}{K}\sum_{i=1}^{K}H_{s2v,i}, \quad
S_{s2v}(x,c)=\cos(\bar{h}_{s2v},p_{x,c}^{cond}).
$$

The final local score is computed as:

$$
S_{local}(x,c)=\beta S_{v2s}(x,c)+(1-\beta)S_{s2v}(x,c).
$$

This design lets the local path provide fine-grained evidence while keeping the global CLIP path as the main recognition basis.

### 3.5 Global-Local Score Fusion

The global path computes holistic image-text compatibility, and the local path supplies complementary fine-grained evidence. The final class score is obtained by additive fusion:

$$
S_{global}(x,c)=\tau\cos(g,p_{x,c}^{cond}), \quad
S_{final}(x,c)=S_{global}(x,c)+\lambda_{local}S_{local}(x,c).
$$

Here $\tau$ is the learnable CLIP logit scale and $\lambda_{local}$ controls the contribution of the local path.

### 3.6 Semantic-Guided Masked Prediction

Final classification loss supervises the local path only indirectly. SGMP adds a training-only auxiliary task. It first selects class-related local tokens according to their semantic relevance to the ground-truth prototype:

$$
\rho_i=\cos(M_{v,i},p_{x,y}^{cond}), \quad
\mathcal{M}=\mathrm{TopR}(\{\rho_i\}_{i=1}^{K}).
$$

The selected tokens are masked as prediction targets, while the remaining tokens provide context:

$$
z_{ctx}=\frac{1}{|\bar{\mathcal{M}}|}\sum_{i\in\bar{\mathcal{M}}}M_{v,i}, \quad
z_{tar}=\mathrm{sg}\left(\frac{1}{|\mathcal{M}|}\sum_{i\in\mathcal{M}}V_{0,i}\right).
$$

The matched and mismatched semantic prototypes define the masked prediction losses:

$$
\hat{z}^{+}=F_{pred}([z_{ctx};p_{x,y}^{cond}]), \quad
\mathcal{L}_{mpp}=1-\cos(\hat{z}^{+},z_{tar}), \quad
\mathcal{L}_{neg}=\max(0,\cos(\hat{z}^{-},z_{tar})-\cos(\hat{z}^{+},z_{tar})+\gamma).
$$

Here $\hat{z}^{-}$ is predicted with a negative seen-class prototype. SGMP is removed during inference.

### 3.7 Training Objective and Inference

PLVSE is trained with the seen-class classification loss and several auxiliary losses. The consistency loss aligns global and local score distributions. The topology loss preserves the semantic relation structure of class prototypes. The bidirectional mutual distribution distillation loss regularizes the two local interaction directions. The masked prediction loss and the negative loss supervise SGMP:

$$
\mathcal{L}
=
\mathcal{L}_{ce}
+\lambda_{cons}^{eff}\mathcal{L}_{cons}
+\lambda_{topo}\mathcal{L}_{topo}
+\lambda_{bmdd}\mathcal{L}_{bmdd}
+\lambda_{mpp}\mathcal{L}_{mpp}
+\lambda_{neg}\mathcal{L}_{neg}.
$$

During inference, SGMP and all auxiliary losses are removed. The model predicts over the full label space:

$$
\hat{y}=\arg\max_{c\in\mathcal{Y}^{s}\cup\mathcal{Y}^{u}}S_{final}(x,c).
$$

No unseen-class image or unseen-class image label is used during training.

## 4. Experiments

### 4.1 Dataset and Evaluation Metrics

The current verified draft reports CUB results. CUB contains 200 bird categories and is a fine-grained GZSL benchmark. The model is evaluated under the generalized zero-shot setting, where test images come from both seen and unseen classes.

We report unseen-class accuracy $U$, seen-class accuracy $S$, harmonic mean $H$, and conventional zero-shot accuracy $ZS$. The harmonic mean is computed as:

$$
H=\frac{2US}{U+S}.
$$

The harmonic mean is the main GZSL metric because it reflects the balance between seen-class and unseen-class recognition.

### 4.2 Implementation Details

PLVSE uses frozen CLIP ViT-L/14@336px as the visual and textual backbone. The feature dimension is 768. The current CUB configuration uses 200 classes, batch size 64, random seed 5, and GPT textual descriptions as semantic input.

For PSE, the current configuration uses four self-attention heads, dropout 0.5, inner residual ratio 0.35, and outer residual ratio 0.65. ICSA uses residual ratio 0.008. FGVD selects 32 patch tokens for the local memory. The local score weight is 0.2. SGMP uses top-8 semantic-guided masked tokens, hidden dimension 512, masked prediction loss weight 0.05, and negative loss weight 0.01.

The optimization schedule uses staged learning rates. The recorded V5 configuration contains three stages with learning rates $10^{-3}$, $10^{-4}$, and $10^{-5}$.

### 4.3 Main Verified Results on CUB

Table 1 reports the verified internal CUB records in the current repository. These results are not yet a cross-paper SOTA table. They show the confirmed development trajectory of the PLVSE implementation.

Table 1. Verified internal CUB GZSL results.

| Version | Evidence status | U | S | H | ZS | Note |
|---|---|---:|---:|---:|---:|---|
| GTPJ-v1 | accepted single run | 72.36 | 75.57 | 73.93 | 81.62 | first accepted baseline |
| GTPJ-v2 | valid single run | 71.32 | 77.52 | 74.29 | 81.59 | owner-activated mainline |
| GTPJ-v3 | valid single run | 71.22 | 77.60 | 74.27 | 81.38 | owner-accepted stochastic version |
| GTPJ-v4 | confirmed config-only | 71.53 | 77.66 | 74.47 | 81.25 | strongest confirmed reference |
| GTPJ-v5 | best observed repeat | 72.13 | 77.11 | 74.54 | 81.65 | active mainline best observation |
| GTPJ-v5 | five-repeat mean | 72.00 | 77.07 | 74.44 | 81.56 | confirmation-grade mean |

The V5 model obtains the best observed harmonic mean of 74.54 on CUB. Its five-repeat mean harmonic value is 74.44. The strongest confirmed reference remains the V4 config-only row with confirmed $H=74.47$. Therefore, the current paper draft should describe V5 as an effective active PLVSE implementation, not as a stronger confirmed baseline over all previous internal references.

### 4.4 Ablation Studies

The final paper should include ablation studies for the main components. The current main branch does not yet contain verified synchronized ablation records for every module. Therefore, Table 2 is a required result table, not a completed result table.

Table 2. Component ablation template.

| Setting | PSE | ICSA | FGVD | Local alignment | SGMP | U | S | H | ZS |
|---|---|---|---|---|---|---:|---:|---:|---:|
| Full PLVSE | yes | yes | yes | yes | yes | 72.13 | 77.11 | 74.54 | 81.65 |
| w/o PSE relation modeling | no | yes | yes | yes | yes | TBD | TBD | TBD | TBD |
| w/o ICSA | yes | no | yes | yes | yes | TBD | TBD | TBD | TBD |
| w/o FGVD selection | yes | yes | no | yes | yes | TBD | TBD | TBD | TBD |
| w/o local alignment path | yes | yes | no | no | no | TBD | TBD | TBD | TBD |
| w/o SGMP | yes | yes | yes | yes | no | TBD | TBD | TBD | TBD |
| CLIP-only baseline | no | no | no | no | no | TBD | TBD | TBD | TBD |

This table should answer three questions. First, it should show whether PSE improves semantic prototypes. Second, it should show whether ICSA provides useful image-conditioned semantic refinement. Third, it should show whether local information from FGVD and the local interaction path adds reliable evidence beyond the global CLIP path.

### 4.5 Analysis of Global and Local Predictions

PLVSE uses both global and local predictions. The global score preserves CLIP's holistic image-text alignment. The BVSA local score focuses on selected patch tokens and enhanced semantic prototypes. If the local branch improves unseen-class accuracy while reducing seen-class accuracy, the local branch should be interpreted as changing the seen-unseen balance rather than universally improving recognition.

For a fine-grained dataset such as CUB, this analysis is important. Local evidence may help categories with similar global appearance. However, local evidence may also introduce noise if the selected patches include background or pose-related regions. Therefore, the final paper should report not only the mean harmonic value, but also the separate changes in $U$ and $S$.

### 4.6 Qualitative Analysis

The qualitative analysis should visualize selected local patches and their semantic relations. For each example, the figure should show the original image, selected FGVD patches, the target class description, and the predicted class scores before and after local fusion. The goal is to show whether the local branch attends to class-related parts such as beak, head pattern, wing bars, tail shape, or body plumage.

The qualitative section should avoid claiming that the model truly detects object parts unless the visualization supports this claim. The descriptions provide part-level semantics, but the current model does not explicitly annotate part boxes. Therefore, the correct wording is local visual evidence or selected patch tokens, not ground-truth body-part localization.

## 5. Conclusion

This paper proposes PLVSE, a progressive language-guided visual-semantic enhancement framework for generalized zero-shot learning. PLVSE preserves the global recognition ability of frozen CLIP and introduces a local visual-semantic path for fine-grained evidence modeling. PSE enhances class semantics from multiple textual descriptions and contains ICSA to refine seen-class semantic prototypes with global visual features. FGVD selects compact local patch tokens, BVSA produces local class scores, and SGMP provides semantic-guided auxiliary supervision for the local path.

Verified CUB results show that the current PLVSE implementation reaches a best observed harmonic mean of 74.54 and a five-repeat mean harmonic value of 74.44. These results support the effectiveness of the framework as an active implementation. However, broader cross-dataset comparison and synchronized module ablation results are still required before making stronger claims such as state-of-the-art performance or stable superiority over all internal references.

## References to Format

The final reference list should be formatted with the target venue template. Required citation groups include:

1. Classical ZSL/GZSL: attribute embedding, semantic embedding, generative ZSL, and standard GZSL evaluation.

2. CLIP and prompt learning: CLIP, CoOp, CoCoOp.

3. GZSL with visual-semantic interaction: APAN, PSVMA+, DPPN, TransZero, I2DFormer, DSECN, TPR.

4. Local writing-style references used for this draft: DVSIE and DVSR.

---

# 中文对照稿

## 摘要

广义零样本学习（GZSL）旨在通过跨模态交互对齐视觉—语义表示，从而识别来自已见类或未见类的图像。近年来，对比语言—图像预训练（CLIP）模型在 GZSL 中展现出显著的全局交互能力。然而，CLIP 模型忽略了细粒度类别中的局部判别信息。

为解决上述问题，我们提出渐进式语言引导视觉—语义增强框架（PLVSE）。该框架保留 CLIP 的全局交互能力，同时增强局部视觉—语义交互。

具体而言，首先，我们提出渐进式语义增强模块（PSE），用于建模多条文本描述之间的关系，并利用全局视觉特征细化语义表示。其次，我们提出频率引导视觉解纠缠模块（FGVD），用于筛选信息性图像块特征，并抑制噪声局部证据。第三，我们提出语义引导掩码预测（SGMP），用于重建被遮盖的类别相关表示，并提供辅助监督。这些模块构成从全局到局部的框架，使细化后的语义原型引导局部证据，并补充 CLIP 全局预测。CUB 基准数据集上的实验验证了 PLVSE 的有效性。

关键词：广义零样本学习；CLIP；视觉—语义交互；语义增强；局部判别信息

## 1. 引言

深度学习依赖大规模人工标注数据集，在传统视觉识别任务中取得了显著成功。然而，这些模型通常难以泛化到训练数据中未出现的类别。零样本学习（ZSL）及其更具实际意义的广义零样本学习（GZSL）被提出用于解决上述挑战。具体而言，给定属性标注或文本描述等辅助语义信息，ZSL/GZSL 基于已见类构建跨模态交互，以对齐视觉表示与语义表示。这一过程使模型能够把已见类知识迁移到未见类。

根据 GZSL 的学习机制，跨模态交互对零样本识别性能具有关键作用。早期嵌入式方法学习视觉表示和语义表示之间的潜在嵌入空间，包括视觉到语义嵌入、语义到视觉嵌入以及共享嵌入空间学习。然而，这些方法容易受到域偏移问题影响。分类器倾向于把未见类样本预测为已见类，从而限制广义识别能力。为缓解这一问题，生成式方法在语义信息引导下合成未见类视觉特征，并将 ZSL 转化为监督分类任务。尽管取得了一定进展，这类方法的性能仍依赖于生成特征的质量。

近年来，CLIP 等大规模视觉—语言模型展现出较强的全局图文对齐和零样本识别能力。CLIP 通过海量图文对学习图像和文本表示之间的对应关系，为图像与类别文本之间的全局匹配提供了强基础。提示学习进一步增强了 CLIP 对下游任务的适应能力。例如，CoOp 使用可学习上下文向量替代人工设计的上下文词，CoCoOp 根据每幅图像生成输入条件化上下文 token。面向 GZSL，已有工作也通过属性提示、视觉—语义适配和局部区域建模提升跨模态迁移能力。

然而，现有 CLIP-based GZSL 方法仍存在两个问题。第一，全局图文匹配可能忽略细粒度类别中的局部判别线索。以鸟类识别为例，喙形、翼斑、尾部纹理或头部颜色等局部特征可能决定两个外观相近类别的区分。第二，密集 patch token 同时包含背景内容和空间冗余。直接使用所有 patch token 会扩大交互空间，并可能引入噪声局部证据。因此，GZSL 模型需要保留 CLIP 的全局识别能力，同时提取紧凑且类别相关的局部证据。

为解决上述局限，我们提出 PLVSE。PLVSE 基于冻结的 CLIP 图像编码器和文本编码器，保留 CLIP 全局识别路径，同时引入互补的局部视觉—语义路径。核心思路是：先把类别描述构造成更强的语义原型，再由图像特征引导已见类语义细化，最后让筛选后的局部视觉 token 与增强后的语义原型交互。

具体而言，我们将 PSE 作为框架的语义核心。PSE 首先建模每个类别多条文本描述之间的关系；其内部的 ICSA 随后利用全局视觉 token 细化已见类语义表示。与此同时，FGVD 筛选信息性 patch token，并减弱由几何关系主导的局部交互。双向视觉—语义对齐（BVSA）利用紧凑局部 memory 和增强语义原型生成局部分数。最后，全局分数与局部分数融合用于 GZSL 预测。训练阶段，SGMP 重建被遮盖的类别相关表示，为视觉—语义路径提供辅助监督。

本文贡献如下：

1. 我们提出 PLVSE，一种面向广义零样本识别的渐进式语言引导视觉—语义增强框架。PLVSE 保留 CLIP 全局路径，并引入互补的局部视觉—语义路径。

2. 我们设计 PSE 作为统一语义增强模块。PSE 建模多条文本描述之间的关系，并包含 ICSA，用全局视觉特征细化已见类语义表示。

3. 我们引入 FGVD、BVSA 和 SGMP 来增强局部视觉—语义交互。FGVD 从 CLIP patch token 中筛选紧凑局部证据，BVSA 生成局部类别分数，SGMP 通过重建被遮盖的类别相关表示提供辅助监督。

4. 已核实的 CUB 结果表明当前 PLVSE 实现有效。V5 记录取得 74.54 的最佳单次 H，以及 74.44 的五次重复平均 H。

## 2. 相关工作

### 2.1 广义零样本学习

广义零样本学习旨在共享标签空间中同时识别已见类和未见类。与传统 ZSL 相比，GZSL 更贴近真实应用，也更困难，因为测试图像既可能来自训练阶段出现过的类别，也可能来自训练阶段从未出现过的类别。由于模型只从已见类图像中学习视觉分类器，GZSL 通常存在偏向已见类的问题。

现有 GZSL 方法大体可分为嵌入式方法和生成式方法。嵌入式方法学习视觉特征与语义表示之间的映射关系。有的方法把图像特征映射到语义空间，有的方法把语义特征映射到视觉空间，也有的方法学习共享嵌入空间。这类方法直接优化视觉—语义兼容性，但容易受到已见类和未见类之间域偏移的影响。

生成式方法在语义信息引导下合成未见类视觉特征。得到合成特征后，ZSL 可以被转化为监督分类任务。这一路线缓解了已见类与未见类之间的样本不平衡。然而，最终性能取决于生成特征是否足够真实、足够有判别性。

PLVSE 沿用嵌入式路线。它不生成未见类视觉特征，而是使用冻结 CLIP 表示，并通过渐进式语义增强和紧凑局部证据建模来增强视觉—语义交互。

### 2.2 面向 GZSL 的视觉—语言模型

视觉—语言模型为零样本识别提供了新路线。CLIP 从大规模图文对中学习对齐的图像表示和文本表示。它可以将图像与类别提示进行比较，在没有任务特定图像标签的情况下执行零样本分类。这种全局图文对齐能力使 CLIP 成为 GZSL 的强骨干。

提示学习通过改进文本表示将 CLIP 适配到下游任务。CoOp 学习类别提示中的上下文向量。CoCoOp 进一步根据图像特征生成输入条件化提示，从而改善未见类泛化。这些方法说明，下游任务发生变化时，语义表示不应保持完全固定。

面向 GZSL，已有方法使用属性提示、类别描述或视觉—语义适配改善知识迁移。这些方法说明，CLIP 语义可以通过可学习模块或图像条件信号进行适配。然而，全局 CLIP 匹配仍倾向于强调整体外观。细粒度类别通常还需要全局 token 之外的局部证据。

PLVSE 使用 CLIP 作为冻结骨干，并聚焦语义增强与局部交互。PSE 根据多条文本描述增强类别语义。ICSA 被放在 PSE 内部，利用全局视觉 token 细化已见类语义原型。该设计使语义端接收图像条件信息，同时保持标准 GZSL 边界。

### 2.3 局部视觉—语义交互

局部视觉—语义交互对细粒度识别很重要。许多 GZSL 方法尝试发现判别性区域，并将这些区域与语义单元对齐。基于区域的方法挖掘属性相关区域。基于 Transformer 的方法使用注意力机制连接 patch token 与类别属性或文本描述。当全局特征无法区分相似类别时，这些方法可以改善分类。

然而，密集局部 token 并不总是有效。CLIP patch token 可能包含目标部位、背景内容、姿态信息和空间布局。如果把所有局部 token 都送入跨模态注意力，模型可能关注冗余模式或几何主导模式，而不是类别相关视觉证据。

PLVSE 使用 FGVD 处理这一问题。FGVD 根据特征频率响应筛选信息性 patch token，并构建紧凑局部视觉 memory。局部 memory 随后与增强后的语义原型交互。SGMP 进一步通过语义引导的掩码重建约束局部路径。

## 3. 方法

### 3.1 问题定义

令 $\mathcal{Y}^{s}$ 和 $\mathcal{Y}^{u}$ 分别表示互不相交的已见类集合和未见类集合。完整标签空间为 $\mathcal{Y}=\mathcal{Y}^{s}\cup\mathcal{Y}^{u}$。训练集定义为 $\mathcal{D}^{s}=\{(x_i,y_i)\}_{i=1}^{N}$，其中 $y_i\in\mathcal{Y}^{s}$。测试阶段，图像可能来自已见类，也可能来自未见类。

对于每个类别 $c\in\mathcal{Y}$，我们使用文本描述集合 $\mathcal{T}_c=\{t_{c,m}\}_{m=1}^{M}$。这些描述包含部位级线索和整体类别描述。它们对已见类和未见类都可用，并提供知识迁移所需的语义信息。

### 3.2 总体框架

PLVSE 基于冻结的 CLIP 图像编码器和文本编码器。给定图像 $x$ 和类别 $c$ 的文本描述，编码器得到视觉 token 和句子嵌入：

$$
[g;P]=E_v(x), \quad T_c=[e_{c,1},e_{c,2},\ldots,e_{c,M}].
$$

PLVSE 包含一条全局路径和一条局部路径。全局路径保留 CLIP 原有的图文匹配能力。局部路径筛选紧凑 patch token，并让它们与增强语义原型交互。框架包含四个主要部分。PSE 从多条描述中增强类别语义，并在内部使用 ICSA 进行图像条件语义细化。FGVD 筛选信息性 patch token 并构建紧凑局部 memory。BVSA 将局部 memory 与增强语义原型对齐，并生成局部类别分数。SGMP 在训练阶段为局部路径提供辅助监督。

### 3.3 渐进式语义增强

类别描述比类别名称包含更丰富的信息。然而，彼此独立的句子嵌入并不会自动形成统一类别表示。PSE 首先建模多条文本描述之间的关系，然后利用全局视觉 token 细化已见类语义原型。

第一阶段，PSE 对句子嵌入应用自注意力适配器，得到图像无关的语义原型。首先通过平均池化得到基础原型：

$$
p_c^{base}=\frac{1}{M}\sum_{m=1}^{M} e_{c,m}.
$$

然后，自注意力适配器建模多条描述之间的关系：

$$
\hat{T}_c=\mathrm{LN}\left(2\left(\alpha_{in}A(T_c)+(1-\alpha_{in})T_c\right)\right).
$$

经过注意力增强后的描述被池化，并与基础原型融合：

$$
p_c^{shared}=\mathrm{Norm}\left(\alpha_{out}\mathrm{Mean}(\hat{T}_c)+(1-\alpha_{out})p_c^{base}\right).
$$

第二阶段，ICSA 将全局视觉 token 投影为语义残差，并将其加入已见类原型：

$$
r_x=\mathrm{Norm}(F_{icsa}(g)), \quad
p_{x,c}^{cond}=p_c^{shared}+\lambda_{icsa}\mathbf{1}[c\in\mathcal{Y}^{s}]r_x.
$$

其中，$F_{icsa}(\cdot)$ 是两层投影网络，$\lambda_{icsa}$ 控制残差强度，$\mathbf{1}[\cdot]$ 是指示函数。当前实现细化已见类原型，并保持未见类原型不变。该设置在训练阶段不使用未见类图像或未见类图像标签。同一组条件原型同时提供给全局评分路径和局部交互路径。

### 3.4 局部视觉-语义交互

密集 CLIP patch token 同时包含目标部位、背景内容、姿态信息和空间冗余。直接把所有 patch token 送入局部交互可能引入噪声证据。因此，FGVD 根据特征频率响应对 patch token 排序，并只保留信息性最高的 token。

$$
\mathcal{F}_i=\mathrm{FFTShift}(\mathrm{FFT}(p_i)), \quad
\tilde{p}_i=\mathrm{Re}\left(\mathrm{IFFT}(\mathrm{IFFTShift}(G_\sigma\odot\mathcal{F}_i))\right).
$$

patch 重要性分数由特征响应和低频重建偏差计算：

$$
s_i=\frac{\frac{1}{d}\sum_{j=1}^{d}|p_{i,j}|}{\frac{1}{d}\sum_{j=1}^{d}|p_{i,j}-\tilde{p}_{i,j}|+\epsilon}.
$$

保留分数最高的 $K$ 个 token：

$$
\mathcal{I}=\mathrm{TopK}(\{s_i\}_{i=1}^{N_p},K), \quad P_K=P[\mathcal{I}].
$$

筛选后的 token 被投影为紧凑局部 memory：

$$
M_v=F_v(P_K).
$$

基于该 memory，BVSA 执行两个互补方向的交互。视觉到语义方向中，类别原型查询局部视觉 memory，并聚合类别相关证据。语义到视觉方向中，筛选后的局部 token 查询语义原型，并更新局部视觉表示。两个方向生成互补的局部分数：

$$
H_{v2s}=\mathrm{Decoder}_{v2s}(P^{cond},M_v), \quad
S_{v2s}(x,c)=\cos(H_{v2s,c},p_{x,c}^{cond}).
$$

$$
H_{s2v}=\mathrm{Decoder}_{s2v}(M_v,P^{cond}), \quad
\bar{h}_{s2v}=\frac{1}{K}\sum_{i=1}^{K}H_{s2v,i}, \quad
S_{s2v}(x,c)=\cos(\bar{h}_{s2v},p_{x,c}^{cond}).
$$

最终局部分数为：

$$
S_{local}(x,c)=\beta S_{v2s}(x,c)+(1-\beta)S_{s2v}(x,c).
$$

该设计使局部路径补充细粒度证据，同时保留全局 CLIP 路径作为主要识别基础。

### 3.5 全局-局部分数融合

全局路径计算整体图文兼容性，局部路径提供互补的细粒度证据。最终类别分数通过加性融合得到：

$$
S_{global}(x,c)=\tau\cos(g,p_{x,c}^{cond}), \quad
S_{final}(x,c)=S_{global}(x,c)+\lambda_{local}S_{local}(x,c).
$$

其中，$\tau$ 是可学习的 CLIP logit scale，$\lambda_{local}$ 控制局部路径的贡献。

### 3.6 语义引导掩码预测

最终分类损失只能间接监督局部路径。SGMP 增加一个只在训练阶段使用的辅助任务。它首先根据局部 token 与真实类别原型的语义相关性选择类别相关 token：

$$
\rho_i=\cos(M_{v,i},p_{x,y}^{cond}), \quad
\mathcal{M}=\mathrm{TopR}(\{\rho_i\}_{i=1}^{K}).
$$

被选中的 token 被遮盖作为预测目标，其余 token 提供上下文：

$$
z_{ctx}=\frac{1}{|\bar{\mathcal{M}}|}\sum_{i\in\bar{\mathcal{M}}}M_{v,i}, \quad
z_{tar}=\mathrm{sg}\left(\frac{1}{|\mathcal{M}|}\sum_{i\in\mathcal{M}}V_{0,i}\right).
$$

匹配语义原型和不匹配语义原型共同定义掩码预测损失：

$$
\hat{z}^{+}=F_{pred}([z_{ctx};p_{x,y}^{cond}]), \quad
\mathcal{L}_{mpp}=1-\cos(\hat{z}^{+},z_{tar}), \quad
\mathcal{L}_{neg}=\max(0,\cos(\hat{z}^{-},z_{tar})-\cos(\hat{z}^{+},z_{tar})+\gamma).
$$

其中，$\hat{z}^{-}$ 由负已见类原型预测得到。推理阶段移除 SGMP。

### 3.7 训练目标与推理

PLVSE 使用已见类分类损失和若干辅助损失进行训练。一致性损失对齐全局和局部分数分布。拓扑损失保持类别原型的语义关系结构。双向分布互蒸馏损失约束两个局部交互方向。掩码预测损失和负类损失监督 SGMP：

$$
\mathcal{L}
=
\mathcal{L}_{ce}
+\lambda_{cons}^{eff}\mathcal{L}_{cons}
+\lambda_{topo}\mathcal{L}_{topo}
+\lambda_{bmdd}\mathcal{L}_{bmdd}
+\lambda_{mpp}\mathcal{L}_{mpp}
+\lambda_{neg}\mathcal{L}_{neg}.
$$

推理阶段移除 SGMP 和所有辅助损失。模型在完整标签空间上预测：

$$
\hat{y}=\arg\max_{c\in\mathcal{Y}^{s}\cup\mathcal{Y}^{u}}S_{final}(x,c).
$$

训练过程中不使用未见类图像或未见类图像标签。

## 4. 实验

### 4.1 数据集与评价指标

当前已核实草稿报告 CUB 结果。CUB 包含 200 个鸟类类别，是细粒度 GZSL 基准。模型在广义零样本设置下评估，测试图像同时来自已见类和未见类。

我们报告未见类准确率 $U$、已见类准确率 $S$、调和平均值 $H$ 以及传统零样本准确率 $ZS$。调和平均值定义为：

$$
H=\frac{2US}{U+S}.
$$

调和平均值是主要 GZSL 指标，因为它反映已见类识别和未见类识别之间的平衡。

### 4.2 实现细节

PLVSE 使用冻结的 CLIP ViT-L/14@336px 作为视觉和文本骨干。特征维度为 768。当前 CUB 配置使用 200 个类别、batch size 64、随机种子 5，并使用 GPT 文本描述作为语义输入。

PSE 当前配置使用 4 个自注意力头、0.5 dropout、0.35 内部残差比例和 0.65 外部残差比例。ICSA 残差比例为 0.008。FGVD 选择 32 个 patch token 构建局部 memory。局部分数权重为 0.2。SGMP 使用 top-8 语义引导遮盖 token、512 隐藏维、0.05 掩码预测损失权重和 0.01 负类损失权重。

优化阶段使用分段学习率。已记录的 V5 配置包含三个阶段，学习率分别为 $10^{-3}$、$10^{-4}$ 和 $10^{-5}$。

### 4.3 CUB 主结果

表 1 报告当前仓库中已核实的 CUB 内部记录。这些结果不是跨论文 SOTA 对比表，而是 PLVSE 实现过程中的已确认开发轨迹。

表 1. 已核实 CUB GZSL 内部结果。

| 版本 | 证据状态 | U | S | H | ZS | 说明 |
|---|---|---:|---:|---:|---:|---|
| GTPJ-v1 | accepted single run | 72.36 | 75.57 | 73.93 | 81.62 | 首个 accepted baseline |
| GTPJ-v2 | valid single run | 71.32 | 77.52 | 74.29 | 81.59 | owner-activated mainline |
| GTPJ-v3 | valid single run | 71.22 | 77.60 | 74.27 | 81.38 | owner-accepted stochastic version |
| GTPJ-v4 | confirmed config-only | 71.53 | 77.66 | 74.47 | 81.25 | strongest confirmed reference |
| GTPJ-v5 | best observed repeat | 72.13 | 77.11 | 74.54 | 81.65 | active mainline best observation |
| GTPJ-v5 | five-repeat mean | 72.00 | 77.07 | 74.44 | 81.56 | confirmation-grade mean |

V5 模型在 CUB 上取得 74.54 的最佳单次 H。其五次重复平均 H 为 74.44。当前最强 confirmed reference 仍为 V4 config-only 行，对应 confirmed $H=74.47$。因此，当前论文草稿应将 V5 描述为有效的 active PLVSE 实现，而不能描述为稳定超过所有内部参考的 confirmed baseline。

### 4.4 消融实验

最终论文需要补齐主要组件消融。当前 main 分支尚未包含每个模块的已同步正式消融记录。因此，表 2 是必须完成的结果表，而不是已经完成的结果表。

表 2. 组件消融模板。

| 设置 | PSE | ICSA | FGVD | 局部对齐 | SGMP | U | S | H | ZS |
|---|---|---|---|---|---|---:|---:|---:|---:|
| Full PLVSE | yes | yes | yes | yes | yes | 72.13 | 77.11 | 74.54 | 81.65 |
| w/o PSE relation modeling | no | yes | yes | yes | yes | TBD | TBD | TBD | TBD |
| w/o ICSA | yes | no | yes | yes | yes | TBD | TBD | TBD | TBD |
| w/o FGVD selection | yes | yes | no | yes | yes | TBD | TBD | TBD | TBD |
| w/o local alignment path | yes | yes | no | no | no | TBD | TBD | TBD | TBD |
| w/o SGMP | yes | yes | yes | yes | no | TBD | TBD | TBD | TBD |
| CLIP-only baseline | no | no | no | no | no | TBD | TBD | TBD | TBD |

该表需要回答三个问题。第一，PSE 是否改善语义原型。第二，ICSA 是否提供有效的图像条件语义细化。第三，FGVD 和局部交互路径是否在全局 CLIP 路径之外提供稳定局部证据。

### 4.5 全局与局部预测分析

PLVSE 同时使用全局预测和局部预测。全局分数保留 CLIP 的整体图文对齐能力。BVSA 局部分数关注筛选后的 patch token 和增强语义原型。如果局部分支提高未见类准确率，同时降低已见类准确率，那么应将其解释为改变已见类与未见类之间的平衡，而不是全面提升识别能力。

对于 CUB 这样的细粒度数据集，这一分析尤其重要。局部证据可能帮助区分全局外观相近的类别。然而，如果筛选出的 patch 包含背景或姿态相关区域，局部证据也可能引入噪声。因此，最终论文不仅要报告平均 H，还要分别报告 $U$ 和 $S$ 的变化。

### 4.6 定性分析

定性分析应可视化被选中的局部 patch 及其语义关系。每个例子应展示原图、FGVD 选中的 patch、目标类别描述，以及局部融合前后的预测分数。目标是说明局部分支是否关注喙、头部纹理、翼斑、尾部形状或身体羽毛等类别相关区域。

定性部分不能声称模型真正完成了身体部位检测，除非可视化证据支持这一点。当前描述提供的是部位级语义，但模型没有显式使用部位框标注。因此，正确表述应是局部视觉证据或被选择的 patch token，而不是真实部位定位。

## 5. 结论

本文提出 PLVSE，一种面向广义零样本学习的渐进式语言引导视觉—语义增强框架。PLVSE 保留冻结 CLIP 的全局识别能力，并引入局部视觉—语义路径进行细粒度证据建模。PSE 从多条文本描述中增强类别语义，并包含 ICSA，用全局视觉特征细化已见类语义原型。FGVD 筛选紧凑局部 patch token，BVSA 生成局部类别分数，SGMP 则为局部路径提供语义引导的辅助监督。

已核实的 CUB 结果表明，当前 PLVSE 实现取得 74.54 的最佳单次 H 和 74.44 的五次重复平均 H。这些结果支持该框架作为有效 active implementation。可是，在做出 state-of-the-art 或稳定优于所有内部参考等更强结论之前，仍需要补齐跨数据集比较和同步后的模块消融结果。

## 待格式化参考文献

最终参考文献应按目标期刊或会议模板整理。必须包含以下引用组：

1. 经典 ZSL/GZSL：属性嵌入、语义嵌入、生成式 ZSL 和标准 GZSL 评价协议。

2. CLIP 与提示学习：CLIP、CoOp、CoCoOp。

3. 视觉—语义交互 GZSL：APAN、PSVMA+、DPPN、TransZero、I2DFormer、DSECN、TPR。

4. 本草稿参考的本地写作风格论文：DVSIE 和 DVSR。
