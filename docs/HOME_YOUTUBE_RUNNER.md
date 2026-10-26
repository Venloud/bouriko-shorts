# Bouriko, private Windows downloader and free public render

## Design

Bouriko stays **public**, retaining its standard GitHub-hosted workflows.
The Windows YouTube downloader belongs only to the separate **private** repo
[Venloud/van02utuberunner](https://github.com/Venloud/van02utuberunner).
Kindled Iron and Kindled Voice are separate projects, not involved.

Manual trigger in Bouriko > generate script > dispatch private Windows runner >
download verifiable YouTube CC BY media > upload private artifact >
dispatch Bouriko hosted render > validate files, render and upload test MP4.
**There is no automatic publishing**.

The two repositories are not automatically connected just by existing.
Tokens and runner registration are required once.

## Owner setup

1. In the **private** repo open
   [Runners](https://github.com/Venloud/van02utuberunner/settings/actions/runners),
   select **New self-hosted runner**, Windows x64, and follow GitHub's generated
   download and configure commands. Register it with custom label
   `bouriko-youtube`. Use an isolated Windows VM or restricted user,
   not a daily-use administrator session. Never paste the short-lived runner
   registration token in chat or commit it to GitHub.
2. On the Windows runner install FFmpeg and make sure `ffmpeg` and `ffprobe`
   work from its actual PowerShell account. Run `run.cmd` from the runner
   installation folder. The private repo should show **Idle**.
3. Under **Bouriko > Settings > Secrets and variables > Actions**, add secret
   `BOURIKO_PRIVATE_RUNNER_TOKEN`, a fine-grained token restricted to
   `Venloud/van02utuberunner` with **Contents: read/write** (to trigger
   `repository_dispatch`) and **Actions: read** (to download its artifacts).
4. Under **van02utuberunner > Settings > Secrets and variables > Actions**, add
   `BOURIKO_PUBLIC_RENDER_TOKEN`, a fine-grained token restricted to
   `Venloud/bouriko-shorts` with **Actions: write** (to trigger its render).
   Give both short expirations and minimum permissions. Do not commit,
   display or share either secret.
5. Open Bouriko's
   [Home YouTube to Hosted Render](https://github.com/Venloud/bouriko-shorts/actions/workflows/home-youtube-render.yml),
   select **Run workflow**, choose **mode: plan** and a topic index. The
   private workflow should then start automatically; a successful acquisition
   triggers **mode: render** automatically in Bouriko.

## What counts as tested

- A GitHub Actions event accepted by the private repository is NOT a download pass.
- A running Windows runner is NOT a proof that YouTube allows downloads from the home IP.
- The private worker must save at least one legitimate CC BY candidate, verify
  the actual playable video with FFprobe, and record source/license metadata.
- The public hosted renderer verifies SHA-256 hashes, the original script
  checksum, and the source code revision before producing an MP4.
- Review resulting shot relevance and source attribution before publication.

## Security considerations

The private runner executes a script checked out from **Bouriko's pinned
commit**. Public repo code can still contain unintended or malicious changes.
An isolated VM and least-privilege Windows account are required safety
boundaries. Do not expose personal browser cookies, workstation files,
administrator privileges, or production credentials to runner code.

This setup preserves free public hosted render minutes. The private side
consumes self-hosted compute, not GitHub-hosted video-render minutes.
A computer must remain online to run the private download stage.

GitHub reference: https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners

**Current acceptance:** Offline architecture tests only; end-to-end YouTube
download and MP4 render remain unverified until secrets and runner are set up.
