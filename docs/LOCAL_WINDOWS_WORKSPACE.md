# Owner's Windows development workspace

Confirmed by owner, 2026-10-25:
- `C:\Users\van02\homebeacon`: home for OmniRoute and Claude tooling, installations and GitHub-project utilities.
- `C:\Users\van02\repos`: home for Git repository working copies.
- Bouriko expected working copy: `C:\Users\van02\repos\bouriko-shorts` **only if cloned under the normal folder name; verify with Test-Path**.

Launch the permitted media diagnostic from a PowerShell window in the Bouriko checkout:

```powershell
Set-Location 'C:\Users\van02\repos\bouriko-shorts'
git pull --ff-only
.\tools\windows\test-youtube-media.ps1 -Url 'https://www.youtube.com/watch?v=YOUR_AUTHORIZED_VIDEO_ID'
```

Do not claim that GitHub Actions has direct access to the owner's Windows PC. A runner integration requires a separately installed, owner-approved local agent. The current diagnostic runs only when manually invoked on Windows. No social posting is authorized.

Test scripts must be made visible for owner review in chat when added or changed, and their exact commands documented. The existing `Bouriko Build` is still the only general video build workflow.

Pending: authored-script-only inbox for six-topic rotation. Existing rotation's `pipeline/script.py` uses Gemini to write scripts and must not be represented as human-authored until corrected. Full MP4 build acceptance is not yet verified.
