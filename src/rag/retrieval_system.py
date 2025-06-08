import uuid
import re
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import numpy as np
import logging

class RetrievalSystem:
    def __init__(
        self,
        embedding_model: str,
        vector_db_path: str,
        chunk_size: int,
        chunk_overlap: int
    ):
        self.logger = logging.getLogger(__name__)
        # Force CPU usage for embeddings to avoid GPU issues
        self.embedding_model = SentenceTransformer(embedding_model, device='cpu')
        # Initialize Chroma vector database
        self.client = chromadb.PersistentClient(
            path=vector_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Create or get the 'building_codes' collection
        self.collection = self.client.get_or_create_collection(
            name="building_codes",
            metadata={"hnsw:space": "cosine"}
        )
        # Set up the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )

    def add_documents(self, documents: list):
        """Add a list of documents (each with a 'text' field) into the vector store."""
        all_chunks, all_embeddings, all_metadatas, all_ids = [], [], [], []
        for doc in documents:
            doc_id = doc.get('id', str(uuid.uuid4()))
            chunks = self.text_splitter.split_text(doc['text'])
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_{idx}"
                # Compute embedding on CPU
                embedding = self.embedding_model.encode(chunk).tolist()
                metadata = {
                    'document_id': doc_id,
                    'chunk_index': idx,
                    'page_number': doc.get('page_number', 0),
                    'confidence': doc.get('confidence', 0),
                    'source': doc.get('source', 'unknown'),
                    'section': self._extract_section(chunk)
                }
                all_chunks.append(chunk)
                all_embeddings.append(embedding)
                all_metadatas.append(metadata)
                all_ids.append(chunk_id)

        # Batch insert for performance
        batch_size = 100
        for start in range(0, len(all_chunks), batch_size):
            end = start + batch_size
            self.collection.add(
                documents=all_chunks[start:end],
                embeddings=all_embeddings[start:end],
                metadatas=all_metadatas[start:end],
                ids=all_ids[start:end]
            )
        self.logger.info(f"Added {len(all_chunks)} chunks to the vector database.")

    def retrieve(self, query: str, k: int = 5) -> list:
        """Retrieve the top-k most relevant chunks for the given query."""
        # Embed the query
        q_emb = self.embedding_model.encode(query).tolist()
        # Query the vector database
        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        dists = results['distances'][0]

        retrieved = []
        for content, meta, dist in zip(docs, metas, dists):
            retrieved.append({
                'content': content,
                'metadata': meta,
                'score': 1 - dist
            })
        return retrieved

    def _extract_section(self, text: str) -> str:
        """Extract section numbers or titles from the text chunk via regex."""
        patterns = [
            r'Section\s+(\d+(?:\.\d+)*)',
            r'Chapter\s+(\d+)',
            r'Article\s+(\d+)'
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return 'unknown'
