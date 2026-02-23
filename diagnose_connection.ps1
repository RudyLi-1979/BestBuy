# Android App Connection Diagnostic Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Android App Connection Diagnostics" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Testing UCP Server Connectivity
Write-Host "1. Testing UCP Server Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://ucp.rudy.xx.kg/" -UseBasicParsing -TimeoutSec 10
    Write-Host "   ✅ UCP Server is Connectable" -ForegroundColor Green
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ UCP Server Cannot Connect" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 2. Testing Chat API
Write-Host "2. Testing Chat API..." -ForegroundColor Yellow
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
    
    Write-Host "   ✅ Chat API Working Properly" -ForegroundColor Green
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Gray
    Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Chat API Error" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 3. Checking Android App Configuration
Write-Host "3. Checking Android App Configuration..." -ForegroundColor Yellow
$ucpClientPath = "app\src\main\java\com\bestbuy\scanner\data\api\UCPRetrofitClient.kt"
if (Test-Path $ucpClientPath) {
    $content = Get-Content $ucpClientPath -Raw
    if ($content -match 'BASE_URL\s*=\s*"([^"]+)"') {
        $baseUrl = $matches[1]
        Write-Host "   BASE_URL: $baseUrl" -ForegroundColor Gray
        if ($baseUrl -eq "https://ucp.rudy.xx.kg/") {
            Write-Host "   ✅ URL Configuration Correct" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  URL May Be Incorrect" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ❌ Cannot Find UCPRetrofitClient.kt" -ForegroundColor Red
}
Write-Host ""

# 4. Checking Menu Configuration
Write-Host "4. Checking Menu Configuration..." -ForegroundColor Yellow
$menuPath = "app\src\main\res\menu\menu_main.xml"
if (Test-Path $menuPath) {
    $content = Get-Content $menuPath -Raw
    if ($content -match 'action_chat') {
        Write-Host "   ✅ Chat Mode Option Added to Menu" -ForegroundColor Green
    } else {
        Write-Host "   ❌ No Chat Mode Option in Menu" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ Cannot Find menu_main.xml" -ForegroundColor Red
}
Write-Host ""

# 5. Checking AndroidManifest
Write-Host "5. Checking AndroidManifest..." -ForegroundColor Yellow
$manifestPath = "app\src\main\AndroidManifest.xml"
if (Test-Path $manifestPath) {
    $content = Get-Content $manifestPath -Raw
    if ($content -match 'ChatActivity') {
        Write-Host "   ✅ ChatActivity Registered" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ChatActivity Not Registered" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ Cannot Find AndroidManifest.xml" -ForegroundColor Red
}
Write-Host ""

# 6. Checking build.gradle.kts
Write-Host "6. Checking Dependencies..." -ForegroundColor Yellow
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
            Write-Host "   ❌ Missing $dep" -ForegroundColor Red
            $allFound = $false
        }
    }
} else {
    Write-Host "   ❌ Cannot Find build.gradle.kts" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Ensure UCP Server is Running" -ForegroundColor White
Write-Host "2. Sync Gradle in Android Studio" -ForegroundColor White
Write-Host "3. Rebuild Project" -ForegroundColor White
Write-Host "4. Reinstall App" -ForegroundColor White
Write-Host "5. Check Android Logcat for Error Messages" -ForegroundColor White
Write-Host ""
