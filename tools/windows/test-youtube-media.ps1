param(
    [string]$TrimSource = "",
    [string]$Start = "0",
    [string]$End = "",
    [string]$Duration = "",
    [string]$ClipOutput = "",
    [switch]$Mute,
    [string]$Query = "",
    [string]$Url = "",
    [string]$ExpectedChannel = "",
    [ValidateRange(1,20)][int]$Results = 8,
    [switch]$Download,
    [string]$OutputDir = "$env:USERPROFILE\Desktop\cody\youtube\downloads"
)

. (Join-Path $PSScriptRoot "rank-youtube-candidates.ps1")
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
        searched = $(if ($Url) { $null } else { $Query })
        chosen = $chosen
        output_file = $path
        checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        publication = "DISABLED"
        accepted_four_clips = $false
    } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $report
}
# A local trim does not require yt-dlp or network access.
if ($TrimSource) {
    if (-not $ClipOutput) { throw 'Provide -ClipOutput with a new .mp4 path.' }
    Need 'ffmpeg'; Need 'ffprobe'; Need 'py'
    $trimArgs = @('-3.13', (Join-Path $PSScriptRoot 'trim-video.py'), '--source', $TrimSource, '--output', $ClipOutput, '--start', $Start)
    if ($End -and $Duration) { throw 'Use -End OR -Duration.' }
    if ($End) { $trimArgs += @('--end', $End) }
    elseif ($Duration) { $trimArgs += @('--duration', $Duration) }
    else { throw 'Provide -End or -Duration.' }
    if ($Mute) { $trimArgs += '--mute' }
    & py @trimArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & py -3.13 (Join-Path $PSScriptRoot 'youtube-library.py')
    exit $LASTEXITCODE
}
try {
    if (-not $Url -and -not $Query.Trim()) { throw "Provide -Query, -Url, or -TrimSource." }
    Need "yt-dlp"
    if ($Download) { Need "ffprobe"; Need "py" }
    $selected = $null
    if ($Url) {
        if ($Url -notmatch '^https://(www\.|m\.)?(youtube\.com|youtu\.be)/') {
            throw "Use a YouTube watch URL, or omit -Url and let the bot search."
        }
        $metadataLines = @(& yt-dlp --no-warnings --no-playlist --skip-download --dump-single-json -- $Url 2>$null)
        if ($LASTEXITCODE -ne 0) { throw 'Could not retrieve source video metadata.' }
        $metadata = ($metadataLines -join "`n") | ConvertFrom-Json
        $selected = [pscustomobject]@{ id=[string](Get-YoutubeField $metadata 'id'); title=[string](Get-YoutubeField $metadata 'title'); uploader=[string](Get-YoutubeField $metadata 'channel' (Get-YoutubeField $metadata 'uploader')); url=$Url; score=0; duration=(Get-YoutubeField $metadata 'duration' 0) }
    }
    else {
        Write-Host "Searching YouTube: $Query"
        $lines = @(& yt-dlp --flat-playlist --no-warnings --no-playlist --dump-json "ytsearch$($Results):$Query" 2>$null)
        if ($LASTEXITCODE -ne 0 -or $lines.Count -eq 0) { throw "YouTube search failed; check yt-dlp version/network connectivity." }
        $videos = @()
        foreach ($line in $lines) {
            try { $videos += ($line | ConvertFrom-Json) } catch { continue }
        }
        $found = @(Get-RankedYoutubeCandidates -Query $Query -Candidates $videos -ExpectedChannel $ExpectedChannel)
        $ranked = @(Sort-YoutubeCandidates $found)
        $ranked | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $resultsFile
        if ($ranked.Count -eq 0) { throw "No usable YouTube candidates found." }
        Write-Host "Candidate videos (metadata relevance only, not scene verification):"
        foreach ($candidate in $ranked) {
            Write-Host ("[{0}] {1}" -f $candidate.score, $candidate.title)
            Write-Host ("  Channel: {0} | Duration: {1}s" -f $candidate.uploader, $candidate.duration)
            Write-Host ("  {0}" -f $candidate.url)
        }
        $selected = $ranked[0]
        Write-Host "Top candidate: $($selected.url)"
    }
    if (-not $Download) {
        Save-Report "SEARCH_COMPLETE" "Discovery complete; no download requested; scene content and rights not confirmed" $selected
        Write-Host "Search saved to: $resultsFile"
        Write-Host "To download the top candidate, rerun with -Download after checking permissions."
        exit 0
    }
    if ($selected.id -notmatch "^[A-Za-z0-9_-]{11}$") { throw "Could not identify an exact video ID; use a watch URL or youtu.be URL." }
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
    $channelProperty = $selected.PSObject.Properties['uploader']
    $channelName = if ($channelProperty) { [string]$channelProperty.Value } else { '' }
    [ordered]@{video_id=$id; title=$selected.title; channel=$channelName; query=$(if ($Url) { '' } else { $Query }); source_url=$chosenUrl; rights_status='NOT_VERIFIED'} | ConvertTo-Json | Set-Content -Encoding UTF8 ([IO.Path]::ChangeExtension($file, '.source.json'))
    & py -3.13 (Join-Path $PSScriptRoot 'youtube-library.py')
    if ($LASTEXITCODE -ne 0) { throw 'Download succeeded but local inventory update failed.' }
    Save-Report "DOWNLOAD_VERIFIED" "Candidate file retrieved; scene events, short clips and reuse rights remain unverified" $selected $file
    Write-Host "Candidate downloaded: $file"
    Write-Host "NOT PASSED: still require four visually verified <=3s scene clips, rights and GitHub assets."
}
catch {
    Save-Report "FAILED" $_.Exception.Message
    Write-Error $_.Exception.Message
    exit 1
}
