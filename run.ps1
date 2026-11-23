# Script PowerShell para iniciar o servidor do BurgerSync Ourinhos
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host " Iniciando BurgerSync Ourinhos - Analisador Feedback" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\Aluno\AppData\Local\Python\pythoncore-3.15-64\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $pythonExe) {
    Write-Error "Python nao encontrado no sistema."
    exit 1
}

Write-Host "[INFO] Utilizando Python: $pythonExe" -ForegroundColor Green
Set-Location -Path $PSScriptRoot
& $pythonExe execution\app.py
