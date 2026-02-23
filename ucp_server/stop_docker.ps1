# UCP Server Docker Stop Script
# Usage: .\stop_docker.ps1 [Options]
# Options: -RemoveVolumes (Remove data volumes)

param(
    [switch]$RemoveVolumes = $false
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   UCP Server - Docker Stop Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Display currently running containers
Write-Host "📊 Current container status:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# Stop containers
Write-Host "🛑 Stopping UCP Server..." -ForegroundColor Yellow

if ($RemoveVolumes) {
    Write-Host "⚠️  All data volumes (including database) will be removed" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "❌ Cancelled" -ForegroundColor Red
        exit 0
    }
    docker-compose down -v
} else {
    docker-compose down
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ UCP Server stopped" -ForegroundColor Green
    Write-Host ""
    if (-not $RemoveVolumes) {
        Write-Host "💾 Data preserved (database, keys, etc.)" -ForegroundColor Cyan
        Write-Host "   For complete removal, use: .\stop_docker.ps1 -RemoveVolumes" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ Stop failed!" -ForegroundColor Red
}
