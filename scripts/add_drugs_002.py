#!/usr/bin/env python3
"""
scripts/add_drugs_002.py — DRUG-DB-002
Add 8 high-priority missing drugs to drug_db_v200.json.
Missing: Erythromycin, Aluminium phosphate, Betamethasone, Clindamycin,
         Lisinopril, Digoxin, Nystatin, Ketoconazole

Run once: python -X utf8 scripts/add_drugs_002.py
"""
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "reference" / "drug_db_v200.json"

NEW_DRUGS = {
    "Erythromycin": {
        "inn": "Erythromycin",
        "brands": ["Erythromycin", "E-mycin", "Ery-tab", "Ilosone", "Erythro",
                   "ê ri tho my xin", "e ri thro", "ery tho my"],
        "forms": ["viên 250mg", "viên 500mg", "siro 200mg/5mL"],
        "typical": "500mg x 4 lần/ngày x 5-7 ngày",
        "category": "Kháng sinh Macrolide",
        "otc": False,
        "keywords": ["erythromycin", "e-mycin", "ery-tab", "ilosone", "macrolide"],
        "phonetic_variants": {
            "north": ["ê ri thơ my xin", "ê ri tho my xin", "ê ri thơ mi xin"],
            "central": ["e ri thro mi cin", "ê ri thơ mi cin", "ê ri tro mi xin"],
            "south": ["ê ri tho my cin", "ê ri tho my", "e ri tho mi cin"]
        },
        "valid_doses_mg": [250, 500],
        "dose_range": {"min": 250, "max": 4000},
        "drug_class": "macrolide",
        "compatible_diagnoses": ["viêm họng", "viêm phổi nhẹ", "nhiễm trùng da", "viêm phế quản"]
    },
    "Aluminium phosphate": {
        "inn": "Aluminium phosphate",
        "brands": ["Phosphalugel", "Nhôm phosphate", "Phophalugel sachets",
                   "phot pha lu gen", "phos pha lu", "nhom phot phat"],
        "forms": ["gói 8g/20mL"],
        "typical": "1 gói x 2-3 lần/ngày sau bữa ăn",
        "category": "Bảo vệ niêm mạc dạ dày",
        "otc": True,
        "keywords": ["phosphalugel", "nhôm phosphate", "antacid", "nhom phot phat",
                     "phos pha lu gen"],
        "phonetic_variants": {
            "north": ["phot pha lu gen", "nhôm phot phat", "a lu mi ni phot phat"],
            "central": ["phot pha lu gen", "nhom phot phat", "phot pha lu"],
            "south": ["phot pha lu gen", "phot pha luc", "nhom phot fa"]
        },
        "valid_doses_mg": [8000],
        "dose_range": {"min": 0, "max": 0},
        "drug_class": "antacid",
        "compatible_diagnoses": ["đau dạ dày", "trào ngược dạ dày", "viêm dạ dày",
                                  "loét dạ dày"]
    },
    "Betamethasone": {
        "inn": "Betamethasone",
        "brands": ["Celestone", "Betnovate", "Diprospan", "Betaderm", "Bethasone",
                   "bê ta met", "bê ta me ta"],
        "forms": ["viên 0.5mg", "kem 0.05%", "tiêm 4mg/mL"],
        "typical": "0.5-1mg/ngày uống",
        "category": "Corticosteroid",
        "otc": False,
        "keywords": ["betamethasone", "betnovate", "celestone", "diprospan",
                     "corticoid"],
        "phonetic_variants": {
            "north": ["bê ta me tha son", "bê ta met a son", "bê ta me ta xon"],
            "central": ["bê ta me tha xon", "bê ta mê tha son", "bê ta me ta"],
            "south": ["bê ta mê ta son", "bê ta met", "bê ta me tha"]
        },
        "valid_doses_mg": [0.5, 1, 2, 4],
        "dose_range": {"min": 0.25, "max": 8},
        "drug_class": "corticosteroid",
        "compatible_diagnoses": ["viêm da", "dị ứng", "viêm khớp", "viêm phế quản"]
    },
    "Clindamycin": {
        "inn": "Clindamycin",
        "brands": ["Dalacin C", "Cleocin", "Clindacin", "Clindamycin",
                   "klin đa my", "clin đa my xin"],
        "forms": ["viên 150mg", "viên 300mg", "kem 1%"],
        "typical": "300mg x 4 lần/ngày x 7 ngày",
        "category": "Kháng sinh Lincosamide",
        "otc": False,
        "keywords": ["clindamycin", "dalacin", "cleocin", "lincosamide"],
        "phonetic_variants": {
            "north": ["klin đa my xin", "clin đa my xin", "klin đa mi xin"],
            "central": ["clin đa mi cin", "klin đa mi cin", "clin đa my"],
            "south": ["klin đa mi cin", "clin đa mi", "klin da my xin"]
        },
        "valid_doses_mg": [150, 300, 450, 600],
        "dose_range": {"min": 150, "max": 4800},
        "drug_class": "lincosamide",
        "compatible_diagnoses": ["nhiễm trùng da", "nhiễm trùng răng", "viêm phổi",
                                  "áp xe"]
    },
    "Lisinopril": {
        "inn": "Lisinopril",
        "brands": ["Zestril", "Prinivil", "Lisinopril", "Lisiprol",
                   "li xi no pril", "li si nô prin"],
        "forms": ["viên 5mg", "viên 10mg", "viên 20mg"],
        "typical": "10mg x 1 lần/ngày",
        "category": "Hạ áp ACE inhibitor",
        "otc": False,
        "keywords": ["lisinopril", "zestril", "prinivil", "ace inhibitor"],
        "phonetic_variants": {
            "north": ["li xi nô pơ rin", "li si nô prin", "li xi no pril"],
            "central": ["li xi no pril", "li si no pril", "li xi nô prin"],
            "south": ["li si no prin", "li xi no prin", "li si no prit"]
        },
        "valid_doses_mg": [2.5, 5, 10, 20, 40],
        "dose_range": {"min": 2.5, "max": 80},
        "drug_class": "ace_inhibitor",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim", "bệnh thận tiểu đường"]
    },
    "Digoxin": {
        "inn": "Digoxin",
        "brands": ["Lanoxin", "Digoxin", "di goc xin", "đi gốc"],
        "forms": ["viên 0.0625mg", "viên 0.125mg", "viên 0.25mg",
                  "tiêm 0.5mg/2mL"],
        "typical": "0.125-0.25mg/ngày",
        "category": "Tim mạch glycoside",
        "otc": False,
        "keywords": ["digoxin", "lanoxin", "glycoside", "tim"],
        "phonetic_variants": {
            "north": ["đi gôc xin", "đi goc xin", "di goc sin"],
            "central": ["đi goc xin", "di goc sin", "đi goc"],
            "south": ["đi gốc xin", "đi gốc", "di goc xin"]
        },
        "valid_doses_mg": [0.0625, 0.125, 0.25, 0.5],
        "dose_range": {"min": 0.0625, "max": 0.5},
        "drug_class": "cardiac_glycoside",
        "compatible_diagnoses": ["suy tim", "rung nhĩ", "nhịp tim nhanh"]
    },
    "Nystatin": {
        "inn": "Nystatin",
        "brands": ["Mycostatin", "Nilstat", "Nystatin", "Nystat",
                   "ny xta tin", "ni xta"],
        "forms": ["viên 500000 IU", "hỗn dịch 100000 IU/mL", "kem 100000 IU/g"],
        "typical": "500000 IU x 4 lần/ngày x 5-7 ngày",
        "category": "Chống nấm Polyene",
        "otc": True,
        "keywords": ["nystatin", "mycostatin", "candida", "nấm"],
        "phonetic_variants": {
            "north": ["ny xta tin", "ni xta tin", "ny xta tinh"],
            "central": ["ni xta tin", "ny xta", "ni xta tinh"],
            "south": ["ny xta tin", "nì xta tin", "ni xta"]
        },
        "valid_doses_mg": [500000, 1000000],
        "dose_range": {"min": 100000, "max": 4000000},
        "drug_class": "polyene_antifungal",
        "compatible_diagnoses": ["nhiễm nấm miệng", "nhiễm nấm âm đạo",
                                  "nhiễm nấm da"]
    },
    "Ketoconazole": {
        "inn": "Ketoconazole",
        "brands": ["Nizoral", "Ketomed", "Ketoconazole",
                   "kê to co na zon", "ni do ral", "kê to con"],
        "forms": ["viên 200mg", "dầu gội 2%", "kem 2%"],
        "typical": "200-400mg/ngày uống",
        "category": "Chống nấm Azole toàn thân",
        "otc": False,
        "keywords": ["ketoconazole", "nizoral", "ketomed", "azole", "nấm"],
        "phonetic_variants": {
            "north": ["kê to co na zol", "kê to co na dôn", "kê to con a zon"],
            "central": ["kê to co na zon", "kê to co na zol", "kê to cô na"],
            "south": ["kê to co na zon", "ni do ral", "kê to co na"]
        },
        "valid_doses_mg": [200, 400],
        "dose_range": {"min": 200, "max": 400},
        "drug_class": "azole_antifungal",
        "compatible_diagnoses": ["nhiễm nấm da", "nấm tóc", "nấm móng",
                                  "viêm da tiết bã"]
    }
}


def main():
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))

    added = 0
    skipped = 0
    for inn, entry in NEW_DRUGS.items():
        if inn in db["by_inn"]:
            print(f"  SKIP (exists): {inn}")
            skipped += 1
            continue
        db["by_inn"][inn] = entry
        # Update keyword_index
        for kw in entry.get("keywords", []):
            db["keyword_index"].setdefault(kw, inn)
        for brand in entry.get("brands", []):
            db["keyword_index"].setdefault(brand.lower(), inn)
        # Update category count
        cat = entry.get("category", "Other")
        db["_meta"]["categories"][cat] = db["_meta"]["categories"].get(cat, 0) + 1
        print(f"  ADDED: {inn}")
        added += 1

    db["_meta"]["total_drugs"] = len(db["by_inn"])
    db["_meta"]["sources_used"].append(
        "DRUG-DB-002: Erythromycin/AluminiumPhosphate/Betamethasone/Clindamycin/"
        "Lisinopril/Digoxin/Nystatin/Ketoconazole (2026-06-09)"
    )

    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone: +{added} drugs, {skipped} skipped. Total: {db['_meta']['total_drugs']}")


if __name__ == "__main__":
    main()
