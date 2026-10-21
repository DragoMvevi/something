@echo off
title GOTA Split Detector [Sub-1ms] - Made by Drago
cd /d "%~dp0"

:: 1. Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: 2. Auto-install required dependencies if missing
python -c "import customtkinter" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing required dependencies (customtkinter)...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements. Please check your internet connection.
        pause
        exit /b 1
    )
    echo [SETUP] Installation complete!
)

:: 3. Launch application
python main.py
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
