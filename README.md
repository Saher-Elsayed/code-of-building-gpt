# 🏗️ Code of Building GPT

An **AI-powered building-code assistant** that lets you OCR your PDF code documents, index them in a vector store, and chat with a local Llama2 model (via Ollama) to get precise, cited answers about building‐code regulations.

---

## 🔍 Project Overview

- **OCR & Document Processing**  
  Uses Tesseract + Poppler to convert PDF pages into cleaned text blocks.

- **RAG Pipeline**  
  Splits text into overlapping chunks, embeds with SentenceTransformers, and stores in a Chroma vector database.

- **Local LLM Integration**  
  Leverages Llama2 (7B) running under Ollama to generate answers based on retrieved chunks.

- **Streamlit UI**  
  Simple web interface to upload PDFs, process them, tune retrieval settings, and chat with the assistant.

- **Citations & Sources**  
  Every answer includes an expander listing the **document**, **page**, **section/chapter**, and **paragraph** that informed the response.

---

 **🖥️ System Requirements (Windows) **
Python 3.8+ installed and on your PATH

Ollama 0.9+
Download & install from https://ollama.ai/download (choose Windows installer)

Verify with:
ollama --version

Tesseract OCR (UB Mannheim build)
Download installer from https://github.com/UB-Mannheim/tesseract/wiki
Install to C:\Program Files\Tesseract-OCR (default)

Poppler for Windows
Download poppler-*-x86_64.zip from https://github.com/oschwartz10612/poppler-windows/releases
Extract to C:\tools\poppler so you have C:\tools\poppler\Library\bin\pdfinfo.exe

⚙️ Setup
**Create & activate a virtual environment:
**python -m venv venv
.\venv\Scripts\activate

**Install Python dependencies:
**pip install --upgrade pip
pip install -r requirements.txt

**Configure environment variables:
copy .env.example .env

**Edit .env to match your paths:
**
# Ollama & LLM
OLLAMA_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=llama2:7b

# Vector DB
VECTOR_DB_PATH=./data/vector_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# OCR
TESSERACT_PATH="C:/Program Files/Tesseract-OCR/tesseract.exe"
POPPLER_PATH="C:/tools/poppler/Library/bin"
DPI=300

# UI & Streaming
STREAM_DELAY=0.01

Initialize and process system tools:
**ollama**
ollama pull llama2:7b

**Verify Tesseract & Poppler:**
tesseract --version
pdfinfo -v

**Run the application:
**
Start Ollama in one terminal:
ollama serve

Launch Streamlit in another terminal
.\run_app.bat
Open your browser at:

http://localhost:8501

## 🚀 Quickstart

### 1. Clone & Enter Repo
```bash
git clone https://github.com/Saher-Elsayed/code-of-building-gpt.git
cd code-of-building-gpt



📂 Project Structure

code-of-building-gpt/
├── .env                # Your environment variables
├── .env.example        # Template for .env
├── .gitignore
├── README.md
├── requirements.txt
├── run_app.bat         # Activates venv & runs Streamlit
├── setup_windows.bat   # (Optional) installs Tesseract, Poppler, Python deps
│
├── config/
│   └── settings.py     # Pydantic-based env settings
│
├── data/
│   ├── raw/            # Your unprocessed PDFs
│   ├── processed/      # (Optional) OCR outputs
│   └── vector_db/      # Chroma database files
│
├── src/
│   ├── ocr/
│   │   └── document_processor.py
│   ├── rag/
│   │   ├── retrieval_system.py
│   │   └── llm_interface.py
│   └── ui/
│       └── streamlit_app.py
│
└── tests/              # PyTest test suite

🏃‍♀️ Usage Workflow
Upload PDFs in the sidebar.
Click “Process” → see progress bar → green success banner.
Adjust Top-k Retrievals slider for how many chunks to fetch.
Ask any building-code question in the chat input.
View streamed answer + expand 📚 Sources for document/page/section/paragraph.
