@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Hogger - bot de The H's
if not exist .venv (
  echo Primero hace doble clic en instalar.bat
  pause
  exit /b
)
call .venv\Scripts\activate.bat
echo Revisando actualizaciones...
python -m pip install -q -r requirements.txt
:loop
python bot.py
echo.
echo Hogger se cerro. Reiniciando en 10 segundos (cerra esta ventana para apagarlo)...
timeout /t 10 >nul
goto loop
