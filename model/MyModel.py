"""
GTPJ v1 baseline model.

This file intentionally keeps only the active baseline path used by
``config/versions/v1.yaml``:

- CLIP text adapter
- FAE geometry-aware patch memory
- LaSt patch selection before FAE
- fixed add scoring: base logits + local_weight * local_score
- conditional seen-class text residual
- CE, consistency, topology, MSDN, and AG-JEPA losses

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


def lastvit_select_patches(F_p, K=64, sigma=None, largest=True, formula="v2_abs_mean"):
    """Select top-K patches with LaSt-ViT frequency saliency."""
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


class Adapter(nn.Module):
    """Bottleneck text adapter for seen-class semantic features."""

    def __init__(self, c_in, reduction=4):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(c_in, c_in // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(c_in // reduction, c_in, bias=False),
        )

    def forward(self, x):
        return self.fc(x)


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


class FAELayer(nn.Module):
    """Single Feature Augmentation Encoder layer."""

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


class CrossModalTransformer(nn.Module):
    """Bidirectional visual-semantic transformer used by the v1 baseline."""

    def __init__(
        self,
        dim_f=768,
        dim_com=512,
        heads=4,
        dropout=0.1,
        weight_s2v=0.5,
        grid_size=(24, 24),
        dim_g=64,
        use_fae=True,
    ):
        super().__init__()
        self.dim_f = dim_f
        self.dim_com = dim_com
        self.weight_s2v = weight_s2v
        self.use_fae = use_fae

        self.embed_cv = nn.Linear(dim_f, dim_com)
        self.embed_text = nn.Linear(dim_f, dim_com)

        if self.use_fae:
            self.box_emb = BoxRelationalEmbedding(grid_size=grid_size, dim_g=dim_g)
            self.fae = FAELayer(dim_com, heads, dropout, dim_g=dim_g)
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
        # initialized them before AG-JEPA/meta_net, so removing them changes
        # downstream random initialization under the same seed.
        self.proj_visual = nn.Linear(dim_com, dim_f)
        self.proj_text = nn.Linear(dim_com, dim_f)

    def forward(
        self,
        patches,
        text,
        cls_token=None,
        lastvit_select_k=0,
        lastvit_select_sigma=0.0,
        lastvit_select_largest=True,
        lastvit_select_formula="v2_abs_mean",
    ):
        B = patches.size(0)
        topk_indices = None

        if lastvit_select_k > 0 and lastvit_select_k < patches.size(1):
            sigma_sel = lastvit_select_sigma if lastvit_select_sigma > 0 else None
            with _autocast_disabled(patches):
                topk_indices, _ = lastvit_select_patches(
                    patches.float(),
                    K=lastvit_select_k,
                    sigma=sigma_sel,
                    largest=lastvit_select_largest,
                    formula=lastvit_select_formula,
                )
            idx_exp = topk_indices.unsqueeze(-1).expand(-1, -1, patches.size(-1))
            patches = torch.gather(patches, dim=1, index=idx_exp)

        vis = self.embed_cv(patches)
        if self.use_fae:
            if patches.size(1) == 576:
                memory = self.fae(vis, self.box_emb(B))
            elif topk_indices is not None:
                full = self.box_emb.geometry_embedding
                K_sel = topk_indices.size(1)
                i_idx = topk_indices.unsqueeze(-1).expand(-1, -1, K_sel)
                j_idx = topk_indices.unsqueeze(-2).expand(-1, K_sel, -1)
                memory = self.fae(vis, full[i_idx, j_idx])
            else:
                memory = vis
        else:
            memory = vis

        txt_com = self.embed_text(text)
        txt_batch = txt_com.unsqueeze(0).expand(B, -1, -1)

        F_p_v2s = self.decoder_v2s(tgt=txt_batch, memory=memory)
        F_p_s2v = self.decoder_s2v(tgt=memory, memory=txt_batch)

        v2s_n = F.normalize(F_p_v2s, dim=-1)
        txt_batch_n = F.normalize(txt_batch, dim=-1)
        score_v2s = (v2s_n * txt_batch_n).sum(dim=-1)

        s2v_pooled = F_p_s2v.mean(dim=1)
        s2v_n = F.normalize(s2v_pooled, dim=-1)
        txt_single = F.normalize(txt_com, dim=-1)
        score_s2v = s2v_n @ txt_single.T

        local_score = self.weight_s2v * score_s2v + (1.0 - self.weight_s2v) * score_v2s
        return {
            "local_score": local_score,
            "score_s2v": score_s2v,
            "score_v2s": score_v2s,
        }


class GTPJ(nn.Module):
    """GTPJ v1 baseline."""

    def __init__(
        self,
        config,
        seenclass,
        unseenclass,
        seen_text_embeds,
        unseen_text_embeds,
        class_attr=None,
        attr_text_embeds=None,
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

        self.adapter_ratio = float(getattr(config, "adapter_ratio", 0.2))
        self.text_adapter = Adapter(self.dim_f, reduction=4)

        tf_common_dim = int(getattr(config, "tf_common_dim", 512))
        tf_heads = int(getattr(config, "tf_heads", 4))
        tf_dropout = float(getattr(config, "tf_dropout", 0.1))
        weight_s2v = float(getattr(config, "weight_s2v", 0.5))
        use_fae = bool(getattr(config, "use_fae", True))
        self.local_weight = float(getattr(config, "local_weight", 0.3))
        self.score_mode = str(getattr(config, "score_mode", "add"))

        self.cross_tf = CrossModalTransformer(
            dim_f=self.dim_f,
            dim_com=tf_common_dim,
            heads=tf_heads,
            dropout=tf_dropout,
            weight_s2v=weight_s2v,
            grid_size=(24, 24),
            dim_g=64,
            use_fae=use_fae,
        )

        self.use_ag_jepa = bool(getattr(config, "use_ag_jepa", False))
        self.jepa_topk = int(getattr(config, "jepa_topk", 8))
        self.jepa_neg_margin = float(getattr(config, "jepa_neg_margin", 0.2))
        if self.use_ag_jepa:
            jepa_hidden = int(getattr(config, "jepa_hidden", tf_common_dim))
            self.jepa_predictor = nn.Sequential(
                nn.Linear(tf_common_dim * 2, jepa_hidden),
                nn.LayerNorm(jepa_hidden),
                nn.GELU(),
                nn.Linear(jepa_hidden, tf_common_dim),
            )

        self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / 0.07))
        # Checkpoint compatibility only. v1 uses fixed add scoring and does not
        # read CIG gates, but old v1 checkpoints contain these parameter keys.
        self.gate_alpha = nn.Parameter(torch.tensor(1.0))
        self.gate_tau = nn.Parameter(torch.tensor(1.0))

        self.lastvit_select_k = int(getattr(config, "lastvit_select_k", 0))
        self.lastvit_select_sigma = float(getattr(config, "lastvit_select_sigma", 0.0))
        largest_raw = getattr(config, "lastvit_select_largest", True)
        if isinstance(largest_raw, str) and largest_raw.lower() == "both":
            self.lastvit_select_largest = "both"
        else:
            self.lastvit_select_largest = bool(largest_raw)
        self.lastvit_select_formula = str(
            getattr(config, "lastvit_select_formula", "v2_abs_mean")
        )

        self.use_conditional_text = bool(getattr(config, "use_conditional_text", False))
        if self.use_conditional_text:
            meta_hidden = int(getattr(config, "meta_net_hidden", 48))
            self.meta_net = nn.Sequential(
                nn.Linear(self.dim_f, meta_hidden),
                nn.LayerNorm(meta_hidden),
                nn.GELU(),
                nn.Linear(meta_hidden, self.dim_f),
            )
            with torch.no_grad():
                self.meta_net[-1].weight.zero_()
                self.meta_net[-1].bias.zero_()
            self.cond_text_ratio = float(getattr(config, "conditional_text_ratio", 0.05))
        else:
            self.cond_text_ratio = 0.0

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
        x = self.seen_text_embeds
        adapted = self.adapter_ratio * self.text_adapter(x) + (1.0 - self.adapter_ratio) * x
        return F.normalize(adapted, dim=1)

    def _make_all_text(self, device, dtype):
        seen_text = self.get_adapted_seen_text().to(device=device, dtype=dtype)
        unseen_text = self.unseen_text_embeds.to(device=device, dtype=dtype)
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

    def _ag_jepa_loss(self, patches, all_text, labels):
        device = patches.device
        if (not self.use_ag_jepa) or patches is None or all_text is None:
            zero = torch.tensor(0.0, device=device if patches is not None else labels.device)
            return zero, zero

        B, N, _ = patches.shape
        k = max(1, min(int(self.jepa_topk), N - 1))
        labels = labels.to(device=device, dtype=torch.long)
        class_text = all_text[labels].to(device=device, dtype=patches.dtype)

        with torch.no_grad():
            patch_n = F.normalize(patches.float(), dim=-1)
            text_n = F.normalize(class_text.float(), dim=-1)
            patch_score = torch.einsum("bnd,bd->bn", patch_n, text_n)
            _, masked_idx = torch.topk(patch_score, k=k, dim=1, largest=True)

        mask = torch.zeros(B, N, dtype=torch.bool, device=device)
        mask.scatter_(1, masked_idx, True)
        keep = ~mask

        patch_z = self.cross_tf.embed_cv(patches)
        target = patch_z[mask].view(B, k, -1).mean(dim=1).detach()
        keep_f = keep.unsqueeze(-1).to(patch_z.dtype)
        context = (patch_z * keep_f).sum(dim=1) / keep_f.sum(dim=1).clamp_min(1.0)

        text_z = self.cross_tf.embed_text(class_text)
        pred = self.jepa_predictor(torch.cat([context, text_z], dim=-1))
        pos_sim = F.cosine_similarity(pred, target, dim=-1)
        loss_jepa = (1.0 - pos_sim).mean()

        seen = self.seenclass.to(device)
        label_map = torch.full((self.nclass,), -1, device=device, dtype=torch.long)
        label_map[seen] = torch.arange(seen.numel(), device=device)
        local_labels = label_map[labels]
        if (local_labels < 0).any():
            raise ValueError("AG-JEPA expects global labels from seen classes.")
        neg_local = (local_labels + 1) % seen.numel()
        neg_text = all_text[seen[neg_local]].to(device=device, dtype=patches.dtype)

        neg_text_z = self.cross_tf.embed_text(neg_text)
        pred_neg = self.jepa_predictor(torch.cat([context.detach(), neg_text_z], dim=-1))
        neg_sim = F.cosine_similarity(pred_neg, target, dim=-1)
        loss_jepa_neg = F.relu(neg_sim - pos_sim.detach() + self.jepa_neg_margin).mean()
        return loss_jepa, loss_jepa_neg

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

        if cls_token is not None:
            vis_n = F.normalize(cls_token, dim=1)
        else:
            vis_n = F.normalize(patches.mean(dim=1), dim=1)

        if self.use_conditional_text and cls_token is not None and self.cond_text_ratio > 0:
            pi_x = F.normalize(self.meta_net(cls_token), dim=-1)
            all_text_cond = all_text.unsqueeze(0).expand(cls_token.size(0), -1, -1).clone()
            seen_idx = self.seenclass.to(patches.device)
            all_text_cond[:, seen_idx, :] = (
                all_text[seen_idx].unsqueeze(0) + self.cond_text_ratio * pi_x.unsqueeze(1)
            )
            text_n_cond = F.normalize(all_text_cond, dim=-1)
            base_logits = (vis_n.unsqueeze(1) * text_n_cond).sum(dim=-1) * logit_scale
        else:
            text_n = F.normalize(all_text, dim=1)
            base_logits = vis_n @ text_n.T * logit_scale

        cm_out = self.cross_tf(
            patches,
            all_text,
            cls_token,
            lastvit_select_k=self.lastvit_select_k,
            lastvit_select_sigma=self.lastvit_select_sigma,
            lastvit_select_largest=self.lastvit_select_largest,
            lastvit_select_formula=self.lastvit_select_formula,
        )
        local_score = cm_out["local_score"]
        logits_200 = base_logits + self.local_weight * local_score

        if is_train:
            logits = logits_200[:, self.seenclass.to(logits_200.device)]
        else:
            logits = logits_200

        return {
            "logits": logits,
            "logits_200": logits_200,
            "base_logits": base_logits,
            "local_score": local_score,
            "text_topology_features": None,
            "clip_S_pp": logits,
            "clip_pred": logits,
            "score_s2v": cm_out["score_s2v"],
            "score_v2s": cm_out["score_v2s"],
            "jepa_patches": patches,
            "all_text": all_text,
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

        base_logits = in_package.get("base_logits")
        local_score = in_package.get("local_score")
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

        loss_jepa = torch.tensor(0.0, device=logits.device)
        loss_jepa_neg = torch.tensor(0.0, device=logits.device)
        lambda_jepa = float(getattr(self.config, "lambda_jepa", 0.0))
        lambda_jepa_neg = float(getattr(self.config, "lambda_jepa_neg", 0.0))
        if self.use_ag_jepa and (lambda_jepa > 0 or lambda_jepa_neg > 0):
            jepa_patches = in_package.get("jepa_patches")
            all_text_jepa = in_package.get("all_text")
            if jepa_patches is not None and all_text_jepa is not None:
                loss_jepa, loss_jepa_neg = self._ag_jepa_loss(
                    jepa_patches, all_text_jepa, labels
                )
                loss = loss + lambda_jepa * loss_jepa
                loss = loss + lambda_jepa_neg * loss_jepa_neg

        score_s2v = in_package.get("score_s2v")
        score_v2s = in_package.get("score_v2s")
        loss_msdn = torch.tensor(0.0, device=logits.device)
        loss_msdn_gate = torch.tensor(1.0, device=logits.device)
        lambda_msdn = float(getattr(self.config, "lambda_msdn", 0.0))
        if lambda_msdn > 0 and score_s2v is not None and score_v2s is not None:
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
            loss_msdn = (T_msdn * T_msdn / 2.0) * (kl_s2v_to_v2s + kl_v2s_to_s2v)
            loss = loss + lambda_msdn * loss_msdn

        return {
            "loss": loss,
            "loss_CE": loss_CE,
            "loss_consist": loss_consist,
            "loss_topo": loss_topo,
            "loss_msdn": loss_msdn,
            "loss_msdn_gate": loss_msdn_gate,
            "loss_jepa": loss_jepa,
            "loss_jepa_neg": loss_jepa_neg,
        }
