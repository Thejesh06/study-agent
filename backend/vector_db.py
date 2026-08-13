# backend/vector_db.py

import json
import math
import os
from typing import List, Optional

STORE_PATH = "./vector_store.json"


def _load() -> List[dict]:
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save(documents: List[dict]) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(documents, f)


def add_document(doc_id: str, text: str, embedding: List[float], user: str = "default") -> None:
    documents = _load()
    documents = [d for d in documents if d["id"] != doc_id]
    documents.append({"id": doc_id, "text": text, "embedding": embedding, "user": user})
    _save(documents)


def list_documents(user: Optional[str] = None) -> List[str]:
    """Return unique document names (filenames) stored in the vector store."""
    documents = _load()
    if user:
        documents = [d for d in documents if d.get("user") == user]
    seen = set()
    names = []
    for d in documents:
        doc_name = d["id"].split("_chunk_")[0]
        if doc_name not in seen:
            seen.add(doc_name)
            names.append(doc_name)
    return names


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_chunks(doc_filter: Optional[str] = None, user: Optional[str] = None) -> List[dict]:
    """Return all stored chunks, optionally filtered by document and user."""
    documents = _load()
    if user:
        documents = [d for d in documents if d.get("user") == user]
    if doc_filter:
        documents = [d for d in documents if d["id"].startswith(doc_filter)]
    return documents


def search_similar(
    query_embedding: List[float],
    top_k: int = 5,
    doc_filter: Optional[str] = None,
    user: Optional[str] = None,
) -> List[dict]:
    """
    Return top_k most similar chunks.
    Filtered by user and optionally by document.
    """
    documents = _load()

    if user:
        documents = [d for d in documents if d.get("user") == user]
    if doc_filter:
        documents = [d for d in documents if d["id"].startswith(doc_filter)]

    scored = [
        (_cosine_similarity(query_embedding, d["embedding"]), d)
        for d in documents
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"id": d["id"], "text": d["text"], "score": round(score, 4)}
        for score, d in scored[:top_k]
    ]
