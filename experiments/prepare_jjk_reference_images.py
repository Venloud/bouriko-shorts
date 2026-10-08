"""Review-only JJK image acquisition, narration-first candidate selection.

Do not silently replace requested real character images with neon graphics.
Character images from Jikan are third-party references, NOT publish-cleared.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
CHARACTERS = {
    "Kenjaku": ["Kenjaku"],
    "YUJI AND MEGUMI": ["Yuji Itadori", "Megumi Fushiguro"],
    "GAME MASTER": ["Kogane"],
}
TIMEOUT = (8, 18)
USER_AGENT = "BourikoJJKReview/1.1 (anime character reference experiment)"

def get_json(session, url):
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()

def fetch_character(session, name):
    # Search by canonical character name; don't silently accept a similar character.
    data = get_json(session, "https://api.jikan.moe/v4/characters?q=" + quote(name) + "&limit=10")
    for item in data.get("data", []):
        if item.get("name", "").casefold() != name.casefold():
            continue
        jpg = (item.get("images") or {}).get("jpg") or {}
        url = jpg.get("large_image_url") or jpg.get("image_url")
        if not url:
            continue
        response = session.get(url, timeout=TIMEOUT)
        response.raise_for_status()
        if not response.headers.get("content-type", "").lower().startswith("image/"):
            raise RuntimeError("Image endpoint did not return image content")
        if len(response.content) < 2000:
            raise RuntimeError("Image payload too small")
        return response.content, url, item.get("url")
    return None

def fetch_local_character(name):
    """Offline fallback: vetted user-supplied stills plus sidecar metadata."""
    folder = ROOT / "assets" / "anime" / "jujutsu_kaisen"
    stem = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        file = folder / (stem + suffix)
        sidecar = folder / (stem + suffix + ".json")
        if not file.is_file() or not sidecar.is_file():
            continue
        meta = json.loads(sidecar.read_text())
        if meta.get("character", "").casefold() != name.casefold():
            continue
        if meta.get("rights_status") not in {"licensed", "user_supplied_review_only"}:
            continue
        if not meta.get("source_url"):
            continue
        return file.read_bytes(), meta["source_url"], meta["source_url"]
    return None

def choose_media(line, candidates, recent_media, index):
    visual_type = line.get("anime_visual_type", "")
    if visual_type in {"animated_map", "animated_counter", "animated_timer", "energy_diagram", "blackboard"}:
        return None, "diagram_explains_better"
    if not candidates:
        return None, "no_exact_character_match"
    if recent_media and index - recent_media[-1] <= 1:
        return None, "avoid_media_spam"
    return candidates[0], "character_match"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    story_path = OUT / "story.json"
    story = json.loads(story_path.read_text())
    media_dir = OUT / "anime_images"
    media_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    cache, failures, manifest, matches, catalog, recent = {}, [], [], [], [], []
    for index, line in enumerate(story["lines"]):
        names = CHARACTERS.get(line.get("visual", ""), [])
        candidates = []
        for name in names:
            if name not in cache:
                try:
                    cache[name] = fetch_local_character(name) or fetch_character(session, name)
                except (requests.RequestException, ValueError, RuntimeError) as exc:
                    failures.append({"character": name, "error": str(exc)[:500]})
                    print(f"MEDIA FETCH FAILED: {name}: {type(exc).__name__}: {exc}", flush=True)
                    cache[name] = None
                time.sleep(0.5)
            result = cache[name]
            if not result:
                continue
            raw, image_url, source_url = result
            digest = hashlib.sha256(raw).hexdigest()
            filename = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + "_" + digest[:12] + ".jpg"
            target = media_dir / filename
            target.write_bytes(raw)
            candidates.append({
                "scene": index, "kind": "image", "provider": "jikan_character_reference",
                "media_id": "sha256:" + digest, "character": name,
                "path": str(target.relative_to(ROOT)), "source_url": source_url,
                "image_url": image_url, "season": None, "episode": None,
                "timestamp_seconds": None, "rights_status": "review_only_unlicensed",
                "reviewed": False
            })
        selected, reason = choose_media(line, candidates, recent, index)
        catalog.append({"scene": index, "narration": line["text"], "candidates": candidates,
                        "selected_media_id": selected["media_id"] if selected else None,
                        "selection_reason": reason})
        if selected:
            recent.append(index)
            line["media_kind"] = "image"
            line["media_asset"] = selected["path"]
            line["media_caller_id"] = selected["media_id"]
            manifest.append(selected)
            matches.append({"scene": index, "status": "reference_image",
                            "character": selected["character"], "media_id": selected["media_id"]})
        else:
            line["media_kind"] = "motion_graphic"
            line.pop("media_asset", None)
            line.pop("media_caller_id", None)
            manifest.append({"scene": index, "kind": "motion_graphic",
                             "provider": "remotion", "visual_type": line.get("anime_visual_type")})
            matches.append({"scene": index, "status": "graphic", "reason": reason})
    (OUT / "media_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    (OUT / "media_fetch_failures.json").write_text(json.dumps(failures, indent=2) + "\n")
    (OUT / "media_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "scene_matches.json").write_text(json.dumps(matches, indent=2) + "\n")
    story_path.write_text(json.dumps(story, indent=2) + "\n")
    images = sum(item["kind"] == "image" for item in manifest)
    print(f"IMAGE PREFLIGHT: {images} selected character-image scenes / {len(manifest)} scenes", flush=True)
    if images == 0:
        raise SystemExit(
            "MEDIA QA FAILED: zero real character images retrieved. "
            "Do not render a graphics-only build as an image-integrated success. "
            "Check runner outbound HTTPS/DNS access to api.jikan.moe and image CDN; "
            "see output/media_fetch_failures.json. "
            "Alternative: provide approved character images in a durable media store."
        )

if __name__ == "__main__":
    main()
