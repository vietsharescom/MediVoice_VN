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


def _build_phonetic_index(drug_db: dict) -> list[tuple[str, str, str]]:
    """
    Build flat list: [(inn, variant_text, drug_class), ...]
    Covers: INN name, all phonetic_variants regions, keywords, brands.
    Used by fuzzy phonetic search as complement to RAG semantic search.
    """
    index: list[tuple[str, str, str]] = []
    for inn, d in drug_db.get("by_inn", {}).items():
        drug_class = d.get("drug_class", "")
        index.append((inn, inn, drug_class))
        for brand in d.get("brands", []):
            index.append((inn, brand, drug_class))
        for kw in d.get("keywords", []):
            index.append((inn, kw, drug_class))
        for region_variants in d.get("phonetic_variants", {}).values():
            for v in region_variants:
                index.append((inn, v, drug_class))
    return index


def _fuzzy_phonetic_search(
    token: str,
    index: list[tuple[str, str, str]],
    top_n: int = 6,
) -> list[dict]:
    """
    RapidFuzz token_set_ratio search on phonetic index.
    Returns [{inn, drug_class, score}] sorted desc.
    """
    from rapidfuzz import process as rf_process, fuzz

    variants = [entry[1] for entry in index]
    raw = rf_process.extract(
        token, variants, limit=top_n * 3, score_cutoff=25, scorer=fuzz.token_set_ratio
    )

    inn_best: dict[str, dict] = {}
    for _match, score, idx in raw:
        inn, _, drug_class = index[idx]
        norm = score / 100.0
        if inn not in inn_best or inn_best[inn]["score"] < norm:
            inn_best[inn] = {
                "inn": inn,
                "drug_class": drug_class,
                "score": norm,
                "doc_snippet": f"Tên thuốc INN: {inn}",
            }
    return sorted(inn_best.values(), key=lambda x: x["score"], reverse=True)[:top_n]


def hybrid_query_drug(
    distorted_token: str,
    chan_doan_context: str,
    collection: "chromadb.Collection",
    drug_db: dict,
    embed_model_instance=None,
    k: int = 3,
    fuzzy_weight: float = 0.65,
    rag_weight: float = 0.35,
) -> list[dict]:
    """
    Hybrid drug search: fuzzy phonetic (65%) + RAG semantic (35%).

    Fixes RC-A (MiniLM not phonetic) and RC-C (missing phonetic variants)
    identified in RAG-001 quality review 2026-06-09.

    Args:
        distorted_token:      chuỗi ASR bị méo, ví dụ "glibizi", "mek foc binh"
        chan_doan_context:     chẩn đoán context
        collection:           ChromaDB collection
        drug_db:              drug_db dict (by_inn) để build phonetic index
        embed_model_instance: reuse để tránh load lại
        k:                    số candidates trả về
        fuzzy_weight:         trọng số fuzzy phonetic (0.65 default)
        rag_weight:           trọng số RAG semantic (0.35 default)

    Returns:
        list[dict] sorted by combined score desc:
          [{inn, drug_class, score, fuzzy_score, rag_score, doc_snippet}]
    """
    if not distorted_token:
        return []

    index = _build_phonetic_index(drug_db)
    fuzzy_results = _fuzzy_phonetic_search(distorted_token, index, top_n=k * 2)

    rag_results: list[dict] = []
    if _DEPS_AVAILABLE and collection is not None:
        rag_results = query_drug_rag(
            distorted_token, chan_doan_context, collection,
            embed_model_instance=embed_model_instance, k=k * 2,
        )

    merged: dict[str, dict] = {}

    for r in fuzzy_results:
        merged[r["inn"]] = {
            "inn": r["inn"],
            "drug_class": r["drug_class"],
            "fuzzy_score": r["score"],
            "rag_score": 0.0,
            "doc_snippet": r["doc_snippet"],
        }

    for r in rag_results:
        inn = r["inn"]
        if inn in merged:
            merged[inn]["rag_score"] = r["score"]
        else:
            merged[inn] = {
                "inn": inn,
                "drug_class": r["drug_class"],
                "fuzzy_score": 0.0,
                "rag_score": r["score"],
                "doc_snippet": r["doc_snippet"],
            }

    for data in merged.values():
        data["score"] = round(
            fuzzy_weight * data["fuzzy_score"] + rag_weight * data["rag_score"],
            4,
        )

    return sorted(merged.values(), key=lambda x: x["score"], reverse=True)[:k]


def hybrid_query_drug_from_file(
    distorted_token: str,
    chan_doan_context: str,
    drug_db_path: str | Path = "data/reference/drug_db_v200.json",
    persist_dir: str | Path = DEFAULT_PERSIST_DIR,
    k: int = 3,
    fuzzy_weight: float = 0.65,
    rag_weight: float = 0.35,
) -> list[dict]:
    """
    Convenience wrapper for hybrid query: load drug_db + vectorstore → hybrid query.
    """
    with open(drug_db_path, encoding="utf-8") as f:
        drug_db = json.load(f)

    collection = load_drug_vectorstore(persist_dir)
    if collection is None:
        collection = build_drug_vectorstore(drug_db, persist_dir)

    return hybrid_query_drug(
        distorted_token, chan_doan_context, collection, drug_db,
        k=k, fuzzy_weight=fuzzy_weight, rag_weight=rag_weight,
    )


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

    _db_path = "data/reference/drug_db_v200.json"
    print("=== RAG-only ===")
    results_rag = [query_drug_rag_from_file(tok, ctx, k=3) for tok, ctx in test_queries]
    for (tok, ctx), results in zip(test_queries, results_rag):
        print(f"\nQuery: '{tok}' + '{ctx}'")
        for r in results:
            print(f"  → {r['inn']} score={r['score']:.4f}")

    print("\n=== Hybrid (fuzzy 65% + RAG 35%) ===")
    results_h = [hybrid_query_drug_from_file(tok, ctx, drug_db_path=_db_path, k=3) for tok, ctx in test_queries]
    for (tok, ctx), results in zip(test_queries, results_h):
        print(f"\nQuery: '{tok}' + '{ctx}'")
        for r in results:
            print(f"  → {r['inn']} score={r['score']:.4f} (f={r['fuzzy_score']:.2f} r={r['rag_score']:.2f})")
