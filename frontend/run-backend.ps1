$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot
python -m uvicorn app.main:app --reload
