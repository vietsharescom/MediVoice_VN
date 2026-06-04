# src/pipeline/p2_decision/l6_soap_generator.py
# Module:   SOAPGenerator + Medical NER (sub-component of L6_AGENT)
# Role:     Generate structured SOAP note from medical entities + translated text.
#           SOAP "A" (Assessment) is differential reasoning — never AI diagnosis.
# Req:      SRS-L6-004, SRS-L6-005 -- see docs/cl08_operation/SRS.md
# FID:      DS-FID-001 | Primary value-creation module
# Policy:   AI_POLICY.md §3 — Medical Term Integrity
#           AI_POLICY.md §1 — All output labeled "AI-assisted draft"
# Standard: ISO/IEC 42001:2023 Clause 8.5
# Version:  v2.1 -- CA-029: stroke/neuro vocab + BGL vital + gender pediatric + edema FP fix

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Lazy-import PhoBERT NER — no crash if model absent
try:
    from src.models.phobert_ner import get_phobert_ner as _get_phobert_ner
    _PHOBERT_AVAILABLE = True
except ImportError:
    _PHOBERT_AVAILABLE = False
    logger.debug("src.models.phobert_ner not importable — rule-based NER only")

# Lazy-import FAISS KB + Qwen — no crash if not built/installed
try:
    from src.models.clinical_kb import get_clinical_kb as _get_kb
    from src.models.qwen_reasoning import get_qwen_reasoner as _get_qwen
    _RAG_AVAILABLE = True
except ImportError:
    _RAG_AVAILABLE = False
    logger.debug("clinical_kb/qwen_reasoning not importable — template DDx only")

# ── NER patterns ──────────────────────────────────────────────────────────────

_AGE_RE = re.compile(
    r'(\d+)\s*(?:-\s*year(?:s)?-old|years?\s*old|yo\b)',
    re.IGNORECASE,
)
_GENDER_RE = re.compile(r'\b(male|female)\b', re.IGNORECASE)
_BP_RE = re.compile(r'\b(\d{2,3}/\d{2,3})\s*(?:mmhg)?\b', re.IGNORECASE)
_HR_RE = re.compile(
    r'\b(?:heart rate|HR|pulse)[^\d]*(\d{2,3})\s*(?:bpm)?\b',
    re.IGNORECASE,
)
_TEMP_RE = re.compile(
    r'\b(?:temp(?:erature)?|fever)[^\d]*(\d{2,3}(?:\.\d)?)\s*(?:°?\s*[CF])\b',
    re.IGNORECASE,
)
_SPO2_RE = re.compile(r'\bSpO2[^\d]*(\d{2,3})\s*%?', re.IGNORECASE)
_MEDICATION_RE = re.compile(
    r'\b([A-Za-z][A-Za-z0-9\-]{4,})\s+(?:high\s+dose\s+|low\s+dose\s+)?(\d+(?:\.\d+)?)\s*(mg|mcg|ml|g|IU|units?)'
    r'(?:\s+(twice daily|once daily|daily|BD|OD|TDS|QID|every morning|every evening|weekly|per day|PRN'
    r'|every\s+(?:4|6|8|12|24)\s+hours?))?\b',
    re.IGNORECASE,
)
_BGL_RE = re.compile(
    r'\b(?:blood\s+glucose|BGL|blood\s+sugar)[^\d]*(\d+(?:\.\d+)?)\s*(?:mmol/l|mg/dl)?\b',
    re.IGNORECASE,
)

_SYMPTOM_KEYWORDS = {
    # Numbness/sensory — CA-032 (TIA signal)
    "right facial numbness":  ("SYMPTOM", "right facial numbness"),
    "left facial numbness":   ("SYMPTOM", "left facial numbness"),
    "facial numbness":        ("SYMPTOM", "facial numbness"),
    "hemifacial numbness":    ("SYMPTOM", "facial numbness"),
    "right hemibody numbness":("SYMPTOM", "right hemibody numbness"),
    "left hemibody numbness": ("SYMPTOM", "left hemibody numbness"),
    # Focal limb weakness — CA-032 (stroke/TIA signal)
    "right arm weakness":     ("SYMPTOM", "right arm weakness"),
    "left arm weakness":      ("SYMPTOM", "left arm weakness"),
    "right leg weakness":     ("SYMPTOM", "right leg weakness"),
    "left leg weakness":      ("SYMPTOM", "left leg weakness"),
    "right hand weakness":    ("SYMPTOM", "right arm weakness"),
    "left hand weakness":     ("SYMPTOM", "left arm weakness"),
    "focal limb weakness":    ("SYMPTOM", "focal limb weakness"),
    # Stroke / neuro — CA-029
    "acute ischemic stroke":  ("SYMPTOM", "ischemic stroke"),
    "ischemic stroke":        ("SYMPTOM", "ischemic stroke"),
    "hemorrhagic stroke":     ("SYMPTOM", "hemorrhagic stroke"),
    "right hemiparesis":      ("SYMPTOM", "right hemiparesis"),
    "left hemiparesis":       ("SYMPTOM", "left hemiparesis"),
    "hemiparesis":            ("SYMPTOM", "hemiparesis"),
    "right hemiplegia":       ("SYMPTOM", "right hemiplegia"),
    "left hemiplegia":        ("SYMPTOM", "left hemiplegia"),
    "dysarthria":             ("SYMPTOM", "dysarthria"),
    "facial droop":           ("SYMPTOM", "facial droop"),
    "facial weakness":        ("SYMPTOM", "facial droop"),
    # Stroke clinical findings — CA-030 (trigger KB-016/020/021)
    # DIAGNOSTIC type: excluded from symptom lists, kept in NER output for records
    "CT no hemorrhage":            ("DIAGNOSTIC", "CT no hemorrhage"),
    "no hemorrhage":               ("DIAGNOSTIC", "CT no hemorrhage"),
    "tPA contraindicated":         ("DIAGNOSTIC", "tPA contraindicated"),
    "thrombolysis not appropriate":("DIAGNOSTIC", "tPA contraindicated"),
    "thrombectomy":                ("DIAGNOSTIC", "thrombectomy indicated"),
    "endovascular thrombectomy":   ("DIAGNOSTIC", "thrombectomy indicated"),
    "mechanical thrombectomy":     ("DIAGNOSTIC", "thrombectomy indicated"),
    # Pediatric neuro
    "neck stiffness":         ("SYMPTOM", "neck stiffness"),
    "nuchal rigidity":        ("SYMPTOM", "neck stiffness"),
    "bulging fontanelle":     ("SYMPTOM", "neck stiffness"),
    "post-ictal":             ("SYMPTOM", "altered consciousness"),
    "musculoskeletal chest pain": ("SYMPTOM", "musculoskeletal chest pain"),
    "chest wall pain":            ("SYMPTOM", "musculoskeletal chest pain"),
    "costochondritis":            ("SYMPTOM", "musculoskeletal chest pain"),
    # Existing
    "chest pain on exertion":("SYMPTOM", "chest pain on exertion"),
    "exertional chest pain": ("SYMPTOM", "chest pain on exertion"),
    "chest pain":            ("SYMPTOM", "chest pain"),
    "left chest pain":       ("SYMPTOM", "left chest pain"),
    "right chest pain":      ("SYMPTOM", "right chest pain"),
    "headache":              ("SYMPTOM", "headache"),
    "double vision":         ("SYMPTOM", "double vision"),
    "diplopia":              ("SYMPTOM", "double vision"),
    "ataxia":                ("SYMPTOM", "ataxia"),
    "gait instability":      ("SYMPTOM", "ataxia"),
    "vertigo":               ("SYMPTOM", "vertigo"),
    "loss of balance":       ("SYMPTOM", "loss of balance"),
    "dizziness":             ("SYMPTOM", "dizziness"),
    "nausea":                ("SYMPTOM", "nausea"),
    "shortness of breath":   ("SYMPTOM", "shortness of breath"),
    "abdominal pain":        ("SYMPTOM", "abdominal pain"),
    "fever":                 ("SYMPTOM", "fever"),
    "cough":                 ("SYMPTOM", "cough"),
    "fatigue":               ("SYMPTOM", "fatigue"),
    "weakness":              ("SYMPTOM", "weakness"),
    "palpitations":          ("SYMPTOM", "palpitations"),
    "ankle sprain":          ("SYMPTOM", "ankle sprain"),
    "ankle pain":            ("SYMPTOM", "ankle pain"),
    "ankle injury":          ("SYMPTOM", "ankle injury"),
    "back pain":             ("SYMPTOM", "back pain"),
    "joint pain":            ("SYMPTOM", "joint pain"),
    "knee pain":             ("SYMPTOM", "knee pain"),
    "shoulder pain":         ("SYMPTOM", "shoulder pain"),
    "swelling":              ("SYMPTOM", "swelling"),
    "stomach pain":          ("SYMPTOM", "abdominal pain"),
    "bloating":              ("SYMPTOM", "bloating"),
    "respiration":           ("SYMPTOM", "abnormal breathing"),
    "loud breathing":        ("SYMPTOM", "abnormal breathing"),
    # Respiratory / sepsis — CA-027
    "severe pneumonia":       ("SYMPTOM", "severe pneumonia"),
    "mechanical ventilation": ("SYMPTOM", "mechanical ventilation"),
    "endotracheal intubation":("SYMPTOM", "mechanical ventilation"),
    # Trauma / hemorrhage — CA-025 + CA-026
    "head-on collision":      ("SYMPTOM", "trauma"),
    "collision trauma":       ("SYMPTOM", "trauma"),
    "motorcycle accident":    ("SYMPTOM", "trauma"),
    "motor vehicle accident": ("SYMPTOM", "trauma"),
    "severe trauma":          ("SYMPTOM", "trauma"),
    "trauma":                 ("SYMPTOM", "trauma"),
    "fall injury":            ("SYMPTOM", "fall"),
    "multiple rib fractures": ("SYMPTOM", "rib fracture"),
    "rib fracture":           ("SYMPTOM", "rib fracture"),
    "liver laceration":       ("SYMPTOM", "liver laceration"),
    "contusion":              ("SYMPTOM", "contusion"),
    "abdominal distension":   ("SYMPTOM", "abdominal distension"),
    "altered consciousness":  ("SYMPTOM", "altered consciousness"),
    "rapid shallow breathing":("SYMPTOM", "tachypnea"),
    "tachypnea":              ("SYMPTOM", "tachypnea"),
    "major hemorrhage":       ("SYMPTOM", "hemorrhage"),
    "continuous bleeding":    ("SYMPTOM", "hemorrhage"),
    "splenic laceration":     ("SYMPTOM", "splenic laceration"),
    "unconscious":            ("SYMPTOM", "coma"),
    "loss of consciousness":  ("SYMPTOM", "coma"),
    # GI / metabolic symptoms — NER-VOCAB + CA-024
    "polyuria":              ("SYMPTOM", "polyuria"),
    "frequent urination":    ("SYMPTOM", "polyuria"),
    "diarrhea":              ("SYMPTOM", "diarrhea"),
    "loose stool":           ("SYMPTOM", "diarrhea"),
    "nausea and vomiting":   ("SYMPTOM", "nausea and vomiting"),
    "vomiting":              ("SYMPTOM", "nausea and vomiting"),
    "insomnia":              ("SYMPTOM", "insomnia"),
    "difficulty sleeping":   ("SYMPTOM", "insomnia"),
    "dehydration":           ("SYMPTOM", "dehydration"),
    # Emergency / critical — CA-023
    "hypotension":           ("SYMPTOM", "hypotension"),
    "low blood pressure":    ("SYMPTOM", "hypotension"),
    "tachycardia":           ("SYMPTOM", "tachycardia"),
    "bradycardia":           ("SYMPTOM", "bradycardia"),
    "emergency":             ("SYMPTOM", "emergency"),
    "critical condition":    ("SYMPTOM", "critical condition"),
    "myocardial infarction": ("SYMPTOM", "myocardial infarction"),
    "stroke":                ("SYMPTOM", "stroke"),
    "sepsis":                ("SYMPTOM", "sepsis"),
    "coma":                  ("SYMPTOM", "coma"),
    "seizure":               ("SYMPTOM", "seizure"),
    # Dental — @req SRS-L6-006 (MV-FID-016)
    "lower right tooth pain":  ("SYMPTOM", "tooth pain"),
    "lower left tooth pain":   ("SYMPTOM", "tooth pain"),
    "upper right tooth pain":  ("SYMPTOM", "tooth pain"),
    "upper left tooth pain":   ("SYMPTOM", "tooth pain"),
    "lower right tooth decay": ("SYMPTOM", "tooth decay"),
    "lower left tooth decay":  ("SYMPTOM", "tooth decay"),
    "upper right tooth decay": ("SYMPTOM", "tooth decay"),
    "upper left tooth decay":  ("SYMPTOM", "tooth decay"),
    "tooth pain":            ("SYMPTOM", "tooth pain"),
    "toothache":             ("SYMPTOM", "tooth pain"),
    "dental pain":           ("SYMPTOM", "tooth pain"),
    "tooth decay":           ("SYMPTOM", "tooth decay"),
    "dental caries":         ("SYMPTOM", "tooth decay"),
    "gum pain":              ("SYMPTOM", "gum pain"),
    "gum inflammation":      ("SYMPTOM", "gum pain"),
    "tooth sensitivity":     ("SYMPTOM", "tooth sensitivity"),
    "jaw pain":              ("SYMPTOM", "jaw pain"),
    # Gum swelling variants (MarianMT output of "sưng nướu") — @req SRS-L6-008
    "gum swelling":          ("SYMPTOM", "gum pain"),
    "swollen gum":           ("SYMPTOM", "gum pain"),
    "swollen gums":          ("SYMPTOM", "gum pain"),
    # Pediatric / Orthodontic dental — @req SRS-L6-008
    "permanent teeth eruption": ("SYMPTOM", "permanent teeth eruption"),
    "permanent teeth":          ("SYMPTOM", "permanent teeth eruption"),
    "wisdom teeth":             ("SYMPTOM", "wisdom teeth"),
    "wisdom tooth":             ("SYMPTOM", "wisdom teeth"),
    "teething":                 ("SYMPTOM", "teething"),
    "tooth crowding":           ("SYMPTOM", "tooth crowding"),
    "dental crowding":          ("SYMPTOM", "tooth crowding"),
    # Wisdom tooth impaction variants — CA-017
    "impacted wisdom tooth":    ("SYMPTOM", "wisdom teeth"),
    "tooth impaction":          ("SYMPTOM", "wisdom teeth"),
    "wisdom tooth extraction":  ("SYMPTOM", "wisdom teeth"),
}
# NER-B1: VI text → canonical SYMPTOM value (parallel VI NER, longest-match priority)
_VI_SYMPTOM_VOCAB: Dict[str, str] = {
    "đau thắt ngực khi gắng sức": "chest pain on exertion",
    "đau ngực khi gắng sức":      "chest pain on exertion",
    "đau thắt ngực":         "chest pain",
    "thắt ngực":             "chest pain",
    "đau ngực trái":         "left chest pain",
    "đau ngực phải":         "right chest pain",
    "đau cơ ngực":           "musculoskeletal chest pain",
    "đau ngực cơ xương":     "musculoskeletal chest pain",
    "đau ngực":              "chest pain",
    "khó thở":               "shortness of breath",
    "đau bụng":              "abdominal pain",
    "mệt mỏi":               "fatigue",
    "buồn nôn":              "nausea",
    "chóng mặt":             "dizziness",
    "đau đầu":               "headache",
    # Trauma — CA-025 + CA-026
    "bị tông trực diện":     "trauma",
    "bị tông":               "trauma",
    "tai nạn xe máy":        "trauma",
    "tai nạn xe":            "trauma",
    "chấn thương nặng":      "trauma",
    "chấn thương":           "trauma",
    "té ngã":                "fall",
    "dập lá lách":           "splenic laceration",
    "tổn thương gan":        "liver laceration",
    "gãy nhiều xương sườn":  "rib fracture",
    "gãy xương sườn":        "rib fracture",
    "bầm tím":               "contusion",
    "bụng chướng":           "abdominal distension",
    "lơ mơ":                 "altered consciousness",
    "thở nhanh nông":        "tachypnea",
    "thở nhanh":             "tachypnea",
    "mạch nhanh":            "tachycardia",
    "máu ra nhiều":          "hemorrhage",
    "máu chảy liên tục":     "hemorrhage",
    "ngủ mê man":            "coma",
    "mê man":                "coma",
    # Respiratory / sepsis — CA-027
    # Stroke / neuro — CA-029
    "yếu nửa người phải":    "right hemiparesis",
    "yếu nửa người trái":    "left hemiparesis",
    "yếu nửa người":         "hemiparesis",
    "yếu tay phải":          "right arm weakness",
    "yếu tay trái":          "left arm weakness",
    "yếu chân phải":         "right leg weakness",
    "yếu chân trái":         "left leg weakness",
    "liệt nửa người":        "hemiplegia",
    "nói khó":               "dysarthria",
    "nói không rõ":          "dysarthria",
    "méo miệng":             "facial droop",
    "lệch miệng":            "facial droop",
    "nhồi máu não cấp":      "ischemic stroke",
    "nhồi máu não":          "ischemic stroke",
    "xuất huyết não":        "hemorrhagic stroke",
    "cổ gượng":              "neck stiffness",
    # A5: Posterior fossa / cerebellar symptoms
    "nhìn đôi":              "double vision",
    "song thị":              "double vision",
    "loạng choạng":          "ataxia",
    "đi loạng choạng":       "ataxia",
    "mất thăng bằng":        "loss of balance",
    "quay cuồng":            "vertigo",
    "cảm giác quay cuồng":   "vertigo",
    # CT no hemorrhage — multiple phrasings (CA-030/032)
    "ct sọ não không thấy xuất huyết": "CT no hemorrhage",
    "ct không thấy xuất huyết":        "CT no hemorrhage",
    "ct không xuất huyết":             "CT no hemorrhage",
    "ct: không xuất huyết":            "CT no hemorrhage",
    "ct sọ não không xuất huyết":      "CT no hemorrhage",
    "ct: âm tính":                     "CT no hemorrhage",
    "không thấy xuất huyết":           "CT no hemorrhage",
    "chưa thấy xuất huyết":            "CT no hemorrhage",
    "không có xuất huyết":             "CT no hemorrhage",
    # Numbness/sensory — CA-032 (TIA signal)
    "tê nửa mặt phải":   "right facial numbness",
    "tê nửa mặt trái":   "left facial numbness",
    "tê mặt phải":       "right facial numbness",
    "tê mặt trái":       "left facial numbness",
    "tê nửa mặt":        "facial numbness",
    "tê một bên mặt":    "facial numbness",
    "tê nửa người phải": "right hemibody numbness",
    "tê nửa người trái": "left hemibody numbness",
    "tiêu sợi huyết không phù hợp":    "tPA contraindicated",
    "không phù hợp tiêu sợi huyết":    "tPA contraindicated",
    "không chỉ định tiêu sợi huyết":   "tPA contraindicated",
    "chống chỉ định tiêu sợi huyết":   "tPA contraindicated",
    "không tiêu sợi huyết":            "tPA contraindicated",
    "không dùng tiêu sợi huyết":       "tPA contraindicated",
    "lấy huyết khối":                  "thrombectomy indicated",
    "can thiệp mạch não":            "thrombectomy indicated",
    "can thiệp lấy huyết khối":      "thrombectomy indicated",
    # Existing respiratory / sepsis
    "nhiễm khuẩn huyết":     "sepsis",
    "viêm phổi nặng":        "severe pneumonia",
    "nội khí quản":          "mechanical ventilation",
    "thở máy":               "mechanical ventilation",
    "tiểu nhiều lần":        "polyuria",
    "tiều nhiều lần":        "polyuria",
    "tiêu chảy":             "diarrhea",
    "đi cầu tiêu chảy":      "diarrhea",
    "ói nôn mửa":            "nausea and vomiting",
    "nôn mửa":               "nausea and vomiting",
    "khó ngủ":               "insomnia",
    "ngủ khó":               "insomnia",
    "mất nước":              "dehydration",
    "huyết áp thấp":         "hypotension",
    "nhịp tim nhanh":        "tachycardia",
    "nhịp tim chậm":         "bradycardia",
    "nhồi máu cơ tim":       "myocardial infarction",
    "nhiễm trùng huyết":     "sepsis",
    "cấp cứu":               "emergency",
    "đột quỵ":               "stroke",
    "hôn mê":                "coma",
    "co giật":               "seizure",
    "sốt":                   "fever",
    "ho":                    "cough",
    "yếu":                   "weakness",
    "tê":                    "numbness",
    "phù":                   "edema",
}
_HISTORY_KEYWORDS = {
    "hypertension":              "hypertension",
    "diabetes mellitus":         "diabetes mellitus",
    "type 2 diabetes mellitus":  "type 2 diabetes mellitus",
    "diabetes":                  "diabetes",
    "heart disease":             "heart disease",
    "kidney disease":            "kidney disease",
    "asthma":                    "asthma",
    "pneumonia":                 "pneumonia",
    "atrial fibrillation":       "atrial fibrillation",
    "coronary artery disease":   "coronary artery disease",
}
# Regex-based symptom patterns for injury verbs and word-order variants
# Each entry: (compiled_regex, canonical_symptom_value)
_INJURY_PATTERNS: List[tuple] = [
    (re.compile(r'\bsprained?\b[^.]{0,30}\bankle\b|\bankle\b[^.]{0,20}\bsprain', re.IGNORECASE), "ankle sprain"),
    (re.compile(r'\b(?:hurt(?:s|ing)?|pain(?:ful)?)\b[^.]{0,20}\bankle\b|\bankle\b[^.]{0,20}\b(?:hurt|pain)', re.IGNORECASE), "ankle pain"),
    (re.compile(r'\bsprained?\b[^.]{0,30}\bknee\b|\bknee\b[^.]{0,20}\bsprain', re.IGNORECASE), "knee sprain"),
    (re.compile(r'\bstrained?\b[^.]{0,30}\bback\b|\bback\b[^.]{0,20}\bstrain', re.IGNORECASE), "back strain"),
    (re.compile(r'\b(?:loud|noisy|abnormal)\b[^.]{0,20}\brespir|\brespir[^\s]*\b[^.]{0,20}\b(?:loud|noisy|abnormal)', re.IGNORECASE), "abnormal breathing"),
    # Dental regex — catch garbled MarianMT output (teeth + chew/bite/pain/decay variants)
    # @req SRS-L6-006 (MV-FID-016)
    (re.compile(r'\bteet?h\b[^.]{0,60}\b(?:chew|bite|biting|pain|ache|hurt|decay|cav)', re.IGNORECASE), "tooth pain"),
    (re.compile(r'\b(?:chew|bite|biting|pain|ache|hurt)\b[^.]{0,40}\bteet?h\b', re.IGNORECASE), "tooth pain"),
    (re.compile(r'\b(?:dental|tooth|molar|incisor)\b[^.]{0,30}\b(?:pain|ache|hurt|decay|cav)', re.IGNORECASE), "tooth pain"),
]

# CA-019: added "from" (MarianMT output for "từ") + VI triggers + VI time expressions
_ONSET_RE = re.compile(
    r'(?:since|from|for|onset|started?|began?|từ|bắt\s+đầu(?:\s+từ)?|khởi\s+phát(?:\s+từ)?)'
    r'[^,.\n]{0,40}?'
    r'(early morning|this morning|yesterday|today'
    r'|[0-9]+\s+(?:day|hour|week)s?'
    r'|sáng sớm|sáng nay|buổi sáng|hôm qua|hôm nay|tối qua|đêm qua'
    r'|[0-9]+\s+(?:ngày|giờ|tuần))',
    re.IGNORECASE,
)

# ── Vietnamese display maps (MV-FID-017) ─────────────────────────────────────
# @req SRS-L6-007 — used by generate_soap_vi() only; EN path unchanged.

_VI_SYMPTOM_DISPLAY: Dict[str, str] = {
    "chest pain on exertion":   "đau thắt ngực khi gắng sức",
    "chest pain":               "đau ngực",
    "left chest pain":          "đau ngực trái",
    "right chest pain":         "đau ngực phải",
    "headache":                 "đau đầu",
    "double vision":            "nhìn đôi",
    "ataxia":                   "loạng choạng",
    "vertigo":                  "chóng mặt quay cuồng",
    "loss of balance":          "mất thăng bằng",
    "dizziness":                "chóng mặt",
    "nausea":                   "buồn nôn",
    "shortness of breath":      "khó thở",
    "abdominal pain":           "đau bụng",
    "fever":                    "sốt",
    "cough":                    "ho",
    "fatigue":                  "mệt mỏi",
    "weakness":                 "yếu",
    "palpitations":             "hồi hộp",
    "ankle sprain":             "bong gân cổ chân",
    "ankle pain":               "đau cổ chân",
    "back pain":                "đau lưng",
    "joint pain":               "đau khớp",
    "knee pain":                "đau đầu gối",
    "shoulder pain":            "đau vai",
    "swelling":                 "phù",
    "abnormal breathing":       "thở bất thường",
    "bloating":                 "đầy hơi",
    "tooth pain":               "đau răng",
    "tooth decay":              "sâu răng",
    "gum pain":                 "đau nướu",
    "tooth sensitivity":        "ê răng",
    "jaw pain":                 "đau hàm",
    "permanent teeth eruption": "mọc răng vĩnh viễn",
    "wisdom teeth":             "răng khôn",
    "teething":                 "mọc răng",
    "tooth crowding":           "răng mọc lệch",
    # Trauma — CA-025 + CA-026
    "trauma":                   "chấn thương",
    "hemorrhage":               "xuất huyết",
    "splenic laceration":       "dập lá lách",
    "liver laceration":         "tổn thương gan",
    "rib fracture":             "gãy xương sườn",
    "contusion":                "bầm tím",
    "abdominal distension":     "bụng chướng",
    "altered consciousness":    "rối loạn ý thức",
    "tachypnea":                "thở nhanh",
    "fall":                     "té ngã",
    # Stroke clinical findings display — CA-030
    "CT no hemorrhage":          "CT không xuất huyết",
    "tPA contraindicated":       "Tiêu sợi huyết không phù hợp",
    "thrombectomy indicated":    "Chỉ định lấy huyết khối",
    # Numbness/sensory — CA-032
    "right facial numbness":    "tê nửa mặt phải",
    "left facial numbness":     "tê nửa mặt trái",
    "facial numbness":          "tê mặt",
    "right hemibody numbness":  "tê nửa người phải",
    "left hemibody numbness":   "tê nửa người trái",
    # Focal limb weakness — CA-032
    "right arm weakness":       "yếu tay phải",
    "left arm weakness":        "yếu tay trái",
    "right leg weakness":       "yếu chân phải",
    "left leg weakness":        "yếu chân trái",
    # Stroke / neuro — CA-029
    "ischemic stroke":          "nhồi máu não",
    "hemorrhagic stroke":       "xuất huyết não",
    "right hemiparesis":        "yếu nửa người phải",
    "left hemiparesis":         "yếu nửa người trái",
    "hemiparesis":              "yếu nửa người",
    "hemiplegia":               "liệt nửa người",
    "dysarthria":               "nói khó",
    "facial droop":             "méo miệng",
    "neck stiffness":           "cổ gượng",
    # Respiratory / sepsis — CA-027
    "severe pneumonia":         "viêm phổi nặng",
    "mechanical ventilation":   "thở máy",
    # GI / metabolic — CA-024
    "diarrhea":                 "tiêu chảy",
    "polyuria":                 "tiểu nhiều lần",
    "nausea and vomiting":      "buồn nôn và ói mửa",
    "insomnia":                 "mất ngủ",
    "dehydration":              "mất nước",
    # Emergency / critical — CA-023
    "hypotension":              "hạ huyết áp",
    "tachycardia":              "nhịp tim nhanh",
    "bradycardia":              "nhịp tim chậm",
    "emergency":                "cấp cứu",
    "critical condition":       "tình trạng nguy kịch",
    "myocardial infarction":    "nhồi máu cơ tim",
    "stroke":                   "đột quỵ",
    "sepsis":                   "nhiễm trùng huyết",
    "coma":                     "hôn mê",
    "seizure":                  "co giật",
}

_VI_HISTORY_DISPLAY: Dict[str, str] = {
    "hypertension":             "tăng huyết áp",
    "diabetes mellitus":        "đái tháo đường",
    "type 2 diabetes mellitus": "đái tháo đường type 2",
    "diabetes":                 "tiểu đường",
    "heart disease":            "bệnh tim",
    "kidney disease":           "bệnh thận",
    "asthma":                   "hen suyễn",
    "pneumonia":                "viêm phổi",
    "atrial fibrillation":      "rung nhĩ",
    "coronary artery disease":  "bệnh mạch vành",
}

# Values that come from _VI_SYMPTOM_VOCAB but are DIAGNOSTIC findings, not symptoms
_VI_DIAGNOSTIC_VALUES: frozenset = frozenset({
    "CT no hemorrhage", "tPA contraindicated", "thrombectomy indicated",
})

_VI_DDX_DISPLAY: Dict[str, str] = {
    # Cardiac / chest
    "Hypertensive urgency":                        "Tăng huyết áp khẩn cấp",
    "Cardiac ischemia (ACS)":                      "Thiếu máu cơ tim cấp (ACS)",
    "Musculoskeletal chest pain":                  "Đau ngực cơ xương",
    "Costochondritis":                             "Viêm sụn sườn",
    "Cardiac ischemia (ACS) — must exclude":       "Thiếu máu cơ tim (ACS) — cần loại trừ",
    "GERD":                                        "GERD",
    "Pulmonary embolism":                          "Thuyên tắc phổi",
    # Neuro / headache
    "Hypertensive headache":                       "Đau đầu do tăng huyết áp",
    "Vestibular neuritis":                         "Viêm thần kinh tiền đình",
    "Migraine":                                    "Đau nửa đầu (Migraine)",
    "Hyperglycemia":                               "Tăng đường huyết",
    "Tension headache":                            "Đau đầu căng thẳng",
    "Intracranial pathology":                      "Bệnh lý nội sọ",
    # Respiratory
    "Community-acquired pneumonia":                "Viêm phổi mắc phải cộng đồng",
    "Viral URTI":                                  "Nhiễm trùng hô hấp trên do virus",
    "COVID-19":                                    "COVID-19",
    "Bronchitis":                                  "Viêm phế quản",
    "Cardiac failure":                             "Suy tim",
    "Asthma exacerbation":                         "Cơn hen cấp",
    # Trauma — CA-025 + CA-026
    "Liver laceration":                            "Rách gan",
    "Multiple rib fractures":                      "Gãy nhiều xương sườn",
    "Tension pneumothorax":                        "Tràn khí màng phổi có áp lực",
    "Traumatic aortic injury":                     "Chấn thương động mạch chủ",
    "Splenic rupture":                             "Vỡ lách",
    "Internal hemorrhage":                         "Xuất huyết nội",
    "Hemorrhagic shock":                           "Sốc xuất huyết",
    "Traumatic brain injury (TBI)":                "Chấn thương sọ não (TBI)",
    "Traumatic liver laceration":                  "Dập gan do chấn thương",
    "Spinal injury":                               "Chấn thương cột sống",
    "Rib fracture":                                "Gãy xương sườn",
    "Pneumothorax":                                "Tràn khí màng phổi",
    "Hemothorax":                                  "Tràn máu màng phổi",
    "Flail chest":                                 "Mảng sườn di động",
    "Liver laceration with hemorrhage":            "Rách gan kèm xuất huyết",
    "Hepatic injury":                              "Chấn thương gan",
    # Respiratory / sepsis — CA-027
    "Septic shock from pneumonia":                 "Sốc nhiễm trùng từ viêm phổi",
    "Community-acquired pneumonia with sepsis":    "Viêm phổi mắc phải cộng đồng kèm nhiễm khuẩn huyết",
    "Hospital-acquired pneumonia":                 "Viêm phổi bệnh viện",
    "COVID-19 pneumonia":                          "Viêm phổi COVID-19",
    "Severe community-acquired pneumonia":         "Viêm phổi mắc phải cộng đồng nặng",
    "ARDS":                                        "Hội chứng suy hô hấp cấp (ARDS)",
    "Pulmonary sepsis":                            "Nhiễm khuẩn huyết từ phổi",
    # GI — CA-024
    "Acute gastroenteritis":                       "Viêm dạ dày ruột cấp",
    "Acute gastroenteritis with dehydration":      "Viêm dạ dày ruột cấp kèm mất nước",
    "Food poisoning":                              "Ngộ độc thực phẩm",
    "Irritable bowel syndrome (IBS)":              "Hội chứng ruột kích thích",
    "Inflammatory bowel disease (IBD)":            "Bệnh viêm ruột (IBD)",
    "Infectious diarrhea":                         "Tiêu chảy nhiễm trùng",
    "Cholera":                                     "Tả (Cholera)",
    "Diabetes insipidus":                          "Đái tháo nhạt",
    "Peptic ulcer disease":                        "Loét dạ dày tá tràng",
    "Appendicitis":                                "Viêm ruột thừa",
    "Cholecystitis":                               "Viêm túi mật",
    "IBS":                                         "Hội chứng ruột kích thích (IBS)",
    # Vestibular / MSK
    "Benign paroxysmal positional vertigo (BPPV)": "Chóng mặt tư thế lành tính (BPPV)",
    "Orthostatic hypotension":                     "Hạ huyết áp tư thế đứng",
    "Central cause":                               "Nguyên nhân trung ương",
    "Lateral ankle ligament sprain (ATFL)":        "Bong gân dây chằng cổ chân ngoài (ATFL)",
    "Fracture (Ottawa criteria)":                  "Gãy xương (tiêu chuẩn Ottawa)",
    "Peroneal tendon injury":                      "Chấn thương gân mác",
    "Lateral ankle ligament sprain":               "Bong gân dây chằng cổ chân ngoài",
    "Fracture":                                    "Gãy xương",
    "Tendinopathy":                                "Bệnh lý gân",
    "Gout":                                        "Gout",
    # MSK shoulder — CA-032
    "Rotator cuff injury":                         "Tổn thương chóp xoay",
    "Shoulder impingement syndrome":               "Hội chứng chèn ép vai",
    "Acromioclavicular joint sprain":              "Bong gân khớp cùng đòn",
    "Mechanical low back pain":                    "Đau lưng cơ học",
    "Lumbar disc herniation":                      "Thoát vị đĩa đệm thắt lưng",
    "Muscle strain":                               "Căng cơ",
    "Vertebral fracture":                          "Gãy đốt sống",
    # Dental
    "Dental caries":                               "Sâu răng",
    "Pulpitis":                                    "Viêm tủy răng",
    "Periapical abscess":                          "Áp xe quanh chóp răng",
    "Periodontal disease":                         "Bệnh nha chu",
    "Cracked tooth syndrome":                      "Hội chứng răng nứt",
    "Dentine hypersensitivity":                    "Quá cảm ngà răng",
    "Enamel erosion":                              "Mòn men răng",
    "Gingivitis":                                  "Viêm lợi",
    "Periodontitis":                               "Viêm nha chu",
    "Pericoronitis":                               "Viêm lợi trùm",
    "Dental abscess":                              "Áp xe răng",
    "Temporomandibular joint disorder (TMJ)":      "Rối loạn khớp thái dương hàm (TMJ)",
    "Trigeminal neuralgia":                        "Đau dây thần kinh sinh ba",
    "Bruxism":                                     "Nghiến răng",
    # Pediatric dental (CA-016)
    "Normal permanent tooth eruption":             "Mọc răng vĩnh viễn bình thường",
    "Delayed eruption":                            "Mọc răng chậm",
    "Ectopic eruption":                            "Mọc răng lệch vị trí",
    "Space management concern":                    "Vấn đề quản lý khoảng cách răng",
    "Dental crowding":                             "Răng mọc chen chúc",
    "Arch length deficiency":                      "Thiếu khoảng cung hàm",
    "Wisdom tooth impaction":                      "Răng khôn mọc ngầm",
    "Normal wisdom tooth eruption":                "Răng khôn mọc bình thường",
    "Normal deciduous tooth eruption":             "Mọc răng sữa bình thường",
    "Teething discomfort":                         "Khó chịu khi mọc răng",
    # Emergency / critical — CA-023
    "Hypoglycaemia":                             "Hạ đường huyết",
    "Diabetic ketoacidosis (DKA)":               "Nhiễm toan ceton đái tháo đường (DKA)",
    "Septic shock":                              "Sốc nhiễm trùng",
    "Cardiogenic shock":                         "Sốc tim",
    "Orthostatic hypotension":                   "Hạ huyết áp tư thế đứng",
    "Dehydration":                               "Mất nước",
    "Anaphylaxis":                               "Phản vệ",
    "Supraventricular tachycardia (SVT)":        "Nhịp nhanh trên thất (SVT)",
    "Hyperthyroidism":                           "Cường giáp",
    "ST-elevation MI (STEMI)":                   "Nhồi máu cơ tim ST chênh lên (STEMI)",
    "Non-ST-elevation MI (NSTEMI)":              "Nhồi máu cơ tim không ST chênh lên (NSTEMI)",
    "Stable angina":                             "Đau thắt ngực ổn định",
    "Unstable angina":                           "Đau thắt ngực không ổn định",
    "Cerebellar stroke":                         "Đột quỵ tiểu não",
    "Vertebrobasilar TIA":                       "Cơn thiếu máu não thoáng qua thân não",
    "Brainstem stroke":                          "Đột quỵ thân não",
    "Brainstem lesion":                          "Tổn thương thân não",
    "Posterior fossa lesion":                    "Tổn thương hố sau",
    "Multiple sclerosis":                        "Bệnh đa xơ cứng",
    "Myasthenia gravis":                         "Nhược cơ",
    "Ischemic stroke":                           "Đột quỵ thiếu máu cục bộ",
    "Ischaemic stroke":                          "Đột quỵ thiếu máu cục bộ",
    "Haemorrhagic stroke":                       "Đột quỵ xuất huyết",
    "TIA":                                       "Cơn thiếu máu não thoáng qua (TIA)",
    "Bacteraemia":                               "Nhiễm khuẩn huyết",
    "Urinary tract infection":                   "Nhiễm trùng đường tiết niệu",
    # Fallback
    "Undifferentiated presenting complaint — further evaluation required":
        "Triệu chứng chưa phân loại — cần đánh giá thêm",
}

_VI_PLAN_DISPLAY: Dict[str, str] = {
    "ECG":                                                    "ECG",
    "ECG to rule out ischemia":                               "ECG loại trừ thiếu máu cơ tim",
    "Troponin if cardiac ischemia suspected":                 "Troponin nếu nghi ngờ thiếu máu cơ tim",
    "CXR":                                                    "X-quang ngực (CXR)",
    "Review antihypertensive regimen if BP persistently elevated":
        "Xem xét phác đồ hạ áp nếu huyết áp tiếp tục cao",
    "Refer to cardiology if ECG changes present":             "Chuyển tim mạch nếu ECG thay đổi",
    "Check BP and BGL":                                       "Kiểm tra huyết áp và đường huyết",
    "Consider neurological examination if BP elevated":       "Xem xét khám thần kinh nếu tăng huyết áp",
    "Follow-up in 48h if not improving":                      "Tái khám sau 48 giờ nếu không cải thiện",
    "Check BP":                                               "Kiểm tra huyết áp",
    "Neurological exam":                                      "Khám thần kinh",
    "Reassess if worsening or red flags emerge":              "Đánh giá lại nếu nặng hơn hoặc có dấu hiệu nguy hiểm",
    "CXR if productive cough":                                "CXR nếu ho có đờm",
    "Sputum culture if purulent":                             "Cấy đờm nếu có mủ",
    "Isolate if viral infection suspected":                   "Cách ly nếu nghi nhiễm virus",
    "O2 sats":                                               "SpO2",
    "BNP if cardiac failure suspected":                       "BNP nếu nghi ngờ suy tim",
    "Abdominal exam":                                         "Khám bụng",
    "FBC and CRP":                                            "CTM và CRP",
    "Urine dipstick":                                         "Tổng phân tích nước tiểu",
    "Consider surgical review if signs of peritonism":
        "Hội chẩn ngoại nếu có dấu hiệu viêm phúc mạc",
    "Dix-Hallpike test":                                      "Nghiệm pháp Dix-Hallpike",
    "Orthostatic BP check":                                   "Kiểm tra huyết áp tư thế",
    "Neurological screen":                                    "Sàng lọc thần kinh",
    "Ottawa Ankle Rules — X-ray if indicated":                "Quy tắc Ottawa — X-quang nếu chỉ định",
    "RICE: Rest Ice Compression Elevation":                   "RICE: Nghỉ, Chườm lạnh, Băng ép, Nâng cao",
    "Shoulder X-ray if acute trauma":                         "X-quang vai nếu chấn thương cấp",
    "Rest + ice":                                             "Nghỉ ngơi và chườm lạnh",
    "Review in 1-2 weeks":                                    "Tái khám sau 1-2 tuần",
    "Physiotherapy referral if grade II/III sprain":          "Vật lý trị liệu nếu bong gân độ II/III",
    "Ottawa Ankle Rules":                                     "Quy tắc Ottawa cổ chân",
    "Uric acid if gout suspected":                            "Uric acid nếu nghi gout",
    "Weight-bearing assessment":                              "Đánh giá chịu lực",
    "Red flag screen (cauda equina)":                         "Sàng lọc dấu hiệu nguy hiểm (đuôi ngựa)",
    "Analgesia":                                              "Giảm đau",
    "Physiotherapy":                                          "Vật lý trị liệu",
    "X-ray if >6 weeks or red flags":                         "X-quang nếu >6 tuần hoặc có dấu hiệu nguy hiểm",
    "Dental X-ray (periapical)":                              "X-quang răng (quanh chóp)",
    "Refer to dentist":                                       "Chuyển khám nha sĩ",
    "Analgesia if required":                                  "Giảm đau nếu cần",
    "Dental X-ray":                                           "X-quang răng",
    "Refer to dentist for restoration or extraction":         "Chuyển nha sĩ để trám hoặc nhổ răng",
    "Dental examination":                                     "Khám nha khoa",
    "Oral hygiene review":                                    "Hướng dẫn vệ sinh răng miệng",
    "Desensitising toothpaste":                               "Kem đánh răng chống ê buốt",
    "TMJ assessment":                                         "Đánh giá khớp thái dương hàm",
    "Refer to dentist or oral surgery":                       "Chuyển nha sĩ hoặc phẫu thuật miệng",
    # Pediatric dental (CA-016)
    "Panoramic X-ray (OPG) assessment":                       "X-quang toàn cảnh (OPG)",
    "Orthodontic evaluation":                                 "Khám chỉnh nha",
    "Monitor eruption sequence":                              "Theo dõi trình tự mọc răng",
    "Panoramic X-ray (OPG)":                                  "X-quang toàn cảnh (OPG)",
    "Orthodontic consultation":                               "Tư vấn chỉnh nha",
    "Space maintainer assessment":                            "Đánh giá khí cụ giữ khoảng",
    "Refer to oral surgery if impacted":                      "Chuyển phẫu thuật miệng nếu mọc ngầm",
    "Reassurance — teething is normal":                       "Giải thích — mọc răng là bình thường",
    "Topical gum gel if discomfort":                          "Gel bôi nướu nếu khó chịu",
    "Routine dental review":                                  "Tái khám nha khoa định kỳ",
    # Respiratory / sepsis plan — CA-027
    "IV antibiotics broad-spectrum":                          "Kháng sinh phổ rộng đường tĩnh mạch",
    "ICU review":                                             "Hội chẩn ICU",
    "ICU review if SpO2 <90%":                                "Hội chẩn ICU nếu SpO2 <90%",
    # Trauma plan — CA-025 + CA-026
    "Urgent thoracic surgery review":                         "Hội chẩn phẫu thuật lồng ngực khẩn",
    "Chest tube insertion":                                   "Đặt dẫn lưu ngực",
    "Intubation if GCS ≤8":                                   "Đặt nội khí quản nếu GCS ≤8",
    "SpO2 monitoring":                                        "Theo dõi SpO2",
    "Urgent surgical review":                                 "Hội chẩn ngoại khẩn cấp",
    "Type and crossmatch blood":                              "Nhóm máu và phản ứng chéo",
    "Trauma team activation":                                 "Kích hoạt đội cấp cứu chấn thương",
    "CT head and abdomen":                                    "CT đầu và bụng",
    "Spinal precautions":                                     "Bảo vệ cột sống",
    "Urgent CT abdomen":                                      "CT bụng khẩn cấp",
    "Chest X-ray":                                            "X-quang ngực",
    "Focused Assessment Sonography for Trauma (FAST)":        "Siêu âm FAST",
    # GI / metabolic plan — CA-024
    "Stool culture if bloody diarrhea":                       "Cấy phân nếu tiêu chảy có máu",
    "Oral rehydration therapy":                               "Bù dịch đường uống (ORS)",
    "Review diet and medications":                            "Xem lại chế độ ăn và thuốc",
    "FBC and electrolytes":                                   "CTM và điện giải đồ",
    "IV fluids if severe dehydration":                        "Truyền dịch nếu mất nước nặng",
    "Stool culture":                                          "Cấy phân",
    "Fasting BGL":                                            "Đường huyết lúc đói",
    "HbA1c":                                                  "HbA1c",
    "Renal function tests":                                   "Xét nghiệm chức năng thận",
    # Emergency — CA-023
    "Check BGL urgently":                                     "Kiểm tra đường huyết khẩn",
    "IV access + fluid resuscitation":                        "Lập đường truyền tĩnh mạch + bù dịch",
    "Urgent medical review":                                  "Hội chẩn khẩn cấp",
    "Thrombolysis assessment if ischaemic":                   "Đánh giá tiêu sợi huyết nếu thiếu máu cục bộ",
    "CT head urgently":                                       "CT não khẩn cấp",
    "Neurology referral":                                     "Chuyển thần kinh học",
    "Blood cultures x2":                                      "Cấy máu x2",
    "IV antibiotics":                                         "Kháng sinh đường tĩnh mạch",
    "IV fluids":                                              "Truyền dịch tĩnh mạch",
    "Thyroid function tests":                                 "Xét nghiệm chức năng tuyến giáp",
    "Aspirin 300mg":                                          "Aspirin 300mg",
    "Urgent cardiology referral":                             "Chuyển tim mạch khẩn cấp",
    "Check BGL":                                              "Kiểm tra đường huyết",
    # Fallbacks
    "Further clinical assessment":                            "Đánh giá lâm sàng thêm",
    "Investigations as indicated":                            "Xét nghiệm theo chỉ định",
    "Follow-up as clinically required":                       "Tái khám theo chỉ định lâm sàng",
}

# ── Differential diagnosis table ──────────────────────────────────────────────
# Key: frozenset of symptom + condition signals → (differentials, plan additions)
_DIFFERENTIALS = [
    (
        {"chest pain", "hypertension"},
        ["Hypertensive urgency", "Cardiac ischemia (ACS)", "Musculoskeletal chest pain"],
        ["ECG to rule out ischemia", "Review antihypertensive regimen if BP persistently elevated",
         "Refer to cardiology if ECG changes present"],
    ),
    # CA-032: Musculoskeletal chest pain — specific rule (scores higher than generic chest pain)
    (
        {"musculoskeletal chest pain"},
        ["Musculoskeletal chest pain", "Costochondritis", "Muscle strain",
         "Cardiac ischemia (ACS) — must exclude"],
        ["ECG to rule out ischemia", "Troponin if any cardiac features",
         "Analgesia (NSAID)", "Rest", "Physiotherapy if prolonged"],
    ),
    (
        {"chest pain on exertion"},
        ["Unstable angina", "Stable angina", "Cardiac ischemia (ACS)",
         "Pulmonary embolism", "Musculoskeletal chest pain"],
        ["ECG", "Troponin", "Stress test", "Cardiology referral",
         "CXR", "Aspirin if angina confirmed"],
    ),
    (
        {"chest pain"},
        ["Cardiac ischemia (ACS)", "Musculoskeletal chest pain", "GERD", "Pulmonary embolism"],
        ["ECG", "Troponin if cardiac ischemia suspected", "CXR"],
    ),
    (
        {"headache", "dizziness", "nausea"},
        ["Hypertensive headache", "Vestibular neuritis", "Migraine", "Hyperglycemia"],
        ["Check BP and BGL", "Consider neurological examination if BP elevated",
         "Follow-up in 48h if not improving"],
    ),
    (
        {"headache"},
        ["Tension headache", "Migraine", "Hypertensive headache", "Intracranial pathology"],
        ["Check BP", "Neurological exam", "Reassess if worsening or red flags emerge"],
    ),
    (
        {"sepsis", "cough", "fever"},
        ["Septic shock from pneumonia", "Community-acquired pneumonia with sepsis",
         "Hospital-acquired pneumonia", "COVID-19 pneumonia"],
        ["Blood cultures x2", "IV antibiotics", "IV fluids", "SpO2 monitoring",
         "Urgent medical review", "FBC and CRP", "Chest X-ray"],
    ),
    (
        {"severe pneumonia", "tachypnea"},
        ["Severe community-acquired pneumonia", "ARDS", "Pulmonary sepsis", "COVID-19"],
        ["Blood cultures x2", "IV antibiotics broad-spectrum", "SpO2 monitoring",
         "FBC and CRP", "Chest X-ray", "ICU review"],
    ),
    (
        {"cough", "fever"},
        ["Community-acquired pneumonia", "Viral URTI", "COVID-19", "Bronchitis"],
        ["CXR if productive cough", "Sputum culture if purulent", "Isolate if viral infection suspected"],
    ),
    (
        {"shortness of breath"},
        ["Cardiac failure", "Pneumonia", "Pulmonary embolism", "Asthma exacerbation"],
        ["O2 sats", "CXR", "ECG", "BNP if cardiac failure suspected"],
    ),
    (
        {"abdominal pain"},
        ["Peptic ulcer disease", "Appendicitis", "Cholecystitis", "IBS"],
        ["Abdominal exam", "FBC and CRP", "Urine dipstick", "Consider surgical review if signs of peritonism"],
    ),
    (
        {"dysarthria", "ataxia"},
        ["Cerebellar stroke", "Vertebrobasilar TIA", "Ischemic stroke", "Multiple sclerosis",
         "Posterior fossa lesion"],
        ["CT/MRI brain urgent", "Neurology referral", "Stroke unit assessment",
         "Glucose check", "ECG"],
    ),
    (
        {"double vision", "ataxia"},
        ["Cerebellar stroke", "Vertebrobasilar TIA", "Multiple sclerosis",
         "Posterior fossa lesion", "Myasthenia gravis"],
        ["CT/MRI brain urgent", "Neurology referral", "Stroke unit assessment"],
    ),
    (
        {"double vision", "dysarthria"},
        ["Vertebrobasilar TIA", "Cerebellar stroke", "Brainstem stroke",
         "Multiple sclerosis"],
        ["CT/MRI brain urgent", "Neurology referral", "Stroke unit assessment"],
    ),
    (
        {"vertigo", "dysarthria"},
        ["Vertebrobasilar TIA", "Cerebellar stroke", "Brainstem lesion"],
        ["CT/MRI brain urgent", "Neurology referral", "Stroke unit assessment"],
    ),
    (
        {"dizziness"},
        ["Benign paroxysmal positional vertigo (BPPV)", "Orthostatic hypotension",
         "Vestibular neuritis", "Central cause"],
        ["Dix-Hallpike test", "Orthostatic BP check", "Neurological screen"],
    ),
    (
        {"ankle sprain"},
        ["Lateral ankle ligament sprain (ATFL)", "Fracture (Ottawa criteria)", "Peroneal tendon injury"],
        ["Ottawa Ankle Rules — X-ray if indicated", "RICE: Rest Ice Compression Elevation",
         "Physiotherapy referral if grade II/III sprain"],
    ),
    (
        {"ankle pain"},
        ["Lateral ankle ligament sprain", "Fracture", "Tendinopathy", "Gout"],
        ["Ottawa Ankle Rules", "Uric acid if gout suspected", "Weight-bearing assessment"],
    ),
    (
        {"back pain"},
        ["Mechanical low back pain", "Lumbar disc herniation", "Muscle strain", "Vertebral fracture"],
        ["Red flag screen (cauda equina)", "Analgesia", "Physiotherapy", "X-ray if >6 weeks or red flags"],
    ),
    # CA-032: MSK shoulder
    (
        {"shoulder pain"},
        ["Rotator cuff injury", "Shoulder impingement syndrome",
         "Acromioclavicular joint sprain", "Muscle strain"],
        ["Shoulder X-ray if acute trauma", "Analgesia (NSAID)",
         "Rest + ice", "Physiotherapy referral", "Review in 1-2 weeks"],
    ),
    # Emergency / critical — CA-023
    (
        {"hypotension", "diabetes mellitus"},
        ["Hypoglycaemia", "Diabetic ketoacidosis (DKA)", "Septic shock", "Cardiogenic shock"],
        ["Check BGL urgently", "IV access + fluid resuscitation", "ECG", "FBC and CRP", "Urgent medical review"],
    ),
    (
        {"hypotension"},
        ["Orthostatic hypotension", "Septic shock", "Cardiogenic shock", "Dehydration", "Anaphylaxis"],
        ["IV access + fluid resuscitation", "ECG", "Check BGL", "Urgent medical review"],
    ),
    (
        {"tachycardia"},
        ["Sepsis", "Dehydration", "Atrial fibrillation", "Supraventricular tachycardia (SVT)", "Hyperthyroidism"],
        ["ECG", "FBC and CRP", "Thyroid function tests", "Urgent medical review"],
    ),
    (
        {"myocardial infarction"},
        ["ST-elevation MI (STEMI)", "Non-ST-elevation MI (NSTEMI)", "Unstable angina"],
        ["ECG urgently", "Troponin", "Aspirin 300mg", "Urgent cardiology referral"],
    ),
    # CA-032: Facial/hemibody numbness → TIA/stroke DDx
    (
        {"right facial numbness"},
        ["TIA — right facial sensory cortex", "Lacunar infarct", "Ischaemic stroke"],
        ["CT head urgently", "MRI brain if CT negative",
         "Neurology referral", "ABCD2 risk stratification", "Stroke unit if TIA confirmed"],
    ),
    (
        {"left facial numbness"},
        ["TIA — left facial sensory cortex", "Lacunar infarct", "Ischaemic stroke"],
        ["CT head urgently", "MRI brain if CT negative",
         "Neurology referral", "ABCD2 risk stratification", "Stroke unit if TIA confirmed"],
    ),
    (
        {"facial numbness"},
        ["TIA", "Lacunar infarct", "Ischaemic stroke — sensory", "Peripheral facial neuropathy"],
        ["CT head urgently", "Neurology referral",
         "ABCD2 risk stratification", "Stroke unit if TIA confirmed"],
    ),
    (
        {"right hemibody numbness"},
        ["TIA", "Lacunar infarct — thalamic/capsular", "Ischaemic stroke"],
        ["CT head urgently", "MRI brain", "Neurology referral", "Stroke unit admission"],
    ),
    # CA-032: Focal limb weakness → stroke/TIA DDx
    (
        {"right arm weakness"},
        ["Ischaemic stroke", "TIA", "Haemorrhagic stroke", "Todd's paresis"],
        ["CT head urgently", "Neurology referral", "Check BGL urgently",
         "Thrombolysis assessment if ischaemic", "Stroke unit admission"],
    ),
    (
        {"left arm weakness"},
        ["Ischaemic stroke", "TIA", "Haemorrhagic stroke", "Todd's paresis"],
        ["CT head urgently", "Neurology referral", "Check BGL urgently",
         "Thrombolysis assessment if ischaemic", "Stroke unit admission"],
    ),
    (
        {"right leg weakness"},
        ["Ischaemic stroke", "TIA", "Lacunar infarct", "Todd's paresis"],
        ["CT head urgently", "Neurology referral", "Check BGL urgently",
         "Thrombolysis assessment if ischaemic", "Stroke unit admission"],
    ),
    (
        {"left leg weakness"},
        ["Ischaemic stroke", "TIA", "Lacunar infarct", "Todd's paresis"],
        ["CT head urgently", "Neurology referral", "Check BGL urgently",
         "Thrombolysis assessment if ischaemic", "Stroke unit admission"],
    ),
    # CA-032: CT no hemorrhage alone → ischemic stroke workup
    (
        {"ct no hemorrhage"},
        ["Ischaemic stroke", "TIA", "Haemorrhagic stroke excluded by CT"],
        ["CT head urgently", "Neurology referral",
         "Thrombolysis assessment if ischaemic", "Stroke unit admission"],
    ),
    # Stroke clinical findings — CA-030 (KB-016/020/021 triggers)
    (
        {"ischemic stroke", "tPA contraindicated", "thrombectomy indicated"},
        ["Cardioembolic ischaemic stroke on anticoagulation",
         "Large vessel occlusion (LVO) — thrombectomy candidate",
         "Ischaemic stroke — tPA excluded"],
        ["CT head urgently", "CTA head and neck (confirm LVO)",
         "Mechanical thrombectomy assessment (NIHSS + ASPECTS)",
         "No tPA — anticoagulant contraindication",
         "BP management target <185/110", "Stroke unit admission",
         "Neurology + interventional radiology referral",
         "Continue/review anticoagulation post-event"],
    ),
    (
        {"ischemic stroke", "CT no hemorrhage", "tPA contraindicated"},
        ["Cardioembolic ischaemic stroke — CT negative for haemorrhage",
         "Ischaemic stroke on anticoagulation — thrombectomy pathway"],
        ["CTA head and neck urgently", "Mechanical thrombectomy assessment",
         "No tPA — anticoagulant use", "BP management",
         "Stroke unit admission", "Neurology referral"],
    ),
    (
        {"CT no hemorrhage", "thrombectomy indicated"},
        ["LVO ischaemic stroke — CT confirmed", "Thrombectomy candidate"],
        ["CTA to confirm vessel occlusion", "Mechanical thrombectomy",
         "BP management", "Stroke unit", "Neurology referral"],
    ),
    # Stroke / neuro — CA-029
    (
        {"ischemic stroke", "atrial fibrillation"},
        ["Cardioembolic ischaemic stroke", "Ischaemic stroke", "TIA", "Haemorrhagic stroke"],
        ["CT head urgently", "Neurology referral", "No tPA if on anticoagulant",
         "Mechanical thrombectomy assessment", "BP management (target <185/110 pre-thrombolysis)",
         "Fasting BGL", "ECG", "Urgent cardiology referral"],
    ),
    (
        {"ischemic stroke"},
        ["Ischaemic stroke", "Haemorrhagic stroke", "TIA", "Hypoglycaemia"],
        ["CT head urgently", "Neurology referral", "Thrombolysis assessment if ischaemic",
         "Check BGL urgently", "BP management", "Stroke unit admission"],
    ),
    (
        {"hemiparesis", "atrial fibrillation"},
        ["Cardioembolic ischaemic stroke", "Ischaemic stroke", "TIA"],
        ["CT head urgently", "Neurology referral", "No tPA if on anticoagulant",
         "Mechanical thrombectomy assessment", "ECG"],
    ),
    (
        {"hemiparesis", "dysarthria"},
        ["Ischaemic stroke", "Haemorrhagic stroke", "TIA", "Todd's paresis"],
        ["CT head urgently", "Neurology referral", "Thrombolysis assessment",
         "Check BGL urgently", "Stroke unit admission"],
    ),
    (
        {"right hemiparesis"}, ["Ischaemic stroke", "Haemorrhagic stroke", "TIA"],
        ["CT head urgently", "Neurology referral", "Thrombolysis assessment if ischaemic",
         "Check BGL urgently", "Stroke unit admission"],
    ),
    (
        {"stroke"},
        ["Ischaemic stroke", "Haemorrhagic stroke", "TIA"],
        ["CT head urgently", "Neurology referral", "Thrombolysis assessment if ischaemic"],
    ),
    # CNS / meningitis — CA-029 (pediatric + adult)
    (
        {"fever", "seizure", "altered consciousness"},
        ["Bacterial meningitis", "Viral encephalitis", "Febrile seizure with complication",
         "Cerebral abscess", "Septic shock"],
        ["CT head before LP", "Lumbar puncture", "IV antibiotics (cefotaxime/ceftriaxone)",
         "Dexamethasone IV", "Seizure protocol (diazepam IV)", "ICU review", "Check BGL"],
    ),
    (
        {"neck stiffness", "fever"},
        ["Bacterial meningitis", "Viral meningitis", "Viral encephalitis"],
        ["CT head before LP if focal neurology", "Lumbar puncture",
         "IV antibiotics empirical", "Dexamethasone IV", "Isolate"],
    ),
    (
        {"sepsis"},
        ["Septic shock", "Bacteraemia", "Community-acquired pneumonia", "Urinary tract infection"],
        ["FBC and CRP", "Blood cultures x2", "IV antibiotics", "IV fluids", "Urgent medical review"],
    ),
    # Trauma / hemorrhage — CA-025 + CA-026
    (
        {"trauma", "tachycardia", "hypotension"},
        ["Hemorrhagic shock", "Splenic rupture", "Internal hemorrhage", "Liver laceration"],
        ["Trauma team activation", "IV access + fluid resuscitation", "Type and crossmatch blood",
         "Focused Assessment Sonography for Trauma (FAST)", "Urgent CT abdomen",
         "Urgent surgical review"],
    ),
    (
        {"trauma", "tachycardia"},
        ["Hemorrhagic shock", "Internal hemorrhage", "Pneumothorax", "Rib fracture"],
        ["Trauma team activation", "IV access + fluid resuscitation",
         "Focused Assessment Sonography for Trauma (FAST)", "Chest X-ray", "SpO2 monitoring"],
    ),
    (
        {"trauma", "rib fracture", "tachypnea"},
        ["Pneumothorax", "Hemothorax", "Flail chest", "Multiple rib fractures"],
        ["Chest X-ray", "SpO2 monitoring", "Urgent thoracic surgery review",
         "IV access + fluid resuscitation"],
    ),
    (
        {"trauma", "liver laceration"},
        ["Liver laceration with hemorrhage", "Hepatic injury", "Internal hemorrhage"],
        ["Urgent surgical review", "Focused Assessment Sonography for Trauma (FAST)",
         "Urgent CT abdomen", "Type and crossmatch blood"],
    ),
    (
        {"trauma", "hemorrhage", "splenic laceration"},
        ["Splenic rupture", "Internal hemorrhage", "Hemorrhagic shock", "Traumatic liver laceration"],
        ["Trauma team activation", "Urgent surgical review", "IV access + fluid resuscitation",
         "Type and crossmatch blood", "Focused Assessment Sonography for Trauma (FAST)", "Urgent CT abdomen"],
    ),
    (
        {"trauma", "hemorrhage"},
        ["Internal hemorrhage", "Hemorrhagic shock", "Splenic rupture", "Hemothorax"],
        ["Trauma team activation", "IV access + fluid resuscitation", "Type and crossmatch blood",
         "Focused Assessment Sonography for Trauma (FAST)", "Urgent CT abdomen"],
    ),
    (
        {"trauma", "coma"},
        ["Traumatic brain injury (TBI)", "Hemorrhagic shock", "Internal hemorrhage", "Spinal injury"],
        ["Trauma team activation", "CT head and abdomen", "Spinal precautions",
         "IV access + fluid resuscitation", "Urgent surgical review"],
    ),
    (
        {"trauma"},
        ["Traumatic brain injury (TBI)", "Internal hemorrhage", "Rib fracture", "Spinal injury"],
        ["Trauma team activation", "CT head and abdomen", "Spinal precautions", "Chest X-ray"],
    ),
    # GI / metabolic — CA-024
    (
        {"diarrhea", "dehydration"},
        ["Acute gastroenteritis with dehydration", "Food poisoning", "Infectious diarrhea", "Cholera"],
        ["IV fluids if severe dehydration", "Stool culture", "FBC and electrolytes", "Oral rehydration therapy"],
    ),
    (
        {"diarrhea"},
        ["Acute gastroenteritis", "Food poisoning", "Irritable bowel syndrome (IBS)", "Inflammatory bowel disease (IBD)"],
        ["Stool culture if bloody diarrhea", "FBC and CRP", "Oral rehydration therapy", "Review diet and medications"],
    ),
    (
        {"polyuria"},
        ["Diabetes mellitus", "Hyperglycemia", "Diabetes insipidus", "Urinary tract infection"],
        ["Fasting BGL", "HbA1c", "Urine dipstick", "Renal function tests"],
    ),
    # Dental — @req SRS-L6-006 (MV-FID-016)
    (
        {"tooth pain", "tooth decay"},
        ["Dental caries", "Pulpitis", "Periapical abscess", "Periodontal disease"],
        ["Dental X-ray (periapical)", "Refer to dentist", "Analgesia if required"],
    ),
    (
        {"tooth pain"},
        ["Dental caries", "Pulpitis", "Cracked tooth syndrome", "Dentine hypersensitivity"],
        ["Dental X-ray (periapical)", "Refer to dentist", "Analgesia if required"],
    ),
    (
        {"tooth decay"},
        ["Dental caries", "Enamel erosion", "Pulpitis"],
        ["Dental X-ray", "Refer to dentist for restoration or extraction"],
    ),
    (
        {"gum pain"},
        ["Gingivitis", "Periodontitis", "Pericoronitis", "Dental abscess"],
        ["Dental examination", "Refer to dentist", "Oral hygiene review"],
    ),
    (
        {"tooth sensitivity"},
        ["Dentine hypersensitivity", "Enamel erosion", "Dental caries", "Cracked tooth"],
        ["Dental examination", "Desensitising toothpaste", "Refer to dentist"],
    ),
    (
        {"jaw pain"},
        ["Temporomandibular joint disorder (TMJ)", "Dental abscess", "Trigeminal neuralgia", "Bruxism"],
        ["TMJ assessment", "Dental X-ray", "Refer to dentist or oral surgery"],
    ),
    # Pediatric / Orthodontic dental — @req SRS-L6-008 (CA-016)
    (
        {"permanent teeth eruption"},
        ["Normal permanent tooth eruption", "Delayed eruption", "Ectopic eruption", "Space management concern"],
        ["Panoramic X-ray (OPG) assessment", "Orthodontic evaluation", "Monitor eruption sequence"],
    ),
    (
        {"tooth crowding"},
        ["Dental crowding", "Arch length deficiency", "Ectopic eruption"],
        ["Panoramic X-ray (OPG)", "Orthodontic consultation", "Space maintainer assessment"],
    ),
    (
        {"wisdom teeth"},
        ["Wisdom tooth impaction", "Pericoronitis", "Normal wisdom tooth eruption"],
        ["Panoramic X-ray (OPG)", "Refer to oral surgery if impacted", "Analgesia if required"],
    ),
    (
        {"teething"},
        ["Normal deciduous tooth eruption", "Teething discomfort"],
        ["Reassurance — teething is normal", "Topical gum gel if discomfort", "Routine dental review"],
    ),
]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class NEREntity:
    type: str
    value: str
    unit: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    onset: Optional[str] = None
    name: Optional[str] = None
    negated: Optional[bool] = None  # True = entity appears in negated context

    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None and v is not False}


@dataclass
class SOAPNote:
    S: str = ""
    O: str = ""
    A: str = ""
    P: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {"S": self.S, "O": self.O, "A": self.A, "P": self.P}

    def is_complete(self) -> bool:
        return (
            len(self.S.strip()) >= 20 and
            self.O.strip() != "" and
            "DDx:" in self.A and
            self.P.strip() != ""
        )


# ── Main class ────────────────────────────────────────────────────────────────

class SOAPGenerator:
    """
    Generate a structured SOAP note from translated medical text.

    Rules (from AI_POLICY.md + DS-FID-001 §5):
    - SOAP "A" contains differentials and clinical reasoning, not a diagnosis conclusion.
    - All drug names preserved verbatim (never paraphrased).
    - Output labeled as AI-assisted draft requiring physician review.
    """

    # @req SRS-L6-005 -- generate SOAP; A section = differentials only, never single diagnosis
    def generate_soap(self, entities: List[NEREntity], translated_text: str) -> SOAPNote:
        """Generate SOAP note from NER entities and translated text."""
        note = SOAPNote()
        note.S = self._build_subjective(entities, translated_text)
        note.O = self._build_objective(entities)
        note.A = self._build_assessment(entities, translated_text)
        note.P = self._build_plan(entities, translated_text)
        return note

    # Fix 2: Pre-negation pattern (scans full VI text before NER)
    _PRE_NEG_RE = re.compile(
        r'\bkhông\s+(?:bị\s+|có\s+|thấy\s+|đau\s+|bị\s+đau\s+|bị\s+)?'
        r'([^\s,\.;\n][^,\.;\n]{0,40})',
        re.IGNORECASE | re.UNICODE
    )
    # Fix 4: MSK context keywords — upgrade chest pain to MSK
    _MSK_CONTEXT_RE = re.compile(
        r'\b(?:gym|tập\s+gym|tập\s+thể\s+dục|vác\s+nặng|mang\s+nặng|'
        r'sau\s+khi\s+tập|cơ\s+ngực|đau\s+cơ|bị\s+ngã|chấn\s+thương\s+nhẹ|'
        r'sau\s+khi\s+làm\s+việc|khi\s+tập|khi\s+nâng)\b',
        re.IGNORECASE | re.UNICODE
    )

    def _build_vi_negated_set(self, vi_text: str) -> set:
        """Fix 2: Build set of VI terms explicitly negated in text BEFORE NER runs."""
        negated: set = set()
        for m in self._PRE_NEG_RE.finditer(vi_text):
            phrase = m.group(1).lower().strip()
            negated.add(phrase)
            # Also sub-phrases (head tokens)
            words = phrase.split()
            for i in range(1, min(len(words) + 1, 5)):
                negated.add(' '.join(words[:i]))
        return negated

    def _extract_vi_entities(self, vi_text: str) -> List[NEREntity]:
        """Scan VI text for symptoms — NER-B1 + Fix2 pre-negation + Fix4 MSK override."""
        entities: List[NEREntity] = []
        seen: set = set()

        # Fix 2: build negated set BEFORE iterating phrases
        negated_set = self._build_vi_negated_set(vi_text)

        # Fix 4: detect MSK context → will upgrade chest pain to musculoskeletal
        is_msk_context = bool(self._MSK_CONTEXT_RE.search(vi_text))

        _NEG_PREFIX = re.compile(
            r'\bkhông\s+(?:bị\s+|có\s+|thấy\s+|đau\s+|bị\s+đau\s+)?',
            re.IGNORECASE | re.UNICODE
        )
        for vi_phrase in sorted(_VI_SYMPTOM_VOCAB.keys(), key=len, reverse=True):
            pattern = re.compile(r'\b' + re.escape(vi_phrase) + r'\b',
                                 re.IGNORECASE | re.UNICODE)
            m = pattern.search(vi_text)
            if m:
                # Fix 2a: check pre-built negated set
                if vi_phrase.lower() in negated_set:
                    continue
                # Fix 2b: check prefix negation (existing per-match check)
                start = max(0, m.start() - 15)
                prefix = vi_text[start:m.start()]
                if _NEG_PREFIX.search(prefix):
                    continue
                sym_val = _VI_SYMPTOM_VOCAB[vi_phrase]
                # Fix 4: MSK context → upgrade "chest pain" to "musculoskeletal chest pain"
                if is_msk_context and sym_val == "chest pain":
                    sym_val = "musculoskeletal chest pain"
                if sym_val not in seen:
                    seen.add(sym_val)
                    ent_type = "DIAGNOSTIC" if sym_val in _VI_DIAGNOSTIC_VALUES else "SYMPTOM"
                    onset = self._extract_global_onset(vi_text) if ent_type == "SYMPTOM" else None
                    entities.append(NEREntity(type=ent_type, value=sym_val, onset=onset))
        return entities

    # VI sub-words that are meaningful only inside compounds, not as standalone symptoms.
    # PhoBERT sometimes tags these as separate B-DISEASESYMTOM entities — filter them out.
    _VI_FRAGMENT_EXCLUDE: frozenset = frozenset({
        # Compound sub-words (body-part or modifier, meaningless standalone)
        "thắt", "gắng", "gắng sức", "sức", "mặt",
        "nặng", "nhẹ", "cao", "thấp", "nhiều", "ít",
        "thoáng", "thoáng qua", "khi", "khi gắng sức",
        # A4: Adverbs / partial words from Test 1
        "đột ngột",       # suddenly — adverb, not symptom
        "khó",            # difficulty (sub-word of "nói khó", "khó thở")
        "hồi",            # fragment of "hồi phục" (recovery)
        "tự",             # self (as in "tự hồi phục")
        "phục",           # fragment of "hồi phục"
    })

    # Medical compound extensions: when PhoBERT returns a root symptom word,
    # try to extend it using known VI compound patterns from the source text.
    _VI_COMPOUND_ROOTS = {
        "đau":   ["thắt ngực", "ngực", "bụng", "đầu", "lưng", "khớp", "cơ", "răng", "tai", "mắt", "cổ", "vai"],
        "khó":   ["thở", "nuốt", "nói", "chịu"],
        "sốt":   ["cao", "nhẹ"],
        "chóng": ["mặt"],
        "buồn":  ["nôn"],
        "tức":   ["ngực", "bụng"],
        "nặng":  ["ngực", "đầu"],
    }

    def _extend_phobert_compound(self, entity_value: str, vi_text: str) -> str:
        """Extend single-word PhoBERT fragment to full VI compound using source text."""
        root = entity_value.lower()
        if root not in self._VI_COMPOUND_ROOTS:
            return entity_value
        # Find root in text, check if any known extension follows
        pattern = re.compile(r'\b' + re.escape(root) + r'\s+(.+?)(?:\s*[,\.;\n]|$)',
                             re.IGNORECASE | re.UNICODE)
        m = pattern.search(vi_text)
        if not m:
            return entity_value
        following = m.group(1).lower().strip()
        for ext in self._VI_COMPOUND_ROOTS[root]:
            if following.startswith(ext):
                compound = root + " " + ext
                # Map to English via vocab so dedup works with rule-based EN entities
                return _VI_SYMPTOM_VOCAB.get(compound, compound)
        return entity_value

    _VI_NEG_WINDOW_RE = re.compile(
        r'\b(không|chưa|chẳng|không có|không thấy|không bị|âm tính)\b',
        re.IGNORECASE | re.UNICODE,
    )

    def _is_negated_in_vi(self, entity_value: str, vi_text: str, negated_set: set) -> bool:
        """Check if entity value is negated via set lookup OR direct window scan.

        Window is clipped at sentence boundaries (.,!?\\n) to prevent
        negation from a previous clause ("không liệt. Chỉ chóng mặt")
        from falsely negating the next clause.
        """
        val_lower = entity_value.lower()
        if val_lower in negated_set or any(w in negated_set for w in val_lower.split()):
            return True
        # Direct window: find entity in text, check for negation in same sentence only
        idx = vi_text.lower().find(val_lower)
        if idx > 0:
            window = vi_text[max(0, idx - 40): idx]
            # Clip at last sentence boundary — do not cross into previous sentence
            for sep in ('.', '!', '?', '\n'):
                boundary = window.rfind(sep)
                if boundary >= 0:
                    window = window[boundary + 1:]
            if self._VI_NEG_WINDOW_RE.search(window):
                return True
        return False

    def _merge_phobert_spans(self, entities: List[NEREntity], vi_text: str) -> List[NEREntity]:
        """Merge adjacent same-type fragments: 'chóng' + 'mặt' → 'chóng mặt'."""
        if len(entities) < 2:
            return entities
        merged: List[NEREntity] = []
        i = 0
        while i < len(entities):
            e = entities[i]
            while i + 1 < len(entities):
                nxt = entities[i + 1]
                candidate = e.value + " " + nxt.value
                if (nxt.type == e.type
                        and nxt.negated == e.negated
                        and candidate in vi_text):
                    e = NEREntity(type=e.type, value=candidate,
                                  unit=e.unit or nxt.unit,
                                  onset=e.onset or nxt.onset,
                                  negated=e.negated)
                    i += 1
                else:
                    break
            merged.append(e)
            i += 1
        return merged

    def _extract_vi_entities_ml(self, vi_text: str) -> List[NEREntity]:
        """VI NER: PhoBERT+CRF merged with rule-based. Rule-based always runs as safety net."""
        result: List[NEREntity] = []
        negated_set = self._build_vi_negated_set(vi_text)

        # PhoBERT path — apply negation filter + span merge
        if _PHOBERT_AVAILABLE:
            try:
                ner = _get_phobert_ner()
                if ner._loaded:
                    ml_entities = ner.predict(vi_text)
                    tagged: List[NEREntity] = []
                    for e in ml_entities:
                        # B2: Strip trailing punctuation from PhoBERT token values
                        if e.value and e.value[-1] in '.,;:!?':
                            e = NEREntity(type=e.type, value=e.value.rstrip('.,;:!?'),
                                          unit=e.unit, onset=e.onset)
                        # Extend single-word fragments to full VI compounds
                        extended_val = self._extend_phobert_compound(e.value, vi_text)
                        if extended_val != e.value:
                            e = NEREntity(type=e.type, value=extended_val,
                                          unit=e.unit, onset=e.onset)
                        # Skip meaningless sub-word fragments
                        if e.value.lower() in self._VI_FRAGMENT_EXCLUDE:
                            continue
                        is_neg = self._is_negated_in_vi(e.value, vi_text, negated_set)
                        if is_neg:
                            tagged.append(NEREntity(
                                type=e.type, value=e.value,
                                unit=e.unit, dose=e.dose,
                                frequency=e.frequency, onset=e.onset,
                                name=e.name, negated=True,
                            ))
                        else:
                            tagged.append(e)
                    tagged = self._merge_phobert_spans(tagged, vi_text)
                    result.extend(tagged)
                    logger.debug("PhoBERT NER: %d entities (%d negated)",
                                 len(tagged),
                                 sum(1 for e in tagged if e.negated))
            except Exception as exc:
                logger.warning("PhoBERT NER failed, rule-based only: %s", exc)

        # Rule-based ALWAYS runs — supplements PhoBERT, never replaced
        seen = {e.value for e in result if not e.negated}
        for e in self._extract_vi_entities(vi_text):
            if e.value not in seen:
                result.append(e)
                seen.add(e.value)

        return result

    # @req SRS-L6-004 -- extract NER entities: age, gender, symptoms, medications, vitals, history
    def extract_entities(self, text: str, vi_text: str = "") -> List[NEREntity]:
        """Extract named medical entities from English text. If vi_text given, merges VI NER results."""
        entities: List[NEREntity] = []

        # AGE
        for m in _AGE_RE.finditer(text):
            entities.append(NEREntity(type="AGE", value=m.group(1), unit="years"))

        # GENDER
        for m in _GENDER_RE.finditer(text):
            entities.append(NEREntity(type="GENDER", value=m.group(1).lower()))

        # SYMPTOMS (longest match first) — CA-031: EN negation filter
        text_lower = text.lower()
        # Build negated term set: "no headache", "not seizing", "denies pain", "without fever"
        _en_neg_re = re.compile(
            r'\b(?:no|not|without|absent|denies?|negative\s+for|ruled?\s+out)\s+'
            r'((?:\w+\s+){0,3}\w+)', re.IGNORECASE
        )
        _negated_en: set = set()
        for m in _en_neg_re.finditer(text):
            _negated_en.add(m.group(1).lower().strip())
            # Also add individual words from negated phrase
            for w in m.group(1).lower().split():
                _negated_en.add(w)

        seen_symptoms: set = set()
        for keyword in sorted(_SYMPTOM_KEYWORDS.keys(), key=len, reverse=True):
            if keyword in text_lower:
                # Skip if this keyword appears only in a negated context
                kw_lower = keyword.lower()
                if kw_lower in _negated_en:
                    continue
                # Double-check: ensure keyword is not preceded by negation in the actual text
                kw_pos = text_lower.find(kw_lower)
                if kw_pos > 0:
                    prefix = text_lower[max(0, kw_pos - 20):kw_pos]
                    if re.search(r'\b(?:no|not|without|absent)\s*$', prefix):
                        continue
                kw_type, sym_val = _SYMPTOM_KEYWORDS[keyword]
                if sym_val not in seen_symptoms:
                    seen_symptoms.add(sym_val)
                    onset = self._extract_global_onset(text) if kw_type == "SYMPTOM" else None
                    entities.append(NEREntity(type=kw_type, value=sym_val, onset=onset))

        # INJURY PATTERNS — regex for verb-noun variants ("sprained my ankle")
        # Skip if a more specific symptom for the same body part already captured.
        for pattern, sym_val in _INJURY_PATTERNS:
            if sym_val not in seen_symptoms:
                primary = sym_val.split()[0]
                if not any(s.startswith(primary) for s in seen_symptoms):
                    if pattern.search(text):
                        seen_symptoms.add(sym_val)
                        entities.append(NEREntity(type="SYMPTOM", value=sym_val))

        # MEDICAL HISTORY — longest match first; skip keyword if already subsumed by a longer match
        seen_history_keywords: set = set()
        for keyword, condition in sorted(_HISTORY_KEYWORDS.items(), key=lambda x: len(x[0]), reverse=True):
            if keyword in text_lower:
                if not any(keyword in seen_kw for seen_kw in seen_history_keywords):
                    seen_history_keywords.add(keyword)
                    entities.append(NEREntity(type="HISTORY", value=condition))

        # MEDICATIONS (drug + dose)
        for m in _MEDICATION_RE.finditer(text):
            drug_name = m.group(1)
            dose = m.group(2)
            unit = m.group(3).lower()
            freq = m.group(4) or ""
            entities.append(NEREntity(
                type="MEDICATION",
                value=drug_name,
                dose=f"{dose}{unit}",
                frequency=freq.lower() if freq else None,
            ))

        # VITALS — Blood pressure
        for m in _BP_RE.finditer(text):
            entities.append(NEREntity(type="VITAL", name="blood_pressure",
                                      value=m.group(1), unit="mmHg"))

        # VITALS — Heart rate
        for m in _HR_RE.finditer(text):
            entities.append(NEREntity(type="VITAL", name="heart_rate",
                                      value=m.group(1), unit="bpm"))

        # VITALS — Temperature
        for m in _TEMP_RE.finditer(text):
            entities.append(NEREntity(type="VITAL", name="temperature",
                                      value=m.group(1), unit="°C"))

        # VITALS — SpO2
        for m in _SPO2_RE.finditer(text):
            entities.append(NEREntity(type="VITAL", name="spo2",
                                      value=m.group(1), unit="%"))

        # VITALS — Blood glucose (CA-029)
        for m in _BGL_RE.finditer(text):
            entities.append(NEREntity(type="VITAL", name="blood_glucose",
                                      value=m.group(1), unit="mmol/L"))

        # MV-FID-018: VI NER — PhoBERT-base-v2 + CRF (preferred) or rule-based fallback
        if vi_text:
            seen_symptoms = {e.value for e in entities if e.type == "SYMPTOM"}
            vi_entities = self._extract_vi_entities_ml(vi_text)
            for ve in vi_entities:
                if ve.value not in seen_symptoms:
                    entities.append(ve)
                    seen_symptoms.add(ve.value)

            # CA-025/027: VI age is authoritative — removes EN duplicates caused by MarianMT
            # (e.g. "40 độ" temperature misread as "40 year old" by MarianMT)
            vi_age_m = re.search(r'\b(\d+)\s*tuổi\b', vi_text, re.IGNORECASE | re.UNICODE)
            if vi_age_m:
                entities = [e for e in entities if e.type != "AGE"]
                entities.insert(0, NEREntity(type="AGE", value=vi_age_m.group(1), unit="years"))

            if not any(e.type == "GENDER" for e in entities):
                # CA-029: expanded gender patterns (bé trai/bé gái for pediatric cases)
                if re.search(r'\b(nữ|bé\s*gái)\b', vi_text, re.IGNORECASE | re.UNICODE):
                    entities.insert(0, NEREntity(type="GENDER", value="female"))
                elif re.search(r'\b(nam|bé\s*trai)\b', vi_text, re.IGNORECASE | re.UNICODE):
                    entities.insert(0, NEREntity(type="GENDER", value="male"))

            if not any(e.type == "VITAL" and e.name == "weight" for e in entities):
                m = re.search(r'\b(\d+(?:\.\d+)?)\s*kg\b', vi_text, re.IGNORECASE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="weight",
                                              value=m.group(1), unit="kg"))

            # CA-026: VI vitals fallback — BP / HR / SpO2 direct from VI text
            if not any(e.type == "VITAL" and e.name == "blood_pressure" for e in entities):
                m = re.search(r'\bhuyết\s*áp\s+(\d{2,3}/\d{2,3})\b',
                              vi_text, re.IGNORECASE | re.UNICODE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="blood_pressure",
                                              value=m.group(1), unit="mmHg"))

            if not any(e.type == "VITAL" and e.name == "heart_rate" for e in entities):
                m = re.search(r'\bmạch(?:\s+nhanh)?\s+(\d{2,3})\s*(?:lần/phút|bpm)?\b',
                              vi_text, re.IGNORECASE | re.UNICODE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="heart_rate",
                                              value=m.group(1), unit="bpm"))

            # CA-028: VI SpO2 authoritative — requires explicit "%" to avoid grabbing RR value
            # MarianMT confuses SpO2 82% with adjacent RR 32/min → EN NER extracts wrong number
            vi_spo2_m = re.search(r'\bSpO2\s*(\d{2,3})\s*%', vi_text, re.IGNORECASE)
            if vi_spo2_m:
                entities = [e for e in entities if not (e.type == "VITAL" and e.name == "spo2")]
                entities.append(NEREntity(type="VITAL", name="spo2",
                                          value=vi_spo2_m.group(1), unit="%"))

            if not any(e.type == "VITAL" and e.name == "temperature" for e in entities):
                m = re.search(r'\bsốt(?:\s+cao)?\s+(\d{2,3}(?:\.\d)?)\s*(?:độ|°)?\b',
                              vi_text, re.IGNORECASE | re.UNICODE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="temperature",
                                              value=m.group(1), unit="°C"))

            if not any(e.type == "VITAL" and e.name == "respiratory_rate" for e in entities):
                m = re.search(r'\bthở\s+nhanh\s+(\d{2,3})\s*(?:lần/phút)?\b',
                              vi_text, re.IGNORECASE | re.UNICODE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="respiratory_rate",
                                              value=m.group(1), unit="bpm"))

            # CA-029: VI blood glucose fallback
            if not any(e.type == "VITAL" and e.name == "blood_glucose" for e in entities):
                m = re.search(r'\bđường\s*huyết\s+(\d+(?:\.\d+)?)\s*(?:mmol)?',
                              vi_text, re.IGNORECASE | re.UNICODE)
                if m:
                    entities.append(NEREntity(type="VITAL", name="blood_glucose",
                                              value=m.group(1), unit="mmol/L"))

            # CA-029/031: remove edema FP
            # "phù hợp" = appropriate (NOT edema) — exclude from edema detection
            has_real_edema = re.search(
                r'\bphù\b(?!\s+hợp)(?!\s+điêu)', vi_text, re.IGNORECASE | re.UNICODE
            )
            if not has_real_edema:
                entities = [e for e in entities
                            if not (e.type == "SYMPTOM" and e.value in ("edema", "phù"))]

            # CA-030: VI HISTORY fallback — bypass MarianMT garbling
            _VI_HISTORY_RE = [
                (r'\bđái\s*tháo\s*đường\s*type\s*2\b',  "type 2 diabetes mellitus"),
                (r'\btiểu\s*đường\s*type\s*2\b',        "type 2 diabetes mellitus"),
                (r'\bđái\s*tháo\s*đường\b',             "diabetes mellitus"),
                (r'\btiểu\s*đường\b',                   "diabetes"),
                (r'\btăng\s*huyết\s*áp\b',              "hypertension"),
                (r'\brung\s*nhĩ\b',                     "atrial fibrillation"),
                (r'\bsuy\s*tim\b',                      "heart failure"),
                (r'\bbệnh\s*mạch\s*vành\b',             "coronary artery disease"),
                (r'\bhen\s*suyễn\b',                    "asthma"),
                (r'\bviêm\s*phổi\s*mãn\b',             "pneumonia"),
            ]
            seen_history = {e.value for e in entities if e.type == "HISTORY"}
            for pattern, condition in _VI_HISTORY_RE:
                if re.search(pattern, vi_text, re.IGNORECASE | re.UNICODE):
                    if condition not in seen_history:
                        entities.append(NEREntity(type="HISTORY", value=condition))
                        seen_history.add(condition)

            # Fix 4 (EN path): MSK context → upgrade "chest pain" → "musculoskeletal chest pain"
            if self._MSK_CONTEXT_RE.search(vi_text):
                msk_upgrade_needed = (
                    any(e.type == "SYMPTOM" and e.value == "chest pain" for e in entities) and
                    not any(e.type == "SYMPTOM" and e.value == "musculoskeletal chest pain" for e in entities)
                )
                if msk_upgrade_needed:
                    entities = [
                        NEREntity(type="SYMPTOM", value="musculoskeletal chest pain",
                                  onset=e.onset) if (e.type == "SYMPTOM" and e.value == "chest pain")
                        else e
                        for e in entities
                    ]

            # CA-030/031: deduplicate SYMPTOM — remove generic if specific present
            _SYMPTOM_SUPERSEDED = {
                "chest pain":         {"musculoskeletal chest pain", "left chest pain", "right chest pain",
                                       "chest pain on exertion"},
                "weakness":           {"hemiparesis", "right hemiparesis", "left hemiparesis",
                                       "right arm weakness", "left arm weakness",
                                       "right leg weakness", "left leg weakness"},
                "hemiparesis":        {"right hemiparesis", "left hemiparesis"},
                "cough":              {"severe pneumonia"},
                "altered consciousness": {"coma"},
                "stroke":             {"ischemic stroke", "hemorrhagic stroke"},
            }
            sym_values = {e.value for e in entities if e.type == "SYMPTOM"}
            entities = [
                e for e in entities
                if not (e.type == "SYMPTOM" and
                        any(s in sym_values for s in _SYMPTOM_SUPERSEDED.get(e.value, set())))
            ]

            # CA-031: deduplicate HISTORY — remove less specific if more specific present
            _HISTORY_SUPERSEDED = {
                "diabetes":          {"diabetes mellitus", "type 2 diabetes mellitus"},
                "diabetes mellitus": {"type 2 diabetes mellitus"},
            }
            hist_values = {e.value for e in entities if e.type == "HISTORY"}
            entities = [
                e for e in entities
                if not (e.type == "HISTORY" and
                        any(s in hist_values for s in _HISTORY_SUPERSEDED.get(e.value, set())))
            ]

        # Fix 1: Source text verification — remove symptoms not traceable to original texts
        # Multi-value reverse lookup: canonical EN value → ALL VI phrases that map to it
        _val_to_vi_multi: dict = {}
        for vi_k, en_v in _VI_SYMPTOM_VOCAB.items():
            _val_to_vi_multi.setdefault(en_v, []).append(vi_k)
        combined_source = (vi_text + " " + text).lower() if vi_text else text.lower()

        # Derived/upgraded symptoms: original base symptom verifies them
        _DERIVED_FROM = {
            "musculoskeletal chest pain": {"chest pain"},
            "right facial numbness":      {"numbness", "facial numbness"},
            "left facial numbness":       {"numbness", "facial numbness"},
            "right arm weakness":         {"weakness"},
            "left arm weakness":          {"weakness"},
            "right leg weakness":         {"weakness"},
            "left leg weakness":          {"weakness"},
            "right hemibody numbness":    {"numbness"},
            "left hemibody numbness":     {"numbness"},
        }

        def _symptom_in_source(sym_val: str) -> bool:
            """Return True if symptom value appears positively in source texts."""
            # Clinical findings always pass (explicit clinical statements)
            if sym_val in ("CT no hemorrhage", "tPA contraindicated", "thrombectomy indicated",
                           "CT no haemorrhage"):
                return True
            # Derived symptoms pass if their base symptom appears in source
            for base in _DERIVED_FROM.get(sym_val, set()):
                if base.lower() in combined_source:
                    return True
            # Check EN keyword in combined source
            if sym_val.lower() in combined_source:
                return True
            # Check ALL VI phrase mappings for this value
            for vi_phrase in _val_to_vi_multi.get(sym_val, []):
                if vi_phrase.lower() in combined_source:
                    return True
            # Check SYMPTOM_KEYWORDS reverse (EN keywords)
            for kw, (_, val) in _SYMPTOM_KEYWORDS.items():
                if val == sym_val and kw.lower() in combined_source:
                    return True
            return False

        verified_entities = []
        for e in entities:
            if e.type == "SYMPTOM" and not _symptom_in_source(e.value):
                logger.debug("Fix1: removed unverified symptom '%s'", e.value)
                continue
            verified_entities.append(e)
        entities = verified_entities

        # S1 FIX: Cross-check EN symptom entities against VI negation.
        # EN NER extracts from MarianMT translation which may lose "không/not".
        # Reverse-lookup EN value → VI phrases → check negation in original VI text.
        if vi_text:
            _negated_vi = self._build_vi_negated_set(vi_text)
            _val_to_vi = {}
            for vi_k, en_v in _VI_SYMPTOM_VOCAB.items():
                _val_to_vi.setdefault(en_v.lower(), []).append(vi_k)
            final: List[NEREntity] = []
            for e in entities:
                if e.type == "SYMPTOM" and not e.negated:
                    for vi_ph in _val_to_vi.get(e.value.lower(), []):
                        if self._is_negated_in_vi(vi_ph, vi_text, _negated_vi):
                            e = NEREntity(type=e.type, value=e.value, unit=e.unit,
                                          dose=e.dose, frequency=e.frequency,
                                          onset=e.onset, name=e.name, negated=True)
                            break
                final.append(e)
            entities = final

        # A1: Deduplicate by (type, value) — removes duplicate DIAGNOSTIC/SYMPTOM entities
        seen_keys: set = set()
        deduped: List[NEREntity] = []
        for e in entities:
            key = (e.type, e.value.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(e)
        entities = deduped

        return entities

    # @req SRS-L6-007 (MV-FID-017) — Vietnamese SOAP generation
    def generate_soap_vi(self, entities: List[NEREntity], translated_text: str) -> SOAPNote:
        """Generate SOAP note in Vietnamese using template-based approach."""
        note = SOAPNote()
        note.S = self._build_subjective_vi(entities, translated_text)
        note.O = self._build_objective_vi(entities)
        note.A = self._build_assessment_vi(entities, translated_text)
        note.P = self._build_plan_vi(entities, translated_text)
        return note

    def validate_soap(self, note: SOAPNote) -> bool:
        """Return True only if all 4 SOAP sections are non-empty."""
        return note.is_complete()

    # ── Private builders ──────────────────────────────────────────────────────

    def _build_subjective(self, entities: List[NEREntity], text: str) -> str:
        age = next((e.value for e in entities if e.type == "AGE"), None)
        gender = next((e.value for e in entities if e.type == "GENDER"), None)
        symptoms = [e.value for e in entities
                    if e.type == "SYMPTOM" and not e.negated
                    and e.value not in self._S_EXCLUDE]
        onset_entity = next((e for e in entities if e.type == "SYMPTOM" and e.onset), None)

        parts = []
        if age and gender:
            parts.append(f"{age}-year-old {gender}")
        elif age:
            parts.append(f"{age}-year-old patient")
        else:
            parts.append("Patient")

        if symptoms:
            onset_str = f" {onset_entity.onset}" if onset_entity and onset_entity.onset else ""
            parts.append(f"presents with {', '.join(symptoms)}{onset_str}.")
        else:
            parts.append("presents for consultation.")

        return " ".join(parts)

    def _build_objective(self, entities: List[NEREntity]) -> str:
        parts = []
        vitals = [e for e in entities if e.type == "VITAL"]
        meds = [e for e in entities if e.type == "MEDICATION"]

        for v in vitals:
            name = v.name.replace("_", " ").title() if v.name else ""
            parts.append(f"{name}: {v.value} {v.unit or ''}".strip())

        for m in meds:
            freq = f" {m.frequency}" if m.frequency else ""
            parts.append(f"Currently on {m.value} {m.dose or ''}{freq}.")

        if not parts:
            parts.append("Vital signs and objective findings pending documentation.")

        return " ".join(parts)

    # Fix 3: Cardiac Safety Gate — these DDx only allowed when cardiac signal present
    _CARDIAC_DDX = {
        "Hypertensive urgency", "Cardiac ischemia (ACS)", "Pulmonary embolism",
        "ST-elevation MI (STEMI)", "Non-ST-elevation MI (NSTEMI)", "Unstable angina",
        "Cardiogenic shock", "Supraventricular tachycardia (SVT)",
    }
    _CARDIAC_SIGNALS = {
        "chest pain", "chest pain on exertion", "left chest pain", "right chest pain",
        "palpitations", "shortness of breath", "myocardial infarction",
        "tachycardia", "hypotension", "syncope",
    }

    _SEIZURE_SIGNALS = frozenset({
        "seizure", "post-ictal", "co giật", "động kinh", "todd", "convulsion",
    })
    _VESTIBULAR_ONLY_DDX = frozenset({
        "Vestibular neuritis", "Benign paroxysmal positional vertigo (BPPV)",
        "Chóng mặt tư thế lành tính (BPPV)", "Viêm thần kinh tiền đình",
        "Labyrinthitis",
    })

    def _select_differentials(self, signals: set) -> tuple:
        """Score differential groups. Cardiac + Todd's + Dysarthria safety gates."""
        best_score = 0
        best_diffs: List[str] = []
        best_plan: List[str] = []
        has_cardiac_signal = bool(signals & self._CARDIAC_SIGNALS)

        for signal_set, diffs, plan in _DIFFERENTIALS:
            score = len(signal_set & signals)
            if score > best_score:
                best_score = score
                best_diffs = list(diffs)
                best_plan = list(plan)
            elif score == best_score and score > 0:
                for d in diffs:
                    if d not in best_diffs:
                        best_diffs.append(d)
                for p in plan:
                    if p not in best_plan:
                        best_plan.append(p)

        # Fix 3: Remove cardiac DDx if no cardiac signal present
        if not has_cardiac_signal:
            best_diffs = [d for d in best_diffs if d not in self._CARDIAC_DDX]

        # Fix 5: Todd's paresis only if seizure signal present
        has_seizure = bool(signals & self._SEIZURE_SIGNALS)
        if not has_seizure:
            best_diffs = [d for d in best_diffs if "Todd" not in d]

        # Fix 6: BPPV / Vestibular neuritis incompatible with dysarthria
        has_dysarthria = any(s in signals for s in ("dysarthria", "nói khó", "speech difficulty"))
        if has_dysarthria:
            best_diffs = [d for d in best_diffs if d not in self._VESTIBULAR_ONLY_DDX]

        return best_diffs, best_plan, best_score

    def _build_assessment(self, entities: List[NEREntity], text: str) -> str:
        """Build differential diagnosis — MV-FID-019: Qwen+KB if available, template fallback."""
        if _RAG_AVAILABLE:
            try:
                kb = _get_kb()
                qwen = _get_qwen()
                if qwen._loaded:
                    query = " ".join(
                        e.value for e in entities if e.type in ("SYMPTOM", "HISTORY")
                    )
                    kb_chunks = kb.query(query, top_k=3) if kb._loaded else []
                    result = qwen.generate(entities, kb_chunks)
                    if result.get("assessment"):
                        return result["assessment"]
            except Exception as exc:
                logger.warning("Qwen Assessment failed, using template: %s", exc)

        # Template fallback (original logic)
        symptoms    = {e.value.lower() for e in entities if e.type == "SYMPTOM"    and not e.negated}
        history     = {e.value.lower() for e in entities if e.type == "HISTORY"    and not e.negated}
        diagnostics = {e.value.lower() for e in entities if e.type == "DIAGNOSTIC"}
        differentials, _, _ = self._select_differentials(symptoms | history | diagnostics)
        if not differentials:
            chief = next(iter(symptoms), "presenting complaint")
            differentials = [f"Undifferentiated {chief} — further evaluation required"]
        # CA-031: prioritise clinically significant chief complaint
        _PRIORITY_SYMPTOMS = [
            "ischemic stroke", "hemorrhagic stroke", "right hemiparesis", "left hemiparesis",
            "hemiparesis", "myocardial infarction", "stroke", "sepsis", "coma",
            "trauma", "severe pneumonia", "thrombectomy indicated",
            "right facial numbness", "left facial numbness", "right arm weakness",
            "left arm weakness", "right leg weakness", "left leg weakness",
            "right hemibody numbness", "left hemibody numbness",
            "dysarthria", "facial droop",
        ]
        chief_symptom = next(
            (s for s in _PRIORITY_SYMPTOMS if s in symptoms),
            next(iter(symptoms), "presenting complaint")
        ).capitalize()
        history_str = f" in patient with known {', '.join(history)}" if history else ""
        diag_text = " ".join(e.value for e in entities if e.type == "DIAGNOSTIC")
        differentials = self._apply_diagnostic_override(differentials, diag_text or text, text)
        return f"{chief_symptom}{history_str}. DDx: {', '.join(differentials)}."

    # Clinical Safety Gate: diagnostic findings that override DDx
    _CT_NO_HEMORRHAGE_RE = re.compile(
        r'\bCT\b[^\n.]*\b(không xuất huyết|không chảy máu|âm tính|no hemorrhage|no bleed)\b',
        re.IGNORECASE | re.UNICODE,
    )
    _MRI_NORMAL_RE = re.compile(
        r'\bMRI\b[^\n.]*\b(bình thường|âm tính|normal|no mass|no infarct)\b',
        re.IGNORECASE | re.UNICODE,
    )
    _ECG_NORMAL_RE = re.compile(
        r'\bECG\b[^\n.]*\b(bình thường|normal|sinus rhythm|no st)\b',
        re.IGNORECASE | re.UNICODE,
    )
    _HEMORRHAGE_DDX = frozenset({
        "Hemorrhagic stroke", "Đột quỵ xuất huyết", "haemorrhagic stroke",
        "Haemorrhagic stroke excluded by CT", "Intracranial hemorrhage",
    })
    _CARDIAC_ISCHEMIA_DDX = frozenset({
        "ST-elevation MI (STEMI)", "Non-ST-elevation MI (NSTEMI)", "Unstable angina",
        "Cardiac ischemia (ACS)",
    })

    def _apply_diagnostic_override(self, diffs: List[str], vi_text: str, en_text: str) -> List[str]:
        """Remove DDx entries contradicted by documented diagnostic findings."""
        full = (vi_text + " " + en_text)
        full_l = full.lower()
        # CT negative for hemorrhage → exclude hemorrhagic DDx
        _has_ct = bool(re.search(r'\bCT\b', full))
        _ct_neg = bool(re.search(
            r'\b(không xuất huyết|không chảy máu|no hemorrhage|no bleed|âm tính)\b',
            full, re.IGNORECASE | re.UNICODE,
        ))
        if _has_ct and _ct_neg:
            diffs = [d for d in diffs if d not in self._HEMORRHAGE_DDX
                     and not re.search(r'h(a)?emorrhag', d, re.IGNORECASE)
                     and "xuất huyết" not in d.lower()]
        # MRI normal → exclude mass/tumor
        _mri_normal = bool(re.search(
            r'\bMRI\b.{0,50}?\b(bình thường|âm tính|normal|no mass|no infarct)\b',
            full, re.IGNORECASE | re.UNICODE,
        ))
        if _mri_normal:
            diffs = [d for d in diffs if "mass" not in d.lower() and "tumor" not in d.lower()]
        # ECG normal → exclude acute MI / arrhythmia
        _ecg_normal = bool(re.search(
            r'\bECG\b.{0,50}?\b(bình thường|normal|sinus rhythm|no st)\b',
            full, re.IGNORECASE | re.UNICODE,
        ))
        if _ecg_normal:
            diffs = [d for d in diffs if d not in self._CARDIAC_ISCHEMIA_DDX]
        return diffs

    # Fix 4: Strict-KB domain signals
    _STROKE_KB_SIGNALS = {
        "ischemic stroke", "hemorrhagic stroke", "right hemiparesis", "left hemiparesis",
        "hemiparesis", "tpa contraindicated", "thrombectomy indicated", "ct no hemorrhage",
        "dysarthria", "facial droop", "right hemiplegia", "left hemiplegia",
    }
    _STROKE_KB_QUERY = (
        "đột quỵ nhồi máu não LVO thrombectomy tPA kháng đông apixaban "
        "CT không xuất huyết can thiệp mạch"
    )

    def _get_kb_query(self, entities: List[NEREntity]) -> str:
        """Fix 4: Use targeted Stroke KB query when stroke context detected."""
        signals = {e.value.lower() for e in entities if e.type in ("SYMPTOM", "HISTORY")}
        if signals & self._STROKE_KB_SIGNALS:
            return self._STROKE_KB_QUERY
        return " ".join(e.value for e in entities if e.type in ("SYMPTOM", "HISTORY"))

    @staticmethod
    def _dedup_plan(plan_items: List[str], max_items: int = 8) -> List[str]:
        """Fix 3: Deduplicate plan items, keep max_items most important."""
        seen: set = set()
        result: List[str] = []
        for item in plan_items:
            key = item.lower().strip().rstrip(".")
            if key not in seen:
                seen.add(key)
                result.append(item)
            if len(result) >= max_items:
                break
        return result

    def _build_plan(self, entities: List[NEREntity], text: str) -> str:
        """Build plan — Fix 3: deduplicate. Fix 4: Strict-KB for stroke context."""
        if _RAG_AVAILABLE:
            try:
                kb = _get_kb()
                qwen = _get_qwen()
                if qwen._loaded:
                    kb_chunks = kb.query(self._get_kb_query(entities), top_k=3) if kb._loaded else []
                    result = qwen.generate(entities, kb_chunks)
                    if result.get("plan"):
                        return result["plan"]
            except Exception as exc:
                logger.warning("Qwen Plan failed, using template: %s", exc)

        # Template fallback — Fix 3: dedup + limit + Fix 5: conditional cardiac tests
        symptoms = {e.value.lower() for e in entities if e.type == "SYMPTOM"}
        history = {e.value.lower() for e in entities if e.type == "HISTORY"}
        _, plan_items, _ = self._select_differentials(symptoms | history)
        if not plan_items:
            plan_items = ["Further clinical assessment", "Investigations as indicated",
                          "Follow-up as clinically required"]

        # Fix 5: Remove ECG/Troponin from plan if musculoskeletal chest pain and no cardiac signal
        is_msk_only = (
            "musculoskeletal chest pain" in symptoms and
            not (symptoms & self._CARDIAC_SIGNALS)
        )
        if is_msk_only:
            _CARDIAC_PLAN_ITEMS = {
                "ECG urgently", "Troponin", "ECG", "Troponin if cardiac ischemia suspected",
                "ECG to rule out ischemia",
            }
            plan_items = [p for p in plan_items if p not in _CARDIAC_PLAN_ITEMS]
            # Add safety note that ECG still recommended if any cardiac features develop
            plan_items.insert(0, "ECG to rule out ischemia if any cardiac features develop")

        plan_items = self._dedup_plan(plan_items)
        return " ".join(f"{item}." if not item.endswith(".") else item for item in plan_items)

    def _extract_global_onset(self, text: str) -> Optional[str]:
        """Extract first onset qualifier found in text. Global search — not per-symptom (Phase 1 limitation)."""
        m = _ONSET_RE.search(text)
        return m.group(1) if m else None

    # ── Vietnamese SOAP builders (MV-FID-017) ─────────────────────────────────

    # CA-031: clinical findings not displayed in Subjective (belong in A/P)
    _S_EXCLUDE = {"CT no hemorrhage", "tPA contraindicated", "thrombectomy indicated",
                  "CT no haemorrhage", "ischemic stroke confirmed"}

    def _build_subjective_vi(self, entities: List[NEREntity], text: str) -> str:
        age = next((e.value for e in entities if e.type == "AGE"), None)
        gender = next((e.value for e in entities if e.type == "GENDER"), None)
        # Filter out clinical findings — not symptoms
        symptoms = [e.value for e in entities
                    if e.type == "SYMPTOM" and not e.negated
                    and e.value not in self._S_EXCLUDE]
        onset_entity = next((e for e in entities if e.type == "SYMPTOM" and e.onset), None)

        gender_vi = {"male": "nam", "female": "nữ"}.get(gender, "") if gender else ""

        if age and gender_vi:
            subject = f"Bệnh nhân {gender_vi} {age} tuổi"
        elif age:
            subject = f"Bệnh nhân {age} tuổi"
        else:
            subject = "Bệnh nhân"

        if symptoms:
            # B1: Dedup VI display strings (e.g. "dysarthria"+"noi kho." -> both show "noi kho")
            seen_s: set = set()
            syms_vi: List[str] = []
            for s in symptoms:
                display = _VI_SYMPTOM_DISPLAY.get(s, s).rstrip('.,')
                if display.lower() not in seen_s:
                    seen_s.add(display.lower())
                    syms_vi.append(display)
            onset_str = f" ({onset_entity.onset})" if onset_entity and onset_entity.onset else ""
            return f"{subject}, triệu chứng {', '.join(syms_vi)}{onset_str}."
        return f"{subject} đến khám tư vấn."  # ≥ 20 chars — validate_soap minimum

    # A2: Vietnamese display for DIAGNOSTIC entity values
    _DIAGNOSTIC_DISPLAY_VI = {
        "CT no hemorrhage":      "CT: không xuất huyết",
        "tPA contraindicated":   "tPA: chống chỉ định",
        "thrombectomy indicated":"Thrombectomy: có chỉ định",
    }

    def _build_objective_vi(self, entities: List[NEREntity]) -> str:
        parts = []
        for v in (e for e in entities if e.type == "VITAL"):
            name = v.name.replace("_", " ").title() if v.name else ""
            parts.append(f"{name}: {v.value} {v.unit or ''}".strip())
        for m in (e for e in entities if e.type == "MEDICATION"):
            freq = f" {m.frequency}" if m.frequency else ""
            parts.append(f"Đang dùng {m.value} {m.dose or ''}{freq}.")
        # A2: Add DIAGNOSTIC findings (CT/MRI/ECG results) to Objective
        for d in (e for e in entities if e.type == "DIAGNOSTIC"):
            display = self._DIAGNOSTIC_DISPLAY_VI.get(d.value, d.value)
            parts.append(f"Kết quả cận lâm sàng: {display}.")
        if not parts:
            parts.append("Dấu hiệu sinh tồn và kết quả khách quan đang chờ ghi nhận.")
        return " ".join(parts)

    def _build_assessment_vi(self, entities: List[NEREntity], text: str) -> str:
        symptoms    = {e.value.lower() for e in entities if e.type == "SYMPTOM"    and not e.negated}
        history     = {e.value.lower() for e in entities if e.type == "HISTORY"    and not e.negated}
        diagnostics = {e.value.lower() for e in entities if e.type == "DIAGNOSTIC"}
        signals = symptoms | history | diagnostics

        differentials, _, _ = self._select_differentials(signals)
        if not differentials:
            # always use the registered DDX key so _VI_DDX_DISPLAY lookup succeeds
            differentials = ["Undifferentiated presenting complaint — further evaluation required"]

        # Use DIAGNOSTIC entity values as primary override check.
        # Fallback to translated text. Avoids MarianMT translation quality issues.
        diag_text = " ".join(e.value for e in entities if e.type == "DIAGNOSTIC")
        differentials = self._apply_diagnostic_override(differentials, diag_text or text, text)
        # B4: Limit DDx to top 8 items — clinical readability
        differentials = differentials[:8]
        # B3: Convert EN DDx strings to VI display
        differentials_vi = [_VI_DDX_DISPLAY.get(d, d) for d in differentials]
        # Dedup display strings (same VI text from different EN spellings)
        seen_vi: set = set()
        differentials_vi = [v for v in differentials_vi if v.lower() not in seen_vi and not seen_vi.add(v.lower())]
        ddx_str = ". DDx: " + ", ".join(differentials_vi) + "."

        # CA-031: prioritise clinically significant chief complaint (VI)
        _PRIORITY_VI = [
            "ischemic stroke", "hemorrhagic stroke", "right hemiparesis", "left hemiparesis",
            "hemiparesis", "myocardial infarction", "stroke", "sepsis", "coma",
            "trauma", "severe pneumonia", "thrombectomy indicated",
            "right facial numbness", "left facial numbness", "right arm weakness",
            "left arm weakness", "right leg weakness", "left leg weakness",
            "right hemibody numbness", "dysarthria", "facial droop",
        ]
        chief_symptom = next(
            (s for s in _PRIORITY_VI if s in symptoms),
            next(iter(symptoms), "triệu chứng")
        )
        chief_vi = _VI_SYMPTOM_DISPLAY.get(chief_symptom, chief_symptom).capitalize()
        history_vi = [_VI_HISTORY_DISPLAY.get(h, h) for h in history]
        history_str = f" ở bệnh nhân có tiền sử {', '.join(history_vi)}" if history_vi else ""

        return f"{chief_vi}{history_str}{ddx_str}"

    def _build_plan_vi(self, entities: List[NEREntity], text: str) -> str:
        symptoms = {e.value.lower() for e in entities if e.type == "SYMPTOM"}
        history = {e.value.lower() for e in entities if e.type == "HISTORY"}
        _, plan_items, _ = self._select_differentials(symptoms | history)

        if not plan_items:
            plan_items = ["Further clinical assessment", "Investigations as indicated",
                          "Follow-up as clinically required"]

        # Fix 3: dedup + limit to 8 items
        plan_items = self._dedup_plan(plan_items, max_items=8)
        plan_vi = [_VI_PLAN_DISPLAY.get(item, item) for item in plan_items]
        return " ".join(f"{item}." if not item.endswith(".") else item for item in plan_vi)
