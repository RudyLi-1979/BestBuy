# UCP Server Docker 停止腳本
# 使用方法: .\stop_docker.ps1 [選項]
# 選項: -RemoveVolumes (移除資料卷)

param(
    [switch]$RemoveVolumes = $false
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   UCP Server - Docker 停止腳本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 顯示當前運行的容器
Write-Host "📊 當前容器狀態:" -ForegroundColor Yellow
docker-compose ps
Write-Host ""

# 停止容器
Write-Host "🛑 正在停止 UCP Server..." -ForegroundColor Yellow

if ($RemoveVolumes) {
    Write-Host "⚠️  將移除所有資料卷（包括資料庫）" -ForegroundColor Red
    $confirm = Read-Host "確定要繼續嗎？(y/n)"
    if ($confirm -ne "y") {
        Write-Host "❌ 已取消" -ForegroundColor Red
        exit 0
    }
    docker-compose down -v
} else {
    docker-compose down
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ UCP Server 已停止" -ForegroundColor Green
    Write-Host ""
    if (-not $RemoveVolumes) {
        Write-Host "💾 資料已保留（資料庫、金鑰等）" -ForegroundColor Cyan
        Write-Host "   如需完全移除，請使用: .\stop_docker.ps1 -RemoveVolumes" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Host "❌ 停止失敗！" -ForegroundColor Red
}
