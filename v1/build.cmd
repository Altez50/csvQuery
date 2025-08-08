@echo off
echo Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    echo Please run setup.cmd first to create the virtual environment
    pause
    exit /b 1
)

echo Building application with PyInstaller...
echo Getting version info...
for /f "delims=" %%i in ('.venv\Scripts\python.exe -c "from version_info import get_last_modification_date; print(get_last_modification_date().replace(' ', '_').replace(':', '-'))"') do set VERSION_DATE=%%i
echo Version date: %VERSION_DATE%
.venv\Scripts\python.exe -m PyInstaller --onefile --windowed --icon=icons\main.png --name=csvQuery_%VERSION_DATE% main.py
if %errorlevel% neq 0 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo Build completed successfully!
echo Executable created in dist\csvQuery_%VERSION_DATE%.exe
pause