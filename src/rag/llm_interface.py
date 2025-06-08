import requests
import json
import logging
from typing import List, Dict, Any, Generator
from config.settings import settings

logger = logging.getLogger(__name__)

class LocalLLMInterface:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.LLM_MODEL
        logger.info(f"LLMInterface configured for model '{self.model}' at {self.base_url}")

    def is_ollama_running(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    def is_model_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("data", [])
                return any(m.get("id") == self.model for m in models)
        except Exception as e:
            logger.error(f"Model availability check failed: {e}")
        return False

    def generate_response(
        self,
        query: str,
        retrieved_docs: List[Dict[str, Any]],
        stream: bool = True
    ) -> Generator[str, None, None]:
        """
        Calls Ollama via the OpenAI‐compatible chat completions endpoint,
        streaming token-by-token via SSE.
        """
        # 1) Health and model checks
        if not self.is_ollama_running():
            yield "❌ Error: Ollama is not running."
            return
        if not self.is_model_available():
            yield f"❌ Error: Model '{self.model}' not pulled. Run: ollama pull {self.model}"
            return

        # 2) Build messages payload
        system = (
            "You are an expert building code assistant. Provide accurate, detailed answers "
            "with citations.\n\n"
            "Guidelines:\n"
            "1. Cite section and page numbers.\n"
            "2. State uncertainties.\n"
            "3. Use professional language.\n"
            "4. Format citations like: [Source: Section X.X, Page Y]\n"
        )
        # Flatten retrieved_docs into context
        context = []
        for i, doc in enumerate(retrieved_docs, 1):
            m = doc["metadata"]
            context.append(
                f"Document {i} (Page {m.get('page_number')}): {doc['content']}"
            )
        # Single system context message
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(context) + f"\n\nUser Question: {query}"}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS,
        }

        url = f"{self.base_url}/v1/chat/completions"
        logger.info(f"POST {url} (stream={stream})")
        try:
            resp = requests.post(url, json=payload, stream=stream, timeout=120)
            # Parse SSE‐style lines
            for line in resp.iter_lines(decode_unicode=True):
                if not line.strip():
                    continue
                # Ollama SSE lines start with "data: "
                if line.startswith("data: "):
                    data = line[len("data: "):]
                else:
                    data = line
                try:
                    part = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = part.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                    if choices[0].get("finish_reason") is not None:
                        return
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"❌ Error: {e}"
