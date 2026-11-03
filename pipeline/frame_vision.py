"""Frame-level visual gate for the reusable scene library.

Open CLIP measures whether sampled pixels resemble the requested visual topic,
not whether a transcript mentions it. For named people/characters, require
locally supplied reference frames; zero-shot text scores alone never establish
an identity. All results remain review-only, including purported CC BY footage.
"""
import io
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from common import ROOT

MODEL_ID = "openai/clip-vit-base-patch32"
# Immutable revision with reviewed safe tensor weights, rather than the mutable main.
MODEL_REVISION = "b527df4b30e5cc18bde1cc712833a741d2d8c362"
NEGATIVE_PROMPTS = (
    "A talking head presenting a video essay, podcast or commentary.",
    "A computer desktop, browser window or video editor with text on screen.",
    "A generic diagram of two circles connected by an arrow.",
    "Unrelated scenic nature or stock background footage.",
)
MIN_POSITIVE = 0.22
MIN_MARGIN = 0.035
MIN_IDENTITY = 0.72
IGNORED_NAMES = {
    "the", "a", "and", "but", "however", "there", "this", "that", "these",
    "those", "it", "its", "when", "where", "why", "what", "how",
    "player", "players", "episode", "season", "scene", "video", "game",
    "culling", "rules", "rule", "first", "next", "finally", "meanwhile",
    "one", "another", "people", "points", "point", "sorcerer", "sorcerers",
    "so", "for", "in", "on", "at", "of", "if", "then", "every",
    "satellites", "satellite", "phone", "phones", "gps", "traffic",
    "road", "sensor", "camera", "map", "video", "technology", "japan",
    "tokyo", "story", "internet", "computer", "today", "finally",
}


def proper_names(narration):
    """Heuristic for named characters/people, independent of any franchise."""
    tokens = re.findall(r"\b[A-Z][a-z]{2,}\b", str(narration))
    return list(dict.fromkeys(t for t in tokens if t.lower() not in IGNORED_NAMES))


def reference_images(library, names):
    """Resolve references exclusively inside a private reference folder."""
    base = (Path(library) / "references").resolve()
    catalog = base / "index.json"
    if not catalog.is_file():
        return {name: [] for name in names}
    data = json.loads(catalog.read_text(encoding="utf-8"))
    entries = data.get("entities", {})
    if not isinstance(entries, dict):
        raise ValueError("Malformed visual identity reference catalog")
    found = {}
    for name in names:
        paths = entries.get(name.casefold()) or []
        if not isinstance(paths, list):
            raise ValueError("Reference catalog entries must be lists of filenames")
        valid = []
        for value in paths:
            if not isinstance(value, str):
                raise ValueError("Invalid reference filename")
            candidate = (base / value).resolve()
            if (base not in candidate.parents or
                    candidate.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"} or
                    not candidate.is_file()):
                raise ValueError(f"Unsafe or missing visual reference for {name}")
            valid.append(candidate)
        found[name] = valid[:6]
    return found


def clip_duration(path):
    process = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True, timeout=20)
    return float(process.stdout.strip())


def sample_frames(path, count=4):
    """Inspect actual video pixels throughout the excerpt, not its thumbnail."""
    from PIL import Image
    duration = clip_duration(path)
    if duration < 0.5:
        raise ValueError("Clip too short to inspect")
    frames = []
    for i in range(count):
        seek = duration * (i + 0.5) / count
        proc = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{seek:.3f}",
             "-i", str(path), "-frames:v", "1", "-vf",
             "scale=448:448:force_original_aspect_ratio=decrease",
             "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
            capture_output=True, timeout=25, check=True)
        if not proc.stdout:
            raise ValueError(f"Could not sample visual frame at {seek:.2f}s")
        with Image.open(io.BytesIO(proc.stdout)) as image:
            frames.append(image.convert("RGB"))
    return frames


@lru_cache(maxsize=1)
def model_bundle():
    """Local model inference; cached weights, never paid per-frame inference."""
    try:
        import torch
        from transformers import CLIPModel, CLIPProcessor
    except ImportError as exc:
        raise RuntimeError(
            "Frame QA requires torch and transformers on the private Windows runner"
        ) from exc
    model = CLIPModel.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, trust_remote_code=False,
        use_safetensors=True)
    model.eval()
    processor = CLIPProcessor.from_pretrained(
        MODEL_ID, revision=MODEL_REVISION, trust_remote_code=False)
    return torch, model, processor


def score_images(frames, prompts, references):
    """Return frame/text and frame/reference cosine similarities."""
    torch, model, processor = model_bundle()
    from PIL import Image
    with torch.inference_mode():
        image_inputs = processor(images=frames, return_tensors="pt")
        image_embeddings = model.get_image_features(**image_inputs)
        texts = processor(text=list(prompts), return_tensors="pt", padding=True, truncation=True)
        text_embeddings = model.get_text_features(**texts)
        # Transformers 4.x returns tensors; newer releases may return outputs.
        if hasattr(image_embeddings, "pooler_output"):
            image_embeddings = image_embeddings.pooler_output
        if hasattr(text_embeddings, "pooler_output"):
            text_embeddings = text_embeddings.pooler_output
        image_embeddings = torch.nn.functional.normalize(image_embeddings, dim=-1)
        text_embeddings = torch.nn.functional.normalize(text_embeddings, dim=-1)
        scores = (image_embeddings @ text_embeddings.T).tolist()
        refs = {}
        for name, paths in references.items():
            if not paths:
                continue
            reference_imgs = []
            for path in paths:
                with Image.open(path) as image:
                    reference_imgs.append(image.convert("RGB"))
            reference_embeddings = model.get_image_features(
                **processor(images=reference_imgs, return_tensors="pt"))
            if hasattr(reference_embeddings, "pooler_output"):
                reference_embeddings = reference_embeddings.pooler_output
            reference_embeddings = torch.nn.functional.normalize(reference_embeddings, dim=-1)
            refs[name] = (image_embeddings @ reference_embeddings.T).tolist()
    return scores, refs


def decide_visual(scores, reference_scores, required_names):
    """Pure gate, easy to test with scored synthetic evidence."""
    if not scores or any(len(row) < 2 for row in scores):
        return {"accepted": False, "reason": "MISSING_FRAME_SCORES"}
    positives = [float(row[0]) for row in scores]
    margins = [float(row[0]) - max(float(v) for v in row[1:]) for row in scores]
    passing = [i for i, (positive, margin) in enumerate(zip(positives, margins))
               if positive >= MIN_POSITIVE and margin >= MIN_MARGIN]
    evidence = {
        "sampled_frames": len(scores),
        "positive_scores": [round(x, 3) for x in positives],
        "negative_margins": [round(x, 3) for x in margins],
        "passing_frame_count": len(passing),
        "identity_matches": {},
        "model_id": MODEL_ID,
    }
    if len(passing) < 2:
        return {**evidence, "accepted": False, "reason": "FRAMES_DO_NOT_SHOW_SUBJECT"}
    for name in required_names:
        identities = reference_scores.get(name) or []
        if not identities or len(identities) != len(scores):
            return {**evidence, "accepted": False, "reason": "MISSING_IDENTITY_REFERENCE",
                    "identity_missing": name}
        values = [max(map(float, row)) if row else 0 for row in identities]
        verified = sum(x >= MIN_IDENTITY for x in values)
        evidence["identity_matches"][name] = {"similarity": [round(x, 3) for x in values],
                                               "matching_frames": verified}
        if verified < 2:
            return {**evidence, "accepted": False,
                    "reason": "CHARACTER_OR_OBJECT_NOT_VISIBLE", "identity_missing": name}
    return {**evidence, "accepted": True,
            "reason": "FRAME_SIMILARITY_PASS_REVIEW_REQUIRED"}


def inspect_clip(clip, narration, topic, visual_hint="", library=None, required_names=None):
    """Fail closed on missing model/frames/references; never certify copyright."""
    if library is None:
        from scene_library import LIBRARY
        library = LIBRARY
    # A character merely MENTIONED in the narration is not necessarily the
    # subject of this shot (e.g., narration names a person while showing a map).
    # Enforce identity only when the visual plan or explicit entity list requires it.
    if required_names is None:
        names = proper_names(visual_hint) if visual_hint else []
    elif isinstance(required_names, str):
        names = [required_names.strip()] if required_names.strip() else []
    elif isinstance(required_names, list) and all(isinstance(n, str) for n in required_names):
        names = [n.strip() for n in required_names if n.strip()]
    else:
        raise ValueError("visual_entities must be a list of names or a single name")
    names = list(dict.fromkeys(names))
    mentioned = proper_names(narration)
    references = reference_images(library, names)
    missing = [n for n in names if not references.get(n)]
    if missing:
        return {"accepted": False, "reason": "MISSING_IDENTITY_REFERENCE",
                "identity_missing": missing, "sampled_frames": 0,
                "model_id": MODEL_ID}
    frames = sample_frames(clip)
    visual = (visual_hint or narration).strip()[:160]
    context = topic.strip()[:100]
    positives = (
        f"An actual scene showing {visual}, in {context}." if context else
        f"An actual scene showing {visual}.")
    scores, refs = score_images(frames, (positives, *NEGATIVE_PROMPTS), references)
    return {**decide_visual(scores, refs, names),
            "visual_prompt": positives, "required_entities": names,
            "mentioned_entities_not_claimed_visible": [
                name for name in mentioned if name not in names],
            "identity_detection": ("reference_image_comparison" if names
                                   else "no_identity_assertion"),
            "source": "sampled_video_frames", "rights_verified": False}
