# Run once from the Bouriko checkout. Non-destructive: copies tools/media, never removes WinGet yt-dlp.
$ErrorActionPreference = "Stop"
$home = Join-Path $env:USERPROFILE 'homebeacon'
$toolDir = Join-Path $home 'tools\youtube'
$mediaDir = Join-Path $home 'media\youtube\downloads'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
New-Item -ItemType Directory -Force -Path $toolDir, $mediaDir | Out-Null
$source = Join-Path $PSScriptRoot 'test-youtube-media.ps1'
$target = Join-Path $toolDir 'test-youtube-media.ps1'
Copy-Item -LiteralPath $source -Destination $target -Force
$old = Join-Path $repo 'output\youtube_media_test'
if (Test-Path -LiteralPath $old) {
    Get-ChildItem -LiteralPath $old -File | ForEach-Object {
        $dest = Join-Path $mediaDir $_.Name
        if (-not (Test-Path -LiteralPath $dest)) { Copy-Item -LiteralPath $_.FullName -Destination $dest }
    }
}
$yt = Get-Command yt-dlp -ErrorAction SilentlyContinue
if ($null -eq $yt) { Write-Warning 'yt-dlp is not on PATH. Existing WinGet install was not modified.' }
else { Write-Host "yt-dlp remains installed at: $($yt.Source)" }
Write-Host "Shared tool copied: $target"
Write-Host "Raw media location: $mediaDir"
Write-Host "Run: & '$target' -Query 'traffic light intersection car arrives changes red green and departs'"
Write-Host "Old files and executable are preserved. Publishing remains disabled."
