# Local YouTube tools

These tools run on the Windows computer. Videos stay in `C:\Users\van02\Desktop\cody\youtube`, never Home Beacon. No runner or publishing workflow is changed.

## Search

```powershell
cd C:\Users\van02\Desktop\cody
. .\tools\powershell\Enter-Cody.ps1
.\tools\youtube\test-youtube-media.ps1 -Query 'Apple iPhone Duo official presentation' -Results 8
```

Ranking uses subject coverage and presentation/review/full/short intent. For an ambiguous query add `-ExpectedChannel 'Apple'`. Display-name matching and verified-channel metadata are not channel identity authentication, scene verification or reuse permission. Ranking reasons and channel metadata are saved with results. There are no topic-specific traffic bonuses.

## Download a selected source

```powershell
.\tools\youtube\test-youtube-media.ps1 -Url 'https://www.youtube.com/watch?v=VIDEO_ID' -Download
```

Replace VIDEO_ID with an actual 11-character video ID. Defaults to `youtube\downloads\VIDEO_ID.mp4`; saves a minimal `.source.json` and refreshes `youtube\index.json`. Source rights remain NOT_VERIFIED. Requires yt-dlp, FFmpeg/FFprobe and Python 3.13 (`py -3.13`). Never enables publishing.

## Cut and trim

```powershell
.\tools\youtube\test-youtube-media.ps1 -TrimSource '.\youtube\downloads\VIDEO_ID.mp4' -Start '00:01:20' -End '00:01:35' -ClipOutput '.\youtube\clips\product-demo.mp4'
```

Alternatively use `-Duration 15` instead of `-End`. Default preserves source aspect ratio and available audio. Add `-Mute` to remove audio. Frame-accurate H264/AAC re-encode; no three-second limit. Source and existing destination files are never overwritten. The older `extract-video-clips.py` remains the separate silent, vertical, <=3-second extraction tool.

## Find saved media

```powershell
py -3.13 .\tools\youtube\youtube-library.py --query 'Apple Duo'
```

Scans downloads, clips and jobs and writes `youtube\index.json` with relative/absolute paths, bytes, title, channel, source URL, query, category and rights status. Older files lacking sidecars remain indexed by filename; missing metadata is not invented. Run after external file changes or trims. Search does not imply semantic scene matching.

## Deployment and tests

Versioned source is `tools/windows`. Copy `test-youtube-media.ps1`, `rank-youtube-candidates.ps1`, `trim-video.py`, `youtube-library.py` together to Cody `tools/youtube`. The existing migration helper copies all four; originals/media remain preserved.

Tests: `powershell -NoProfile -File tools/tests/test-youtube-ranking.ps1` and `python tools/tests/test_youtube_trim.py`. Tests need FFmpeg/FFprobe; ranking needs Windows PowerShell 5.1 or newer. No API credentials or network required for regression tests.
