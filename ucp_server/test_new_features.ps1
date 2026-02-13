# Test New Best Buy API Features
# Run this script to test Store Availability, Also Bought, and Advanced Search

Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host "🧪 Testing New Best Buy API Features" -ForegroundColor Cyan
Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host ""

# Change to ucp_server directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found. Please run setup first." -ForegroundColor Red
    Write-Host "   Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please create .env with BESTBUY_API_KEY" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment ready" -ForegroundColor Green
Write-Host ""

# Test 1: Direct API Tests
Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host "📋 TEST 1: Direct API Tests (bestbuy_client.py)" -ForegroundColor Cyan
Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host ""

python test_new_features.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Direct API tests failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Chat tests..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

# Test 2: Chat Integration Tests
Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host "💬 TEST 2: Chat Integration Tests (Gemini + Functions)" -ForegroundColor Cyan
Write-Host "================================================================================================" -ForegroundColor Cyan
Write-Host ""

python test_chat_new_features.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Chat integration tests failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================================================" -ForegroundColor Green
Write-Host "✅ All tests completed successfully!" -ForegroundColor Green
Write-Host "================================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Summary of New Features:" -ForegroundColor Cyan
Write-Host "   1. 🏪 Store Availability Query (BOPIS) - Check product inventory at nearby stores" -ForegroundColor White
Write-Host "   2. 🛒 Also Bought Recommendations - Cross-sell suggestions" -ForegroundColor White
Write-Host "   3. 🔍 Advanced Search Operators - Filter by price, manufacturer, shipping, etc." -ForegroundColor White
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   - Test in Android app chat mode" -ForegroundColor White
Write-Host "   - Try queries like:" -ForegroundColor White
Write-Host "     * 'Where can I buy iPhone 15 near 94103?'" -ForegroundColor Gray
Write-Host "     * 'What do people buy with MacBook Air?'" -ForegroundColor Gray
Write-Host "     * 'Show me Apple laptops under $2000'" -ForegroundColor Gray
Write-Host ""
