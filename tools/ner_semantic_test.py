#!/usr/bin/env python3
"""NER semantic capture test — chạy NER trên HYP transcript thực tế."""
import sys
sys.path.insert(0, "src")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.l1b_drug_correct import correct_drug_names, extract_drug_candidates
from core.l1c_ner import extract_entities

# ── HYP transcripts thật từ PhoWhisper (giữ nguyên dấu) ─────────────────────
CASES = {
    "BS1 SC-01 (WER=8.1%)": (
        "ừm bệnh nhân nam bốn mươi hai tuổi nghề nghiệp kế toán "
        "lý do vào khám đau họng ba ngày nay nuốt khó "
        "ừ bệnh nhân tự uống paracetamol nhưng không đỡ "
        "huyết áp một trăm hai mươi trên tám mươi "
        "mạch tám mươi nhiệt độ ba mươi bảy phẩy tám cân nặng bảy mươi ki lô "
        "họng đỏ amidan hai bên sưng to không có mủ không có hạch cổ "
        "chẩn đoán viêm họng cấp "
        "amoxicillin năm trăm miligam uống ba lần một ngày trong năm ngày "
        "paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ "
        "tái khám sau năm ngày hoặc sớm hơn nếu sốt cao không hạ"
    ),
    "BS2 SC-01 (WER=19.3%)": (
        "bệnh nhân năm bốn hai tuổi kế toán đầu học ba ngày nay nuốt khó "
        "uống thuốc hạ sốt mà hổng đỡ "
        "huyết áp một hai mươi trên tám mươi mạch tám mươi "
        "sốt ba bảy phẩy tám nặng bảy mươi ký "
        "họng đỏ amidan sưng hai bên hông có mủ hông có hạch "
        "viêm họng cấp "
        "amoxicillin năm trăm ba lần một ngày năm ngày nha "
        "paracetamol năm trăm khi sốt "
        "tái khám năm ngày nặng hơn thì vô sớm nha"
    ),
}

# Ground truth SC-01
GT_DRUGS    = ["Amoxicillin", "Paracetamol"]
GT_CHANDOAN = "viêm họng cấp"
GT_HA       = (120, 80)
GT_NHIETDO  = 37.8
GT_MACH     = 80
GT_CANNANG  = 70.0
GT_TAIKHAM  = "5"

print("=" * 65)
print("  NER Semantic Capture — HYP transcript thực tế PhoWhisper")
print("=" * 65)

for label, hyp in CASES.items():
    corrected = correct_drug_names(hyp)
    cands     = extract_drug_candidates(corrected)
    ents      = extract_entities(corrected, cands)

    drugs_found = [d["inn"] for d in ents.don_thuoc]
    drug_hit    = sum(1 for g in GT_DRUGS
                      if any(g.lower() in f.lower() for f in drugs_found))
    cd_ok  = GT_CHANDOAN.lower() in (ents.chan_doan or "").lower()
    ha_ok  = (ents.huyet_ap_tam_thu == GT_HA[0] and
               ents.huyet_ap_tam_truong == GT_HA[1])
    nd_ok  = ents.nhiet_do is not None and abs(ents.nhiet_do - GT_NHIETDO) < 0.2
    mc_ok  = ents.mach is not None and abs(ents.mach - GT_MACH) <= 2
    cn_ok  = ents.can_nang is not None and abs(ents.can_nang - GT_CANNANG) <= 1
    tk_ok  = GT_TAIKHAM in (ents.tai_kham or "")

    score  = sum([drug_hit == len(GT_DRUGS), cd_ok, ha_ok, nd_ok, mc_ok, cn_ok, tk_ok])
    total  = 7

    print(f"\n  [{label}]")
    print(f"  {'Entity':<18} {'Extracted':<30} {'GT':<20} {'OK'}")
    print(f"  {'-'*75}")
    print(f"  {'Drugs':<18} {str(drugs_found):<30} {str(GT_DRUGS):<20} {'✅' if drug_hit==len(GT_DRUGS) else f'⚠️ {drug_hit}/{len(GT_DRUGS)}'}")
    print(f"  {'Chan doan':<18} {str(ents.chan_doan):<30} {GT_CHANDOAN:<20} {'✅' if cd_ok else '❌'}")
    cd_err = "" if cd_ok else f"  ← ASR: 'đầu học'→miss" if "BS2" in label else ""
    if cd_err: print(f"  {'':<18} {cd_err}")
    print(f"  {'Huyet ap':<18} {str(ents.huyet_ap_tam_thu)}/{str(ents.huyet_ap_tam_truong):<26} 120/80               {'✅' if ha_ok else '❌'}")
    print(f"  {'Nhiet do':<18} {str(ents.nhiet_do):<30} 37.8                 {'✅' if nd_ok else '❌'}")
    print(f"  {'Mach':<18} {str(ents.mach):<30} 80                   {'✅' if mc_ok else '❌'}")
    print(f"  {'Can nang':<18} {str(ents.can_nang):<30} 70.0                 {'✅' if cn_ok else '❌'}")
    print(f"  {'Tai kham':<18} {str(ents.tai_kham):<30} 5 ngay               {'✅' if tk_ok else '❌'}")
    print(f"  {'─'*75}")
    print(f"  NER Score: {score}/{total} = {score/total:.0%}")
