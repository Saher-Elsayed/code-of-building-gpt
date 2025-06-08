import streamlit as st
import time
import os
import sys
import logging

# — Console logging setup —
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Ensure project root is on Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.rag.retrieval_system import RetrievalSystem
from src.rag.llm_interface import LocalLLMInterface
from src.ocr.document_processor import DocumentProcessor
from config.settings import settings

class BuildingCodeGPTApp:
    def __init__(self):
        logger.info("Starting StreamlitApp")
        self.setup_page()

        logger.info("Initialize RetrievalSystem")
        self.retriever = RetrievalSystem(
            embedding_model=settings.EMBEDDING_MODEL,
            vector_db_path=settings.VECTOR_DB_PATH,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )

        logger.info("Initialize LocalLLMInterface")
        self.llm = LocalLLMInterface(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL
        )

        logger.info("Initialize DocumentProcessor")
        self.doc_proc = DocumentProcessor(
            tesseract_path=settings.TESSERACT_PATH,
            poppler_path=settings.POPPLER_PATH
        )

    def setup_page(self):
        st.set_page_config(
            page_title="Code of Building GPT",
            page_icon="🏗️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.title("🏗️ Code of Building GPT")
        st.markdown("*AI-Powered Building Code Assistant for Engineers*")

    def run(self):
        # Sidebar: upload, process, and settings
        with st.sidebar:
            st.header("📁 Document Upload")
            uploaded = st.file_uploader(
                "Upload PDF(s)", type=["pdf"], accept_multiple_files=True
            )
            if uploaded and st.button("Process"):
                self.process_uploaded(uploaded)

            st.markdown("---")
            st.header("⚙️ Settings")
            num_results = st.slider("Top-k Retrievals", 1, 20, 5)
            st.session_state.num_results = num_results

        # Main chat interface
        self.chat_interface()

    def process_uploaded(self, files):
        logger.info(f"Processing {len(files)} file(s)")
        progress = st.progress(0)
        status = st.empty()
        docs = []

        for i, f in enumerate(files, start=1):
            status.text(f"Processing {f.name} ({i}/{len(files)})")
            tmp_path = f"temp_{f.name}"
            with open(tmp_path, "wb") as out:
                out.write(f.getbuffer())

            try:
                pages = self.doc_proc.extract_text_from_pdf(tmp_path, dpi=settings.DPI)
                logger.info(f" - {len(pages)} pages extracted from {f.name}")
                for p in pages:
                    docs.append({
                        "id": f"{f.name}_{p['page_number']}",
                        "text": p["text"],
                        "page_number": p["page_number"],
                        "confidence": p["confidence"],
                        "source": f.name,
                        "chunk_index": p.get("chunk_index", 0),
                        "section": p.get("section", "unknown")
                    })
            except Exception as e:
                logger.error(f"OCR error on {f.name}: {e}")
                st.error(f"Error processing {f.name}: {e}")
            finally:
                os.remove(tmp_path)

            progress.progress(i / len(files))

        if docs:
            logger.info(f"Adding {len(docs)} chunks to vector DB")
            self.retriever.add_documents(docs)
            st.success(f"✅ Successfully processed {len(docs)} pages!")
        else:
            logger.warning("No pages extracted; nothing added to DB")

        status.empty()
        progress.empty()

    def chat_interface(self):
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # User input
        prompt = st.chat_input("Ask building code questions...")
        if not prompt:
            return

        # Greeting handler
        if prompt.strip().lower() in ("hi", "hello", "hey"):
            reply = "Hello there! Ready to help with building code questions—what can I do for you today?"
            st.chat_message("assistant").markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            logger.info("Handled greeting directly")
            return

        # Record user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        logger.info(f"User asks: {prompt}")

        # Retrieve top-k chunks
        k = st.session_state.get("num_results", 5)
        with st.spinner("🔍 Retrieving…"):
            docs = self.retriever.retrieve(prompt, k=k)
        logger.info(f"Retrieved {len(docs)} chunks")

        # Sidebar debug of retrieved snippets
        with st.sidebar:
            st.markdown(f"**🔍 Retrieved {len(docs)} chunks**")
            for idx, d in enumerate(docs, start=1):
                snippet = d["content"][:100].replace("\n", " ")
                st.markdown(f"{idx}. {snippet!r}…")

        # Generate and stream assistant response
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full = ""

            if not docs:
                msg = "😕 No relevant sections found."
                placeholder.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
                logger.warning("Aborting generation: no retrieved documents")
                return

            logger.info("Starting LLM streaming")
            for chunk in self.llm.generate_response(prompt, docs, stream=True):
                full += chunk
                placeholder.markdown(full + "▌")
                time.sleep(settings.STREAM_DELAY)
            placeholder.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
            logger.info("LLM stream complete")

            # Sources expander
            with st.expander("📚 Sources"):
                seen = set()
                for d in docs:
                    meta = d["metadata"]
                    src     = meta.get("source", "unknown")
                    pg      = meta.get("page_number", "N/A")
                    section = meta.get("section", "unknown")
                    para    = meta.get("chunk_index", 0) + 1

                    key = (src, pg, section, para)
                    if key in seen:
                        continue
                    seen.add(key)

                    st.markdown(
                        f"- **{src}**, page {pg}, section {section}, paragraph {para}"
                    )

if __name__ == "__main__":
    BuildingCodeGPTApp().run()
