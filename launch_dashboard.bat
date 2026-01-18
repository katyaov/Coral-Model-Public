@echo off
REM -----------------------------------------------------------------------------
REM launch_dashboard.bat
REM - Launches the Coral Model Dashboard using 'uv run app.py'
REM - Automatically opens the browser to the dashboard URL
REM Usage: double-click or run from a command prompt in the project root
REM -----------------------------------------------------------------------------

echo ========================================
echo  Coral Model Dashboard Launcher
echo ========================================
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] uv is not installed!
    echo.
    echo Please run 'install_deps.bat' first to install uv and dependencies.
    echo.
    pause
    exit /b 1
)

REM Open the dashboard URL in the default browser (non-blocking)
echo Opening browser to http://127.0.0.1:8050...
start "" "http://127.0.0.1:8050"

echo.
echo Starting Coral Model Dashboard...
echo Press Ctrl+C to stop the server.
echo ----------------------------------------
echo.

REM Run the Flask app using uv (automatically uses the project's virtual environment)
uv run app.py

REM If process exits (Ctrl+C or crash), pause so user can read messages
echo.
echo ----------------------------------------
echo Dashboard has stopped.
pause