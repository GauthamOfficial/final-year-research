@echo off
REM Run git commands using full path (use this until Git is in your PATH)
set "GIT=C:\Program Files\Git\bin\git.exe"
if not exist "%GIT%" (
    echo Git not found. Install from https://git-scm.com/download/win
    exit /b 1
)
"%GIT%" init
"%GIT%" branch -M main
echo Done. Run: push-to-github.ps1  (or add Git to PATH - see below)
