# src/models/clinical_kb.py
# Clinical Knowledge Base — FAISS vector store for Vietnamese medical guidelines
# FID: MV-FID-019
# Version: v1.0

import json
import logging
import os
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

GUIDELINES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "kb", "guidelines.json"
)
FAISS_INDEX_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "kb", "faiss_index.bin"
)
CHUNKS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "kb", "chunks.json"
)
EMBEDDING_MODEL = "keepitreal/vietnamese-sbert"
EMBEDDING_FALLBACK = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


class ClinicalKB:
    """
    FAISS-backed clinical knowledge base.

    Usage:
        kb = ClinicalKB()
        kb.load()          # load index from disk
        chunks = kb.query("viêm màng não sốt co giật", top_k=3)
    """

    def __init__(self):
        self._index = None
        self._chunks: List[dict] = []
        self._embedder = None
        self._loaded = False

    def load(self) -> bool:
        """Load FAISS index + chunks from disk. Auto-builds from chunks.json if index missing."""
        if self._loaded:
            return True
        try:
            import faiss

            if not os.path.exists(CHUNKS_PATH):
                logger.warning("chunks.json not found at %s — KB disabled.", CHUNKS_PATH)
                return False

            if not os.path.exists(FAISS_INDEX_PATH):
                logger.info("FAISS index not found — building from chunks.json...")
                if not self._build_from_chunks():
                    return False

            self._index = faiss.read_index(FAISS_INDEX_PATH)
            with open(CHUNKS_PATH, encoding="utf-8") as f:
                self._chunks = json.load(f)
            self._embedder = self._load_embedder()
            self._loaded = True
            logger.info("ClinicalKB loaded: %d chunks, FAISS dim=%d",
                        len(self._chunks), self._index.d)
            return True
        except ImportError:
            logger.warning("faiss-cpu not installed — KB disabled. pip install faiss-cpu")
            return False
        except Exception as exc:
            logger.error("ClinicalKB load failed: %s", exc)
            return False

    def _build_from_chunks(self) -> bool:
        """Build FAISS index from chunks.json and save to disk."""
        try:
            import faiss
            import numpy as np

            embedder = self._load_embedder()
            if embedder is None:
                logger.error("Cannot build FAISS index — embedder unavailable.")
                return False

            with open(CHUNKS_PATH, encoding="utf-8") as f:
                chunks = json.load(f)

            texts = [c["content"] for c in chunks]
            logger.info("Embedding %d chunks for FAISS build...", len(texts))
            embeddings = embedder.encode(texts, normalize_embeddings=True)
            embeddings = np.array(embeddings, dtype="float32")

            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)

            os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
            faiss.write_index(index, FAISS_INDEX_PATH)
            logger.info("FAISS index built and saved: %d vectors, dim=%d", index.ntotal, dim)
            return True
        except Exception as exc:
            logger.error("FAISS auto-build failed: %s", exc)
            return False

    def query(self, query_text: str, top_k: int = 3) -> List[str]:
        """Return top_k relevant guideline chunks for query_text."""
        if not self._loaded or self._index is None or not self._embedder:
            return []
        try:
            import numpy as np
            vec = self._embedder.encode([query_text], normalize_embeddings=True)
            vec = np.array(vec, dtype="float32")
            distances, indices = self._index.search(vec, top_k)
            results = []
            for idx in indices[0]:
                if 0 <= idx < len(self._chunks):
                    results.append(self._chunks[idx]["content"])
            return results
        except Exception as exc:
            logger.error("ClinicalKB.query failed: %s", exc)
            return []

    def _load_embedder(self):
        """Load sentence embedding model (VI-SBERT or multilingual fallback)."""
        try:
            from sentence_transformers import SentenceTransformer
            try:
                model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info("Embedding model: %s", EMBEDDING_MODEL)
                return model
            except Exception:
                model = SentenceTransformer(EMBEDDING_FALLBACK)
                logger.info("Embedding model (fallback): %s", EMBEDDING_FALLBACK)
                return model
        except ImportError:
            logger.warning("sentence-transformers not installed — KB disabled")
            return None


# Module-level singleton
_kb_instance: Optional[ClinicalKB] = None


def get_clinical_kb() -> ClinicalKB:
    """Return singleton ClinicalKB, loading on first call."""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = ClinicalKB()
        _kb_instance.load()
    return _kb_instance
