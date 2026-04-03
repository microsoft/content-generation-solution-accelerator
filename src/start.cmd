@echo off
REM Start the Content Generation Solution Accelerator (Windows)

echo Starting Content Generation Solution Accelerator...

REM Set Python path
set PYTHONPATH=%PYTHONPATH%;%cd%

REM Set default port if not provided
if "%PORT%"=="" set PORT=5000

REM Run with hypercorn
hypercorn app:app --bind 0.0.0.0:%PORT% --access-log - --error-log -
