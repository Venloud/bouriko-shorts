#!/usr/bin/env python3
"""Offline library-first regression (no network). Needs vandam_assets (pip, or a sibling checkout) and Pillow."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "tools"))
sibling = ROOT.parent / "vandam-assets"
if sibling.is_dir():
    sys.path.insert(0, str(sibling))
try:
    from vandam_assets import Library
    from PIL import Image
except ImportError as exc:
    print(f"SKIP: {exc} (install vandam_assets and Pillow to run this test)")
    sys.exit(0)

import media
import library_ingest


def jpeg(path, color):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), color).save(path, "JPEG")
    return path


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    lib_root = tmp / "lib"
    media.MEDIA_DIR = tmp / "bouriko/output/media"
    media.ROOT = tmp / "bouriko"
    action = {"kind": "image", "query": "traffic light at a busy intersection"}

    # 1. Off by default: providers are searched exactly as before.
    with patch.dict(os.environ, {"VANDAM_ASSET_LIBRARY": ""}), \
            patch("media.choose", return_value=[]) as choose, \
            patch("media.generate_local_diagram", return_value={"provider": "local_diagram"}):
        assert media.ensure_asset(action, 1)["provider"] == "local_diagram"
        choose.assert_called_once()

    os.environ["VANDAM_ASSET_LIBRARY"] = str(lib_root)
    lib = Library(lib_root)
    lib.add(jpeg(tmp / "src/a.jpg", "red"), {
        "kind": "image", "provider": "pexels", "source_url": "https://pexels.com/photo/1",
        "download_url": "https://images.pexels.com/1.jpg", "creator": "A", "license": "Pexels license",
        "tags": ["traffic", "light", "intersection"]}, "openmontage")

    # 2. A good match is reused; no provider is called.
    with patch("media.choose") as choose:
        rec = media.ensure_asset(action, 2)
        choose.assert_not_called()
    assert rec["library_id"] and rec["provider"] == "pexels" and rec["license"] == "Pexels license"
    assert (media.ROOT / rec["local_path"]).is_file()

    # 3. Already used in this video, a weak match, or a lookup error -> fall through to providers.
    with patch("media.choose", return_value=[]) as choose, patch("media.generate_local_diagram", return_value=None), \
            patch("media.generate_ai_image", return_value=None):
        assert media.ensure_asset(action, 3, {"https://images.pexels.com/1.jpg"}) is None
        assert media.ensure_asset({"kind": "image", "query": "traffic jam on a rainy highway bridge"}, 4) is None
        with patch.object(Library, "find", side_effect=ValueError("corrupt index")):
            assert media.ensure_asset(action, 5) is None
        assert choose.call_count == 3

    # 4. Ingest after a finished build: downloaded media saved, generated media left out, uses recorded.
    broot = media.ROOT
    jpeg(broot / "output/media/01_stock.jpg", "blue")
    jpeg(broot / "output/media/02_ai.jpg", "green")
    manifest = tmp / "manifest.json"
    manifest.write_text(json.dumps([
        {"provider": "wikimedia_commons", "kind": "image", "url": "https://c/1.jpg", "source_url": "https://c/File:1",
         "license": "CC0", "query": "radar speed sensor", "local_path": "output/media/01_stock.jpg"},
        {"provider": "gemini_ai", "kind": "image", "license": "AI-generated", "source_url": "https://ai",
         "local_path": "output/media/02_ai.jpg"},
        {**rec},
    ]), encoding="utf-8")
    with patch.object(library_ingest, "ROOT", broot):
        assert library_ingest.main(["--video", "ep1", "--manifest", str(manifest)]) == 0
    s = Library(lib_root).stats()
    assert s["assets"] == 2, s  # the CC0 still + the already-stored Pexels photo; no AI image
    used = Library(lib_root).records()[rec["library_id"]]["uses"]
    assert [u["video"] for u in used] == ["ep1"], used

    # 5. Assets used in ep1 are held back by the 10-video cooldown, then found again once it has passed.
    assert Library(lib_root).find("radar speed sensor", "image", "bouriko") == []
    hits = Library(lib_root).find("radar speed sensor", "image", "bouriko", cooldown_videos=0)
    assert hits and hits[0]["provider"] == "wikimedia_commons"

print("PASS: library off by default, reuse without provider calls, fallthrough on miss/weak/used/error, "
      "post-build ingest skips generated media and records uses")
