"""
Part 3 — Local Semantic Search
Uses sentence-transformers/all-MiniLM-L6-v2 (pinned to ==3.0.0 in requirements.txt)
to compute cosine similarity between a query and all notes in the dataset.
No API key required. First run downloads model weights (~80 MB, cached under
~/.cache/huggingface). Every subsequent run is fully offline.
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any

# Lazy-load the model so the app starts fast even on cold starts
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D numpy arrays."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def semantic_search(
    query: str,
    notes: List[Dict[str, Any]],
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Rank `notes` by cosine similarity of their content embeddings to `query`.

    Parameters
    ----------
    query : str   — the search string
    notes : list  — each dict must have at least 'id', 'title', 'content',
                    'tag', and optionally other fields
    top_k : int   — number of top results to return (default 3)

    Returns
    -------
    List of dicts sorted descending by 'similarity', length <= top_k.
    """
    if not notes:
        return []

    model = _get_model()

    contents = [n["content"] for n in notes]
    # Encode all note contents + query in one batch for efficiency
    embeddings = model.encode(contents, convert_to_numpy=True)
    query_embedding = model.encode(query, convert_to_numpy=True)

    scored = []
    for note, emb in zip(notes, embeddings):
        sim = _cosine_similarity(query_embedding, emb)
        scored.append({**note, "similarity": round(sim, 6)})

    # Sort descending by similarity (manual sort — no sorted() with key)
    for i in range(1, len(scored)):
        cur = scored[i]
        j = i - 1
        while j >= 0 and scored[j]["similarity"] < cur["similarity"]:
            scored[j + 1] = scored[j]
            j -= 1
        scored[j + 1] = cur

    return scored[:top_k]
