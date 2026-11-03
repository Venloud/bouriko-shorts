#!/usr/bin/env python3
"""Real CLIP calibration harness for approved, local video excerpts.

No model downloads happen until the operator executes this script.
The fixture list must contain labeled REAL positive and negative clips,
and the output lives in a private directory, not GitHub artifacts.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
from frame_vision import inspect_clip
from scene_library import LIBRARY


def summarize(rows):
    totals = {"true_positive": 0, "true_negative": 0,
              "false_positive": 0, "false_negative": 0, "error": 0}
    for row in rows:
        if row.get("error"):
            totals["error"] += 1
            continue
        expected, detected = row["expected_relevant"], row["model_accepted"]
        totals[("true_positive" if expected else "false_positive") if detected else
               ("false_negative" if expected else "true_negative")] += 1
    positives = totals["true_positive"] + totals["false_negative"]
    negatives = totals["true_negative"] + totals["false_positive"]
    total = positives + negatives
    return {
        "counts": totals, "evaluated": total,
        "recall": round(totals["true_positive"] / positives, 3) if positives else None,
        "false_positive_rate": round(totals["false_positive"] / negatives, 3) if negatives else None,
        "accuracy": round((totals["true_positive"] + totals["true_negative"]) / total, 3)
                    if total else None,
        "calibration_sufficient": positives >= 2 and negatives >= 2 and totals["error"] == 0,
        "status": ("NEEDS_MORE_REAL_LABELED_POSITIVES_AND_NEGATIVES"
                   if positives < 2 or negatives < 2 else
                   "MODEL_ERRORS" if totals["error"] else
                   "REVIEW_THRESHOLD_ERRORS_AND_VIDEO_FRAMES"),
    }


def evaluate(fixtures, dataset_base, library, evaluator=inspect_clip):
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= 100:
        raise ValueError("A list of 1-100 labeled video fixtures is required")
    rows = []
    for i, fixture in enumerate(fixtures):
        if not isinstance(fixture, dict):
            raise ValueError(f"Fixture {i} must be an object")
        relative = fixture.get("clip")
        if not isinstance(relative, str) or not relative:
            raise ValueError(f"Fixture {i} has no local clip filename")
        path = (dataset_base / relative).resolve()
        if dataset_base not in path.parents or not path.is_file():
            raise ValueError(f"Fixture {i} is outside the dataset or missing")
        label = fixture.get("expected_relevant")
        if type(label) is not bool:
            raise ValueError(f"Fixture {i} needs a boolean expected_relevant label")
        topic = str(fixture.get("topic") or "").strip()
        visual = str(fixture.get("visual") or "").strip()
        if not topic or not visual:
            raise ValueError(f"Fixture {i} needs topic and visual text")
        row = {"fixture": i, "clip": relative, "topic": topic,
               "visual": visual, "expected_relevant": label}
        try:
            result = evaluator(path, fixture.get("narration", visual), topic,
                               visual_hint=visual, library=library,
                               required_names=fixture.get("required_entities"))
            row.update({"model_accepted": bool(result.get("accepted")),
                        "verdict": result})
        except Exception as exc:
            row["error"] = type(exc).__name__ + ": " + str(exc)[:300]
        rows.append(row)
    return {"schema": 1, "model_evaluated": not any(x.get("error") for x in rows),
            "summary": summarize(rows), "fixtures": rows,
            "human_rights_review_required": True,
            "thresholds_automatically_approved": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, required=True,
                        help="Private JSON array of labeled local video fixtures")
    parser.add_argument("--output", type=Path, default=LIBRARY / "frame_evaluation.json")
    parser.add_argument("--library", type=Path, default=LIBRARY)
    args = parser.parse_args()
    input_path = args.fixtures.expanduser().resolve()
    dataset_base = input_path.parent
    report = evaluate(json.loads(input_path.read_text(encoding="utf-8")),
                      dataset_base, args.library.expanduser().resolve())
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Private evaluation saved: {output}")
    if not report["summary"]["calibration_sufficient"]:
        raise SystemExit("Calibration is INCOMPLETE: review/add labeled positives and negatives")
    if (report["summary"]["counts"]["false_positive"] or
            report["summary"]["counts"]["false_negative"]):
        raise SystemExit("Model thresholds need review; nonzero errors on labeled fixtures")


if __name__ == "__main__":
    main()
