param(
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -c "import fastapi, uvicorn" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "缺少 Web 依赖，请先运行: py -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "Knowledge Base Web: http://${HostAddress}:$Port" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务。" -ForegroundColor DarkGray
python -m uvicorn backend.app.main:app --host $HostAddress --port $Port
