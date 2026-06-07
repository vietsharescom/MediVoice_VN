#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/build_drug_db_v200.py
Build drug_db_v200.json from drug_db.json (v0.3.0)

Adds per-drug:
  - phonetic_variants: {north, central, south}  ← CONS-20260610-001 Approach C
  - valid_doses_mg: []
  - dose_range: {min, max}
  - drug_class: str
  - compatible_diagnoses: []

New drugs added (~30): SGLT-2, DPP-4 additions, ARBs, CCBs, new PPIs,
  antacids, beta-blockers, neuropathy, psychiatry, antibiotics

Phoneme rules (CONS-20260610-001, R1–R7):
  R1 Consonant cluster → insert /ơ/: "str"→"xtơ", "cl"→"cờ lơ"
  R2 Final -ine/-pine → north:-pin, central:-phin, south:drop
  R3 /r/ → north:/z/, south:/ɣ/, central:varies
  R4 Vowel shift Trung: ô→o, ê→e, ă→e
  R5 /f/ → /ph/
  R6 Tone neutralization (fast speech)
  R7 Southern abbreviation: drop final 2-3 syllables

Usage:
  python -X utf8 scripts/build_drug_db_v200.py
  → writes data/reference/drug_db_v200.json
"""

import json
import copy
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
SRC  = ROOT / "data" / "reference" / "drug_db.json"
DST  = ROOT / "data" / "reference" / "drug_db_v200.json"

# ─── MANUAL phonetic_variants for top 40 clinical drugs ─────────────────────
# Format: "INN" → {north:[], central:[], south:[], valid_doses_mg:[], dose_range, drug_class, compatible_diagnoses}
TOP_MANUAL = {
    "Paracetamol": {
        "phonetic_variants": {
            "north":   ["pa ra xe ta mol", "pa ra xê ta mol"],
            "central": ["pa ra xe ta mol", "pa ra xê ta môl", "pa ra xê ta"],
            "south":   ["pa ra", "pa ra xe ta", "pa ra xe ta mol"],
        },
        "valid_doses_mg": [125, 250, 325, 500, 650, 1000],
        "dose_range": {"min": 125, "max": 4000},
        "drug_class": "analgesic_antipyretic",
        "compatible_diagnoses": ["sốt", "đau đầu", "đau cơ", "cảm cúm"],
    },
    "Ibuprofen": {
        "phonetic_variants": {
            "north":   ["i bu pho phen", "i bu pro phen"],
            "central": ["i bu pho phen", "i bu pro phen"],
            "south":   ["i bu pro", "i bu pro phen"],
        },
        "valid_doses_mg": [200, 400, 600, 800],
        "dose_range": {"min": 200, "max": 3200},
        "drug_class": "nsaid",
        "compatible_diagnoses": ["đau", "viêm khớp", "sốt"],
    },
    "Amoxicillin": {
        "phonetic_variants": {
            "north":   ["a mốc xi lin", "a mô xi lin", "a mô xi xinh"],
            "central": ["a móc xi lin", "a moc xi ling", "a moc xi lin"],
            "south":   ["a moc xi lin", "a moc si lin", "ô mô xi lin"],
        },
        "valid_doses_mg": [125, 250, 500, 875, 1000],
        "dose_range": {"min": 125, "max": 3000},
        "drug_class": "penicillin",
        "compatible_diagnoses": ["viêm họng", "viêm phổi", "nhiễm trùng tai", "viêm xoang"],
    },
    "Amoxicillin/Clavulanate": {
        "phonetic_variants": {
            "north":   ["ô gờ men tin", "au gờ men tin", "ô gờ men tin"],
            "central": ["ô gờ men tin", "o go men tin"],
            "south":   ["ô gờ men tin", "an xi lin", "anh xi lin"],
        },
        "valid_doses_mg": [375, 625, 1000],
        "dose_range": {"min": 375, "max": 4000},
        "drug_class": "penicillin_beta_lactamase_inhibitor",
        "compatible_diagnoses": ["viêm phổi", "viêm xoang", "nhiễm trùng"],
    },
    "Azithromycin": {
        "phonetic_variants": {
            "north":   ["a zi thro my xin", "a zi tro my xin"],
            "central": ["a zi tro my xin", "a zi tro my xinh"],
            "south":   ["a zi tro my", "a zi tro", "a zi tro my xin"],
        },
        "valid_doses_mg": [250, 500],
        "dose_range": {"min": 250, "max": 1500},
        "drug_class": "macrolide",
        "compatible_diagnoses": ["viêm phổi", "viêm họng", "nhiễm trùng hô hấp"],
    },
    "Clarithromycin": {
        "phonetic_variants": {
            "north":   ["cla ri thro my xin", "kla ri tro my xin"],
            "central": ["cla ri tro my xin", "cla ri tro my xinh"],
            "south":   ["cla ri tro my", "kla ri tro", "cla ri thro"],
        },
        "valid_doses_mg": [250, 500],
        "dose_range": {"min": 250, "max": 2000},
        "drug_class": "macrolide",
        "compatible_diagnoses": ["viêm phổi", "loét dạ dày H.pylori"],
    },
    "Ciprofloxacin": {
        "phonetic_variants": {
            "north":   ["xi pro phlo xa xin", "xi pro phlo xa xinh"],
            "central": ["xi pro phloc xa xin", "xi pro phlo xa xin"],
            "south":   ["xi pro phlo", "xi pro", "xi pro phlo xa"],
        },
        "valid_doses_mg": [250, 500, 750],
        "dose_range": {"min": 250, "max": 3000},
        "drug_class": "quinolone",
        "compatible_diagnoses": ["nhiễm trùng tiết niệu", "viêm phổi"],
    },
    "Levofloxacin": {
        "phonetic_variants": {
            "north":   ["le vo phlo xa xin", "lê vo phlo xa xin"],
            "central": ["le vo phloc xa xin", "le vo phlo xa xin"],
            "south":   ["le vo phlo", "le vo", "le vo phlo xa"],
        },
        "valid_doses_mg": [250, 500, 750],
        "dose_range": {"min": 250, "max": 1500},
        "drug_class": "quinolone",
        "compatible_diagnoses": ["viêm phổi", "viêm xoang", "nhiễm trùng tiết niệu"],
    },
    "Metronidazole": {
        "phonetic_variants": {
            "north":   ["me tro ni đa zôl", "me trô ni da zol"],
            "central": ["me tro ni đa zol", "me tro ni da zon"],
            "south":   ["me tro ni", "me tro", "me tro ni đa"],
        },
        "valid_doses_mg": [250, 400, 500],
        "dose_range": {"min": 250, "max": 4000},
        "drug_class": "nitroimidazole",
        "compatible_diagnoses": ["nhiễm trùng kỵ khí", "loét dạ dày H.pylori"],
    },
    "Amlodipine": {
        "phonetic_variants": {
            "north":   ["am lô đi pin", "am lô đi pinh"],
            "central": ["am lô đi phin", "am lô đi pin"],
            "south":   ["am lo", "am lor", "a mờ lo", "am lô"],
        },
        "valid_doses_mg": [2.5, 5, 10],
        "dose_range": {"min": 2.5, "max": 10},
        "drug_class": "calcium_channel_blocker",
        "compatible_diagnoses": ["tăng huyết áp", "đau thắt ngực"],
    },
    "Losartan": {
        "phonetic_variants": {
            "north":   ["lo sar tan", "lo xa tan", "lô xa tan"],
            "central": ["lo sa tan", "lo sa tăn", "lo sar tan"],
            "south":   ["lo sa", "lo sa tan", "lô za tan"],
        },
        "valid_doses_mg": [25, 50, 100],
        "dose_range": {"min": 25, "max": 150},
        "drug_class": "arb",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim", "bệnh thận đái tháo đường"],
    },
    "Valsartan": {
        "phonetic_variants": {
            "north":   ["van sa tan", "van xa tan"],
            "central": ["van sa tan", "val sa tan"],
            "south":   ["van sa", "val sa tan"],
        },
        "valid_doses_mg": [40, 80, 160, 320],
        "dose_range": {"min": 40, "max": 320},
        "drug_class": "arb",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim"],
    },
    "Bisoprolol": {
        "phonetic_variants": {
            "north":   ["bi so pro lol", "bi xo pro lol"],
            "central": ["bi so pro lol", "bi so pro lon"],
            "south":   ["bi so pro", "bi so", "bi xo pro"],
        },
        "valid_doses_mg": [1.25, 2.5, 5, 10],
        "dose_range": {"min": 1.25, "max": 20},
        "drug_class": "beta_blocker",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim", "rối loạn nhịp"],
    },
    "Atenolol": {
        "phonetic_variants": {
            "north":   ["a te no lol", "a tê nô lôl"],
            "central": ["a te no lol", "a tê no lon"],
            "south":   ["a te no", "a tê nô"],
        },
        "valid_doses_mg": [25, 50, 100],
        "dose_range": {"min": 25, "max": 200},
        "drug_class": "beta_blocker",
        "compatible_diagnoses": ["tăng huyết áp", "đau thắt ngực"],
    },
    "Enalapril": {
        "phonetic_variants": {
            "north":   ["e na la pril", "ê na la pril"],
            "central": ["e na la pril", "ê na la pril"],
            "south":   ["e na la", "e na la pril"],
        },
        "valid_doses_mg": [2.5, 5, 10, 20],
        "dose_range": {"min": 2.5, "max": 40},
        "drug_class": "ace_inhibitor",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim"],
    },
    "Perindopril": {
        "phonetic_variants": {
            "north":   ["pe rin đo pril", "pe rin do pril"],
            "central": ["pe rin đo pril", "pe rin do pril"],
            "south":   ["pe rin đo", "pe rin do pril"],
        },
        "valid_doses_mg": [2, 4, 8, 10],
        "dose_range": {"min": 2, "max": 10},
        "drug_class": "ace_inhibitor",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim"],
    },
    "Atorvastatin": {
        "phonetic_variants": {
            "north":   ["a to va sta tin", "a to va xta tin"],
            "central": ["a to va sta tinh", "a to va xta tinh"],
            "south":   ["a to va", "a to va sta", "a to va sta tin"],
        },
        "valid_doses_mg": [10, 20, 40, 80],
        "dose_range": {"min": 10, "max": 80},
        "drug_class": "statin",
        "compatible_diagnoses": ["rối loạn lipid máu", "phòng ngừa tim mạch"],
    },
    "Rosuvastatin": {
        "phonetic_variants": {
            "north":   ["ro su va sta tin", "rô xu va xta tin"],
            "central": ["ro su va sta tinh", "ro xu va xta tinh"],
            "south":   ["ro su va", "ro su va sta", "cờ re xto"],
        },
        "valid_doses_mg": [5, 10, 20, 40],
        "dose_range": {"min": 5, "max": 40},
        "drug_class": "statin",
        "compatible_diagnoses": ["rối loạn lipid máu", "phòng ngừa tim mạch"],
    },
    "Simvastatin": {
        "phonetic_variants": {
            "north":   ["xim va sta tin", "sim va xta tin"],
            "central": ["xim va sta tinh", "sim va xta tinh"],
            "south":   ["xim va", "xim va sta"],
        },
        "valid_doses_mg": [5, 10, 20, 40, 80],
        "dose_range": {"min": 5, "max": 80},
        "drug_class": "statin",
        "compatible_diagnoses": ["rối loạn lipid máu"],
    },
    "Metformin": {
        "phonetic_variants": {
            "north":   ["mét pho min", "me pho min", "met pho min"],
            "central": ["mét pho min", "mét pho miên", "me pho miên"],
            "south":   ["me pho min", "mờ pho min", "mét pho"],
        },
        "valid_doses_mg": [500, 850, 1000],
        "dose_range": {"min": 500, "max": 3000},
        "drug_class": "biguanide",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    "Glimepiride": {
        "phonetic_variants": {
            "north":   ["gli me pi rit", "gli me pi ride"],
            "central": ["gli me pi rit", "gli mê pi rit"],
            "south":   ["gli me pi", "a ma ryl", "gli me"],
        },
        "valid_doses_mg": [1, 2, 3, 4],
        "dose_range": {"min": 1, "max": 8},
        "drug_class": "sulfonylurea",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    "Gliclazide": {
        "phonetic_variants": {
            "north":   ["gli cla zit", "gli cla ziđ"],
            "central": ["gli cla zit", "gli kla zit"],
            "south":   ["gli cla", "gli cla zit"],
        },
        "valid_doses_mg": [30, 60, 80],
        "dose_range": {"min": 30, "max": 240},
        "drug_class": "sulfonylurea",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    "Sitagliptin": {
        "phonetic_variants": {
            "north":   ["xi ta glip tin", "si ta glip tin"],
            "central": ["xi ta glip tinh", "si ta glip tin"],
            "south":   ["xi ta glip", "si ta glip", "gia nuvi a"],
        },
        "valid_doses_mg": [25, 50, 100],
        "dose_range": {"min": 25, "max": 100},
        "drug_class": "dpp4_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    "Omeprazole": {
        "phonetic_variants": {
            "north":   ["ô me pra zôl", "ô mê pra zol", "o me pra zol"],
            "central": ["ô me pra zol", "o me pra zol"],
            "south":   ["o me pra", "o me", "ô me pra zôl"],
        },
        "valid_doses_mg": [10, 20, 40],
        "dose_range": {"min": 10, "max": 80},
        "drug_class": "ppi",
        "compatible_diagnoses": ["loét dạ dày", "trào ngược dạ dày thực quản"],
    },
    "Esomeprazole": {
        "phonetic_variants": {
            "north":   ["e so me pra zôl", "ne xi um"],
            "central": ["e so me pra zol", "nê xi um"],
            "south":   ["e so me pra", "ne xi um", "nê xum"],
        },
        "valid_doses_mg": [20, 40],
        "dose_range": {"min": 20, "max": 80},
        "drug_class": "ppi",
        "compatible_diagnoses": ["loét dạ dày", "trào ngược dạ dày thực quản"],
    },
    "Pantoprazole": {
        "phonetic_variants": {
            "north":   ["pan to pra zôl", "pan tô pra zol"],
            "central": ["pan to pra zol", "pan tô pra zol"],
            "south":   ["pan to pra", "pan to"],
        },
        "valid_doses_mg": [20, 40],
        "dose_range": {"min": 20, "max": 80},
        "drug_class": "ppi",
        "compatible_diagnoses": ["loét dạ dày", "trào ngược dạ dày thực quản"],
    },
    "Domperidone": {
        "phonetic_variants": {
            "north":   ["dom pe ri đon", "đom pe ri đon"],
            "central": ["dom pe ri đon", "đom pe ri đon"],
            "south":   ["dom pe", "dom pe ri", "mo ti li um"],
        },
        "valid_doses_mg": [10],
        "dose_range": {"min": 10, "max": 40},
        "drug_class": "prokinetic",
        "compatible_diagnoses": ["buồn nôn", "đầy hơi", "khó tiêu"],
    },
    "Cetirizine": {
        "phonetic_variants": {
            "north":   ["xe ti ri zin", "se ti ri zin"],
            "central": ["xe ti ri zing", "xe ti ri zin"],
            "south":   ["xe ti ri", "xe ti", "xi ri zec"],
        },
        "valid_doses_mg": [5, 10],
        "dose_range": {"min": 5, "max": 20},
        "drug_class": "antihistamine_2nd_gen",
        "compatible_diagnoses": ["dị ứng", "mề đay", "viêm mũi dị ứng"],
    },
    "Loratadine": {
        "phonetic_variants": {
            "north":   ["lo ra ta đin", "lo ra ta din"],
            "central": ["lo ra ta đin", "lo ra ta din"],
            "south":   ["lo ra ta", "lo ra", "cla ri tin"],
        },
        "valid_doses_mg": [10],
        "dose_range": {"min": 10, "max": 20},
        "drug_class": "antihistamine_2nd_gen",
        "compatible_diagnoses": ["dị ứng", "viêm mũi dị ứng"],
    },
    "Prednisolone": {
        "phonetic_variants": {
            "north":   ["prét ni so lon", "prét ni xô lôn"],
            "central": ["prét ni so lon", "prét ni so lôn"],
            "south":   ["prét ni", "prét ni so", "prét"],
        },
        "valid_doses_mg": [1, 5, 10, 20, 25, 30],
        "dose_range": {"min": 1, "max": 60},
        "drug_class": "corticosteroid",
        "compatible_diagnoses": ["viêm", "dị ứng nặng", "hen phế quản"],
    },
    "Furosemide": {
        "phonetic_variants": {
            "north":   ["phu ro se mit", "phu rô xê mit"],
            "central": ["phu ro se mit", "phu ro se mid"],
            "south":   ["phu ro", "phu ro se", "la xích"],
        },
        "valid_doses_mg": [20, 40, 80],
        "dose_range": {"min": 20, "max": 600},
        "drug_class": "loop_diuretic",
        "compatible_diagnoses": ["phù", "tăng huyết áp", "suy tim"],
    },
    "Salbutamol": {
        "phonetic_variants": {
            "north":   ["xan bu ta mol", "san bu ta mol"],
            "central": ["xan bu ta mol", "xal bu ta mol"],
            "south":   ["xan bu ta", "ven to lin", "xan bu"],
        },
        "valid_doses_mg": [2, 4],
        "dose_range": {"min": 2, "max": 32},
        "drug_class": "beta2_agonist",
        "compatible_diagnoses": ["hen phế quản", "co thắt phế quản"],
    },
    "Tramadol": {
        "phonetic_variants": {
            "north":   ["tra ma đol", "tra ma dol"],
            "central": ["tra ma đol", "tra ma dol"],
            "south":   ["tra ma", "tra ma đol"],
        },
        "valid_doses_mg": [50, 100, 150, 200],
        "dose_range": {"min": 50, "max": 400},
        "drug_class": "opioid_weak",
        "compatible_diagnoses": ["đau vừa đến nặng"],
    },
    "Warfarin": {
        "phonetic_variants": {
            "north":   ["oa pha rin", "wa pha rin"],
            "central": ["oa pha rin", "wa pha rin"],
            "south":   ["oa pha", "wa pha rin"],
        },
        "valid_doses_mg": [1, 2, 2.5, 3, 5],
        "dose_range": {"min": 1, "max": 10},
        "drug_class": "anticoagulant",
        "compatible_diagnoses": ["rung nhĩ", "huyết khối tĩnh mạch"],
    },
    "Clopidogrel": {
        "phonetic_variants": {
            "north":   ["clo pi đo grel", "clo pi đo grel"],
            "central": ["clo pi đo grel", "klo pi do grel"],
            "south":   ["clo pi đo", "pla vích", "clo pi"],
        },
        "valid_doses_mg": [75, 300],
        "dose_range": {"min": 75, "max": 600},
        "drug_class": "antiplatelet",
        "compatible_diagnoses": ["hội chứng vành cấp", "đột quỵ", "phòng ngừa tim mạch"],
    },
    "Gabapentin": {
        "phonetic_variants": {
            "north":   ["ga ba pen tin", "ga ba phen tin"],
            "central": ["ga ba pen tinh", "ga ba phen tin"],
            "south":   ["ga ba pen", "ga ba", "neu ron tin"],
        },
        "valid_doses_mg": [100, 300, 400, 600, 800],
        "dose_range": {"min": 100, "max": 3600},
        "drug_class": "anticonvulsant_neuropathic",
        "compatible_diagnoses": ["đau thần kinh", "động kinh"],
    },
    "Pregabalin": {
        "phonetic_variants": {
            "north":   ["pre ga ba lin", "pré ga ba lin"],
            "central": ["pre ga ba linh", "pré ga ba lin"],
            "south":   ["pre ga ba", "ly ri ca"],
        },
        "valid_doses_mg": [25, 50, 75, 100, 150, 200, 225, 300],
        "dose_range": {"min": 25, "max": 600},
        "drug_class": "anticonvulsant_neuropathic",
        "compatible_diagnoses": ["đau thần kinh", "động kinh", "rối loạn lo âu"],
    },
    "Diazepam": {
        "phonetic_variants": {
            "north":   ["đi a ze pam", "đi a ze pam"],
            "central": ["đi a ze pam", "đi a za pam"],
            "south":   ["đi a ze", "va li um"],
        },
        "valid_doses_mg": [2, 5, 10],
        "dose_range": {"min": 2, "max": 60},
        "drug_class": "benzodiazepine",
        "compatible_diagnoses": ["lo âu", "co giật", "mất ngủ"],
    },
    "Allopurinol": {
        "phonetic_variants": {
            "north":   ["a lo pu ri nol", "a lô pu ri nol"],
            "central": ["a lo pu ri nol", "a lo pu ri non"],
            "south":   ["a lo pu ri", "a lo pu", "a pu rin"],
        },
        "valid_doses_mg": [100, 200, 300],
        "dose_range": {"min": 100, "max": 900},
        "drug_class": "uric_acid_lowering",
        "compatible_diagnoses": ["gout", "tăng acid uric"],
    },
    "Colchicine": {
        "phonetic_variants": {
            "north":   ["con xi xin", "kol chi xin"],
            "central": ["con xi xinh", "kol chi xin"],
            "south":   ["con xi", "col chi xin"],
        },
        "valid_doses_mg": [0.5, 1],
        "dose_range": {"min": 0.5, "max": 6},
        "drug_class": "gout_acute",
        "compatible_diagnoses": ["gout cấp"],
    },
}

# ─── NEW DRUGS to add (DRUG-DB-002 missing + common VN clinic) ──────────────
NEW_DRUGS = [
    # SGLT-2 inhibitors — very hot in VN diabetes management
    {
        "inn": "Empagliflozin",
        "brands": ["Jardiance", "em pa gli phlo zin", "em pa gli phlô zin"],
        "forms": ["viên 10mg", "viên 25mg"],
        "typical": "10mg x 1 lần/ngày sáng; tăng 25mg nếu cần",
        "category": "Tiểu đường type 2 SGLT-2 inhibitor",
        "otc": False,
        "keywords": ["empagliflozin", "jardiance", "sglt2", "sglt-2", "em pa gli"],
        "phonetic_variants": {
            "north":   ["em pa gli phlo zin", "em pa gli phlô zin"],
            "central": ["em pa gli phlo zinh", "em pa gli phlô zin"],
            "south":   ["em pa gli phlo", "em pa gli", "gia di an"],
        },
        "valid_doses_mg": [10, 25],
        "dose_range": {"min": 10, "max": 25},
        "drug_class": "sglt2_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2", "suy tim", "bệnh thận mạn"],
    },
    {
        "inn": "Dapagliflozin",
        "brands": ["Forxiga", "da pa gli phlo zin", "dap a gli phlô"],
        "forms": ["viên 5mg", "viên 10mg"],
        "typical": "10mg x 1 lần/ngày sáng",
        "category": "Tiểu đường type 2 SGLT-2 inhibitor",
        "otc": False,
        "keywords": ["dapagliflozin", "forxiga", "sglt2", "da pa gli"],
        "phonetic_variants": {
            "north":   ["da pa gli phlo zin", "đa pa gli phlô zin"],
            "central": ["da pa gli phlo zinh", "đa pa gli phlô zin"],
            "south":   ["da pa gli phlo", "da pa gli", "pho xi ga"],
        },
        "valid_doses_mg": [5, 10],
        "dose_range": {"min": 5, "max": 10},
        "drug_class": "sglt2_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2", "suy tim", "bệnh thận mạn"],
    },
    {
        "inn": "Canagliflozin",
        "brands": ["Invokana", "ca na gli phlo zin"],
        "forms": ["viên 100mg", "viên 300mg"],
        "typical": "100mg x 1 lần/ngày trước bữa sáng; tăng 300mg nếu cần",
        "category": "Tiểu đường type 2 SGLT-2 inhibitor",
        "otc": False,
        "keywords": ["canagliflozin", "invokana", "sglt2", "ca na gli"],
        "phonetic_variants": {
            "north":   ["ca na gli phlo zin", "ka na gli phlô zin"],
            "central": ["ca na gli phlo zinh", "ka na gli phlô zin"],
            "south":   ["ca na gli phlo", "ca na gli", "in vo ca na"],
        },
        "valid_doses_mg": [100, 300],
        "dose_range": {"min": 100, "max": 300},
        "drug_class": "sglt2_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    # DPP-4 additions
    {
        "inn": "Vildagliptin",
        "brands": ["Galvus", "vil đa glip tin"],
        "forms": ["viên 50mg", "viên 50/1000mg"],
        "typical": "50mg x 2 lần/ngày (sáng tối)",
        "category": "Tiểu đường DPP-4 inhibitor",
        "otc": False,
        "keywords": ["vildagliptin", "galvus", "vil da glip", "gan vus"],
        "phonetic_variants": {
            "north":   ["vil đa glip tin", "vin đa glip tin"],
            "central": ["vil đa glip tinh", "vin đa glip tinh"],
            "south":   ["vil đa glip", "gan vus"],
        },
        "valid_doses_mg": [50],
        "dose_range": {"min": 50, "max": 100},
        "drug_class": "dpp4_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    {
        "inn": "Linagliptin",
        "brands": ["Trajenta", "li na glip tin"],
        "forms": ["viên 5mg"],
        "typical": "5mg x 1 lần/ngày",
        "category": "Tiểu đường DPP-4 inhibitor",
        "otc": False,
        "keywords": ["linagliptin", "trajenta", "li na glip"],
        "phonetic_variants": {
            "north":   ["li na glip tin", "li na glip tinh"],
            "central": ["li na glip tinh", "li na glip tin"],
            "south":   ["li na glip", "tra gen ta"],
        },
        "valid_doses_mg": [5],
        "dose_range": {"min": 5, "max": 5},
        "drug_class": "dpp4_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    {
        "inn": "Pioglitazone",
        "brands": ["Actos", "pio gli ta zon"],
        "forms": ["viên 15mg", "viên 30mg"],
        "typical": "15-30mg x 1 lần/ngày",
        "category": "Tiểu đường type 2 Thiazolidinedione",
        "otc": False,
        "keywords": ["pioglitazone", "actos", "pio gli ta", "ac tos"],
        "phonetic_variants": {
            "north":   ["pio gli ta zon", "pi ô gli ta zon"],
            "central": ["pio gli ta zon", "pi ô gli ta zon"],
            "south":   ["pio gli ta", "ac tos"],
        },
        "valid_doses_mg": [15, 30, 45],
        "dose_range": {"min": 15, "max": 45},
        "drug_class": "thiazolidinedione",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
    # New ARBs
    {
        "inn": "Telmisartan",
        "brands": ["Micardis", "tel mi sa tan"],
        "forms": ["viên 20mg", "viên 40mg", "viên 80mg"],
        "typical": "40-80mg x 1 lần/ngày",
        "category": "Hạ áp ARB",
        "otc": False,
        "keywords": ["telmisartan", "micardis", "tel mi sa tan", "mi ca dis"],
        "phonetic_variants": {
            "north":   ["tel mi sa tan", "tên mi xa tan"],
            "central": ["tel mi sa tan", "ten mi sa tan"],
            "south":   ["tel mi sa", "mi ca dis"],
        },
        "valid_doses_mg": [20, 40, 80],
        "dose_range": {"min": 20, "max": 80},
        "drug_class": "arb",
        "compatible_diagnoses": ["tăng huyết áp", "bệnh thận đái tháo đường"],
    },
    {
        "inn": "Olmesartan",
        "brands": ["Olmetec", "ol me sa tan"],
        "forms": ["viên 10mg", "viên 20mg", "viên 40mg"],
        "typical": "20-40mg x 1 lần/ngày",
        "category": "Hạ áp ARB",
        "otc": False,
        "keywords": ["olmesartan", "olmetec", "ol me sa tan", "ol me tec"],
        "phonetic_variants": {
            "north":   ["ol me sa tan", "ol mê xa tan"],
            "central": ["ol me sa tan", "ol me sa tăn"],
            "south":   ["ol me sa", "ol mê tec"],
        },
        "valid_doses_mg": [10, 20, 40],
        "dose_range": {"min": 10, "max": 40},
        "drug_class": "arb",
        "compatible_diagnoses": ["tăng huyết áp"],
    },
    {
        "inn": "Irbesartan",
        "brands": ["Aprovel", "ir be sa tan"],
        "forms": ["viên 75mg", "viên 150mg", "viên 300mg"],
        "typical": "150mg x 1 lần/ngày",
        "category": "Hạ áp ARB",
        "otc": False,
        "keywords": ["irbesartan", "aprovel", "ir be sa tan", "a pro vel"],
        "phonetic_variants": {
            "north":   ["ir be sa tan", "ir bê xa tan"],
            "central": ["ir be sa tan", "ir be sa tăn"],
            "south":   ["ir be sa", "a pro vel"],
        },
        "valid_doses_mg": [75, 150, 300],
        "dose_range": {"min": 75, "max": 300},
        "drug_class": "arb",
        "compatible_diagnoses": ["tăng huyết áp", "bệnh thận đái tháo đường"],
    },
    # New CCBs
    {
        "inn": "Nifedipine",
        "brands": ["Adalat", "ni phe đi pin"],
        "forms": ["viên 10mg", "viên phóng thích chậm 20mg", "viên phóng thích chậm 30mg"],
        "typical": "30-60mg x 1 lần/ngày (XL); 10mg x 3 lần/ngày (thường)",
        "category": "Hạ áp Calcium antagonist",
        "otc": False,
        "keywords": ["nifedipine", "adalat", "ni phe đi pin", "a da lat"],
        "phonetic_variants": {
            "north":   ["ni phe đi pin", "ni phê đi pin"],
            "central": ["ni phe đi phin", "ni phê đi phin"],
            "south":   ["ni phe đi", "a da lat"],
        },
        "valid_doses_mg": [10, 20, 30, 60],
        "dose_range": {"min": 10, "max": 120},
        "drug_class": "calcium_channel_blocker",
        "compatible_diagnoses": ["tăng huyết áp", "đau thắt ngực"],
    },
    {
        "inn": "Lercanidipine",
        "brands": ["Zanidip", "le ca ni đi pin"],
        "forms": ["viên 10mg", "viên 20mg"],
        "typical": "10-20mg x 1 lần/ngày trước ăn",
        "category": "Hạ áp Calcium antagonist",
        "otc": False,
        "keywords": ["lercanidipine", "zanidip", "le ca ni đi pin", "za ni đip"],
        "phonetic_variants": {
            "north":   ["le ca ni đi pin", "le ca ni đi pinh"],
            "central": ["le ca ni đi phin", "le ca ni đi pin"],
            "south":   ["le ca ni đi", "za ni đip"],
        },
        "valid_doses_mg": [10, 20],
        "dose_range": {"min": 10, "max": 20},
        "drug_class": "calcium_channel_blocker",
        "compatible_diagnoses": ["tăng huyết áp"],
    },
    # Beta-blocker addition
    {
        "inn": "Metoprolol",
        "brands": ["Betaloc", "Betaloc ZOK", "me to pro lol"],
        "forms": ["viên 25mg", "viên 50mg", "viên 100mg", "viên phóng thích chậm 50mg"],
        "typical": "25-100mg x 1-2 lần/ngày",
        "category": "Beta-blocker",
        "otc": False,
        "keywords": ["metoprolol", "betaloc", "me to pro lol", "be ta loc"],
        "phonetic_variants": {
            "north":   ["me to pro lol", "mê tô prô lôl"],
            "central": ["me to pro lol", "me to pro lon"],
            "south":   ["me to pro", "be ta loc"],
        },
        "valid_doses_mg": [25, 50, 100, 200],
        "dose_range": {"min": 25, "max": 400},
        "drug_class": "beta_blocker",
        "compatible_diagnoses": ["tăng huyết áp", "suy tim", "rối loạn nhịp tim"],
    },
    # Diuretics
    {
        "inn": "Indapamide",
        "brands": ["Natrilix", "in đa pa mit"],
        "forms": ["viên 1.5mg", "viên 2.5mg"],
        "typical": "1.5-2.5mg x 1 lần/ngày sáng",
        "category": "Lợi tiểu Thiazide-like",
        "otc": False,
        "keywords": ["indapamide", "natrilix", "in đa pa mit", "na tri lích"],
        "phonetic_variants": {
            "north":   ["in đa pa mit", "in đa pa miđ"],
            "central": ["in đa pa mit", "in đa pa mid"],
            "south":   ["in đa pa", "na tri lích"],
        },
        "valid_doses_mg": [1.5, 2.5],
        "dose_range": {"min": 1.5, "max": 5},
        "drug_class": "thiazide_like_diuretic",
        "compatible_diagnoses": ["tăng huyết áp"],
    },
    # PPIs
    {
        "inn": "Rabeprazole",
        "brands": ["Pariet", "ra be pra zôl"],
        "forms": ["viên 10mg", "viên 20mg"],
        "typical": "20mg x 1-2 lần/ngày trước ăn",
        "category": "Ức chế bơm proton",
        "otc": False,
        "keywords": ["rabeprazole", "pariet", "ra be pra zôl", "pa ri ê"],
        "phonetic_variants": {
            "north":   ["ra be pra zôl", "ra bê pra zol"],
            "central": ["ra be pra zol", "ra bê pra zol"],
            "south":   ["ra be pra", "pa ri e"],
        },
        "valid_doses_mg": [10, 20],
        "dose_range": {"min": 10, "max": 40},
        "drug_class": "ppi",
        "compatible_diagnoses": ["loét dạ dày", "trào ngược dạ dày thực quản"],
    },
    {
        "inn": "Lansoprazole",
        "brands": ["Prevacid", "lan so pra zôl"],
        "forms": ["viên 15mg", "viên 30mg"],
        "typical": "30mg x 1 lần/ngày trước bữa sáng",
        "category": "Ức chế bơm proton",
        "otc": False,
        "keywords": ["lansoprazole", "prevacid", "lan so pra zôl", "pre va xid"],
        "phonetic_variants": {
            "north":   ["lan so pra zôl", "lăn xô pra zol"],
            "central": ["lan so pra zol", "lăn xô pra zol"],
            "south":   ["lan so pra", "pre va xid"],
        },
        "valid_doses_mg": [15, 30],
        "dose_range": {"min": 15, "max": 60},
        "drug_class": "ppi",
        "compatible_diagnoses": ["loét dạ dày", "trào ngược dạ dày thực quản"],
    },
    # Antacids / Gastroprotective
    {
        "inn": "Aluminum phosphate",
        "brands": ["Phosphalugel", "phot pha lu gen", "phos pha lu gel"],
        "forms": ["gói gel 20g"],
        "typical": "1-2 gói x 3-4 lần/ngày sau ăn và trước ngủ",
        "category": "Bảo vệ niêm mạc / Antacid",
        "otc": True,
        "keywords": ["phosphalugel", "nhôm phosphate", "phot pha lu gen", "phos pha lu gel"],
        "phonetic_variants": {
            "north":   ["phot pha lu gel", "phot pha lu ghen"],
            "central": ["phot pha lu gen", "phos pha lu gen"],
            "south":   ["phot pha", "phos pha lu", "phot pha lu"],
        },
        "valid_doses_mg": [],
        "dose_range": {"min": 0, "max": 0},
        "drug_class": "antacid",
        "compatible_diagnoses": ["đau dạ dày", "loét dạ dày", "trào ngược"],
    },
    {
        "inn": "Sucralfate",
        "brands": ["Ulcogant", "su cra phat", "su kra phat"],
        "forms": ["viên 1g", "hỗn dịch 1g/5ml"],
        "typical": "1g x 4 lần/ngày trước bữa ăn và trước ngủ",
        "category": "Bảo vệ niêm mạc",
        "otc": False,
        "keywords": ["sucralfate", "ulcogant", "su cra phat", "su kra phat"],
        "phonetic_variants": {
            "north":   ["su cra phat", "su kra phát"],
            "central": ["su cra phat", "su kra phát"],
            "south":   ["su cra", "un co gant"],
        },
        "valid_doses_mg": [1000],
        "dose_range": {"min": 1000, "max": 4000},
        "drug_class": "gastroprotective",
        "compatible_diagnoses": ["loét dạ dày", "loét tá tràng"],
    },
    # NSAIDs
    {
        "inn": "Lornoxicam",
        "brands": ["Xefocam", "lol no xi cam", "lo no xi cam"],
        "forms": ["viên 4mg", "viên 8mg", "ống tiêm 8mg"],
        "typical": "8-16mg/ngày chia 2 lần",
        "category": "Chống viêm NSAIDs",
        "otc": False,
        "keywords": ["lornoxicam", "xefocam", "lo no xi cam", "xe phô cam"],
        "phonetic_variants": {
            "north":   ["lol no xi cam", "lo no xi cam"],
            "central": ["lol no xi cam", "lor no xi cam"],
            "south":   ["lo no xi", "xe phô cam"],
        },
        "valid_doses_mg": [4, 8],
        "dose_range": {"min": 4, "max": 16},
        "drug_class": "nsaid",
        "compatible_diagnoses": ["đau", "viêm khớp"],
    },
    # Neuropathy
    {
        "inn": "Mecobalamin",
        "brands": ["Methycobal", "Mecobal", "me co ba la min"],
        "forms": ["viên 500mcg", "ống tiêm 500mcg"],
        "typical": "500mcg x 3 lần/ngày",
        "category": "Vitamin B12 hoạt tính",
        "otc": True,
        "keywords": ["mecobalamin", "methycobal", "me co ba la min", "mê co ba"],
        "phonetic_variants": {
            "north":   ["me co ba la min", "mê cô ba la min"],
            "central": ["me co ba la min", "mê co ba la minh"],
            "south":   ["me co ba la", "me co ba", "me co ba min"],
        },
        "valid_doses_mg": [0.5],
        "dose_range": {"min": 0.5, "max": 3},
        "drug_class": "vitamin_b12_active",
        "compatible_diagnoses": ["đau thần kinh ngoại vi", "thiếu B12"],
    },
    {
        "inn": "Alpha Lipoic Acid",
        "brands": ["Alphalipon", "Thioctacid", "an pha li po ic"],
        "forms": ["viên 300mg", "viên 600mg", "ống tiêm 300mg"],
        "typical": "300-600mg x 1 lần/ngày",
        "category": "Chống oxy hóa thần kinh",
        "otc": True,
        "keywords": ["alpha lipoic", "alphalipon", "thioctacid", "an pha li po ic", "thio"],
        "phonetic_variants": {
            "north":   ["an pha li po ic", "an pha li po ích"],
            "central": ["an pha li po ic", "an pha li po ích"],
            "south":   ["an pha li po", "an pha"],
        },
        "valid_doses_mg": [300, 600],
        "dose_range": {"min": 300, "max": 1800},
        "drug_class": "antioxidant_neuropathic",
        "compatible_diagnoses": ["đau thần kinh ngoại vi", "biến chứng thần kinh đái tháo đường"],
    },
    # Psychiatry / Sleep
    {
        "inn": "Sertraline",
        "brands": ["Zoloft", "xe tra lin"],
        "forms": ["viên 25mg", "viên 50mg", "viên 100mg"],
        "typical": "50mg x 1 lần/ngày sáng",
        "category": "Chống trầm cảm SSRI",
        "otc": False,
        "keywords": ["sertraline", "zoloft", "xe tra lin", "zô lôpht"],
        "phonetic_variants": {
            "north":   ["xe tra lin", "sé tra lin"],
            "central": ["xe tra linh", "sé tra linh"],
            "south":   ["xe tra", "zo lô pht"],
        },
        "valid_doses_mg": [25, 50, 100],
        "dose_range": {"min": 25, "max": 200},
        "drug_class": "ssri",
        "compatible_diagnoses": ["trầm cảm", "lo âu", "rối loạn ám ảnh cưỡng chế"],
    },
    {
        "inn": "Escitalopram",
        "brands": ["Lexapro", "Cipralex", "e xi ta lo pram"],
        "forms": ["viên 5mg", "viên 10mg", "viên 20mg"],
        "typical": "10mg x 1 lần/ngày",
        "category": "Chống trầm cảm SSRI",
        "otc": False,
        "keywords": ["escitalopram", "lexapro", "cipralex", "e xi ta lo pram", "le xa prô"],
        "phonetic_variants": {
            "north":   ["e xi ta lo pram", "ê xi ta lô pram"],
            "central": ["e xi ta lo pram", "ê xi ta lo pram"],
            "south":   ["e xi ta lo", "le xa prô"],
        },
        "valid_doses_mg": [5, 10, 20],
        "dose_range": {"min": 5, "max": 20},
        "drug_class": "ssri",
        "compatible_diagnoses": ["trầm cảm", "lo âu"],
    },
    {
        "inn": "Zolpidem",
        "brands": ["Stilnox", "Ambien", "zol pi đem"],
        "forms": ["viên 5mg", "viên 10mg"],
        "typical": "10mg trước ngủ",
        "category": "Thuốc ngủ Z-drug",
        "otc": False,
        "keywords": ["zolpidem", "stilnox", "ambien", "zol pi đem", "xtil noc"],
        "phonetic_variants": {
            "north":   ["zol pi đem", "zôl pi đem"],
            "central": ["zol pi đem", "zol pi dem"],
            "south":   ["zol pi", "xtil noc"],
        },
        "valid_doses_mg": [5, 10],
        "dose_range": {"min": 5, "max": 10},
        "drug_class": "sedative_hypnotic",
        "compatible_diagnoses": ["mất ngủ"],
    },
    # Antibiotics
    {
        "inn": "Cefdinir",
        "brands": ["Omnicef", "xe phi ni"],
        "forms": ["viên 300mg", "hỗn dịch 125mg/5ml"],
        "typical": "300mg x 2 lần/ngày hoặc 600mg x 1 lần/ngày",
        "category": "Kháng sinh Cephalosporin 3G",
        "otc": False,
        "keywords": ["cefdinir", "omnicef", "xe phi ni", "om ni xef"],
        "phonetic_variants": {
            "north":   ["xe phi ni", "xê phi ni"],
            "central": ["xe phi ninh", "xê phi ninh"],
            "south":   ["xe phi", "om ni xef"],
        },
        "valid_doses_mg": [300, 600],
        "dose_range": {"min": 300, "max": 1200},
        "drug_class": "cephalosporin_3g",
        "compatible_diagnoses": ["viêm phổi", "viêm tai giữa", "viêm họng"],
    },
    {
        "inn": "Spiramycin",
        "brands": ["Rovamycine", "xi pi ra my xin"],
        "forms": ["viên 1.5MIU", "viên 3MIU"],
        "typical": "3MUI x 3 lần/ngày",
        "category": "Kháng sinh Macrolide",
        "otc": False,
        "keywords": ["spiramycin", "rovamycine", "xi pi ra my xin", "ro va my xin"],
        "phonetic_variants": {
            "north":   ["xi pi ra my xin", "spi ra my xin"],
            "central": ["xi pi ra my xinh", "spi ra my xin"],
            "south":   ["xi pi ra my", "ro va my xin"],
        },
        "valid_doses_mg": [],
        "dose_range": {"min": 0, "max": 0},
        "drug_class": "macrolide",
        "compatible_diagnoses": ["nhiễm trùng miệng hầu", "toxoplasma"],
    },
    {
        "inn": "Tinidazole",
        "brands": ["Fasigyn", "ti ni đa zôl"],
        "forms": ["viên 500mg"],
        "typical": "2g x 1 lần/ngày × 3 ngày",
        "category": "Kháng sinh Nitroimidazole",
        "otc": False,
        "keywords": ["tinidazole", "fasigyn", "ti ni đa zôl", "pha xi ghin"],
        "phonetic_variants": {
            "north":   ["ti ni đa zôl", "ti ni da zol"],
            "central": ["ti ni đa zol", "ti ni da zon"],
            "south":   ["ti ni đa", "pha xi ghin"],
        },
        "valid_doses_mg": [500],
        "dose_range": {"min": 500, "max": 4000},
        "drug_class": "nitroimidazole",
        "compatible_diagnoses": ["nhiễm Trichomonas", "nhiễm Giardia", "H.pylori"],
    },
    # Supplements common in VN clinics
    {
        "inn": "Coenzyme Q10",
        "brands": ["CoQ10", "co en zim cu mười"],
        "forms": ["viên 30mg", "viên 60mg", "viên 100mg"],
        "typical": "100-200mg/ngày",
        "category": "Bổ sung tim mạch",
        "otc": True,
        "keywords": ["coq10", "coenzyme q10", "co en zim cu", "co en zim"],
        "phonetic_variants": {
            "north":   ["co en zim cu mười", "co en zim"],
            "central": ["co en zim cu mười", "co en zim"],
            "south":   ["co en zim cu", "co en zim"],
        },
        "valid_doses_mg": [30, 60, 100, 200],
        "dose_range": {"min": 30, "max": 1200},
        "drug_class": "supplement_cardiac",
        "compatible_diagnoses": ["suy tim", "bổ sung tim mạch"],
    },
    # Spironolactone — already in list? Let me check... yes it's there
    # Acarbose
    {
        "inn": "Acarbose",
        "brands": ["Glucobay", "a ca rô", "a ca bô"],
        "forms": ["viên 25mg", "viên 50mg", "viên 100mg"],
        "typical": "25-100mg x 3 lần/ngày với bữa ăn",
        "category": "Tiểu đường type 2 Alpha-glucosidase inhibitor",
        "otc": False,
        "keywords": ["acarbose", "glucobay", "a ca rô", "a ca bô", "glu co bê"],
        "phonetic_variants": {
            "north":   ["a ca rô", "a ca boz"],
            "central": ["a ca rô", "a ca bo"],
            "south":   ["a ca rô", "glu co bê"],
        },
        "valid_doses_mg": [25, 50, 100],
        "dose_range": {"min": 25, "max": 300},
        "drug_class": "alpha_glucosidase_inhibitor",
        "compatible_diagnoses": ["đái tháo đường type 2"],
    },
]

# ─── Auto rule-based variant generator ──────────────────────────────────────
def syllabify_latin(name: str) -> list[str]:
    """Very rough syllabification of Latin drug names for VN phonetics."""
    import re
    # Remove parenthetical
    name = re.sub(r"\(.*?\)", "", name).strip()
    # Split on / for combination drugs
    name = name.split("/")[0].strip()
    # Basic: split on vowel-consonant boundaries (approximate)
    syllables = re.findall(r"[A-Za-z]+", name)
    # Join into one word and split into ~3-char chunks
    word = syllables[0] if syllables else name
    return [word]


def generate_auto_variants(inn_name: str) -> dict:
    """
    Generate approximate phonetic variants for non-manual drugs.
    Applies R2/R5/R7 rules from CONS-20260610-001.
    """
    import re
    # Take first word of INN (before /, before space)
    base = re.sub(r"\(.*?\)", "", inn_name).strip()
    base = base.split("/")[0].split()[0]

    b = base.lower()

    # R5: f → ph
    b_ph = b.replace("f", "ph")

    # R2: final -ine → pin (north), phin (central), drop (south)
    b_north  = re.sub(r"ine$", "in",  b_ph)
    b_north  = re.sub(r"pine$", "pin", b_ph)
    b_central = re.sub(r"ine$", "inh", b_ph)
    b_central = re.sub(r"pine$", "phin", b_ph)
    b_south  = re.sub(r"ine$", "",   b_ph)
    b_south  = re.sub(r"pine$", "", b_ph)

    # R2b: -ol → ol (north/central), o (south)
    b_south_ol = re.sub(r"ol$", "o", b_south if b_south else b_ph)

    # Basic variant: insert spaces roughly every 2-3 chars (very rough)
    def space_it(s):
        # split Latin into segments
        parts = re.findall(r"[aeiou]+[^aeiou]*|[^aeiou]+[aeiou]+", s)
        return " ".join(parts) if parts else s

    v_north   = space_it(b_north)   if b_north   else space_it(b_ph)
    v_central = space_it(b_central) if b_central else space_it(b_ph)
    v_south   = space_it(b_south_ol or b_south or b_ph)

    return {
        "north":   [v_north, b_north] if v_north != b_north else [v_north],
        "central": [v_central],
        "south":   [v_south] if v_south else [b_ph[:max(3, len(b_ph)//2)]],
    }


# ─── Main builder ────────────────────────────────────────────────────────────
def build():
    print(f"Loading {SRC} ...")
    with open(SRC, encoding="utf-8") as f:
        db = json.load(f)

    existing_inns = set(db["by_inn"].keys())

    # 1. Add new fields to all existing drugs
    for inn, drug in db["by_inn"].items():
        manual = TOP_MANUAL.get(inn)
        if manual:
            drug["phonetic_variants"]    = manual["phonetic_variants"]
            drug["valid_doses_mg"]       = manual["valid_doses_mg"]
            drug["dose_range"]           = manual["dose_range"]
            drug["drug_class"]           = manual["drug_class"]
            drug["compatible_diagnoses"] = manual["compatible_diagnoses"]
        else:
            # Auto-generate
            drug["phonetic_variants"]    = generate_auto_variants(inn)
            drug["valid_doses_mg"]       = []
            drug["dose_range"]           = {"min": 0, "max": 0}
            drug["drug_class"]           = ""
            drug["compatible_diagnoses"] = []

    # 2. Add new drugs
    added = 0
    for nd in NEW_DRUGS:
        inn = nd["inn"]
        if inn in existing_inns:
            print(f"  SKIP (already exists): {inn}")
            continue
        db["by_inn"][inn] = {k: v for k, v in nd.items() if k != "inn"}
        db["by_inn"][inn]["inn"] = inn
        # ensure brands list always includes INN itself
        if inn not in db["by_inn"][inn].get("brands", []):
            db["by_inn"][inn].setdefault("brands", [])
            db["by_inn"][inn]["brands"].append(inn.lower())
        # rebuild keyword_index entry
        if "keyword_index" not in db:
            db["keyword_index"] = {}
        for kw in nd.get("keywords", []):
            db["keyword_index"].setdefault(kw, [])
            if inn not in db["keyword_index"][kw]:
                db["keyword_index"][kw].append(inn)
        added += 1
        print(f"  ADDED: {inn}")

    # 3. Update metadata
    total = len(db["by_inn"])
    db["_meta"]["total_drugs"] = total
    db["_meta"]["version"]     = "2.0.0"
    db["_meta"]["sources_used"].append(
        "CONS-20260610-001 + CONS-20260610-002: phonetic_variants + drug_class + dose_range (2026-06-10)"
    )
    db["_meta"]["sources_used"].append(
        "DRUG-DB-002: SGLT-2/DPP-4/ARB/CCB/PPI/neuropathy additions (2026-06-10)"
    )
    db["_meta"]["schema_version"] = "v200"
    db["_meta"]["new_fields"] = [
        "phonetic_variants",
        "valid_doses_mg",
        "dose_range",
        "drug_class",
        "compatible_diagnoses",
    ]

    # 4. Write output
    print(f"\nWriting {DST} ...")
    with open(DST, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(db['by_inn'])} drugs ({added} new). Schema v200.")
    print(f"Top manual entries: {len(TOP_MANUAL)}")
    print(f"Auto-generated: {total - len(TOP_MANUAL) - added} drugs")


if __name__ == "__main__":
    build()
