@echo off
echo Starting Humbly Plural...
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe humbly_plural.py
) else (
    python humbly_plural.py
)
pause