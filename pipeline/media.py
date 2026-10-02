"""Free-media discovery and download for Bouriko.

Providers:
- Pixabay/Pexels/Coverr when configured.
- Wikimedia Commons as a no-key fallback.

The renderer should never silently turn a missing-media build into a slideshow.
Every downloaded asset records its source and license metadata.
"""
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


def choose(query, kind):
    candidates = []
    # Prefer configured stock providers, then Commons.
    for fn in (pixabay, pexels):
        try:
            candidates += fn(query, kind)
        except Exception:
            pass
    if kind == "video":
        try:
            candidates += coverr(query)
        except Exception:
            pass
    try:
        candidates += commons(query, kind)
    except Exception:
        pass
    return candidates[:20]


def ensure_asset(action, index):
    query = str(action.get("query") or action.get("search") or "").strip()
    kind = str(action.get("kind") or "video").lower()
    if not query or kind not in {"image","video"}:
        return None

    candidates = choose(query, kind)
    if not candidates:
        return None

    # A provider can return a valid search result whose file URL is temporarily
    # rate-limited or unavailable. Try the next candidate instead of aborting
    # the entire video build.
    for candidate_no, chosen in enumerate(candidates):
        ext = (
            ".webm"
            if chosen["provider"] == "wikimedia_commons"
            and "webm" in chosen["url"].lower()
            else (".mp4" if kind == "video" else ".jpg")
        )
        path = MEDIA_DIR / f"{index:02}_{_slug(query)}_{candidate_no}{ext}"
        if path.exists() and path.stat().st_size > 0:
            break
        try:
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
        return None

    return {
        "index": index, "query": query, "kind": kind,
        "provider": chosen["provider"], "source_url": chosen.get("source_url"),
        "creator": chosen.get("creator"), "title": chosen.get("title"),
        "license": chosen.get("license"), "license_url": chosen.get("license_url"),
        "local_path": str(path.relative_to(ROOT))
    }

def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    records = []
    for i, line in enumerate(story.get("lines", [])):
        for action in line.get("visual_actions", []) or []:
            if str(action.get("type","")).lower() != "media":
                continue
            rec = ensure_asset(action, i)
            if rec:
                line["media_asset"] = rec["local_path"]
                line["media_source"] = rec
                records.append(rec)
                break

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(records, indent=2))
    (ROOT / "output/story.json").write_text(json.dumps(story, indent=2))
    print(f"Media assets downloaded: {len(records)}")


if __name__ == "__main__":
    main()
