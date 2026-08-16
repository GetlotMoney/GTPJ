"""Extract deterministic crop CLS features and evaluate frozen X2 plus ARTV."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np
import scipy.io as sio
import torch
import torch.nn.functional as F
import yaml
from PIL import Image

from artv import AnatomyAnchoredRoleTransportVerifier


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPECTED_ROLES = (
    "beak",
    "head_features",
    "body_plumage",
    "wings",
    "tail",
    "legs",
    "overall_appearance",
    "unique_discriminative_features",
)
HASHED_KEYS = (
    "sentence_embeds",
    "train_labels",
    "seen_features",
    "seen_labels",
    "unseen_features",
    "unseen_labels",
    "res101",
    "att_splits",
    "clip_weight",
    "x2_checkpoint",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clip_package_sha256(module_file: Path) -> str:
    """Hash CLIP sources and tokenizer data without binding the install root."""

    root = module_file.resolve().parent
    sources = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in {".py", ".gz"}
            and "__pycache__" not in path.parts
        ),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    if not sources:
        raise ValueError(f"CLIP package has no source or tokenizer files: {root}.")
    digest = hashlib.sha256()
    for source in sources:
        relative = source.relative_to(root).as_posix().encode("utf-8")
        content = source.read_bytes()
        digest.update(len(relative).to_bytes(8, byteorder="big", signed=False))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, byteorder="big", signed=False))
        digest.update(content)
    return digest.hexdigest()


def normalized_preprocess_repr(preprocess) -> str:
    return re.sub(r" at 0x[0-9a-fA-F]+", "", repr(preprocess))


def role_token_sha256(tokens: torch.Tensor) -> str:
    if tuple(tokens.shape) != (6, 77):
        raise ValueError("role anchor tokens must have shape [6,77].")
    serialized = json.dumps(tokens.detach().cpu().long().tolist(), separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def verify_runtime_identity(config: dict, clip_module, preprocess) -> dict[str, str]:
    import PIL
    import torchvision

    actual = {
        "torch_version": str(torch.__version__),
        "torch_cuda_version": str(torch.version.cuda),
        "torchvision_version": str(torchvision.__version__),
        "pillow_version": str(PIL.__version__),
        "clip_package_sha256": clip_package_sha256(Path(clip_module.__file__)),
        "preprocess_normalized_repr_sha256": hashlib.sha256(
            normalized_preprocess_repr(preprocess).encode("utf-8")
        ).hexdigest(),
    }
    expected = config["runtime_identity"]
    if actual != expected:
        mismatches = sorted(key for key in expected if actual.get(key) != expected[key])
        raise ValueError("ARTV runtime identity mismatch: " + ", ".join(mismatches))
    return actual


def configure_determinism(config: dict) -> None:
    settings = config["determinism"]
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = settings["cublas_workspace_config"]
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def clean_commit() -> str:
    commit = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or dirty:
        raise ValueError("formal ARTV evaluation requires one clean committed worktree.")
    return commit


def load_config(path: Path, expected_sha256: str) -> tuple[dict, str]:
    digest = sha256_file(path)
    if digest != expected_sha256:
        raise ValueError(f"config SHA-256 mismatch: {digest}.")
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("experiment_id") != "V5-INNOVATION-022" or config.get("run_id") != "RUN-001":
        raise ValueError("ARTV experiment/run identity mismatch.")
    if tuple(config.get("role_order", ())) != EXPECTED_ROLES:
        raise ValueError("role_order violates the 6 local + global + unique contract.")
    if config.get("crop_scheme") != "deterministic_15":
        raise ValueError("ARTV freezes deterministic_15 crops.")
    if config.get("crop_scales") != [0.5, 0.7, 1.0] or config.get(
        "crops_per_scale"
    ) != [9, 5, 1]:
        raise ValueError("ARTV crop geometry differs from the frozen 9+5+1 bank.")
    if config.get("certificate_votes") != 5:
        raise ValueError("ARTV freezes a five-of-seven certificate.")
    if not isinstance(config.get("seed"), int) or config["seed"] < 0:
        raise ValueError("seed must be a non-negative integer.")
    for key in ("crop_batch_images", "evaluation_batch_size", "sinkhorn_iterations"):
        if not isinstance(config.get(key), int) or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer.")
    epsilon = config.get("transport_epsilon")
    if not isinstance(epsilon, (int, float)) or not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("transport_epsilon must be finite and positive.")
    image_digest = config.get("official_image_content_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", image_digest):
        raise ValueError("official_image_content_sha256 must be a lowercase SHA-256.")
    if not re.fullmatch(r"[0-9a-f]{64}", str(config.get("role_anchor_tokens_sha256", ""))):
        raise ValueError("role_anchor_tokens_sha256 must be a lowercase SHA-256.")
    expected_runtime_keys = {
        "torch_version",
        "torch_cuda_version",
        "torchvision_version",
        "pillow_version",
        "clip_package_sha256",
        "preprocess_normalized_repr_sha256",
    }
    runtime_identity = config.get("runtime_identity")
    if not isinstance(runtime_identity, dict) or set(runtime_identity) != expected_runtime_keys:
        raise ValueError("runtime_identity does not match the frozen ARTV contract.")
    for key in ("clip_package_sha256", "preprocess_normalized_repr_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", str(runtime_identity[key])):
            raise ValueError(f"runtime_identity.{key} must be a lowercase SHA-256.")
    determinism = config.get("determinism")
    if determinism != {"enabled": True, "cublas_workspace_config": ":4096:8"}:
        raise ValueError("ARTV deterministic execution settings differ from the frozen contract.")
    return config, digest


def resolve_paths(config: dict, data_root: Path) -> dict[str, Path]:
    paths = {}
    for key, value in config["inputs"].items():
        candidate = Path(value)
        paths[key] = candidate if candidate.is_absolute() else data_root / candidate
    missing = [key for key, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError("missing ARTV input: " + ", ".join(missing))
    return paths


def verify_hashes(config: dict, paths: dict[str, Path]) -> dict[str, str]:
    actual = {}
    for key in HASHED_KEYS:
        actual[key] = sha256_file(paths[key])
        if actual[key] != config["expected_sha256"][key]:
            raise ValueError(f"ARTV input SHA mismatch: {key}.")
    return actual


def verify_class_order(config: dict, split_path: Path) -> None:
    raw = sio.loadmat(split_path)["allclasses_names"]
    if tuple(raw.shape) != (200, 1):
        raise ValueError("CUB class order must have shape [200,1].")
    names = [str(item[0][0]) for item in raw]
    serialized = json.dumps(names, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    if digest != config["class_order_sha256"]:
        raise ValueError("CUB class order SHA mismatch.")


def verify_output_boundary(run_dir: Path) -> None:
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite {run_dir}.")
    output = subprocess.check_output(
        ["git", "-C", str(PROJECT_ROOT), "worktree", "list", "--porcelain"], text=True
    )
    for line in output.splitlines():
        if not line.startswith("worktree "):
            continue
        worktree = Path(line.split(" ", 1)[1]).resolve()
        try:
            run_dir.resolve().relative_to(worktree)
        except ValueError:
            continue
        raise ValueError("run directory must stay outside every Git worktree.")


def frozen_x2_from_checkpoint(
    sentence_embeds: torch.Tensor,
    seenclasses: torch.Tensor,
    checkpoint_path: Path,
    config: dict,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, dict]:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("code_commit") != config["x2_identity"]["code_commit"]:
        raise ValueError("X2 checkpoint code commit mismatch.")
    if int(checkpoint.get("best_epoch", -1)) != int(config["x2_identity"]["best_epoch"]):
        raise ValueError("X2 checkpoint epoch mismatch.")
    checkpoint_config = checkpoint.get("config", {})
    if checkpoint_config.get("conditions", {}).get("PSE-X2", {}).get("mode") != "legacy_uniform":
        raise ValueError("checkpoint is not frozen PSE-X2 legacy-uniform.")
    state = checkpoint["model"]
    required = {
        "legacy_attention.in_proj_weight",
        "legacy_attention.in_proj_bias",
        "legacy_attention.out_proj.weight",
        "legacy_attention.out_proj.bias",
        "post_projection.weight",
        "post_projection.bias",
        "layer_norm.weight",
        "layer_norm.bias",
        "logit_scale",
        "sentence_embeds",
        "adapted_classes",
    }
    if not required.issubset(state):
        raise ValueError("X2 checkpoint misses a required tensor.")
    expected_sentences = F.normalize(sentence_embeds.detach().float(), dim=-1)
    checkpoint_sentences = state["sentence_embeds"].detach().cpu().float()
    if not torch.equal(checkpoint_sentences, expected_sentences):
        raise ValueError("X2 sentence buffer differs from the frozen cache.")
    checkpoint_classes = state["adapted_classes"].detach().cpu().long()
    if not torch.equal(checkpoint_classes, seenclasses.detach().cpu().long()):
        raise ValueError("X2 adapted classes differ from the training split.")
    sentences = checkpoint_sentences.to(device)
    seen = checkpoint_classes.to(device)
    roles = sentences.index_select(0, seen)
    dim, heads = roles.shape[-1], 4
    head_dim = dim // heads
    in_weight = state["legacy_attention.in_proj_weight"].to(device)
    in_bias = state["legacy_attention.in_proj_bias"].to(device)
    _, _, value_weight = in_weight.chunk(3, dim=0)
    _, _, value_bias = in_bias.chunk(3, dim=0)
    value = F.linear(roles, value_weight, value_bias)
    value = value.view(roles.shape[0], 8, heads, head_dim).transpose(1, 2)
    uniform = value.new_full((roles.shape[0], heads, 8, 8), 1.0 / 8.0)
    context = torch.matmul(uniform, value)
    context = context.transpose(1, 2).contiguous().view(roles.shape[0], 8, dim)
    context = F.linear(
        context,
        state["legacy_attention.out_proj.weight"].to(device),
        state["legacy_attention.out_proj.bias"].to(device),
    )
    context = F.linear(
        context,
        state["post_projection.weight"].to(device),
        state["post_projection.bias"].to(device),
    )
    mixed = 0.35 * context + 0.65 * roles
    transformed = F.layer_norm(
        2.0 * mixed,
        (dim,),
        state["layer_norm.weight"].to(device),
        state["layer_norm.bias"].to(device),
        1e-5,
    )
    base_vectors = sentences.mean(dim=1)
    base_scale = base_vectors.new_ones((base_vectors.shape[0],))
    base_scale[seen] = 0.35
    base_part = base_scale.unsqueeze(-1) * base_vectors
    role_part = transformed.new_zeros((200, 8, dim))
    role_part[seen] = 0.65 * transformed / 8.0
    prototypes = F.normalize(base_part + role_part.sum(dim=1), dim=-1)
    scale = state["logit_scale"].to(device).exp().clamp(max=100.0)
    diagnostics = {
        "checkpoint_code_commit": checkpoint["code_commit"],
        "checkpoint_best_epoch": int(checkpoint["best_epoch"]),
        "scale": float(scale.detach().cpu()),
    }
    return prototypes.detach().cpu(), scale.detach().cpu(), diagnostics


def _mat_string(value: object) -> str:
    while isinstance(value, np.ndarray):
        if value.size != 1:
            raise ValueError("image_files contains a non-scalar entry.")
        value = value.reshape(-1)[0]
    return str(value).replace("\\", "/")


def split_image_paths(
    res_path: Path, split_path: Path, images_root: Path
) -> tuple[list[Path], torch.Tensor, list[Path], torch.Tensor]:
    res = sio.loadmat(res_path)
    split = sio.loadmat(split_path)
    raw_paths = np.squeeze(res["image_files"])
    labels = torch.from_numpy(res["labels"].astype(np.int64).squeeze() - 1)

    def select(key: str) -> tuple[list[Path], torch.Tensor]:
        indices = split[key].astype(np.int64).squeeze() - 1
        paths = []
        for index in indices.tolist():
            raw = _mat_string(raw_paths[index])
            marker = "images/"
            relative = raw.split(marker, 1)[1] if marker in raw else Path(raw).name
            path = images_root / relative
            if not path.is_file():
                raise FileNotFoundError(f"missing CUB image: {path}")
            paths.append(path)
        return paths, labels[torch.from_numpy(indices)]

    seen_paths, seen_labels = select("test_seen_loc")
    unseen_paths, unseen_labels = select("test_unseen_loc")
    return seen_paths, seen_labels, unseen_paths, unseen_labels


def ordered_image_content_sha256(image_paths: list[Path]) -> str:
    """Bind every image byte to its frozen evaluation position."""

    digest = hashlib.sha256()
    for index, path in enumerate(image_paths):
        size = path.stat().st_size
        digest.update(index.to_bytes(8, byteorder="big", signed=False))
        digest.update(size.to_bytes(8, byteorder="big", signed=False))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def deterministic_crops(image: Image.Image) -> list[Image.Image]:
    width, height = image.size
    side = min(width, height)
    output = []
    for scale, grid in ((0.5, 3), (0.7, 2)):
        crop_side = max(1, int(round(side * scale)))
        x_max, y_max = width - crop_side, height - crop_side
        if grid == 3:
            xs = (0, x_max // 2, x_max)
            ys = (0, y_max // 2, y_max)
            positions = [(x, y) for y in ys for x in xs]
        else:
            positions = [(0, 0), (x_max, 0), (0, y_max), (x_max, y_max), (x_max // 2, y_max // 2)]
        output.extend(
            image.crop((x, y, x + crop_side, y + crop_side)) for x, y in positions
        )
    offset_x, offset_y = (width - side) // 2, (height - side) // 2
    output.append(image.crop((offset_x, offset_y, offset_x + side, offset_y + side)))
    if len(output) != 15:
        raise AssertionError("deterministic crop bank must contain 15 crops.")
    return output


def extract_crop_features(
    image_paths: list[Path], clip_model, preprocess, device: torch.device, batch_images: int, logger
) -> torch.Tensor:
    outputs = []
    for start in range(0, len(image_paths), batch_images):
        current = image_paths[start : start + batch_images]
        tensors = []
        for path in current:
            with Image.open(path) as handle:
                image = handle.convert("RGB")
                tensors.extend(preprocess(crop) for crop in deterministic_crops(image))
        batch = torch.stack(tensors).to(device)
        with torch.no_grad():
            encoded = F.normalize(clip_model.encode_image(batch).float(), dim=-1)
        if not torch.isfinite(encoded).all():
            raise RuntimeError("CLIP produced a non-finite crop feature.")
        outputs.append(encoded.view(len(current), 15, -1).half().cpu())
        completed = min(start + batch_images, len(image_paths))
        if completed == len(image_paths) or completed % 100 == 0:
            logger(f"crop_extraction={completed}/{len(image_paths)}")
    return torch.cat(outputs, dim=0)


def per_class_accuracy(labels: torch.Tensor, predictions: torch.Tensor, classes: torch.Tensor) -> float:
    values = []
    for class_id in classes.cpu().long():
        mask = labels.cpu().long() == class_id
        if not mask.any():
            raise ValueError(f"evaluation has no class {int(class_id)}.")
        values.append((predictions.cpu().long()[mask] == labels.cpu().long()[mask]).float().mean())
    return 100.0 * float(torch.stack(values).mean())


def metric_set(
    seen_logits: torch.Tensor,
    unseen_logits: torch.Tensor,
    zs_logits: torch.Tensor,
    seen_labels: torch.Tensor,
    unseen_labels: torch.Tensor,
    unseenclasses: torch.Tensor,
) -> dict[str, float]:
    allclasses = torch.arange(200)
    seenclasses = allclasses[~torch.isin(allclasses, unseenclasses)]
    seen_predictions = seen_logits.argmax(dim=1)
    unseen_predictions = unseen_logits.argmax(dim=1)
    zs_predictions = unseenclasses[zs_logits.argmax(dim=1)]
    seen = per_class_accuracy(seen_labels, seen_predictions, seenclasses)
    unseen = per_class_accuracy(unseen_labels, unseen_predictions, unseenclasses)
    denominator = seen + unseen
    harmonic = 0.0 if denominator == 0.0 else 2.0 * seen * unseen / denominator
    zs = per_class_accuracy(unseen_labels, zs_predictions, unseenclasses)
    return {"U": unseen, "S": seen, "H": harmonic, "ZS": zs}


def batched_logits(
    model: AnatomyAnchoredRoleTransportVerifier,
    images: torch.Tensor,
    crops: torch.Tensor,
    device: torch.device,
    batch_size: int,
    class_ids: torch.Tensor | None = None,
    **kwargs,
) -> torch.Tensor:
    outputs = []
    with torch.no_grad():
        for start in range(0, images.shape[0], batch_size):
            outputs.append(
                model.logits(
                    images[start : start + batch_size].to(device),
                    None if class_ids is None else class_ids.to(device),
                    crop_features=crops[start : start + batch_size].to(device),
                    **kwargs,
                ).cpu()
            )
    logits = torch.cat(outputs, dim=0)
    if not torch.isfinite(logits).all():
        raise RuntimeError("ARTV produced a non-finite logit.")
    return logits


def change_diagnostics(base: torch.Tensor, variant: torch.Tensor, labels: torch.Tensor) -> dict[str, int]:
    base_predictions = base.argmax(dim=1)
    variant_predictions = variant.argmax(dim=1)
    changed = base_predictions != variant_predictions
    return {
        "changed": int(changed.sum()),
        "rescued": int((changed & base_predictions.ne(labels) & variant_predictions.eq(labels)).sum()),
        "harmed": int((changed & base_predictions.eq(labels) & variant_predictions.ne(labels)).sum()),
    }


def run(
    config_path: Path,
    data_root: Path,
    run_dir: Path,
    expected_commit: str,
    expected_config_sha256: str,
) -> dict:
    commit = clean_commit()
    if commit != expected_commit:
        raise ValueError(f"run commit mismatch: {commit}.")
    config, config_sha256 = load_config(config_path, expected_config_sha256)
    configure_determinism(config)
    if run_dir.name != config["run_id"]:
        raise ValueError("run directory name must equal RUN-001.")
    verify_output_boundary(run_dir)
    paths = resolve_paths(config, data_root)
    input_sha256 = verify_hashes(config, paths)
    verify_class_order(config, paths["att_splits"])
    seen_paths, raw_seen_labels, unseen_paths, raw_unseen_labels = split_image_paths(
        paths["res101"], paths["att_splits"], paths["cub_images"]
    )
    if len(seen_paths) != 1764 or len(unseen_paths) != 2967:
        raise ValueError("official CUB image counts differ from 1764/2967.")
    image_content_sha256 = ordered_image_content_sha256(seen_paths + unseen_paths)
    if image_content_sha256 != config["official_image_content_sha256"]:
        raise ValueError("official CUB image content SHA mismatch.")
    input_sha256["official_images"] = image_content_sha256
    device = torch.device(config["device"])
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("formal ARTV evaluation requires a visible CUDA device.")
    torch.manual_seed(int(config["seed"]))
    np.random.seed(int(config["seed"]))
    torch.cuda.manual_seed_all(int(config["seed"]))

    import clip

    clip_model, preprocess = clip.load(
        str(paths["clip_weight"]),
        device=device,
        jit=False,
    )
    runtime_identity = verify_runtime_identity(config, clip, preprocess)
    tokens = clip.tokenize(config["role_anchor_prompts"]).long()
    anchor_token_sha256 = role_token_sha256(tokens)
    if anchor_token_sha256 != config["role_anchor_tokens_sha256"]:
        raise ValueError("ARTV role anchor token SHA mismatch.")

    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / "evaluation.log"

    def logger(message: str) -> None:
        print(message, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    logger(f"code_commit={commit}")
    logger(f"config_sha256={config_sha256}")
    sentence_embeds = torch.load(paths["sentence_embeds"], map_location="cpu", weights_only=True)
    train_labels = torch.load(paths["train_labels"], map_location="cpu", weights_only=True).long()
    seen_features = torch.load(paths["seen_features"], map_location="cpu", weights_only=True).float()
    seen_labels = torch.load(paths["seen_labels"], map_location="cpu", weights_only=True).long()
    unseen_features = torch.load(paths["unseen_features"], map_location="cpu", weights_only=True).float()
    unseen_labels = torch.load(paths["unseen_labels"], map_location="cpu", weights_only=True).long()
    if not torch.equal(seen_labels, raw_seen_labels) or not torch.equal(unseen_labels, raw_unseen_labels):
        raise ValueError("raw-image order differs from frozen official feature caches.")
    if tuple(sentence_embeds.shape) != (200, 8, 768):
        raise ValueError("sentence cache must have shape [200,8,768].")
    if tuple(seen_features.shape) != (1764, 768) or tuple(unseen_features.shape) != (2967, 768):
        raise ValueError("official CLS feature shapes are invalid.")
    seenclasses = torch.unique(train_labels, sorted=True)
    unseenclasses = torch.arange(200)[~torch.isin(torch.arange(200), seenclasses)]
    x2_prototypes, x2_scale, x2_diagnostics = frozen_x2_from_checkpoint(
        sentence_embeds, seenclasses, paths["x2_checkpoint"], config, device
    )

    clip_model.eval()
    for parameter in clip_model.parameters():
        parameter.requires_grad_(False)
    tokens = tokens.to(device)
    with torch.no_grad():
        role_anchors = F.normalize(clip_model.encode_text(tokens).float(), dim=-1).cpu()
    if tuple(role_anchors.shape) != (6, 768) or not torch.isfinite(role_anchors).all():
        raise RuntimeError("CLIP role anchors are invalid.")
    seen_crops = extract_crop_features(
        seen_paths, clip_model, preprocess, device, int(config["crop_batch_images"]), logger
    )
    seen_crop_path = run_dir / "seen_crop_features.pt"
    torch.save(seen_crops, seen_crop_path)
    unseen_crops = extract_crop_features(
        unseen_paths, clip_model, preprocess, device, int(config["crop_batch_images"]), logger
    )
    unseen_crop_path = run_dir / "unseen_crop_features.pt"
    torch.save(unseen_crops, unseen_crop_path)
    crop_feature_sha256 = {
        "seen": sha256_file(seen_crop_path),
        "unseen": sha256_file(unseen_crop_path),
    }
    del clip_model
    torch.cuda.empty_cache()

    model = AnatomyAnchoredRoleTransportVerifier(
        sentence_embeds,
        x2_prototypes.float(),
        x2_scale,
        role_anchors,
        sinkhorn_iterations=int(config["sinkhorn_iterations"]),
        transport_epsilon=float(config["transport_epsilon"]),
        certificate_votes=int(config["certificate_votes"]),
    ).to(device)
    if sum(parameter.numel() for parameter in model.parameters()) != 0:
        raise RuntimeError("ARTV must remain training-free.")
    evaluation_batch = int(config["evaluation_batch_size"])
    controls = {
        "artv": {},
        "role_shuffle": {"role_description_permutation": torch.tensor(config["role_shuffle_permutation"])},
        "unique_swap": {"unique_swap_with_runner_up": True},
    }
    all_logits = {}
    x2_seen = model.base_logits(seen_features.to(device)).cpu()
    x2_unseen = model.base_logits(unseen_features.to(device)).cpu()
    x2_zs = model.base_logits(unseen_features.to(device), unseenclasses.to(device)).cpu()
    if not all(torch.isfinite(value).all() for value in (x2_seen, x2_unseen, x2_zs)):
        raise RuntimeError("frozen X2 produced a non-finite logit.")
    all_logits["x2"] = (x2_seen, x2_unseen, x2_zs)
    for name, kwargs in controls.items():
        all_logits[name] = (
            batched_logits(model, seen_features, seen_crops, device, evaluation_batch, **kwargs),
            batched_logits(model, unseen_features, unseen_crops, device, evaluation_batch, **kwargs),
            batched_logits(
                model,
                unseen_features,
                unseen_crops,
                device,
                evaluation_batch,
                class_ids=unseenclasses,
                **kwargs,
            ),
        )
    metrics = {
        name: metric_set(*values, seen_labels, unseen_labels, unseenclasses)
        for name, values in all_logits.items()
    }
    expected_x2 = config["x2_identity"]["metrics_percent"]
    if any(abs(metrics["x2"][key] - float(expected_x2[key])) > 1e-5 for key in ("U", "S", "H", "ZS")):
        raise RuntimeError("ARTV did not reproduce the frozen X2 baseline.")
    changes = {}
    for name in controls:
        changes[name] = {
            "seen": change_diagnostics(x2_seen, all_logits[name][0], seen_labels),
            "unseen": change_diagnostics(x2_unseen, all_logits[name][1], unseen_labels),
        }
    state_path = run_dir / "artv_state.pth"
    torch.save(
        {
            "model": model.state_dict(),
            "code_commit": commit,
            "config_sha256": config_sha256,
            "input_sha256": input_sha256,
        },
        state_path,
    )
    result = {
        "status": "completed",
        "experiment_id": config["experiment_id"],
        "run_id": config["run_id"],
        "code_commit": commit,
        "config_sha256": config_sha256,
        "input_sha256": input_sha256,
        "clip_model": config["clip_model"],
        "runtime_identity": runtime_identity,
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "role_anchor_prompts": config["role_anchor_prompts"],
        "role_anchor_tokens_sha256": anchor_token_sha256,
        "x2_diagnostics": x2_diagnostics,
        "trainable_parameters": 0,
        "formal_evidence": bool(config["formal_evidence"]),
        "evidence_label": config["evidence_label"],
        "official_test_policy": config["official_test_policy"],
        "official_test_used_for_selection": False,
        "official_test_evaluations": {name: 1 for name in metrics},
        "metrics_percent": metrics,
        "delta_vs_x2_H": metrics["artv"]["H"] - metrics["x2"]["H"],
        "delta_vs_role_shuffle_H": metrics["artv"]["H"] - metrics["role_shuffle"]["H"],
        "delta_vs_unique_swap_H": metrics["artv"]["H"] - metrics["unique_swap"]["H"],
        "change_diagnostics": changes,
        "crop_feature_sha256": crop_feature_sha256,
        "artv_state_sha256": sha256_file(state_path),
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    for name, values in metrics.items():
        logger(
            f"{name} U={values['U']:.6f} S={values['S']:.6f} "
            f"H={values['H']:.6f} ZS={values['ZS']:.6f}"
        )
    logger(f"delta_vs_x2_H={result['delta_vs_x2_H']:.6f}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    args = parser.parse_args()
    run(
        args.config.resolve(),
        args.data_root.resolve(),
        args.run_dir.resolve(),
        args.expected_commit,
        args.expected_config_sha256,
    )


if __name__ == "__main__":
    main()
