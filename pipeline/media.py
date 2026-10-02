"""Free-media discovery and download for Bouriko.

Primary providers:
- Pixabay: free API for photos + videos.
- Coverr: free API for stock video.
- Pexels: optional if a key is available.

Every downloaded asset gets a sidecar attribution/source record. The pipeline
never treats a provider URL as permanently hotlinkable; media is downloaded
into output/media and rendered locally.
"""
import json, os, re
from pathlib import Path
from urllib.parse import quote
import requests

from common import ROOT, run

MEDIA_DIR = ROOT / "output/media"
MANIFEST = ROOT / "output/media_manifest.json"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")[:70] or "asset"


def _get(url, **kwargs):
    r = requests.get(url, timeout=45, **kwargs)
    r.raise_for_status()
    return r


def _download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=90) as r:
        r.raise_for_status()
        with path.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if chunk:
                    f.write(chunk)


def pixabay(query, kind):
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return []
    endpoint = "https://pixabay.com/api/videos/" if kind == "video" else "https://pixabay.com/api/"
    params = {
        "key": key, "q": query, "safesearch": "true",
        "per_page": 12, "order": "popular",
    }
    if kind == "image":
        params.update({"image_type": "photo", "orientation": "vertical"})
    d = _get(endpoint, params=params).json()
    hits = d.get("hits", [])
    out = []
    for h in hits:
        if kind == "video":
            sizes = h.get("videos", {})
            choice = sizes.get("large") or sizes.get("medium") or {}
            url = choice.get("url")
        else:
            url = h.get("largeImageURL") or h.get("webformatURL")
        if url:
            out.append({
                "provider": "pixabay",
                "kind": kind,
                "url": url,
                "source_url": h.get("pageURL"),
                "creator": h.get("user"),
                "title": h.get("tags", query),
            })
    return out


def pexels(query, kind):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return []
    endpoint = "https://api.pexels.com/v1/videos/search" if kind == "video" else "https://api.pexels.com/v1/search"
    headers = {"Authorization": key}
    params = {"query": query, "per_page": 12}
    if kind == "video":
        params.update({"orientation": "portrait", "size": "large"})
    else:
        params.update({"orientation": "portrait", "size": "large"})
    d = _get(endpoint, headers=headers, params=params).json()
    out = []
    for h in d.get("videos" if kind == "video" else "photos", []):
        if kind == "video":
            files = sorted(h.get("video_files", []), key=lambda x: (x.get("height", 0), x.get("width", 0)), reverse=True)
            url = files[0].get("link") if files else None
            creator = (h.get("user") or {}).get("name")
        else:
            url = (h.get("src") or {}).get("original")
            creator = (h.get("photographer"))
        if url:
            out.append({
                "provider": "pexels",
                "kind": kind,
                "url": url,
                "source_url": h.get("url"),
                "creator": creator,
                "title": h.get("alt") or query,
            })
    return out


def coverr(query):
    key = os.getenv("COVERR_API_KEY")
    if not key:
        return []
    d = _get(
        "https://api.coverr.co/videos/search",
        headers={"x-api-key": key},
        params={"query": query, "page_size": 12},
    ).json()
    out = []
    for h in d.get("hits", []):
        files = h.get("urls") or h.get("video_files") or {}
        url = None
        if isinstance(files, dict):
            for k in ("mp4", "1080p", "hd", "url"):
                if isinstance(files.get(k), str):
                    url = files[k]
                    break
        if not url and isinstance(h.get("download_url"), str):
            url = h["download_url"]
        if url:
            out.append({
                "provider": "coverr",
                "kind": "video",
                "url": url,
                "source_url": h.get("url") or h.get("page_url"),
                "creator": h.get("author") or h.get("creator"),
                "title": h.get("title") or query,
            })
    return out


def choose(query, kind):
    candidates = []
    # Pixabay first because it supplies both image and video search and is free.
    candidates += pixabay(query, kind)
    candidates += pexels(query, kind)
    if kind == "video":
        candidates += coverr(query)
    return candidates[:12]


def ensure_asset(action, index):
    query = str(action.get("query") or action.get("search") or "").strip()
    kind = str(action.get("kind") or "video").lower()
    if not query or kind not in {"image", "video"}:
        return None

    candidates = choose(query, kind)
    if not candidates:
        return None

    chosen = candidates[0]
    ext = ".mp4" if kind == "video" else ".jpg"
    path = MEDIA_DIR / f"{index:02}_{_slug(query)}{ext}"
    if not path.exists():
        _download(chosen["url"], path)

    record = {
        "index": index,
        "query": query,
        "kind": kind,
        "provider": chosen["provider"],
        "source_url": chosen["source_url"],
        "creator": chosen.get("creator"),
        "title": chosen.get("title"),
        "local_path": str(path.relative_to(ROOT)),
    }
    return record


def main():
    story = json.loads((ROOT / "output/story.json").read_text())
    records = []
    for i, line in enumerate(story.get("lines", [])):
        for action in line.get("visual_actions", []) or []:
            if str(action.get("type", "")).lower() != "media":
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
