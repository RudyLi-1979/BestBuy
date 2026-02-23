# Chat API Test Script (PowerShell)
# Uses Invoke-RestMethod to test Chat API

Write-Host "=== Chat API Tests ===" -ForegroundColor Green

# Test 1: Send first message
Write-Host "`n[Test 1] Sending message to AI assistant..." -ForegroundColor Cyan

$body = @{
    message = "I want to buy an iPhone"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
    
    Write-Host "✓ Success!" -ForegroundColor Green
    Write-Host "Session ID: $($response.session_id)" -ForegroundColor Yellow
    Write-Host "AI Response: $($response.message)" -ForegroundColor White
    
    # Save session_id for later use
    $sessionId = $response.session_id
    
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Continue conversation
Write-Host "`n[Test 2] Continue conversation (using session_id)..." -ForegroundColor Cyan

$body2 = @{
    message = "Add the first one to my cart"
    session_id = $sessionId
} | ConvertTo-Json

try {
    $response2 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body2
    
    Write-Host "✓ Success!" -ForegroundColor Green
    Write-Host "AI Response: $($response2.message)" -ForegroundColor White
    
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test 3: View shopping cart
Write-Host "`n[Test 3] View shopping cart..." -ForegroundColor Cyan

$body3 = @{
    message = "Show me my cart"
    session_id = $sessionId
} | ConvertTo-Json

try {
    $response3 = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body3
    
    Write-Host "✓ Success!" -ForegroundColor Green
    Write-Host "AI Response: $($response3.message)" -ForegroundColor White
    
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

# Test 4: View conversation history
Write-Host "`n[Test 4] View conversation history..." -ForegroundColor Cyan

try {
    $history = Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat/session/$sessionId/history" `
        -Method Get
    
    Write-Host "✓ Success!" -ForegroundColor Green
    Write-Host "Number of conversation records: $($history.messages.Count)" -ForegroundColor Yellow
    
} catch {
    Write-Host "✗ Failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Tests Completed ===" -ForegroundColor Green
Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
