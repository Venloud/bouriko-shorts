"""Apply a hand-authored visual plan to the story (beats, diagrams, callouts, pinned media, tts_text).

A plan lives in data/visual_plans/<id>.json and is matched by story["visual_plan"], the exact
script file name, or a title substring. A story can also carry "beats" on its lines directly
(the JJK experiment does). Lines without beats are split automatically later in
remotion_prepare.py, so normal generated stories keep working with no plan at all.

Pinned assets make a render reproducible: the callout coordinates in a plan only make sense for
the exact shot they were drawn on. Supported asset specs:
  {"commons": "File:X.jpg", "kind": "image"|"video"}   Wikimedia Commons (license recorded)
  {"path": "assets/...", "kind": ..., "source_url": ..., "license": ...}   a local file
  {"media_line": 3}                                     the asset media.py found for line 3
Every resolved asset is logged with source, license and sha256 in output/visual_plan_assets.json.
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests

from common import ROOT, log

PLANS = ROOT / "data/visual_plans"
CACHE = ROOT / "cache/media"
UA = "BourikoShorts/1.0 (https://github.com/Venloud/bouriko-shorts; contact via GitHub)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _get(url, **kw):
    """Wikimedia asks for a contact User-Agent and backs off with 429 + Retry-After."""
    for attempt in range(6):
        r = requests.get(url, headers={"User-Agent": UA}, timeout=120, **kw)
        if r.status_code == 429:
            wait = min(90, int(r.headers.get("Retry-After", "20") or 20))
            log(f"  Commons 429, waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"rate limited: {url[:80]}")


def commons_asset(title, kind):
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(title.encode()).hexdigest()[:16]
    meta_path = CACHE / f"{key}.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if (ROOT / meta["local_path"]).exists():
            return meta
    params = {"action": "query", "format": "json", "formatversion": "2", "titles": title,
              "prop": "imageinfo|videoinfo", "iiprop": "url|mime|size|extmetadata",
              "viprop": "derivatives|url", "iiurlwidth": "1600"}
    page = _get(COMMONS_API, params=params).json()["query"]["pages"][0]
    if page.get("missing"):
        raise RuntimeError(f"Commons file not found: {title}")
    info = page["imageinfo"][0]
    meta = info.get("extmetadata") or {}
    url = info["url"]
    if kind == "image" and info.get("thumburl"):
        url = info["thumburl"]
    if kind == "video":
        # prefer a 720p/1080p transcode over a huge original
        ders = (page.get("videoinfo") or [{}])[0].get("derivatives") or []
        best = None
        for d in ders:
            if d.get("type", "").startswith("video/webm") and 700 <= int(d.get("height") or 0) <= 1100:
                if not best or int(d["height"]) > int(best["height"]):
                    best = d
        if best and info.get("size", 0) > 25_000_000:
            url = best["src"]
    ext = Path(url.split("?")[0]).suffix or (".webm" if kind == "video" else ".jpg")
    local = CACHE / f"{key}{ext}"
    if not local.exists():
        local.write_bytes(_get(url).content)
        time.sleep(2)
    license_name = str((meta.get("LicenseShortName") or {}).get("value") or "")
    if re.search(r"\bNC\b|non-?commercial|\bND\b", license_name, re.I):
        raise RuntimeError(f"{title}: license {license_name} is not usable")
    artist = re.sub(r"<[^>]+>", "", str((meta.get("Artist") or {}).get("value") or "")).strip()
    rec = {
        "provider": "wikimedia_commons", "kind": kind, "title": title, "url": url,
        "source_url": info.get("descriptionurl"), "license": license_name,
        "license_url": str((meta.get("LicenseUrl") or {}).get("value") or ""),
        "creator": artist[:120], "local_path": str(local.relative_to(ROOT)), "sha256": sha256(local),
    }
    meta_path.write_text(json.dumps(rec, indent=2))
    return rec


def credit_of(rec):
    if not rec:
        return None
    if rec.get("credit"):
        return rec["credit"]
    prov = {"wikimedia_commons": "Wikimedia Commons", "pexels": "Pexels", "pixabay": "Pixabay",
            "mixkit": "Mixkit", "coverr": "Coverr", "youtube_cc": "YouTube CC BY"}.get(rec.get("provider"), "")
    lic = rec.get("license") or ""
    creator = (rec.get("creator") or "").split("\n")[0][:40]
    bits = [b for b in (creator, prov, lic) if b and b not in ("Public domain",)]
    if lic == "Public domain":
        bits.append("Public domain")
    return " · ".join(bits) if bits else None


def resolve_asset(spec, story):
    if "commons" in spec:
        rec = commons_asset(spec["commons"], spec.get("kind", "image"))
    elif "path" in spec:
        p = ROOT / spec["path"]
        if not p.exists():
            raise RuntimeError(f"local asset missing: {spec['path']}")
        rec = {"provider": spec.get("provider", "local"), "kind": spec.get("kind", "image"),
               "local_path": spec["path"], "source_url": spec.get("source_url"),
               "license": spec.get("license"), "creator": spec.get("creator"),
               "rights_status": spec.get("rights_status"), "sha256": sha256(p)}
    elif "media_line" in spec:
        line = story["lines"][int(spec["media_line"])]
        src = line.get("media_source") or {}
        if not line.get("media_asset"):
            raise RuntimeError(f"line {spec['media_line']} has no media asset")
        rec = {**src, "local_path": line["media_asset"], "kind": src.get("kind") or line.get("media_kind", "image")}
    else:
        raise RuntimeError(f"unknown asset spec {spec}")
    rec = dict(rec)
    for k in ("start", "focus", "fit", "box", "credit"):
        if k in spec:
            rec[k] = spec[k]
    if spec.get("credit") is None:
        rec["credit"] = credit_of(rec)
    return rec


def find_plan(story):
    if not PLANS.exists():
        return None
    want = story.get("visual_plan")
    for p in sorted(PLANS.glob("*.json")):
        plan = json.loads(p.read_text())
        m = plan.get("match", {})
        if want and plan.get("id") == want:
            return plan
        if story.get("script_file") and story["script_file"] in m.get("script_files", []):
            return plan
        title = (story.get("title") or "").lower()
        if any(s.lower() in title for s in m.get("title_contains", [])):
            return plan
    return None


def norm_words(text):
    return [re.sub(r"[^a-z0-9]", "", w.lower()) for w in text.split()]


def apply(story, plan):
    """Copy plan lines (tts_text, beats) onto the story; resolve every asset once."""
    assets_spec = {**plan.get("assets", {}), **story.get("assets", {})}
    lines = story["lines"]
    plan_lines = plan.get("lines", [])
    if plan_lines and len(plan_lines) != len(lines):
        log(f"PLAN WARNING: plan has {len(plan_lines)} lines, story has {len(lines)}; matching by index")
    for i, pl in enumerate(plan_lines[: len(lines)]):
        if pl.get("text") and norm_words(pl["text"]) != norm_words(lines[i]["text"]):
            log(f"PLAN WARNING: line {i} text differs from the plan; plan beats skipped for this line")
            continue
        for k in ("tts_text", "beats"):
            if k in pl:
                lines[i][k] = pl[k]
    for k in ("theme", "hook_answer_line", "voice_settings", "voice_speed"):
        if k in plan and k not in story:
            story[k] = plan[k]
    story["assets"] = assets_spec
    return story


def resolve_all(story):
    specs = story.get("assets") or {}
    used = {b.get("asset") for line in story["lines"] for b in line.get("beats", []) if b.get("asset")}
    resolved, failures = {}, []
    for name in sorted(used):
        if name not in specs:
            failures.append({"asset": name, "error": "not defined in plan assets"})
            continue
        try:
            resolved[name] = resolve_asset(specs[name], story)
            log(f"  asset {name}: {resolved[name].get('provider')} {resolved[name].get('license') or resolved[name].get('rights_status') or ''} sha256={resolved[name]['sha256'][:12]}")
        except Exception as e:  # noqa: BLE001
            failures.append({"asset": name, "error": str(e)[:300]})
            log(f"  asset {name} FAILED: {e}")
    story["resolved_assets"] = resolved
    # Beats whose asset failed fall back to the line's own media / auto beat later.
    for line in story["lines"]:
        for b in line.get("beats", []):
            if b.get("asset") and b["asset"] not in resolved:
                b["missing_asset"] = b.pop("asset")
    return failures


def main():
    path = ROOT / "output/story.json"
    story = json.loads(path.read_text())
    plan = find_plan(story)
    if plan:
        log(f"Visual plan: {plan.get('id')}")
        story = apply(story, plan)
    elif not any(line.get("beats") for line in story["lines"]):
        log("Visual plan: none (automatic 2-4 s beats from the media found for each line)")
    failures = resolve_all(story)
    (ROOT / "output/visual_plan_assets.json").write_text(json.dumps(
        {"resolved": story.get("resolved_assets", {}), "failures": failures}, indent=2))
    path.write_text(json.dumps(story, indent=2))
    if failures and "--strict" in sys.argv:
        raise SystemExit(f"VISUAL PLAN FAILED: {len(failures)} asset(s) missing, see output/visual_plan_assets.json")


if __name__ == "__main__":
    main()
