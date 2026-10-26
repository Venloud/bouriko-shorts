"""Reusable YouTube shot index: title/topic discovery, caption timecodes, trimmed clips.

This is general-purpose: anime, sports, technology, history, games, etc.
Transcript overlap proposes likely *spoken-about* moments; it does NOT prove
what frames depict, a video's episode metadata, or redistribution rights.
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import requests

from common import ROOT

LIBRARY = Path(os.environ.get(
    "BOURIKO_SCENE_LIBRARY", str(Path.home() / "Videos" / "BourikoSceneLibrary")
)).expanduser()
INDEX = LIBRARY / "index.json"
STOP = {"about", "after", "also", "and", "are", "before", "because", "been",
        "could", "does", "each", "from", "have", "into", "just", "like", "more",
        "much", "only", "other", "over", "same", "some", "that", "them", "then",
        "there", "these", "this", "those", "through", "very", "what", "when",
        "where", "which", "while", "with", "would", "your", "their", "they"}
ALIASES = {"jjk": "jujutsu", "kaisen": "jujutsu", "culling": "culling",
           "colonies": "colony", "players": "player", "rules": "rule",
           "sorcerers": "sorcerer", "satellites": "satellite",
           "phones": "phone", "controllers": "controller",
           "points": "point", "signals": "signal", "techniques": "technique"}


def words(text):
    return {ALIASES.get(x, x) for x in re.findall(r"[a-z0-9]+", str(text).lower())
            if len(x) >= 3 and x not in STOP}


def _time(value):
    parts = value.replace(",", ".").strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError("Subtitle timecode must be MM:SS or HH:MM:SS")
    return float(parts[-1]) + 60 * int(parts[-2]) + (
        3600 * int(parts[-3]) if len(parts) == 3 else 0)


def parse_captions(raw, ext="vtt"):
    """Parse official subtitle timing, not video frame content. Handles VTT and JSON3."""
    cues = []
    if ext == "json3":
        for e in json.loads(raw).get("events", []):
            text = " ".join(str(x.get("utf8") or "") for x in e.get("segs", []))
            start = float(e.get("tStartMs") or 0) / 1000.0
            dur = float(e.get("dDurationMs") or 0) / 1000.0
            if dur > 0 and words(text):
                cues.append({"start": start, "end": start + dur, "text": text.strip()})
        return cues
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text)
    pattern = re.compile(
        r"(?P<start>(?:\d{2}:)?\d{2}:\d{2}[,.]\d{3})"
        r"\s*-->\s*(?P<end>(?:\d{2}:)?\d{2}:\d{2}[,.]\d{3})"
    )
    for block in blocks:
        match = pattern.search(block)
        if not match:
            continue
        start, end = _time(match["start"]), _time(match["end"])
        body = block[match.end():]
        body = re.sub(r"<[^>]+>", "", body)
        body = re.sub(r"&(?:amp|gt|lt|nbsp);", " ", body)
        phrase = " ".join(body.split()).strip()
        if 0 < end - start < 40 and words(phrase):
            cues.append({"start": start, "end": end, "text": phrase})
    return cues


def best_caption_span(cues, narration, max_seconds=8):
    """Rank consecutive subtitle groups by concrete word overlap; no fake timecodes."""
    target = words(narration)
    if len(target) < 2:
        return None
    best = None
    for i, cue in enumerate(cues):
        for n in range(1, 5):
            subset = cues[i:i + n]
            if len(subset) != n:
                continue
            start, end = subset[0]["start"], subset[-1]["end"]
            if start < 0 or end <= start or end - start > max_seconds:
                break
            context = words(" ".join(c["text"] for c in subset))
            overlap = len(context & target)
            score = overlap / max(3, len(target))
            # Two distinct concrete words, never just "game" or "video".
            if overlap < 2 or score < 0.26:
                continue
            current = {"start": max(0, start - 0.3), "end": end + 0.3,
                       "transcript_excerpt": " ".join(c["text"] for c in subset)[:450],
                       "overlap_words": overlap, "score": round(score, 3)}
            if best is None or (score, overlap) > (best["score"], best["overlap_words"]):
                best = current
    return best


def episode_hints(title):
    """Hints only; never claim verified season/episode from a thumbnail or transcript."""
    title = str(title)
    match = re.search(r"\bS(\d{1,2})[\s._-]*E(\d{1,3})\b", title, re.I)
    if not match:
        match = re.search(r"\bseason\s*(\d{1,2})\W+episode\s*(\d{1,3})\b", title, re.I)
    return ({"season_hint": int(match.group(1)), "episode_hint": int(match.group(2)),
             "episode_hint_source": "video_title_unverified"}
            if match else {"season_hint": None, "episode_hint": None,
                           "episode_hint_source": None})


def subtitle_url(candidate):
    """No arbitrary URLs/SSRF: yt-dlp supplied caption tracks from YouTube only."""
    for field in ("subtitles", "automatic_captions"):
        tracks = candidate.get(field) or {}
        for lang in ("en", "en-US", "en-GB"):
            for entry in tracks.get(lang, []):
                ext, url = entry.get("ext"), entry.get("url") or ""
                host = (urlparse(url).hostname or "").lower()
                if (ext in ("vtt", "json3")
                        and urlparse(url).scheme == "https"
                        and (host == "youtube.com" or host.endswith(".youtube.com"))):
                    return url, ext, ("manual" if field == "subtitles" else "automatic")
    return None


def read_subtitles(candidate):
    track = subtitle_url(candidate)
    if not track:
        return [], "unavailable"
    url, ext, origin = track
    try:
        response = requests.get(url, timeout=25,
                                headers={"User-Agent": "Bouriko scene research/1.0"})
        response.raise_for_status()
        if len(response.content) > 2_000_000:
            return [], "oversized"
        return parse_captions(response.text, ext), origin
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return [], "failed"


def query_score(candidate, subject):
    """Block unrelated videos even if a subtitle coincidentally mentions two words."""
    source = words((candidate.get("title") or "") + " " + (candidate.get("description") or "")[:260])
    target = words(subject)
    if not source or not target:
        return 0
    return len(source & target)


def choose_segment(candidates, narration, subject, used=None):
    """Return a caption-located candidate, or None. Never invent an offset."""
    used = used or set()
    matches = []
    for candidate in candidates:
        if candidate.get("provider") != "youtube_cc":
            continue
        if "creative commons attribution" not in str(candidate.get("license") or "").lower():
            continue
        if not candidate.get("url") or query_score(candidate, subject) < 1:
            continue
        # Reuse previously verified caption offsets, but only if the fresh
        # discovery still reports CC BY and the narration overlaps that cue.
        hit, origin = None, "unavailable"
        if INDEX.is_file():
            try:
                memory = json.loads(INDEX.read_text(encoding="utf-8"))
                for old in memory.get("scenes", []):
                    if old.get("source_url") != candidate["url"]:
                        continue
                    span = best_caption_span([{
                        "start": old.get("scene_start_seconds", 0),
                        "end": old.get("scene_end_seconds", 0),
                        "text": old.get("transcript_excerpt", ""),
                    }], narration)
                    if span:
                        hit, origin = span, old.get("caption_origin", "cached")
                        break
            except (OSError, ValueError, TypeError, KeyError):
                pass
        if not hit:
            cues, origin = read_subtitles(candidate)
            hit = best_caption_span(cues, narration)
        if not hit:
            continue
        source_key = candidate.get("youtube_id") or candidate["url"]
        start = round(hit["start"], 1)
        if (source_key, start) in used:
            continue
        result = dict(candidate)
        # Don't persist expiring caption URLs or entire subtitle response.
        for key in ("subtitles", "automatic_captions", "description"):
            result.pop(key, None)
        result.update(hit)
        result.update(episode_hints(candidate.get("title")))
        result["caption_origin"] = origin
        result["semantic_status"] = "TRANSCRIPT_MATCH_FRAME_REVIEW_REQUIRED"
        result["rights_status"] = "CC_BY_METADATA_OWNER_RIGHTS_UNVERIFIED"
        result["scene_start_seconds"] = start
        result["scene_end_seconds"] = round(hit["end"], 1)
        matches.append((hit["score"] + 0.02 * query_score(candidate, subject), result))
    if not matches:
        return None
    return max(matches, key=lambda x: x[0])[1]


def download_exact_excerpt(scene, index):
    """Fetch ONLY an explicit verified-timecode section; never full episode downloads."""
    try:
        import yt_dlp
        from yt_dlp.utils import download_range_func
    except ImportError as exc:
        raise RuntimeError("yt-dlp is required on the private acquisition runner") from exc

    output = ROOT / "output" / "media"
    output.mkdir(parents=True, exist_ok=True)
    clip_id = hashlib.sha256(
        (str(scene.get("youtube_id") or scene["url"]) + ":" +
         str(scene["scene_start_seconds"]) + ":" + str(scene["scene_end_seconds"]))
        .encode("utf-8")).hexdigest()[:14]
    path = output / f"{index:02}_scene_{clip_id}.mp4"
    if not path.is_file() or path.stat().st_size <= 2048:
        from yt_dlp import YoutubeDL
        start, end = scene["scene_start_seconds"], scene["scene_end_seconds"]
        if not (0 <= start < end <= start + 10):
            raise ValueError("Refusing invalid or overly long excerpt range")
        opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
                "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
                "merge_output_format": "mp4", "outtmpl": str(path.with_suffix(".%(ext)s")),
                "download_ranges": download_range_func(None, [(start, end)]),
                "force_keyframes_at_cuts": True,
                "js_runtimes": {"node": {}},
                "extractor_args": {"youtube": {"player_client": ["mweb", "tv", "web_safari"]}}}
        with YoutubeDL(opts) as dl:
            dl.download([scene["url"]])
        candidates = list(output.glob(path.stem + ".*"))
        if not path.is_file():
            for item in candidates:
                if item.suffix.lower() in (".mp4", ".mkv", ".webm"):
                    subprocess.run(
                        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                         "-i", str(item), "-an", "-c:v", "libx264", "-crf", "24",
                         "-preset", "veryfast", str(path)],
                        check=True, timeout=90)
                    item.unlink(missing_ok=True)
                    break
    if not path.is_file() or path.stat().st_size <= 2048:
        raise RuntimeError("No playable excerpt downloaded for reviewed segment")
    return path


def record_segment(scene, path, index, subject):
    """Store reusable scene metadata and source provenance, never auth/caption URLs."""
    ref = {"index": index, "kind": "video", "provider": "youtube_cc_scene",
           "query": subject, "title": scene.get("title"),
           "source_url": scene["url"], "url": scene["url"],
           "creator": scene.get("creator"), "license": scene.get("license"),
           "license_url": scene.get("license_url"), "youtube_id": scene.get("youtube_id"),
           "local_path": path.relative_to(ROOT).as_posix(),
           "scene_start_seconds": scene["scene_start_seconds"],
           "scene_end_seconds": scene["scene_end_seconds"],
           "transcript_excerpt": scene["transcript_excerpt"],
           "caption_origin": scene["caption_origin"],
           "semantic_status": scene["semantic_status"],
           "rights_status": scene["rights_status"], "rights_verified": False,
           **episode_hints(scene.get("title"))}
    LIBRARY.mkdir(parents=True, exist_ok=True)
    index_data = {"version": 1, "scenes": []}
    if INDEX.is_file():
        try:
            index_data = json.loads(INDEX.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    entries = index_data.get("scenes", [])
    if not isinstance(entries, list):
        entries = []
    identity = (ref["source_url"], ref["scene_start_seconds"], ref["scene_end_seconds"])
    if not any((i.get("source_url"), i.get("scene_start_seconds"),
                i.get("scene_end_seconds")) == identity for i in entries):
        entries.append({k: v for k, v in ref.items()
                        if k not in {"local_path", "index"}})
    new_path = INDEX.with_suffix(".tmp")
    entries = entries[-2000:]  # Bound persistent metadata size.
    new_path.write_text(json.dumps({"version": 1, "scenes": entries},
                                   indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(new_path, INDEX)
    return ref
