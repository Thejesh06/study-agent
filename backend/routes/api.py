# backend/routes/api.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from backend.auth import get_current_user
import pypdf
import io
import uuid
import json
import random
import re

from backend.llm import ask_groq
from backend.embeddings import embed_text
from backend.vector_db import add_document, search_similar, list_documents, get_chunks
from backend.chunker import chunk_text
from backend.database import get_doc_registry

router = APIRouter()

SYSTEM_PROMPT = """You are a smart study assistant. When the user asks a question:
- If the provided document excerpts contain relevant information, use them as your primary source and answer in detail.
- You may also use your own general knowledge to explain, expand, or clarify concepts from the document.
- If a follow-up question refers to something from the conversation history, use that context naturally.
- Always give thorough, helpful answers. Never refuse to answer — if the document doesn't cover something, use your general knowledge and say so."""


@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.get("/documents")
def get_documents(current_user: str = Depends(get_current_user)):
    return {"documents": list_documents(user=current_user)}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    filename = file.filename or "unknown"
    content = await file.read()

    if filename.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
    elif filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported")

    if not text.strip():
        raise HTTPException(status_code=400, detail="File appears to be empty or unreadable")

    chunks = chunk_text(text)
    doc_base_id = filename.replace(" ", "_")

    stored = 0
    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        if embedding is None:
            continue
        chunk_id = f"{doc_base_id}_chunk_{i}_{uuid.uuid4().hex[:6]}"
        add_document(chunk_id, chunk, embedding, user=current_user)
        stored += 1

    get_doc_registry().update_one(
        {"user": current_user},
        {"$addToSet": {"filenames": filename}},
        upsert=True
    )

    return {"status": "uploaded", "filename": filename, "chunks_stored": stored}


@router.post("/query")
def query_rag(data: dict, current_user: str = Depends(get_current_user)):
    """
    RAG pipeline with conversation history and optional document filter.
    Expects:
      - question: str
      - history: list of {role, content} — previous turns (optional)
      - doc_filter: str — filename to restrict search to (optional)
      - k: int — number of chunks to retrieve (optional, default 5)
    """
    question = data.get("question")
    history = data.get("history", [])
    doc_filter = data.get("doc_filter") or None
    top_k = data.get("k", 3)

    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' field")

    query_embedding = embed_text(question)
    if query_embedding is None:
        raise HTTPException(status_code=500, detail="Embedding failed")

    results = search_similar(query_embedding, top_k=top_k, doc_filter=doc_filter, user=current_user)

    # Build context block from retrieved chunks
    if results:
        context_parts = [f"[Excerpt {i+1}]\n{r['text'][:400]}" for i, r in enumerate(results)]
        context_block = "\n\n".join(context_parts)
        context_note = f"Relevant excerpts from the document:\n\n{context_block}\n\n---\n"
    else:
        context_note = "No document excerpts were found. Answer using your general knowledge.\n\n---\n"

    # Build message list: system → history → context + question
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include recent conversation history (last 4 turns = 2 exchanges)
    for turn in history[-4:]:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Attach context to the current question
    messages.append({
        "role": "user",
        "content": f"{context_note}\nQuestion: {question}",
    })

    answer = ask_groq(messages)

    return {
        "answer": answer,
        "sources": [{"id": r["id"], "score": r["score"]} for r in results],
    }


@router.post("/quiz")
def generate_quiz(data: dict, current_user: str = Depends(get_current_user)):
    """
    Generate multiple choice questions from an uploaded document.
    Expects:
      - doc_filter: str — document name to quiz on (optional, uses all if omitted)
      - num_questions: int — how many questions to generate (default 5)
    Returns a list of {question, options, answer, explanation} objects.
    """
    doc_filter = data.get("doc_filter") or None
    num_questions = min(int(data.get("num_questions", 5)), 10)

    chunks = get_chunks(doc_filter=doc_filter, user=current_user)
    if not chunks:
        raise HTTPException(status_code=400, detail="No documents found. Please upload a document first.")

    # Sample up to 8 chunks spread across the document for variety
    sample = random.sample(chunks, min(8, len(chunks)))
    context = "\n\n---\n\n".join(c["text"] for c in sample)

    prompt = f"""You are a quiz generator. Read the document excerpts below and generate exactly {num_questions} multiple choice questions that test understanding of the content.

Output ONLY a valid JSON array — no explanation, no markdown, no extra text. Use this exact format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A",
    "explanation": "Brief reason why this is correct."
  }}
]

Document excerpts:
{context}"""

    raw = ask_groq([{"role": "user", "content": prompt}])

    # Extract JSON array from response robustly
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise HTTPException(status_code=500, detail="Quiz generation failed — LLM did not return valid JSON.")

    try:
        questions = json.loads(match.group())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Quiz generation failed — could not parse questions.")

    return {"questions": questions}


@router.post("/llm-test")
def llm_test(data: dict):
    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing 'prompt' field")
    answer = ask_groq([{"role": "user", "content": prompt}])
    return {"answer": answer}
