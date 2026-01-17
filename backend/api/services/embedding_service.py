from sentence_transformers import SentenceTransformer
import os

# Global variable to hold the model in memory
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("DEBUG: Loading Local Embedding Model (all-MiniLM-L6-v2)...")
        # This will download the model the first time (~80MB)
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("DEBUG: Local Embedding Model Loaded.")
    return _embedding_model

def get_embedding(text: str):
    """
    Generates a 384-dimensional embedding for the input text 
    using the local sentence-transformers model.
    """
    try:
        if not text or not text.strip():
            return []
            
        model = get_embedding_model()
        # encode returns a numpy array, convert to list for JSON serialization
        embedding = model.encode(text).tolist()
        return embedding
    except Exception as e:
        print(f"Local Embedding Error: {e}")
        return []
