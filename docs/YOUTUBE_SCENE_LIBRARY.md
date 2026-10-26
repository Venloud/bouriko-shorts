# Bouriko reusable YouTube scene library (all subjects)

## Why
The first JJK run assembled unrelated mushroom-house, video-essay and Creative Commons explainer footage plus repeated blue-circle diagram placeholders. A playable stock video is not a semantically correct video. This feature changes the **generic home YouTube acquisition lane for every topic**, without JJK-specific code, episode lists, or anime-only dependencies.

## Automatic flow
1. Use the story topic and each narration line to search YouTube. Existing subject-specific shot guides remain optional, not mandatory.
2. Consider only videos which YouTube metadata labels Creative Commons Attribution. Check the title/description for subject overlap.
3. Check captions or auto-captions for **concrete word overlap with the narration**. Find an actual timed caption span (not a guessed random timestamp).
4. Save suggested source URL, exact start/end seconds, caption excerpt and provenance in a reusable private metadata index.
5. Use yt-dlp section download and FFmpeg (no full-video cache) to fetch the short excerpt; verify it plays.
6. Write the complete source/trim record into story.json and media_manifest.json for the private-to-public SHA-256 verification.
7. If any scene is missing or irrelevant under the strict home YouTube lane, fail loudly instead of substituting unrelated content or the blue-circle fallback.
8. Public hosted Remotion render stays review-only, **never automatically publishes**.

This is topic-agnostic and works with anime, games, technology, geography, education, documentary subjects and more **when** relevant Creative Commons source metadata and timecoded captions exist.

## Source metadata / season and episode
Generic source metadata includes optional season/episode **hints** when video titles provide S03E04 or Season 3 Episode 4. These are marked unverified and must not be treated as canonical show metadata. Precise time offsets are from video captions, not made up by the bot. No topic-specific season list is hard-coded.

## Smart library location
Set BOURIKO_SCENE_LIBRARY to choose the private metadata folder. Default:

    C:\Users\<WindowsUser>\Videos\BourikoSceneLibrary\index.json

This file stores prior clip source URLs, time ranges, caption excerpts, topic relevance metadata and licence notes, never tokens, whole episodes, or ephemeral subtitle URLs. Captions and clip files are not a replacement for frame inspection.

## IMPORTANT limits
- A matching transcript does not guarantee the video **visually shows** the claimed scene. Source titles can be misleading, footage edited out of context, or copyrighted material incorrectly labeled CC BY. Metadata licensing is **not independent rights verification**.
- Only YouTube videos with CC BY metadata and recognized English-language captions are currently supported in this lane. If a clip cannot be matched reliably, the pipeline stops; it does not pretend to understand scenes it has not inspected.
- Season/episode numbers inferred from the uploader title are hints, not authoritative facts. No invented timestamps.
- The private Windows runner, public artifacts and reviewer access should be protected. Avoid passing credentials/browser cookies to downloads.
- This is the first working core of a reusable scene library. Frame-embedding semantic recognition, verified canonical episode catalogs, on-screen character/action identification, clip previews, scene-boundary detection, rights review and complete automated approval are future extensions, not completed functionality.
- Publishing remains disabled and the final creative_qa.json must remain REVIEW_REQUIRED until footage and rights are manually checked.

## Offline regression
    python -m unittest discover -s tools -p "test_scene_library.py" -v

Then test on the Windows self-hosted runner with a story from multiple unrelated topics. Inspect every selected segment, its original source, exact caption timecode, soundtrack, visual relevance and the final rendered MP4. Do not merge as fully accepted on unit tests alone.
