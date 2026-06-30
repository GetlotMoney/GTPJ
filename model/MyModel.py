"""
GTPJ framework model.

This file intentionally keeps only the active baseline path used by
``config/versions/v1.yaml``:

- Progressive Semantic Enhancement (PSE)
- Frequency-Guided Visual Disentanglement (FGVD)
- Bidirectional Visual-Semantic Alignment (BVSA)
- Image-Conditioned Semantic Adapter (ICSA)
- Semantic-Guided Masked Prediction (SGMP)
- fixed add scoring: S_final = S_global + local_weight * S_local
- CE, consistency, topology, BMDD, MPP, and negative semantic losses

Interface contract:
- forward(clip_features, is_train=False) returns a dict with ``clip_S_pp``.
- is_train=True  -> logits shape [B, n_seen].
- is_train=False -> logits shape [B, num_class].
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def _gaussian_kernel_1d(length, sigma):
    x = torch.arange(-length // 2 + 1, length // 2 + 1, dtype=torch.float32)
    kernel = torch.exp(-0.5 * (x / sigma) ** 2)
    return kernel / torch.max(kernel)


def _autocast_disabled(tensor):
    return torch.amp.autocast(device_type=tensor.device.type, enabled=False)


def _config_get(config, key, legacy_key=None, default=None):
    if hasattr(config, key):
        return getattr(config, key)
    if legacy_key is not None and hasattr(config, legacy_key):
        return getattr(config, legacy_key)
    return default


def fgvd_select_patches(F_p, K=64, sigma=None, largest=True, formula="v2_abs_mean"):
    """Select top-K patches for Frequency-Guided Visual Disentanglement."""
    _, N, D = F_p.shape
    K = max(1, min(int(K), N))

    F_p_fp32 = F_p.float()
    x_freq = torch.fft.fft(F_p_fp32, dim=-1)
    if sigma is None:
        sigma = D ** 0.5
    gs_k = _gaussian_kernel_1d(D, sigma).to(F_p_fp32.device)
    x_freq = torch.fft.fftshift(x_freq, dim=-1)
    x_freq = x_freq * gs_k
    x_freq = torch.fft.ifftshift(x_freq, dim=-1)
    x_lp = torch.fft.ifft(x_freq, dim=-1).real

    if formula == "v1_strict":
        diff = F_p_fp32 / (torch.abs(x_lp - F_p_fp32) + 1e-6)
        patch_score = diff.mean(dim=-1)
    elif formula == "v3_norm":
        patch_score = 1.0 / (torch.norm(x_lp - F_p_fp32, dim=-1) + 1e-6)
    else:
        diff = F_p_fp32 / (torch.abs(x_lp - F_p_fp32) + 1e-6)
        patch_score = diff.abs().mean(dim=-1)

    if isinstance(largest, str) and largest.lower() == "both":
        k_half = K // 2
        _, idx_top = torch.topk(patch_score, k=k_half, dim=1, largest=True)
        _, idx_bot = torch.topk(patch_score, k=K - k_half, dim=1, largest=False)
        topk_indices = torch.cat([idx_top, idx_bot], dim=1)
    else:
        _, topk_indices = torch.topk(patch_score, k=K, dim=1, largest=bool(largest))

    return topk_indices, patch_score


lastvit_select_patches = fgvd_select_patches


class SemanticPrototypeAdapter(nn.Module):
    """Bottleneck adapter in Progressive Semantic Enhancement."""

    def __init__(self, c_in, reduction=4):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(c_in, c_in // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(c_in // reduction, c_in, bias=False),
        )

    def forward(self, x):
        return self.fc(x)


Adapter = SemanticPrototypeAdapter


class ProgressiveSemanticSelfAttention(nn.Module):
    """Sentence-level self-attention inside Progressive Semantic Enhancement."""

    def __init__(self, dim, heads=1, dropout=0.5, inner_ratio=0.5):
        super().__init__()
        self.inner_ratio = float(inner_ratio)
        self.attn = nn.MultiheadAttention(
            embed_dim=dim,
            num_heads=int(heads),
            dropout=float(dropout),
            batch_first=True,
        )
        self.proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(float(dropout))
        self.layer_norm = nn.LayerNorm(dim)

    def forward(self, x):
        attn_out, _ = self.attn(x, x, x, need_weights=False)
        attn_out = self.dropout(self.proj(attn_out))
        mixed = self.inner_ratio * attn_out + (1.0 - self.inner_ratio) * x
        return self.layer_norm(2.0 * mixed)


class BoxRelationalEmbedding(nn.Module):
    """Precomputed 24x24 patch-grid relational geometry embedding."""

    def __init__(self, grid_size=(24, 24), dim_g=64, wave_len=1000.0):
        super().__init__()
        self.grid_size = grid_size
        self.dim_g = dim_g
        self.wave_len = wave_len
        self.register_buffer("geometry_embedding", self._compute_embedding())

    def _compute_embedding(self):
        H, W = self.grid_size
        seq_len = H * W

        x = torch.arange(H).float()
        y = torch.arange(W).float()
        px_min = x.view(-1, 1).expand(-1, W).contiguous().view(-1)
        py_min = y.view(1, -1).expand(H, -1).contiguous().view(-1)
        px_max = px_min + 1
        py_max = py_min + 1

        cx = (px_min + px_max) * 0.5
        cy = (py_min + py_max) * 0.5
        w = px_max - px_min + 1.0
        h = py_max - py_min + 1.0

        delta_x = cx.unsqueeze(0) - cx.unsqueeze(1)
        delta_x = torch.clamp(torch.abs(delta_x / w.unsqueeze(0)), min=1e-3).log()
        delta_y = cy.unsqueeze(0) - cy.unsqueeze(1)
        delta_y = torch.clamp(torch.abs(delta_y / h.unsqueeze(0)), min=1e-3).log()
        delta_w = torch.log(w.unsqueeze(0) / w.unsqueeze(1))
        delta_h = torch.log(h.unsqueeze(0) / h.unsqueeze(1))
        pos_mat = torch.stack([delta_x, delta_y, delta_w, delta_h], dim=-1)

        feat_range = torch.arange(self.dim_g / 8).float()
        dim_mat = 1.0 / (self.wave_len ** (feat_range / (self.dim_g / 8)))
        dim_mat = dim_mat.view(1, 1, 1, -1)
        pos_mat = pos_mat.unsqueeze(-1) * 100.0
        mul_mat = (pos_mat * dim_mat).view(seq_len, seq_len, -1)
        embedding = torch.cat([mul_mat.sin(), mul_mat.cos()], dim=-1)
        return embedding.half()

    def forward(self, batch_size):
        return self.geometry_embedding.unsqueeze(0).expand(batch_size, -1, -1, -1)


class GeometryMultiHeadAttention(nn.Module):
    """Multi-head self-attention with TransZero-style geometry subtraction."""

    def __init__(self, dim_com, heads, dim_g=64, dropout=0.1):
        super().__init__()
        assert dim_com % heads == 0
        self.heads = heads
        self.d_k = dim_com // heads

        self.fc_q = nn.Linear(dim_com, dim_com)
        self.fc_k = nn.Linear(dim_com, dim_com)
        self.fc_v = nn.Linear(dim_com, dim_com)
        self.fc_o = nn.Linear(dim_com, dim_com)
        self.WGs = nn.ModuleList([nn.Linear(dim_g, 1, bias=True) for _ in range(heads)])
        self.ln = nn.LayerNorm(dim_com)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, geometry_emb):
        B, N, D = x.shape
        q = self.fc_q(x).view(B, N, self.heads, self.d_k).permute(0, 2, 1, 3)
        k = self.fc_k(x).view(B, N, self.heads, self.d_k).permute(0, 2, 1, 3)
        v = self.fc_v(x).view(B, N, self.heads, self.d_k).permute(0, 2, 1, 3)

        att = torch.matmul(q, k.transpose(-2, -1)) / (self.d_k ** 0.5)
        geo_flat = geometry_emb.float().reshape(-1, geometry_emb.shape[-1])
        geo_per_head = [
            layer(geo_flat).view(B, N, N, 1).permute(0, 3, 1, 2)
            for layer in self.WGs
        ]
        geo_weights = F.relu(torch.cat(geo_per_head, dim=1))
        att = F.softmax(att - geo_weights, dim=-1)
        att = self.dropout(att)
        out = torch.matmul(att, v).permute(0, 2, 1, 3).contiguous().view(B, N, D)
        return self.ln(x + self.fc_o(out))


class GeometryDecoupledEncoderLayer(nn.Module):
    """Geometry-decoupled visual encoder layer used by FGVD."""

    def __init__(self, dim_com, heads, dropout=0.1, dim_g=64):
        super().__init__()
        self.attn = GeometryMultiHeadAttention(dim_com, heads, dim_g, dropout)
        self.ffn = nn.Sequential(
            nn.Linear(dim_com, dim_com * 2),
            nn.ReLU(inplace=True),
            nn.Linear(dim_com * 2, dim_com),
        )
        self.ln = nn.LayerNorm(dim_com)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, geometry_emb):
        x = self.attn(x, geometry_emb)
        return self.ln(x + self.dropout(self.ffn(x)))


FAELayer = GeometryDecoupledEncoderLayer


class BidirectionalVisualSemanticAlignment(nn.Module):
    """Bidirectional Visual-Semantic Alignment (BVSA)."""

    def __init__(
        self,
        dim_f=768,
        dim_com=512,
        heads=4,
        dropout=0.1,
        weight_s2v=0.5,
        grid_size=(24, 24),
        dim_g=64,
        use_fgvd_geometry=True,
        use_fae=None,
    ):
        super().__init__()
        if use_fae is not None:
            use_fgvd_geometry = use_fae
        self.dim_f = dim_f
        self.dim_com = dim_com
        self.weight_s2v = weight_s2v
        self.use_fgvd_geometry = use_fgvd_geometry
        self.use_fae = self.use_fgvd_geometry

        self.embed_cv = nn.Linear(dim_f, dim_com)
        self.embed_text = nn.Linear(dim_f, dim_com)

        if self.use_fgvd_geometry:
            self.box_emb = BoxRelationalEmbedding(grid_size=grid_size, dim_g=dim_g)
            self.fae = GeometryDecoupledEncoderLayer(dim_com, heads, dropout, dim_g=dim_g)
        else:
            self.box_emb = None
            self.fae = None

        self.decoder_v2s = nn.TransformerDecoderLayer(
            d_model=dim_com,
            nhead=heads,
            dim_feedforward=dim_com * 2,
            dropout=dropout,
            batch_first=True,
        )
        self.decoder_s2v = nn.TransformerDecoderLayer(
            d_model=dim_com,
            nhead=heads,
            dim_feedforward=dim_com * 2,
            dropout=dropout,
            batch_first=True,
        )
        # Kept for v1 seed and checkpoint compatibility. The active add-mode
        # baseline does not read these projections, but the original v1 model
        # initialized them before SGMP/ICSA, so removing them changes
        # downstream random initialization under the same seed.
        self.proj_visual = nn.Linear(dim_com, dim_f)
        self.proj_text = nn.Linear(dim_com, dim_f)

    def geometry_for_indices(self, batch_size, token_indices=None, seq_len=None):
        if not self.use_fgvd_geometry or self.box_emb is None:
            return None
        if token_indices is None:
            if seq_len == self.box_emb.geometry_embedding.size(0):
                return self.box_emb(batch_size)
            return None

        K = token_indices.size(1)
        full = self.box_emb.geometry_embedding
        i_idx = token_indices.unsqueeze(-1).expand(-1, -1, K)
        j_idx = token_indices.unsqueeze(-2).expand(-1, K, -1)
        return full[i_idx, j_idx]

    def forward(
        self,
        patches,
        text,
        cls_token=None,
        fgvd_select_k=0,
        fgvd_select_sigma=0.0,
        fgvd_select_largest=True,
        fgvd_select_formula="v2_abs_mean",
        lastvit_select_k=None,
        lastvit_select_sigma=None,
        lastvit_select_largest=None,
        lastvit_select_formula=None,
    ):
        B = patches.size(0)
        topk_indices = None
        if lastvit_select_k is not None:
            fgvd_select_k = lastvit_select_k
        if lastvit_select_sigma is not None:
            fgvd_select_sigma = lastvit_select_sigma
        if lastvit_select_largest is not None:
            fgvd_select_largest = lastvit_select_largest
        if lastvit_select_formula is not None:
            fgvd_select_formula = lastvit_select_formula

        if fgvd_select_k > 0 and fgvd_select_k < patches.size(1):
            sigma_sel = fgvd_select_sigma if fgvd_select_sigma > 0 else None
            with _autocast_disabled(patches):
                topk_indices, _ = fgvd_select_patches(
                    patches.float(),
                    K=fgvd_select_k,
                    sigma=sigma_sel,
                    largest=fgvd_select_largest,
                    formula=fgvd_select_formula,
                )
            idx_exp = topk_indices.unsqueeze(-1).expand(-1, -1, patches.size(-1))
            patches = torch.gather(patches, dim=1, index=idx_exp)

        vis = self.embed_cv(patches)
        if self.use_fgvd_geometry:
            geometry_emb = self.geometry_for_indices(
                B, topk_indices, seq_len=patches.size(1)
            )
            if geometry_emb is not None:
                memory = self.fae(vis, geometry_emb)
            else:
                memory = vis
        else:
            memory = vis

        txt_com = self.embed_text(text)
        if txt_com.dim() == 2:
            txt_batch = txt_com.unsqueeze(0).expand(B, -1, -1)
        elif txt_com.dim() == 3:
            if txt_com.size(0) != B:
                raise ValueError(
                    "Batched BVSA text must have shape [B, C, D] with the same B "
                    f"as patches; got text batch {txt_com.size(0)} and patches batch {B}."
                )
            txt_batch = txt_com
        else:
            raise ValueError(
                "BVSA text must be [C, D] for shared class text or [B, C, D] "
                f"for sample-conditioned class text; got {tuple(text.shape)}."
            )

        F_p_v2s = self.decoder_v2s(tgt=txt_batch, memory=memory)
        F_p_s2v = self.decoder_s2v(tgt=memory, memory=txt_batch)

        v2s_n = F.normalize(F_p_v2s, dim=-1)
        txt_batch_n = F.normalize(txt_batch, dim=-1)
        score_v2s = (v2s_n * txt_batch_n).sum(dim=-1)

        s2v_pooled = F_p_s2v.mean(dim=1)
        s2v_n = F.normalize(s2v_pooled, dim=-1)
        txt_single = F.normalize(txt_com, dim=-1)
        if txt_single.dim() == 2:
            score_s2v = s2v_n @ txt_single.T
        else:
            score_s2v = torch.einsum("bd,bcd->bc", s2v_n, txt_single)

        local_score = self.weight_s2v * score_s2v + (1.0 - self.weight_s2v) * score_v2s
        return {
            "local_score": local_score,
            "score_s2v": score_s2v,
            "score_v2s": score_v2s,
            "fgvd_selected_patches": patches,
            "fgvd_selected_indices": topk_indices,
            "fgvd_patch_z": vis,
            "fgvd_memory": memory,
            "jepa_selected_patches": patches,
            "jepa_selected_indices": topk_indices,
            "jepa_patch_z": vis,
            "jepa_memory": memory,
        }


CrossModalTransformer = BidirectionalVisualSemanticAlignment
CLIPASelfAdapter = ProgressiveSemanticSelfAttention


class GTPJ(nn.Module):
    """GTPJ framework with PSE, ICSA, FGVD, BVSA, and SGMP."""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        class_attr=None,
        attr_text_embeds=None,
        seen_sentence_embeds=None,
        unseen_sentence_embeds=None,
    ):
        super().__init__()
        self.config = config
        self.nclass = int(config.num_class)
        self.dim_f = int(config.dim_f_clip)
        self._validate_baseline_scope(config)

        self.register_buffer(
            "seenclass", torch.as_tensor(seenclass, dtype=torch.long), persistent=False
        )
        self.register_buffer(
            "unseenclass", torch.as_tensor(unseenclass, dtype=torch.long), persistent=False
        )

        self.seen_text_embeds = nn.Parameter(
            F.normalize(seen_text_embeds, dim=1), requires_grad=False
        )
        self.unseen_text_embeds = nn.Parameter(
            F.normalize(unseen_text_embeds, dim=1), requires_grad=False
        )

        self.adapter_ratio = float(_config_get(config, "pse_adapter_ratio", "adapter_ratio", 0.2))
        self.pse_adapter_ratio = self.adapter_ratio
        self.use_clip_a_self = bool(
            _config_get(config, "use_pse_self_attention", "use_clip_a_self", False)
        )
        self.use_pse_self_attention = self.use_clip_a_self
        self.clip_a_self_apply_unseen = bool(
            _config_get(config, "pse_apply_unseen", "clip_a_self_apply_unseen", False)
        )
        self.pse_apply_unseen = self.clip_a_self_apply_unseen
        self.clip_a_self_outer_ratio = float(
            _config_get(config, "pse_outer_ratio", "clip_a_self_outer_ratio", self.adapter_ratio)
        )
        self.pse_outer_ratio = self.clip_a_self_outer_ratio
        if self.use_clip_a_self:
            if seen_sentence_embeds is None:
                raise ValueError("use_pse_self_attention=True requires seen_sentence_embeds.")
            if seen_sentence_embeds.dim() != 3 or seen_sentence_embeds.size(-1) != self.dim_f:
                raise ValueError("seen_sentence_embeds must have shape [C_seen, M, D].")
            self.seen_sentence_embeds = nn.Parameter(
                F.normalize(seen_sentence_embeds, dim=-1), requires_grad=False
            )
            if unseen_sentence_embeds is not None:
                if unseen_sentence_embeds.dim() != 3 or unseen_sentence_embeds.size(-1) != self.dim_f:
                    raise ValueError("unseen_sentence_embeds must have shape [C_unseen, M, D].")
                self.unseen_sentence_embeds = nn.Parameter(
                    F.normalize(unseen_sentence_embeds, dim=-1), requires_grad=False
                )
            else:
                self.unseen_sentence_embeds = None
            self.clip_a_self_adapter = ProgressiveSemanticSelfAttention(
                dim=self.dim_f,
                heads=int(_config_get(config, "pse_heads", "clip_a_self_heads", 1)),
                dropout=float(_config_get(config, "pse_dropout", "clip_a_self_dropout", 0.5)),
                inner_ratio=float(
                    _config_get(config, "pse_inner_ratio", "clip_a_self_inner_ratio", 0.5)
                ),
            )
        else:
            self.text_adapter = SemanticPrototypeAdapter(self.dim_f, reduction=4)

        tf_common_dim = int(getattr(config, "tf_common_dim", 512))
        tf_heads = int(getattr(config, "tf_heads", 4))
        tf_dropout = float(getattr(config, "tf_dropout", 0.1))
        weight_s2v = float(getattr(config, "weight_s2v", 0.5))
        use_fgvd_geometry = bool(_config_get(config, "use_fgvd_geometry", "use_fae", True))
        self.local_weight = float(getattr(config, "local_weight", 0.3))
        self.score_mode = str(getattr(config, "score_mode", "add"))

        self.cross_tf = BidirectionalVisualSemanticAlignment(
            dim_f=self.dim_f,
            dim_com=tf_common_dim,
            heads=tf_heads,
            dropout=tf_dropout,
            weight_s2v=weight_s2v,
            grid_size=(24, 24),
            dim_g=64,
            use_fgvd_geometry=use_fgvd_geometry,
        )

        self.use_sgmp = bool(_config_get(config, "use_sgmp", "use_ag_jepa", False))
        self.use_ag_jepa = self.use_sgmp
        context_aliases = {
            "embed": "embed",
            "fae_memory": "fgvd_memory",
            "fgvd_memory": "fgvd_memory",
            "fae_main_memory": "fgvd_main_memory",
            "fgvd_main_memory": "fgvd_main_memory",
        }
        raw_context_mode = str(
            _config_get(config, "sgmp_context_mode", "jepa_context_mode", "embed")
        ).lower()
        self.sgmp_context_mode = context_aliases.get(raw_context_mode, raw_context_mode)
        self.jepa_context_mode = self.sgmp_context_mode
        if self.sgmp_context_mode not in {"embed", "fgvd_memory", "fgvd_main_memory"}:
            raise ValueError(
                "sgmp_context_mode must be 'embed', 'fgvd_memory', or 'fgvd_main_memory', "
                f"got {raw_context_mode!r}."
            )
        if self.sgmp_context_mode in {"fgvd_memory", "fgvd_main_memory"} and not use_fgvd_geometry:
            raise ValueError(
                f"sgmp_context_mode={self.sgmp_context_mode!r} requires use_fgvd_geometry=True."
            )
        self.sgmp_topk = int(_config_get(config, "sgmp_topk", "jepa_topk", 8))
        self.jepa_topk = self.sgmp_topk
        self.sgmp_neg_margin = float(_config_get(config, "sgmp_neg_margin", "jepa_neg_margin", 0.2))
        self.jepa_neg_margin = self.sgmp_neg_margin
        if self.use_sgmp:
            sgmp_hidden = int(_config_get(config, "sgmp_hidden", "jepa_hidden", tf_common_dim))
            self.jepa_predictor = nn.Sequential(
                nn.Linear(tf_common_dim * 2, sgmp_hidden),
                nn.LayerNorm(sgmp_hidden),
                nn.GELU(),
                nn.Linear(sgmp_hidden, tf_common_dim),
            )

        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
        # Checkpoint compatibility only. v1 uses fixed add scoring and does not
        # read CIG gates, but old v1 checkpoints contain these parameter keys.
        self.gate_alpha = nn.Parameter(torch.tensor(1.0))
        self.gate_tau = nn.Parameter(torch.tensor(1.0))

        self.fgvd_select_k = int(_config_get(config, "fgvd_select_k", "lastvit_select_k", 0))
        self.lastvit_select_k = self.fgvd_select_k
        self.fgvd_select_sigma = float(
            _config_get(config, "fgvd_select_sigma", "lastvit_select_sigma", 0.0)
        )
        self.lastvit_select_sigma = self.fgvd_select_sigma
        largest_raw = _config_get(config, "fgvd_select_largest", "lastvit_select_largest", True)
        if isinstance(largest_raw, str) and largest_raw.lower() == "both":
            self.fgvd_select_largest = "both"
        else:
            self.fgvd_select_largest = bool(largest_raw)
        self.lastvit_select_largest = self.fgvd_select_largest
        self.fgvd_select_formula = str(
            _config_get(config, "fgvd_select_formula", "lastvit_select_formula", "v2_abs_mean")
        )
        self.lastvit_select_formula = self.fgvd_select_formula

        self.use_conditional_text = bool(_config_get(config, "use_icsa", "use_conditional_text", False))
        self.use_icsa = self.use_conditional_text
        if self.use_conditional_text:
            meta_hidden = int(_config_get(config, "icsa_hidden", "meta_net_hidden", 48))
            self.meta_net = nn.Sequential(
                nn.Linear(self.dim_f, meta_hidden),
                nn.LayerNorm(meta_hidden),
                nn.GELU(),
                nn.Linear(meta_hidden, self.dim_f),
            )
            with torch.no_grad():
                self.meta_net[-1].weight.zero_()
                self.meta_net[-1].bias.zero_()
            self.cond_text_ratio = float(_config_get(config, "icsa_ratio", "conditional_text_ratio", 0.05))
            self.icsa_ratio = self.cond_text_ratio
        else:
            self.cond_text_ratio = 0.0
            self.icsa_ratio = 0.0
        self.bvsa_text_mode = str(getattr(config, "bvsa_text_mode", "adapted")).lower()
        if self.bvsa_text_mode not in {"adapted", "conditional"}:
            raise ValueError(
                "bvsa_text_mode must be 'adapted' or 'conditional', "
                f"got {self.bvsa_text_mode!r}."
            )
        if self.bvsa_text_mode == "conditional":
            if not self.use_conditional_text:
                raise ValueError("bvsa_text_mode='conditional' requires use_icsa=True.")
            if self.cond_text_ratio <= 0:
                raise ValueError("bvsa_text_mode='conditional' requires icsa_ratio > 0.")
        self.sgmp_text_mode = str(
            _config_get(config, "sgmp_text_mode", "jepa_text_mode", "adapted")
        ).lower()
        self.jepa_text_mode = self.sgmp_text_mode
        if self.sgmp_text_mode not in {"adapted", "conditional"}:
            raise ValueError(
                "sgmp_text_mode must be 'adapted' or 'conditional', "
                f"got {self.sgmp_text_mode!r}."
            )
        if self.sgmp_text_mode == "conditional":
            if not self.use_conditional_text:
                raise ValueError("sgmp_text_mode='conditional' requires use_icsa=True.")
            if self.cond_text_ratio <= 0:
                raise ValueError("sgmp_text_mode='conditional' requires icsa_ratio > 0.")

    @property
    def bvsa(self):
        return self.cross_tf

    @property
    def semantic_prototype_adapter(self):
        return self.text_adapter

    @property
    def semantic_prototype_self_attention(self):
        return self.clip_a_self_adapter

    @property
    def image_conditioned_semantic_adapter(self):
        return self.meta_net

    @property
    def sgmp_predictor(self):
        return self.jepa_predictor

    @staticmethod
    def _float_config(config, key, default=0.0):
        return float(getattr(config, key, default))

    @classmethod
    def _validate_baseline_scope(cls, config):
        mode_defaults = {
            "model_mode": "gtpj",
            "score_mode": "add",
            "pool_method": "mean",
            "gating": "fixed",
            "gating_dynamic": "fixed",
            "weight_s2v_mode": "fixed",
            "pool_dynamic": "fixed",
            "residual_mode": "fixed",
            "cosine_base_blend_mode": "fixed",
        }
        for key, expected in mode_defaults.items():
            if hasattr(config, key) and str(getattr(config, key)) != expected:
                raise ValueError(
                    f"MyModel.py is baseline-only; unsupported {key}={getattr(config, key)!r}."
                )

        unsupported_switches = [
            "use_lastvit_cls",
            "use_geo_attr_routing",
            "use_attr_patch_ot",
            "use_text_attr_reservoir",
            "use_ag_jepa_v2",
            "use_uncertainty_msdn_gate",
            "use_cf_neg_text",
        ]
        for key in unsupported_switches:
            if bool(getattr(config, key, False)):
                raise ValueError(f"MyModel.py is baseline-only; unsupported switch {key}=True.")

        unsupported_weights = [
            "lambda_cal",
            "lambda_l2sp",
            "lambda_v_anchor",
            "lambda_t_unseen_anchor",
            "lambda_distill",
            "lambda_aux_s2v",
            "lambda_aux_v2s",
            "lambda_cf_neg_text",
            "lambda_geo_attr_routing",
            "lambda_attr_patch_ot",
            "lambda_bias",
        ]
        for key in unsupported_weights:
            if cls._float_config(config, key, 0.0) != 0.0:
                raise ValueError(f"MyModel.py is baseline-only; unsupported loss weight {key}.")

    def get_adapted_seen_text(self):
        if self.use_clip_a_self:
            sentence_embeds = self.seen_sentence_embeds
            base = sentence_embeds.mean(dim=1)
            attn = self.semantic_prototype_self_attention(sentence_embeds).mean(dim=1)
            ratio = self.clip_a_self_outer_ratio
            adapted = ratio * attn + (1.0 - ratio) * base
            return F.normalize(adapted, dim=1)
        x = self.seen_text_embeds
        adapted = self.adapter_ratio * self.semantic_prototype_adapter(x) + (1.0 - self.adapter_ratio) * x
        return F.normalize(adapted, dim=1)

    def get_adapted_unseen_text(self):
        if (
            self.use_clip_a_self
            and self.clip_a_self_apply_unseen
            and self.unseen_sentence_embeds is not None
        ):
            sentence_embeds = self.unseen_sentence_embeds
            base = sentence_embeds.mean(dim=1)
            attn = self.semantic_prototype_self_attention(sentence_embeds).mean(dim=1)
            ratio = self.clip_a_self_outer_ratio
            return F.normalize(ratio * attn + (1.0 - ratio) * base, dim=1)
        return self.unseen_text_embeds

    def _make_all_text(self, device, dtype):
        seen_text = self.get_adapted_seen_text().to(device=device, dtype=dtype)
        unseen_text = self.get_adapted_unseen_text().to(device=device, dtype=dtype)
        all_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        all_text[self.seenclass.to(device)] = seen_text
        all_text[self.unseenclass.to(device)] = unseen_text
        return all_text

    def _topology_pearson_loss(self, enh_text=None):
        if enh_text is None:
            adapted_seen = self.get_adapted_seen_text()
            device = adapted_seen.device
            dtype = adapted_seen.dtype
        else:
            device = enh_text.device
            dtype = enh_text.dtype

        base_text = torch.zeros(self.nclass, self.dim_f, device=device, dtype=dtype)
        seen_idx = self.seenclass.to(device)
        unseen_idx = self.unseenclass.to(device)
        base_text[seen_idx] = self.seen_text_embeds.to(device=device, dtype=dtype)
        base_text[unseen_idx] = self.unseen_text_embeds.to(device=device, dtype=dtype)

        if enh_text is None:
            enh_text = torch.zeros_like(base_text)
            enh_text[seen_idx] = adapted_seen.to(device=device, dtype=dtype)
            enh_text[unseen_idx] = base_text[unseen_idx]

        base_text = F.normalize(base_text.float(), dim=-1)
        enh_text = F.normalize(enh_text.float(), dim=-1)
        base_sim = base_text @ base_text.T
        if enh_text.dim() == 2:
            enh_sim = enh_text @ enh_text.T
        else:
            enh_sim = torch.matmul(enh_text, enh_text.transpose(-1, -2))

        off_diag = ~torch.eye(self.nclass, dtype=torch.bool, device=device)
        base_vec = base_sim.detach()[off_diag]
        if enh_sim.dim() == 2:
            enh_vec = enh_sim[off_diag].unsqueeze(0)
        else:
            enh_vec = enh_sim[:, off_diag]
        base_vec = base_vec.unsqueeze(0).expand_as(enh_vec)

        enh_centered = enh_vec - enh_vec.mean(dim=1, keepdim=True)
        base_centered = base_vec - base_vec.mean(dim=1, keepdim=True)
        numerator = (enh_centered * base_centered).sum(dim=1)
        denominator = (
            torch.sqrt((enh_centered ** 2).sum(dim=1) + 1e-8)
            * torch.sqrt((base_centered ** 2).sum(dim=1) + 1e-8)
        )
        return (1.0 - numerator / denominator).mean()

    def _semantic_guided_masked_prediction_loss(
        self,
        patches,
        all_text,
        labels,
        selected_patches=None,
        selected_indices=None,
        selected_patch_z=None,
        selected_memory=None,
        all_text_cond=None,
    ):
        device = patches.device
        if (not self.use_sgmp) or patches is None or all_text is None:
            zero = torch.tensor(0.0, device=device if patches is not None else labels.device)
            return zero, zero

        if self.sgmp_context_mode in {"fgvd_memory", "fgvd_main_memory"}:
            if selected_patches is None or selected_patch_z is None:
                raise ValueError("SGMP with FGVD memory requires selected patches and patch_z.")
            sgmp_patches = selected_patches
        else:
            sgmp_patches = patches
            selected_patch_z = None

        B, N, _ = sgmp_patches.shape
        if N < 2:
            zero = torch.tensor(0.0, device=device)
            return zero, zero
        k = max(1, min(int(self.sgmp_topk), N - 1))
        labels = labels.to(device=device, dtype=torch.long)
        batch_idx = torch.arange(B, device=device)
        if self.sgmp_text_mode == "conditional":
            if all_text_cond is None:
                raise ValueError("sgmp_text_mode='conditional' requires all_text_cond from GTPJ.forward.")
            class_text = all_text_cond[batch_idx, labels].to(device=device, dtype=sgmp_patches.dtype)
        else:
            class_text = all_text[labels].to(device=device, dtype=sgmp_patches.dtype)

        with torch.no_grad():
            patch_n = F.normalize(sgmp_patches.float(), dim=-1)
            text_n = F.normalize(class_text.float(), dim=-1)
            patch_score = torch.einsum("bnd,bd->bn", patch_n, text_n)
            _, masked_idx = torch.topk(patch_score, k=k, dim=1, largest=True)

        mask = torch.zeros(B, N, dtype=torch.bool, device=device)
        mask.scatter_(1, masked_idx, True)
        keep = ~mask

        if self.sgmp_context_mode == "fgvd_memory":
            patch_z = selected_patch_z
            context = self._sgmp_fgvd_context(patch_z, keep, selected_indices)
        elif self.sgmp_context_mode == "fgvd_main_memory":
            if selected_memory is None:
                raise ValueError("fgvd_main_memory SGMP requires main-path FGVD memory.")
            patch_z = selected_patch_z
            keep_f = keep.unsqueeze(-1).to(selected_memory.dtype)
            context = (selected_memory * keep_f).sum(dim=1) / keep_f.sum(dim=1).clamp_min(1.0)
        else:
            patch_z = self.bvsa.embed_cv(sgmp_patches)
            keep_f = keep.unsqueeze(-1).to(patch_z.dtype)
            context = (patch_z * keep_f).sum(dim=1) / keep_f.sum(dim=1).clamp_min(1.0)

        target = patch_z[mask].view(B, k, -1).mean(dim=1).detach()

        text_z = self.bvsa.embed_text(class_text)
        pred = self.sgmp_predictor(torch.cat([context, text_z], dim=-1))
        pos_sim = F.cosine_similarity(pred, target, dim=-1)
        loss_mpp = (1.0 - pos_sim).mean()

        seen = self.seenclass.to(device)
        label_map = torch.full((self.nclass,), -1, device=device, dtype=torch.long)
        label_map[seen] = torch.arange(seen.numel(), device=device)
        local_labels = label_map[labels]
        if (local_labels < 0).any():
            raise ValueError("SGMP expects global labels from seen classes.")
        neg_local = (local_labels + 1) % seen.numel()
        neg_labels = seen[neg_local]
        if self.sgmp_text_mode == "conditional":
            neg_text = all_text_cond[batch_idx, neg_labels].to(device=device, dtype=sgmp_patches.dtype)
        else:
            neg_text = all_text[neg_labels].to(device=device, dtype=sgmp_patches.dtype)

        neg_text_z = self.bvsa.embed_text(neg_text)
        pred_neg = self.sgmp_predictor(torch.cat([context.detach(), neg_text_z], dim=-1))
        neg_sim = F.cosine_similarity(pred_neg, target, dim=-1)
        loss_neg = F.relu(neg_sim - pos_sim.detach() + self.sgmp_neg_margin).mean()
        return loss_mpp, loss_neg

    def _sgmp_fgvd_context(self, patch_z, keep, selected_indices):
        B, N, D = patch_z.shape
        keep_count = int(keep[0].sum().item())
        if keep_count <= 0:
            raise ValueError("SGMP fgvd_memory mode requires at least one keep patch.")

        token_range = torch.arange(N, device=patch_z.device).unsqueeze(0).expand(B, -1)
        keep_idx = token_range[keep].view(B, keep_count)
        idx_exp = keep_idx.unsqueeze(-1).expand(-1, -1, D)
        patch_z_keep = torch.gather(patch_z, dim=1, index=idx_exp)

        if selected_indices is None:
            full_len = self.bvsa.box_emb.geometry_embedding.size(0)
            if N != full_len:
                raise ValueError(
                    "SGMP fgvd_memory needs selected patch indices when patch count "
                    f"is {N}, not the full geometry length {full_len}."
                )
            selected_indices = token_range
        else:
            selected_indices = selected_indices.to(device=patch_z.device)

        keep_orig_idx = torch.gather(selected_indices, dim=1, index=keep_idx)
        geometry_emb = self.bvsa.geometry_for_indices(
            B, keep_orig_idx, seq_len=keep_count
        )
        if geometry_emb is None:
            raise ValueError("SGMP fgvd_memory could not build keep-token geometry.")

        memory_keep = self.bvsa.fae(patch_z_keep, geometry_emb)
        return memory_keep.mean(dim=1)

    def _ag_jepa_loss(self, *args, **kwargs):
        return self._semantic_guided_masked_prediction_loss(*args, **kwargs)

    def _ag_jepa_fae_context(self, *args, **kwargs):
        return self._sgmp_fgvd_context(*args, **kwargs)

    def _prepare_patches(self, clip_features):
        if clip_features.dim() == 3:
            if clip_features.size(1) == 577:
                return clip_features[:, 1:, :]
            if clip_features.size(1) == 576:
                return clip_features
            if clip_features.size(1) == 1:
                return clip_features.expand(-1, 576, -1)
        return clip_features.unsqueeze(1).expand(-1, 576, -1)

    def forward(self, clip_features, is_train=False):
        if clip_features.dim() == 3 and clip_features.size(1) == 577:
            cls_token = clip_features[:, 0, :]
            patches = clip_features[:, 1:, :]
        else:
            patches = self._prepare_patches(clip_features)
            cls_token = None

        logit_scale = torch.clamp(self.logit_scale.exp(), max=100.0)
        all_text = self._make_all_text(patches.device, patches.dtype)
        all_text_cond = None

        if cls_token is not None:
            vis_n = F.normalize(cls_token, dim=1)
        else:
            vis_n = F.normalize(patches.mean(dim=1), dim=1)

        if self.use_conditional_text and cls_token is not None and self.cond_text_ratio > 0:
            pi_x = F.normalize(self.image_conditioned_semantic_adapter(cls_token), dim=-1)
            all_text_cond = all_text.unsqueeze(0).expand(cls_token.size(0), -1, -1).clone()
            seen_idx = self.seenclass.to(patches.device)
            all_text_cond[:, seen_idx, :] = (
                all_text[seen_idx].unsqueeze(0) + self.cond_text_ratio * pi_x.unsqueeze(1)
            )
            text_n_cond = F.normalize(all_text_cond, dim=-1)
            s_global = (vis_n.unsqueeze(1) * text_n_cond).sum(dim=-1) * logit_scale
        else:
            text_n = F.normalize(all_text, dim=1)
            s_global = vis_n @ text_n.T * logit_scale

        bvsa_text = all_text
        if self.bvsa_text_mode == "conditional":
            if all_text_cond is None:
                raise ValueError(
                    "bvsa_text_mode='conditional' requires all_text_cond from GTPJ.forward."
                )
            bvsa_text = all_text_cond

        bvsa_out = self.bvsa(
            patches,
            bvsa_text,
            cls_token,
            fgvd_select_k=self.fgvd_select_k,
            fgvd_select_sigma=self.fgvd_select_sigma,
            fgvd_select_largest=self.fgvd_select_largest,
            fgvd_select_formula=self.fgvd_select_formula,
        )
        s_local = bvsa_out["local_score"]
        s_final = s_global + self.local_weight * s_local

        if is_train:
            logits = s_final[:, self.seenclass.to(s_final.device)]
        else:
            logits = s_final

        return {
            "logits": logits,
            "logits_200": s_final,
            "s_final": s_final,
            "base_logits": s_global,
            "s_global": s_global,
            "local_score": s_local,
            "s_local": s_local,
            "text_topology_features": None,
            "clip_S_pp": logits,
            "clip_pred": logits,
            "score_s2v": bvsa_out["score_s2v"],
            "score_v2s": bvsa_out["score_v2s"],
            "sgmp_patches": patches,
            "sgmp_selected_patches": bvsa_out["fgvd_selected_patches"],
            "sgmp_selected_indices": bvsa_out["fgvd_selected_indices"],
            "sgmp_patch_z": bvsa_out["fgvd_patch_z"],
            "sgmp_memory": bvsa_out["fgvd_memory"],
            "jepa_patches": patches,
            "jepa_selected_patches": bvsa_out["jepa_selected_patches"],
            "jepa_selected_indices": bvsa_out["jepa_selected_indices"],
            "jepa_patch_z": bvsa_out["jepa_patch_z"],
            "jepa_memory": bvsa_out["jepa_memory"],
            "all_text": all_text,
            "all_text_cond": all_text_cond,
        }

    def _global_to_seen_labels(self, labels):
        labels = labels.to(device=self.seenclass.device, dtype=torch.long)
        label_map = torch.full(
            (self.nclass,), -1, device=self.seenclass.device, dtype=torch.long
        )
        label_map[self.seenclass] = torch.arange(
            self.seenclass.numel(), device=self.seenclass.device
        )
        seen_labels = label_map[labels]
        if (seen_labels < 0).any():
            raise ValueError("Training labels must be global ids from seen classes.")
        return seen_labels

    def compute_loss(self, in_package):
        logits = in_package["logits"]
        labels = in_package["batch_label"]
        if labels.dim() > 1:
            labels = torch.argmax(labels, dim=1)
        labels = labels.to(device=logits.device, dtype=torch.long)
        seen_labels = self._global_to_seen_labels(labels).to(logits.device)

        loss_CE = F.cross_entropy(logits, seen_labels)
        loss = loss_CE

        base_logits = in_package.get("s_global", in_package.get("base_logits"))
        local_score = in_package.get("s_local", in_package.get("local_score"))
        loss_consist = torch.tensor(0.0, device=logits.device)
        lambda_consist = float(getattr(self.config, "lambda_consist", 0.0))
        if base_logits is not None and local_score is not None and lambda_consist > 0:
            T = float(getattr(self.config, "consist_temp", 2.0))
            seen_idx = self.seenclass.to(logits.device)
            base_seen = base_logits[:, seen_idx].detach()
            local_seen = local_score[:, seen_idx]
            base_p = F.softmax(base_seen / T, dim=-1)
            local_logp = F.log_softmax(local_seen / T, dim=-1)
            loss_consist = F.kl_div(local_logp, base_p, reduction="batchmean") * (T * T)
            if bool(getattr(self.config, "consist_dynamic", False)):
                gamma = float(getattr(self.config, "consist_dynamic_gamma", 0.1))
                with torch.no_grad():
                    scale = 1.0 / (1.0 + gamma * loss_consist.detach())
                loss = loss + (lambda_consist * scale) * loss_consist
            else:
                loss = loss + lambda_consist * loss_consist

        loss_topo = torch.tensor(0.0, device=logits.device)
        lambda_topo = float(getattr(self.config, "lambda_topo_pearson", 0.0))
        if lambda_topo > 0:
            loss_topo = self._topology_pearson_loss(
                in_package.get("text_topology_features")
            )
            loss = loss + lambda_topo * loss_topo

        loss_mpp = torch.tensor(0.0, device=logits.device)
        loss_neg = torch.tensor(0.0, device=logits.device)
        lambda_mpp = float(_config_get(self.config, "lambda_mpp", "lambda_jepa", 0.0))
        lambda_neg = float(_config_get(self.config, "lambda_neg", "lambda_jepa_neg", 0.0))
        if self.use_sgmp and (lambda_mpp > 0 or lambda_neg > 0):
            sgmp_patches = in_package.get("sgmp_patches", in_package.get("jepa_patches"))
            all_text_sgmp = in_package.get("all_text")
            if sgmp_patches is not None and all_text_sgmp is not None:
                loss_mpp, loss_neg = self._semantic_guided_masked_prediction_loss(
                    sgmp_patches,
                    all_text_sgmp,
                    labels,
                    selected_patches=in_package.get(
                        "sgmp_selected_patches", in_package.get("jepa_selected_patches")
                    ),
                    selected_indices=in_package.get(
                        "sgmp_selected_indices", in_package.get("jepa_selected_indices")
                    ),
                    selected_patch_z=in_package.get("sgmp_patch_z", in_package.get("jepa_patch_z")),
                    selected_memory=in_package.get("sgmp_memory", in_package.get("jepa_memory")),
                    all_text_cond=in_package.get("all_text_cond"),
                )
                loss = loss + lambda_mpp * loss_mpp
                loss = loss + lambda_neg * loss_neg

        score_s2v = in_package.get("score_s2v")
        score_v2s = in_package.get("score_v2s")
        loss_bmdd = torch.tensor(0.0, device=logits.device)
        loss_msdn_gate = torch.tensor(1.0, device=logits.device)
        lambda_bmdd = float(_config_get(self.config, "lambda_bmdd", "lambda_msdn", 0.0))
        if lambda_bmdd > 0 and score_s2v is not None and score_v2s is not None:
            T_msdn = float(getattr(self.config, "msdn_temp", 2.0))
            seen_idx = self.seenclass.to(logits.device)
            s2v_seen = score_s2v[:, seen_idx] / T_msdn
            v2s_seen = score_v2s[:, seen_idx] / T_msdn
            p_s2v = F.softmax(s2v_seen, dim=-1)
            p_v2s = F.softmax(v2s_seen, dim=-1)
            log_p_s2v = F.log_softmax(s2v_seen, dim=-1)
            log_p_v2s = F.log_softmax(v2s_seen, dim=-1)
            kl_s2v_to_v2s = F.kl_div(log_p_v2s, p_s2v.detach(), reduction="batchmean")
            kl_v2s_to_s2v = F.kl_div(log_p_s2v, p_v2s.detach(), reduction="batchmean")
            loss_bmdd = (T_msdn * T_msdn / 2.0) * (kl_s2v_to_v2s + kl_v2s_to_s2v)
            loss = loss + lambda_bmdd * loss_bmdd

        return {
            "loss": loss,
            "loss_CE": loss_CE,
            "loss_ce": loss_CE,
            "loss_consist": loss_consist,
            "loss_cons": loss_consist,
            "loss_topo": loss_topo,
            "loss_bmdd": loss_bmdd,
            "loss_msdn": loss_bmdd,
            "loss_msdn_gate": loss_msdn_gate,
            "loss_mpp": loss_mpp,
            "loss_neg": loss_neg,
            "loss_jepa": loss_mpp,
            "loss_jepa_neg": loss_neg,
        }
