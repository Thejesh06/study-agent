# backend/vector_db.py

import os
from typing import List, Optional
from pinecone import Pinecone

_index = None


def _get_index():
    global _index
    if _index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _index = pc.Index(os.getenv("PINECONE_INDEX", "study-agent"))
    return _index


def add_document(doc_id: str, text: str, embedding: List[float], user: str = "default") -> None:
    filename = doc_id.split("_chunk_")[0]
    _get_index().upsert(
        vectors=[{
            "id": doc_id,
            "values": embedding,
            "metadata": {"text": text, "filename": filename}
        }],
        namespace=user
    )


def list_documents(user: Optional[str] = None) -> List[str]:
    namespace = user or "default"
    seen = set()
    try:
        for id_batch in _get_index().list(namespace=namespace):
            if isinstance(id_batch, str):
                id_batch = [id_batch]
            for vid in id_batch:
                if "_chunk_" in vid:
                    seen.add(vid.split("_chunk_")[0])
    except Exception as e:
        print("list_documents error:", e)
    return list(seen)


def get_chunks(doc_filter: Optional[str] = None, user: Optional[str] = None) -> List[dict]:
    namespace = user or "default"
    prefix = (doc_filter.replace(" ", "_") + "_chunk_") if doc_filter else None
    ids = []
    for id_batch in _get_index().list(namespace=namespace, prefix=prefix):
        if isinstance(id_batch, str):
            ids.append(id_batch)
        else:
            ids.extend(id_batch)

    if not ids:
        return []

    chunks = []
    for i in range(0, len(ids), 100):
        batch = ids[i:i + 100]
        result = _get_index().fetch(ids=batch, namespace=namespace)
        for vid, vec in result.vectors.items():
            chunks.append({"id": vid, "text": vec.metadata.get("text", "")})
    return chunks


def search_similar(
    query_embedding: List[float],
    top_k: int = 3,
    doc_filter: Optional[str] = None,
    user: Optional[str] = None,
) -> List[dict]:
    namespace = user or "default"
    filter_dict = None
    if doc_filter:
        filter_dict = {"filename": {"$eq": doc_filter.replace(" ", "_")}}

    results = _get_index().query(
        vector=query_embedding,
        top_k=top_k,
        filter=filter_dict,
        include_metadata=True,
        namespace=namespace
    )
    return [
        {"id": m.id, "text": m.metadata.get("text", ""), "score": round(m.score, 4)}
        for m in results.matches
    ]
