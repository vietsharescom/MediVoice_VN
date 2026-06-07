#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_synthetic_ner.py — MediVoice VN
Tạo dữ liệu NER tổng hợp cho outpatient consultation tiếng Việt.

Output:
  data/synthetic_ner/train.jsonl   — BIO format cho PhoBERT+CRF
  data/synthetic_ner/val.jsonl
  data/synthetic_ner/test.jsonl
  data/synthetic_ner/summary.json  — thống kê

Usage:
  python -X utf8 scripts/generate_synthetic_ner.py              # mặc định 10000 samples
  python -X utf8 scripts/generate_synthetic_ner.py --n 500      # 500 samples
  python -X utf8 scripts/generate_synthetic_ner.py --seed 42    # reproducible
  python -X utf8 scripts/generate_synthetic_ner.py --preview 5  # xem 5 mẫu, không lưu
"""

import sys, io, json, re, random, argparse
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
from typing import Optional
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── Entity types ──────────────────────────────────────────────────────────────
# Đồng bộ với VietMed-NER schema (dùng tên gần nhất)
ENTITY_TYPES = {
    "MEDICATION",   # Tên thuốc (drug name only)
    "DOSE",         # Liều lượng: 500mg, 250mg/5ml
    "FREQUENCY",    # Tần suất: 3 lần/ngày
    "DURATION",     # Thời gian dùng: 7 ngày, 2 tuần
    "ROUTE",        # Đường dùng: uống, tiêm bắp, bôi
    "SYMPTOM",      # Triệu chứng BN mô tả: đau họng, sốt, ho
    "DIAGNOSIS",    # Chẩn đoán BS: viêm họng cấp J02.9
    "VITAL",        # Sinh hiệu: 38.5°C, 120/80 mmHg, 65 kg
    "FOLLOWUP",     # Tái khám: sau 7 ngày nếu không đỡ
}

# ── Scenario definitions ──────────────────────────────────────────────────────

@dataclass
class Drug:
    name: str
    dose: str
    frequency: str
    duration: str
    route: str = "uống"
    alt_names: list[str] = field(default_factory=list)  # PhoWhisper mishear variants

@dataclass
class Scenario:
    id: str
    icd10: str
    diagnosis_vi: str
    symptoms: list[str]
    vitals: list[str]
    drugs: list[Drug]
    followup_days: list[int]
    followup_conditions: list[str]

SCENARIOS: list[Scenario] = [
    Scenario(
        id="viem_hong",
        icd10="J02.9",
        diagnosis_vi="viêm họng cấp",
        symptoms=["đau họng", "sốt", "nuốt đau", "họng đỏ", "mệt mỏi", "đau đầu nhẹ", "ho khan"],
        vitals=["38.2", "38.5", "37.8", "38.0", "37.6"],
        drugs=[
            Drug("Amoxicillin", "500mg", "3 lần/ngày", "7 ngày",
                 alt_names=["ammos lim", "amô xi xi lin", "amoxycillin"]),
            Drug("Paracetamol", "500mg", "khi sốt trên 38.5°C", "khi cần",
                 alt_names=["para xi ta mol", "paracidamone"]),
            Drug("Loratadine", "10mg", "1 lần/ngày buổi tối", "5 ngày"),
        ],
        followup_days=[5, 7, 10],
        followup_conditions=["không đỡ", "sốt kéo dài", "ho nặng hơn"],
    ),
    Scenario(
        id="viem_da_day",
        icd10="K25.9",
        diagnosis_vi="viêm loét dạ dày",
        symptoms=["đau thượng vị", "đau bụng trên", "buồn nôn", "ợ chua", "khó tiêu", "chướng bụng"],
        vitals=["36.8", "37.0", "36.5", "37.2"],
        drugs=[
            Drug("Omeprazole", "20mg", "2 lần/ngày trước ăn 30 phút", "4 tuần",
                 alt_names=["ô mê pra zol", "omeprazol"]),
            Drug("Domperidone", "10mg", "3 lần/ngày trước ăn", "2 tuần",
                 alt_names=["đom pê ri đon", "domperidon"]),
            Drug("Amoxicillin", "500mg", "2 lần/ngày", "2 tuần",
                 alt_names=["amoxycillin"]),
            Drug("Metronidazole", "500mg", "2 lần/ngày", "2 tuần",
                 alt_names=["mê trô ni đa zol"]),
        ],
        followup_days=[14, 28],
        followup_conditions=["không cải thiện", "đau nhiều hơn", "nôn ra máu"],
    ),
    Scenario(
        id="tang_huyet_ap",
        icd10="I10",
        diagnosis_vi="tăng huyết áp",
        symptoms=["đau đầu", "chóng mặt", "hồi hộp", "khó thở nhẹ"],
        vitals=["145/95", "150/90", "160/100", "140/85", "155/95"],
        drugs=[
            Drug("Amlodipine", "5mg", "1 lần/ngày buổi sáng", "1 tháng",
                 alt_names=["am lô đi pin", "amlodipine"]),
            Drug("Losartan", "50mg", "1 lần/ngày", "1 tháng",
                 alt_names=["lô sar tan", "losartan"]),
            Drug("Atenolol", "50mg", "1 lần/ngày", "1 tháng"),
        ],
        followup_days=[14, 30],
        followup_conditions=["huyết áp không ổn định", "chóng mặt nhiều", "phù chân"],
    ),
    Scenario(
        id="dai_thao_duong",
        icd10="E11.9",
        diagnosis_vi="đái tháo đường type 2",
        symptoms=["khát nước nhiều", "tiểu nhiều lần", "mệt mỏi", "sụt cân không rõ lý do"],
        vitals=["7.2", "8.5", "6.8", "9.1", "7.8"],  # HbA1c hoặc đường huyết mmol/L
        drugs=[
            Drug("Metformin", "500mg", "2 lần/ngày trong bữa ăn", "1 tháng",
                 alt_names=["mê phô min", "glucophage"]),
            Drug("Gliclazide", "80mg", "1 lần/ngày buổi sáng trước ăn", "1 tháng",
                 alt_names=["gli cla zit"]),
            Drug("Sitagliptin", "50mg", "1 lần/ngày", "1 tháng",
                 alt_names=["si ta glip tin"]),
        ],
        followup_days=[14, 30],
        followup_conditions=["đường huyết không kiểm soát", "hạ đường huyết", "mệt nhiều"],
    ),
    Scenario(
        id="gout",
        icd10="M10.9",
        diagnosis_vi="gout cấp",
        symptoms=["sưng đau khớp ngón cái", "nóng đỏ khớp", "đau dữ dội", "khớp gối sưng"],
        vitals=["37.2", "37.5", "37.0", "36.8"],
        drugs=[
            Drug("Colchicine", "0.5mg", "2 lần/ngày", "5 ngày",
                 alt_names=["kôn chi xin", "colchicin"]),
            Drug("Allopurinol", "300mg", "1 lần/ngày sau ăn", "1 tháng",
                 alt_names=["a lô pu ri nol"]),
            Drug("Etoricoxib", "60mg", "1 lần/ngày", "7 ngày",
                 alt_names=["ê to ri kô xib"]),
        ],
        followup_days=[7, 14, 30],
        followup_conditions=["đau không giảm", "axit uric còn cao", "tái phát"],
    ),
    Scenario(
        id="cam_cum",
        icd10="J06.9",
        diagnosis_vi="cảm cúm",
        symptoms=["sổ mũi", "nghẹt mũi", "đau họng nhẹ", "sốt nhẹ", "mệt mỏi", "nhức mình"],
        vitals=["37.5", "37.8", "37.3", "38.0"],
        drugs=[
            Drug("Paracetamol", "500mg", "3 lần/ngày khi sốt", "3 ngày",
                 alt_names=["para xi ta mol"]),
            Drug("Cetirizine", "10mg", "1 lần/ngày buổi tối", "5 ngày",
                 alt_names=["xê ti ri zin"]),
            Drug("Xylometazoline", "0.1%", "nhỏ 2-3 giọt mỗi mũi", "5 ngày",
                 route="nhỏ mũi"),
        ],
        followup_days=[5, 7],
        followup_conditions=["sốt kéo dài hơn 3 ngày", "khó thở", "không đỡ"],
    ),
    Scenario(
        id="xuong_khop",
        icd10="M79.3",
        diagnosis_vi="đau cơ xương khớp",
        symptoms=["đau lưng", "đau vai gáy", "đau cổ", "tê tay", "mỏi vai", "đau khớp gối"],
        vitals=["36.8", "37.0", "37.2"],
        drugs=[
            Drug("Diclofenac", "50mg", "2 lần/ngày sau ăn", "7 ngày",
                 alt_names=["đi clo phê nak", "diclophenac"]),
            Drug("Glucosamine", "500mg", "2 viên/ngày", "2 tháng",
                 alt_names=["glu cô sa min"]),
            Drug("Pregabalin", "75mg", "2 lần/ngày", "2 tuần",
                 alt_names=["prê ga ba lin"]),
        ],
        followup_days=[14, 21],
        followup_conditions=["đau không cải thiện", "tê tay nặng hơn"],
    ),
    Scenario(
        id="viem_phe_quan",
        icd10="J20.9",
        diagnosis_vi="viêm phế quản cấp",
        symptoms=["ho có đờm", "ho khan kéo dài", "khó thở nhẹ", "tức ngực", "sốt nhẹ", "mệt mỏi"],
        vitals=["37.5", "37.8", "38.0", "37.3"],
        drugs=[
            Drug("Ambroxol", "30mg", "3 lần/ngày sau ăn", "7 ngày",
                 alt_names=["am bro xol", "ambroxol"]),
            Drug("Salbutamol", "4mg", "3 lần/ngày", "5 ngày",
                 alt_names=["sal bu ta mol", "ventolin"]),
            Drug("Prednisolone", "5mg", "1 lần/ngày buổi sáng", "5 ngày",
                 alt_names=["prêd ni so lon"]),
            Drug("Doxycycline", "100mg", "2 lần/ngày", "7 ngày",
                 alt_names=["đô xi xi klin"]),
        ],
        followup_days=[7, 10, 14],
        followup_conditions=["ho không giảm", "khó thở tăng", "sốt kéo dài"],
    ),
    Scenario(
        id="viem_xoang",
        icd10="J32.9",
        diagnosis_vi="viêm xoang mũi mạn tính",
        symptoms=["nghẹt mũi", "chảy mũi vàng xanh", "đau nhức vùng mặt", "đau đầu", "mất mùi", "hắt hơi"],
        vitals=["36.8", "37.0", "37.2", "36.5"],
        drugs=[
            Drug("Amoxicillin-Clavulanate", "625mg", "2 lần/ngày sau ăn", "7 ngày",
                 alt_names=["a moc xi lin cla vu la nat", "augmentin"]),
            Drug("Fluticasone", "50mcg", "xịt 2 nhát mỗi mũi buổi sáng", "1 tháng",
                 route="xịt mũi", alt_names=["flu ti ca zon", "flixonase"]),
            Drug("Cetirizine", "10mg", "1 lần/ngày buổi tối", "2 tuần",
                 alt_names=["xê ti ri zin"]),
            Drug("Xylometazoline", "0.1%", "nhỏ 2 giọt mỗi mũi", "5 ngày",
                 route="nhỏ mũi"),
        ],
        followup_days=[7, 14, 21],
        followup_conditions=["không cải thiện", "đau nhiều hơn", "chảy mũi máu"],
    ),
    Scenario(
        id="di_ung_mui",
        icd10="J30.4",
        diagnosis_vi="viêm mũi dị ứng",
        symptoms=["hắt hơi liên tục", "chảy mũi trong", "ngứa mũi", "ngứa mắt", "nghẹt mũi", "chảy nước mắt"],
        vitals=["36.5", "36.8", "37.0"],
        drugs=[
            Drug("Loratadine", "10mg", "1 lần/ngày buổi sáng", "2 tuần",
                 alt_names=["lo ra ta đin", "claritin"]),
            Drug("Mometasone", "50mcg", "xịt 2 nhát mỗi mũi mỗi ngày", "1 tháng",
                 route="xịt mũi", alt_names=["mo me ta zon", "nasonex"]),
            Drug("Fexofenadine", "120mg", "1 lần/ngày", "2 tuần",
                 alt_names=["fex sô phê na đin", "telfast"]),
        ],
        followup_days=[14, 30],
        followup_conditions=["triệu chứng không cải thiện", "khó thở", "phát ban"],
    ),
    Scenario(
        id="viem_da_ruot",
        icd10="A09",
        diagnosis_vi="viêm dạ dày ruột cấp",
        symptoms=["tiêu chảy", "buồn nôn", "nôn", "đau bụng quặn", "chướng bụng", "sốt nhẹ", "mất nước"],
        vitals=["37.2", "37.5", "37.8", "38.0"],
        drugs=[
            Drug("Oresol", "1 gói", "pha 200ml nước uống sau mỗi lần đi tiêu", "khi cần",
                 alt_names=["o rê sol", "ors"]),
            Drug("Loperamide", "2mg", "sau mỗi lần tiêu chảy tối đa 16mg/ngày", "3 ngày",
                 alt_names=["lô pê ra mit"]),
            Drug("Smecta", "3g", "3 gói/ngày hòa nước uống", "5 ngày",
                 alt_names=["smék ta", "diosmectite"]),
            Drug("Metronidazole", "500mg", "3 lần/ngày", "5 ngày",
                 alt_names=["mê trô ni đa zol"]),
        ],
        followup_days=[3, 5, 7],
        followup_conditions=["tiêu chảy không giảm", "nôn nhiều", "mất nước nặng", "có máu trong phân"],
    ),
    Scenario(
        id="nhiem_trung_tiet_nieu",
        icd10="N39.0",
        diagnosis_vi="nhiễm trùng đường tiết niệu",
        symptoms=["tiểu buốt", "tiểu rắt", "tiểu nhiều lần", "nước tiểu đục", "đau vùng bàng quang", "sốt nhẹ"],
        vitals=["37.3", "37.5", "37.8", "38.0"],
        drugs=[
            Drug("Trimethoprim-Sulfamethoxazole", "960mg", "2 lần/ngày", "7 ngày",
                 alt_names=["tri mê tô prim", "bactrim"]),
            Drug("Ciprofloxacin", "500mg", "2 lần/ngày sau ăn", "7 ngày",
                 alt_names=["xi pro phlo xa xin", "cipro"]),
            Drug("Nitrofurantoin", "100mg", "2 lần/ngày trong bữa ăn", "5 ngày",
                 alt_names=["ni tro phu ran toin"]),
        ],
        followup_days=[7, 14],
        followup_conditions=["triệu chứng không cải thiện", "sốt cao", "đau lưng"],
    ),
    Scenario(
        id="thieu_mau",
        icd10="D50.9",
        diagnosis_vi="thiếu máu thiếu sắt",
        symptoms=["mệt mỏi", "da xanh", "chóng mặt", "hồi hộp", "đau đầu", "khó thở khi gắng sức"],
        vitals=["36.5", "36.8", "37.0"],
        drugs=[
            Drug("Ferrous Sulfate", "325mg", "2 lần/ngày trước ăn 1 giờ", "3 tháng",
                 alt_names=["phê rơ sul phat", "sắt sulfate"]),
            Drug("Vitamin C", "500mg", "2 lần/ngày cùng sắt", "3 tháng",
                 alt_names=["vi ta min xê"]),
            Drug("Folic Acid", "5mg", "1 lần/ngày", "3 tháng",
                 alt_names=["fo lic axít", "axit folic"]),
        ],
        followup_days=[30, 60, 90],
        followup_conditions=["mệt mỏi không cải thiện", "chóng mặt nhiều", "xét nghiệm máu lại"],
    ),
    Scenario(
        id="mat_ngu",
        icd10="G47.0",
        diagnosis_vi="mất ngủ",
        symptoms=["khó vào giấc ngủ", "ngủ không sâu", "thức dậy sớm", "mệt mỏi ban ngày", "lo âu", "căng thẳng"],
        vitals=["36.8", "37.0", "36.5"],
        drugs=[
            Drug("Melatonin", "3mg", "1 lần/ngày trước ngủ 30 phút", "2 tuần",
                 alt_names=["mê la to nin"]),
            Drug("Zolpidem", "10mg", "1 lần/ngày trước khi ngủ", "2 tuần",
                 alt_names=["zol pi đem", "stilnox"]),
            Drug("Hydroxyzine", "25mg", "1 lần/ngày trước ngủ", "2 tuần",
                 alt_names=["hi đrô xi zin"]),
        ],
        followup_days=[14, 21, 30],
        followup_conditions=["vẫn mất ngủ", "lo âu tăng", "buồn ngủ ban ngày nhiều"],
    ),
    Scenario(
        id="tang_mo_mau",
        icd10="E78.5",
        diagnosis_vi="rối loạn lipid máu",
        symptoms=["không có triệu chứng rõ", "đau đầu nhẹ", "mệt mỏi", "xanthoma"],
        vitals=["36.8", "37.0", "36.5"],
        drugs=[
            Drug("Atorvastatin", "20mg", "1 lần/ngày buổi tối", "3 tháng",
                 alt_names=["a to va sta tin", "lipitor"]),
            Drug("Rosuvastatin", "10mg", "1 lần/ngày buổi tối", "3 tháng",
                 alt_names=["ro su va sta tin", "crestor"]),
            Drug("Fenofibrate", "160mg", "1 lần/ngày trong bữa ăn", "3 tháng",
                 alt_names=["phê no phi brat"]),
        ],
        followup_days=[30, 90],
        followup_conditions=["xét nghiệm lipid máu", "đau cơ", "men gan tăng"],
    ),
    Scenario(
        id="viem_ket_mac",
        icd10="H10.9",
        diagnosis_vi="viêm kết mạc",
        symptoms=["mắt đỏ", "chảy nước mắt", "ngứa mắt", "ghèn mắt", "cộm mắt", "nhạy cảm ánh sáng"],
        vitals=["36.8", "37.0", "37.2"],
        drugs=[
            Drug("Tobramycin", "0.3%", "nhỏ 1-2 giọt mỗi mắt 4 lần/ngày", "7 ngày",
                 route="nhỏ mắt", alt_names=["to bra my xin"]),
            Drug("Ofloxacin", "0.3%", "nhỏ 1 giọt mỗi mắt 4 lần/ngày", "5 ngày",
                 route="nhỏ mắt", alt_names=["ô phlo xa xin"]),
            Drug("Dexamethasone", "0.1%", "nhỏ 1 giọt 3 lần/ngày", "5 ngày",
                 route="nhỏ mắt", alt_names=["đê xa mê ta zon"]),
        ],
        followup_days=[5, 7, 10],
        followup_conditions=["mắt không đỡ", "đau mắt nhiều hơn", "thị lực giảm"],
    ),
    Scenario(
        id="viem_amidan",
        icd10="J35.0",
        diagnosis_vi="viêm amidan cấp",
        symptoms=["đau họng dữ dội", "sốt cao", "khó nuốt", "amidan sưng to", "có mủ amidan", "hạch cổ sưng"],
        vitals=["38.5", "39.0", "38.8", "38.2", "39.2"],
        drugs=[
            Drug("Amoxicillin-Clavulanate", "625mg", "2 lần/ngày sau ăn", "10 ngày",
                 alt_names=["augmentin", "a moc xi lin"]),
            Drug("Cefuroxime", "500mg", "2 lần/ngày sau ăn", "7 ngày",
                 alt_names=["xê phu rôc sim"]),
            Drug("Paracetamol", "500mg", "3 lần/ngày khi sốt", "khi cần",
                 alt_names=["para xi ta mol"]),
            Drug("Ibuprofen", "400mg", "3 lần/ngày sau ăn", "5 ngày",
                 alt_names=["i bu pro phen"]),
        ],
        followup_days=[5, 7, 10],
        followup_conditions=["sốt không hạ", "amidan mủ nhiều hơn", "khó thở"],
    ),
]

# ── Regional language markers ─────────────────────────────────────────────────

REGIONS = {
    "HN": {
        "name": "Hà Nội / Miền Bắc",
        "speed": "medium",
        "fillers": ["thì", "ừ", "nhé", "thôi", "được rồi", "vâng"],
        "prescription_verb": "kê đơn",
        "reexam_phrase": "tái khám",
        "ok_phrase": "được",
        "neg": "không",
        "drug_intro": ["Tôi kê cho bạn", "Kê đơn thuốc", "Tôi cho bạn dùng"],
    },
    "SG": {
        "name": "Sài Gòn / Miền Nam",
        "speed": "fast",
        "fillers": ["thì", "hén", "nhen", "hông", "ha"],
        "prescription_verb": "kê toa",
        "reexam_phrase": "tái khám",
        "ok_phrase": "được nhen",
        "neg": "hổng",
        "drug_intro": ["Tui kê toa cho anh/chị", "Cho anh/chị uống", "Kê toa"],
    },
    "CT": {
        "name": "Cần Thơ / Tây Nam Bộ",
        "speed": "slow",
        "fillers": ["thì", "nha", "hen", "dzậy", "ừ"],
        "prescription_verb": "kê đơn",
        "reexam_phrase": "tái khám lại",
        "ok_phrase": "được nha",
        "neg": "hổng",
        "drug_intro": ["Tui cho anh/chị uống", "Kê đơn thuốc nha", "Cho dùng"],
    },
    "CA": {
        "name": "Canada / Việt kiều",
        "speed": "medium",
        "fillers": ["thì", "uh", "basically", "thật ra", "ừ"],
        "prescription_verb": "kê đơn",
        "reexam_phrase": "follow up",
        "ok_phrase": "okay nhen",
        "neg": "không",
        "drug_intro": ["Tôi prescribe cho bạn", "Kê đơn", "Cho bạn dùng"],
    },
}

# ── Sample templates ──────────────────────────────────────────────────────────
# Mỗi template là 1 cấu trúc câu — điền variable vào

TEMPLATES = [
    # Full consultation
    (
        "Qua thăm khám thì {filler1} bạn bị {diagnosis}. "
        "{drug_intro} {drug_name} {dose} {route} {frequency} trong {duration}. "
        "{vital_phrase} "
        "{reexam_phrase} sau {followup_days} ngày nếu {followup_cond}.",
        ["diagnosis", "drug1", "vital", "followup"]
    ),
    (
        "Chẩn đoán là {diagnosis}. {filler1} "
        "Kê {drug_name} {dose} {frequency}, {route}, {duration}. "
        "Thêm {drug2_name} {drug2_dose} {drug2_freq}. "
        "{vital_phrase} "
        "Hẹn {reexam_phrase} {followup_days} ngày.",
        ["diagnosis", "drug1", "drug2", "vital", "followup"]
    ),
    # Short prescription only
    (
        "{drug_intro} {drug_name} {dose}, {frequency}, {duration}.",
        ["drug1"]
    ),
    # Diagnosis + vital + drug
    (
        "{vital_phrase}. {filler1} {diagnosis}. "
        "{drug_intro} {drug_name} {dose} {route} {frequency}.",
        ["vital", "diagnosis", "drug1"]
    ),
    # Multi-drug
    (
        "Bệnh nhân {symptoms_phrase}. {filler1} Chẩn đoán {diagnosis}. "
        "Toa thuốc: {drug_name} {dose} {frequency}; "
        "{drug2_name} {drug2_dose} {drug2_freq}. "
        "{reexam_phrase} sau {followup_days} ngày.",
        ["symptom", "diagnosis", "drug1", "drug2", "followup"]
    ),
    # Symptoms + diagnosis + followup
    (
        "Bệnh nhân khai {symptoms_phrase}, {filler1} {vital_phrase}. "
        "{diagnosis}. {drug_intro} {drug_name} {dose} {route} {frequency} trong {duration}. "
        "{filler2} {reexam_phrase} {followup_days} ngày.",
        ["symptom", "vital", "diagnosis", "drug1", "followup"]
    ),
]

VITAL_PHRASES = {
    "viem_hong":              "Nhiệt độ {vital} độ C",
    "viem_da_day":            "Nhiệt độ {vital} độ, không sốt",
    "tang_huyet_ap":          "Huyết áp {vital} mmHg",
    "dai_thao_duong":         "Đường huyết {vital} mmol/L",
    "gout":                   "Nhiệt độ {vital} độ",
    "cam_cum":                "Nhiệt độ {vital} độ C",
    "xuong_khop":             "Nhiệt độ {vital} độ bình thường",
    "viem_phe_quan":          "Nhiệt độ {vital} độ C",
    "viem_xoang":             "Nhiệt độ {vital} độ, không sốt cao",
    "di_ung_mui":             "Nhiệt độ {vital} độ bình thường",
    "viem_da_ruot":           "Nhiệt độ {vital} độ C",
    "nhiem_trung_tiet_nieu":  "Nhiệt độ {vital} độ C",
    "thieu_mau":              "Nhiệt độ {vital} độ bình thường",
    "mat_ngu":                "Nhiệt độ {vital} độ bình thường",
    "tang_mo_mau":            "Nhiệt độ {vital} độ bình thường",
    "viem_ket_mac":           "Nhiệt độ {vital} độ",
    "viem_amidan":            "Nhiệt độ {vital} độ C",
}

# ── BIO annotation ────────────────────────────────────────────────────────────

def simple_tokenize(text: str) -> list[str]:
    """Tokenize VN text thành words (split by spaces, keep punctuation)."""
    tokens = []
    for word in re.split(r"(\s+)", text):
        if word.strip():
            tokens.append(word.strip())
    return tokens


def bio_tag(tokens: list[str], entity_text: str, entity_type: str,
            labels: list[str]) -> list[str]:
    """Gán BIO tags cho entity_text trong token list."""
    entity_tokens = simple_tokenize(entity_text)
    n = len(entity_tokens)
    for i in range(len(tokens) - n + 1):
        if [t.lower() for t in tokens[i:i+n]] == [t.lower() for t in entity_tokens]:
            # Check chưa tagged
            if all(labels[i+j] == "O" for j in range(n)):
                labels[i] = f"B-{entity_type}"
                for j in range(1, n):
                    labels[i+j] = f"I-{entity_type}"
                break
    return labels


# ── Sample generation ─────────────────────────────────────────────────────────

def build_sample(scenario: Scenario, region_id: str, rng: random.Random,
                 add_asr_errors: bool = False) -> dict:
    """Tạo 1 training sample với entities đã annotated."""
    region = REGIONS[region_id]

    drug = rng.choice(scenario.drugs)
    drug2 = rng.choice([d for d in scenario.drugs if d.name != drug.name]) \
        if len(scenario.drugs) > 1 else drug

    symptoms_sample = rng.sample(scenario.symptoms, min(2, len(scenario.symptoms)))
    vital = rng.choice(scenario.vitals)
    followup_day = rng.choice(scenario.followup_days)
    followup_cond = rng.choice(scenario.followup_conditions)
    filler1 = rng.choice(region["fillers"])
    filler2 = rng.choice(region["fillers"])

    # Thỉnh thoảng dùng tên nhầm (ASR error) — simulate PhoWhisper output
    drug_display = drug.name
    if add_asr_errors and drug.alt_names and rng.random() < 0.3:
        drug_display = rng.choice(drug.alt_names)

    # Vital phrase
    vital_phrase = VITAL_PHRASES.get(scenario.id, "Nhiệt độ {vital}°C").format(vital=vital)

    # Build text từ template
    template, required_fields = rng.choice(TEMPLATES)
    try:
        text = template.format(
            filler1=filler1,
            filler2=filler2,
            diagnosis=scenario.diagnosis_vi,   # BS nói tên bệnh, không đọc mã ICD
            drug_intro=rng.choice(region["drug_intro"]),
            drug_name=drug_display,
            dose=drug.dose,
            route=drug.route,
            frequency=drug.frequency,
            duration=drug.duration,
            drug2_name=drug2.name,
            drug2_dose=drug2.dose,
            drug2_freq=drug2.frequency,
            vital_phrase=vital_phrase,
            vital=vital,
            symptoms_phrase=" và ".join(symptoms_sample),
            reexam_phrase=region["reexam_phrase"],
            followup_days=followup_day,
            followup_cond=followup_cond,
        ).strip()
    except KeyError:
        # Fallback template đơn giản
        text = (
            f"Chẩn đoán {scenario.diagnosis_vi} {scenario.icd10}. "
            f"{vital_phrase}. "
            f"Kê {drug_display} {drug.dose} {drug.frequency} trong {drug.duration}. "
            f"Tái khám sau {followup_day} ngày."
        )

    # Tokenize
    tokens = simple_tokenize(text)
    labels = ["O"] * len(tokens)

    # Entity list để annotate
    entities: list[tuple[str, str]] = []  # (text, type)

    # DIAGNOSIS — chỉ tên bệnh tiếng Việt (ICD code không xuất hiện trong spoken text)
    entities.append((scenario.diagnosis_vi, "DIAGNOSIS"))

    # MEDICATION
    entities.append((drug_display, "MEDICATION"))
    entities.append((drug2.name, "MEDICATION"))

    # DOSE
    entities.append((drug.dose, "DOSE"))
    entities.append((drug2.dose, "DOSE"))

    # FREQUENCY
    entities.append((drug.frequency, "FREQUENCY"))
    entities.append((drug2.frequency, "FREQUENCY"))

    # DURATION
    if drug.duration != "khi cần":
        entities.append((drug.duration, "DURATION"))

    # ROUTE
    if drug.route != "uống":
        entities.append((drug.route, "ROUTE"))

    # VITAL
    if vital_phrase:
        entities.append((vital_phrase, "VITAL"))
        entities.append((vital, "VITAL"))

    # FOLLOWUP
    followup_text = f"{followup_day} ngày"
    entities.append((followup_text, "FOLLOWUP"))

    # SYMPTOM
    for sym in symptoms_sample:
        entities.append((sym, "SYMPTOM"))

    # Apply BIO tags (longest match first)
    entities.sort(key=lambda x: -len(x[0]))
    for ent_text, ent_type in entities:
        labels = bio_tag(tokens, ent_text, ent_type, labels)

    return {
        "id": f"SYN-{scenario.id}-{region_id}-{rng.randint(100000, 999999)}",
        "scenario": scenario.id,
        "icd10": scenario.icd10,
        "region": region_id,
        "region_name": region["name"],
        "has_asr_errors": add_asr_errors,
        "text": text,
        "words": tokens,
        "labels": labels,
        "entities": [
            {"text": t, "type": tp}
            for t, tp in entities
            if any(t.lower() in tok.lower() for tok in tokens)
        ],
        "ground_truth": {
            "chan_doan": scenario.diagnosis_vi,
            "icd10": scenario.icd10,
            "thuoc": [
                {
                    "ten": drug.name,
                    "ham_luong": drug.dose,
                    "tan_suat": drug.frequency,
                    "thoi_gian": drug.duration,
                    "duong_dung": drug.route,
                }
            ],
            "sinh_hieu": vital,
            "tai_kham": f"sau {followup_day} ngày",
        },
    }


def generate_dataset(n_total: int, rng: random.Random,
                     asr_error_rate: float = 0.2) -> list[dict]:
    """Tạo n_total samples phân bổ đều qua scenarios × regions."""
    samples = []
    region_ids = list(REGIONS.keys())
    n_per_combo = max(1, n_total // (len(SCENARIOS) * len(region_ids)))

    for scenario in SCENARIOS:
        for region_id in region_ids:
            for i in range(n_per_combo):
                add_errors = (i % 5 == 0) and (rng.random() < asr_error_rate)
                try:
                    s = build_sample(scenario, region_id, rng, add_asr_errors=add_errors)
                    samples.append(s)
                except Exception as e:
                    pass  # Skip malformed samples

    # Shuffle
    rng.shuffle(samples)

    # Top up nếu còn thiếu
    while len(samples) < n_total:
        sc = rng.choice(SCENARIOS)
        rg = rng.choice(region_ids)
        try:
            samples.append(build_sample(sc, rg, rng))
        except Exception:
            pass

    return samples[:n_total]


def split_dataset(samples: list[dict]) -> tuple[list, list, list]:
    """80/10/10 train/val/test split stratified by scenario."""
    from collections import defaultdict
    by_scenario: dict[str, list] = defaultdict(list)
    for s in samples:
        by_scenario[s["scenario"]].append(s)

    train, val, test = [], [], []
    for sc_samples in by_scenario.values():
        n = len(sc_samples)
        t1 = int(n * 0.8)
        t2 = int(n * 0.9)
        train.extend(sc_samples[:t1])
        val.extend(sc_samples[t1:t2])
        test.extend(sc_samples[t2:])

    return train, val, test


def save_jsonl(samples: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def print_preview(samples: list[dict], n: int = 3):
    """In n mẫu để kiểm tra chất lượng."""
    for i, s in enumerate(samples[:n]):
        print(f"\n{'─'*70}")
        print(f"ID: {s['id']}  Scenario: {s['scenario']}  Region: {s['region_name']}")
        print(f"Text: {s['text']}")
        print(f"Entities:")
        prev_label = "O"
        current_entity = []
        for tok, lbl in zip(s["words"], s["labels"]):
            if lbl == "O":
                if current_entity:
                    print(f"  [{prev_label[2:]}] {' '.join(current_entity)}")
                    current_entity = []
                    prev_label = "O"
            elif lbl.startswith("B-"):
                if current_entity:
                    print(f"  [{prev_label[2:]}] {' '.join(current_entity)}")
                current_entity = [tok]
                prev_label = lbl
            elif lbl.startswith("I-"):
                current_entity.append(tok)
        if current_entity:
            print(f"  [{prev_label[2:]}] {' '.join(current_entity)}")

        print(f"Ground truth: {json.dumps(s['ground_truth'], ensure_ascii=False)}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Tạo synthetic NER training data cho MediVoice VN")
    parser.add_argument("--n",       type=int, default=10000, help="Số samples tổng (default: 10000)")
    parser.add_argument("--seed",    type=int, default=42,   help="Random seed (default: 42)")
    parser.add_argument("--preview", type=int, default=0,    help="In N mẫu, không lưu file")
    parser.add_argument("--out",     type=str, default="data/synthetic_ner", help="Output directory")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    out_dir = Path(args.out)

    print(f"\n  generate_synthetic_ner.py — MediVoice VN")
    print(f"  Scenarios: {len(SCENARIOS)} | Regions: {len(REGIONS)} | Target: {args.n} samples")
    print(f"  Seed: {args.seed} | Output: {out_dir}")

    samples = generate_dataset(args.n, rng)

    if args.preview:
        print_preview(samples, args.preview)
        print(f"\n  Preview mode — {len(samples)} samples generated, không lưu file.")
        return

    train, val, test = split_dataset(samples)
    save_jsonl(train, out_dir / "train.jsonl")
    save_jsonl(val,   out_dir / "val.jsonl")
    save_jsonl(test,  out_dir / "test.jsonl")

    # Summary
    entity_counts = Counter(
        lbl[2:] for s in samples for lbl in s["labels"] if lbl.startswith("B-")
    )
    scenario_counts = Counter(s["scenario"] for s in samples)
    region_counts   = Counter(s["region"] for s in samples)
    asr_error_count = sum(1 for s in samples if s["has_asr_errors"])

    summary = {
        "total": len(samples),
        "train": len(train),
        "val":   len(val),
        "test":  len(test),
        "scenarios": dict(scenario_counts),
        "regions":   dict(region_counts),
        "entity_counts": dict(entity_counts.most_common()),
        "asr_error_samples": asr_error_count,
        "seed": args.seed,
        "entity_types": sorted(ENTITY_TYPES),
        "usage": {
            "train_ner": "from datasets import load_dataset; ds = load_dataset('json', data_files={'train': 'data/synthetic_ner/train.jsonl', 'validation': 'data/synthetic_ner/val.jsonl'})",
            "load_sample": "import json; [json.loads(l) for l in open('data/synthetic_ner/train.jsonl')]",
        },
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n  ✅ Generated {len(samples)} samples → {out_dir}/")
    print(f"     Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")
    print(f"     ASR error samples: {asr_error_count} ({asr_error_count/len(samples)*100:.0f}%)")
    print(f"\n  Entity distribution:")
    for etype, cnt in entity_counts.most_common():
        print(f"    {cnt:>5}  {etype}")
    print(f"\n  Scenario distribution:")
    for sc, cnt in scenario_counts.most_common():
        print(f"    {cnt:>5}  {sc}")
    print(f"\n  Bước tiếp theo:")
    print(f"    python -X utf8 scripts/generate_synthetic_ner.py --preview 3")
    print(f"    # Xem mẫu → confirm quality → train PhoBERT+CRF (TRAIN-002)")


if __name__ == "__main__":
    main()
