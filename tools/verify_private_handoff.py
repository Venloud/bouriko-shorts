#!/usr/bin/env python3
"""Check that a downloaded private runner artifact matches the requested plan."""
import argparse
import json
import re
from pathlib import Path

META = Path("output/handoff_metadata.json")

def check(meta, sha, story_hash):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid source revision in workflow request")
    if not re.fullmatch(r"[0-9a-f]{64}", story_hash):
        raise ValueError("Invalid plan checksum in workflow request")
    if meta.get("schema") != 1 or meta.get("source_repo") != "Venloud/bouriko-shorts":
        raise ValueError("Artifact source marker is not Bouriko")
    if meta.get("public_sha") != sha or meta.get("original_story_sha256") != story_hash:
        raise ValueError("Private artifact does not match requested source revision and story")
    if not re.fullmatch(r"[1-9][0-9]{0,16}", str(meta.get("plan_run_id", ""))):
        raise ValueError("Missing original plan run")
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--public-sha", required=True)
    p.add_argument("--plan-sha", required=True)
    args = p.parse_args()
    check(json.loads(META.read_text(encoding="utf-8")), args.public_sha, args.plan_sha)
    print("PASS: private acquisition matches exact source commit and original plan hash")
