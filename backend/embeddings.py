# backend/embeddings.py

from sentence_transformers import SentenceTransformer

# Load embedding model once (very fast & small)
model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str):
    """
    Convert text into an embedding vector using a local model (no API needed).
    """
    try:
        embedding = model.encode(text).tolist()  # convert numpy → python list
        return embedding
    except Exception as e:
        print("Embedding Error:", repr(e))
        return None
