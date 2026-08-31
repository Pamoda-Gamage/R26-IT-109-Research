"""
Primary image recogniser — zero-shot CLIP, no Gemini.

Mirrors the frozen-encoder + cheap-head pattern of predict_service.py: CLIP's
image tower is the frozen encoder; the "heads" are zero-shot prompt banks
(image_taxonomy.PROMPT_BANK). At inference we embed the image once and score it
by cosine similarity against per-head text-embedding matrices built once at load.

`recognize_image()` returns the same dict shape a future LogisticRegression
linear probe would, so process_image_message / classify_and_respond never need
to know which produced the numbers. `should_fallback_to_gemini()` is a pure
function (no model load) that decides when the local result is too shaky and
Gemini should "improvise".
"""
from __future__ import annotations

import io

import numpy as np

from app.core.logger import logger
from app.services import image_taxonomy as tax
from app.services.image_taxonomy import service_type_for_subtype

# Lazily populated by _ensure_loaded() — kept module-global so the model loads
# at most once per process.
_model = None
_processor = None
_torch = None
_loaded = False
_logit_scale = 100.0
_matrices: dict[str, np.ndarray] = {}   # head -> [n_labels, d] float32, L2-normalised
_labels: dict[str, list[str]] = {}

_HEADS = ("object_type", "subtype", "condition", "service_type")


def _cfg():
    """Fetched per call so tests can monkeypatch thresholds on app.config."""
    from app import config
    return config


# ---------------------------------------------------------------------------
# Model / prompt-bank loading
# ---------------------------------------------------------------------------
def _ensure_loaded() -> None:
    global _model, _processor, _torch, _loaded, _logit_scale
    if _loaded:
        return

    import torch
    from transformers import CLIPModel, AutoProcessor

    cfg = _cfg()
    tax.validate()

    # Warn (don't fail) if the image taxonomy's service vocab has drifted from
    # what the text classifier actually knows.
    try:
        from app.services.predict_service import SERVICE_TYPE_LABELS
        drift = set(SERVICE_TYPE_LABELS) - set(tax.KNOWN_SERVICE_TYPES)
        if drift:
            logger.warning(
                "image_taxonomy.KNOWN_SERVICE_TYPES is missing labels the text "
                "classifier uses: %s", sorted(drift),
            )
    except Exception as e:  # pragma: no cover - predict_service import issues
        logger.warning("Could not cross-check service vocab: %s", e)

    logger.info("Loading CLIP image recogniser: %s", cfg.CLIP_MODEL_NAME)
    _torch = torch
    _model = CLIPModel.from_pretrained(cfg.CLIP_MODEL_NAME)
    _model.eval()
    # No torchvision in the venv by design — the processor falls back to its
    # Pillow image backend, which is all we need.
    _processor = AutoProcessor.from_pretrained(cfg.CLIP_MODEL_NAME)

    with torch.no_grad():
        _logit_scale = float(_model.logit_scale.exp().item())
        for head, labels in (
            ("object_type", list(tax.OBJECT_TYPES)),
            ("subtype", list(tax.ALL_SUBTYPES)),
            ("condition", list(tax.CONDITION_TAGS)),
            ("service_type", list(tax.KNOWN_SERVICE_TYPES)),
        ):
            _labels[head] = labels
            _matrices[head] = _encode_label_matrix(labels)

    _loaded = True
    logger.info("CLIP recogniser ready (logit_scale=%.1f)", _logit_scale)


def _encode_label_matrix(labels: list[str]) -> np.ndarray:
    """One L2-normalised text vector per label = mean of its prompt embeddings."""
    prompts: list[str] = []
    spans: list[tuple[int, int]] = []
    for lab in labels:
        p = tax.PROMPT_BANK[lab]
        spans.append((len(prompts), len(prompts) + len(p)))
        prompts.extend(p)

    inputs = _processor(text=prompts, return_tensors="pt", padding=True, truncation=True)
    # transformers 5.x returns a BaseModelOutputWithPooling; `pooler_output` is
    # the projected CLIP text embedding (verified to match logits_per_image).
    feats = _model.get_text_features(**inputs).pooler_output
    feats = feats / feats.norm(dim=-1, keepdim=True)
    feats = feats.cpu().numpy().astype("float32")

    out = np.zeros((len(labels), feats.shape[1]), dtype="float32")
    for i, (a, b) in enumerate(spans):
        v = feats[a:b].mean(axis=0)
        out[i] = v / (np.linalg.norm(v) + 1e-8)
    return out


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def embed_image(image_bytes: bytes) -> np.ndarray:
    """Single L2-normalised CLIP image embedding, shape [d]. Also the entry
    point a future linear-probe trainer uses to build its feature cache."""
    _ensure_loaded()
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    with _torch.no_grad():
        inputs = _processor(images=img, return_tensors="pt")
        feat = _model.get_image_features(**inputs).pooler_output
        feat = feat / feat.norm(dim=-1, keepdim=True)
    return feat.cpu().numpy().astype("float32")[0]


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - x.max()
    e = np.exp(x)
    return e / e.sum()


def _score(head: str, emb: np.ndarray, candidates: set[str] | None = None) -> dict:
    mat, labels = _matrices[head], _labels[head]
    idx = [i for i, l in enumerate(labels) if candidates is None or l in candidates]
    if not idx:
        idx = list(range(len(labels)))

    sims = mat[idx] @ emb                         # cosine (both normalised)
    probs = _softmax(_logit_scale * sims)
    order = np.argsort(probs)[::-1]
    top1 = int(order[0])
    top2 = int(order[1]) if len(order) > 1 else top1
    return {
        "label": labels[idx[top1]],
        "confidence": float(probs[top1]),
        "top2_margin": float(probs[top1] - probs[top2]),
        "sims": {labels[idx[i]]: float(sims[i]) for i in range(len(idx))},
        # Softmax probabilities over this same (possibly candidate-restricted)
        # set — comparable to "confidence" above, unlike the raw cosines in
        # "sims". Used to build a ranked candidate list for research display.
        "probs": {labels[idx[i]]: float(probs[i]) for i in range(len(idx))},
    }


def _top_candidates(probs: dict[str, float], top: int = 5) -> list[dict]:
    ranked = sorted(probs.items(), key=lambda x: -x[1])[:top]
    return [{"label": label, "confidence": conf} for label, conf in ranked]


def _describe(object_type: str, subtype: str | None, subtype_conf: float,
              conditions: list[str]) -> str:
    if subtype and subtype != "other" and subtype_conf >= 0.25:
        subj = tax.humanize(subtype)
    elif object_type != "other":
        subj = tax.humanize(object_type)
    else:
        subj = "an unidentified item"
    article = "an" if subj[:1].lower() in "aeiou" else "a"
    base = f"Photo shows {article} {subj}"
    real = [c for c in conditions if c != "no_visible_problem"]
    if real:
        return base + ", with " + ", ".join(tax.humanize(c) for c in real) + "."
    return base + "."


def recognize_image(image_bytes: bytes, caption: str = "") -> dict:
    """Zero-shot CLIP recognition. `caption` is accepted for API symmetry with
    the Gemini fallback but is not currently used to bias the vision result
    (it is already folded into the case narrative by the caller)."""
    _ensure_loaded()
    cfg = _cfg()
    emb = embed_image(image_bytes)

    ot = _score("object_type", emb)
    object_type = ot["label"]

    sub = _score("subtype", emb, candidates=set(tax.subtypes_for(object_type)))
    subtype = sub["label"] if sub["label"] != "other" else None
    subtype_conf = sub["confidence"]

    allowed = tax.allowed_service_types(object_type)
    st = _score("service_type", emb, candidates=allowed or None)
    st_label, st_conf = st["label"], st["confidence"]

    # Blend the zero-shot service_type with the subtype -> service_type prior:
    # a confidently recognised subtype is a stronger routing signal than the
    # (coarser) service_type head.
    prior = service_type_for_subtype(subtype)
    if prior and subtype_conf >= cfg.IMAGE_SUBTYPE_MIN_CONF and prior in (allowed or {prior}):
        if prior == st_label:
            service_type, service_type_conf = prior, st_conf
        else:
            service_type, service_type_conf = prior, float((st_conf + subtype_conf) / 2.0)
    else:
        service_type, service_type_conf = st_label, st_conf

    if service_type_conf < cfg.IMAGE_SERVICE_TYPE_MIN_CONF:
        service_type = None

    # conditions — multi-label. Raw CLIP cosines aren't comparable to a fixed
    # threshold, so score each tag as a pairwise softmax against the
    # "nothing wrong" anchor and keep the ones that clearly beat it.
    cond_sims = _matrices["condition"] @ emb
    cond_labels = _labels["condition"]
    anchor = float(cond_sims[cond_labels.index("no_visible_problem")])
    scored = []
    for i, lab in enumerate(cond_labels):
        if lab == "no_visible_problem":
            continue
        p = float(_softmax(_logit_scale * np.array([cond_sims[i], anchor]))[0])
        scored.append((lab, p, float(cond_sims[i])))
    scored.sort(key=lambda x: x[1], reverse=True)
    real = [lab for lab, p, s in scored
            if p >= cfg.IMAGE_CONDITION_THRESHOLD and s > anchor][:3]
    conditions = real or ["no_visible_problem"]

    return {
        "object_type": object_type,
        "object_type_confidence": ot["confidence"],
        "object_type_top2_margin": ot["top2_margin"],
        "object_type_candidates": _top_candidates(ot["probs"]),
        "subtype": subtype,
        "subtype_confidence": subtype_conf,
        "subtype_candidates": _top_candidates(sub["probs"]),
        "service_type": service_type,
        "service_type_confidence": service_type_conf,
        "service_type_candidates": _top_candidates(st["probs"]),
        "conditions": conditions,
        "condition_scores": {lab: p for lab, p, _ in scored},
        "description": _describe(object_type, subtype, subtype_conf, conditions),
        "suggested_service_type": service_type,
        "recognition_source": "clip_zero_shot",
    }


# ---------------------------------------------------------------------------
# Fallback policy (pure function — no model load)
# ---------------------------------------------------------------------------
def should_fallback_to_gemini(result: dict,
                              text_service_type: str | None = None) -> tuple[bool, list[str]]:
    """Decide whether the local result is too uncertain and Gemini should
    improvise. Returns (do_fallback, reasons)."""
    cfg = _cfg()
    if not cfg.ENABLE_GEMINI_FALLBACK:
        return False, []

    reasons: list[str] = []
    if result.get("object_type_confidence", 0.0) < cfg.IMAGE_OBJECT_TYPE_MIN_CONF:
        reasons.append("low_object_type_conf")
    if result.get("object_type_top2_margin", 0.0) < cfg.IMAGE_TOP2_MARGIN_MIN:
        reasons.append("small_top2_margin")
    if result.get("object_type") == "other":
        reasons.append("object_type_other")
    if result.get("subtype") in (None, "other") or \
            result.get("subtype_confidence", 0.0) < cfg.IMAGE_SUBTYPE_MIN_CONF:
        reasons.append("subtype_unknown")
    if result.get("service_type") is None or \
            result.get("service_type_confidence", 0.0) < cfg.IMAGE_SERVICE_TYPE_MIN_CONF:
        reasons.append("low_service_type_conf")

    prior = service_type_for_subtype(result.get("subtype"))
    if prior and result.get("service_type") and prior != result["service_type"]:
        reasons.append("cross_head_disagreement")

    if text_service_type and result.get("service_type") \
            and text_service_type != result["service_type"] \
            and result.get("service_type_confidence", 0.0) < 0.60:
        reasons.append("image_text_service_mismatch")

    return bool(reasons), reasons


def reconcile(clip_result: dict, gemini_result: dict, reasons: list[str]) -> dict:
    """Merge a Gemini fallback result over the local one. Gemini wins on the
    recognition fields (it was called precisely because the local ones were
    weak); anything Gemini omitted keeps the local value."""
    out = dict(clip_result)
    out.update({k: v for k, v in gemini_result.items() if v is not None})
    out["recognition_source"] = "gemini_fallback"
    out["fallback_reasons"] = reasons
    # Gemini has no comparable scored distribution (see analyze_image_v2's
    # fixed placeholder confidences) — the CLIP candidate lists inherited via
    # `dict(clip_result)` above would otherwise disagree with Gemini's own
    # top-1 labels just applied. Drop them rather than show a stale ranking.
    for key in ("object_type_candidates", "subtype_candidates", "service_type_candidates"):
        out.pop(key, None)
    return out
