"""Embedding model wrapper for code chunks.

Uses sentence-transformers all-MiniLM-L6-v2 (free, local).
Each chunk is embedded as: context + code content for better semantic matching.
"""

from sentence_transformers import SentenceTransformer

# Singleton model instance
_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def get_model() -> SentenceTransformer:
    """Load the embedding model (lazy singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returns list of float vectors."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    model = get_model()
    embedding = model.encode(query, normalize_embeddings=True)
    return embedding.tolist()


def format_chunk_for_embedding(content: str, context: str, file_path: str,
                                chunk_type: str, name: str, language: str) -> str:
    """Format a code chunk into a string optimized for embedding.

    Combines context (imports, class header) with the code itself,
    plus metadata hints for better semantic matching.
    """
    parts = []

    # Add metadata hints
    parts.append(f"[{language}] [{chunk_type}] {name}")
    parts.append(f"File: {file_path}")

    # Add context (imports, class definition) if available
    if context:
        parts.append(f"Context:\n{context[:500]}")

    # Add the actual code
    parts.append(f"Code:\n{content[:1500]}")

    return "\n".join(parts)
