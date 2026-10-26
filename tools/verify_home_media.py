#!/usr/bin/env python3
"""Verify Bouriko's self-hosted-media -> hosted-render artifact handoff.

The receipt binds the generated story to the exact media bytes. This is not
semantic footage approval or a substitute for confirming reuse rights.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from media import usable_media_file

OUTPUT = ROOT / "output"
STORY = OUTPUT / "story.json"
MANIFEST = OUTPUT / "media_manifest.json"
RECEIPT = OUTPUT / "home_media_receipt.json"


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_path(value):
    path = (ROOT / value).resolve()
    if path == ROOT or ROOT not in path.parents:
        raise ValueError(f"Media path escapes repository: {value!r}")
    if not path.is_file():
        raise ValueError(f"Missing media: {value!r}")
    return path


def audit(min_youtube=1):
    story = json.loads(STORY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(manifest, list) or not manifest:
        raise ValueError("Media manifest is empty or invalid")
    if story.get("media_strategy") == "youtube_scene_library":
        if len(manifest) != len(story.get("lines", [])):
            raise ValueError("Scene library did not match every narration beat")
        for i, rec in enumerate(manifest):
            if (rec.get("index") != i
                    or rec.get("provider") != "youtube_cc_scene"
                    or rec.get("semantic_status") != "TRANSCRIPT_MATCH_FRAME_REVIEW_REQUIRED"
                    or not rec.get("transcript_excerpt")
                    or not isinstance(rec.get("scene_start_seconds"), (int, float))
                    or not isinstance(rec.get("scene_end_seconds"), (int, float))
                    or not 0 <= rec["scene_start_seconds"] < rec["scene_end_seconds"]
                    or rec["scene_end_seconds"] - rec["scene_start_seconds"] > 10):
                raise ValueError(f"Missing scene evidence/timecode for beat {i}")
    index = {}
    files = {}
    for record in manifest:
        name = record.get("local_path")
        kind = record.get("kind")
        if not name or kind not in ("image", "video"):
            raise ValueError("Manifest contains missing path or invalid media kind")
        path = safe_path(name)
        if not usable_media_file(path, kind):
            raise ValueError(f"Invalid or unsupported {kind}: {name}")
        files[name] = checksum(path)
        index[name] = record

    for scene_number, line in enumerate(story.get("lines", [])):
        name = line.get("media_asset")
        if not name or name not in index:
            raise ValueError(f"Scene {scene_number} missing acquired media")
        if line.get("media_asset_2") and line["media_asset_2"] not in index:
            raise ValueError(f"Scene {scene_number} secondary media absent from manifest")

    youtube = [r for r in manifest if r.get("provider") in {"youtube_cc", "youtube_cc_scene"}]
    for item in youtube:
        if "creative commons attribution" not in str(item.get("license", "")).lower():
            raise ValueError("YouTube clip missing explicit CC BY metadata")
        if not str(item.get("source_url", "")).startswith("https://"):
            raise ValueError("YouTube clip missing traceable source URL")
    if len(youtube) < min_youtube:
        raise ValueError(f"Expected >= {min_youtube} verified-playable YouTube CC clips; got {len(youtube)}")

    return {"version": 1, "story_sha256": checksum(STORY),
            "file_sha256": files, "youtube_count": len(youtube),
            "media_count": len(manifest),
            "youtube_sources": [r["source_url"] for r in youtube],
            "review_status": "PROVISIONAL_NOT_SEMANTICALLY_VERIFIED"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("create", "check"), required=True)
    parser.add_argument("--min-youtube", type=int, default=1)
    args = parser.parse_args()
    report = audit(min_youtube=args.min_youtube)
    if args.mode == "create":
        RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    else:
        previous = json.loads(RECEIPT.read_text(encoding="utf-8"))
        if report != previous:
            raise ValueError("Home-media receipt mismatch after artifact transfer")
    print(f"PASS: {report['media_count']} playable media files, "
          f"{report['youtube_count']} licensed YouTube clips; "
          f"artifact hashes match ({args.mode})")
    print("REVIEW REQUIRED: media suitability is not automatically approved.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"HOME MEDIA HANDOFF FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
