#!/usr/bin/env python3
"""Offline tests for Bouriko's subject-agnostic YouTube segment selector."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
import scene_library as library
from visual_plan import planned_query


class SceneLibraryTests(unittest.TestCase):
    def test_vtt_captions(self):
        vtt = ("WEBVTT\n\n00:01:07.100 --> 00:01:10.200\n"
               "Kenjaku starts the Culling Game.\n\n"
               "00:01:11.100 --> 00:01:14.100\n"
               "Players collect points for new rules.\n\n")
        cues = library.parse_captions(vtt)
        self.assertEqual(len(cues), 2)
        self.assertAlmostEqual(cues[0]["start"], 67.1)
        hit = library.best_caption_span(cues, "Kenjaku starts the Culling Game")
        self.assertIsNotNone(hit)
        self.assertGreaterEqual(hit["start"], 0)
        self.assertLess(hit["end"], 80)

    def test_json3_captions(self):
        data = {"events": [{"tStartMs": 4000, "dDurationMs": 2200, "segs": [
            {"utf8": "Satellites send GPS signals to phones"}]}]}
        cues = library.parse_captions(json.dumps(data), "json3")
        self.assertEqual(cues[0]["start"], 4)
        self.assertEqual(cues[0]["end"], 6.2)

    def test_unrelated_metadata_is_rejected(self):
        unrelated = {"provider":"youtube_cc", "url":"https://www.youtube.com/watch?v=abc",
            "license":"Creative Commons Attribution license", "title":"Cooking cake at home"}
        with patch.object(library, "read_subtitles", return_value=(
            [{"start":20,"end":24,"text":"Kenjaku starts the Culling Game"}], "manual")):
            self.assertIsNone(library.choose_segment(
                [unrelated], "Kenjaku starts the Culling Game", "Jujutsu Kaisen"))

    def test_real_caption_timecode_not_guessed(self):
        candidate = {"provider":"youtube_cc", "url":"https://www.youtube.com/watch?v=abc",
                     "youtube_id":"abc", "license":"Creative Commons Attribution license",
                     "title":"Jujutsu Kaisen Culling Game explained S3E04"}
        captions = [
            {"start":14, "end":17, "text":"Mushroom forest and magic islands"},
            {"start":98, "end":101, "text":"Kenjaku starts the Culling Game ritual"},
        ]
        with patch.object(library, "read_subtitles", return_value=(captions,"manual")):
            result = library.choose_segment([candidate],
                "Kenjaku starts the Culling Game", "Jujutsu Kaisen")
        self.assertIsNotNone(result)
        self.assertGreater(result["scene_start_seconds"], 90)
        self.assertEqual(result["season_hint"], 3)
        self.assertEqual(result["episode_hint"], 4)
        self.assertEqual(result["episode_hint_source"], "video_title_unverified")
        self.assertFalse(result["rights_status"] == "verified")
        self.assertEqual(result["semantic_status"], "TRANSCRIPT_MATCH_FRAME_REVIEW_REQUIRED")

    def test_missing_captions_does_not_create_fake_timecodes(self):
        candidate = {"provider":"youtube_cc", "url":"https://www.youtube.com/watch?v=abc",
                     "license":"Creative Commons Attribution license",
                     "title":"Jujutsu Kaisen Culling Game"}
        with patch.object(library, "read_subtitles", return_value=([], "unavailable")):
            self.assertIsNone(library.choose_segment([candidate],
                "Kenjaku starts the Culling Game", "Jujutsu Kaisen"))

    def test_generic_topic_guidance(self):
        line = {"text":"Kenjaku creates dangerous colonies for the Culling Game"}
        q = planned_query("unknown_topic", line, 0, "Jujutsu Kaisen rules")
        self.assertIn("Jujutsu Kaisen", q)
        self.assertIn("Kenjaku", q)
        g = planned_query("unknown_topic",
            {"text":"Satellites let phones estimate GPS position"},0,"GPS explained")
        self.assertIn("GPS", g)
        self.assertIn("Satellites", g)

    def test_no_generic_jjk_template(self):
        import visual_plan
        self.assertNotIn("jjk", visual_plan.SHOTS)

    def test_prohibited_caption_host(self):
        candidate={"subtitles":{"en":[{"ext":"vtt","url":"https://evil.example/captions"}]}}
        self.assertIsNone(library.subtitle_url(candidate))

    def test_ranked_caption_moments_try_another_timestamp(self):
        candidate = {"provider":"youtube_cc",
                     "url":"https://www.youtube.com/watch?v=scene123",
                     "youtube_id":"scene123",
                     "license":"Creative Commons Attribution license",
                     "title":"GPS satellite navigation"}
        captions = [
            {"start":12, "end":15, "text":"GPS satellites send location signals"},
            {"start":60, "end":63, "text":"GPS satellites send navigation signals"},
        ]
        with patch.object(library, "read_subtitles", return_value=(captions, "manual")):
            first = library.choose_segment([candidate],
                "GPS satellites send signals", "GPS")
            self.assertIsNotNone(first)
            second = library.choose_segment([candidate],
                "GPS satellites send signals", "GPS",
                used={("scene123", first["scene_start_seconds"])})
        self.assertIsNotNone(second)
        self.assertNotEqual(second["scene_start_seconds"], first["scene_start_seconds"])

    def test_reuse_prevents_duplicate_video_second(self):
        candidate = {"provider":"youtube_cc", "url":"https://www.youtube.com/watch?v=abc",
                     "youtube_id":"abc", "license":"Creative Commons Attribution license",
                     "title":"Satellites GPS explained"}
        cues=[{"start":13,"end":16,"text":"Satellites send GPS signals to your phone"}]
        with patch.object(library,"read_subtitles",return_value=(cues,"automatic")):
            first=library.choose_segment([candidate],"Satellites send GPS signals",
                                         "GPS explained")
            self.assertIsNotNone(first)
            second=library.choose_segment([candidate],"Satellites send GPS signals",
                "GPS explained",used={("abc", first["scene_start_seconds"])})
            self.assertIsNone(second)


if __name__ == "__main__":
    unittest.main()
