# SecureFlow CSPM Platform setup and initialization script for Windows
$ErrorActionPreference = "Stop"

Write-Host "====================================================" -ForegroundColor Green
Write-Host "🚀 SECUREFLOW CSPM PLATFORM INITIALIZATION (WINDOWS)" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 1. Prerequisite checks
Write-Host "Checking system prerequisites..."
$prereqs = @("node", "npm", "docker")
foreach ($cmd in $prereqs) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Warning "Warning: '$cmd' is not installed or not in system path."
    }
}
Write-Host "✔ Prerequisites check completed." -ForegroundColor Green

# 2. Database Initialization & Seeding
Write-Host "Configuring database schema and seeding sandbox data..."
& C:\Users\HP\AppData\Local\Python\bin\python.exe scripts/seed_database.py
Write-Host "✔ Baseline database structures initialized." -ForegroundColor Green

# 3. Frontend package installation
Write-Host "Configuring frontend application workspace..."
Set-Location frontend
npm install
Write-Host "✔ Frontend dependencies successfully configured." -ForegroundColor Green
Set-Location ..

Write-Host "====================================================" -ForegroundColor Green
Write-Host "🎉 SETUP COMPLETED SUCCESSFULLY" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green
Write-Host "To launch the API backend server:"
Write-Host '  $env:PYTHONPATH="backend"'
Write-Host "  & C:\Users\HP\AppData\Local\Python\bin\python.exe -m uvicorn app.main:app --port 8000 --reload"
Write-Host ""
Write-Host "To launch the React dashboard frontend:"
Write-Host "  cd frontend"
Write-Host "  npm run dev"
Write-Host "====================================================" -ForegroundColor Green
