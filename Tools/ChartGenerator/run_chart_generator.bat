@echo off
chcp 65001 > nul
title Chart Generator Tool

echo ========================================
echo           Chart Generator Tool
echo ========================================
echo.

REM Save current directory
set CURRENT_DIR=%CD%

REM Move to script directory
cd /d "%~dp0"

echo Checking Python environment...
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed.
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Checking required libraries...

REM Check required libraries
python -c "import yfinance" > nul 2>&1
if errorlevel 1 (
    echo Installing yfinance library...
    pip install yfinance
    if errorlevel 1 (
        echo Error: Failed to install yfinance.
        pause
        exit /b 1
    )
)

python -c "import matplotlib" > nul 2>&1
if errorlevel 1 (
    echo Installing matplotlib library...
    pip install matplotlib
    if errorlevel 1 (
        echo Error: Failed to install matplotlib.
        pause
        exit /b 1
    )
)

python -c "import pandas" > nul 2>&1
if errorlevel 1 (
    echo Installing pandas library...
    pip install pandas
    if errorlevel 1 (
        echo Error: Failed to install pandas.
        pause
        exit /b 1
    )
)

python -c "import numpy" > nul 2>&1
if errorlevel 1 (
    echo Installing numpy library...
    pip install numpy
    if errorlevel 1 (
        echo Error: Failed to install numpy.
        pause
        exit /b 1
    )
)

echo.
echo Library check completed.
echo.

REM Execute Python script
echo Starting chart generator tool...
echo.
python chart_generator.py

REM Return to original directory
cd /d "%CURRENT_DIR%"

echo.
echo Process completed.
pause
