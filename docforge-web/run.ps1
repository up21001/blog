# DocForge 서버 — 브라우저에서 http://127.0.0.1:8765/ 로 접속
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"
python -m uvicorn app:app --host 127.0.0.1 --port 8765 --reload
