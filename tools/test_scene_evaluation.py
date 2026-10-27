#!/usr/bin/env python3
"""Offline tests for labeled real-video evaluation reporting (no model download)."""
import sys
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools"))
import evaluate_scene_vision as evaluator


class CalibrationTests(unittest.TestCase):
    def test_summary_does_not_call_small_dataset_calibrated(self):
        rows=[{"expected_relevant": True,"model_accepted":True},
              {"expected_relevant":False,"model_accepted":False}]
        result=evaluator.summarize(rows)
        self.assertEqual(result["accuracy"],1.0)
        self.assertFalse(result["calibration_sufficient"])

    def test_false_positive_and_false_negative_reported(self):
        rows=[{"expected_relevant":True,"model_accepted":False},
              {"expected_relevant":True,"model_accepted":True},
              {"expected_relevant":False,"model_accepted":True},
              {"expected_relevant":False,"model_accepted":False}]
        result=evaluator.summarize(rows)
        self.assertEqual(result["counts"]["false_positive"],1)
        self.assertEqual(result["counts"]["false_negative"],1)
        self.assertTrue(result["calibration_sufficient"])

    def test_real_local_clips_required_and_cross_directory_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            video=root/"video.mp4"
            video.write_bytes(b"fixture")
            one={"clip":"video.mp4","topic":"roads",
                 "visual":"traffic light", "expected_relevant":True}
            def fake_inspect(path, narration, topic, visual_hint="",library=None,required_names=None):
                return {"accepted":True,"sampled_frames":4}
            report=evaluator.evaluate([one],root,root,evaluator=fake_inspect)
            self.assertEqual(report["summary"]["counts"]["true_positive"],1)
            self.assertTrue(report["model_evaluated"])
            with self.assertRaises(ValueError):
                evaluator.evaluate([{**one,"clip":"../outside.mp4"}],
                                   root,root,evaluator=fake_inspect)

    def test_invalid_labels_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td).resolve()
            (path/"clip.mp4").write_bytes(b"fixture")
            bad={"clip":"clip.mp4", "visual":"map", "topic":"roads",
                 "expected_relevant":"true"}
            with self.assertRaisesRegex(ValueError,"boolean"):
                evaluator.evaluate([bad],path,path,evaluator=lambda *a,**kw:None)


if __name__=="__main__":
    unittest.main()
