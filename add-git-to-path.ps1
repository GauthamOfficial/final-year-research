# Add Git to your user PATH so "git" works in any new terminal.
# Run once: Right-click -> Run with PowerShell (or: powershell -ExecutionPolicy Bypass -File add-git-to-path.ps1)

# Git for Windows uses \cmd for CLI; \bin has git.exe
$gitPath = "C:\Program Files\Git\cmd"
if (-not (Test-Path $gitPath)) { $gitPath = "C:\Program Files\Git\bin" }

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$gitPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$gitPath", "User")
    Write-Host "Added Git to your PATH: $gitPath"
    Write-Host "Open a NEW Command Prompt or PowerShell window and run: git --version"
} else {
    Write-Host "Git is already in your PATH."
}
