#!/usr/bin/env python3
"""Offline Openverse provider regression (mocked HTTP; no network)."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import media


class Reply:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code = status
        self._body = body if body is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise media.requests.HTTPError(f"HTTP {self.status_code}")


def hit(i, lic, **kw):
    return {"id": f"id{i}", "title": f"traffic light {i}", "url": f"https://img.example/{i}.jpg",
            "foreign_landing_url": f"https://flickr.example/{i}", "creator": f"maker{i}",
            "license": lic, "license_version": "4.0", "license_url": f"https://creativecommons.org/{lic}",
            "attribution": f'"traffic light {i}" by maker{i}', "source": "flickr", **kw}


BODY = {"results": [hit(1, "by"), hit(2, "cc0"), hit(3, "by-nc"), hit(4, "by-sa"),
                    hit(5, "by-nd"), hit(6, "pdm"), hit(7, "by", mature=True)]}

with tempfile.TemporaryDirectory() as tmp:
    media.OPENVERSE_CACHE = Path(tmp)

    with patch.dict(os.environ, {"BOURIKO_OPENVERSE": ""}), patch("media.requests.get") as get:
        assert media.openverse("traffic light", "image") == [], "Openverse must be off by default"
        get.assert_not_called()

    os.environ["BOURIKO_OPENVERSE"] = "1"
    assert media.openverse("traffic light", "video") == [], "Openverse has no video"

    with patch("media.requests.get", return_value=Reply(body=BODY)) as get:
        found = media.openverse("traffic light", "image")
        params = get.call_args.kwargs["params"]
        assert params["license"] == "by,cc0,pdm", params
    assert [f["openverse_id"] for f in found] == ["id1", "id2", "id6"], "NC/SA/ND/mature must be excluded"
    first = found[0]
    for key in ("creator", "source_url", "license", "license_url", "attribution"):
        assert first[key], f"missing rights field {key}"
    assert first["license"] == "CC BY 4.0" and found[2]["license"].startswith("Public Domain Mark")

    with patch("media.requests.get") as get:
        assert len(media.openverse("traffic light", "image")) == 3, "cached results should be reused"
        get.assert_not_called()

    with patch("media.requests.get", return_value=Reply(429, headers={"Retry-After": "60"})):
        assert media.openverse("rate limited query", "image") == []

    with patch("media.requests.get", return_value=Reply(body={"detail": "bad"})):
        try:
            media.openverse("broken query", "image")
            raise AssertionError("invalid response accepted")
        except ValueError:
            pass

    with patch("media.requests.get", return_value=Reply(500)):
        try:
            media.openverse("server error", "image")
            raise AssertionError("HTTP 500 accepted")
        except media.requests.HTTPError:
            pass

    # choose() keeps other providers and survives an Openverse failure.
    commons_hit = [{"provider": "wikimedia_commons", "kind": "image", "url": "https://c.example/a.jpg"}]
    with patch("media.pixabay", return_value=[]), patch("media.pexels", return_value=[]), \
         patch("media.mixkit", return_value=[]), patch("media.youtube_cc", return_value=[]), \
         patch("media.commons", return_value=commons_hit), \
         patch("media.openverse", side_effect=RuntimeError("down")):
        got = media.choose("traffic light", "image")
    assert got and got[0]["provider"] == "wikimedia_commons", "fallback provider lost"

print("PASS: Openverse off by default, license filter, rights metadata, cache, 429, invalid response, fallback")
