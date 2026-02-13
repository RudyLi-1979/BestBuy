# Chat API 測試腳本（PowerShell）
# 使用 Invoke-RestMethod 測試 Chat API

Write-Host "=== Chat API 測試 ===" -ForegroundColor Green

# 測試 1: 發送第一條訊息
Write-Host "`n[測試 1] 發送訊息給 AI 助手..." -ForegroundColor Cyan

$body = @{
    message = "I want to buy an iPhone"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "✓ 成功！" -ForegroundColor Green
    Write-Host "Session ID: $($response.session_id)" -ForegroundColor Yellow
    Write-Host "AI 回應: $($response.message)" -ForegroundColor White
    
    # 儲存 session_id 供後續使用
    $sessionId = $response.session_id
    
} catch {
    Write-Host "✗ 失敗: $_" -ForegroundColor Red
    exit 1
}

# 測試 2: 繼續對話
Write-Host "`n[測試 2] 繼續對話（使用 session_id）..." -ForegroundColor Cyan

$body2 = @{
    message = "Add the first one to my cart"
    session_id = $sessionId
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body2
    
    Write-Host "✓ 成功！" -ForegroundColor Green
    Write-Host "AI 回應: $($response2.message)" -ForegroundColor White
    
} catch {
    Write-Host "✗ 失敗: $_" -ForegroundColor Red
}

# 測試 3: 查看購物車
Write-Host "`n[測試 3] 查看購物車..." -ForegroundColor Cyan

$body3 = @{
    message = "Show me my cart"
    session_id = $sessionId
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body3
    
    Write-Host "✓ 成功！" -ForegroundColor Green
    Write-Host "AI 回應: $($response3.message)" -ForegroundColor White
    
} catch {
    Write-Host "✗ 失敗: $_" -ForegroundColor Red
}

# 測試 4: 查看對話歷史
Write-Host "`n[測試 4] 查看對話歷史..." -ForegroundColor Cyan

try {
    $history = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat/session/$sessionId/history" `
        -Method Get
    
    Write-Host "✓ 成功！" -ForegroundColor Green
    Write-Host "對話記錄數: $($history.messages.Count)" -ForegroundColor Yellow
    
} catch {
    Write-Host "✗ 失敗: $_" -ForegroundColor Red
}

Write-Host "`n=== 測試完成 ===" -ForegroundColor Green
Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
