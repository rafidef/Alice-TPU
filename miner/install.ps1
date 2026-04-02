$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r miner/requirements.txt

Write-Host ""
Write-Host "Alice miner environment ready."
Write-Host "Next:"
Write-Host "  .\\miner\\run_miner.bat --ps-url https://ps.aliceprotocol.org"

