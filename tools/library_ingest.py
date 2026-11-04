#!/usr/bin/env python3
"""Save a finished build's downloaded media into the shared local asset library (Venloud/vandam-assets).

Run only after a local build passed QA and rendered:
    VANDAM_ASSET_LIBRARY=C:\\Users\\van02\\Desktop\\cody\\asset-library python tools/library_ingest.py --video <id>

Generated diagrams, AI images and owner references are never added. Assets with a restricted or unknown
licence are kept for Bouriko only; the library decides what other projects may reuse.
"""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "output/media_manifest.json"
SKIP = {"local_diagram", "gemini_ai", "owner_reference"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, help="id of the finished video, recorded as the asset's use")
    ap.add_argument("--manifest", default=str(MANIFEST))
    args = ap.parse_args(argv)
    root = os.getenv("VANDAM_ASSET_LIBRARY")
    if not root:
        print("VANDAM_ASSET_LIBRARY is not set; nothing saved")
        return 1
    from vandam_assets import Library

    records = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    keep = [r for r in records if r.get("provider") not in SKIP and r.get("local_path")]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(keep, f)
    try:
        result = Library(root).seed_bouriko_manifest(f.name, ROOT, args.video)
    finally:
        os.unlink(f.name)
    print(f"Asset library: {result['added']} saved or re-used, {result['skipped']} skipped, "
          f"{len(records) - len(keep)} generated/owner assets left out")
    return 0


if __name__ == "__main__":
    sys.exit(main())
