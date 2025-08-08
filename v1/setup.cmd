@echo off
echo Setting up csvQuery development environment...

echo Creating virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    echo Please ensure Python is installed and available in PATH
    pause
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo Setup completed successfully!
echo You can now run the application with run.cmd or build it with build.cmd
pause