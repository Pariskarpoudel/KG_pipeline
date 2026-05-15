import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import config

logger = logging.getLogger(__name__)

# _model = SentenceTransformer("all-MiniLM-L6-v2")
# utils/embedder.py
_model = SentenceTransformer(
    config.EMBEDDING_MODEL,
    trust_remote_code=config.EMBEDDING_TRUST_REMOTE_CODE
)

def embed(texts: list[str]) -> np.ndarray:
    """Embed a list of strings. Returns normalized embeddings."""
    if not texts:
        raise ValueError("Cannot embed empty list")
    return _model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=config.EMBEDDING_NORMALIZE
    )


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))