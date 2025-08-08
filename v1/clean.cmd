@echo off
echo Cleaning up build artifacts and cache files...

if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q "dist"
)

if exist "build" (
    echo Removing build directory...
    rmdir /s /q "build"
)

if exist "__pycache__" (
    echo Removing __pycache__ directory...
    rmdir /s /q "__pycache__"
)

if exist "*.spec" (
    echo Removing .spec files...
    del /q "*.spec"
)

echo Cleanup completed!
pause