# Push this project to https://github.com/GauthamOfficial/final-year-research.git
# Uses full path to git so it works even when Git is not in PATH.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$gitExe = "C:\Program Files\Git\bin\git.exe"
if (-not (Test-Path $gitExe)) {
    Write-Error "Git not found at $gitExe. Install from https://git-scm.com/download/win"
    exit 1
}

$remote = "https://github.com/GauthamOfficial/final-year-research.git"

if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..."
    & $gitExe init
    & $gitExe branch -M main
}

$origin = & $gitExe remote get-url origin 2>$null
if (-not $origin) {
    Write-Host "Adding remote origin..."
    & $gitExe remote add origin $remote
} elseif ($origin -ne $remote) {
    Write-Host "Updating remote origin to $remote"
    & $gitExe remote set-url origin $remote
}

Write-Host "Adding files..."
& $gitExe add -A
Write-Host "Committing..."
& $gitExe commit -m "Initial commit: RAG tourism project (Kandy/Badulla)"
Write-Host "Pushing to main..."
& $gitExe push -u origin main

Write-Host "Done. Repository: $remote"
