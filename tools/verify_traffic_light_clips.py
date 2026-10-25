"""Fail-closed proof for four real traffic-light clips, each at most 3 seconds.
Does not download YouTube videos or upload/publish anything.
Usage: python tools/verify_traffic_light_clips.py
Approval receipts must identify the real source URL, lawful usage basis, and independent human visual review.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "assets" / "video_reference" / "traffic_light_detector" / "clips"
REQUIRED = {
    "01_car_arrives.mp4": "car arrives at intersection",
    "02_light_turns_red.mp4": "traffic light changes to red",
    "03_light_turns_green.mp4": "traffic light changes to green",
    "04_car_leaves.mp4": "car leaves intersection",
}

def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height",
         "-of", "json", str(path)],
        text=True, capture_output=True, check=True,
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not any(s.get("codec_type") == "video" for s in streams):
        raise ValueError(f"{path.name}: no video stream")
    length = float(data["format"]["duration"])
    if not 0 < length <= 3.0:
        raise ValueError(f"{path.name}: {length:.3f}s is outside (0, 3] seconds")
    return round(length, 3)

def main():
    receipts_path = DIR / "review.json"
    if not receipts_path.exists():
        raise SystemExit("NOT PASSED: clips/review.json is missing")
    receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
    errors, successes = [], []
    for filename, event in REQUIRED.items():
        path = DIR / filename
        receipt = receipts.get(filename, {})
        try:
            if not path.is_file() or path.stat().st_size < 10000:
                raise ValueError("missing or invalid clip")
            duration = probe(path)
            if receipt.get("event") != event:
                raise ValueError("event label or manual scene verification missing")
            if receipt.get("visually_verified") is not True:
                raise ValueError("human confirmation of the actual depicted event missing")
            if receipt.get("rights_verified") is not True:
                raise ValueError("lawful clip reuse verification missing")
            if not receipt.get("source_url") or not receipt.get("license_or_permission"):
                raise ValueError("source or authorization evidence missing")
            successes.append({"clip": filename, "seconds": duration})
        except Exception as exc:
            errors.append(f"{filename}: {exc}")
    if errors:
        print("NOT PASSED: all four real events and rights receipts are required.")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PASS: all four distinct traffic light events verified, each <= 3 seconds")
    print(json.dumps(successes, indent=2))

if __name__ == "__main__":
    main()
