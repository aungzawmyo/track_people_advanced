# FaceScannerPro - PowerShell Demo Script
# Shows exactly how to run the application

Write-Host "🚀 FaceScannerPro - Running Demo" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📍 Step 1: Navigate to project directory" -ForegroundColor Yellow
Write-Host "Command: " -NoNewline
Write-Host 'cd "D:\Workspace\python\FaceScannerPro\tracker"' -ForegroundColor Green
Write-Host ""

Write-Host "📍 Step 2: Activate virtual environment" -ForegroundColor Yellow
Write-Host "Command: " -NoNewline
Write-Host '.\.venv\Scripts\activate.bat' -ForegroundColor Green
Write-Host "Expected: You'll see (.venv) at the start of your prompt" -ForegroundColor Gray
Write-Host ""

Write-Host "📍 Step 3: Run the application" -ForegroundColor Yellow
Write-Host "Command: " -NoNewline
Write-Host 'python minimal_app.py' -ForegroundColor Green
Write-Host ""

Write-Host "📍 Step 4: Access the dashboard" -ForegroundColor Yellow
Write-Host "Open browser to: " -NoNewline
Write-Host 'http://localhost:8080' -ForegroundColor Blue
Write-Host ""

Write-Host "📍 Step 5: Start tracking" -ForegroundColor Yellow
Write-Host "Click the 'Start' button in the web interface" -ForegroundColor Gray
Write-Host ""

Write-Host "📍 Step 6: Stop the application" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in the terminal" -ForegroundColor Gray
Write-Host ""

Write-Host "🎯 Complete Command Sequence:" -ForegroundColor Magenta
Write-Host 'cd "D:\Workspace\python\FaceScannerPro\tracker"' -ForegroundColor White
Write-Host '.\.venv\Scripts\activate.bat' -ForegroundColor White
Write-Host 'python minimal_app.py' -ForegroundColor White
Write-Host ""

Write-Host "✅ Environment Status Check:" -ForegroundColor Green
if (Test-Path ".venv") {
    Write-Host "✓ Virtual environment exists (.venv folder found)" -ForegroundColor Green
} else {
    Write-Host "✗ Virtual environment missing" -ForegroundColor Red
}

if (Test-Path "people_tracking.db") {
    Write-Host "✓ Database exists (people_tracking.db found)" -ForegroundColor Green
} else {
    Write-Host "! Database will be created on first run" -ForegroundColor Yellow
}

if (Test-Path "minimal_app.py") {
    Write-Host "✓ Main application file exists" -ForegroundColor Green
} else {
    Write-Host "✗ Main application file missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Ready to run! Use the commands above or run: " -NoNewline -ForegroundColor Cyan
Write-Host ".\start.bat" -ForegroundColor White
