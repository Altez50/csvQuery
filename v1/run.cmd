@echo off
echo Starting csvQuery application...

echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    echo Please run setup.cmd first to create the virtual environment
    pause
    exit /b 1
)

echo Running application...
python main.py
if %errorlevel% neq 0 (
    echo Error: Application failed to start
    pause
    exit /b 1
)

pause