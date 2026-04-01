"""Embedding model wrapper for code chunks.

Uses all-MiniLM-L6-v2 via ONNX Runtime (no PyTorch dependency).
Each chunk is embedded as: context + code content for better semantic matching.
"""

import os
import numpy as np
from pathlib import Path

_session = None
_tokenizer = None
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / MODEL_NAME


def _download_model():
    """Download the ONNX model and tokenizer if not cached."""
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = _MODEL_DIR / "model.onnx"
    tokenizer_path = _MODEL_DIR / "tokenizer.json"

    if onnx_path.exists() and tokenizer_path.exists():
        return

    from huggingface_hub import hf_hub_download

    hf_hub_download(
        repo_id=f"sentence-transformers/{MODEL_NAME}",
        filename="onnx/model.onnx",
        local_dir=str(_MODEL_DIR),
    )
    # Move from onnx/ subfolder
    downloaded = _MODEL_DIR / "onnx" / "model.onnx"
    if downloaded.exists():
        downloaded.rename(onnx_path)
        (_MODEL_DIR / "onnx").rmdir()

    hf_hub_download(
        repo_id=f"sentence-transformers/{MODEL_NAME}",
        filename="tokenizer.json",
        local_dir=str(_MODEL_DIR),
    )


def _get_session():
    """Load the ONNX session (lazy singleton)."""
    global _session
    if _session is None:
        import onnxruntime as ort
        _download_model()
        onnx_path = str(_MODEL_DIR / "model.onnx")
        _session = ort.InferenceSession(
            onnx_path,
            providers=["CPUExecutionProvider"],
        )
    return _session


def _get_tokenizer():
    """Load the tokenizer (lazy singleton)."""
    global _tokenizer
    if _tokenizer is None:
        from tokenizers import Tokenizer
        _download_model()
        _tokenizer = Tokenizer.from_file(str(_MODEL_DIR / "tokenizer.json"))
        _tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=128)
        _tokenizer.enable_truncation(max_length=128)
    return _tokenizer


def _mean_pooling(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    """Mean pooling with attention mask."""
    mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(np.float32)
    sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(mask_expanded, axis=1), a_min=1e-9, a_max=None)
    return sum_embeddings / sum_mask


def _normalize(embeddings: np.ndarray) -> np.ndarray:
    """L2 normalize embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.clip(norms, a_min=1e-9, a_max=None)


def _encode(texts: list[str]) -> np.ndarray:
    """Encode texts to normalized embeddings."""
    tokenizer = _get_tokenizer()
    session = _get_session()

    encodings = tokenizer.encode_batch(texts)
    input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
    attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

    outputs = session.run(
        None,
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        },
    )

    embeddings = _mean_pooling(outputs[0], attention_mask)
    return _normalize(embeddings)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts, returns list of float vectors."""
    if not texts:
        return []
    # Process in batches to limit memory
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = _encode(batch)
        all_embeddings.append(embeddings)
    return np.vstack(all_embeddings).tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    return _encode([query])[0].tolist()


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
