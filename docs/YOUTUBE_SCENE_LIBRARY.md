# Bouriko reusable YouTube scene library (all subjects)

## Why
The first JJK run assembled unrelated mushroom-house, video-essay and Creative Commons explainer footage plus repeated blue-circle diagram placeholders. A playable stock video is not a semantically correct video. This feature changes the **generic home YouTube acquisition lane for every topic**, without JJK-specific code, episode lists, or anime-only dependencies.

## Automatic flow
1. Use the story topic and each narration line to search YouTube. Existing subject-specific shot guides remain optional, not mandatory.
2. Consider only videos which YouTube metadata labels Creative Commons Attribution. Check the title/description for subject overlap.
3. Check captions or auto-captions for **concrete word overlap with the narration**. Find an actual timed caption span (not a guessed random timestamp).
4. Save suggested source URL, exact start/end seconds, caption excerpt and provenance in a reusable private metadata index.
5. Use yt-dlp section download and FFmpeg (no full-video cache) to fetch the short excerpt; verify it plays.
6. Inspect 4 pixel frames throughout the actual excerpt with a local CLIP visual-text model. Contrast the intended visual subject against talking-head commentary, browser windows, placeholder diagrams, and unrelated scenery. Require 2+ credible frames, otherwise reject and try another YouTube candidate. For specifically named people/characters, additionally require two frame-to-reference-image matches.
7. Persist frame similarity scores, positive/negative margins, required visual identities and rejection reasons in the private library and artifact metadata.
8. Write the complete source/trim record into story.json and media_manifest.json for the private-to-public SHA-256 verification.
9. If no frame-verified scene matches under the strict home YouTube lane, fail loudly instead of substituting unrelated content or the blue-circle fallback.
10. Public hosted Remotion render stays review-only, **never automatically publishes**.

This is topic-agnostic and works with anime, games, technology, geography, education, documentary subjects and more **when** relevant Creative Commons source metadata and timecoded captions exist.

## Source metadata / season and episode
Generic source metadata includes optional season/episode **hints** when video titles provide S03E04 or Season 3 Episode 4. These are marked unverified and must not be treated as canonical show metadata. Precise time offsets are from video captions, not made up by the bot. No topic-specific season list is hard-coded.

## Smart library location
Set BOURIKO_SCENE_LIBRARY to choose the private metadata folder. Default:

    C:\Users\<WindowsUser>\Videos\BourikoSceneLibrary\index.json

This file stores prior clip source URLs, time ranges, caption excerpts, topic relevance metadata and licence notes, never tokens, whole episodes, or ephemeral subtitle URLs. Captions and clip files are not a replacement for frame inspection.

## Local frame intelligence
The private Windows runner must install the pinned public-repo requirements:

    python -m pip install -r bouriko/requirements-scene-vision.txt

The companion PR in van02utuberunner makes this dependency available when the two changes are deliberately integrated. This downloads an open-weight CLIP model (approximately hundreds of MB) into the local model cache, then reuses it. The model executes locally on CPU and does not call a paid vision API. The runner must have sufficient disk/RAM and outbound model access on its first run.

**Named identity reference folder**, for example:

    C:\Users\<WindowsUser>\Videos\BourikoSceneLibrary\references\index.json

Use a local JSON mapping like:

    {"entities": {"examplecharacter": ["examplecharacter-front.jpg", "examplecharacter-side.png"]}}

The referenced images must reside *inside the same references folder*, and should be source-verified, permitted image examples of the actual identity. When narration names the target, a clip must visually match its reference images. If the references are missing or the model cannot identify it, the candidate is rejected, **not falsely approved**. This mechanism is generic for anime characters, known people and recognizable products, not JJK-specific. A narration line can explicitly set `visual_entities` to identify the required subjects. CLIP similarities are heuristic, not identity proof. Review borderline results and provide reference images only if you have the rights to do so.

## Real model acceptance and threshold calibration

The GitHub-hosted offline smoke tests do NOT download the 605 MB CLIP model or prove it recognizes footage. The private Windows host must run real inference with locally available, rights-reviewed clips from two unrelated subjects and explicit true/false labels.

1. With the existing Windows Bouriko checkout, install the pinned requirements from the PUBLIC branch checked out at the expected feature commit. Use the same Python 3.11 environment as the private runner.
2. Create a PRIVATE fixture JSON alongside short local videos (do not upload the clips or references to GitHub):

       [
         {"clip":"positive-gps.mp4","topic":"GPS satellites","visual":"Satellites orbiting the Earth","expected_relevant":true},
         {"clip":"negative-gps.mp4","topic":"GPS satellites","visual":"Satellites orbiting the Earth","expected_relevant":false},
         {"clip":"positive-game.mp4","topic":"video game competition","visual":"Players fighting inside an arena","expected_relevant":true},
         {"clip":"negative-game.mp4","topic":"video game competition","visual":"Players fighting inside an arena","expected_relevant":false}
       ]

3. On your Windows computer, run the isolated smoke script from a checkout of this PR:

       powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\windows\validate-scene-vision.ps1 -Fixtures C:\PrivateTests\fixtures.json

   This command requires Python 3.11 and uses a dedicated local venv. It does not modify runner registration, GitHub secrets, or publish a video. Leave out `-Fixtures` to check only that the actual pinned model loads on CPU. The file is in the public Bouriko PR; invoke it manually on your own computer after reviewing its contents. The private runner PR adds its own automatic model preflight when approved.
4. Execute real local model inference:

       python tools/evaluate_scene_vision.py --fixtures C:\path\to\private-fixtures.json

5. Inspect the PRIVATE evaluation report in the BourikoSceneLibrary folder. It records source clip, expected result, observed prediction, CLIP cosine scores and margins, false positives, false negatives, recall and accuracy. The harness reports INCOMPLETE with fewer than two positive and two negative examples, and does not approve thresholds automatically.
6. Calibrate against observed failure examples. Edit score thresholds only with actual positive/negative evidence, then rerun the offline regression and all four live evaluation examples.
7. Only after public/runner PR owner review, conduct a two-topic private acquisition plus public render trial. Review the resulting MP4, captions, safe area, visual timing, sources and rights. Keep publishing disabled.

The selector now retries independent caption-located moments and bounded visual-only windows, compares up to two passing visual candidates (with a bounded inspection budget), deduplicates attempts across search queries, and saves rejected candidate reasons to the private file `rejections.jsonl`. CLIP scores rank plausible videos but DO NOT establish identities or copyright permissions.

A person or character *mentioned* in narration does not automatically have to appear in a map/graphic scene. If the *planned visual* or explicit `visual_entities` requires that person, the match must use source-verified private reference images. Missing references are a blocked identity claim, not a silently successful identification. Those recognition rules are subject-independent.

### Actual acceptance status

- Feature PR contains generic research, timestamped section-cutting, real-frame CLIP integration, identity reference gating, ranked retry, provenance reporting and labeled local evaluation tooling.
- Nonpublishing GitHub smoke checks exercise pipeline contracts, mocked cosine decisions and REAL FFmpeg frame sampling. They do not load pretrained weights.
- Real Windows model inference, video downloads on this PR head, cross-repository media handoff and two finished MP4s remain **UNVERIFIED** until evidence is recorded.
- Publishing remains disabled; no draft PR is automatically merged.

## IMPORTANT limits
- A matching transcript does not guarantee the video **visually shows** the claimed scene. Source titles can be misleading, footage edited out of context, or copyrighted material incorrectly labeled CC BY. Metadata licensing is **not independent rights verification**.
- YouTube clips with CC BY metadata may use English subtitle timecodes, or a bounded visual-only probe of three short windows when a relevant candidate is 8–900 seconds long. An exploratory offset is not a verified dialogue or episode timestamp. If a clip cannot be matched reliably, the pipeline stops; it does not pretend to understand scenes it has not inspected.
- Season/episode numbers inferred from the uploader title are hints, not authoritative facts. No invented timestamps.
- The private Windows runner, public artifacts and reviewer access should be protected. Avoid passing credentials/browser cookies to downloads.
- Local CLIP frame embeddings are implemented in this PR, but character recognition still needs accurate reference images. This cannot certify exact anime character IDs without references, on-screen actions, verified canonical episode catalogs, scene-boundary detection, or downstream reuse rights. Full multimodal video understanding remains a future, independently evaluated improvement.
- Publishing remains disabled and the final creative_qa.json must remain REVIEW_REQUIRED until footage and rights are manually checked.

## Offline regression
    python -m unittest discover -s tools -p "test_scene_library.py" -v
    python -m unittest discover -s tools -p "test_frame_vision.py" -v

Then test on the Windows self-hosted runner with a story from multiple unrelated topics. Inspect every selected segment, its original source, exact caption timecode, soundtrack, visual relevance and the final rendered MP4. Do not merge as fully accepted on unit tests alone.
