$ModelName = "qwen3guard-gen:0.6b"
$ModelPath = ".\Qwen3Guard-Gen-0.6B.Q4_K_M.gguf"

# ตรวจสอบว่าไฟล์ GGUF มีอยู่จริงหรือไม่
if (-Not (Test-Path -Path $ModelPath)) {
    Write-Host "Error: Model file $ModelPath not found in the current directory." -ForegroundColor Red
    Exit
}

$ModelfileContent = "FROM `"$ModelPath`""

Write-Host "1. Creating Modelfile..." -ForegroundColor Cyan
Set-Content -Path ".\Modelfile" -Value $ModelfileContent -Encoding UTF8

Write-Host "2. Loading model '$ModelName' into Ollama..." -ForegroundColor Cyan
ollama create $ModelName -f .\Modelfile

Write-Host "3. Cleaning up Modelfile..." -ForegroundColor Cyan
if (Test-Path -Path ".\Modelfile") {
    Remove-Item -Path ".\Modelfile" -Force
}

Write-Host "`nDone! Model imported successfully." -ForegroundColor Green
Write-Host "You can test the model with: " -NoNewline
Write-Host "ollama run $ModelName" -ForegroundColor Yellow

Write-Host "`nNote: If you want to use this model in your app, make sure NEMO_QWEN_GUARD_MODEL in settings.py is set to '$ModelName'" -ForegroundColor Yellow
