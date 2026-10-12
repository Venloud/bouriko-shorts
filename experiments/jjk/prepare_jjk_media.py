"""JJK media director: resolve every named character to the RIGHT character image, write the media
plan, and refuse to continue with a blank or wrong-character slot.

Replaces the generic pipeline/media.py in the JJK workflow (no stock search, no new anime
footage providers). Order per character:
  1. vetted local still: assets/anime/jujutsu_kaisen/<slug>.(png|jpg|webp) + <file>.json sidecar
     {"character": "...", "source_url": "...", "rights_status": "licensed|user_supplied_review_only"}
  2. AniList character image (exact name or alias AND a Jujutsu Kaisen credit)
  3. Jikan / MyAnimeList character image (same checks)
Database art is third-party: every one is logged as rights_status "review_only_unlicensed".
Footage is used ONLY from files the owner puts in assets/anime/jujutsu_kaisen/footage/ (each with a
sidecar .json: source, episode, timestamps, rights). None are fetched from the internet.

Outputs: output/jjk_images/*, output/jjk_media_plan.json, output/jjk_media_plan.md,
         story["assets"] rewritten to local paths for pipeline/visual_plan.py.
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output"
LOCAL = ROOT / "assets/anime/jujutsu_kaisen"
FOOTAGE = LOCAL / "footage"
UA = "BourikoJJKReview/1.2 (https://github.com/Venloud/bouriko-shorts; review-only character references)"
ANILIST_Q = """query($s:String){Page(perPage:10){characters(search:$s){id name{full native alternative}
  image{large} siteUrl media(perPage:25){nodes{title{romaji english}}}}}}"""


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def is_jjk(titles):
    return any("jujutsu" in (t or "").lower() for t in titles)


def local_still(name):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        f = LOCAL / (slug(name) + ext)
        side = f.with_name(f.name + ".json")
        if f.is_file() and side.is_file():
            meta = json.loads(side.read_text())
            if meta.get("character", "").casefold() == name.casefold() and meta.get("source_url") \
                    and meta.get("rights_status") in {"licensed", "user_supplied_review_only"}:
                return f.read_bytes(), {"provider": "local_vetted", "source_url": meta["source_url"],
                                        "image_url": None, "rights_status": meta["rights_status"]}
    return None


def anilist(session, name, aliases):
    wanted = {n.casefold() for n in [name, *aliases]}
    for q in [name, *aliases]:
        r = session.post("https://graphql.anilist.co", json={"query": ANILIST_Q, "variables": {"s": q}}, timeout=30)
        r.raise_for_status()
        for c in r.json()["data"]["Page"]["characters"]:
            names = {c["name"]["full"].casefold(), *[(a or "").casefold() for a in c["name"].get("alternative") or []]}
            titles = [m["title"]["romaji"] for m in c["media"]["nodes"]] + [m["title"]["english"] for m in c["media"]["nodes"]]
            if not (names & wanted) or not is_jjk(titles):
                continue
            url = c["image"]["large"]
            img = session.get(url, timeout=30)
            img.raise_for_status()
            if not img.headers.get("content-type", "").startswith("image/") or len(img.content) < 2000:
                continue
            return img.content, {"provider": "anilist_character", "source_url": c["siteUrl"], "image_url": url,
                                 "matched_name": c["name"]["full"], "anilist_id": c["id"],
                                 "rights_status": "review_only_unlicensed"}
        time.sleep(1)
    return None


def jikan(session, name, aliases):
    wanted = {n.casefold() for n in [name, *aliases]}
    for q in [name, *aliases]:
        r = session.get("https://api.jikan.moe/v4/characters?q=" + quote(q) + "&limit=10", timeout=(8, 20))
        r.raise_for_status()
        for item in r.json().get("data", []):
            if item.get("name", "").casefold() not in wanted:
                continue
            anime = session.get(f"https://api.jikan.moe/v4/characters/{item['mal_id']}/anime", timeout=(8, 20)).json()
            if not is_jjk([(a.get("anime") or {}).get("title") for a in anime.get("data", [])]):
                continue
            url = ((item.get("images") or {}).get("jpg") or {}).get("large_image_url")
            img = session.get(url, timeout=(8, 20))
            img.raise_for_status()
            return img.content, {"provider": "jikan_character", "source_url": item.get("url"), "image_url": url,
                                 "matched_name": item.get("name"), "rights_status": "review_only_unlicensed"}
    return None


def resolve_character(session, name, aliases, failures):
    for fn in (lambda: local_still(name), lambda: anilist(session, name, aliases), lambda: jikan(session, name, aliases)):
        try:
            got = fn()
            if got:
                return got
        except Exception as e:  # noqa: BLE001
            failures.append({"character": name, "error": f"{type(e).__name__}: {str(e)[:200]}"})
    return None


def footage_index():
    """Owner-supplied clips only. Each needs a sidecar: {source, episode, start, end, shows, rights_status}."""
    clips = []
    if FOOTAGE.exists():
        for f in sorted(FOOTAGE.iterdir()):
            if f.suffix.lower() in {".mp4", ".mov", ".webm", ".mkv"}:
                side = f.with_name(f.name + ".json")
                meta = json.loads(side.read_text()) if side.exists() else {}
                clips.append({"path": str(f.relative_to(ROOT)), "has_sidecar": side.exists(), **meta})
    return clips


def main():
    story_path = OUT / "story.json"
    story = json.loads(story_path.read_text())
    img_dir = OUT / "jjk_images"
    img_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    failures, resolved = [], {}

    for key, spec in story.get("assets", {}).items():
        if "character" not in spec:
            continue
        name = spec["character"]
        got = resolve_character(session, name, spec.get("aliases", []), failures)
        if not got:
            print(f"MISSING: no verified image for {name}")
            continue
        raw, meta = got
        digest = hashlib.sha256(raw).hexdigest()
        ext = ".png" if raw[:4] == b"\x89PNG" else ".jpg"
        target = img_dir / f"{slug(name)}_{digest[:12]}{ext}"
        target.write_bytes(raw)
        resolved[key] = {"path": str(target.relative_to(ROOT)), "kind": "image", "character": name,
                         "sha256": digest, "credit": f"{name} · {meta['provider'].split('_')[0]} · review only",
                         **meta}
        print(f"IMAGE {name}: {meta['provider']} {meta.get('matched_name', '')} sha256={digest[:12]} {meta['source_url']}")
        time.sleep(0.7)

    # rewrite the plan's character specs to local files for pipeline/visual_plan.py
    for key, rec in resolved.items():
        story["assets"][key] = {"path": rec["path"], "kind": "image", "provider": rec["provider"],
                                "source_url": rec["source_url"], "license": None, "creator": None,
                                "rights_status": rec["rights_status"], "credit": rec["credit"]}

    # media plan: every beat, what it shows, where it comes from, what is missing
    plan, missing = [], []
    for i, line in enumerate(story["lines"]):
        for k, b in enumerate(line.get("beats", [])):
            row = {"line": i, "beat": k, "starts_at_word": b.get("word", 0),
                   "narration": line["text"], "tts_text": line.get("tts_text")}
            if b.get("asset"):
                spec = story["assets"].get(b["asset"], {})
                rec = resolved.get(b["asset"])
                row.update(kind="character_image", character=spec.get("character") or (rec or {}).get("character"))
                if rec:
                    row.update(status="ok", provider=rec["provider"], source_url=rec["source_url"],
                               image_url=rec.get("image_url"), sha256=rec["sha256"], rights_status=rec["rights_status"])
                else:
                    row.update(status="MISSING")
                    missing.append(f"line {i} beat {k}: no verified image for {row['character']}")
            else:
                d = b.get("diagram", {})
                row.update(kind="motion_graphic", diagram=d.get("name"), params=d.get("params"),
                           status="ok", provider="remotion (original graphic)", rights_status="original")
            plan.append(row)

    # Named characters that are spoken but have no image beat are flagged too.
    names = {spec["character"]: key for key, spec in {**story.get("assets", {}), **{k: {"character": v["character"]} for k, v in resolved.items()}}.items() if "character" in spec}
    for i, line in enumerate(story["lines"]):
        shown = {story["assets"].get(b.get("asset"), {}).get("character") or resolved.get(b.get("asset"), {}).get("character")
                 for b in line.get("beats", []) if b.get("asset")}
        for full in names:
            first = full.split()[0]
            if re.search(r"\b" + re.escape(first) + r"\b", line["text"]) and full not in shown:
                missing.append(f"line {i}: '{first}' is spoken but no {full} image is on screen in this line")

    footage = footage_index()
    report = {
        "script_version": story.get("script_version"),
        "beats": plan,
        "characters": resolved,
        "fetch_failures": failures,
        "owner_footage": footage,
        "footage_note": "No anime footage used: no owner-supplied clips in assets/anime/jujutsu_kaisen/footage/."
                        if not footage else f"{len(footage)} owner-supplied clip(s) indexed; none are wired to a beat yet.",
        "missing": missing,
        "rights_note": "Character art from AniList/MyAnimeList is third-party and NOT publish-cleared (review only).",
    }
    (OUT / "jjk_media_plan.json").write_text(json.dumps(report, indent=2) + "\n")
    md = ["# JJK Culling Game: media plan", "", f"Script: {story.get('script_version')}", "",
          "| line | beat | shows | source | sha256 | rights | status |", "|---|---|---|---|---|---|---|"]
    for r in plan:
        shows = r.get("character") or f"diagram: {r.get('diagram')}"
        src = r.get("source_url") or r.get("provider")
        md.append(f"| {r['line']} | {r['beat']} | {shows} | {src} | {(r.get('sha256') or '')[:12]} | {r.get('rights_status')} | {r['status']} |")
    md += ["", "## Missing / flagged", *([f"- {m}" for m in missing] or ["- none"]),
           "", "## Footage", f"- {report['footage_note']}", "", "## Rights", f"- {report['rights_note']}"]
    if failures:
        md += ["", "## Fetch failures", *[f"- {f['character']}: {f['error']}" for f in failures]]
    (OUT / "jjk_media_plan.md").write_text("\n".join(md) + "\n")
    story_path.write_text(json.dumps(story, indent=2) + "\n")
    print(f"JJK MEDIA PLAN: {len(plan)} beats, {len(resolved)} character images, {len(missing)} missing")
    if any("no verified image" in m for m in missing):
        raise SystemExit("JJK MEDIA FAILED: a named-character beat has no verified image; see output/jjk_media_plan.md")


if __name__ == "__main__":
    main()
