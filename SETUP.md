# Setup

## 1. Assets (owner)
Done: the current sheets in `assets/reference/` are the final master (warm tan skin, blue stripe on both cheeks).
Original reference notes:
- `bouriko_master.png`: front/side/back + expressions + props (warm tan skin, blue stripe on both cheeks,
  striped saber-tooth pelt, fang necklace)
- `bouriko_poses.png`: the pose sheet made from the master
The files are named `draft_master_and_poses.png` and `draft_poses.png`; despite the names, they ARE the final master. Keep them.

## 2. GitHub secrets (Settings > Secrets and variables > Actions)
Use SEPARATE free keys from Night Files where possible, so the two channels don't share daily limits.
| Secret | Where | Needed for |
|---|---|---|
| GEMINI_API_KEY | aistudio.google.com (new free key, ideally another Google account) | writer/critic |
| GROQ_API_KEY | console.groq.com (new free key) | backup writer |
| HF_TOKEN | huggingface.co settings > tokens | optional Spaces |
| NTFY_TOPIC | any unique topic name | phone alerts |
| YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN | Google Cloud OAuth (same steps as Night Files), for the Bouriko YouTube channel | YouTube upload |
| TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET / TIKTOK_REFRESH_TOKEN | TikTok developer app, Bouriko TikTok account | TikTok drafts |
| TIKTOK_REDIRECT_URI | the redirect URI set in the TikTok developer app | Connect TikTok workflow |
| GH_PAT | fine-grained PAT for **bouriko-shorts only**: Contents + Actions + **Secrets** read/write | saves TIKTOK_REFRESH_TOKEN, buffer refill trigger |

Never paste keys into chat. Secrets only.

## 3. Accounts (owner)
- Handle: **@bourikoh** (trailing "h"), the same on TikTok and YouTube. Claimed; plain @bouriko is not ours.
- TikTok: Personal account (not Business).
- YouTube: new channel (or brand account) named Bouriko, handle @bourikoh.

## 4. One-time connections (owner)
Both files are unchanged copies from Night Files (horror-shorts main @ 647ddf7).

### TikTok: `Connect TikTok (one time)` workflow (.github/workflows/connect-tiktok.yml + pipeline/connect_tiktok.py)
1. Needs these secrets in THIS repo: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REDIRECT_URI, GH_PAT
   (GH_PAT must include Secrets read/write on bouriko-shorts, or the save step fails).
2. Logged in to TikTok as **@bourikoh**, open the app's login URL, approve, and copy the URL you land on.
   (Sandbox app: add @bourikoh as a target user in the TikTok developer portal first.)
3. Actions > Connect TikTok (one time) > Run workflow > paste that URL (or just the code). Do it within a few
   minutes: login codes expire fast.
4. It saves TIKTOK_REFRESH_TOKEN into **this repo** (`gh secret set --repo ${{ github.repository }}`), never into
   horror-shorts. The last log line still says "run 'Daily horror video'" (copied unchanged); ignore it.

### YouTube: pipeline/connect_youtube.py (on your own computer, it opens a browser)
1. Google Cloud: enable YouTube Data API v3 (+ YouTube Analytics API), OAuth consent screen "In production"
   (Testing = token expires after 7 days), OAuth client ID type Desktop app, download client_secret.json.
2. `pip install google-auth-oauthlib` then `python pipeline/connect_youtube.py path/to/client_secret.json`.
3. Sign in and pick the **Bouriko (@bourikoh)** channel, not Night Files.
4. Put the three printed values into this repo's secrets YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
   Never paste them into a chat.
