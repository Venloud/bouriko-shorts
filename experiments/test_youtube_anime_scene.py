"""Search YouTube for anime trailers, download a short section and validate an MP4.

Use for footage you have permission to reuse. No DRM, login or access bypass.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "youtube_scene_test"
def run(command, timeout=120):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-2500:])
    return result.stdout

def discover(query, limit=5):
    raw = run(["yt-dlp", "--no-playlist", "--dump-single-json",
               "--flat-playlist", f"ytsearch{limit}:{query}"], timeout=90)
    data = json.loads(raw)
    candidates = []
    for entry in data.get("entries") or []:
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            continue
        candidates.append({"title": entry.get("title"), "channel": entry.get("channel") or entry.get("uploader"),
                           "url": "https://www.youtube.com/watch?v=" + video_id, "id": video_id})
    return candidates

def validate(path):
    raw = run(["ffprobe", "-v", "error", "-show_entries",
               "format=duration,size:stream=codec_type,width,height",
               "-of", "json", str(path)], timeout=30)
    info = json.loads(raw)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    duration = float(info.get("format", {}).get("duration", 0))
    if not video or duration < 0.5 or path.stat().st_size < 5000:
        raise RuntimeError("Downloaded section is not a usable video")
    return {"duration": duration, "bytes": path.stat().st_size,
            "width": video.get("width"), "height": video.get("height")}

def keywords(script):
    stop = {"the","and","that","with","from","this","into","when","where","have","will","they","them","about","what","then","there","after","before","story","scene"}
    return list(dict.fromkeys(w.lower() for w in re.findall(r"[A-Za-z]{4,}", script) if w.lower() not in stop))

def score_candidate(candidate, script):
    title = (candidate.get("title") or "").lower()
    channel = (candidate.get("channel") or "").lower()
    words = keywords(script)
    hits = [w for w in words if re.search(r"(?<!\\w)" + re.escape(w) + r"(?!\\w)", title)]
    score = len(hits) * 3
    if "official" in title: score += 3
    if "trailer" in title or "pv" in title: score += 2
    if "toho" in channel: score += 4
    if "reaction" in title or "fan made" in title: score -= 8
    return score, hits

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--query", default="", help="Optional search override")
    p.add_argument("--script", default="", help="Narration or story to match footage against")
    p.add_argument("--script-file", type=Path, help="UTF-8 story/narration file")
    p.add_argument("--url", default="", help="Optional explicit video URL; bypasses search selection")
    p.add_argument("--start", type=float, default=10)
    p.add_argument("--duration", type=float, default=5)
    p.add_argument("--search-only", action="store_true")
    args = p.parse_args()
    if args.start < 0 or not 0.5 <= args.duration <= 20:
        p.error("start must be nonnegative; duration must be between 0.5 and 20 seconds")
    script = args.script_file.read_text(encoding="utf-8") if args.script_file else args.script
    if not (args.query.strip() or script.strip() or args.url.strip()):
        p.error("Provide --script, --script-file, --query or --url")
    query = args.query or (" ".join(keywords(script)[:9]) + " anime official trailer" if script.strip() else "")
    if not query.strip() and not args.url:
        p.error("Provide --script, --script-file, --query or --url")
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"query": query, "script": script, "start": args.start, "requested_duration": args.duration}
    try:
        report["candidates"] = discover(query, limit=10)
        for candidate in report["candidates"]:
            candidate["relevance_score"], candidate["matched_terms"] = score_candidate(candidate, script or query)
        report["candidates"].sort(key=lambda x: x["relevance_score"], reverse=True)
    except Exception as exc:
        report["search_error"] = str(exc)
        report["candidates"] = []
    if args.search_only:
        report["status"] = "search_complete" if report["candidates"] else "search_failed"
    else:
        selected = args.url or next((x["url"] for x in report["candidates"]), "")
        report["selected_url"] = selected
        report["selection_method"] = "explicit_url" if args.url else "ranked_search_result"
        if not selected:
            report["status"] = "no_source"
        else:
            # The downloaded section is only a candidate until ffprobe verifies real video frames.
            end = args.start + args.duration
            template = str(OUT / "downloaded_section.%(ext)s")
            try:
                run(["yt-dlp", "--no-playlist", "--no-progress", "--socket-timeout", "20",
                     "--retries", "2", "--download-sections", f"*{args.start}-{end}",
                     "--force-keyframes-at-cuts", "-f", "bv*[height<=720]+ba/b[height<=720]/best",
                     "--merge-output-format", "mp4", "--recode-video", "mp4",
                     "-o", template, selected], timeout=240)
                files = sorted(OUT.glob("downloaded_section.*"), key=lambda x: x.stat().st_mtime, reverse=True)
                files = [x for x in files if x.suffix.lower() in {".mp4", ".mkv", ".webm"}]
                if not files:
                    raise RuntimeError("Downloader returned success without a video file")
                source = files[0]
                final = OUT / "anime_scene_clip.mp4"
                run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-i", str(source), "-t", str(args.duration),
                     "-vf", "scale=720:-2", "-an", "-c:v", "libx264", "-preset", "veryfast",
                     "-crf", "24", "-movflags", "+faststart", str(final)], timeout=120)
                report["video"] = {"file": str(final.relative_to(ROOT)), **validate(final)}
                report["status"] = "video_downloaded_and_extracted"
            except Exception as exc:
                report["status"] = "download_or_extract_failed"
                report["error"] = str(exc)
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    if report["status"] not in {"video_downloaded_and_extracted", "search_complete"}:
        raise SystemExit(1)
if __name__ == "__main__":
    main()
