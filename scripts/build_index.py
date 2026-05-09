"""
Build a FAISS vector index from data/catalog.json.

Each product gets a searchable text blob:
  name + description + job_levels + test_types + languages

Run:  python scripts/build_index.py
Output: data/index.faiss  +  data/index_meta.json
"""

import json
import numpy as np
from pathlib import Path

CATALOG = Path(__file__).parent.parent / "data" / "catalog.json"
INDEX_PATH = Path(__file__).parent.parent / "data" / "index.faiss"
META_PATH = Path(__file__).parent.parent / "data" / "index_meta.json"


def product_to_text(p: dict) -> str:
    parts = [p.get("name", "")]
    if p.get("description"):
        parts.append(p["description"])
    if p.get("job_levels"):
        parts.append("Job levels: " + ", ".join(p["job_levels"]))
    if p.get("test_types"):
        type_map = {
            "A": "Ability/Aptitude",
            "B": "Biodata/Situational Judgment",
            "K": "Knowledge/Skills",
            "P": "Personality/Motivation",
            "S": "Simulation",
            "C": "Competency",
            "E": "Exercise/Assessment Centre",
        }
        expanded = [type_map.get(t, t) for t in p["test_types"]]
        parts.append("Test type: " + ", ".join(expanded))
    if p.get("languages"):
        parts.append("Languages: " + ", ".join(p["languages"][:5]))
    if p.get("duration_minutes"):
        parts.append(f"Duration: {p['duration_minutes']} minutes")
    return ". ".join(parts)


def build():
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Please install: pip install faiss-cpu sentence-transformers")
        raise

    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    print(f"Loaded {len(catalog)} products")

    model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    texts = [product_to_text(p) for p in catalog]

    print("Encoding…")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=128, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)

    # Normalize for cosine similarity via inner product
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / (norms + 1e-9)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    META_PATH.write_text(json.dumps(catalog, ensure_ascii=False))
    print(f"Index saved → {INDEX_PATH}  ({index.ntotal} vectors, dim={dim})")


if __name__ == "__main__":
    build()
