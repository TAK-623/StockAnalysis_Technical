@echo off
chcp 65001 > nul
title Chart Generator Tool (Fast Mode)

echo ========================================
echo      Chart Generator Tool (Fast Mode)
echo ========================================
echo.

REM Save current directory
set CURRENT_DIR=%CD%

REM Move to script directory
cd /d "%~dp0"

REM Execute Python script directly
echo Starting chart generator tool...
echo.
python chart_generator.py

REM Return to original directory
cd /d "%CURRENT_DIR%"

echo.
echo Process completed.
pause
