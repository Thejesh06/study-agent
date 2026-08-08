# backend/embeddings.py

from fastembed import TextEmbedding

model = None

def get_model():
    global model
    if model is None:
        model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return model

def embed_text(text: str):
    try:
        embeddings = list(get_model().embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        print("Embedding Error:", repr(e))
        return None
