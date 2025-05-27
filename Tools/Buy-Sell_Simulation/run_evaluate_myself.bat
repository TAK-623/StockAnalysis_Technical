@echo off
setlocal enabledelayedexpansion

echo ====================================
echo Stock Evaluation Tool (Manual Input)
echo ====================================
echo.

:: Get first argument (signal date)
:INPUT_SIGNAL_DATE
echo Enter signal date (yyyymmdd format):
set /p SIGNAL_DATE=^> 

:: Basic input validation - just check if not empty
if "!SIGNAL_DATE!"=="" (
    echo Error: Please enter a date
    echo.
    goto INPUT_SIGNAL_DATE
)

echo.
echo Enter evaluation date (yyyymmdd format):
echo Press Enter without input to use latest Close value
set /p EVAL_DATE=^> 

:: Handle evaluation date
if "!EVAL_DATE!"=="" (
    set EVAL_DATE_DISPLAY=Not specified (Use latest Close value)
    set PYTHON_ARGS=!SIGNAL_DATE!
) else (
    set EVAL_DATE_DISPLAY=!EVAL_DATE! (Use Close value of specified date)
    set PYTHON_ARGS=!SIGNAL_DATE! !EVAL_DATE!
)

echo.
echo Execution Parameters:
echo   Signal Date: !SIGNAL_DATE!
echo   Evaluation Date: !EVAL_DATE_DISPLAY!
echo.

echo Execute with above settings?
set /p CONFIRM=y/n: 
if /i not "!CONFIRM!"=="y" (
    echo Execution cancelled
    goto END
)

echo.
echo ====================================
echo Starting process...
echo ====================================

:: Execute Python script
python evaluate_signals.py !PYTHON_ARGS!

:: Check execution result
if errorlevel 1 (
    echo.
    echo ====================================
    echo Error occurred
    echo ====================================
    echo Error occurred during Python script execution.
    echo Please check the following:
    echo - Python is installed
    echo - Required packages pandas yfinance are installed
    echo - CSV files exist in InputData folder
    echo - evaluate_signals.py file is in the same folder
    echo - Input dates are in correct format
) else (
    echo.
    echo ====================================
    echo Process completed successfully
    echo ====================================
    echo Results are output to Output folder.
    echo Used parameters:
    echo   Signal Date: !SIGNAL_DATE!
    echo   Evaluation Date: !EVAL_DATE_DISPLAY!
)

:END
echo.
echo Press any key to close window...
pause >nul