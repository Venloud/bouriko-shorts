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
| GH_PAT | fine-grained PAT for this repo: Contents + Actions read/write | buffer refill trigger |

Never paste keys into chat. Secrets only.

## 3. Accounts (owner)
- Handle: **@bourikoh** (trailing "h"), the same on TikTok and YouTube. Claimed; plain @bouriko is not ours.
- TikTok: Personal account (not Business).
- YouTube: new channel (or brand account) named Bouriko, handle @bourikoh.
