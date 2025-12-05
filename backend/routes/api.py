from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def ping():
    return {"message": "pong"}

@router.post("/embed")
def embed_text(data: dict):
    """Embed text and save to vector DB (logic tomorrow)."""
    return {"status": "embed endpoint ready"}

@router.post("/query")
def query_rag(data: dict):
    """Query RAG pipeline (logic in Day 5)."""
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

from fastapi import HTTPException
from backend.llm import ask_groq

@router.post("/llm-test")
def llm_test(data: dict):
    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field")

    answer = ask_groq(prompt)
    return {"answer": answer}



