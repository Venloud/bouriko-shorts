# JJK scene library: episode-aware, precise-trim, fail-closed

## Behavior
JJK narration must use real scene cuts from the private video library, with series, season, episode, overall episode number, start/end seconds, scene ID, rights documentation, and human approval. If any narration beat lacks a suitable reviewed scene, the build fails and lists each missing beat. It does not silently use unrelated Creative Commons clips or identical generic diagrams.

The original video files stay on the owner's Windows PC, not in this public GitHub repo. Bouriko trims only the selected excerpts and submits them through the existing private-runner artifact and public review renderer. Social auto-publishing stays disabled.

## Verified episode lookup
The authoritative Season 3 Culling Game Part 1 index is in data/jjk_episode_index.json, based on https://jujutsukaisen.jp/episodes/index.php. Episodes are S03E01-S03E12, overall #48-59. S03E03, overall #50, is "About the Culling Game" (also https://www.crunchyroll.com/watch/GE00367570ENUS/about-the-culling-game). Episode descriptions do NOT supply frame-accurate timecodes. Exact times must come from the source file, subtitles, and actual visual inspection.

## Windows private source folder
Put footage you have permission to process in:

    C:\Users\<user>\Videos\BourikoAnime\videos\

Or set BOURIKO_ANIME_LIBRARY before starting the Windows GitHub runner, pointing at an alternative private folder. Never upload entire copyrighted episodes or browser cookies to a public repo.

From a Bouriko checkout:

    python pipeline/anime_scene_library.py episodes
    python pipeline/anime_scene_library.py suggest "100 points lets a player change a rule."

Add a real clip from a locally supplied episode after watching it:

    python pipeline/anime_scene_library.py add --source videos/s03e03.mp4 --season 3 --episode 3 --start 05:17.0 --end 05:22.0 --description "Players discuss game rules" --tag "rule" --tag "points" --beat rule_change --rights-reference "LOCAL_RIGHTS_REVIEW_RECORD" --approve

IMPORTANT: The above timestamps are format examples, NOT verified JJK scene positions. Review your footage and use actual in-file times. An approval means the owner checked the scene frames. It does not, by itself, prove a license or fair-use case.

For a rights-unverified online *discovery list* of JJK clips (metadata only, not downloads):

    python pipeline/anime_scene_library.py discover "Culling Game Kenjaku rule explanation" --limit 10

This searches public video titles and saves candidates in the private BourikoAnime/discovery.json, marked unverified. It DOES NOT automatically download, claim an exact episode/timestamp, or approve the footage. Use an authorized source before indexing real excerpts.

For subtitle-assisted scene proposals:

    python pipeline/anime_scene_library.py subtitles --file C:\path\to\episode.srt
    python pipeline/anime_scene_library.py propose --source videos/s03e03.mp4 --season 3 --episode 3 --subtitles C:\path\to\episode.srt --rights-reference "LOCAL_RIGHTS_REVIEW_RECORD"

The subtitle matcher creates beat-matched, timestamped CANDIDATES only. It does not assert that matching words prove the actual frames match. After previewing and adjusting a candidate if needed:

    python pipeline/anime_scene_library.py approve --scene-id YOUR_SCENE_ID

Metadata is stored in the private BourikoAnime/catalog.json. The CLI does not scrape streaming services, bypass DRM, download unlicensed episodes, or assert that a YouTube title confers reuse rights.

## Acceptance and safety
- Current status: code proposed, source footage not supplied. Zero JJK episode scene cuts actually verified.
- All 12 narration beats must have distinct approved scene entries before JJK acquisition succeeds. Other topics retain existing stock-footage behavior.
- Hash validation stays mandatory. In JJK mode the YouTube-CC minimum is replaced by strict per-beat scene provenance.
- Owner scene approval and publication rights are separate. Final video and rights still require review; publication remains off.
- Running unit tests is not proof of a finished video or correct episode timecodes.
- A future scene-understanding engine could use vision and subtitle alignment but must be evaluated against actual authorized episode frames, with no fabricated precision.

Regression tests:

    python -m unittest discover -s tools -p "test_anime_scene_library.py" -v

Then run the existing Bouriko plan workflow with topic index 0, inspect private Windows acquisition, review the complete rendered MP4 and per-beat creative_qa.json. Do not publish until semantic and rights QA pass.
