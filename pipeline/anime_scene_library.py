"""JJK source-aware scene library, local permissioned footage only.

Episodes are factual metadata, not evidence of a precise cut. SRT-derived
timestamps are *candidates* until the owner approves a matching scene.
No scraping of streaming services, DRM bypass, or fabricated rights checks.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from common import ROOT

LIBRARY = Path(os.environ.get("BOURIKO_ANIME_LIBRARY", str(Path.home() / "Videos" / "BourikoAnime"))).expanduser()
EPISODE_INDEX = ROOT / "data" / "jjk_episode_index.json"
STOP = {"a", "an", "the", "in", "and", "or", "is", "are", "to", "of", "for", "with", "who",
        "what", "when", "why", "how", "this", "that", "there", "their", "them", "they", "into",
        "from", "but", "can", "be", "have", "has", "would", "because", "people", "game"}
ALIASES = {
    "culling": "culling", "colonies": "colony", "players": "player", "rules": "rule",
    "sorcerers": "sorcerer", "kenjaku": "kenjaku", "itadori": "yuji", "fushiguro": "megumi",
    "megumi": "megumi", "yuji": "yuji", "points": "point", "killing": "kill",
    "killed": "kill", "violence": "kill", "techniques": "technique",
}
BEATS = [
    ("opening", "deadly ritual and the culling game"),
    ("kenjaku", "kenjaku establishes the culling game"),
    ("colonies", "japan culling game colonies"),
    ("points", "sorcerer five points non sorcerer one point"),
    ("rule_change", "one hundred points add game rule"),
    ("rule_limit", "cannot cancel culling game rule"),
    ("participation", "participate or lose cursed technique"),
    ("scoreboard", "violence and culling game scoreboard"),
    ("yuji_megumi", "yuji megumi navigate rules protect others"),
    ("allies", "allies colonies and rules"),
    ("not_tournament", "culling game deadly tournament"),
    ("kenjaku_plan", "kenjaku larger plan"),
]


def terms(value):
    return {ALIASES.get(word, word) for word in re.findall(r"[a-z0-9]+", str(value).lower())
            if word not in STOP and len(word) > 2}


def library_path(value):
    """Only read source assets within the private library folder."""
    base = LIBRARY.resolve()
    target = (base / value).resolve()
    if target == base or base not in target.parents:
        raise ValueError("Source path must stay inside BOURIKO_ANIME_LIBRARY")
    return target


def catalog_path():
    return LIBRARY / "catalog.json"


def load_catalog():
    path = catalog_path()
    if not path.is_file():
        return {"version": 1, "scenes": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("scenes"), list):
        raise ValueError("Invalid anime scene catalog")
    return data


def save_catalog(catalog):
    LIBRARY.mkdir(parents=True, exist_ok=True)
    path = catalog_path()
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def episodes():
    return json.loads(EPISODE_INDEX.read_text(encoding="utf-8"))["episodes"]


def episode_for(season, episode):
    return next((x for x in episodes() if x["season"] == season and x["episode"] == episode), None)


def timestamp(raw):
    parts = raw.strip().replace(",", ".").split(":")
    if len(parts) not in (1, 2, 3):
        raise ValueError("Use SS, MM:SS or HH:MM:SS timestamps")
    try:
        return float(parts[-1]) + (60 * int(parts[-2]) if len(parts) >= 2 else 0) + (3600 * int(parts[-3]) if len(parts) == 3 else 0)
    except ValueError as exc:
        raise ValueError("Invalid timestamp") from exc


def subtitle_candidates(path):
    """Read SRT/VTT cue timing as research candidates, never as approved cuts."""
    data = path.read_text(encoding="utf-8-sig", errors="replace")
    pattern = re.compile(r"(?m)^\s*(\d{2}:)?\d{2}:\d{2}[,.]\d{3}\s*-->\s*(?:\d{2}:)?\d{2}:\d{2}[,.]\d{3}[^\n]*\n")
    matches = list(pattern.finditer(data))
    cues = []
    for idx, match in enumerate(matches):
        head = match.group().strip().split("-->")
        start = timestamp(head[0])
        end = timestamp(head[1].split()[0])
        body = data[match.end():(matches[idx + 1].start() if idx + 1 < len(matches) else len(data))]
        words = " ".join(re.sub(r"<[^>]*>", "", body).split())
        if 0 < end - start <= 12 and terms(words):
            cues.append({"start": start, "end": end, "description": words[:300]})
    return cues


def add_scene(source, season, episode, start, end, description, tags, beat_ids,
              rights_reference, approved=False, scene_id=None):
    video = library_path(source)
    if not video.is_file() or video.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
        raise ValueError("A supported, locally available episode/video file is required")
    meta = episode_for(season, episode)
    if meta is None:
        raise ValueError("Unknown season/episode. Check the official episode index")
    if not rights_reference.strip():
        raise ValueError("Document the reuse authorization or review basis; do not assume licensing")
    if not (0 <= start < end and 0.5 <= end - start <= 12):
        raise ValueError("A scene must be between 0.5 and 12 seconds")
    scene_id = scene_id or hashlib.sha256(f"{source}:{start}:{end}".encode()).hexdigest()[:16]
    scene = {
        "id": scene_id, "series": "jujutsu_kaisen", "season": season,
        "episode": episode, "overall_episode": meta["overall_episode"],
        "episode_title": meta["title"], "source_file": str(video.relative_to(LIBRARY.resolve())).replace("\\", "/"),
        "start_seconds": start, "end_seconds": end, "description": description,
        "tags": [str(x).strip() for x in tags if str(x).strip()],
        "beat_ids": list(beat_ids), "rights_reference": rights_reference.strip(),
        "approved": bool(approved),
        "review_status": "owner_approved" if approved else "candidate_needs_scene_review",
    }
    catalog = load_catalog()
    if any(s.get("id") == scene_id for s in catalog["scenes"]):
        raise ValueError("Duplicate scene ID, choose another")
    catalog["scenes"].append(scene)
    save_catalog(catalog)
    return scene


def scene_score(scene, narration, beat_id, description):
    if beat_id in scene.get("beat_ids", []):
        return 20.0
    wanted = terms(narration) | terms(description)
    identity = terms(" ".join(scene.get("tags", [])) + " " + scene.get("description", ""))
    common = wanted & identity
    if len(common) < 2:
        return 0.0
    return len(common) / max(len(wanted), 3)


def eligible_scenes():
    return [s for s in load_catalog()["scenes"]
            if s.get("series") == "jujutsu_kaisen"
            and s.get("approved") is True
            and s.get("rights_reference")
            and s.get("start_seconds") is not None
            and s.get("end_seconds") is not None]


def choose_scene(narration, index, used=None):
    used = used or set()
    beat_id, description = BEATS[index] if index < len(BEATS) else (f"beat_{index}", narration)
    options = []
    for scene in eligible_scenes():
        if scene["id"] in used:
            continue
        score = scene_score(scene, narration, beat_id, description)
        if score >= 0.35 or score >= 20:
            options.append((score, scene))
    return max(options, key=lambda x: x[0])[1] if options else None


def clip_scene(scene, index):
    src = library_path(scene["source_file"])
    if not src.is_file():
        raise ValueError(f"Missing owner-provided scene source: {src.name}")
    start = float(scene["start_seconds"])
    end = float(scene["end_seconds"])
    if not (0 <= start < end and 0.5 <= end - start <= 12):
        raise ValueError("Invalid approved trim range")
    target = ROOT / "output" / "media" / f"{index:02}_jjk_s{scene['season']:02}e{scene['episode']:02}_{scene['id']}.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start),
         "-i", str(src), "-t", str(end - start), "-an", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-movflags", "+faststart", str(target)],
        check=True, timeout=120,
    )
    if not target.is_file() or target.stat().st_size < 2048:
        raise RuntimeError("Trimmed clip is empty")
    return target


def populate_jjk(story):
    """Fail closed: no irrelevant stock or diagram substitutes for real JJK beats."""
    lines = story.get("lines", [])
    if not lines:
        raise ValueError("JJK story is empty")
    records, used, missing = [], set(), []
    for i, line in enumerate(lines):
        scene = choose_scene(line["text"], i, used)
        if not scene:
            beat = BEATS[i][0] if i < len(BEATS) else f"beat_{i}"
            missing.append(f"{i:02} {beat}: {line['text'][:95]}")
            continue
        used.add(scene["id"])
        target = clip_scene(scene, i)
        record = {
            "index": i, "kind": "video", "provider": "anime_scene_library",
            "query": line["text"], "local_path": target.relative_to(ROOT).as_posix(),
            "series": scene["series"], "scene_id": scene["id"],
            "season": scene["season"], "episode": scene["episode"],
            "overall_episode": scene["overall_episode"], "episode_title": scene["episode_title"],
            "trim_start_seconds": scene["start_seconds"], "trim_end_seconds": scene["end_seconds"],
            "description": scene["description"], "source_file_name": Path(scene["source_file"]).name,
            "license": "Owner-approved source; rights documentation requires human review",
            "rights_reference": scene["rights_reference"], "rights_verified": False,
            "semantic_role": "jjk_approved_scene", "scene_reviewed": True,
        }
        line["media_asset"] = record["local_path"]
        line["media_kind"] = "video"
        line["media_source"] = record
        records.append(record)
    if missing:
        for record in records:
            (ROOT / record["local_path"]).unlink(missing_ok=True)
        raise RuntimeError(
            "JJK footage library incomplete. Add approved scene cuts in "
            f"{catalog_path()} instead of generic placeholders:\n" + "\n".join(missing)
        )
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    (output / "media_manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (output / "story.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
    print(f"JJK library: {len(records)} precise, reviewed trims; publication rights remain review-required")


def online_candidates(query, limit=10):
    """Discover JJK clip titles and source URLs, never download or assert reuse rights."""
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("Install yt-dlp to search public clip metadata") from exc
    search_text = "Jujutsu Kaisen " + query
    options = {"quiet": True, "no_warnings": True, "skip_download": True,
               "extract_flat": "in_playlist", "ignoreerrors": True,
               "playlistend": limit}
    with yt_dlp.YoutubeDL(options) as ydl:
        data = ydl.extract_info("ytsearch" + str(limit) + ":" + search_text, download=False)
    results = []
    for item in (data or {}).get("entries", []):
        if not item:
            continue
        title = str(item.get("title") or "")
        overlap = len(terms(query) & terms(title))
        if overlap < 1 or not ({"jujutsu", "kaisen", "jjk"} & terms(title)):
            continue
        video_id = str(item.get("id") or "")
        url = item.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
        results.append({"title": title, "url": url, "channel": item.get("channel") or item.get("uploader"),
                        "duration": item.get("duration"), "query": search_text,
                        "keyword_overlap": overlap, "rights_status": "unverified",
                        "episode_and_scene_timestamps_verified": False})
    results.sort(key=lambda item: item["keyword_overlap"], reverse=True)
    LIBRARY.mkdir(parents=True, exist_ok=True)
    (LIBRARY / "discovery.json").write_text(json.dumps({
        "query": search_text, "review_only": True, "candidates": results
    }, indent=2), encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description="Private JJK episode scene index, no streaming-site scraping")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("episodes")
    discover = sub.add_parser("discover", help="Search public JJK clip metadata, no automatic downloading")
    discover.add_argument("query")
    discover.add_argument("--limit", type=int, default=10)
    listing = sub.add_parser("suggest")
    listing.add_argument("text")
    reg = sub.add_parser("add")
    reg.add_argument("--source", required=True, help="File relative to private library root")
    reg.add_argument("--season", type=int, required=True)
    reg.add_argument("--episode", type=int, required=True)
    reg.add_argument("--start", required=True)
    reg.add_argument("--end", required=True)
    reg.add_argument("--description", required=True)
    reg.add_argument("--tag", action="append", default=[])
    reg.add_argument("--beat", action="append", default=[])
    reg.add_argument("--rights-reference", required=True)
    reg.add_argument("--approve", action="store_true", help="Owner reviewed the exact frames and trim")
    reg.add_argument("--scene-id")
    propose = sub.add_parser("propose", help="Rank subtitle cues by narration beat; candidates need approval")
    propose.add_argument("--source", required=True)
    propose.add_argument("--season", type=int, required=True)
    propose.add_argument("--episode", type=int, required=True)
    propose.add_argument("--subtitles", required=True)
    propose.add_argument("--rights-reference", required=True)
    approve = sub.add_parser("approve", help="Approve a visually reviewed candidate with documented usage basis")
    approve.add_argument("--scene-id", required=True)
    cues = sub.add_parser("subtitles")
    cues.add_argument("--file", required=True)
    args = parser.parse_args()
    if args.command == "episodes":
        for e in episodes():
            print(f"S{e['season']:02}E{e['episode']:02} (overall {e['overall_episode']}): {e['title']}")
    elif args.command == "discover":
        for row in online_candidates(args.query, max(1, min(20, args.limit))):
            print(json.dumps(row, ensure_ascii=False))
        print("DISCOVERY ONLY: public visibility does not prove permission to reuse or episode timing")
    elif args.command == "suggest":
        for i, e in enumerate(BEATS):
            score = len(terms(args.text) & terms(e[1]))
            if score:
                print(f"{e[0]} | keywords matched: {score} | {e[1]}")
        print(f"Official episode index: {EPISODE_INDEX}. Precise timestamps require source footage/subtitles.")
    elif args.command == "propose":
        video = library_path(args.source)
        if not video.is_file():
            raise ValueError("Source video is missing")
        suggestions = subtitle_candidates(Path(args.subtitles))
        recorded = 0
        for beat_id, description in BEATS:
            matches = [(scene_score({"tags": [], "description": c["description"]},
                                    description, beat_id, description), c) for c in suggestions]
            matches = [(score, cue) for score, cue in matches if score >= 0.30]
            if not matches:
                continue
            score, cue = max(matches, key=lambda x: x[0])
            start = max(0, cue["start"] - 0.4)
            end = min(start + 8, max(cue["end"] + 1.5, start + 0.5))
            scene = add_scene(args.source, args.season, args.episode, start, end,
                              cue["description"], [description], [beat_id],
                              args.rights_reference, approved=False,
                              scene_id=f"{video.stem}_{beat_id}_{int(start * 1000)}")
            print(f"CANDIDATE (NOT APPROVED): {beat_id} => {scene['id']} "
                  f"S{args.season}E{args.episode} {start:.2f}-{end:.2f}s")
            recorded += 1
        print(f"Proposed {recorded} subtitle-matched cuts; preview and approve each exact cut before use")
    elif args.command == "approve":
        catalog = load_catalog()
        scene = next((item for item in catalog["scenes"] if item.get("id") == args.scene_id), None)
        if scene is None:
            raise ValueError("Unknown scene ID")
        if not library_path(scene["source_file"]).is_file() or not scene.get("rights_reference"):
            raise ValueError("Source video or rights documentation missing")
        scene["approved"] = True
        scene["review_status"] = "owner_approved"
        save_catalog(catalog)
        print(f"Approved scene {args.scene_id}; publishing still requires separate rights review")
    elif args.command == "subtitles":
        for cue in subtitle_candidates(Path(args.file)):
            print(json.dumps({**cue, "approved": False}))
    elif args.command == "add":
        record = add_scene(args.source, args.season, args.episode, timestamp(args.start),
                           timestamp(args.end), args.description, args.tag, args.beat,
                           args.rights_reference, args.approve, args.scene_id)
        print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
