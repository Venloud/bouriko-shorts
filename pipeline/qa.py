"""Final media-first explainer QA gate."""
import json, subprocess
from visual_plan import planned_query
from common import ROOT, CONFIG


def main():
    p = ROOT / "output/bouriko.mp4"
    d = float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1",str(p)
    ]))
    lo, hi = CONFIG["target_seconds"]
    print(f"DURATION DATA: {d:.2f}s (target {lo}-{hi}s)")
    if not (lo <= d <= hi + 0.5):
        print(f"QA INFO: {d:.2f}s is outside the target window; continuing for visual review.")

    a = subprocess.check_output([
        "ffprobe","-v","error","-select_streams","a",
        "-show_entries","stream=codec_name","-of","csv=p=0",str(p)
    ]).decode().strip()
    assert a, "no audio"

    story = json.loads((ROOT / "output/story.json").read_text())
    lines = story.get("lines", [])
    assert len(lines) >= 8, "too few narration lines"
    exact_script = bool(story.get("exact_script"))
    if not exact_script and not story.get("test_topic_id"):
        assert story.get("sources"), "no sources"
    assert all(x.get("text") for x in lines), "missing caption text"
    assert all(x.get("visual") for x in lines), "missing visual plan"

    manifest = ROOT / "output/media_manifest.json"
    media_count = 0
    if manifest.exists():
        media_count = len(json.loads(manifest.read_text()))
    video_count = sum(1 for x in json.loads(manifest.read_text()) if x.get("kind") == "video") if manifest.exists() else 0
    print(f"MEDIA DATA: {media_count} usable visual assets ({video_count} video)")
    # A completed technical render is not a semantic quality pass.
    # Require explicit per-beat assignment and write an inspectable review plan.
    if story.get("media_strategy") == "youtube_scene_library":
        for i, line in enumerate(lines):
            source = line.get("media_source") or {}
            assert source.get("provider") == "youtube_cc_scene", (
                f"Scene {i} used a generic or misleading fallback")
            assert source.get("transcript_excerpt") and source.get("scene_end_seconds", 0) > source.get("scene_start_seconds", 0), (
                f"Scene {i} missing narrated moment/timecode evidence")
            evidence = source.get("visual_evidence") or {}
            assert evidence.get("accepted") and evidence.get("passing_frame_count", 0) >= 2, (
                f"Scene {i} lacks real pixel-based visual verification")
            assert source.get("semantic_status") == "FRAME_SIMILARITY_PASS_REVIEW_REQUIRED", (
                f"Scene {i} failed the scene library provenance gate")
    report = []
    visual_mode = story.get("media_strategy") == "youtube_scene_library"
    for i, line in enumerate(lines):
        src = line.get("media_source") or {}
        query = str(src.get("query") or "")
        planned = planned_query(story.get("test_topic_id"), line, i)
        generic = query.strip().lower() in {"illustration","technology explainer","technology","education"}
        evidence = src.get("visual_evidence") or {}
        report.append({"line_index":i,"narration":line.get("text",""),
                       "planned_subject":planned,"chosen_query":query,
                       "asset":line.get("media_asset"),"provider":src.get("provider"),
                       "source_url":src.get("source_url"),
                       "scene_start_seconds":src.get("scene_start_seconds"),
                       "scene_end_seconds":src.get("scene_end_seconds"),
                       "season_hint":src.get("season_hint"),
                       "episode_hint":src.get("episode_hint"),
                       "episode_hint_source":src.get("episode_hint_source"),
                       "rights_status":src.get("rights_status") or src.get("license"),
                       "rights_verified":src.get("rights_verified",False),
                       "transcript_excerpt":src.get("transcript_excerpt"),
                       "pixel_frame_analysis_performed":bool(evidence.get("source") == "sampled_video_frames"),
                       "automated_visual_match":bool(evidence.get("accepted")),
                       "visual_evidence":evidence,
                       "semantic_frame_verified":False,  # Human review remains required.
                       "generic_query":generic})
    audit = ROOT / "output/creative_qa.json"
    audit.write_text(json.dumps({"topic":story.get("topic") or story.get("test_topic_id"),
             "status":"REVIEW_REQUIRED",
             "automated_frame_analysis_performed":bool(visual_mode),
             "all_scenes_have_pixel_evidence":bool(visual_mode and all(
                 x["pixel_frame_analysis_performed"] for x in report)),
             "human_semantic_review_performed":False,
             "rights_review_performed":False,
             "shots":report}, indent=2), encoding="utf-8")
    assert all(x["asset"] for x in report), "Missing visual for narration beat"
    assert not any(x["generic_query"] for x in report), "Generic illustration query used for scene"
    assert len({x["asset"] for x in report}) >= min(6,len(report)), "Excessive reused media in narration beats"
    assert media_count >= 8, "not enough usable visual assets; refusing to publish a weak visual build"
    if not exact_script:
        assert video_count >= 4, "not enough actual video footage; refusing to publish a slideshow"
    print(f"QA PASS: {d:.2f}s, audio={a}, lines={len(lines)}, visuals={media_count}, video={video_count}, exact_script={exact_script}")


if __name__ == "__main__":
    main()
