@echo off
setlocal

set ROOT=%~dp0..
cd /d %ROOT%

if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Run miner\install.ps1 first.
  exit /b 1
)

set WALLET=%USERPROFILE%\.alice\wallet.json
set HASADDR=

:scan
if "%~1"=="" goto afterscan
if "%~1"=="--address" set HASADDR=1
shift
goto scan

:afterscan
if defined HASADDR goto run

if not exist "%WALLET%" (
  .venv\Scripts\python.exe miner\alice_wallet.py create
)

for /f "usebackq delims=" %%A in (`.venv\Scripts\python.exe -c "import json, pathlib; print(json.loads((pathlib.Path.home()/'.alice'/'wallet.json').read_text())['address'])"`) do set WALLET_ADDR=%%A

set CMDARGS=--address %WALLET_ADDR% %*

:run
if defined HASADDR (
  .venv\Scripts\python.exe miner\alice_miner.py %*
) else (
  .venv\Scripts\python.exe miner\alice_miner.py %CMDARGS%
)

