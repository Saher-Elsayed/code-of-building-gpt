@echo off
REM -----------------------------------------
REM Windows Setup Script for Code of Building GPT
REM -----------------------------------------

REM 1. Create virtual environment if not exists
if not exist venv (
    python -m venv venv
)

REM 2. Activate virtual environment
call venv\Scripts\activate

REM 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

REM 4. Add Poppler to PATH (adjust if you extracted it under project root)
SETX PATH "%PATH%;%~dp0poppler\Library\bin"

REM 5. Inform user
echo.
echo Setup complete! To run the app, use run_app.bat
pause