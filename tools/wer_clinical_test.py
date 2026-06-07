#!/usr/bin/env python3
"""
tools/wer_clinical_test.py — WER test trên clinical WAV (lâm sàng)
Model: PhoWhisper-medium (vinai)
Data:  data/synthetic_audio/wav/  (60 WAV: 4 BS × 5 SC × 3 vùng miền)
Ref:   docs/dev/RECORDING_SCRIPTS_4BS.md — đúng script từng BS

Cấu trúc WAV: BS{1-4}_{Hanoi|Hue|Nam}_SC-{01-05}.wav
  BS1 → Hà Nội (giọng Bắc chuẩn, formal)
  BS2 → TP.HCM (giọng Nam nhanh, bỏ từ)
  BS3 → Cần Thơ (giọng Tây Nam Bộ, chậm)
  BS4 → Canada (code-switching Anh-Việt)
  Hanoi/Hue/Nam → 3 vùng miền người nghe/take

Usage:
    python tools/wer_clinical_test.py
    python tools/wer_clinical_test.py --scenario SC-01
    python tools/wer_clinical_test.py --bs BS2
    python tools/wer_clinical_test.py --region Hue
"""

from __future__ import annotations
import re, sys, argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# TTS cũ (60 files: BS1_Hanoi_SC-01.wav)
WAV_DIR_TTS  = Path("data/synthetic_audio/wav")
# PA-008 thật (40 files: SC01_HN_take1.wav)
WAV_DIR_REAL = Path("data/audio/corpus/semi_synthetic")

# Region code → BS key trong REFERENCE
REGION_TO_BS = {"HN": "BS1", "SG": "BS2", "CT": "BS3", "CA": "BS4"}

# ── Reference: 4 BS × 5 SC — trích từ RECORDING_SCRIPTS_4BS.md ──────────────
# Cleaned: bỏ [DỪNG Xs], [NHANH], [CHẬM] — giữ nguyên lời nói thật

REFERENCE = {
    # ── BS1: Hà Nội — giọng Bắc chuẩn, formal ──────────────────────────────
    "BS1": {
        "SC-01": (
            "Ừm bệnh nhân nam bốn mươi hai tuổi nghề nghiệp kế toán "
            "Lý do vào khám đau họng ba ngày nay nuốt khó "
            "Ừ bệnh nhân tự uống Paracetamol nhưng không đỡ "
            "Khám tình trạng tỉnh táo tiếp xúc tốt "
            "Huyết áp một trăm hai mươi trên tám mươi "
            "Mạch tám mươi Nhiệt độ ba mươi bảy phẩy tám Cân nặng bảy mươi ki lô "
            "Họng đỏ amidan hai bên sưng to không có mủ Không có hạch cổ "
            "Chẩn đoán Viêm họng cấp "
            "Điều trị thì "
            "Amoxicillin năm trăm miligam uống ba lần một ngày trong năm ngày "
            "Paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ "
            "Tái khám sau năm ngày hoặc sớm hơn nếu sốt cao không hạ"
        ),
        "SC-02": (
            "Bệnh nhân nữ ba mươi lăm tuổi "
            "Đau thượng vị hai tuần nay ừ đau âm ỉ đau khi đói giảm sau khi ăn "
            "Có ợ chua đầy bụng Không nôn ra máu không đi phân đen "
            "Tiền sử thì có uống Ibuprofen nhiều lần trong tháng trước do đau khớp "
            "Huyết áp một trăm mười trên bảy mươi Mạch bảy mươi lăm "
            "Bụng mềm ấn đau vùng thượng vị không có phản ứng thành bụng "
            "Chẩn đoán Viêm loét dạ dày tá tràng "
            "Điều trị "
            "Omeprazole hai mươi miligam uống một lần một ngày trước ăn sáng ba mươi phút trong bốn tuần "
            "Domperidone mười miligam uống ba lần một ngày trước bữa ăn "
            "Ngưng Ibuprofen hoàn toàn nhé "
            "Hẹn tái khám sau bốn tuần"
        ),
        "SC-03": (
            "Bệnh nhân nam sáu mươi tuổi nghề nghiệp lái xe "
            "Tái khám tăng huyết áp định kỳ "
            "Đo huyết áp lần một một trăm bảy mươi trên một trăm "
            "Đo lại lần hai sau năm phút một trăm sáu mươi lăm trên chín mươi lăm "
            "Bệnh nhân khai đã uống thuốc đều không bỏ liều "
            "Ừ không đau đầu không chóng mặt không khó thở "
            "Đang dùng Amlodipine năm miligam một viên mỗi ngày "
            "Đánh giá huyết áp chưa kiểm soát được "
            "Điều chỉnh điều trị "
            "Tăng Amlodipine lên mười miligam mỗi ngày "
            "Thêm Losartan năm mươi miligam uống một lần một ngày buổi sáng "
            "Theo dõi huyết áp tại nhà sáng tối ghi vào sổ Hạn chế muối "
            "Tái khám sau hai tuần nhớ mang sổ huyết áp"
        ),
        "SC-04": (
            "Bệnh nhân nữ năm mươi lăm tuổi nội trợ "
            "Tiền sử đái tháo đường type hai tám năm nay "
            "Tái khám định kỳ "
            "Đường huyết đói sáng nay chín phẩy ba milimol trên lít "
            "HbA1c tháng trước tám phẩy hai phần trăm "
            "Bệnh nhân khai ăn uống khó kiểm soát hay ăn nhiều cơm "
            "Ừ uống Metformin đều không bỏ liều "
            "Huyết áp một trăm ba mươi trên tám mươi lăm Mạch tám mươi hai "
            "Cân nặng bảy mươi tám ki lô "
            "Khám không có phù nề mạch mu bàn chân bình thường "
            "Ừm cảm giác hai bàn chân giảm nhẹ "
            "Chẩn đoán Đái tháo đường type hai chưa kiểm soát tốt "
            "Biến chứng thần kinh ngoại biên nhẹ "
            "Điều trị "
            "Giữ Metformin năm trăm miligam uống hai lần một ngày sau ăn "
            "Thêm Glimepiride hai miligam uống một lần trước ăn sáng "
            "Vitamin B1 B6 B12 uống một viên một ngày "
            "Hẹn xét nghiệm lại HbA1c sau ba tháng Tái khám sau một tháng"
        ),
        "SC-05": (
            "Bệnh nhân nam bảy mươi tuổi "
            "Đau ngón chân cái phải đột ngột từ đêm qua sưng đỏ nóng "
            "Ờ bệnh nhân có uống bia hôm qua khoảng mười lon "
            "Tiền sử gout ba năm nay không uống thuốc đều "
            "Huyết áp một trăm ba mươi trên tám mươi Mạch tám mươi lăm "
            "Axit uric máu tuần trước tám phẩy ba milimol "
            "Khám ngón chân cái phải sưng to đỏ đau khi chạm "
            "Chẩn đoán Gout cấp ngón chân cái phải "
            "Điều trị "
            "Colchicine không phẩy năm miligam uống hai viên ngay "
            "sau đó một viên mỗi giờ cho đến khi đỡ đau "
            "tối đa sáu viên trong hai mươi bốn giờ "
            "Etoricoxib sáu mươi miligam uống một lần một ngày sau ăn trong năm ngày "
            "Tuyệt đối không uống bia rượu Uống nhiều nước vào "
            "Tái khám sau một tuần xem xét thuốc hạ axit uric dài hạn"
        ),
    },

    # ── BS2: TP.HCM — giọng Nam nhanh, bỏ từ, "hổng/hông" ──────────────────
    "BS2": {
        "SC-01": (
            "Bệnh nhân nam bốn hai tuổi kế toán "
            "Đau họng ba ngày nay nuốt khó Uống thuốc hạ sốt mà hổng đỡ "
            "Huyết áp một hai mươi trên tám mươi Mạch tám mươi "
            "Sốt ba bảy phẩy tám Nặng bảy mươi ký "
            "Họng đỏ amidan sưng hai bên hông có mủ Hông có hạch "
            "Viêm họng cấp "
            "Toa "
            "Amoxicillin năm trăm ba lần một ngày năm ngày nha "
            "Paracetamol năm trăm khi sốt "
            "Tái khám năm ngày Nặng hơn thì vô sớm nha"
        ),
        "SC-02": (
            "Bệnh nhân nữ ba lăm tuổi "
            "Đau bụng trên hai tuần đói đau ăn vô thì đỡ Ợ chua đầy bụng "
            "Hổng nôn máu hổng đi phân đen "
            "Tiền sử uống Ibuprofen nhiều tháng rồi do đau khớp "
            "Huyết áp một mười trên bảy mươi Mạch bảy lăm "
            "Bụng mềm ấn đau thượng vị Hổng có phản ứng thành bụng "
            "Viêm loét dạ dày tá tràng "
            "Toa "
            "Omeprazole hai mươi một lần trước ăn sáng ba mươi phút bốn tuần "
            "Domperidone mười ba lần trước ăn "
            "Ngưng Ibuprofen luôn nha "
            "Tái khám bốn tuần"
        ),
        "SC-03": (
            "Bệnh nhân nam sáu mươi tuổi lái xe Tái khám huyết áp "
            "Đo lần một một bảy mươi trên một trăm "
            "Đo lại lần hai một sáu lăm trên chín lăm "
            "Thuốc uống đều hông có bỏ Hổng đau đầu hổng chóng mặt "
            "Amlodipine năm một viên mỗi ngày "
            "Huyết áp chưa kiểm soát "
            "Tăng Amlodipine lên mười "
            "Thêm Losartan năm mươi uống sáng "
            "Theo dõi huyết áp ở nhà ghi sổ Ít muối thôi "
            "Tái khám hai tuần mang sổ nha"
        ),
        "SC-04": (
            "Bệnh nhân nữ năm lăm tuổi nội trợ Tiểu đường loại hai tám năm rồi "
            "Tái khám Đường đói sáng nay chín phẩy ba "
            "HbA1c tháng rồi tám phẩy hai phần trăm "
            "Ăn khó giữ lắm Metformin thì uống đều "
            "Huyết áp một ba mươi trên tám lăm Mạch tám hai Nặng bảy mươi tám ký "
            "Hổng phù Mạch mu bàn chân bình thường Cảm giác hai bàn chân giảm nhẹ "
            "Tiểu đường loại hai chưa kiểm soát Có biến chứng thần kinh nhẹ "
            "Toa "
            "Giữ Metformin năm trăm hai lần sau ăn "
            "Thêm Glimepiride hai một lần trước ăn sáng "
            "Vitamin B tổng hợp một viên mỗi ngày "
            "HbA1c lại ba tháng Tái khám một tháng nha"
        ),
        "SC-05": (
            "Bệnh nhân nam bảy mươi tuổi "
            "Đau ngón cái phải đêm qua sưng đỏ nóng "
            "Uống bia hôm qua khoảng mười lon Gout ba năm thuốc uống hổng đều "
            "HA một ba mươi trên tám mươi Mạch tám lăm "
            "Uric tuần rồi tám phẩy ba milimol "
            "Ngón cái phải sưng to đỏ đau khi chạm "
            "Gout cấp ngón cái phải "
            "Toa "
            "Colchicine không phẩy năm hai viên ngay "
            "sau đó một viên mỗi giờ tối đa sáu viên trong hai mươi bốn giờ "
            "Etoricoxib sáu mươi một lần sau ăn năm ngày "
            "Hổng được uống bia rượu nghen Nhiều nước vô "
            "Một tuần tái khám xem thuốc hạ uric dài hạn"
        ),
    },

    # ── BS3: Cần Thơ — giọng Tây Nam Bộ, chậm, "dó/tui/dùng cơm" ──────────
    "BS3": {
        "SC-01": (
            "Bệnh nhân nam bốn mươi hai tuổi làm kế toán "
            "Ờ lý do vô khám là đau họng ba bữa nay nuốt khó "
            "Tự uống thuốc hạ sốt mà hổng thấy đỡ "
            "Huyết áp một trăm hai mươi trên tám mươi "
            "Mạch tám mươi Sốt ba mươi bảy phẩy tám "
            "Cân nặng bảy mươi ký "
            "Họng đỏ amidan hai bên sưng to hổng có mủ "
            "Hổng có hạch cổ "
            "Chẩn đoán là viêm họng cấp "
            "Điều trị "
            "Amoxicillin năm trăm miligam uống ba lần một ngày trong năm ngày "
            "Paracetamol năm trăm miligam uống khi sốt "
            "Tái khám sau năm ngày "
            "Sốt cao hổng hạ thì vô sớm hơn dó"
        ),
        "SC-02": (
            "Bệnh nhân nữ ba mươi lăm tuổi "
            "Ờ đau bụng trên hai tuần rồi đau khi đói "
            "dùng cơm vô thì đỡ hơn "
            "Ợ chua đầy bụng Hổng nôn ra máu hổng đi phân đen "
            "Tiền sử uống Ibuprofen nhiều lần tháng rồi do đau khớp "
            "Huyết áp một trăm mười trên bảy mươi Mạch bảy lăm "
            "Bụng mềm ấn đau vùng thượng vị Hổng có phản ứng thành bụng "
            "Chẩn đoán viêm loét dạ dày tá tràng "
            "Cho thuốc "
            "Omeprazole hai mươi miligam uống sáng trước ăn ba mươi phút trong bốn tuần "
            "Domperidone mười miligam ba lần trước bữa ăn "
            "Ngưng Ibuprofen luôn nha "
            "Hẹn tái khám bốn tuần"
        ),
        "SC-03": (
            "Bệnh nhân nam sáu mươi tuổi nghề lái xe "
            "Tái khám huyết áp "
            "Đo lần một một trăm bảy mươi trên một trăm "
            "Đo lần hai sau năm phút một trăm sáu mươi lăm trên chín mươi lăm "
            "Thuốc uống đều hổng có bỏ Hổng đau đầu hổng chóng mặt "
            "Đang uống Amlodipine năm miligam một viên mỗi ngày "
            "Huyết áp chưa kiểm soát được "
            "Tăng Amlodipine lên mười miligam "
            "Thêm Losartan năm mươi miligam uống sáng mỗi ngày "
            "Ghi huyết áp sáng tối ở nhà ghi vô sổ Ăn ít muối thôi "
            "Tái khám hai tuần mang sổ theo dó"
        ),
        "SC-04": (
            "Bệnh nhân nữ năm mươi lăm tuổi nội trợ "
            "Có tiểu đường từ tám năm nay "
            "Tái khám định kỳ "
            "Đường đói sáng nay chín phẩy ba milimol "
            "HbA1c tháng rồi tám phẩy hai phần trăm "
            "Bệnh nhân khai khó giữ ăn hay dùng cơm nhiều "
            "Uống Metformin thì đều "
            "Huyết áp một trăm ba mươi trên tám mươi lăm "
            "Mạch tám mươi hai Cân nặng bảy mươi tám ký "
            "Hổng có phù nề Mạch mu bàn chân bình thường "
            "Cảm giác hai bàn chân giảm nhẹ "
            "Chẩn đoán là tiểu đường loại hai chưa kiểm soát tốt "
            "Có biến chứng thần kinh ngoại biên nhẹ "
            "Điều trị "
            "Giữ Metformin năm trăm miligam hai lần mỗi ngày sau ăn "
            "Thêm Glimepiride hai miligam một lần trước ăn sáng "
            "Vitamin B tổng hợp một viên mỗi ngày "
            "Xét nghiệm HbA1c lại sau ba tháng "
            "Tái khám sau một tháng"
        ),
        "SC-05": (
            "Bệnh nhân nam bảy mươi tuổi "
            "Ờ đau ngón chân cái phải từ đêm qua sưng đỏ nóng "
            "Uống bia hôm qua khoảng mười lon "
            "Gout ba năm rồi uống thuốc hổng đều "
            "Huyết áp một trăm ba mươi trên tám mươi Mạch tám mươi lăm "
            "Uric tuần rồi tám phẩy ba milimol "
            "Ngón chân cái phải sưng to đỏ đau khi chạm vô "
            "Chẩn đoán gout cấp ngón chân cái phải "
            "Điều trị "
            "Colchicine không phẩy năm miligam uống hai viên ngay "
            "rồi một viên mỗi giờ cho đến khi đỡ đau "
            "tối đa sáu viên trong hai mươi bốn giờ "
            "Etoricoxib sáu mươi miligam một lần sau ăn trong năm ngày "
            "Tuyệt đối hổng uống bia rượu nha Nhiều nước vô "
            "Tái khám một tuần xem xét thuốc hạ uric dài hạn"
        ),
    },

    # ── BS4: Canada — code-switching Việt-Anh tự nhiên ───────────────────────
    "BS4": {
        "SC-01": (
            "Bệnh nhân nam bốn mươi hai tuổi làm kế toán "
            "Euh chief complaint là đau họng ba ngày nuốt khó "
            "Patient tự dùng Paracetamol at home nhưng không bớt "
            "Vitals blood pressure một hai mươi trên tám mươi "
            "Mạch tám mươi Temperature ba bảy phẩy tám Cân nặng bảy mươi kg "
            "Throat exam họng đỏ amidan sưng hai bên không có exudate "
            "Không hạch cổ "
            "Diagnosis viêm họng cấp acute pharyngitis "
            "Treatment "
            "Amoxicillin năm trăm mg ba lần mỗi ngày trong năm ngày "
            "Paracetamol năm trăm mg uống khi sốt trên ba mươi tám "
            "Follow up sau năm ngày hoặc trước nếu sốt không hạ"
        ),
        "SC-02": (
            "Bệnh nhân nữ ba mươi lăm tuổi "
            "Chief complaint epigastric pain hai tuần nay "
            "worse khi đói better sau khi ăn "
            "Có ợ chua bloating Không nôn máu không melena "
            "History dùng Ibuprofen thường xuyên tháng trước vì joint pain "
            "BP một mười trên bảy mươi Mạch bảy lăm "
            "Abdomen mềm tender vùng epigastric Không có peritoneal signs "
            "Diagnosis peptic ulcer disease viêm loét dạ dày tá tràng "
            "Prescription "
            "Omeprazole hai mươi mg một lần mỗi ngày trước breakfast ba mươi phút bốn tuần "
            "Domperidone mười mg ba lần trước ăn "
            "Stop Ibuprofen completely "
            "Follow up bốn tuần"
        ),
        "SC-03": (
            "Bệnh nhân nam sáu mươi tuổi lái xe "
            "Follow up cho hypertension hôm nay "
            "Blood pressure lần một một bảy mươi trên một trăm "
            "Repeat sau năm phút một sáu lăm trên chín lăm "
            "Patient báo medication compliance tốt không bỏ thuốc "
            "Không đau đầu không chóng mặt "
            "Currently on Amlodipine năm mg một viên mỗi ngày "
            "So huyết áp chưa controlled "
            "Adjustment "
            "Increase Amlodipine lên mười mg mỗi ngày "
            "Add Losartan năm mươi mg uống buổi sáng "
            "Monitor BP at home sáng tối ghi log Giảm salt intake "
            "Follow up hai tuần mang log theo"
        ),
        "SC-04": (
            "Bệnh nhân nữ năm mươi lăm tuổi nội trợ "
            "History of type two diabetes tám năm "
            "Euh routine follow up hôm nay "
            "Fasting glucose sáng nay chín phẩy ba mmol per liter "
            "HbA1c tháng trước tám phẩy hai percent "
            "Patient có khó kiểm soát diet Metformin compliance okay "
            "BP một ba mươi trên tám mươi lăm Mạch tám mươi hai Weight bảy mươi tám kg "
            "On exam không phù dorsalis pedis pulses intact "
            "Cảm giác hai bàn chân giảm nhẹ mild peripheral neuropathy "
            "Diagnosis type two diabetes poorly controlled với mild peripheral neuropathy "
            "Plan "
            "Continue Metformin năm trăm mg hai lần mỗi ngày sau ăn "
            "Add Glimepiride hai mg một lần buổi sáng trước ăn "
            "Vitamin B complex một viên mỗi ngày "
            "Repeat HbA1c in ba tháng Follow up một tháng"
        ),
        "SC-05": (
            "Bệnh nhân nam bảy mươi tuổi "
            "Acute onset đau ngón chân cái phải từ đêm qua sưng đỏ nóng "
            "Patient báo uống bia hôm qua khoảng mười lon "
            "History of gout ba năm không compliance với thuốc "
            "BP một ba mươi trên tám mươi Mạch tám mươi lăm "
            "Serum uric acid tuần trước tám phẩy ba mmol "
            "Exam right great toe sưng to đỏ đau khi chạm "
            "Diagnosis acute gouty arthritis gout cấp ngón chân cái phải "
            "Treatment "
            "Colchicine không phẩy năm mg hai viên stat "
            "sau đó một viên mỗi giờ until pain resolves max sáu viên trong hai mươi bốn giờ "
            "Etoricoxib sáu mươi mg một lần sau ăn trong năm ngày "
            "No alcohol completely Uống nhiều nước "
            "Follow up một tuần reassess urate-lowering therapy"
        ),
    },
}


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[.,!?;:()\[\]\"'\-—]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_wav_name(wav: Path) -> tuple[str, str, str] | tuple[None, None, None]:
    """
    Extract (BS, SC, region) từ filename.

    TTS naming:  BS2_Hue_SC-03.wav    → ('BS2', 'SC-03', 'Hue')
    Real naming: SC01_HN_take1.wav    → ('BS1', 'SC-01', 'HN')
    """
    stem = wav.stem
    parts = stem.split("_")

    # Real PA-008 format: SC01_HN_take1
    if parts[0].startswith("SC") and len(parts) >= 2:
        sc_raw = parts[0]                          # SC01
        sc = "SC-" + sc_raw[2:].lstrip("0") or "SC-01"
        sc = f"SC-{sc_raw[2:]:0>2}"               # SC-01
        region_code = parts[1].upper()             # HN / SG / CT / CA
        bs = REGION_TO_BS.get(region_code)
        return bs, sc, region_code

    # TTS format: BS2_Hue_SC-03
    bs = None
    sc = None
    region = "?"
    for i, p in enumerate(parts):
        if p.startswith("BS") and p[2:].isdigit():
            bs = p
        if p.startswith("SC-"):
            sc = p
        if i == 1 and not p.startswith("SC-") and not p.startswith("BS"):
            region = p
    return bs, sc, region


def transcribe_wav(wav_path: Path) -> str:
    import numpy as np
    import soundfile as sf
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from core.l1a_asr import transcribe
    audio, sr = sf.read(str(wav_path), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr)


def wer_score(reference: str, hypothesis: str) -> tuple[float, dict]:
    import jiwer
    ref_c = _clean(reference)
    hyp_c = _clean(hypothesis)
    out = jiwer.process_words(ref_c, hyp_c)
    return out.wer, {
        "wer": out.wer,
        "substitutions": out.substitutions,
        "deletions": out.deletions,
        "insertions": out.insertions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=None, help="SC-01 … SC-05")
    parser.add_argument("--bs",       default=None, help="BS1 | BS2 | BS3 | BS4")
    parser.add_argument("--region",   default=None, help="Hanoi | Hue | Nam")
    parser.add_argument("--no-asr",   action="store_true", help="Skip ASR — debug only")
    args = parser.parse_args()

    wav_files = sorted(WAV_DIR_REAL.rglob("*.wav"))
    if args.scenario:
        wav_files = [w for w in wav_files if args.scenario in w.name]
    if args.bs:
        wav_files = [w for w in wav_files if w.name.startswith(args.bs + "_")]
    if args.region:
        wav_files = [w for w in wav_files if f"_{args.region}_" in w.name]

    if not wav_files:
        print("[ERROR] Không tìm thấy WAV files.")
        sys.exit(1)

    print("=" * 72)
    print(f"  WER Clinical Test — PhoWhisper-medium | MediVoice VN")
    print(f"  Files: {len(wav_files)}  BS: {args.bs or 'all'}  SC: {args.scenario or 'all'}  Region: {args.region or 'all'}")
    print("=" * 72)

    if not args.no_asr:
        print("  [INFO] Loading PhoWhisper-medium (~30s first load)...")

    all_wers: list[float] = []
    by_bs:       dict[str, list[float]] = {}
    by_scenario: dict[str, list[float]] = {}
    by_region:   dict[str, list[float]] = {}

    for wav in wav_files:
        bs, sc, region = _parse_wav_name(wav)

        if bs not in REFERENCE or sc not in REFERENCE.get(bs, {}):
            print(f"  [SKIP] {wav.name} — không có reference (BS={bs}, SC={sc})")
            continue

        ref = REFERENCE[bs][sc]
        print(f"\n  [{wav.name}]")

        if args.no_asr:
            print(f"    REF: {_clean(ref)[:80]}...")
            continue

        hyp = transcribe_wav(wav)
        if not hyp:
            print("    [SKIP] Transcript rỗng")
            continue

        wer, m = wer_score(ref, hyp)
        all_wers.append(wer)
        by_bs.setdefault(bs, []).append(wer)
        by_scenario.setdefault(sc, []).append(wer)
        by_region.setdefault(region, []).append(wer)

        print(f"    HYP: {hyp[:90]}")
        print(f"    REF: {_clean(ref)[:90]}")
        print(f"    WER: {wer:.1%}  (S={m['substitutions']} D={m['deletions']} I={m['insertions']})")

    if not all_wers:
        print("\n  Không có kết quả.")
        return

    def avg(lst): return sum(lst) / len(lst) if lst else 0

    print("\n" + "=" * 72)
    print("  TỔNG KẾT")
    print("=" * 72)
    print(f"  Files tested  : {len(all_wers)}")
    print(f"  Overall WER   : {avg(all_wers):.1%}")
    print()
    print("  Theo BS (accent):")
    for bs in sorted(by_bs):
        print(f"    {bs}: {avg(by_bs[bs]):.1%}  ({len(by_bs[bs])} files)")
    print()
    print("  Theo Scenario (bệnh):")
    for sc in sorted(by_scenario):
        print(f"    {sc}: {avg(by_scenario[sc]):.1%}  ({len(by_scenario[sc])} files)")
    print()
    print("  Theo Region (vùng miền người nghe):")
    for r in sorted(by_region):
        print(f"    {r}: {avg(by_region[r]):.1%}  ({len(by_region[r])} files)")

    ow = avg(all_wers)
    print()
    if ow <= 0.10:
        verdict = "✅ WER ≤ 10% — ASR đủ tốt cho pilot"
    elif ow <= 0.20:
        verdict = "⚠️  WER 10–20% — dùng được, BS cần review kỹ"
    elif ow <= 0.35:
        verdict = "🟡 WER 20–35% — cần fine-tune sau khi có real audio"
    else:
        verdict = "🔴 WER > 35% — cần TRAIN-001 trước khi pilot"
    print(f"  Verdict: {verdict}")
    print("=" * 72)
    print()
    print("  NOTE: Audio này là TTS/synthetic → WER thấp hơn real BS speech ~2x.")
    print("  WER thật cần PA-008 (4 người ghi âm) → chạy lại script này.")
    print("=" * 72)


if __name__ == "__main__":
    main()
