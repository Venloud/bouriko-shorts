#!/usr/bin/env python3
"""Offline regression test for the October 25 GPS visual-selection failure."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"pipeline"))
from visual_plan import planned_query, approved_assets, requires_diagram, diagram_beat

story={"test_topic_id":"gps","lines":[{"text":"Your phone can show a blue dot on a map."},{"text":"GPS satellites constantly transmit their positions."},{"text":"Your phone estimates the signals."}]}
queries=[planned_query("gps",line,i) for i,line in enumerate(story["lines"])]
assert all("illustration" not in x.lower() for x in queries), queries
assert "phone" in queries[0].lower() and "satellite" in queries[1].lower(), queries
manifest=json.loads((ROOT/"assets/video_reference/manifest.json").read_text())
gps=[x for x in manifest["assets"] if x.get("topic_id")=="gps"]
assert gps, "Missing GPS asset registration"
assets=approved_assets(story)
asset_file=ROOT/gps[0]["path"]
if asset_file.is_file():
    assert 0 in assets, "Existing owner-provided GPS asset was ignored"
else:
    assert not assets, "Manifest entry cannot stand in for missing image"
print("PASS: GPS narration queries are topical, no illustration search; local image resolved when present")

# Real narration about mechanism must never be matched to generic traffic stock.
examples = [
 ("The induction loop under the road changes its magnetic field.", "MAGNETIC FIELD CHANGE"),
 ("The controller receives that detection signal.", "SENSOR TO CONTROLLER"),
 ("Radar and cameras can also detect a waiting vehicle.", "CAMERA AND RADAR"),
 ("Some bicycles are harder for these sensors to detect.", "BICYCLE DETECTION"),
]
for narration, expected in examples:
    line = {"text": narration}
    assert requires_diagram("traffic_light", line), narration
    assert diagram_beat(line) == expected, (narration, diagram_beat(line))
assert not requires_diagram("traffic_light", {"text": "A car drives through the green traffic light"})
print("PASS: mechanism beats route to explanatory diagrams, real-life traffic beats stay footage candidates")
