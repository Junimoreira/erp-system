@echo off
cd /d "%~dp0"

echo ============================================
echo INICIANDO ERP VERDE INFANCIA
echo ============================================
echo.

set "ERP_PYTHON="

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version >nul 2>nul
    if not errorlevel 1 set "ERP_PYTHON=.venv\Scripts\python.exe"
)

if not defined ERP_PYTHON (
    where py >nul 2>nul
    if not errorlevel 1 set "ERP_PYTHON=py"
)

if not defined ERP_PYTHON (
    echo ERRO: Python nao foi encontrado neste computador.
    echo Instale o Python ou configure o ambiente virtual .venv.
    echo.
    pause
    exit /b 1
)

echo Python utilizado: %ERP_PYTHON%
echo.

"%ERP_PYTHON%" iniciar_erp.py

echo.
echo ============================================
echo ERP ENCERRADO
echo ============================================
pause
