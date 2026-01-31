# Git Sync Script
# This script pulls latest changes using rebase to keep history clean, then pushes local changes.

Write-Host "--- Starting Sync ---" -ForegroundColor Cyan

# 1. Fetch changes
Write-Host "Fetching from origin..."
git fetch origin

# 2. Pull with rebase
Write-Host "Pulling latest changes (rebase)..."
git pull --rebase origin $(git rev-parse --abbrev-ref HEAD)

if ($LASTEXITCODE -ne 0) {
    Write-Host "Sync failed! Resolving conflicts might be required." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Push local changes
Write-Host "Pushing to GitHub..."
git push origin $(git rev-parse --abbrev-ref HEAD)

Write-Host "--- Sync Complete! ---" -ForegroundColor Green
