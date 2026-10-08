import unittest
from experiments.scene_locator import parse_srt, locate, score


class SceneLocatorTests(unittest.TestCase):
    def setUp(self):
        cues = parse_srt("""1
00:01:02,000 --> 00:01:05,500
The Culling Game has begun.

2
00:02:10,000 --> 00:02:13,000
Yuji and Megumi enter the colony.
""")
        self.episodes = [{"episode": "S3E01", "subtitle_path": "sample.srt", "cues": cues}]

    def test_srt_times(self):
        self.assertEqual(self.episodes[0]["cues"][0]["start"], 62.0)

    def test_specific_match(self):
        result = locate({"evidence_query": "Yuji and Megumi enter the colony"}, self.episodes)
        self.assertEqual(result["status"], "candidate")
        self.assertEqual(result["match"]["episode"], "S3E01")
        self.assertEqual(result["match"]["start"], 128.5)

    def test_no_guess(self):
        result = locate({"evidence_query": "Gojo uses hollow purple"}, self.episodes)
        self.assertEqual(result["status"], "needs_review")

    def test_action_not_guessed(self):
        result = locate({"evidence_query": "Yuji and Megumi enter the colony", "visual_type": "action_only"}, self.episodes)
        self.assertEqual(result["reason"], "action_requires_visual_verification")

    def test_score(self):
        self.assertGreater(score("Yuji enters colony", "Yuji enters the colony"), 0.8)


if __name__ == "__main__":
    unittest.main()
