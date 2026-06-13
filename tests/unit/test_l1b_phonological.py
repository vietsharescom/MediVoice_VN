# tests/unit/test_l1b_phonological.py
# Tests for _phonological_variants() + _add_phon_alias() [FID-VN-019, CT-042]
# Vietnamese-English contrastive phonology — see fids/FID-VN-019.md WHY

from src.core.l1b_drug_correct import _phonological_variants, _add_phon_alias


class TestAspirationSwap:
    def test_phon_variants_b_p_swap(self):
        assert "pa tin" in _phonological_variants("ba tin")
        assert "ba tin" in _phonological_variants("pa tin")

    def test_phon_variants_d_t_swap(self):
        assert "ta tin" in _phonological_variants("da tin")
        assert "da tin" in _phonological_variants("ta tin")

    def test_phon_variants_g_k_c_swap(self):
        assert "ka tin" in _phonological_variants("ga tin")
        assert "ka tin" in _phonological_variants("ca tin")
        variants_from_k = _phonological_variants("ka tin")
        assert "ga tin" in variants_from_k
        assert "ca tin" in variants_from_k


class TestCodaRestriction:
    def test_phon_variants_coda_drop_multisyllable(self):
        # "me tro ni đa zol" (5 syllables) → drop final "l" of "zol"
        assert "me tro ni đa zo" in _phonological_variants("me tro ni đa zol")

    def test_phon_variants_coda_drop_single_syllable_skipped(self):
        # CONSTRAINT 1 (v3): single-syllable alias → no standalone coda-drop key
        assert _phonological_variants("zol") == set()

    def test_phon_variants_coda_keep_valid(self):
        # "n" is a valid Vietnamese coda — no rubbed/dropped variant
        assert "ti xa" not in _phonological_variants("tin xa")
        assert "mi xa" not in _phonological_variants("min xa")
        assert "pi xa" not in _phonological_variants("pin xa")


class TestThToTD:
    def test_phon_variants_th_to_t_d(self):
        variants = _phonological_variants("theo xa")
        assert "teo xa" in variants
        assert "deo xa" in variants


class TestRLNSwap:
    def test_phon_variants_r_l_n_swap_north(self):
        north_variants = _phonological_variants("no xa", region="north")
        assert "lo xa" in north_variants
        # "r" onset rules must NOT apply for north
        assert _phonological_variants("ro xa", region="north") == set()

    def test_phon_variants_r_l_n_swap_south(self):
        south_variants = _phonological_variants("ro xa", region="south")
        assert "lo xa" in south_variants
        assert "zo xa" in south_variants
        # l/n swap must NOT apply for south
        assert _phonological_variants("no xa", region="south") == set()


class TestLimitsAndGuards:
    def test_phon_variants_limit_2_syllables(self):
        # 5-syllable alias — only first ("ba") and last ("pol") may change
        variants = _phonological_variants("ba tro ni go pol")
        for variant in variants:
            tokens = variant.split(" ")
            assert tokens[1:4] == ["tro", "ni", "go"]
        assert "pa tro ni go pol" in variants

    def test_phon_variants_min_length_filter(self):
        # single-syllable alias "ka" → swapped variants "ga"/"ca" are <3 chars
        assert _phonological_variants("ka") == set()

    def test_alias_map_collision_skipped(self):
        alias_map = {"foo bar": "DrugA"}
        _add_phon_alias(alias_map, "foo bar", "DrugB")
        assert alias_map["foo bar"] == "DrugA"
        _add_phon_alias(alias_map, "new key", "DrugB")
        assert alias_map["new key"] == "DrugB"

    def test_phon_variants_blacklist_skipped(self):
        # "ko xa" → rule1 (k→c) would produce "co xa", but "co" (có) is blacklisted
        variants = _phonological_variants("ko xa")
        assert "co xa" not in variants
        assert "go xa" in variants
