# Start UCP Server on port 58000
Write-Host "Starting UCP Server on port 58000..."
uvicorn app.main:app --reload --port 58000 --log-level debug
