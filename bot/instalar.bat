@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Instalando Hogger ===
where py >nul 2>&1 && (set PY=py) || (set PY=python)
%PY% --version >nul 2>&1 || (
  echo No encontre Python. Instalalo desde https://www.python.org/downloads/
  echo IMPORTANTE: tilda la casilla "Add python.exe to PATH" al instalar.
  pause
  exit /b
)
%PY% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
echo.
echo === Listo! ===
echo Ahora hace doble clic en iniciar.bat. La primera vez te pide el token: lo pegas y Enter.
pause
