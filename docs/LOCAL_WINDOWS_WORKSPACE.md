# Owner's Windows development workspace

Confirmed by owner, 2026-10-25:
- `C:\Users\van02\homebeacon`: central rules, Markdown documentation, project references and handoffs (updated by owner approval, 2026-11-02).
- `C:\Users\van02\Desktop\cody`: media production, YouTube downloads, FFmpeg workflows, and local media dependencies.
- `C:\Users\van02\repos`: home for Git repository working copies.
- Bouriko expected working copy: `C:\Users\van02\repos\bouriko-shorts` **only if cloned under the normal folder name; verify with Test-Path**.

Launch the permitted media diagnostic from a PowerShell window in the Bouriko checkout:

```powershell
Set-Location 'C:\Users\van02\repos\bouriko-shorts'
git pull --ff-only
.\tools\windows\test-youtube-media.ps1 -Url 'https://www.youtube.com/watch?v=YOUR_AUTHORIZED_VIDEO_ID'
```

## Approved Cody path migration, 2026-11-02

The diagnostic now defaults to `C:\Users\van02\Desktop\cody\youtube\downloads`.
Its deployed local copy is `C:\Users\van02\Desktop\cody\tools\youtube\test-youtube-media.ps1`.
Clip-extraction cleanup, only when explicitly requested, is restricted to child jobs under
`C:\Users\van02\Desktop\cody\youtube\jobs`.
The historical filename `tools\windows\migrate-youtube-to-homebeacon.ps1` is preserved,
but its destination is now Cody. Do not run it as cleanup; it copies and may overwrite
the deployed script. Existing Home Beacon originals are preserved pending separate cleanup approval.

For scoped PATH refresh and Python 3.13 faster-whisper activation:

```powershell
. 'C:\Users\van02\Desktop\cody\tools\powershell\Enter-Cody.ps1'
& 'C:\Users\van02\Desktop\cody\tools\youtube\test-youtube-media.ps1' -Query 'traffic light intersection car' -Results 2
```

The migration changes local media paths only. GitHub workflows, private dispatch,
the existing Windows runner and its credentials remain in place. These local tests
do not establish production runner or publishing acceptance.
Handoff: `C:\Users\van02\homebeacon\handoffs\CODY_SETUP_2026-11-02.md`.

Do not claim that GitHub Actions has direct access to the owner's Windows PC. A runner integration requires a separately installed, owner-approved local agent. The current diagnostic runs only when manually invoked on Windows. No social posting is authorized.

Test scripts must be made visible for owner review in chat when added or changed, and their exact commands documented. The existing `Bouriko Build` is still the only general video build workflow.

Pending: authored-script-only inbox for six-topic rotation. Existing rotation's `pipeline/script.py` uses Gemini to write scripts and must not be represented as human-authored until corrected. Full MP4 build acceptance is not yet verified.
