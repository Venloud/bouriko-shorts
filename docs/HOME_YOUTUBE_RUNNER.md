# Bouriko home YouTube acquisition (Windows) -> hosted render

## Why this lane exists
GitHub-hosted datacenter IPs are being challenged on YouTube video pages **before**
a PO token is requested. This workflow keeps YouTube acquisition on a Windows
machine on an owner-controlled network. GitHub-hosted Ubuntu handles script
planning, narration, SFX, Remotion and final video QA.

**This does not guarantee YouTube access or content rights.** The YouTube
metadata must explicitly report Creative Commons Attribution. Assets remain
provisional until a human checks scene relevance and reuse conditions.
Other Bouriko workflows, publishers and Horror Shorts are unchanged.

## Important security warning: this repo is public
As of October 25, 2026, `Venloud/bouriko-shorts` is **public**.
GitHub warns that self-hosted runners are unsafe for public repositories
because untrusted PR/workflow code could run on the machine. Do not connect a
runner running with your daily Windows administrator identity, personal data,
browser cookies, or other credentials. **Prefer making the repo private**
before attaching a home PC, or use a disposable, isolated Windows VM with a
restricted account and no personal files or secrets.

The new workflow is manual-dispatch-only, reads `main` exclusively, checks
out with `persist-credentials: false`, and has `contents: read` permissions.
These mitigations do **not** remove GitHub's broader public-runner risks.

## Register the runner (one-time owner action)
1. On GitHub open **Bouriko > Settings > Actions > Runners > New self-hosted runner**.
2. Choose **Windows x64** and follow the *exact GitHub-generated instructions*
   to download and configure the runner. The registration token is short-lived.
   Never paste runner tokens, GitHub PATs, browser cookies or secrets into chat.
3. When the GitHub configuration prompt asks for additional labels, enter
   **`bouriko-youtube`**. The runner also needs its usual GitHub-provided
   `self-hosted`, `Windows` and `X64` labels.
4. On that Windows environment, install FFmpeg once, and reopen the terminal:
   ```powershell
   winget install -e --id Gyan.FFmpeg
   ffmpeg -version
   ffprobe -version
   ```
   The workflow installs Python 3.11, Node 22 and Python packages via
   GitHub Actions. The GitHub runner service account must see FFmpeg on PATH.
5. From the runner installation folder, start `run.cmd` and leave it online
   for the test. Wait until GitHub shows the runner as **Idle**. Do not install
   it as an elevated Windows service on a personal PC.

Official guidance:
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners
- https://docs.github.com/en/actions/reference/security/secure-use

## Run the workflow
1. Open **Actions > Bouriko Home YouTube to Hosted Render > Run workflow**.
2. Select `main`, then topic index `0` for an initial nonpublishing run.
3. Follow the three separate jobs:
   - **plan** (GitHub hosted): generate `output/story.json`.
   - **youtube_acquisition** (Windows `bouriko-youtube`): search metadata
     for **CC BY** clips, download on your network, inspect files with FFprobe,
     and upload `bouriko-home-media`. This step **fails** if no usable
     YouTube CC asset is found, rather than pretending a stock substitute is YouTube.
   - **hosted_render** (GitHub hosted): retrieve that exact story and its media,
     verify SHA-256 hashes, generate voice and SFX, render and QA the MP4.
4. If the render succeeds, the run artifact is **`bouriko-home-youtube-render`**.
   No YouTube or TikTok posting occurs.

### Troubleshooting
- **Waiting for runner:** runner is offline, missing label `bouriko-youtube`,
  or unavailable. The job cannot start until it is connected.
- **ffmpeg/ffprobe not recognized:** reopen the runner session after installing
  FFmpeg; confirm both commands work under its actual Windows user.
- **YouTube "sign in to confirm":** residential IP or account may still be
  challenged. Review the yt-dlp output. A PO token alone cannot guarantee
  access, and personal-account browser cookies are not automatically consumed.
- **No YouTube CC clips:** the strict license filter found nothing usable for
  that story. The workflow fails closed, it does not license random uploads.
- **Mismatch on hosted renderer:** `tools/verify_home_media.py` rejects missing,
  corrupt, unsupported or modified media, including SHA-256 mismatches.
- **Visual relevance:** the handoff validation proves formats and provenance,
  not that footage illustrates narration. Review `creative_qa.json` and the MP4.

This is a **manual, isolated test lane**. It does not activate background
publishing or alter the existing Bouriko Build workflow.
