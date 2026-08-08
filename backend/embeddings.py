# backend/embeddings.py

from sentence_transformers import SentenceTransformer

model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def embed_text(text: str):
    try:
        embedding = get_model().encode(text).tolist()
        return embedding
    except Exception as e:
        print("Embedding Error:", repr(e))
        return None
