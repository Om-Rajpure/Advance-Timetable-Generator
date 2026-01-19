Write-Host "🚀 Launching Smart Timetable System..." -ForegroundColor Cyan

# Start Backend
Write-Host "Starting Backend..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "app.py" -WorkingDirectory "backend"

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Yellow
# On Windows, npm is a batch file, so we need npm.cmd
Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev" -WorkingDirectory "frontend"

Write-Host "✅ Systems Go! Access the app at http://localhost:5173" -ForegroundColor Green
Write-Host "   Admin Credentials: Om / Om@123" -ForegroundColor Gray
