from sentence_transformers import SentenceTransformer
import numpy as np

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        # Load all-MiniLM-L6-v2 lazily
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Computes cosine similarity between two text strings using sentence-transformers.
    
    WARNING: Cosine similarity is a cheap secondary evaluation signal. It measures semantic
    alignment of textual concepts but is blind to numeric value changes and logical negation.
    For example:
    - 'The GCS score is 14' and 'The GCS score is 15'
    - 'Patient has clinical signs of DVT' and 'Patient does not have clinical signs of DVT'
    will both output high cosine similarity (~0.9+) despite conveying clinically contradictory information.
    Always combine this with LLM-as-judge checks.
    """
    if not text1 or not text2:
        return 0.0
        
    try:
        model = get_embedding_model()
        embeddings = model.encode([text1, text2])
        
        emb1 = embeddings[0]
        emb2 = embeddings[1]
        
        dot_product = np.dot(emb1, emb2)
        norm_emb1 = np.linalg.norm(emb1)
        norm_emb2 = np.linalg.norm(emb2)
        
        if norm_emb1 == 0 or norm_emb2 == 0:
            return 0.0
            
        return float(dot_product / (norm_emb1 * norm_emb2))
    except Exception as e:
        print(f"Error calculating semantic similarity: {e}")
        return 0.0
