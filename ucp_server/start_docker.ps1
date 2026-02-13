# UCP Server Docker 快速啟動腳本
# 使用方法: .\start_docker.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   UCP Server - Docker 啟動腳本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 Docker Desktop 是否運行
Write-Host "🔍 檢查 Docker Desktop 狀態..." -ForegroundColor Yellow
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Desktop 未運行！" -ForegroundColor Red
    Write-Host "請先啟動 Docker Desktop，然後重新執行此腳本。" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker Desktop 正在運行" -ForegroundColor Green
Write-Host ""

# 檢查 .env 文件是否存在
Write-Host "🔍 檢查環境變數文件..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env 文件不存在！" -ForegroundColor Red
    if (Test-Path ".env.example") {
        Write-Host "📋 正在從 .env.example 創建 .env 文件..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✅ .env 文件已創建" -ForegroundColor Green
        Write-Host "⚠️  請編輯 .env 文件並填入您的 API Keys，然後重新執行此腳本。" -ForegroundColor Yellow
        exit 0
    } else {
        Write-Host "❌ .env.example 文件也不存在！" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✅ .env 文件存在" -ForegroundColor Green
Write-Host ""

# 檢查端口 58000 是否被佔用
Write-Host "🔍 檢查端口 58000..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 58000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  端口 58000 已被佔用！" -ForegroundColor Yellow
    $portInUse | Format-Table -Property LocalAddress, LocalPort, State, OwningProcess
    $continue = Read-Host "是否繼續啟動？(y/n)"
    if ($continue -ne "y") {
        Write-Host "❌ 已取消啟動" -ForegroundColor Red
        exit 0
    }
} else {
    Write-Host "✅ 端口 58000 可用" -ForegroundColor Green
}
Write-Host ""

# 停止並移除舊容器（如果存在）
Write-Host "🛑 檢查並清理舊容器..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null
Write-Host "✅ 清理完成" -ForegroundColor Green
Write-Host ""

# 建立並啟動容器
Write-Host "🚀 啟動 UCP Server..." -ForegroundColor Cyan
Write-Host ""
docker-compose up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "   ✅ UCP Server 啟動成功！" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Server 地址:" -ForegroundColor Cyan
    Write-Host "   - 本地: http://localhost:58000" -ForegroundColor White
    Write-Host "   - API 文件: http://localhost:58000/docs" -ForegroundColor White
    Write-Host "   - UCP Profile: http://localhost:58000/.well-known/ucp" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 常用命令:" -ForegroundColor Cyan
    Write-Host "   - 查看日誌: docker-compose logs -f" -ForegroundColor White
    Write-Host "   - 停止服務: docker-compose stop" -ForegroundColor White
    Write-Host "   - 重啟服務: docker-compose restart" -ForegroundColor White
    Write-Host "   - 完全移除: docker-compose down" -ForegroundColor White
    Write-Host ""
    Write-Host "⏳ 等待 5 秒讓服務完全啟動..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Write-Host ""
    Write-Host "🔍 容器狀態:" -ForegroundColor Cyan
    docker-compose ps
} else {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "   ❌ 啟動失敗！" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "查看錯誤日誌:" -ForegroundColor Yellow
    docker-compose logs --tail=50
}
