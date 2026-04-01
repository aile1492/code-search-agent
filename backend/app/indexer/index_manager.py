"""Vector DB management using ChromaDB.

Handles indexing, searching, and project management.
"""

import os
import hashlib
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings

from app.config import CHROMA_PERSIST_DIR
from app.indexer.chunker import CodeChunk, chunk_project, collect_files
from app.indexer.embedder import embed_texts, embed_query, format_chunk_for_embedding


# Project metadata file
PROJECTS_META_FILE = os.path.join(CHROMA_PERSIST_DIR, "projects.json")


def _get_client() -> chromadb.ClientAPI:
    """Get or create ChromaDB persistent client."""
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    return chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )


def _collection_name(project_name: str) -> str:
    """Sanitize project name for ChromaDB collection name."""
    safe = project_name.lower().replace(" ", "_").replace("-", "_")
    # ChromaDB collection names: 3-63 chars, alphanumeric + underscores
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    if len(safe) < 3:
        safe = safe + "_project"
    return safe[:63]


def _chunk_id(chunk: CodeChunk) -> str:
    """Generate a unique ID for a chunk."""
    content = f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}:{chunk.name}"
    return hashlib.md5(content.encode()).hexdigest()


def _load_projects_meta() -> dict:
    """Load project metadata from disk."""
    if os.path.exists(PROJECTS_META_FILE):
        with open(PROJECTS_META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_projects_meta(meta: dict):
    """Save project metadata to disk."""
    os.makedirs(os.path.dirname(PROJECTS_META_FILE), exist_ok=True)
    with open(PROJECTS_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def index_project(
    project_path: str,
    project_name: str | None = None,
    on_progress=None,
) -> dict:
    """Index a project directory into ChromaDB.

    Args:
        project_path: Absolute path to the project root
        project_name: Optional name (defaults to directory name)
        on_progress: Optional callback(stage, message, progress_pct)

    Returns:
        dict with indexing stats
    """
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        raise ValueError(f"Not a valid directory: {project_path}")

    if project_name is None:
        project_name = os.path.basename(project_path)

    col_name = _collection_name(project_name)

    if on_progress:
        on_progress("scanning", f"Scanning files in {project_name}...", 0)

    # Collect and chunk files
    files = collect_files(project_path)
    if not files:
        raise ValueError(f"No indexable source files found in {project_path}")

    if on_progress:
        on_progress("parsing", f"Parsing {len(files)} files with Tree-sitter...", 10)

    chunks = chunk_project(project_path)
    if not chunks:
        raise ValueError("No code chunks could be extracted")

    if on_progress:
        on_progress("embedding", f"Embedding {len(chunks)} code chunks...", 30)

    # Prepare texts for embedding
    texts = [
        format_chunk_for_embedding(
            content=c.content,
            context=c.context,
            file_path=c.file_path,
            chunk_type=c.chunk_type,
            name=c.name,
            language=c.language,
        )
        for c in chunks
    ]

    # Batch embed
    BATCH_SIZE = 64
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_embeds = embed_texts(batch)
        all_embeddings.extend(batch_embeds)
        if on_progress:
            pct = 30 + int(60 * (i + len(batch)) / len(texts))
            on_progress("embedding", f"Embedded {i + len(batch)}/{len(chunks)} chunks", pct)

    if on_progress:
        on_progress("storing", "Storing in vector database...", 90)

    # Store in ChromaDB
    client = _get_client()

    # Delete existing collection if re-indexing
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},
    )

    # ChromaDB add in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        batch_embeds = all_embeddings[i:i + BATCH_SIZE]
        batch_ids = [_chunk_id(c) for c in batch_chunks]
        batch_docs = [c.content for c in batch_chunks]
        batch_metas = [
            {
                "file_path": c.file_path,
                "language": c.language,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "chunk_type": c.chunk_type,
                "name": c.name,
                "context": c.context[:500],
            }
            for c in batch_chunks
        ]
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeds,
            documents=batch_docs,
            metadatas=batch_metas,
        )

    # Collect language stats
    languages = list(set(c.language for c in chunks))

    # Save project metadata
    meta = _load_projects_meta()
    meta[project_name] = {
        "path": project_path,
        "collection": col_name,
        "total_files": len(files),
        "total_chunks": len(chunks),
        "languages": languages,
    }
    _save_projects_meta(meta)

    if on_progress:
        on_progress("done", "Indexing complete!", 100)

    return {
        "project": project_name,
        "total_files": len(files),
        "total_chunks": len(chunks),
        "languages": languages,
        "status": "indexed",
    }


def search_code(
    query: str,
    project_name: str | None = None,
    n_results: int = 10,
) -> list[dict]:
    """Search indexed code using semantic similarity.

    Args:
        query: Natural language query or code snippet
        project_name: Optional project to search in (searches all if None)
        n_results: Number of results to return

    Returns:
        List of result dicts with code, metadata, and similarity score
    """
    client = _get_client()
    query_embedding = embed_query(query)

    results = []

    if project_name:
        meta = _load_projects_meta()
        if project_name not in meta:
            return []
        col_name = meta[project_name]["collection"]
        collections = [client.get_collection(col_name)]
    else:
        # Search all collections
        meta = _load_projects_meta()
        collections = []
        for info in meta.values():
            try:
                collections.append(client.get_collection(info["collection"]))
            except Exception:
                continue

    for collection in collections:
        try:
            res = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            continue

        if res["documents"] and res["documents"][0]:
            for doc, meta_item, dist in zip(
                res["documents"][0],
                res["metadatas"][0],
                res["distances"][0],
            ):
                results.append({
                    "code": doc,
                    "file_path": meta_item.get("file_path", ""),
                    "language": meta_item.get("language", ""),
                    "start_line": meta_item.get("start_line", 0),
                    "end_line": meta_item.get("end_line", 0),
                    "chunk_type": meta_item.get("chunk_type", ""),
                    "name": meta_item.get("name", ""),
                    "context": meta_item.get("context", ""),
                    "similarity": round(1 - dist, 4),  # cosine distance -> similarity
                })

    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:n_results]


def list_projects() -> list[dict]:
    """List all indexed projects."""
    meta = _load_projects_meta()
    return [
        {
            "name": name,
            "path": info["path"],
            "total_files": info["total_files"],
            "total_chunks": info["total_chunks"],
            "languages": info["languages"],
        }
        for name, info in meta.items()
    ]


def delete_project(project_name: str) -> bool:
    """Delete an indexed project."""
    meta = _load_projects_meta()
    if project_name not in meta:
        return False

    col_name = meta[project_name]["collection"]
    client = _get_client()
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    del meta[project_name]
    _save_projects_meta(meta)
    return True
