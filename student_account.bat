@echo off
chcp 65001 >nul

cls

IF NOT EXIST ".venv" (
    echo Создание виртуального окружения
    python -m venv .venv
)
call .venv\Scripts\activate

cd scripts
python install_requirements.py
IF %ERRORLEVEL% NEQ 0 (
   pause
   exit /b %ERRORLEVEL%
)

cd ..
python -m src.main