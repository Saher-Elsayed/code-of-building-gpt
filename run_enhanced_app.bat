@echo off
REM Enhanced run script with MCP support
call venv\Scripts\activate

REM Load environment variables
for /f "usebackq tokens=1* delims==" %%A in (`findstr /r "^[^#].*=" .env`) do (
    set %%A=%%B
)

echo Starting Building Code GPT with MCP integration...
streamlit run src\ui\enhanced_streamlit_app.py --server.address=127.0.0.1 --server.port=8501
pause
