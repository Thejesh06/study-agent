# backend/routes/api.py

from fastapi import APIRouter, HTTPException

from backend.llm import ask_groq
from backend.embeddings import embed_text
from backend.vector_db import add_document, search_similar

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.post("/query")
def query_rag(data: dict):
    """Query RAG pipeline (logic in Day 5+)."""
    return {"status": "query endpoint ready"}


@router.post("/upload")
def upload_file():
    """Document upload logic (Day 6-7)."""
    return {"status": "upload endpoint ready"}


@router.post("/echo")
def echo_data(data: dict):
    return {
        "you_sent": data
    }


@router.post("/llm-test")
def llm_test(data: dict):
    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field")

    answer = ask_groq(prompt)
    return {"answer": answer}


@router.post("/embed")
def embed_document(data: dict):
    """
    Take text and id, create an embedding, and store it in the in-memory vector DB.
    """
    text = data.get("text")
    doc_id = data.get("id")

    if not text or not doc_id:
        return {"error": "text and id are required"}

    vector = embed_text(text)

    if vector is None:
        return {"error": "Embedding failed"}

    # Store in our in-memory vector DB
    add_document(doc_id, text, vector)

    return {"status": "stored", "id": doc_id}


@router.post("/search")
def search_documents(data: dict):
    """
    Take a query, embed it, and return the most similar stored documents.
    """
    query = data.get("query")
    top_k = data.get("k", 3)

    if not query:
        return {"error": "query is required"}

    query_embedding = embed_text(query)
    if query_embedding is None:
        return {"error": "Embedding failed"}

    results = search_similar(query_embedding, top_k=top_k)

    return {"results": results}
