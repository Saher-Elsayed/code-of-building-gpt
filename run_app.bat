@echo off
REM -----------------------------------------
REM Run Script for Code of Building GPT (bind to localhost)
REM -----------------------------------------

REM 1. Activate virtual environment
call venv\Scripts\activate

REM 2. Load only real KEY=VALUE lines from .env (skip comments)
for /f "usebackq tokens=1* delims==" %%A in (`findstr /r "^[^#].*=" .env`) do (
    set %%A=%%B
)

REM 3. Launch Streamlit bound to localhost:8501
streamlit run src\ui\streamlit_app.py --server.address=127.0.0.1 --server.port=8501

pause
