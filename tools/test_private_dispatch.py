#!/usr/bin/env python3
"""Offline test for cross-repo dispatch checks, with no GitHub token."""
import base64
import hashlib
import json
import sys
from pathlib import Path
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dispatch_private_media import create_payload
from verify_private_handoff import check

sha = "c" * 40
story = json.dumps({"lines": [{"text": "The intersection detects cars."}]}, separators=(",", ":")).encode()
wire = create_payload(story, sha, "321")
event = json.loads(wire)
assert event["event_type"] == "bouriko_acquire"
assert event["client_payload"]["source_repo"] == "Venloud/bouriko-shorts"
raw = zlib.decompress(base64.b64decode(event["client_payload"]["story_z"]))
assert raw == story
checksum = hashlib.sha256(raw).hexdigest()
assert event["client_payload"]["original_sha256"] == checksum

meta = {"schema": 1, "source_repo": "Venloud/bouriko-shorts",
        "public_sha": sha, "original_story_sha256": checksum, "plan_run_id": "321"}
assert check(meta, sha, checksum)

for corrupt in [
    {**meta, "public_sha": "f" * 40},
    {**meta, "original_story_sha256": "0" * 64},
    {**meta, "source_repo": "Venloud/kindled-iron-voice"},
]:
    try:
        check(corrupt, sha, checksum)
    except ValueError:
        pass
    else:
        raise AssertionError("An invalid cross-repository source was accepted")

try:
    create_payload(story, "not_a_revision", "321")
except ValueError:
    pass
else:
    raise AssertionError("Unpinned source code was accepted")
print("PASS: cross-repository story dispatch compression, integrity, and origin checks.")
