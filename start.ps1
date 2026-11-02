param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Chưa có .venv. Chạy: python -m venv .venv và .\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt'
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
    Copy-Item -LiteralPath (Join-Path $projectRoot '.env.example') -Destination (Join-Path $projectRoot '.env')
}
Write-Host "Internship Connect: http://localhost:$Port/app/"
& $pythonPath -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $Port --reload
