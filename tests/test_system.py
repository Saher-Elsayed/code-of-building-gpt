import tempfile
from src.rag.retrieval_system import RetrievalSystem

def test_retrieval_system():
    with tempfile.TemporaryDirectory() as tmp:
        rs = RetrievalSystem(
            embedding_model="all-MiniLM-L6-v2",
            vector_db_path=tmp,
            chunk_size=100,
            chunk_overlap=10
        )
        docs = [{
            'id':'test1',
            'text':'Max building height is 50 feet in R1 zones.',
            'page_number':1,
            'confidence':1.0,
            'source':'test.pdf'
        }]
        rs.add_documents(docs)
        results = rs.retrieve("What is the height limit for residential buildings?", k=1)
        assert results, "Expected at least one result"
        assert "50 feet" in results[0]['content']