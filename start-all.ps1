$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start backend in a new window
Start-Process powershell -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-File", (Join-Path $here "start-backend.ps1")
)

# Start frontend in a new window
Start-Process powershell -ArgumentList @(
  "-NoProfile",
  "-ExecutionPolicy", "Bypass",
  "-File", (Join-Path $here "start-frontend.ps1")
)

Write-Host "Starting DevCareer..."
Write-Host "Backend:  http://127.0.0.1:8000/"
Write-Host "Frontend: http://localhost:3000/"

