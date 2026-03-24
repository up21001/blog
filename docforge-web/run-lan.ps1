# 같은 Wi-Fi의 다른 기기에서 접속할 때 (방화벽 허용 필요)
Set-Location $PSScriptRoot
$env:PYTHONUTF8 = "1"
python -m uvicorn app:app --host 0.0.0.0 --port 8765 --reload
