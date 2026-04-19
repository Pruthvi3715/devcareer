$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $here "frontend")

npm install
npm run dev

