# backend/vector_db.py

import os
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "study_docs"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension

_client: QdrantClient = None

def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        if not QDRANT_URL or not QDRANT_API_KEY:
            raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must be set in environment variables")
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        existing = [c.name for c in _client.get_collections().collections]
        if COLLECTION not in existing:
            _client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
    return _client


def add_document(doc_id: str, text: str, embedding: List[float]) -> None:
    """Upsert a document chunk into Qdrant."""
    _get_client().upsert(
        collection_name=COLLECTION,
        points=[
            PointStruct(
                id=abs(hash(doc_id)) % (2**63),
                vector=embedding,
                payload={"doc_id": doc_id, "text": text},
            )
        ],
    )


def list_documents() -> List[str]:
    """Return unique document names stored in Qdrant."""
    results = _get_client().scroll(collection_name=COLLECTION, limit=1000, with_payload=True)[0]
    seen = set()
    names = []
    for point in results:
        doc_id = point.payload.get("doc_id", "")
        doc_name = doc_id.split("_chunk_")[0]
        if doc_name not in seen:
            seen.add(doc_name)
            names.append(doc_name)
    return names


def get_chunks(doc_filter: Optional[str] = None) -> List[dict]:
    """Return all chunks, optionally filtered by document name."""
    results = _get_client().scroll(collection_name=COLLECTION, limit=1000, with_payload=True)[0]
    chunks = [
        {"id": p.payload["doc_id"], "text": p.payload["text"]}
        for p in results
    ]
    if doc_filter:
        chunks = [c for c in chunks if c["id"].startswith(doc_filter)]
    return chunks


def search_similar(
    query_embedding: List[float],
    top_k: int = 5,
    doc_filter: Optional[str] = None,
) -> List[dict]:
    """Return top_k most similar chunks, optionally filtered by document."""
    results = _get_client().query_points(
        collection_name=COLLECTION,
        query=query_embedding,
        limit=top_k * 3 if doc_filter else top_k,
        with_payload=True,
    ).points

    output = []
    for hit in results:
        doc_id = hit.payload.get("doc_id", "")
        if doc_filter and not doc_id.startswith(doc_filter):
            continue
        output.append({
            "id": doc_id,
            "text": hit.payload.get("text", ""),
            "score": round(hit.score, 4),
        })
        if len(output) == top_k:
            break

    return output
