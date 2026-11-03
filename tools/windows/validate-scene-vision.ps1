<#
.SYNOPSIS
    Runs a real local CLIP CPU check against an isolated Bouriko checkout.
.DESCRIPTION
    This script is NEVER invoked by automatic production workflows.
    It installs pinned public-PR dependencies in a venv outside the repo,
    downloads the pinned 605 MB SafeTensors model (once), and optionally
    evaluates LOCAL positive/negative video fixtures. No videos are published.
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\validate-scene-vision.ps1
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\validate-scene-vision.ps1 -Fixtures C:\PrivateTests\fixtures.json
#>
[CmdletBinding()]
param(
    [string] $Fixtures = "",
    [string] $Python311 = "",
    [string] $EnvironmentDir = "",
    [switch] $SkipInstall
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$requirements = Join-Path $repo 'requirements-scene-vision.txt'
if (!(Test-Path $requirements)) { throw "Missing pinned requirements: $requirements" }
if (-not $EnvironmentDir) {
    $EnvironmentDir = Join-Path $env:LOCALAPPDATA 'Bouriko\vision-test-venv'
}
if (-not $Python311) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if (!$launcher) {
        throw "Python 3.11 launcher unavailable. Install Python 3.11 or pass -Python311 with its full exe path."
    }
    & py -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11)"
    if ($LASTEXITCODE -ne 0) { throw "Python 3.11 not available; supply -Python311 explicitly." }
    $Python311 = "py"
    $pythonArgs = @("-3.11")
} else {
    $pythonArgs = @()
    & $Python311 -c "import sys; assert sys.version_info[:2] == (3, 11)"
    if ($LASTEXITCODE -ne 0) { throw "Supplied Python is not 3.11" }
}
if (!(Test-Path (Join-Path $EnvironmentDir "Scripts\python.exe"))) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $EnvironmentDir) | Out-Null
    & $Python311 @pythonArgs -m venv $EnvironmentDir
    if ($LASTEXITCODE -ne 0) { throw "Could not create isolated Python virtualenv" }
}
$venvPython = Join-Path $EnvironmentDir 'Scripts\python.exe'
if (!$SkipInstall) {
    & $venvPython -m pip install -q --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
    & $venvPython -m pip check
    if ($LASTEXITCODE -ne 0) { throw "Pinned packages have incompatible dependencies" }
}
Write-Host "Checking pinned CLIP model with safe weights on CPU; first run may download ~605 MB."
$env:BOURIKO_PROJECT_DIR = $repo
$code = 'import os,sys;sys.path.insert(0,os.path.join(os.environ["BOURIKO_PROJECT_DIR"],"pipeline"));from frame_vision import model_bundle,MODEL_ID,MODEL_REVISION;torch,m,p=model_bundle();print("MODEL_LOAD_PASS",MODEL_ID,MODEL_REVISION,"device",next(m.parameters()).device)'
& $venvPython -c $code
if ($LASTEXITCODE -ne 0) { throw "Model load/inference setup failed" }
if ($Fixtures) {
    if (!(Test-Path $Fixtures)) { throw "Fixtures file missing: $Fixtures" }
    & $venvPython (Join-Path $repo 'tools\evaluate_scene_vision.py') --fixtures $Fixtures
    if ($LASTEXITCODE -ne 0) { throw "Calibration incomplete or observed false positives/false negatives. Check private report." }
}
Write-Host "Finished local model validation. Real full-video acceptance still requires reviewing finished MP4s."
