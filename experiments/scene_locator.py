"""Conservative, subtitle-grounded scene locator for licensed/local episode media.

Input: a JSON scene request plus episode subtitle files. No network downloading.
Only return a time range when subtitle evidence clears a confidence threshold.
Action-only scenes must be manually verified, never guessed.
"""
import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

STOP = set("the a an and or to of in is are was were that this with for on from it its you your they he she we but into at as by".split())


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOP


def seconds(clock):
    parts = re.split(r"[:,.]", clock.strip())
    if len(parts) != 4:
        raise ValueError("Invalid SRT time: " + clock)
    h, m, s, ms = map(int, parts)
    return h * 3600 + m * 60 + s + ms / 1000


def parse_srt(text):
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r", "").strip()):
        match = re.search(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})", block)
        if not match:
            continue
        start, end = seconds(match.group(1)), seconds(match.group(2))
        if end <= start:
            continue
        dialogue = re.sub(r"<[^>]*>", "", block[match.end():]).strip()
        if dialogue:
            cues.append({"start": start, "end": end, "text": dialogue})
    return cues


def score(query, dialogue):
    q, d = words(query), words(dialogue)
    if not q or not d:
        return 0.0
    overlap = len(q & d) / len(q)
    similarity = SequenceMatcher(None, " ".join(sorted(q)), " ".join(sorted(d))).ratio()
    return round(0.8 * overlap + 0.2 * similarity, 4)


def locate(scene, episodes, threshold=0.62, margin=1.5):
    query = scene.get("evidence_query") or scene.get("narration", "")
    if not query.strip():
        return {"status": "needs_review", "reason": "missing_evidence_query"}
    if scene.get("visual_type") == "action_only":
        return {"status": "needs_review", "reason": "action_requires_visual_verification"}
    matches = []
    for ep in episodes:
        for cue in ep["cues"]:
            confidence = score(query, cue["text"])
            if confidence >= threshold:
                matches.append({"episode": ep["episode"], "start": max(0, cue["start"] - margin),
                                "end": cue["end"] + margin, "confidence": confidence,
                                "subtitle_evidence": cue["text"], "source": ep["subtitle_path"]})
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    if not matches:
        return {"status": "needs_review", "reason": "no_supported_subtitle_match"}
    if len(matches) > 1 and matches[0]["confidence"] - matches[1]["confidence"] < 0.08:
        return {"status": "needs_review", "reason": "ambiguous_episode_or_time", "candidates": matches[:3]}
    return {"status": "candidate", "match": matches[0],
            "warning": "Subtitle evidence only; confirm visuals and rights before extraction"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", required=True, help="JSON list of scenes with evidence_query")
    parser.add_argument("--episodes", required=True, help="JSON list of {episode, subtitle_path}")
    parser.add_argument("--output", default="output/scene_matches.json")
    args = parser.parse_args()
    scenes = json.loads(Path(args.requests).read_text())
    episode_specs = json.loads(Path(args.episodes).read_text())
    episodes = [{"episode": e["episode"], "subtitle_path": e["subtitle_path"],
                 "cues": parse_srt(Path(e["subtitle_path"]).read_text(encoding="utf-8-sig"))}
                for e in episode_specs]
    results = [{"scene_index": i, "narration": s.get("narration"), **locate(s, episodes)}
               for i, s in enumerate(scenes)]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2) + "\n")
    print(f"Located {sum(r['status'] == 'candidate' for r in results)}/{len(results)} candidate scenes; remaining need review.")


if __name__ == "__main__":
    main()
