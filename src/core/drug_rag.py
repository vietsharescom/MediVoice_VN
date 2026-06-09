# src/core/drug_rag.py
# RAG-001-DRUG-VECTOR — FID-VN-010
# ChromaDB + sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
# Query: distorted ASR token + diagnosis context → ranked INN candidates

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Optional

# Lazy imports — RAG-001 is optional feature; pipeline degrades gracefully if not installed
try:
    import chromadb
    from sentence_transformers import SentenceTransformer as _SentenceTransformer
    _DEPS_AVAILABLE = True
except ImportError:
    _DEPS_AVAILABLE = False

if TYPE_CHECKING:
    import chromadb as _chromadb_t

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "drug_db_v200"
DEFAULT_PERSIST_DIR = Path("data/drug_vectorstore")

# ---------------------------------------------------------------------------
# Internal — document builder
# ---------------------------------------------------------------------------

def _build_doc(inn: str, d: dict) -> str:
    """
    Build rich text document for one drug entry.
    Includes: INN, phonetic variants (all regions), keywords, brands,
    drug class, diagnoses, category, typical dose.
    """
    parts = [f"Tên thuốc INN: {inn}"]

    pv = d.get("phonetic_variants", {})
    north = " ".join(pv.get("north", []))
    central = " ".join(pv.get("central", []))
    south = " ".join(pv.get("south", []))
    if north:
        parts.append(f"Cách đọc miền Bắc: {north}")
    if central:
        parts.append(f"Cách đọc miền Trung: {central}")
    if south:
        parts.append(f"Cách đọc miền Nam: {south}")

    aliases = list(dict.fromkeys(d.get("keywords", []) + d.get("brands", [])))
    if aliases:
        parts.append(f"Tên khác biệt thể: {' '.join(aliases)}")

    drug_class = d.get("drug_class", "")
    if drug_class:
        parts.append(f"Nhóm thuốc: {drug_class}")

    category = d.get("category", "")
    if category:
        parts.append(f"Phân loại: {category}")

    diagnoses = " ".join(d.get("compatible_diagnoses", []))
    if diagnoses:
        parts.append(f"Dùng cho: {diagnoses}")

    typical = d.get("typical", "")
    if typical:
        parts.append(f"Liều thường dùng: {typical}")

    return "\n".join(parts)


def _doc_id(inn: str) -> str:
    """Stable ASCII-safe ID for ChromaDB."""
    return inn.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_drug_vectorstore(
    drug_db: dict,
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    embed_model: str = EMBED_MODEL,
) -> "chromadb.Collection":
    """
    Build ChromaDB vectorstore từ drug_db_v200 dict.
    Persist vào data/drug_vectorstore/ (gitignored).
    Gọi lại để rebuild khi drug_db thay đổi.

    Raises:
        ImportError: nếu chromadb / sentence-transformers chưa cài.
    """
    if not _DEPS_AVAILABLE:
        raise ImportError(
            "RAG-001 requires: pip install chromadb sentence-transformers"
        )

    persist_dir = Path(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(persist_dir))

    # Xóa collection cũ → rebuild sạch
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:  # nosec B110 — collection may not exist on first build
        pass

    by_inn: dict = drug_db.get("by_inn", {})
    if not by_inn:
        raise ValueError("drug_db['by_inn'] is empty — cannot build vectorstore")

    docs: list[str] = []
    ids: list[str] = []
    metadatas: list[dict] = []

    for inn, d in by_inn.items():
        docs.append(_build_doc(inn, d))
        ids.append(_doc_id(inn))
        metadatas.append({
            "inn": inn,
            "drug_class": d.get("drug_class", ""),
            "category": d.get("category", ""),
            "otc": str(d.get("otc", False)).lower(),
        })

    model = _SentenceTransformer(embed_model)
    embeddings = model.encode(docs, show_progress_bar=False).tolist()

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        documents=docs,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    return collection


def load_drug_vectorstore(
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
) -> Optional["chromadb.Collection"]:
    """
    Load persisted vectorstore. Returns None nếu chưa build.

    Raises:
        ImportError: nếu chromadb chưa cài.
    """
    if not _DEPS_AVAILABLE:
        raise ImportError(
            "RAG-001 requires: pip install chromadb sentence-transformers"
        )

    persist_dir = Path(persist_dir)
    if not persist_dir.exists():
        return None

    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        return None


def query_drug_rag(
    distorted_token: str,
    chan_doan_context: str,
    collection: "chromadb.Collection",
    embed_model_instance: Optional["_SentenceTransformer"] = None,
    k: int = 3,
) -> list[dict]:
    """
    Query drug RAG với distorted ASR token + diagnosis context.

    Args:
        distorted_token:     chuỗi ASR bị méo, ví dụ "glibizi", "ong lau di pin"
        chan_doan_context:   chẩn đoán context, ví dụ "đái tháo đường"
        collection:          ChromaDB collection từ build/load
        embed_model_instance: reuse để tránh load lại (optional)
        k:                   số candidates trả về

    Returns:
        list[dict] sorted by score descending:
          [{"inn": str, "drug_class": str, "score": float, "doc_snippet": str}]

    Ví dụ:
        query("glibizi", "đái tháo đường")       → Glipizide (sulfonylurea)
        query("ong lau di pin", "tăng huyết áp") → Amlodipine
        query("mek foc binh", "tiểu đường")      → Metformin
    """
    if not _DEPS_AVAILABLE:
        raise ImportError(
            "RAG-001 requires: pip install chromadb sentence-transformers"
        )

    if not distorted_token:
        return []

    if embed_model_instance is None:
        embed_model_instance = _SentenceTransformer(EMBED_MODEL)

    query_text = f"{distorted_token} {chan_doan_context}".strip()
    query_embedding = embed_model_instance.encode([query_text])[0].tolist()

    n = min(k, collection.count())
    if n == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )

    candidates: list[dict] = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        # ChromaDB cosine space: distance = 1 - cosine_similarity
        score = round(1.0 - distance, 4)
        candidates.append({
            "inn": results["metadatas"][0][i]["inn"],
            "drug_class": results["metadatas"][0][i]["drug_class"],
            "score": score,
            "doc_snippet": results["documents"][0][i].split("\n")[0],
        })

    return sorted(candidates, key=lambda x: x["score"], reverse=True)


def query_drug_rag_from_file(
    distorted_token: str,
    chan_doan_context: str,
    drug_db_path: str | Path = "data/reference/drug_db_v200.json",
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    k: int = 3,
) -> list[dict]:
    """
    Convenience wrapper: load vectorstore (or build on first call) → query.
    Dùng để test nhanh từ CLI hoặc pipeline.
    """
    collection = load_drug_vectorstore(persist_dir)

    if collection is None:
        with open(drug_db_path, encoding="utf-8") as f:
            drug_db = json.load(f)
        collection = build_drug_vectorstore(drug_db, persist_dir)

    return query_drug_rag(distorted_token, chan_doan_context, collection, k=k)


# ---------------------------------------------------------------------------
# CLI quick-test (python -m src.core.drug_rag)
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import sys

    if not _DEPS_AVAILABLE:
        print("Install: pip install chromadb sentence-transformers")
        sys.exit(1)

    test_queries = [
        ("glibizi", "đái tháo đường"),
        ("ong lau di pin", "tăng huyết áp"),
        ("mek foc binh", "tiểu đường type 2"),
        ("amosicilin", "viêm họng"),
        ("para xi ta mol", "sốt"),
    ]

    print("Building vectorstore from drug_db_v200.json...")
    results_all = [query_drug_rag_from_file(tok, ctx, k=3) for tok, ctx in test_queries]

    for (tok, ctx), results in zip(test_queries, results_all):
        print(f"\nQuery: '{tok}' + '{ctx}'")
        for r in results:
            print(f"  → {r['inn']} ({r['drug_class']}) score={r['score']:.4f}")
