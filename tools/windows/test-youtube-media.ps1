param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://(www\.|m\.)?(youtube\.com|youtu\.be)/')]
    [string]$Url,
    [string]$OutputDir = "output/youtube_media_test"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$folder = Join-Path $root $OutputDir
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$report = Join-Path $folder "youtube_test_report.json"

function Test-Exe($name) {
    $exe = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $exe) { throw "Missing $name. Install it, then retry. winget install yt-dlp.yt-dlp; winget install Gyan.FFmpeg" }
}
function Save-Report($status, $reason, $file = "") {
    $obj = [ordered]@{
        status = $status
        reason = $reason
        source_url = $Url
        output_file = $file
        checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
        host = $env:COMPUTERNAME
        publishing = "DISABLED"
        note = "A download is not proof of redistribution rights or verified clip events."
    }
    $obj | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $report
}
try {
    Test-Exe "yt-dlp"
    Test-Exe "ffprobe"
    & yt-dlp --version
    if ($LASTEXITCODE -ne 0) { throw "yt-dlp version check failed" }
    & yt-dlp --no-playlist --skip-download --no-warnings --print "%(id)s | %(title)s | %(duration)s" -- "$Url"
    if ($LASTEXITCODE -ne 0) { throw "YouTube metadata probe failed or access was denied" }

    & yt-dlp --no-playlist --no-progress --no-overwrites --restrict-filenames -f "bv*[height<=1080]+ba/b[height<=1080]/best" --merge-output-format mp4 -o (Join-Path $folder "%(id)s.%(ext)s") -- "$Url"
    if ($LASTEXITCODE -ne 0) { throw "yt-dlp could not download this source" }

    $videos = @(Get-ChildItem $folder -File | Where-Object { $_.Extension -in '.mp4','.mkv','.webm' })
    if ($videos.Count -eq 0) { throw "No downloaded video found" }
    $file = $videos[0].FullName
    & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$file"
    if ($LASTEXITCODE -ne 0) { throw "Downloaded file did not pass ffprobe" }
    Save-Report "DOWNLOAD_VERIFIED" "Video downloaded and probed; four scene-specific clips and rights review still pending" $file
    Write-Host "DOWNLOAD VERIFIED: $file"
    Write-Host "NEXT: manually confirm source permissions and the four scene events before trimming and committing clips."
}
catch {
    Save-Report "FAILED" $_.Exception.Message
    Write-Error $_.Exception.Message
    exit 1
}
