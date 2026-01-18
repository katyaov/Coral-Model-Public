@echo off
REM -----------------------------------------------------------------------------
REM install_deps.bat
REM - Installs uv (fast Python package manager) if not already installed
REM - Runs 'uv sync' to create virtual environment and install all dependencies from pyproject.toml
REM For Windows (double-click or run in CMD/PowerShell)
REM -----------------------------------------------------------------------------

echo ========================================
echo  Coral Model - Dependency Installation
echo ========================================
echo.

REM Check if uv is already installed
where uv >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK] uv is already installed.
    echo.
) else (
    echo [INFO] uv is not installed. Installing uv...
    echo.
    
    REM Download and run the official uv installer for Windows
    echo Downloading uv installer from https://astral.sh/uv/install.ps1...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Failed to install uv. Please check your internet connection and try again.
        echo You can also manually install uv by visiting: https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    
    echo.
    echo [OK] uv installed successfully!
    echo.
    
    REM Add uv to PATH for current session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

REM Verify uv is accessible
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] uv was installed but is not in PATH yet.
    echo Please close this window and run the script again, or add '%USERPROFILE%\.cargo\bin' to your PATH.
    pause
    exit /b 1
)

echo ----------------------------------------
echo Running 'uv sync' to install dependencies from pyproject.toml...
echo This may take a few minutes on first run.
echo ----------------------------------------
echo.

REM Run uv sync to create venv and install all dependencies
uv sync

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 'uv sync' failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo All dependencies have been installed.
echo To start the dashboard, run 'launch_dashboard.bat' or use:
echo   uv run app.py
echo.
pause