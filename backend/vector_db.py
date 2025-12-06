# backend/vector_db.py

import math
from typing import List, Dict, Any

# In-memory "vector database"
# Each document: {"id": str, "text": str, "embedding": List[float]}
DOCUMENTS: List[Dict[str, Any]] = []


def add_document(doc_id: str, text: str, embedding: List[float]) -> None:
    """
    Store a document and its embedding in memory.
    """
    DOCUMENTS.append({
        "id": doc_id,
        "text": text,
        "embedding": embedding,
    })


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_similar(query_embedding: List[float], top_k: int = 3):
    """
    Return top_k most similar documents to the query embedding.
    """
    scored = []
    for doc in DOCUMENTS:
        score = cosine_similarity(query_embedding, doc["embedding"])
        scored.append((score, doc))

    # Sort by similarity descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top_k docs with their scores
    results = []
    for score, doc in scored[:top_k]:
        results.append({
            "id": doc["id"],
            "text": doc["text"],
            "score": score,
        })
    return results
