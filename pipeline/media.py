"""Free-media discovery and download for Bouriko.

Providers:
- Pixabay/Pexels/Coverr when configured.
- Wikimedia Commons as a no-key fallback.

The renderer should never silently turn a missing-media build into a slideshow.
Every downloaded asset records its source and license metadata.
"""
import base64
import json
import os
import re
import time
from pathlib import Path

import requests

from common import ROOT

MEDIA_DIR = ROOT / "output/media"
MANIFEST = ROOT / "output/media_manifest.json"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
UA = "BourikoShorts/1.0 (automated media retrieval)"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")[:70] or "asset"


def _get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", UA)
    r = requests.get(url, timeout=45, headers=headers, **kwargs)
    r.raise_for_status()
    return r


def _download(url, path, attempts=4):
    """Download with retry/backoff so a rate-limited provider does not kill the build."""
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(attempts):
        try:
            with requests.get(url, stream=True, timeout=120, headers={"User-Agent": UA, "Accept": "*/*"}) as r:
                if r.status_code == 429:
                    retry_after = r.headers.get("Retry-After")
                    try:
                        delay = min(30, max(2, int(retry_after))) if retry_after else 2 ** attempt
                    except ValueError:
                        delay = 2 ** attempt
                    time.sleep(delay)
                    continue
                r.raise_for_status()
                with path.open("wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(min(15, 2 ** attempt))
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to download {url}")

def mixkit(query, kind):
    """Discover a small set of Mixkit stock-video candidates without an API key."""
    if kind != "video":
        return []

    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")
    if not slug:
        return []

    url = f"https://mixkit.co/free-stock-video/{slug}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        r = requests.get(url, timeout=30, headers=headers)
        if not r.ok:
            return []
        html = r.text
    except requests.RequestException:
        return []

    # Mixkit pages expose downloadable MP4 URLs in the page source.
    raw_urls = re.findall(r'https://assets\.mixkit\.co/videos[^"\s]+?\.mp4', html)
    urls = []
    for raw in raw_urls:
        clean = raw.replace("\\u0026", "&").replace("\\/", "/")
        # Prefer the 720p asset when the page exposes the 360p variant.
        if "-360.mp4" in clean:
            clean = clean.replace("-360.mp4", "-720.mp4")
        if clean not in urls:
            urls.append(clean)

    out = []
    for media_url in urls[:8]:
        out.append({
            "provider": "mixkit",
            "kind": "video",
            "url": media_url,
            "source_url": url,
            "creator": None,
            "title": query,
            "license": "Mixkit Stock Video Free License (verify per clip)",
            "license_url": "https://mixkit.co/license/",
        })
    return out


def youtube_cc(query, kind):
    """Find downloadable YouTube clips whose metadata explicitly says CC BY."""
    if kind != "video":
        return []
    try:
        import yt_dlp
    except ImportError:
        print("  youtube_cc: yt-dlp is not installed")
        return []

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "playlistend": 8,
        "noplaylist": False,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch8:{query}", download=False)
    except Exception as exc:
        print(f"  youtube_cc: search failed for '{query}': {exc}")
        return []

    entries = result.get("entries", []) if isinstance(result, dict) else []
    out = []
    for item in entries:
        if not item or item.get("_type") == "playlist":
            continue
        license_name = str(item.get("license") or "")
        if "creative commons attribution" not in license_name.lower():
            continue
        webpage_url = item.get("webpage_url") or item.get("original_url")
        if not webpage_url and item.get("id"):
            webpage_url = f"https://www.youtube.com/watch?v={item['id']}"
        if not webpage_url:
            continue
        out.append({
            "provider": "youtube_cc",
            "kind": "video",
            "url": webpage_url,
            "source_url": webpage_url,
            "creator": item.get("uploader") or item.get("channel"),
            "title": item.get("title") or query,
            "license": license_name,
            "license_url": "https://support.google.com/youtube/answer/2797468",
            "youtube_id": item.get("id"),
        })
    return out



def pixabay(query, kind):
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return []
    endpoint = "https://pixabay.com/api/videos/" if kind == "video" else "https://pixabay.com/api/"
    params = {"key": key, "q": query, "safesearch": "true", "per_page": 20, "order": "popular"}
    if kind == "image":
        params["image_type"] = "photo"
    d = _get(endpoint, params=params).json()
    hits = d.get("hits", [])
    out = []
    for h in hits:
        if kind == "video":
            sizes = h.get("videos", {})
            choice = sizes.get("large") or sizes.get("medium") or sizes.get("small") or {}
            url = choice.get("url")
        else:
            url = h.get("largeImageURL") or h.get("webformatURL")
        if url:
            out.append({"provider":"pixabay","kind":kind,"url":url,
                        "source_url":h.get("pageURL"),"creator":h.get("user"),
                        "title":h.get("tags", query), "license":"Pixabay license"})
    return out


def pexels(query, kind):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return []
    endpoint = "https://api.pexels.com/v1/videos/search" if kind == "video" else "https://api.pexels.com/v1/search"
    params = {"query": query, "per_page": 20}
    headers = {"Authorization": key, "User-Agent": UA}
    d = _get(endpoint, headers=headers, params=params).json()
    out = []
    for h in d.get("videos" if kind == "video" else "photos", []):
        if kind == "video":
            files = sorted(h.get("video_files", []), key=lambda x: (x.get("width",0), x.get("height",0)), reverse=True)
            url = files[0].get("link") if files else None
            creator = (h.get("user") or {}).get("name")
        else:
            url = (h.get("src") or {}).get("original")
            creator = h.get("photographer")
        if url:
            out.append({"provider":"pexels","kind":kind,"url":url,
                        "source_url":h.get("url"),"creator":creator,
                        "title":h.get("alt") or query,"license":"Pexels license"})
    return out


def coverr(query):
    key = os.getenv("COVERR_API_KEY")
    if not key:
        return []
    d = _get("https://api.coverr.co/videos/search",
              headers={"x-api-key":key,"User-Agent":UA},
              params={"query":query,"page_size":20}).json()
    out = []
    for h in d.get("hits", []):
        files = h.get("urls") or h.get("video_files") or {}
        url = None
        if isinstance(files, dict):
            for k in ("mp4","1080p","hd","url"):
                if isinstance(files.get(k), str):
                    url = files[k]; break
        if not url and isinstance(h.get("download_url"), str):
            url = h["download_url"]
        if url:
            out.append({"provider":"coverr","kind":"video","url":url,
                        "source_url":h.get("url") or h.get("page_url"),
                        "creator":h.get("author") or h.get("creator"),
                        "title":h.get("title") or query,"license":"Coverr license"})
    return out


def commons(query, kind):
    """Search Commons without an API key and return reusable candidates."""
    # Commons exposes file metadata and direct URLs through its read-only API.
    d = _get(COMMONS_API, params={
        "action":"query","format":"json","formatversion":"2",
        "generator":"search","gsrnamespace":"6","gsrwhat":"text",
        "gsrlimit":"30","gsrsearch":query,
        "prop":"imageinfo","iiprop":"url|mime|size|extmetadata",
        "iiurlwidth":"1800"
    }).json()
    out = []
    for page in d.get("query", {}).get("pages", []):
        info = (page.get("imageinfo") or [{}])[0]
        mime = (info.get("mime") or "").lower()
        title = page.get("title") or ""
        if kind == "video":
            if not (mime.startswith("video/") or any(title.lower().endswith(x) for x in (".webm",".mp4",".ogv"))):
                continue
        else:
            if not mime.startswith("image/"):
                continue
        meta = info.get("extmetadata") or {}
        license_name = str((meta.get("LicenseShortName") or {}).get("value") or "")
        license_url = str((meta.get("LicenseUrl") or {}).get("value") or "")
        # Avoid non-commercial-only files.
        if "NC" in license_name.upper() or "NONCOMMERCIAL" in license_name.upper():
            continue
        url = info.get("url")
        if not url:
            continue
        artist = str((meta.get("Artist") or {}).get("value") or "")
        source_url = info.get("descriptionurl") or ("https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"))
        score = 0
        qwords = set(re.findall(r"[a-z0-9]+", query.lower()))
        twords = set(re.findall(r"[a-z0-9]+", title.lower()))
        score += len(qwords & twords) * 10
        if kind == "video" and mime.startswith("video/"):
            score += 20
        if license_name:
            score += 3
        out.append({"provider":"wikimedia_commons","kind":kind,"url":url,
                    "source_url":source_url,"creator":artist,"title":title,
                    "license":license_name or "See Commons file page",
                    "license_url":license_url,"score":score})
    out.sort(key=lambda x:x.get("score",0), reverse=True)
    return out


def _query_variants(query, kind):
    """Turn a natural-language scene description into several stock-search queries."""
    q = re.sub(r"[^a-z0-9\s-]", " ", str(query).lower())
    q = re.sub(r"\s+", " ", q).strip()
    variants = [q]

    keyword_groups = [
        ("traffic light", "traffic light"),
        ("traffic signal", "traffic signal"),
        ("intersection", "intersection"),
        ("road traffic", "road traffic"),
        ("traffic", "traffic"),
        ("car", "cars"),
        ("bicycle", "bicycle"),
        ("bike", "bicycle"),
        ("traffic camera", "traffic camera"),
        ("camera", "traffic camera"),
        ("radar", "radar"),
        ("induction loop", "induction loop"),
        ("road sensor", "road sensor"),
        ("road", "road"),
        ("street", "street"),
    ]
    for needle, replacement in keyword_groups:
        if needle in q:
            variants.append(replacement)

    words = q.split()
    if len(words) > 3:
        variants.append(" ".join(words[:3]))
        variants.append(" ".join(words[-3:]))

    out = []
    for item in variants:
        item = item.strip()
        if item and item not in out:
            out.append(item)
    return out[:6]


def choose(query, kind):
    candidates = []
    seen = set()
    variants = _query_variants(query, kind)

    print(f"Media search: {kind} | {query} | variants={variants}")

    for variant in variants:
        for name, fn in (
            ("youtube_cc", youtube_cc),
            ("pixabay", pixabay),
            ("pexels", pexels),
            ("mixkit", mixkit),
        ):
            try:
                found = fn(variant, kind)
                print(f"  {name}: {len(found)} candidates for '{variant}'")
                for item in found:
                    key = (item.get("provider"), item.get("url"))
                    if key not in seen:
                        seen.add(key)
                        candidates.append(item)
            except Exception as exc:
                print(f"  {name}: ERROR for '{variant}': {exc}")

        if kind == "video":
            try:
                found = coverr(variant)
                print(f"  coverr: {len(found)} candidates for '{variant}'")
                for item in found:
                    key = (item.get("provider"), item.get("url"))
                    if key not in seen:
                        seen.add(key)
                        candidates.append(item)
            except Exception as exc:
                print(f"  coverr: ERROR for '{variant}': {exc}")

        try:
            found = commons(variant, kind)
            print(f"  wikimedia_commons: {len(found)} candidates for '{variant}'")
            for item in found:
                key = (item.get("provider"), item.get("url"))
                if key not in seen:
                    seen.add(key)
                    candidates.append(item)
        except Exception as exc:
            print(f"  wikimedia_commons: ERROR for '{variant}': {exc}")

        if len(candidates) >= 12:
            break

    return candidates[:30]




def generate_local_diagram(query, index):
    """Deterministic technical visual fallback when stock/AI media cannot fill a scene.

    Inspired by Lumen's local no-cost fallback philosophy: a missing provider must
    not turn into a fake slideshow or make the whole production fail. For Bouriko,
    the fallback is a subject-specific explainer diagram rather than a generic card.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None

    w, h = 1080, 1920
    bg = (244, 239, 228)
    ink = (27, 27, 27)
    blue = (46, 168, 255)
    red = (230, 57, 70)
    green = (31, 182, 94)
    yellow = (255, 210, 63)

    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)

    def f(size, bold=False):
        candidates = [
            "/usr/share/fonts/truetype/lato/Lato-Black.ttf" if bold else "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in candidates:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    q = str(query).lower()
    title = "HOW THE SENSOR WORKS"
    if "traffic" in q or "intersection" in q or "road" in q or "loop" in q:
        title = "HIDDEN ROAD SENSOR"

        # Road
        d.rounded_rectangle((90, 470, 990, 1450), radius=35, fill=(65, 65, 65))
        d.line((90, 760, 990, 760), fill=(235, 235, 235), width=8)
        d.line((90, 1160, 990, 1160), fill=(235, 235, 235), width=8)

        # Induction loop under the car.
        loop = (260, 900, 820, 1110)
        d.rounded_rectangle(loop, radius=28, outline=blue, width=18)
        d.text((110, 300), title, font=f(66, True), fill=ink)
        d.text((110, 380), "Induction loop detects a vehicle", font=f(38), fill=ink)

        # Car
        d.rounded_rectangle((360, 780, 720, 930), radius=30, fill=(215, 215, 215), outline=ink, width=6)
        d.polygon([(420, 780), (485, 710), (610, 710), (670, 780)], fill=(190, 220, 235), outline=ink)
        d.ellipse((395, 885, 455, 945), fill=ink)
        d.ellipse((625, 885, 685, 945), fill=ink)

        # Signal + controller.
        d.rounded_rectangle((770, 260, 930, 500), radius=28, fill=ink)
        for cy, fill in ((315, red), (380, yellow), (445, green)):
            d.ellipse((815, cy, 885, cy + 70), fill=fill)

        d.line((810, 500, 810, 620), fill=ink, width=10)
        d.rounded_rectangle((705, 600, 915, 735), radius=18, fill=(225,225,225), outline=ink, width=5)
        d.text((730, 635), "CONTROLLER", font=f(25, True), fill=ink)

        # Signal path
        d.line((540, 1110, 540, 1320), fill=blue, width=14)
        d.polygon([(540, 1370), (510, 1310), (570, 1310)], fill=blue)
        d.text((585, 1240), "vehicle changes", font=f(28, True), fill=ink)
        d.text((585, 1280), "the magnetic field", font=f(28), fill=ink)
        d.line((705, 665, 585, 665), fill=blue, width=10)
        d.polygon([(545, 665), (605, 635), (605, 695)], fill=blue)

        d.text((120, 1530), "CAR → LOOP → CONTROLLER → SIGNAL", font=f(42, True), fill=ink)
    else:
        title = "TECHNICAL EXPLAINER"
        d.text((90, 300), title, font=f(66, True), fill=ink)
        d.text((90, 400), str(query)[:70], font=f(38), fill=ink)
        d.rounded_rectangle((120, 650, 960, 1250), radius=40, outline=blue, width=14)
        d.ellipse((220, 820, 380, 980), fill=blue)
        d.ellipse((700, 820, 860, 980), fill=blue)
        d.line((380, 900, 700, 900), fill=ink, width=16)
        d.polygon([(700, 900), (640, 865), (640, 935)], fill=ink)
        d.text((120, 1400), "LOCAL DIAGRAM FALLBACK", font=f(38, True), fill=ink)

    path = MEDIA_DIR / f"{index:02}_diagram_{_slug(query)}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "PNG")
    if path.stat().st_size < 5000:
        path.unlink(missing_ok=True)
        return None

    return {
        "index": index,
        "query": query,
        "kind": "image",
        "provider": "local_diagram",
        "url": None,
        "source_url": None,
        "creator": "Bouriko local renderer",
        "title": f"Technical explainer diagram: {query}",
        "license": "Original locally generated Bouriko artwork",
        "license_url": None,
        "local_path": str(path.relative_to(ROOT)),
    }

def generate_ai_image(query, index, exact_visual=False):
    """Last-resort realistic 9:16 image using the existing Gemini API key."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
    if exact_visual:
        prompt = (
            "Create an original illustrated vertical 9:16 scene for a YouTube commentary video. "
            "Follow this visual direction exactly as the scene concept: " + query + ". "
            "Use a polished hand-drawn anime-inspired editorial illustration style, dynamic composition, "
            "bold readable shapes, cinematic lighting, expressive faces when appropriate, and strong visual storytelling. "
            "Do not copy or reproduce any copyrighted anime character exactly. Do not use stock photography. "
            "No captions, logos, UI, watermark-like text, or fake screenshots. "
            "The image should communicate the visual direction clearly on its own."
        )
    else:
        prompt = (
            "Create a realistic photographic vertical 9:16 image for a modern tech explainer short. "
            "Show exactly this real-world subject: " + query + ". "
            "Make it look like authentic documentary/B-roll photography, natural lighting, believable scale, "
            "sharp details, no cartoon style, no logos, no captions, no UI, no watermark-like text. "
            "Compose the important subject clearly in the center safe area for a vertical video."
        )
    try:
        from google import genai
        client = genai.Client(api_key=key)
        interaction = client.interactions.create(
            model=model,
            input=prompt,
            response_format={"type":"image","aspect_ratio":"9:16","image_size":"1K"},
        )
        image = getattr(interaction, "output_image", None)
        data = getattr(image, "data", None) if image else None
        if not data:
            return None
        path = MEDIA_DIR / f"{index:02}_ai_{_slug(query)}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(data))
        if path.stat().st_size < 5000:
            path.unlink(missing_ok=True)
            return None
        print(f"AI image fallback created: scene={index} query='{query}'")
        return {
            "index": index, "query": query, "kind": "image",
            "provider": "gemini_ai", "url": None,
            "source_url": "https://ai.google.dev/gemini-api/docs/image-generation",
            "creator": "Google Gemini",
            "title": f"AI-generated realistic image: {query}",
            "license": "AI-generated; subject to Google Gemini API terms",
            "license_url": "https://ai.google.dev/gemini-api/terms",
            "local_path": str(path.relative_to(ROOT)),
        }
    except Exception as exc:
        print(f"AI image fallback failed: {exc}")
        return None

def ensure_asset(action, index, used_urls=None):
    query = str(action.get("query") or action.get("search") or "").strip()
    kind = str(action.get("kind") or "video").lower()
    if not query or kind not in {"image","video"}:
        return None

    used_urls = used_urls or set()
    candidates = choose(query, kind)
    if not candidates:
        diagram = generate_local_diagram(query, index)
        if diagram:
            return diagram
        return generate_ai_image(query, index)

    # Prefer a genuinely new source URL so different scenes do not collapse
    # onto the same stock clip.
    candidates = [c for c in candidates if c.get("url") not in used_urls] or candidates

    # A provider can return a valid search result whose file URL is temporarily
    # rate-limited or unavailable. Try the next candidate instead of aborting
    # the entire video build.
    for candidate_no, chosen in enumerate(candidates):
        if chosen.get("url") in used_urls:
            continue
        ext = (
            ".mp4" if chosen["provider"] == "youtube_cc"
            else (
                ".webm"
                if chosen["provider"] == "wikimedia_commons"
                and "webm" in chosen["url"].lower()
                else (".mp4" if kind == "video" else ".jpg")
            )
        )
        path = MEDIA_DIR / f"{index:02}_{_slug(query)}_{candidate_no}{ext}"
        if path.exists() and path.stat().st_size > 0:
            break
        try:
            if chosen.get("provider") == "youtube_cc":
                import yt_dlp
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "format": "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/b",
                    "merge_output_format": "mp4",
                    "outtmpl": str(path.with_suffix(".%(ext)s")),
                    "noplaylist": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([chosen["url"]])
                produced = list(path.parent.glob(path.stem + ".*"))
                if produced:
                    produced[0].replace(path)
            else:
                _download(chosen["url"], path)
            if path.stat().st_size == 0:
                raise RuntimeError("Downloaded media file is empty")
            break
        except Exception as exc:
            print(f"Media download failed ({chosen.get('provider')}): {chosen.get('url')} -> {exc}")
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
            path = None
    else:
        diagram = generate_local_diagram(query, index)
        if diagram:
            return diagram
        ai = generate_ai_image(query, index)
        if ai:
            return ai
        return None

    return {
        "index": index, "query": query, "kind": kind,
        "provider": chosen["provider"], "url": chosen["url"],
        "source_url": chosen.get("source_url"), "creator": chosen.get("creator"),
        "title": chosen.get("title"), "license": chosen.get("license"),
        "license_url": chosen.get("license_url"),
        "local_path": str(path.relative_to(ROOT))
    }

def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    records = []
    used_urls = set()

    # Exact-script productions use the script's VISUAL directions directly.
    # Do not search stock providers for these runs.
    if story.get("exact_script"):
        sections = {}
        for i, line in enumerate(story.get("lines", [])):
            key = line.get("section") or f"section-{i}"
            sections.setdefault(key, {
                "prompt": line.get("visual_prompt") or line.get("visual") or "original illustrated scene",
                "lines": [],
            })
            sections[key]["lines"].append(i)

        for section_no, (section_name, data) in enumerate(sections.items()):
            rec = generate_ai_image(
                data["prompt"],
                section_no,
                exact_visual=True,
            )
            if not rec:
                rec = generate_local_diagram(data["prompt"], section_no)
            if not rec:
                continue

            for line_index in data["lines"]:
                story["lines"][line_index]["media_asset"] = rec["local_path"]
                story["lines"][line_index]["media_kind"] = "image"
                story["lines"][line_index]["media_source"] = rec
            records.append(rec)

        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(records, indent=2))
        (ROOT / "output/story.json").write_text(json.dumps(story, indent=2))
        print(f"Exact-script visual production: {len(sections)} sections, {len(records)} original visual assets")
        return

    # First pass: use the story's exact visual intent.
    for i, line in enumerate(story.get("lines", [])):
        for action in line.get("visual_actions", []) or []:
            if str(action.get("type","")).lower() != "media":
                continue
            rec = ensure_asset(action, i, used_urls)
            if rec:
                line["media_asset"] = rec["local_path"]
                line["media_source"] = rec
                records.append(rec)
                used_urls.add(rec["url"])
                break

    # Second pass: fill failed scenes with broad, still-relevant stock footage.
    # Derive the fallback from the scene itself so the pipeline is reusable
    # outside the original traffic-light test.
    fallback_queries = []
    for line in story.get("lines", []):
        query = str(line.get("visual") or "").strip()
        if query and query not in fallback_queries:
            fallback_queries.append(query)
    if not fallback_queries:
        fallback_queries = ["technology explainer", "technology", "education"]
    for i, line in enumerate(story.get("lines", [])):
        if line.get("media_asset"):
            continue
        for query in fallback_queries:
            rec = ensure_asset({"kind": "video", "query": query}, i, used_urls)
            if not rec:
                continue
            line["media_asset"] = rec["local_path"]
            line["media_source"] = rec
            records.append(rec)
            used_urls.add(rec["url"])
            print(f"Fallback media assigned: scene={i} query='{query}' provider={rec['provider']}")
            break

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(records, indent=2))
    (ROOT / "output/story.json").write_text(json.dumps(story, indent=2))
    video_count = sum(1 for r in records if r.get("kind") == "video")
    print(f"Media assets downloaded: {len(records)} ({video_count} video)")

    if len(records) < 8:
        print("Media target not reached; using subject-specific local diagrams before AI.")
        for i, line in enumerate(story.get("lines", [])):
            if len(records) >= 8:
                break
            if line.get("media_asset"):
                continue
            diagram = generate_local_diagram(
                line.get("visual") or line.get("text", "technology"), i
            )
            if diagram:
                line["media_asset"] = diagram["local_path"]
                line["media_source"] = diagram
                line["media_kind"] = "image"
                records.append(diagram)

    if len(records) < 8:
        print("Local diagram target not reached; generating AI stills for missing scenes.")
        for i, line in enumerate(story.get("lines", [])):
            if len(records) >= 8:
                break
            if line.get("media_asset"):
                continue
            ai = generate_ai_image(line.get("visual") or line.get("text", "technology"), i)
            if ai:
                line["media_asset"] = ai["local_path"]
                line["media_source"] = ai
                line["media_kind"] = "image"
                records.append(ai)

    # Recovery pass inspired by capability-aware fallback systems:
    # if every narration line already has a primary asset but the build is still
    # below the visual minimum, add a real secondary cutaway to an existing scene.
    # This avoids both a fake duplicate and a slideshow-only workaround.
    min_assets = 8
    if len(records) < min_assets:
        print(f"Visual recovery: {len(records)}/{min_assets}; generating secondary cutaways.")
        for i, line in enumerate(story.get("lines", [])):
            if len(records) >= min_assets:
                break
            if not line.get("media_asset") or line.get("media_asset_2"):
                continue
            query = line.get("visual") or line.get("text") or "technology explainer"
            diagram = generate_local_diagram(query, 100 + i)
            if diagram:
                line["media_asset_2"] = diagram["local_path"]
                line["media_kind_2"] = "image"
                line["media_source_2"] = diagram
                records.append(diagram)
                print(f"Secondary cutaway assigned: scene={i} query='{query}'")

    MANIFEST.write_text(json.dumps(records, indent=2))
    (ROOT / "output/story.json").write_text(json.dumps(story, indent=2))
    print(f"After media fallback/recovery: {len(records)} assets")



if __name__ == "__main__":
    main()