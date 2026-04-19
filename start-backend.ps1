$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $here "backend")

python -m pip install -r "requirements.txt"
python -m uvicorn main:app --host 127.0.0.1 --port 8000

