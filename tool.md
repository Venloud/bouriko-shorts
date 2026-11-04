# The Lab of Tory — tools

| Tool | Purpose | Access | Current status |
|---|---|---|---|
| `tools/windows/test-youtube-media.ps1` | Search, selected-video download, local trim entry point | yt-dlp network calls; local FFmpeg | Search/download tested on owner PC; helper scripts deployed to Cody |
| `tools/windows/rank-youtube-candidates.ps1` | General subject/publisher/format metadata ranking | Local; no API/key | Offline regressions and live Apple query passed; not scene or channel identity authentication |
| `tools/windows/trim-video.py` | Timestamp trim with optional mute; preserves aspect ratio | Local FFmpeg/FFprobe | Actual export/decode/audio/no-overwrite tests passed; source preserved |
| `tools/windows/youtube-library.py` | Catalog saved files and source metadata for bots | Local filesystem | Writes Cody `youtube/index.json`; no reuse-rights approval |
| `pipeline/media.py`: Pexels | Find stock video/photos | Pexels HTTP API; `PEXELS_API_KEY` | Source implementation present; current credential/live request not verified |
| `pipeline/media.py`: Pixabay | Find stock video/photos | Pixabay HTTP API; `PIXABAY_API_KEY` | Source implementation present; current credential/live request not verified |
| `pipeline/media.py`: Commons / YouTube CC | Media discovery and eligible source selection | Commons API / yt-dlp | Code present; downloaded media must pass relevance and licensing review |
| `pipeline/library_ingest.py` / shared asset library | Reuse local assets before provider lookups | Local; opt-in configuration | Offline library-first regression passed; inspect current environment for activation |
| `pipeline/voice.py` | Kokoro narration | Local model/runtime | Present; not retested for fresh narration in this change |
| `pipeline/remotion_prepare.py`, `remotion/` | Prepare and render media-led videos | Local Node/Chrome/FFmpeg | Isolated Windows smoke passed after URL fix; that unrelated fix is not included here |
| `pipeline/qa.py` | Structural video checks | Local FFprobe/metadata | Existing fixture test passed; does not enforce visual relevance or production duration |
| `pipeline/youtube.py` | YouTube publishing | YouTube Data API / OAuth | **Disabled by existing owner lock** |
| `.github/workflows/daily.yml` | Old daily build | GitHub Actions | **No active trigger (`on: {}`)** |
| `.github/workflows/home-youtube-render.yml` | Plan → private Windows acquisition → hosted render | GitHub dispatch/artifacts | Existing runner verified online; no workflow changes or dispatches in this PR |

Download storage: `C:\Users\van02\Desktop\cody\youtube\downloads`; edited clips: `clips`; search job evidence: `jobs`; bot-readable catalog: `index.json`. No media in Home Beacon or Git. API keys/tokens stay outside docs and commits.

[Commands and deployment](docs/LOCAL_YOUTUBE_TOOLS.md). “Present” means implemented, not necessarily configured or currently running. This inventory is scoped to this repository; the owner's central all-repo catalog is `C:\Users\van02\homebeacon\tool.md`.
