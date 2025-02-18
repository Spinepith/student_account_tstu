@echo off
chcp 65001 >nul

cls
cd /d %~dp0

IF NOT EXIST "libs" (
    mkdir libs
)

set PYTHONPATH=libs

cd scripts
python install_requirements.py
IF %ERRORLEVEL% NEQ 0 (
   pause
   exit /b %ERRORLEVEL%
)

cd ..
python -m src.main