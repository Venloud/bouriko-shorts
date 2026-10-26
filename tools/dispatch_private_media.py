#!/usr/bin/env python3
"""Send one checksum-bound Bouriko plan to the dedicated private Windows worker."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request
import zlib

def create_payload(story_bytes, source_sha, run_id):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("Expected pinned public 40-character commit")
    if not re.fullmatch(r"[1-9][0-9]{0,16}", str(run_id)):
        raise ValueError("Invalid public run ID")
    story = json.loads(story_bytes)
    if not isinstance(story, dict) or not isinstance(story.get("lines"), list) or not story["lines"]:
        raise ValueError("No script lines to dispatch")
    if len(story_bytes) > 250000:
        raise ValueError("Script is too large for the private worker")
    compressed = base64.b64encode(zlib.compress(story_bytes, 9)).decode("ascii")
    event = {"event_type": "bouriko_acquire",
             "client_payload": {
                 "source_repo": "Venloud/bouriko-shorts",
                 "public_sha": source_sha,
                 "source_run_id": str(run_id),
                 "original_sha256": hashlib.sha256(story_bytes).hexdigest(),
                 "story_z": compressed}}
    wire = json.dumps(event, separators=(",", ":")).encode("utf-8")
    if len(wire) >= 60000:
        raise ValueError("Compressed story still exceeds the GitHub dispatch limit")
    return wire

def main():
    token = os.environ.get("BOURIKO_PRIVATE_RUNNER_TOKEN")
    if not token:
        raise SystemExit("Missing Bouriko secret BOURIKO_PRIVATE_RUNNER_TOKEN")
    content = Path("output/story.json").read_bytes()
    wire = create_payload(content, os.environ.get("GITHUB_SHA", ""), os.environ.get("GITHUB_RUN_ID", ""))
    request = urllib.request.Request(
        "https://api.github.com/repos/Venloud/van02utuberunner/dispatches",
        data=wire, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 204:
                raise SystemExit(f"Private runner dispatch failed with HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Private runner dispatch rejected with HTTP {exc.code}: check token permissions and repo Actions settings")
    print(f"Private runner dispatched for Bouriko run {os.environ['GITHUB_RUN_ID']}; story checksum bound and source SHA pinned")
    print("This is an accepted dispatch, not evidence of downloaded footage.")

if __name__ == "__main__":
    main()
