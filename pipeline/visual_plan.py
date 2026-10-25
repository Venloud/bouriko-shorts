"""Narration-grounded shot selection and owner-approved local reference assets."""
import json
from common import ROOT

SHOTS = {
 "gps": [
 "phone navigation map blue GPS dot", "GPS satellites orbiting Earth", "satellite positioning signals reaching a smartphone", "four GPS satellites signal timing trilateration", "GPS signal reflection between city buildings", "GPS navigation blue location marker", "phone navigation ETA arrival time", "navigation traffic congestion route map", "traffic accident delay GPS navigation ETA", "navigation alternative exit reroute map", "GPS location versus travel time visual comparison", "navigation blue location dot ETA"],
 "traffic_light": [
 "car stops at traffic signal junction", "road pavement induction loop sensor", "traffic detection electromagnetic loop diagram", "car driving over road detection sensor", "traffic signal controller cabinet", "traffic signal changes green at junction", "traffic camera radar intersection", "traffic light timer diagram"],
 "beauty": [
 "skin cream skincare bottle closeup", "cosmetics lab emulsion blending", "oil water emulsifier laboratory closeup", "glycerin moisture skincare cosmetic demonstration", "skincare ingredient mixing production", "cosmetic preservative microbiology test", "beauty product temperature stability laboratory", "cosmetic scientist skin safety testing"],
 "jjk": ["original stylized fantasy competition rules diagram", "original illustrated fantasy colony map", "original fantasy scoring points graphic"],
 "iphone": ["smartphone official product photo comparison", "smartphone display closeup", "smartphone camera lens technical closeup"],
 "faceless_youtube": ["vertical short video editing timeline", "script storyboard workstation", "voiceover audio waveform editing", "stock footage trimming on editing timeline", "animated captions short form vertical video"]
}

def planned_query(topic_id, line, index):
    shots = SHOTS.get(topic_id, [])
    if index < len(shots):
        return shots[index]
    return (line.get("text") or "specific subject").strip()[:120] + " visually relevant stock footage"

def approved_assets(story):
    manifest_file = ROOT / "assets/video_reference/manifest.json"
    if not manifest_file.exists():
        return {}
    records = json.loads(manifest_file.read_text(encoding="utf-8")).get("assets", [])
    chosen = {}
    for record in records:
        if record.get("topic_id") != story.get("test_topic_id"):
            continue
        # Presence is required: neither the manifest nor a promised asset pack suffices.
        path = (ROOT / str(record.get("path",""))).resolve()
        if not path.is_file() or ROOT.resolve() not in path.parents:
            continue
        if path.suffix.lower() not in {".png",".jpg",".jpeg",".webp",".mp4",".webm"}:
            continue
        for index in record.get("target_script_lines", []):
            if isinstance(index,int) and index >= 0:
                chosen.setdefault(index, (record,path))
    return chosen
