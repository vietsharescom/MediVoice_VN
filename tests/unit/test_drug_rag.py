# tests/unit/test_drug_rag.py
# RAG-001 unit tests — FID-VN-010
# Mock chromadb + sentence-transformers (không cần install để chạy CI)

import sys
import types
from unittest.mock import MagicMock, patch, call
import pytest

# ---------------------------------------------------------------------------
# Bootstrap mock modules BEFORE importing drug_rag
# Allows CI to pass without chromadb / sentence-transformers installed
# ---------------------------------------------------------------------------

def _make_mock_chromadb():
    """Return a fake chromadb module."""
    mod = types.ModuleType("chromadb")

    # PersistentClient mock
    fake_client = MagicMock()
    fake_collection = MagicMock()
    fake_collection.count.return_value = 3
    fake_collection.query.return_value = {
        "ids": [["paracetamol", "ibuprofen", "aspirin"]],
        "documents": [
            [
                "Tên thuốc INN: Paracetamol\nNhóm thuốc: analgesic_antipyretic",
                "Tên thuốc INN: Ibuprofen\nNhóm thuốc: nsaid",
                "Tên thuốc INN: Aspirin (Acetylsalicylic acid)\nNhóm thuốc: nsaid",
            ]
        ],
        "metadatas": [
            [
                {"inn": "Paracetamol", "drug_class": "analgesic_antipyretic", "category": "Giảm đau", "otc": "true"},
                {"inn": "Ibuprofen", "drug_class": "nsaid", "category": "NSAIDs", "otc": "true"},
                {"inn": "Aspirin (Acetylsalicylic acid)", "drug_class": "nsaid", "category": "NSAIDs", "otc": "true"},
            ]
        ],
        "distances": [[0.1, 0.3, 0.5]],
    }
    fake_client.get_collection.return_value = fake_collection
    fake_client.create_collection.return_value = fake_collection
    fake_client.delete_collection.return_value = None

    mod.PersistentClient = MagicMock(return_value=fake_client)
    return mod, fake_client, fake_collection


def _make_mock_sentence_transformers():
    """Return fake sentence_transformers module."""
    mod = types.ModuleType("sentence_transformers")
    fake_model = MagicMock()
    import numpy as np
    fake_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
    mod.SentenceTransformer = MagicMock(return_value=fake_model)
    return mod, fake_model


# Patch sys.modules BEFORE importing drug_rag
_mock_chroma_mod, _mock_client, _mock_collection = _make_mock_chromadb()
_mock_st_mod, _mock_st_model = _make_mock_sentence_transformers()

sys.modules.setdefault("chromadb", _mock_chroma_mod)
sys.modules.setdefault("sentence_transformers", _mock_st_mod)

# Force reimport with mocks active
if "src.core.drug_rag" in sys.modules:
    del sys.modules["src.core.drug_rag"]

from src.core.drug_rag import (
    _build_doc,
    _doc_id,
    _build_phonetic_index,
    _fuzzy_phonetic_search,
    hybrid_query_drug,
    build_drug_vectorstore,
    load_drug_vectorstore,
    query_drug_rag,
    COLLECTION_NAME,
    DEFAULT_PERSIST_DIR,
    EMBED_MODEL,
)

# ---------------------------------------------------------------------------
# Minimal drug_db fixture
# ---------------------------------------------------------------------------

MINIMAL_DRUG_DB = {
    "by_inn": {
        "Paracetamol": {
            "inn": "Paracetamol",
            "brands": ["Panadol", "Hapacol"],
            "keywords": ["para", "hạ sốt"],
            "forms": ["viên 500mg"],
            "typical": "500mg x 3-4 lần/ngày",
            "category": "Giảm đau / Hạ sốt",
            "otc": True,
            "phonetic_variants": {
                "north": ["pa ra xe ta mol"],
                "central": ["pa ra xê ta môl"],
                "south": ["pa ra xe ta"],
            },
            "drug_class": "analgesic_antipyretic",
            "compatible_diagnoses": ["sốt", "đau đầu"],
            "dose_range": {"min": 125, "max": 4000},
        },
        "Metformin": {
            "inn": "Metformin",
            "brands": ["Glucophage"],
            "keywords": ["metformin", "glucophage"],
            "forms": ["viên 500mg", "viên 850mg"],
            "typical": "500mg x 2 lần/ngày",
            "category": "Đái tháo đường",
            "otc": False,
            "phonetic_variants": {
                "north": ["met pho min"],
                "central": ["mét pho min"],
                "south": ["mek foc binh"],
            },
            "drug_class": "biguanide",
            "compatible_diagnoses": ["đái tháo đường", "tiểu đường type 2"],
            "dose_range": {"min": 500, "max": 2550},
        },
        "Amlodipine": {
            "inn": "Amlodipine",
            "brands": ["Norvasc", "Amlor"],
            "keywords": ["amlodipine", "norvasc"],
            "forms": ["viên 5mg", "viên 10mg"],
            "typical": "5mg x 1 lần/ngày",
            "category": "Tăng huyết áp",
            "otc": False,
            "phonetic_variants": {
                "north": ["am lo di pin"],
                "central": ["am lo đi pin"],
                "south": ["ong lau di pin"],
            },
            "drug_class": "calcium_channel_blocker",
            "compatible_diagnoses": ["tăng huyết áp", "đau thắt ngực"],
        },
    }
}


# ===========================================================================
# _build_doc tests — pure function, no deps
# ===========================================================================

class TestBuildDoc:
    def test_returns_string(self):
        doc = _build_doc("Paracetamol", MINIMAL_DRUG_DB["by_inn"]["Paracetamol"])
        assert isinstance(doc, str)

    def test_contains_inn(self):
        doc = _build_doc("Paracetamol", MINIMAL_DRUG_DB["by_inn"]["Paracetamol"])
        assert "Paracetamol" in doc

    def test_contains_phonetic_north(self):
        doc = _build_doc("Paracetamol", MINIMAL_DRUG_DB["by_inn"]["Paracetamol"])
        assert "pa ra xe ta mol" in doc

    def test_contains_phonetic_south(self):
        doc = _build_doc("Metformin", MINIMAL_DRUG_DB["by_inn"]["Metformin"])
        assert "mek foc binh" in doc

    def test_contains_drug_class(self):
        doc = _build_doc("Metformin", MINIMAL_DRUG_DB["by_inn"]["Metformin"])
        assert "biguanide" in doc

    def test_contains_diagnoses(self):
        doc = _build_doc("Metformin", MINIMAL_DRUG_DB["by_inn"]["Metformin"])
        assert "đái tháo đường" in doc

    def test_contains_category(self):
        doc = _build_doc("Amlodipine", MINIMAL_DRUG_DB["by_inn"]["Amlodipine"])
        assert "Tăng huyết áp" in doc

    def test_contains_brands(self):
        doc = _build_doc("Paracetamol", MINIMAL_DRUG_DB["by_inn"]["Paracetamol"])
        assert "Panadol" in doc or "Hapacol" in doc

    def test_missing_phonetic_variants_no_crash(self):
        d = {"inn": "TestDrug", "drug_class": "test"}
        doc = _build_doc("TestDrug", d)
        assert "TestDrug" in doc

    def test_empty_drug_entry(self):
        doc = _build_doc("EmptyDrug", {})
        assert "EmptyDrug" in doc

    def test_multiline_structure(self):
        doc = _build_doc("Paracetamol", MINIMAL_DRUG_DB["by_inn"]["Paracetamol"])
        assert "\n" in doc

    def test_all_phonetic_regions_present(self):
        doc = _build_doc("Amlodipine", MINIMAL_DRUG_DB["by_inn"]["Amlodipine"])
        assert "am lo di pin" in doc     # north
        assert "am lo đi pin" in doc    # central
        assert "ong lau di pin" in doc  # south


# ===========================================================================
# _doc_id tests — pure function, no deps
# ===========================================================================

class TestDocId:
    def test_lowercase(self):
        assert _doc_id("Paracetamol") == "paracetamol"

    def test_spaces_to_underscore(self):
        assert _doc_id("Aspirin tablet") == "aspirin_tablet"

    def test_parentheses_removed(self):
        result = _doc_id("Aspirin (Acetylsalicylic acid)")
        assert "(" not in result
        assert ")" not in result

    def test_slash_to_underscore(self):
        result = _doc_id("Drug A/B")
        assert "/" not in result

    def test_simple_name(self):
        assert _doc_id("Metformin") == "metformin"


# ===========================================================================
# build_drug_vectorstore tests — mock chromadb
# ===========================================================================

class TestBuildDrugVectorstore:
    def test_returns_collection(self):
        result = build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir="/tmp/test_vs")
        assert result is not None

    def test_calls_create_collection(self, tmp_path):
        _mock_client.reset_mock()
        build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir=str(tmp_path))
        _mock_client.create_collection.assert_called()

    def test_collection_name_correct(self, tmp_path):
        _mock_client.reset_mock()
        build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir=str(tmp_path))
        call_args = _mock_client.create_collection.call_args
        assert call_args[1].get("name") == COLLECTION_NAME or \
               (call_args[0] and call_args[0][0] == COLLECTION_NAME)

    def test_empty_drug_db_raises(self, tmp_path):
        with pytest.raises(ValueError, match="by_inn"):
            build_drug_vectorstore({"by_inn": {}}, persist_dir=str(tmp_path))

    def test_missing_by_inn_raises(self, tmp_path):
        with pytest.raises(ValueError):
            build_drug_vectorstore({}, persist_dir=str(tmp_path))

    def test_adds_all_drugs(self, tmp_path):
        _mock_collection.reset_mock()
        build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir=str(tmp_path))
        add_args = _mock_collection.add.call_args
        assert add_args is not None
        ids = add_args[1].get("ids") or add_args[0][0]
        assert len(ids) == len(MINIMAL_DRUG_DB["by_inn"])

    def test_metadata_otc_field(self, tmp_path):
        _mock_collection.reset_mock()
        build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir=str(tmp_path))
        add_kwargs = _mock_collection.add.call_args[1]
        metadatas = add_kwargs.get("metadatas", [])
        assert any("otc" in m for m in metadatas)

    def test_persist_dir_created(self, tmp_path):
        new_dir = tmp_path / "new_vectorstore"
        assert not new_dir.exists()
        build_drug_vectorstore(MINIMAL_DRUG_DB, persist_dir=str(new_dir))
        assert new_dir.exists()


# ===========================================================================
# load_drug_vectorstore tests — mock chromadb
# ===========================================================================

class TestLoadDrugVectorstore:
    def test_returns_none_if_dir_missing(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist"
        result = load_drug_vectorstore(persist_dir=str(nonexistent))
        assert result is None

    def test_returns_collection_if_exists(self, tmp_path):
        # Create the dir so load attempts to open it
        (tmp_path / "chroma.sqlite3").touch()
        result = load_drug_vectorstore(persist_dir=str(tmp_path))
        assert result is not None

    def test_returns_none_on_get_collection_exception(self, tmp_path):
        (tmp_path / "chroma.sqlite3").touch()
        _mock_client.get_collection.side_effect = Exception("collection not found")
        result = load_drug_vectorstore(persist_dir=str(tmp_path))
        assert result is None
        _mock_client.get_collection.side_effect = None  # reset
        _mock_client.get_collection.return_value = _mock_collection


# ===========================================================================
# query_drug_rag tests — mock collection
# ===========================================================================

class TestQueryDrugRag:
    def setup_method(self):
        """Reset mock to default behavior before each test."""
        _mock_collection.reset_mock()
        import numpy as np
        _mock_st_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        _mock_collection.count.return_value = 3
        _mock_collection.query.return_value = {
            "ids": [["paracetamol", "metformin", "amlodipine"]],
            "documents": [
                [
                    "Tên thuốc INN: Paracetamol\nNhóm thuốc: analgesic_antipyretic",
                    "Tên thuốc INN: Metformin\nNhóm thuốc: biguanide",
                    "Tên thuốc INN: Amlodipine\nNhóm thuốc: calcium_channel_blocker",
                ]
            ],
            "metadatas": [
                [
                    {"inn": "Paracetamol", "drug_class": "analgesic_antipyretic", "category": "Giảm đau", "otc": "true"},
                    {"inn": "Metformin", "drug_class": "biguanide", "category": "Đái tháo đường", "otc": "false"},
                    {"inn": "Amlodipine", "drug_class": "calcium_channel_blocker", "category": "Tăng huyết áp", "otc": "false"},
                ]
            ],
            "distances": [[0.05, 0.2, 0.4]],
        }

    def test_returns_list(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        assert isinstance(results, list)

    def test_returns_k_results(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model, k=3)
        assert len(results) == 3

    def test_result_has_inn_field(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        assert all("inn" in r for r in results)

    def test_result_has_score_field(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        assert all("score" in r for r in results)

    def test_result_has_drug_class_field(self):
        results = query_drug_rag("mek foc binh", "tiểu đường", _mock_collection, _mock_st_model)
        assert all("drug_class" in r for r in results)

    def test_result_has_doc_snippet(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        assert all("doc_snippet" in r for r in results)

    def test_scores_sorted_descending(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_score_is_1_minus_distance(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        # distances=[0.05, 0.2, 0.4] → scores=[0.95, 0.80, 0.60] after sort
        assert results[0]["score"] == pytest.approx(0.95, abs=0.001)

    def test_empty_token_returns_empty(self):
        results = query_drug_rag("", "đái tháo đường", _mock_collection, _mock_st_model)
        assert results == []

    def test_empty_context_still_works(self):
        results = query_drug_rag("metformin", "", _mock_collection, _mock_st_model)
        assert isinstance(results, list)

    def test_k_equals_1(self):
        _mock_collection.count.return_value = 1
        _mock_collection.query.return_value = {
            "ids": [["metformin"]],
            "documents": [["Tên thuốc INN: Metformin\nNhóm thuốc: biguanide"]],
            "metadatas": [[{"inn": "Metformin", "drug_class": "biguanide", "category": "Đái tháo đường", "otc": "false"}]],
            "distances": [[0.1]],
        }
        results = query_drug_rag("metformin", "", _mock_collection, _mock_st_model, k=1)
        assert len(results) == 1

    def test_empty_collection_returns_empty(self):
        _mock_collection.count.return_value = 0
        results = query_drug_rag("test", "context", _mock_collection, _mock_st_model)
        assert results == []

    def test_doc_snippet_is_inn_line(self):
        results = query_drug_rag("para", "sốt", _mock_collection, _mock_st_model)
        # doc_snippet = first line of document = "Tên thuốc INN: <name>"
        assert results[0]["doc_snippet"].startswith("Tên thuốc INN:")

    def test_query_combines_token_and_context(self):
        query_drug_rag("ong lau di pin", "tăng huyết áp", _mock_collection, _mock_st_model)
        encode_args = _mock_st_model.encode.call_args[0][0]
        assert "ong lau di pin" in encode_args[0]
        assert "tăng huyết áp" in encode_args[0]

    def test_k_capped_by_collection_count(self):
        _mock_collection.count.return_value = 2
        _mock_collection.query.return_value = {
            "ids": [["paracetamol", "metformin"]],
            "documents": [["Tên thuốc INN: Paracetamol\n", "Tên thuốc INN: Metformin\n"]],
            "metadatas": [
                [
                    {"inn": "Paracetamol", "drug_class": "analgesic_antipyretic", "category": "", "otc": "true"},
                    {"inn": "Metformin", "drug_class": "biguanide", "category": "", "otc": "false"},
                ]
            ],
            "distances": [[0.1, 0.3]],
        }
        results = query_drug_rag("test", "context", _mock_collection, _mock_st_model, k=10)
        assert len(results) == 2


# ===========================================================================
# _build_phonetic_index tests
# ===========================================================================

class TestBuildPhoneticIndex:
    def test_returns_list(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        assert isinstance(idx, list)

    def test_contains_inn_entries(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        inns = {e[0] for e in idx}
        assert "Paracetamol" in inns
        assert "Metformin" in inns
        assert "Amlodipine" in inns

    def test_contains_phonetic_variants(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        variants = {e[1] for e in idx}
        assert "mek foc binh" in variants  # Metformin south phonetic
        assert "ong lau di pin" in variants  # Amlodipine south phonetic

    def test_contains_brands(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        variants = {e[1] for e in idx}
        assert "Panadol" in variants
        assert "Norvasc" in variants

    def test_contains_keywords(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        variants = {e[1] for e in idx}
        assert "para" in variants
        assert "hạ sốt" in variants

    def test_tuple_structure(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        for entry in idx:
            assert len(entry) == 3  # (inn, variant, drug_class)

    def test_drug_class_preserved(self):
        idx = _build_phonetic_index(MINIMAL_DRUG_DB)
        metformin_entries = [(inn, v, dc) for inn, v, dc in idx if inn == "Metformin"]
        assert all(dc == "biguanide" for _, _, dc in metformin_entries)

    def test_empty_db_returns_empty(self):
        idx = _build_phonetic_index({"by_inn": {}})
        assert idx == []

    def test_no_by_inn_returns_empty(self):
        idx = _build_phonetic_index({})
        assert idx == []


# ===========================================================================
# _fuzzy_phonetic_search tests
# ===========================================================================

class TestFuzzyPhoneticSearch:
    def setup_method(self):
        self.idx = _build_phonetic_index(MINIMAL_DRUG_DB)

    def test_returns_list(self):
        results = _fuzzy_phonetic_search("para", self.idx)
        assert isinstance(results, list)

    def test_paracetamol_from_variant(self):
        results = _fuzzy_phonetic_search("pa ra xe ta mol", self.idx)
        inns = [r["inn"] for r in results]
        assert "Paracetamol" in inns

    def test_metformin_from_south_phonetic(self):
        # "mek foc binh" is exact south phonetic for Metformin — should rank #1
        results = _fuzzy_phonetic_search("mek foc binh", self.idx)
        assert results
        assert results[0]["inn"] == "Metformin"

    def test_amlodipine_from_south_phonetic(self):
        results = _fuzzy_phonetic_search("ong lau di pin", self.idx)
        inns = [r["inn"] for r in results]
        assert "Amlodipine" in inns

    def test_result_has_required_fields(self):
        results = _fuzzy_phonetic_search("para", self.idx)
        if results:
            r = results[0]
            assert "inn" in r
            assert "score" in r
            assert "drug_class" in r

    def test_score_between_0_and_1(self):
        results = _fuzzy_phonetic_search("paracetamol", self.idx)
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_sorted_descending(self):
        results = _fuzzy_phonetic_search("metformin", self.idx)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_respected(self):
        results = _fuzzy_phonetic_search("para", self.idx, top_n=1)
        assert len(results) <= 1

    def test_empty_token_returns_empty(self):
        results = _fuzzy_phonetic_search("", self.idx)
        assert results == []

    def test_no_match_below_cutoff_returns_empty(self):
        results = _fuzzy_phonetic_search("xyzxyzxyz999", self.idx)
        assert results == []

    def test_deduplication_by_inn(self):
        # Multiple variants for same drug → each INN appears only once
        results = _fuzzy_phonetic_search("pa ra", self.idx)
        inns = [r["inn"] for r in results]
        assert len(inns) == len(set(inns))


# ===========================================================================
# hybrid_query_drug tests
# ===========================================================================

class TestHybridQueryDrug:
    def setup_method(self):
        _mock_collection.count.return_value = 3
        _mock_collection.query.return_value = {
            "ids": [["paracetamol", "metformin", "amlodipine"]],
            "documents": [[
                "Tên thuốc INN: Paracetamol\n",
                "Tên thuốc INN: Metformin\n",
                "Tên thuốc INN: Amlodipine\n",
            ]],
            "metadatas": [[
                {"inn": "Paracetamol", "drug_class": "analgesic_antipyretic", "category": "", "otc": "true"},
                {"inn": "Metformin", "drug_class": "biguanide", "category": "", "otc": "false"},
                {"inn": "Amlodipine", "drug_class": "calcium_channel_blocker", "category": "", "otc": "false"},
            ]],
            "distances": [[0.1, 0.4, 0.5]],
        }

    def test_returns_list(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert isinstance(r, list)

    def test_empty_token_returns_empty(self):
        r = hybrid_query_drug("", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert r == []

    def test_k_limits_results(self):
        r = hybrid_query_drug("paracetamol", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model, k=1)
        assert len(r) <= 1

    def test_result_has_score_field(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert all("score" in item for item in r)

    def test_result_has_fuzzy_score_field(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert all("fuzzy_score" in item for item in r)

    def test_result_has_rag_score_field(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert all("rag_score" in item for item in r)

    def test_sorted_descending(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        scores = [item["score"] for item in r]
        assert scores == sorted(scores, reverse=True)

    def test_metformin_south_phonetic_ranked(self):
        # "mek foc binh" → fuzzy should strongly match Metformin
        r = hybrid_query_drug("mek foc binh", "tiểu đường", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        inns = [item["inn"] for item in r]
        assert "Metformin" in inns

    def test_amlodipine_south_phonetic_ranked(self):
        r = hybrid_query_drug("ong lau di pin", "tăng huyết áp", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        inns = [item["inn"] for item in r]
        assert "Amlodipine" in inns

    def test_score_is_weighted_combination(self):
        r = hybrid_query_drug("mek foc binh", "tiểu đường", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        for item in r:
            expected = round(0.65 * item["fuzzy_score"] + 0.35 * item["rag_score"], 4)
            assert abs(item["score"] - expected) < 1e-3

    def test_custom_weights(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model,
                              fuzzy_weight=1.0, rag_weight=0.0)
        for item in r:
            assert abs(item["score"] - item["fuzzy_score"]) < 1e-4

    def test_null_collection_still_uses_fuzzy(self):
        r = hybrid_query_drug("mek foc binh", "", None, MINIMAL_DRUG_DB, _mock_st_model)
        inns = [item["inn"] for item in r]
        assert "Metformin" in inns

    def test_result_has_inn_field(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert all("inn" in item for item in r)

    def test_result_has_drug_class_field(self):
        r = hybrid_query_drug("para", "", _mock_collection, MINIMAL_DRUG_DB, _mock_st_model)
        assert all("drug_class" in item for item in r)


# ===========================================================================
# Constants / module-level checks
# ===========================================================================

class TestModuleConstants:
    def test_embed_model_name(self):
        assert "MiniLM" in EMBED_MODEL or "multilingual" in EMBED_MODEL

    def test_collection_name(self):
        assert "drug" in COLLECTION_NAME.lower() or "v200" in COLLECTION_NAME

    def test_default_persist_dir_under_data(self):
        assert "drug_vectorstore" in str(DEFAULT_PERSIST_DIR)
