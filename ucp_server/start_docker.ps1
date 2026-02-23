# UCP Server Docker Quick Start Script
# Usage: .\start_docker.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   UCP Server - Docker Startup Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker Desktop is running
Write-Host "🔍 Checking Docker Desktop status..." -ForegroundColor Yellow
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Desktop is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop first, then run this script again." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker Desktop is running" -ForegroundColor Green
Write-Host ""

# Check if .env file exists
Write-Host "🔍 Checking environment variable file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file does not exist!" -ForegroundColor Red
    if (Test-Path ".env.example") {
        Write-Host "📋 Creating .env file from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env file created" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env file and fill in your API Keys, then run this script again." -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "❌ .env.example file does not exist either!" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ .env file exists" -ForegroundColor Green
Write-Host ""

# Check if port 58000 is in use
Write-Host "🔍 Checking port 58000..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 58000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  Port 58000 is already in use!" -ForegroundColor Yellow
    $portInUse | Format-Table -Property LocalAddress, LocalPort, State, OwningProcess
    $continue = Read-Host "Continue startup? (y/n)"
    if ($continue -ne "y") {
        Write-Host "❌ Startup cancelled" -ForegroundColor Red
        exit 0
    }
} else {
    Write-Host "✅ Port 58000 is available" -ForegroundColor Green
}
Write-Host ""

# Stop and remove old containers (if exist)
Write-Host "🛑 Checking and cleaning old containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ Cleanup complete" -ForegroundColor Green
Write-Host ""

# Build and start containers
Write-Host "🚀 Starting UCP Server..." -ForegroundColor Cyan
Write-Host ""
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   ✅ UCP Server started successfully!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Server address:" -ForegroundColor Cyan
    Write-Host "   - Local: http://localhost:58000" -ForegroundColor White
    Write-Host "   - API Documentation: http://localhost:58000/docs" -ForegroundColor White
    Write-Host "   - UCP Profile: http://localhost:58000/.well-known/ucp" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Common commands:" -ForegroundColor Cyan
    Write-Host "   - View logs: docker-compose logs -f" -ForegroundColor White
    Write-Host "   - Stop service: docker-compose stop" -ForegroundColor White
    Write-Host "   - Restart service: docker-compose restart" -ForegroundColor White
    Write-Host "   - Remove completely: docker-compose down" -ForegroundColor White
    Write-Host ""
    Write-Host "⏳ Waiting 5 seconds for service to fully start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host ""
    Write-Host "🔍 Container status:" -ForegroundColor Cyan
    docker-compose ps
} else {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "   ❌ Startup failed!" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "View error logs:" -ForegroundColor Yellow
    docker-compose logs --tail=50
}
