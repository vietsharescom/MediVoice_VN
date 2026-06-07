#!/usr/bin/env python
# scripts/generate_drug_eval_dataset.py
# Generate evaluation dataset for DrugCorrectionEngine v2 [CONS-002-EVAL]
# Output: data/eval/drug_correction_eval.json
# Coverage: 3 categories × 4 subcategories = ~200 cases
#
# Run: python -X utf8 scripts/generate_drug_eval_dataset.py

import json
import sys
from pathlib import Path

OUT = Path("data/eval/drug_correction_eval.json")

# ─── SEED DATA ────────────────────────────────────────────────────────────────
# (inn, alias_in_transcript, dose_mg, freq_per_day, days)
# dose_mg is the "correct" dose used in CLEAN / NOISY cases (within valid range)

CLEAN_INN = [
    # Exact INN name — Layer 1 tests
    ("Metformin",          "metformin",        500,  2, 30),
    ("Amlodipine",         "amlodipine",         5,  1, 30),
    ("Paracetamol",        "paracetamol",       500,  3,  5),
    ("Amoxicillin",        "amoxicillin",       500,  3,  7),
    ("Omeprazole",         "omeprazole",         20,  1, 14),
    ("Ibuprofen",          "ibuprofen",         400,  3,  5),
    ("Atorvastatin",       "atorvastatin",       20,  1, 30),
    ("Losartan",           "losartan",           50,  1, 30),
    ("Metronidazole",      "metronidazole",     250,  3,  7),
    ("Metoprolol",         "metoprolol",         50,  1, 30),
    ("Furosemide",         "furosemide",         40,  1, 14),
    ("Glimepiride",        "glimepiride",         2,  1, 30),
    ("Cetirizine",         "cetirizine",         10,  1,  7),
    ("Prednisolone",       "prednisolone",        5,  2,  7),
    ("Azithromycin",       "azithromycin",      500,  1,  3),
    ("Clarithromycin",     "clarithromycin",    500,  2,  7),
    ("Ciprofloxacin",      "ciprofloxacin",     500,  2,  7),
    ("Levofloxacin",       "levofloxacin",      500,  1,  7),
    ("Amoxicillin/Clavulanate", "augmentin",    625,  3,  7),
    ("Salbutamol",         "salbutamol",          4,  3,  7),
    ("Loratadine",         "loratadine",         10,  1,  7),
    ("Valsartan",          "valsartan",          80,  1, 30),
    ("Esomeprazole",       "esomeprazole",       40,  1, 14),
    ("Domperidone",        "domperidone",        10,  3,  7),
    ("Dexamethasone injection", "dexamethasone",    4,  1,  5),
]

CLEAN_BRAND = [
    # Brand name → INN mapping (Layer 1 alias tests)
    ("Paracetamol",   "panadol",     500, 3,  5),
    ("Paracetamol",   "efferalgan",  500, 3,  5),
    ("Ibuprofen",     "advil",       400, 3,  5),
    ("Ibuprofen",     "nurofen",     400, 3,  5),
    ("Amlodipine",    "norvasc",       5, 1, 30),
    ("Omeprazole",    "losec",        20, 1, 14),
    ("Omeprazole",    "prilosec",     20, 1, 14),
    ("Metformin",     "glucophage",  500, 2, 30),
    ("Atorvastatin",  "lipitor",      20, 1, 30),
    ("Losartan",      "cozaar",       50, 1, 30),
    ("Azithromycin",  "zithromax",   500, 1,  3),
    ("Cetirizine",    "zyrtec",       10, 1,  7),
    ("Loratadine",    "claritin",     10, 1,  7),
    ("Metoprolol",    "betaloc",      50, 1, 30),
    ("Salbutamol",    "ventolin",      4, 3,  7),
]

CLEAN_NEGATIVE = [
    # No drug mentioned — expect zero predictions (FP check)
    "bệnh nhân 45 tuổi tái khám tăng huyết áp.",
    "đo huyết áp 130/80 mmHg, mạch 80 lần/phút.",
    "bệnh nhân khỏe mạnh, không có triệu chứng gì.",
    "lý do khám: kiểm tra sức khỏe định kỳ.",
    "tiền sử gia đình có bố bị tiểu đường.",
    "bệnh nhân phủ nhận dị ứng thuốc.",
    "hẹn tái khám sau 2 tuần nếu không đỡ.",
    "kết quả xét nghiệm máu bình thường.",
    "bệnh nhân ngưng tự ý dùng thuốc cũ.",
    "chẩn đoán viêm họng cấp, không kê thuốc.",
    "bệnh nhân được giải thích về lối sống lành mạnh.",
    "cần kiểm tra lại sau 1 tháng.",
    "theo dõi thêm, chưa cần dùng thuốc.",
    "bệnh nhân đang cho con bú, cần thận trọng.",
    "chuyển viện để làm thêm xét nghiệm chuyên sâu.",
]

# ─── NOISY CATEGORY ──────────────────────────────────────────────────────────
# (inn, phonetic_transcript, dose_mg, region)

NOISY_NORTH = [
    ("Amlodipine",    "am lô đi pin",         5),
    ("Amlodipine",    "am lô đi pinh",        5),
    ("Amoxicillin",   "a mốc xi lin",       500),
    ("Amoxicillin",   "a mô xi lin",        500),
    ("Metformin",     "mét pho min",        500),
    ("Metformin",     "me pho min",         500),
    ("Paracetamol",   "pa ra xe ta mol",    500),
    ("Paracetamol",   "pa ra xê ta mol",    500),
    ("Omeprazole",    "ô me pra zôl",        20),
    ("Omeprazole",    "ô mê pra zol",        20),
    ("Ibuprofen",     "i bu pho phen",      400),
    ("Ibuprofen",     "i bu pro phen",      400),
    ("Azithromycin",  "a zi thro my xin",   500),
    ("Metronidazole", "me tro ni đa zôl",   250),
    ("Atorvastatin",  "a to va sta tin",     20),
    ("Losartan",      "lo sar tan",          50),
    ("Metoprolol",    "me to pro lol",       50),
    ("Furosemide",    "phu ro se mit",       40),
    ("Glimepiride",   "gli me pi rit",        2),
    ("Cetirizine",    "xe ti ri zin",        10),
    ("Loratadine",    "lo ra ta đin",        10),
    ("Prednisolone",  "prét ni so lon",       5),
    ("Esomeprazole",  "e so me pra zôl",     40),
    ("Domperidone",   "dom pe ri đon",       10),
    ("Salbutamol",    "xan bu ta mol",        4),
]

NOISY_SOUTH = [
    ("Amlodipine",    "am lo",              5),
    ("Amlodipine",    "am lor",             5),
    ("Amoxicillin",   "a moc xi lin",     500),
    ("Amoxicillin",   "a moc si lin",     500),
    ("Metformin",     "me pho min",       500),
    ("Metformin",     "mờ pho min",       500),
    ("Paracetamol",   "pa ra",            500),
    ("Paracetamol",   "pa ra xe ta",      500),
    ("Omeprazole",    "o me pra",          20),
    ("Omeprazole",    "o me",              20),
    ("Ibuprofen",     "i bu pro",         400),
    ("Azithromycin",  "a zi tro my",      500),
    ("Metronidazole", "me tro ni",        250),
    ("Atorvastatin",  "a to va",           20),
    ("Losartan",      "lo sa",             50),
    ("Metoprolol",    "be ta loc",         50),
    ("Furosemide",    "phu ro",            40),
    ("Glimepiride",   "gli me pi",          2),
    ("Glimepiride",   "a ma ryl",           2),
    ("Cetirizine",    "xe ti ri",          10),
    ("Loratadine",    "lo ra ta",          10),
    ("Prednisolone",  "prét ni",            5),
    ("Esomeprazole",  "ne xi um",          40),
    ("Domperidone",   "dom pe",            10),
    ("Salbutamol",    "ven to lin",         4),
]

NOISY_FUZZY = [
    # ASR typos and mishears (Layer 2 fuzzy tests)
    ("Amlodipine",    "amlodiphin",         5),
    ("Amlodipine",    "amlodipine",         5),
    ("Metformin",     "metphomin",        500),
    ("Metformin",     "metfornin",        500),
    ("Paracetamol",   "parasetamol",      500),
    ("Paracetamol",   "paracetamole",     500),
    ("Amoxicillin",   "amoxicilline",     500),
    ("Omeprazole",    "omeprazol",         20),
    ("Ibuprofen",     "ibuprophen",       400),
    ("Azithromycin",  "azithromicin",     500),
    ("Atorvastatin",  "atorvaxtatine",     20),
    ("Losartan",      "loxartan",          50),
    ("Metronidazole", "metronidazol",     250),
]

# ─── DANGEROUS CATEGORY ──────────────────────────────────────────────────────

DANGEROUS_LOW_DOSE = [
    # Doses below drug_db_v200 dose_range.min → expect DOSE_OUT_OF_RANGE HIGH
    ("Metformin",     10,    500, 3000, "DOSE_OUT_OF_RANGE"),   # min=500
    ("Metformin",     100,   500, 3000, "DOSE_OUT_OF_RANGE"),   # min=500
    ("Furosemide",     5,    20,  600,  "DOSE_OUT_OF_RANGE"),   # min=20
    ("Glimepiride",  0.1,    1,   8,    "DOSE_OUT_OF_RANGE"),   # min=1 (extreme)
    ("Ibuprofen",     50,   200, 3200,  "DOSE_OUT_OF_RANGE"),   # min=200
    ("Prednisolone",  0.5,   1,  60,    "DOSE_OUT_OF_RANGE"),   # min=1
    ("Azithromycin",  50,   250, 1500,  "DOSE_OUT_OF_RANGE"),   # min=250
    ("Metronidazole", 50,   250, 4000,  "DOSE_OUT_OF_RANGE"),   # min=250
]

DANGEROUS_HIGH_DOSE = [
    # Doses above dose_range.max → expect DOSE_OUT_OF_RANGE HIGH
    ("Amlodipine",    50,  2.5,   10,  "DOSE_OUT_OF_RANGE"),   # max=10
    ("Amlodipine",    20,  2.5,   10,  "DOSE_OUT_OF_RANGE"),   # max=10
    ("Atorvastatin", 100,   10,   80,  "DOSE_OUT_OF_RANGE"),   # max=80
    ("Metoprolol",   500,   25,  400,  "DOSE_OUT_OF_RANGE"),   # max=400
    ("Glimepiride",   10,    1,    8,  "DOSE_OUT_OF_RANGE"),   # max=8
    ("Prednisolone",  80,    1,   60,  "DOSE_OUT_OF_RANGE"),   # max=60
    ("Cetirizine",    40,    5,   20,  "DOSE_OUT_OF_RANGE"),   # max=20
    ("Loratadine",    30,   10,   20,  "DOSE_OUT_OF_RANGE"),   # max=20
]

DANGEROUS_AMBIGUOUS = [
    # Short/ambiguous names → expect AMBIGUOUS flag
    ("met",        ["Metformin", "Metoprolol", "Metronidazole"], "AMBIGUOUS"),
    ("metro",      ["Metronidazole", "Metoprolol"],               "AMBIGUOUS"),
    ("me tro",     ["Metronidazole", "Metoprolol"],               "AMBIGUOUS"),
]


# ─── BUILD CASES ─────────────────────────────────────────────────────────────

def build_cases() -> list[dict]:
    cases = []
    idx = 1

    def add(category: str, subcategory: str, transcript: str,
            expected_drugs: list, expected_flags: list,
            is_negative: bool = False, notes: str = "") -> None:
        nonlocal idx
        cases.append({
            "id": f"CE-{idx:03d}",
            "category": category,
            "subcategory": subcategory,
            "transcript": transcript,
            "expected_drugs": expected_drugs,
            "expected_flags": expected_flags,
            "is_negative": is_negative,
            "notes": notes,
        })
        idx += 1

    # CLEAN — INN exact match (2 templates per drug)
    templates_clean = [
        "kê {alias} {dose}mg ngày {freq} lần trong {days} ngày",
        "cho bệnh nhân uống {alias} {dose}mg ngày {freq} lần",
        "bệnh nhân dùng {alias} {dose}mg mỗi ngày",
        "điều trị bằng {alias} {dose}mg ngày {freq} lần trong {days} ngày",
    ]
    for i, (inn, alias, dose, freq, days) in enumerate(CLEAN_INN):
        for j in range(2):  # 2 template variants per drug
            tmpl = templates_clean[(i + j) % len(templates_clean)]
            t = tmpl.format(alias=alias, dose=dose, freq=freq, days=days)
            add("clean", "exact_inn", t,
                [{"inn": inn, "dose_mg": dose}], [])

    # CLEAN — brand name
    for inn, brand, dose, freq, days in CLEAN_BRAND:
        t = f"kê {brand} {dose}mg ngày {freq} lần"
        add("clean", "brand_name", t,
            [{"inn": inn, "dose_mg": dose}], [])

    # CLEAN — multi-drug (2-3 drugs)
    multi_pairs = [
        (("Metformin", "metformin", 500), ("Amlodipine", "amlodipine", 5)),
        (("Paracetamol", "paracetamol", 500), ("Ibuprofen", "ibuprofen", 400)),
        (("Omeprazole", "omeprazole", 20), ("Amoxicillin", "amoxicillin", 500)),
        (("Atorvastatin", "atorvastatin", 20), ("Losartan", "losartan", 50), ("Amlodipine", "amlodipine", 5)),
        (("Metformin", "metformin", 500), ("Glimepiride", "glimepiride", 2)),
        (("Metoprolol", "metoprolol", 50), ("Losartan", "losartan", 50)),
        (("Cetirizine", "cetirizine", 10), ("Salbutamol", "salbutamol", 4)),
        (("Prednisolone", "prednisolone", 5), ("Azithromycin", "azithromycin", 500)),
        (("Omeprazole", "omeprazole", 20), ("Domperidone", "domperidone", 10)),
        (("Furosemide", "furosemide", 40), ("Valsartan", "valsartan", 80), ("Metoprolol", "metoprolol", 50)),
    ]
    for combo in multi_pairs:
        parts = [f"{a} {d}mg" for _, a, d in combo]
        t = "kê " + " và ".join(parts) + " cho bệnh nhân"
        expected = [{"inn": inn, "dose_mg": d} for inn, _, d in combo]
        add("clean", "multi_drug", t, expected, [])

    # CLEAN — negative (no drug)
    for neg_t in CLEAN_NEGATIVE:
        add("clean", "negative", neg_t, [], [], is_negative=True)

    # NOISY — north phonetic
    for inn, phonetic, dose in NOISY_NORTH:
        t = f"kê {phonetic} {dose}mg ngày 1 lần"
        add("noisy", "phonetic_north", t,
            [{"inn": inn, "dose_mg": dose}], [],
            notes=f"north phonetic for {inn}")

    # NOISY — south phonetic
    for inn, phonetic, dose in NOISY_SOUTH:
        t = f"cho bệnh nhân dùng {phonetic} {dose}mg mỗi ngày"
        add("noisy", "phonetic_south", t,
            [{"inn": inn, "dose_mg": dose}], [],
            notes=f"south phonetic for {inn}")

    # NOISY — fuzzy/typo (2 templates each)
    fuzzy_templates = [
        "kê {typo} {dose}mg",
        "bệnh nhân uống {typo} {dose}mg ngày 2 lần",
    ]
    for i, (inn, typo, dose) in enumerate(NOISY_FUZZY):
        for j in range(2):
            t = fuzzy_templates[j].format(typo=typo, dose=dose)
            add("noisy", "fuzzy_typo", t,
                [{"inn": inn, "dose_mg": dose}], [],
                notes=f"typo variant of {inn}")

    # DANGEROUS — dose too low (2 transcript templates each)
    low_templates = [
        "kê {inn} {dose}mg ngày 2 lần",
        "bệnh nhân uống {inn} {dose}mg mỗi ngày",
    ]
    for i, (inn, dose, min_d, max_d, flag) in enumerate(DANGEROUS_LOW_DOSE):
        for j in range(2):
            t = low_templates[j].format(inn=inn.lower(), dose=dose)
            add("dangerous", "dose_too_low", t,
                [{"inn": inn, "dose_mg": dose}],
                [flag],
                notes=f"dose {dose}mg below min {min_d}mg")

    # DANGEROUS — dose too high (2 templates each)
    high_templates = [
        "kê {inn} {dose}mg ngày 1 lần",
        "cho bệnh nhân uống {inn} {dose}mg",
    ]
    for i, (inn, dose, min_d, max_d, flag) in enumerate(DANGEROUS_HIGH_DOSE):
        for j in range(2):
            t = high_templates[j].format(inn=inn.lower(), dose=dose)
            add("dangerous", "dose_too_high", t,
                [{"inn": inn, "dose_mg": dose}],
                [flag],
                notes=f"dose {dose}mg above max {max_d}mg")

    # DANGEROUS — ambiguous (2 templates each)
    amb_templates = [
        "uống {name} 500mg ngày 2 lần",
        "kê {name} ngày 1 lần",
    ]
    for short_name, possible_inns, flag in DANGEROUS_AMBIGUOUS:
        for j in range(2):
            t = amb_templates[j].format(name=short_name)
            add("dangerous", "ambiguous", t,
                [],
                [flag],
                notes=f"'{short_name}' ambiguous among {possible_inns}")

    return cases


def main() -> None:
    cases = build_cases()
    by_cat: dict[str, int] = {}
    for c in cases:
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1

    dataset = {
        "_meta": {
            "name": "MediVoice Drug Correction Eval Dataset",
            "version": "1.0.0",
            "created": "2026-06-10",
            "total": len(cases),
            "categories": by_cat,
            "purpose": "CONS-002-EVAL — Evaluation dataset for DrugCorrectionEngine v2",
            "metrics": [
                "Drug Recall (INN recognition)",
                "False Positive Rate (no-drug transcripts)",
                "Safety Catch Rate (dangerous doses + ambiguous)",
                "Phonetic Recall (noisy category only)",
            ],
        },
        "cases": cases,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(cases)} cases → {OUT}")
    for cat, cnt in by_cat.items():
        print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    main()
