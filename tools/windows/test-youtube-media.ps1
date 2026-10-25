param(
    [string]$Query = "traffic light intersection car arrives signal turns red turns green car drives away",
    [string]$Url = "",
    [ValidateRange(1,20)][int]$Results = 8,
    [switch]$Download,
    [string]$OutputDir = "$env:USERPROFILE\homebeacon\media\youtube\downloads"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$folder = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $root $OutputDir }
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$report = Join-Path $folder "youtube_test_report.json"
$resultsFile = Join-Path $folder "youtube_search_results.json"

function Need($program) {
    if (-not (Get-Command $program -ErrorAction SilentlyContinue)) {
        throw "Missing $program. Install with winget: yt-dlp.yt-dlp or Gyan.FFmpeg."
    }
}
function Save-Report($state, $message, $chosen = $null, $path = "") {
    [ordered]@{
        status = $state
        message = $message
        searched = $Query
        chosen = $chosen
        output_file = $path
        checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        publication = "DISABLED"
        accepted_four_clips = $false
    } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $report
}
try {
    Need "yt-dlp"
    if ($Download) { Need "ffprobe" }
    $selected = $null
    if ($Url) {
        if ($Url -notmatch '^https://(www\.|m\.)?(youtube\.com|youtu\.be)/') {
            throw "Use a YouTube watch URL, or omit -Url and let the bot search."
        }
        $selected = [pscustomobject]@{ id = ""; title = "Owner-supplied YouTube URL"; url = $Url; score = 0; duration = $null }
    }
    else {
        Write-Host "Searching YouTube: $Query"
        $lines = @(& yt-dlp --flat-playlist --no-warnings --no-playlist --dump-json "ytsearch$($Results):$Query" 2>$null)
        if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0) { throw "YouTube search failed; check yt-dlp version/network connectivity." }
        $found = @()
        foreach ($line in $lines) {
            try { $video = $line | ConvertFrom-Json } catch { continue }
            $id = [string]$video.id
            if ($id -notmatch '^[A-Za-z0-9_-]{11}$') { continue }
            $title = [string]$video.title
            $dur = if ($null -ne $video.duration) { [double]$video.duration } else { 0 }
            $tokens = @($Query.ToLowerInvariant().Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) | Select-Object -Unique)
            $hits = @($tokens | Where-Object { $title.ToLowerInvariant().Contains($_) }).Count
            $priority = @('traffic','light','signal','intersection','car')
            $bonus = @($priority | Where-Object { $title.ToLowerInvariant().Contains($_) }).Count
            $score = $hits + 2 * $bonus
            if ($dur -gt 0 -and $dur -le 600) { $score += 2 }
            if ($title -match '(compilation|livestream|live stream|shorts compilation)') { $score -= 4 }
            $found += [pscustomobject]@{
                id = $id; title = $title; duration = $dur; score = $score
                url = "https://www.youtube.com/watch?v=$id"
                uploader = [string]$video.uploader
            }
        }
        $ranked = @($found | Sort-Object -Property @{Expression='score';Descending=$true}, @{Expression='duration';Descending=$false})
        $ranked | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $resultsFile
        if ($ranked.Count -eq 0) { throw "No usable YouTube candidates found." }
        Write-Host "Candidate videos (metadata relevance only, not scene verification):"
        $ranked | Select-Object score,duration,title,url | Format-Table -Wrap
        $selected = $ranked[0]
        Write-Host "Top candidate: $($selected.url)"
    }
    if (-not $Download) {
        Save-Report "SEARCH_COMPLETE" "Discovery complete; no download requested; scene content and rights not confirmed" $selected
        Write-Host "Search saved to: $resultsFile"
        Write-Host "To download the top candidate, rerun with -Download after checking permissions."
        exit 0
    }
    $chosenUrl = [string]$selected.url
    Write-Host "Downloading candidate: $chosenUrl"
    & yt-dlp --no-playlist --no-progress --no-overwrites --restrict-filenames -f "bv*[height<=1080]+ba/b[height<=1080]/best" --merge-output-format mp4 -o (Join-Path $folder "%(id)s.%(ext)s") -- "$chosenUrl"
    if ($LASTEXITCODE -ne 0) { throw "Download failed or blocked by YouTube" }
    $id = if ($null -ne $selected.id) { [string]$selected.id } else { "" }
    $videos = @(Get-ChildItem $folder -File | Where-Object { $_.Extension -in '.mp4','.mkv','.webm' -and (!$id -or $_.BaseName -eq $id) })
    if ($videos.Count -eq 0) { throw "No downloaded media found" }
    $file = $videos[0].FullName
    & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded file failed ffprobe validation" }
    Save-Report "DOWNLOAD_VERIFIED" "Candidate file retrieved; scene events, short clips and reuse rights remain unverified" $selected $file
    Write-Host "Candidate downloaded: $file"
    Write-Host "NOT PASSED: still require four visually verified <=3s scene clips, rights and GitHub assets."
}
catch {
    Save-Report "FAILED" $_.Exception.Message
    Write-Error $_.Exception.Message
    exit 1
}
