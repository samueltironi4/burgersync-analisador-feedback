@echo off
chcp 65001 > nul
title BurgerSync Ourinhos - Servidor Web

echo =======================================================
echo  Iniciando BurgerSync Ourinhos - Analisador Feedback
echo =======================================================
echo.

set PYTHON_CMD=python
if exist "C:\Users\Aluno\AppData\Local\Python\pythoncore-3.15-64\python.exe" (
    set PYTHON_CMD="C:\Users\Aluno\AppData\Local\Python\pythoncore-3.15-64\python.exe"
)

echo [INFO] Utilizando Python: %PYTHON_CMD%
%PYTHON_CMD% execution\app.py

pause
