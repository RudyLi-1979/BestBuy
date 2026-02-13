# Android App 連線診斷腳本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Android App 連線診斷" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 測試 UCP Server 可達性
Write-Host "1. 測試 UCP Server 連線..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://ucp.rudy.xx.kg/" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ UCP Server 可連線" -ForegroundColor Green
    Write-Host "   狀態碼: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   回應: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ UCP Server 無法連線" -ForegroundColor Red
    Write-Host "   錯誤: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 2. 測試 Chat API
Write-Host "2. 測試 Chat API..." -ForegroundColor Yellow
try {
    $body = @{
        message = "Hello"
        session_id = "test-session"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "https://ucp.rudy.xx.kg/chat" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -TimeoutSec 30
    
    Write-Host "   ✅ Chat API 正常運作" -ForegroundColor Green
    Write-Host "   狀態碼: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   回應: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Chat API 錯誤" -ForegroundColor Red
    Write-Host "   錯誤: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 3. 檢查 Android App 配置
Write-Host "3. 檢查 Android App 配置..." -ForegroundColor Yellow
$ucpClientPath = "app\src\main\java\com\bestbuy\scanner\data\api\UCPRetrofitClient.kt"
if (Test-Path $ucpClientPath) {
    $content = Get-Content $ucpClientPath -Raw
    if ($content -match 'BASE_URL\s*=\s*"([^"]+)"') {
        $baseUrl = $matches[1]
        Write-Host "   BASE_URL: $baseUrl" -ForegroundColor Gray
        if ($baseUrl -eq "https://ucp.rudy.xx.kg/") {
            Write-Host "   ✅ URL 配置正確" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  URL 可能不正確" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ❌ 找不到 UCPRetrofitClient.kt" -ForegroundColor Red
}
Write-Host ""

# 4. 檢查 Menu 配置
Write-Host "4. 檢查 Menu 配置..." -ForegroundColor Yellow
$menuPath = "app\src\main\res\menu\menu_main.xml"
if (Test-Path $menuPath) {
    $content = Get-Content $menuPath -Raw
    if ($content -match 'action_chat') {
        Write-Host "   ✅ Chat Mode 選項已加入 Menu" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Menu 中沒有 Chat Mode 選項" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ 找不到 menu_main.xml" -ForegroundColor Red
}
Write-Host ""

# 5. 檢查 AndroidManifest
Write-Host "5. 檢查 AndroidManifest..." -ForegroundColor Yellow
$manifestPath = "app\src\main\AndroidManifest.xml"
if (Test-Path $manifestPath) {
    $content = Get-Content $manifestPath -Raw
    if ($content -match 'ChatActivity') {
        Write-Host "   ✅ ChatActivity 已註冊" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ChatActivity 未註冊" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ 找不到 AndroidManifest.xml" -ForegroundColor Red
}
Write-Host ""

# 6. 檢查 build.gradle.kts
Write-Host "6. 檢查依賴..." -ForegroundColor Yellow
$buildGradlePath = "app\build.gradle.kts"
if (Test-Path $buildGradlePath) {
    $content = Get-Content $buildGradlePath -Raw
    $dependencies = @(
        "activity-ktx",
        "fragment-ktx",
        "lifecycle-viewmodel-ktx",
        "retrofit",
        "kotlinx-coroutines-android"
    )
    
    $allFound = $true
    foreach ($dep in $dependencies) {
        if ($content -match $dep) {
            Write-Host "   ✅ $dep" -ForegroundColor Green
        } else {
            Write-Host "   ❌ 缺少 $dep" -ForegroundColor Red
            $allFound = $false
        }
    }
} else {
    Write-Host "   ❌ 找不到 build.gradle.kts" -ForegroundColor Red
}
Write-Host ""

# 總結
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "診斷完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步建議：" -ForegroundColor Yellow
Write-Host "1. 確保 UCP Server 正在運行" -ForegroundColor White
Write-Host "2. 在 Android Studio 中 Sync Gradle" -ForegroundColor White
Write-Host "3. Rebuild Project" -ForegroundColor White
Write-Host "4. 重新安裝 App" -ForegroundColor White
Write-Host "5. 檢查 Android Logcat 查看錯誤訊息" -ForegroundColor White
Write-Host ""
