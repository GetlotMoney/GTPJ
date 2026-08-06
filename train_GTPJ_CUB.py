import os
import sys
import argparse
import torch
import torch.optim as optim
import numpy as np
import yaml
import clip
from types import SimpleNamespace
from datetime import datetime

# ★ 加速优化: 让 cuDNN 自动选最优算法 (对固定输入形状有效)
# ⚠️ RTX 5070 Ti (sm_120) + cuDNN 9.19 + BF16 在搜索内核时巨吃显存导致 8s/step
#    暂时禁用, 只用预加载和 BF16 加速
torch.backends.cudnn.benchmark = False

from model.MyModel import GTPJ
from tools.dataset import CUBDataLoader
from tools.helper_func import eval_zs_gzsl, get_clip_spatial_features
from tools.reproducibility import (
    config_bool,
    config_int,
    configure_reproducibility,
    make_batch_generator,
)

CACHE_DIR = './data/cache'
CACHE_TRAIN_FEAT   = os.path.join(CACHE_DIR, 'CUB_train_features.pt')
CACHE_TRAIN_LABEL  = os.path.join(CACHE_DIR, 'CUB_train_labels.pt')
CACHE_TRAIN_PATCH  = os.path.join(CACHE_DIR, 'CUB_train_patch_features.pt')  # [N, 576, 768] float16
# ★ 多视角增强缓存 (可选, 由 extract_features.py [K] 生成)
CACHE_TRAIN_FEAT_AUG  = os.path.join(CACHE_DIR, 'CUB_train_features_aug.pt')        # [K, N, 768]
CACHE_TRAIN_PATCH_AUG = os.path.join(CACHE_DIR, 'CUB_train_patch_features_aug.pt')  # [K, N, 576, 768] f16
CACHE_TRAIN_VIEWS     = os.path.join(CACHE_DIR, 'CUB_train_views.pt')
# ★ 加速优化 (方案 2a): CLIP 文本嵌入缓存 (避免每次启动重新跑 CLIP encode_text)
CACHE_CLASS_TEXT      = os.path.join(CACHE_DIR, 'CUB_class_text_embeds.pt')         # [200, 768]
# {text_source}_text_embeds.pt: gpt4 / claude / gpt55 / merge
def _gpt_embed_cache_path(text_source):
    return os.path.join(CACHE_DIR, f'CUB_{text_source}_text_embeds.pt')


def _gpt_sentence_cache_path(text_source):
    return os.path.join(CACHE_DIR, f'CUB_{text_source}_sentence_embeds.pt')

# ==========================================
#   日志
# ==========================================
current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
LOG_FILE = f"./train_log/CUB/training_log_CUB_{current_time}.txt"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def print_log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'))
    with open(LOG_FILE, "a", encoding='utf-8') as f:
        f.write(msg + "\n")


# ==========================================
#   加载配置
# ==========================================
parser = argparse.ArgumentParser(description="Train GTPJ on CUB GZSL.", allow_abbrev=False)
parser.add_argument(
    "--config",
    default="./config/GTPJ_cub_gzsl.yaml",
    help="Path to the YAML config. Use an experiment-local config.yaml for tracked runs.",
)
args = parser.parse_args()
config_path = os.path.normpath(args.config)

if not os.path.exists(config_path):
    print_log(f"Error: Config file {config_path} not found!")
    raise SystemExit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
config = {k: v['value'] if isinstance(v, dict) and 'value' in v else v for k, v in config.items()}
config = SimpleNamespace(**config)
config.config_path = config_path

if not hasattr(config, 'device'):
    config.device = 'cuda:0'

seed = config_int(config, 'random_seed', 5)
strict_determinism = config_bool(config, 'strict_determinism', False)
deterministic_warn_only = config_bool(config, 'deterministic_warn_only', True)
use_dedicated_batch_rng = config_bool(config, 'use_dedicated_batch_rng', False)
batch_sampling_seed = config_int(config, 'batch_sampling_seed', seed)
repro_state = configure_reproducibility(
    seed,
    strict_determinism=strict_determinism,
    deterministic_warn_only=deterministic_warn_only,
)


def _planned_total_epochs(cfg):
    lr_stages_cfg = getattr(cfg, 'lr_stages', None) or []
    if lr_stages_cfg:
        return sum(int(stage['epochs']) for stage in lr_stages_cfg)
    return int(getattr(cfg, 'epochs', 0)) + int(getattr(cfg, 'extra_epochs', 0) or 0)


planned_total_epochs = _planned_total_epochs(config)
epoch_schedule = "lr_stages" if (getattr(config, 'lr_stages', None) or []) else "epochs + extra_epochs"


print_log("=" * 60)
print_log("  CLIP + PSE + FGVD + BVSA + SGMP  |  CUB GZSL Training")
print_log("=" * 60)
print_log(f"  Log file  : {LOG_FILE}")
print_log(f"  Config    : {config_path}")
print_log(f"  Device    : {config.device}")
print_log(f"  Config epochs        : {config.epochs}")
print_log(f"  Planned train epochs : {planned_total_epochs} ({epoch_schedule})")
print_log(f"  Batch size: {config.batch_size}")
print_log(f"  Random seed: {seed}")
print_log(f"  Strict determinism: {strict_determinism}")
print_log(f"  Dedicated batch RNG: {use_dedicated_batch_rng}")
print_log(f"  Batch RNG seed: {batch_sampling_seed}")
print_log("=" * 60)

# ★ 模块配置摘要 (每次训练记录, 便于回看)
print_log("")
print_log("┌─ Module Configuration ───────────────────────────────────┐")
print_log(f"│  text_source   : {config.text_source}")
print_log(f"│  use_aug_cache : {getattr(config, 'use_aug_cache', False)}")
print_log("├─ Architecture ──────────────────────────────────────────┤")
print_log(f"│  use_fgvd_geometry: {config.use_fgvd_geometry}")
print_log(f"│  pse_adapter_ratio: {config.pse_adapter_ratio}")
use_pse_self_attention = config.use_pse_self_attention
print_log(f"│  use_pse_self_attention: {use_pse_self_attention}")
if use_pse_self_attention:
    print_log(f"│  pse_apply_unseen: {config.pse_apply_unseen}")
    print_log(f"│  pse_heads       : {config.pse_heads}")
    print_log(f"│  pse_dropout     : {config.pse_dropout}")
    print_log(f"│  pse_outer_ratio : {config.pse_outer_ratio}")
    print_log(f"│  pse_inner_ratio : {config.pse_inner_ratio}")
print_log(f"│  tf_common_dim : {config.tf_common_dim}")
print_log(f"│  tf_heads      : {config.tf_heads}")
print_log(f"│  tf_dropout    : {config.tf_dropout}")
print_log("├─ Pooling (s2v) ─────────────────────────────────────────┤")
print_log(f"│  pool_method   : {config.pool_method}")
print_log("├─ Fixed Scoring ─────────────────────────────────────────┤")
print_log(f"│  score_mode    : {config.score_mode}")
print_log(f"│  local_weight  : {config.local_weight}")
print_log(f"│  weight_s2v    : {config.weight_s2v}")
print_log(f"│  text_residual : {config.text_residual}")
print_log(f"│  visual_residual: {config.visual_residual}")
print_log(f"│  use_icsa      : {config.use_icsa}")
print_log(f"│  icsa_ratio    : {config.icsa_ratio}")
print_log("├─ Loss Weights ──────────────────────────────────────────┤")
print_log(f"│  lambda_consist: {config.lambda_consist}")
print_log(f"│  lambda_topo   : {config.lambda_topo_pearson}")
print_log(f"│  lambda_bmdd   : {config.lambda_bmdd}")
print_log(f"│  lambda_mpp    : {config.lambda_mpp}")
print_log(f"│  lambda_neg    : {config.lambda_neg}")
print_log(f"│  sgmp_context  : {config.sgmp_context_mode}")
print_log(f"│  sgmp_text     : {config.sgmp_text_mode}")
print_log(f"│  bvsa_text     : {config.bvsa_text_mode}")
print_log("├─ Resume ────────────────────────────────────────────────┤")
print_log(f"│  resume_from        : {getattr(config, 'resume_from', '')!r}")
print_log(f"│  resume_lr_schedule : {getattr(config, 'resume_lr_schedule', 'continue')}")
print_log(f"│  extra_epochs       : {getattr(config, 'extra_epochs', 0)}")
print_log("├─ Speed Optimizations ───────────────────────────────────┤")
print_log(f"│  use_amp       : {getattr(config, 'use_amp', False)}  (BF16 autocast)")
print_log(f"│  pin_memory    : enabled if patch cache loaded  non_blocking H2D : True")
print_log("├─ Reproducibility ───────────────────────────────────────┤")
print_log(f"│  strict_determinism      : {strict_determinism}")
print_log(f"│  deterministic_warn_only : {deterministic_warn_only}")
print_log(f"│  use_dedicated_batch_rng : {use_dedicated_batch_rng}")
print_log(f"│  batch_sampling_seed     : {batch_sampling_seed}")
print_log(f"│  cudnn_benchmark         : {repro_state['cudnn_benchmark']}")
print_log(f"│  cudnn_deterministic     : {repro_state['cudnn_deterministic']}")
print_log(f"│  deterministic_algorithms: {repro_state['deterministic_algorithms']}")
print_log(f"│  cublas_workspace_config : {repro_state['cublas_workspace_config'] or '(unset)'}")
print_log(f"│  torch/cuda              : {repro_state['torch_version']} / {repro_state['cuda_version'] or 'cpu'}")
print_log("└─────────────────────────────────────────────────────────┘")

# ==========================================
#   加载 CLIP (冻结)
# ==========================================
print_log("\n[1/5] Loading CLIP (ViT-L/14@336px)...")
clip_model, _ = clip.load("ViT-L/14@336px", device=config.device)
clip_model = clip_model.float()
clip_model.eval()
for p in clip_model.parameters():
    p.requires_grad = False
print_log("      CLIP loaded & frozen.")

# ==========================================
#   加载数据
# ==========================================
print_log("\n[2/5] Loading CUB Dataset...")
dataloader = CUBDataLoader('.', config.device, is_balance=False)
print_log(f"      Train images : {dataloader.ntrain_clip}")
print_log(f"      Seen classes : {len(dataloader.seenclasses)}  (used for training)")
print_log(f"      Unseen classes: {len(dataloader.unseenclasses)}  (zero-shot target)")
print_log(f"      Test seen    : {len(dataloader.test_seen_loader.dataset)} images")
print_log(f"      Test unseen  : {len(dataloader.test_unseen_loader.dataset)} images")

# Reset RNG after CLIP/data setup so model init and training sampling start from the run seed.
repro_state = configure_reproducibility(
    seed,
    strict_determinism=strict_determinism,
    deterministic_warn_only=deterministic_warn_only,
)
batch_generator = make_batch_generator(use_dedicated_batch_rng, batch_sampling_seed)


def _sample_randperm(length):
    if batch_generator is None:
        return torch.randperm(length)
    return torch.randperm(length, generator=batch_generator)


def _sample_randint(high, size):
    if batch_generator is None:
        return torch.randint(0, high, size)
    return torch.randint(0, high, size, generator=batch_generator)

# ==========================================
#   加载/提取训练集图像特征缓存
# ==========================================
# 优先级:
#   1) 多视角增强缓存 (use_aug_cache=True 且文件存在) — K 个增强视角
#   2) 单视角 patch 缓存 — 完整 576 token 但无增强
#   3) 单视角 CLS 缓存   — 仅 CLS, 兼容旧逻辑
#   4) 实时提取
USE_AUG = bool(getattr(config, 'use_aug_cache', False))
HAS_AUG_CACHE = (USE_AUG
                 and os.path.exists(CACHE_TRAIN_PATCH_AUG)
                 and os.path.exists(CACHE_TRAIN_FEAT_AUG)
                 and os.path.exists(CACHE_TRAIN_LABEL))
HAS_PATCH_CACHE = os.path.exists(CACHE_TRAIN_PATCH) and os.path.exists(CACHE_TRAIN_LABEL)
HAS_CLS_CACHE   = os.path.exists(CACHE_TRAIN_FEAT)  and os.path.exists(CACHE_TRAIN_LABEL)

train_patches  = None   # [N, 576, 768] float16 存 CPU
train_features = None   # [N, 768] float32 (legacy)
train_labels   = None
train_cls      = None
train_patches_aug = None   # [K, N, 576, 768] float16 多视角
train_cls_aug     = None   # [K, N, 768] float32 多视角
NUM_VIEWS_CACHE   = 1

if HAS_AUG_CACHE:
    print_log("\n[★] Loading MULTI-VIEW augmented cache (best mode)...")
    train_patches_aug = torch.load(CACHE_TRAIN_PATCH_AUG, map_location='cpu', weights_only=True)
    train_cls_aug     = torch.load(CACHE_TRAIN_FEAT_AUG,  map_location='cpu', weights_only=True)
    train_labels      = torch.load(CACHE_TRAIN_LABEL,     map_location=config.device, weights_only=True)
    NUM_VIEWS_CACHE   = train_patches_aug.shape[0]
    print_log(f"      Views K        : {NUM_VIEWS_CACHE}")
    print_log(f"      train_cls_aug    : {train_cls_aug.shape}  dtype={train_cls_aug.dtype}")
    print_log(f"      train_patches_aug: {train_patches_aug.shape}  dtype={train_patches_aug.dtype}")
    print_log(f"      train_labels     : {train_labels.shape}")
    USE_CACHE = 'aug'
elif HAS_PATCH_CACHE:
    print_log("\n[★] Loading train PATCH + CLS features from cache (single-view)...")
    train_patches = torch.load(CACHE_TRAIN_PATCH, map_location='cpu', weights_only=True)
    train_labels  = torch.load(CACHE_TRAIN_LABEL, map_location=config.device, weights_only=True)
    train_cls = torch.load(CACHE_TRAIN_FEAT, map_location='cpu', weights_only=True) if HAS_CLS_CACHE else None

    # ⚠️ GPU 预加载已禁用 (实测在 PyTorch 2.11+cu128 + 5070 Ti 上仍会慢到 8s/step)
    # 真因不明, 怀疑 BF16 张量核 + 6GB 静态张量索引在 Blackwell 上有 driver 路径问题
    # 保守模式: patch 留 CPU, 每 step CPU→GPU 切片
    # ★ Bug 修复 (2026-05-25): 真正调用 pin_memory(), 让 non_blocking=True 异步传输生效
    # 旧代码注释说 pinned 但没真调, non_blocking 在普通 CPU tensor 上效果几乎为 0
    try:
        train_patches = train_patches.pin_memory()
        if train_cls is not None:
            train_cls = train_cls.pin_memory()
        _PIN_OK = True
        print_log(f"      ★ Patches pinned to locked CPU memory (non_blocking H2D enabled)")
    except Exception as _pin_err:
        _PIN_OK = False
        print_log(f"      [info] pin_memory failed ({_pin_err}), fallback to plain CPU tensor")

    if train_cls is None:
        print_log("      WARNING: CLS cache missing, fallback to patch.mean()")
    else:
        print_log(f"      train_cls:     {train_cls.shape}  dtype={train_cls.dtype}  device={train_cls.device}")
    print_log(f"      train_patches: {train_patches.shape}  dtype={train_patches.dtype}  device={train_patches.device}")
    print_log(f"      train_labels:  {train_labels.shape}")
    USE_CACHE = 'patch'
elif HAS_CLS_CACHE:
    print_log("\n[★] Loading train CLS features from cache (legacy mode)...")
    train_features = torch.load(CACHE_TRAIN_FEAT,  map_location=config.device, weights_only=True)
    train_labels   = torch.load(CACHE_TRAIN_LABEL, map_location=config.device, weights_only=True)
    print_log(f"      train_features: {train_features.shape}  train_labels: {train_labels.shape}")
    USE_CACHE = 'cls'
else:
    print_log("\n[!] Cache not found. Will extract features on-the-fly (slow).")
    print_log("    Run: python tools/extract_features.py  to generate cache.")
    USE_CACHE = None

# ==========================================
#   生成类名文本特征 (CLIP 模板 prompt)
# ==========================================
print_log("\n[3/5] Encoding class name text features...")
class_names = [c.split('.')[-1].replace("_", " ") for c in dataloader.class_names]
# ★ 加速优化 (方案 2a): 类名文本嵌入缓存 (200 句 prompt, 启动省 ~3s)
if os.path.exists(CACHE_CLASS_TEXT):
    class_text_embeds = torch.load(CACHE_CLASS_TEXT, map_location=config.device,
                                    weights_only=True)
    print_log(f"      ★ class_text_embeds loaded from cache: {class_text_embeds.shape}")
else:
    prompts = [f"a photo of a {c}, a type of bird." for c in class_names]
    text_inputs = torch.cat([clip.tokenize(p) for p in prompts]).to(config.device)
    with torch.no_grad():
        class_text_embeds = clip_model.encode_text(text_inputs).float()  # [200, 768]
    try:
        torch.save(class_text_embeds.cpu(), CACHE_CLASS_TEXT)
        print_log(f"      class_text_embeds: {class_text_embeds.shape}  (cached for next run)")
        class_text_embeds = class_text_embeds.to(config.device)
    except Exception as e:
        print_log(f"      class_text_embeds: {class_text_embeds.shape}  "
                  f"(cache save failed: {e})")

# ==========================================
#   加载 GPT-4 描述并编码
# ==========================================
gpt_text_embeds = None
gpt_sentence_embeds = None
# 文本数据来源切换:
#   'gpt4'     → cub.pt          (GPT-4, 7 句/类)
#   'claude'   → cub_claude.pt   (Claude, 7 句/类)
#   'gpt55'    → cub_gpt55.pt    (GPT-5.5 style, 7 句/类)
#   'merge'    → cub_merge.pt    (GPT-4 + Claude 拼接, 14 句/类)
#   'weighted' → α × Claude_emb + (1-α) × GPT_emb (各自编码再加权融合)
text_source = getattr(config, 'text_source', 'gpt4')


def _encode_descriptions(file_path, dataloader, clip_model, device, class_text_embeds):
    """加载并 CLIP 编码描述文件 → 返回 [200, 768] 嵌入"""
    sentences_dict = torch.load(file_path, map_location='cpu', weights_only=False)
    embeds_list = []
    hit = 0
    for cls_name in dataloader.class_names:
        gpt_key = '.'.join(cls_name.split('.')[1:]).lower()
        if gpt_key in sentences_dict:
            sentences = sentences_dict[gpt_key]
            tokens = torch.cat([clip.tokenize(s) for s in sentences]).to(device)
            with torch.no_grad():
                feats = clip_model.encode_text(tokens).float()
            embeds_list.append(feats.mean(dim=0))
            hit += 1
        else:
            idx = dataloader.class_names.index(cls_name)
            embeds_list.append(class_text_embeds[idx])
    return torch.stack(embeds_list), hit, len(sentences_dict)


def _encode_description_sentences(file_path, dataloader, clip_model, device, class_text_embeds):
    """加载并 CLIP 编码描述文件 → 返回 [200, M, 768] 句级嵌入"""
    sentences_dict = torch.load(file_path, map_location='cpu', weights_only=False)
    max_sentences = max(len(v) for v in sentences_dict.values()) if sentences_dict else 1
    embeds_list = []
    hit = 0
    for cls_idx, cls_name in enumerate(dataloader.class_names):
        gpt_key = '.'.join(cls_name.split('.')[1:]).lower()
        if gpt_key in sentences_dict:
            sentences = list(sentences_dict[gpt_key])
            tokens = torch.cat([clip.tokenize(s) for s in sentences]).to(device)
            with torch.no_grad():
                feats = clip_model.encode_text(tokens).float()
            if feats.size(0) < max_sentences:
                pad = feats[-1:].expand(max_sentences - feats.size(0), -1)
                feats = torch.cat([feats, pad], dim=0)
            elif feats.size(0) > max_sentences:
                feats = feats[:max_sentences]
            hit += 1
        else:
            feats = class_text_embeds[cls_idx].unsqueeze(0).expand(max_sentences, -1)
        embeds_list.append(feats)
    return torch.stack(embeds_list), hit, len(sentences_dict)


if text_source == 'weighted':
    if bool(config.use_pse_self_attention):
        raise ValueError("use_pse_self_attention=True does not support text_source='weighted'.")
    text_alpha = getattr(config, 'text_alpha', 1.0)
    gpt_path    = os.path.join('.', 'data', 'gpt4_data', 'cub.pt')
    claude_path = os.path.join('.', 'data', 'gpt4_data', 'cub_claude.pt')
    print_log(f"\n[4/5] Using Weighted fusion: α={text_alpha} × Claude + {1-text_alpha:.2f} × GPT-4")

    # ★ 加速优化 (方案 2a): weighted 模式两套都缓存
    weighted_cache = os.path.join(CACHE_DIR,
                                   f'CUB_weighted_a{text_alpha:.2f}_text_embeds.pt')
    if os.path.exists(weighted_cache):
        gpt_text_embeds = torch.load(weighted_cache, map_location=config.device,
                                      weights_only=True)
        print_log(f"      ★ weighted text embeds loaded from cache: {gpt_text_embeds.shape}")
    else:
        print_log(f"      Encoding GPT-4 descriptions...")
        gpt_embeds, gpt_hit, _    = _encode_descriptions(gpt_path,    dataloader, clip_model,
                                                          config.device, class_text_embeds)
        print_log(f"      Encoding Claude descriptions...")
        claude_embeds, claude_hit, _ = _encode_descriptions(claude_path, dataloader, clip_model,
                                                             config.device, class_text_embeds)
        gpt_text_embeds = text_alpha * claude_embeds + (1.0 - text_alpha) * gpt_embeds
        print_log(f"      GPT hit: {gpt_hit} | Claude hit: {claude_hit} classes")
        try:
            torch.save(gpt_text_embeds.cpu(), weighted_cache)
            gpt_text_embeds = gpt_text_embeds.to(config.device)
        except Exception:
            pass
    print_log(f"      gpt_text_embeds: {gpt_text_embeds.shape} (α={text_alpha})")
else:
    if text_source == 'merge':
        gpt4_data_path = os.path.join('.', 'data', 'gpt4_data', 'cub_merge.pt')
        print_log(f"\n[4/5] Using Merge (GPT-4 + Claude) descriptions: {gpt4_data_path}")
    elif text_source == 'claude':
        gpt4_data_path = os.path.join('.', 'data', 'gpt4_data', 'cub_claude.pt')
        print_log(f"\n[4/5] Using Claude descriptions: {gpt4_data_path}")
    elif text_source == 'gpt55':
        gpt4_data_path = os.path.join('.', 'data', 'gpt4_data', 'cub_gpt55.pt')
        print_log(f"\n[4/5] Using GPT-5.5 descriptions: {gpt4_data_path}")
    else:
        gpt4_data_path = os.path.join('.', 'data', 'gpt4_data', 'cub.pt')
        print_log(f"\n[4/5] Using GPT-4 descriptions: {gpt4_data_path}")

    # ★ 加速优化 (方案 2a): GPT 文本嵌入缓存 (200 类 × 7 句 = 1400 个 CLIP encode_text)
    # 启动省 ~10 秒 (CLIP ViT-L/14 文本编码慢, 7 次 encode_text)
    embed_cache = _gpt_embed_cache_path(text_source)
    sentence_cache = _gpt_sentence_cache_path(text_source)
    use_pse_sentence_text = bool(config.use_pse_self_attention)
    if use_pse_sentence_text and os.path.exists(sentence_cache):
        gpt_sentence_embeds = torch.load(sentence_cache, map_location=config.device,
                                        weights_only=True)
        gpt_text_embeds = gpt_sentence_embeds.mean(dim=1)
        print_log(f"      ★ gpt_sentence_embeds loaded from cache: {gpt_sentence_embeds.shape}")
        print_log(f"      gpt_text_embeds derived by mean: {gpt_text_embeds.shape}")
    elif (not use_pse_sentence_text) and os.path.exists(embed_cache):
        gpt_text_embeds = torch.load(embed_cache, map_location=config.device,
                                      weights_only=True)
        print_log(f"      ★ gpt_text_embeds loaded from cache: {gpt_text_embeds.shape}")
    elif os.path.exists(gpt4_data_path):
        print_log(f"      Loading text descriptions from {gpt4_data_path}...")
        if use_pse_sentence_text:
            gpt_sentence_embeds, hit, n_cls = _encode_description_sentences(
                gpt4_data_path, dataloader, clip_model, config.device, class_text_embeds)
            gpt_text_embeds = gpt_sentence_embeds.mean(dim=1)
        else:
            gpt_text_embeds, hit, n_cls = _encode_descriptions(
                gpt4_data_path, dataloader, clip_model, config.device, class_text_embeds)
        n_desc = len(list(torch.load(gpt4_data_path, map_location='cpu',
                                     weights_only=False).values())[0])
        print_log(f"      {n_cls} classes × {n_desc} descriptions/class")
        print_log(f"      GPT hit: {hit} classes | fallback: {n_cls - hit} classes")
        try:
            torch.save(gpt_text_embeds.cpu(), embed_cache)
            if use_pse_sentence_text and gpt_sentence_embeds is not None:
                torch.save(gpt_sentence_embeds.cpu(), sentence_cache)
            print_log(f"      gpt_text_embeds: {gpt_text_embeds.shape}  (cached for next run)")
            if use_pse_sentence_text:
                print_log(f"      gpt_sentence_embeds: {gpt_sentence_embeds.shape}  (cached for next run)")
            gpt_text_embeds = gpt_text_embeds.to(config.device)
            if gpt_sentence_embeds is not None:
                gpt_sentence_embeds = gpt_sentence_embeds.to(config.device)
        except Exception as e:
            print_log(f"      gpt_text_embeds: {gpt_text_embeds.shape}  "
                      f"(cache save failed: {e})")
    else:
        print_log(f"      WARNING: text data not found at {gpt4_data_path}, using class name only")

# ==========================================
#   初始化模型
# ==========================================
print_log("\n[5/5] Initializing model...")

# 只取 seen 类的文本特征传给模型训练
# unseen 类的原始 CLIP 文本特征用于评估时拼接
seen_gpt_embeds = gpt_text_embeds[dataloader.seenclasses] \
    if gpt_text_embeds is not None else class_text_embeds[dataloader.seenclasses]
# unseen 类也用 GPT 7句平均（语义更丰富），不再用类名模板
# GPT 描述是纯文本语义，不含视觉监督信号，不算信息泄露
unseen_clip_embeds = gpt_text_embeds[dataloader.unseenclasses] \
    if gpt_text_embeds is not None else class_text_embeds[dataloader.unseenclasses]
seen_sentence_embeds = gpt_sentence_embeds[dataloader.seenclasses] \
    if gpt_sentence_embeds is not None else None
unseen_sentence_embeds = gpt_sentence_embeds[dataloader.unseenclasses] \
    if gpt_sentence_embeds is not None else None

model = GTPJ(
    config,
    dataloader.seenclasses,
    dataloader.unseenclasses,
    seen_text_embeds=seen_gpt_embeds,       # [150, 768] seen 类 GPT 文本
    unseen_text_embeds=unseen_clip_embeds,  # [50, 768]  unseen 类原始 CLIP 文本
    class_attr=dataloader.att,              # [200, 312] CUB 专家属性
    attr_text_embeds=dataloader.clip_att,    # [312, 768] CLIP 属性文本原型
    seen_sentence_embeds=seen_sentence_embeds,
    unseen_sentence_embeds=unseen_sentence_embeds,
).to(config.device)

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print_log(f"      Total params    : {total_params:,}")
print_log(f"      Trainable params: {trainable_params:,}")

# ==========================================
#   优化器 & 调度器
# ==========================================
optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)

# ==========================================
#   Resume 系统
# ==========================================
# 三种使用场景:
#   1. 从头训练 (默认): yaml resume_from='' → 不加载任何 checkpoint
#   2. 续训接着原 LR: resume_from='auto' + resume_lr_schedule='continue'
#   3. 续训重启 LR: resume_from='auto' + resume_lr_schedule='restart'
#   4. 微调: resume_from='auto' + resume_lr_schedule='finetune' (LR=1e-4)
#
# checkpoint 内容 (full_ckpt): model + optimizer + scheduler + epoch + best_H
# best_model_*.pth 仅含规范字段的 model.state_dict；历史权重必须先运行显式转换工具。
import glob


def find_latest_checkpoint(ckpt_dir, full_only=False):
    """
    在 ckpt_dir 下找最新的 checkpoint
    full_only=True: 只找含完整状态的 ckpt_full_*.pth
    full_only=False: 也接受规范字段的 best_model_*.pth（仅权重）
    """
    if full_only:
        candidates = glob.glob(os.path.join(ckpt_dir, 'ckpt_full_*.pth'))
    else:
        candidates = (glob.glob(os.path.join(ckpt_dir, 'ckpt_full_*.pth'))
                      + glob.glob(os.path.join(ckpt_dir, 'best_model_*.pth')))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


resume_from        = getattr(config, 'resume_from', '')
resume_lr_schedule = getattr(config, 'resume_lr_schedule', 'continue')
extra_epochs       = int(getattr(config, 'extra_epochs', 0))

start_epoch = 1     # 默认从 epoch 1 开始
best_H = 0.0
best_metrics = {'U': 0, 'S': 0, 'H': 0, 'ZS': 0, 'epoch': 0}

if resume_from:
    if resume_from == 'auto':
        # ★ Bug 修复 (2026-05-25): continue 模式只接受 ckpt_full_*.pth
        # 否则 legacy best_model_*.pth (仅权重) 比 full ckpt 新时会退化, 丢失 optimizer/scheduler
        _full_only = (resume_lr_schedule == 'continue')
        ckpt_path = find_latest_checkpoint('./train_log/CUB', full_only=_full_only)
    else:
        ckpt_path = resume_from

    if ckpt_path is None or not os.path.exists(ckpt_path):
        print_log(f"\n[!] resume_from='{resume_from}' but no checkpoint found, "
                  f"starting from scratch.")
    else:
        print_log(f"\n[Resume] Loading checkpoint: {ckpt_path}")
        ckpt = torch.load(ckpt_path, map_location=config.device,
                          weights_only=False)

        # 支持两种规范 ckpt 格式:
        # 1) 完整 ckpt: dict with 'model_state_dict' / 'optimizer_state_dict' / ...
        # 2) 仅权重 ckpt: 直接是规范字段的 model.state_dict()
        if isinstance(ckpt, dict) and 'model_state_dict' in ckpt:
            # 完整 checkpoint
            model.load_state_dict(ckpt['model_state_dict'])
            print_log(f"  ✓ Loaded model weights")

            # ★ 不论 resume_lr_schedule 是什么, 都读 epoch/best 信息以正确显示进度
            #   仅 LR/optimizer/scheduler 是否恢复因模式而异
            ckpt_epoch = ckpt.get('epoch', 0)
            best_H = ckpt.get('best_H', 0.0)
            if 'best_metrics' in ckpt:
                best_metrics = ckpt['best_metrics']

            if resume_lr_schedule == 'continue':
                # 继续 LR 进度: 恢复 optimizer + scheduler, epoch 接着数
                required_states = {'optimizer_state_dict', 'scheduler_state_dict'}
                missing_states = sorted(required_states - set(ckpt))
                if missing_states:
                    raise ValueError(
                        "resume_lr_schedule='continue' 需要同一干净母版产生的完整 checkpoint；"
                        f"当前缺少 {missing_states}。历史转换权重请使用 restart 或 finetune。"
                    )
                optimizer.load_state_dict(ckpt['optimizer_state_dict'])
                print_log(f"  ✓ Loaded optimizer state")
                scheduler.load_state_dict(ckpt['scheduler_state_dict'])
                print_log(f"  ✓ Loaded scheduler state")
                start_epoch = ckpt_epoch + 1
                print_log(f"  ✓ Resuming from epoch {start_epoch}, best_H so far = {best_H*100:.2f}%")
            elif resume_lr_schedule == 'restart':
                # 只载权重, LR 重启 cosine 0.001 → 0
                # epoch 计数仍从 1 (因为 LR 调度从 0 开始, 跟 ckpt epoch 不一致)
                print_log(f"  ✓ Loaded model weights (epoch {ckpt_epoch}, best_H={best_H*100:.2f}%)")
                print_log(f"  ✓ LR scheduler restarted (LR=0.001 → cosine over {config.epochs} epochs)")
                print_log(f"  ⚠ epoch counter resets to 1 (not continuing from {ckpt_epoch + 1})")
            elif resume_lr_schedule == 'finetune':
                # LR 重置 finetune_lr (默认 1e-4), cosine 在新 epochs 上从头走
                # epoch 计数也从 1 (类似 restart)
                # ★ 2026-05-25: 支持 yaml 配置 finetune_lr (默认 1e-4 兼容旧实验)
                #   方案 B 多段训练: 第一段 finetune_lr=1e-4, 第二段 finetune_lr=1e-5
                finetune_lr = float(getattr(config, 'finetune_lr', 1e-4))
                for g in optimizer.param_groups:
                    g['lr'] = finetune_lr
                scheduler = optim.lr_scheduler.CosineAnnealingLR(
                    optimizer, T_max=config.epochs)
                print_log(f"  ✓ Loaded model weights (epoch {ckpt_epoch}, best_H={best_H*100:.2f}%)")
                print_log(f"  ✓ Finetune mode: LR={finetune_lr:g}, cosine over {config.epochs} epochs")
                print_log(f"  ⚠ epoch counter resets to 1 (treating as new finetune run)")
        else:
            # 仅模型权重；load_state_dict 默认严格检查，历史字段不能静默混入。
            model.load_state_dict(ckpt)
            print_log(f"  ✓ Loaded canonical model weights only "
                      f"(no optimizer/scheduler/epoch state)")
            print_log(f"  ⚠ resume_lr_schedule='{resume_lr_schedule}' "
                      f"applies to LR, but no optimizer state to restore")
            if resume_lr_schedule == 'finetune':
                finetune_lr = float(getattr(config, 'finetune_lr', 1e-4))
                for g in optimizer.param_groups:
                    g['lr'] = finetune_lr
                scheduler = optim.lr_scheduler.CosineAnnealingLR(
                    optimizer, T_max=config.epochs)
                print_log(f"  ✓ Finetune mode: LR={finetune_lr:g}")

# 续训时在原 epochs 基础上加 extra_epochs
total_epochs = config.epochs + extra_epochs
if extra_epochs > 0:
    print_log(f"  + {extra_epochs} extra epochs → total {total_epochs} epochs")
    # 调度器也要扩 T_max (重新初始化, 用当前 LR 作为起点)
    if resume_lr_schedule != 'continue':
        scheduler = optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=total_epochs)

# ──────────────────────────────────────────────────────────────
# ★ 2026-05-25: 一键多段训练 (Multi-Stage Training)
# ──────────────────────────────────────────────────────────────
# yaml 写法示例:
#   lr_stages:
#     value:
#       - {lr: 0.001,  epochs: 20}    # 第 1 段: 头训
#       - {lr: 0.0001, epochs: 30}    # 第 2 段: finetune
#       - {lr: 0.00001, epochs: 30}   # 第 3 段: micro-finetune
#
# 行为:
#   - total_epochs 自动等于各段 epochs 之和 (覆盖上面 extra_epochs 计算)
#   - 每段开始时: 把 optimizer.lr 切换到 stage.lr, 重新初始化 CosineAnnealingLR(T_max=stage.epochs)
#   - 关掉 (lr_stages 为空 / None / 不存在): 完全走旧逻辑, 兼容 H=72.95 ckpt recipe
lr_stages = getattr(config, 'lr_stages', None) or []
stage_boundaries = []     # 第 i 段结束时的 epoch 编号 (1-indexed, 含)
if lr_stages:
    print_log(f"\n[Multi-Stage] {len(lr_stages)} stages enabled "
              f"(overrides epochs/extra_epochs):")
    cum = 0
    for i, st in enumerate(lr_stages):
        cum += int(st['epochs'])
        stage_boundaries.append(cum)
        _emin = float(st.get('eta_min', 0))
        print_log(f"  Stage {i+1}: lr={float(st['lr']):g}, epochs={int(st['epochs'])}, eta_min={_emin:g} "
                  f"(epoch {cum - int(st['epochs']) + 1}..{cum})")
    total_epochs = stage_boundaries[-1]
    print_log(f"  Total epochs (sum of stages) = {total_epochs}")

    # 第 1 段立即生效: 设 lr + 重置 cosine
    first = lr_stages[0]
    for g in optimizer.param_groups:
        g['lr'] = float(first['lr'])
    _emin = float(first.get('eta_min', 0))
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(first['epochs']), eta_min=_emin)
    print_log(f"  [OK] Stage 1 active: lr={float(first['lr']):g}, "
              f"cosine T_max={int(first['epochs'])}, eta_min={_emin:g}")

# ==========================================
#   训练循环
# ==========================================
iters_per_epoch = dataloader.ntrain_clip // config.batch_size
total_iters = iters_per_epoch * total_epochs

# 最佳模型保存路径
BEST_MODEL_DIR = './train_log/CUB'
BEST_MODEL_PATH = os.path.join(BEST_MODEL_DIR, f'best_model_CUB_{current_time}.pth')
# 完整 checkpoint 保存路径 (含 optimizer/scheduler/epoch)
CKPT_FULL_PATH  = os.path.join(BEST_MODEL_DIR, f'ckpt_full_CUB_{current_time}.pth')

print_log("\n" + "=" * 60)
print_log(f"  Start Training: epoch [{start_epoch}/{total_epochs}], "
          f"{iters_per_epoch} iters/epoch")
print_log("=" * 60)

# ==========================================
#   ★ 加速优化 (方案 D): Mixed Precision (autocast + GradScaler)
# ==========================================
# autocast: forward 自动用 fp16 张量核（FGVD 矩阵乘加速约 30%）
# GradScaler: backward 自动放大 loss 防 fp16 underflow
# GTPJ-v1 keeps AMP disabled by default for reproducibility.
USE_AMP = bool(getattr(config, 'use_amp', False))
if USE_AMP:
    # ★ 新 API: torch.amp.autocast('cuda', ...)
    # 用 BF16 而非 FP16: 5070 Ti 原生支持, 数值范围与 FP32 同, 无需 GradScaler
    from torch.amp import autocast
    print_log(f"  ★ AMP enabled (BF16 autocast, no GradScaler needed)")
else:
    print_log(f"  ⚠ AMP disabled (use_amp=False), running fp32")

for epoch in range(start_epoch, total_epochs + 1):

    # ---------- 训练阶段 ----------
    model.train()
    epoch_loss = 0.0
    epoch_iters = 0

    print_log(f"\n{'─'*60}")
    print_log(f"  Epoch [{epoch}/{total_epochs}]  Training...")
    print_log(f"{'─'*60}")

    for step in range(iters_per_epoch):
        optimizer.zero_grad()

        if USE_CACHE == 'aug':
            # ── 多视角增强缓存: 每张图随机抽 1 个视角 ──
            idx = _sample_randperm(train_patches_aug.shape[1])[:config.batch_size]
            view_idx = _sample_randint(NUM_VIEWS_CACHE, (config.batch_size,))
            batch_label = train_labels[idx]
            patch_batch = train_patches_aug[view_idx, idx].to(config.device).float()  # [B, 576, 768]
            cls_batch   = train_cls_aug[view_idx, idx].to(config.device).float().unsqueeze(1)  # [B, 1, 768]
            clip_features = torch.cat([cls_batch, patch_batch], dim=1)                # [B, 577, 768]
        elif USE_CACHE == 'patch':
            # ── 随机采样：每步随机取 batch ──
            idx = _sample_randperm(len(train_patches))[:config.batch_size]
            batch_label = train_labels[idx]
            # ★ 加速优化 (方案 A): pin_memory + non_blocking 异步 H2D
            # train_patches 已在 __init__ 时 pin_memory(), 这里 non_blocking=True
            # 让 CPU→GPU 传输与 GPU forward 并发, 减少阻塞等待
            if train_patches.is_cuda:
                patch_batch = train_patches[idx].float()                # 已在 GPU, 直接 float32
            else:
                patch_batch = train_patches[idx].to(
                    config.device, non_blocking=True).float()
            if train_cls is not None:
                if train_cls.is_cuda:
                    cls_batch = train_cls[idx].float().unsqueeze(1)
                else:
                    cls_batch = train_cls[idx].to(
                        config.device, non_blocking=True).float().unsqueeze(1)
                clip_features = torch.cat([cls_batch, patch_batch], dim=1)
            else:
                cls_batch = patch_batch.mean(dim=1, keepdim=True)
                clip_features = torch.cat([cls_batch, patch_batch], dim=1)
        elif USE_CACHE == 'cls':
            idx = _sample_randperm(len(train_features))[:config.batch_size]
            batch_label = train_labels[idx]
            clip_features = train_features[idx].unsqueeze(1)  # [B, 1, 768]
        else:
            # ── 实时模式：读图 → CLIP 提取特征 ──
            batch_label, batch_images, batch_att = dataloader.next_batch(config.batch_size)
            clip_features = get_clip_spatial_features(clip_model, batch_images).float()

        # Forward (训练模式：只用 150 seen 类 logits)
        # ★ 加速优化 (方案 D): autocast 让 FGVD 注意力走 BF16 张量核
        # BF16 比 FP16 数值范围大, 5070 Ti 原生支持, GradScaler 也可省略
        if USE_AMP:
            with autocast('cuda', dtype=torch.bfloat16):
                out_package = model(clip_features, is_train=True)
                in_package = out_package.copy()
                in_package['batch_label'] = batch_label
                loss_pack = model.compute_loss(in_package)
                loss = loss_pack['loss']
            # BF16 不需要 GradScaler (数值范围足够), 直接 backward
            loss.backward()
            optimizer.step()
        else:
            out_package = model(clip_features, is_train=True)
            in_package = out_package.copy()
            in_package['batch_label'] = batch_label
            loss_pack = model.compute_loss(in_package)
            loss = loss_pack['loss']

            # Backward
            loss.backward()
            optimizer.step()

        epoch_loss += loss.item()
        epoch_iters += 1

        # 每 20 步打印一次进度
        if (step + 1) % 20 == 0 or (step + 1) == iters_per_epoch:
            avg_loss = epoch_loss / epoch_iters
            ce_v   = loss_pack.get('loss_ce',      torch.tensor(0.)).item()
            cons_v = loss_pack.get('loss_consist', torch.tensor(0.)).item()
            topo_v = loss_pack.get('loss_topo',    torch.tensor(0.)).item()
            bmdd_v = loss_pack.get('loss_bmdd',    torch.tensor(0.)).item()
            mpp_v  = loss_pack.get('loss_mpp',     torch.tensor(0.)).item()
            neg_v  = loss_pack.get('loss_neg',     torch.tensor(0.)).item()
            print_log(f"  Step [{step+1:3d}/{iters_per_epoch}] | "
                      f"Loss: {loss.item():.4f} | Avg: {avg_loss:.4f} | "
                      f"CE: {ce_v:.3f}  Cons: {cons_v:.3f}  "
                      f"Topo: {topo_v:.4f}  BMDD: {bmdd_v:.4f}  "
                      f"MPP: {mpp_v:.4f}  Neg: {neg_v:.4f}")

    # 更新学习率
    scheduler.step()
    current_lr = optimizer.param_groups[0]['lr']
    avg_epoch_loss = epoch_loss / epoch_iters

    print_log(f"\n  >> Epoch [{epoch}/{total_epochs}] Train Summary")
    print_log(f"     Avg Loss : {avg_epoch_loss:.4f}")
    print_log(f"     LR       : {current_lr:.6f}")

    # ★ 2026-05-25: 多段训练 - 段边界自动切到下一段
    # 当前 epoch 等于某段终点 → 切换到下一段 lr + 重置 cosine T_max
    if lr_stages and epoch in stage_boundaries and epoch < total_epochs:
        next_idx = stage_boundaries.index(epoch) + 1
        if next_idx < len(lr_stages):
            next_stage = lr_stages[next_idx]
            new_lr = float(next_stage['lr'])
            new_T = int(next_stage['epochs'])

            # ★ 2026-05-25: 段切换时是否从历史 best ckpt 重启 (warm-restart)
            #   yaml 写法: lr_stages: [{lr:..., epochs:..., restart_from_best: True}, ...]
            #   等价于"严格 early stopping at best + finetune from best"
            #   这是 GZSL 领域 (TransZero/MSDN) 的标准做法, 比严格连续高 ~0.8 H
            if bool(next_stage.get('restart_from_best', False)):
                # 从当前 run 已保存的 best ckpt 重启
                if os.path.exists(CKPT_FULL_PATH):
                    _ckpt = torch.load(CKPT_FULL_PATH, map_location=config.device,
                                       weights_only=False)
                    if isinstance(_ckpt, dict) and 'model_state_dict' in _ckpt:
                        model.load_state_dict(_ckpt['model_state_dict'])
                        _bH = _ckpt.get('best_H', 0.0) * 100
                        _bep = _ckpt.get('epoch', 0)
                        print_log(f"\n  ★ Warm-restart: rolled back to best ckpt "
                                  f"(epoch {_bep}, H={_bH:.2f}%)")
                else:
                    print_log(f"\n  ⚠ restart_from_best=True 但 best ckpt 还不存在, 跳过回滚")

            for g in optimizer.param_groups:
                g['lr'] = new_lr
            _emin = float(next_stage.get('eta_min', 0))
            scheduler = optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=new_T, eta_min=_emin)
            print_log(f"\n  ★★★ Stage {next_idx + 1} starts at epoch {epoch + 1} "
                      f"★★★\n     lr → {new_lr:g}, cosine T_max={new_T}, eta_min={_emin:g}")

    # ---------- 测试阶段 ----------
    print_log(f"\n  >> Epoch [{epoch}/{total_epochs}] Evaluating GZSL...")
    gzsl_bias = getattr(config, 'gzsl_bias', 0.0)
    acc_seen, acc_novel, H, acc_zs = eval_zs_gzsl(
        dataloader, clip_model, model, config.device,
        bias_unseen=gzsl_bias)

    # 更新最佳结果
    if H > best_H:
        best_H = H
        best_metrics = {
            'U': acc_novel,
            'S': acc_seen,
            'H': H,
            'ZS': acc_zs,
            'epoch': epoch
        }
        # 保存最佳模型权重（写盘失败不影响训练继续）
        # 文件名带 H 后缀, 便于跨 run 排序识别
        H_int = int(round(H * 10000))
        BEST_MODEL_PATH_WITH_H = BEST_MODEL_PATH.replace(
            '.pth', f'_H{H_int}.pth')
        try:
            # 先删本次 run 之前更低 H 的旧权重 (同 timestamp 但低 H)
            import glob
            old_pattern = BEST_MODEL_PATH.replace('.pth', '_H*.pth')
            for old_p in glob.glob(old_pattern):
                if old_p != BEST_MODEL_PATH_WITH_H:
                    try:
                        os.remove(old_p)
                    except Exception:
                        pass
            # 保存当前最佳 (仅模型权重, 兼容旧逻辑)
            torch.save(model.state_dict(), BEST_MODEL_PATH_WITH_H)
            print_log(f"  [★] Best model saved → {BEST_MODEL_PATH_WITH_H}")

            # ★ 同时保存完整 checkpoint (含 optimizer/scheduler 用于 resume)
            # 文件总是覆盖同一个路径, 只保留当前 run 的最新
            try:
                torch.save({
                    'epoch': epoch,
                    'best_H': best_H,
                    'best_metrics': best_metrics,
                    'model_state_dict':     model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                }, CKPT_FULL_PATH)
            except Exception as e2:
                print_log(f"  [!] Full ckpt save failed (training continues): {e2}")
        except Exception as e:
            print_log(f"  [!] Best model save failed (training continues): {e}")
            # 删除可能产生的损坏文件
            if os.path.exists(BEST_MODEL_PATH_WITH_H):
                try:
                    os.remove(BEST_MODEL_PATH_WITH_H)
                except Exception:
                    pass

    # 打印当前 epoch 结果
    print_log(f"\n  ┌─ Epoch [{epoch}/{total_epochs}] Results ─────────────────────")
    print_log(f"  │  GZSL-U (Unseen Acc) : {acc_novel*100:.2f}%")
    print_log(f"  │  GZSL-S (Seen Acc)   : {acc_seen*100:.2f}%")
    print_log(f"  │  GZSL-H (Harmonic)   : {H*100:.2f}%  {'★ NEW BEST' if H == best_H else ''}")
    print_log(f"  │  ZSL    (ZS Acc)     : {acc_zs*100:.2f}%")
    print_log(f"  └──────────────────────────────────────────────────────")

# ==========================================
#   最终汇总
# ==========================================
print_log("\n" + "=" * 60)
print_log("  Training Finished!")
print_log("=" * 60)
print_log(f"  Best Results @ Epoch {best_metrics['epoch']}")
print_log(f"  ┌─────────────────────────────────────")
print_log(f"  │  GZSL-U : {best_metrics['U']*100:.2f}%")
print_log(f"  │  GZSL-S : {best_metrics['S']*100:.2f}%")
print_log(f"  │  GZSL-H : {best_metrics['H']*100:.2f}%")
print_log(f"  │  ZSL    : {best_metrics['ZS']*100:.2f}%")
print_log(f"  └─────────────────────────────────────")
print_log(f"\n  Log saved to: {LOG_FILE}")
