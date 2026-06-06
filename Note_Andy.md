05/06/26

ĐÁNH GIÁ HIỆN TRẠNG — CÓ THỂ TIẾP TỤC KHÔNG
✅ Sẵn sàng (không cần làm thêm)
Thứ	Trạng thái
Pipeline L0→L10	✅ DONE — 388/388 PASS
Deploy Windows	✅ DONE — install.bat + start.bat
L4 Correction Capture	✅ DONE — tự học từ BS corrections
Semi-synthetic plan + scripts	✅ DONE — 20 scripts × 4 BS sẵn
Dataset catalog + download script	✅ DONE — P1 ready to pull
🔴 Blockers — Andy phải làm trước khi tiến tiếp
ID	Việc	Tại sao chặn
LEGAL-001	Thuê luật sư VN (healthtech + AI)	Chặn launch thương mại. Nếu pilot xong mà chưa có luật sư → không ký hợp đồng được
ONBOARD-001	Ký docs/compliance/BS_ONBOARDING_CHECKLIST.md với từng BS pilot	Bắt buộc trước khi BS đưa audio thật vào hệ thống (NĐ13/2023 consent)
PA-008	Tìm 4 người (HN/SG/CT/CA) ghi âm 5 scripts	Chặn BENCH-002a → không có data để calibrate → không biết hệ thống đang yếu ở đâu
🟡 Việc Claude có thể làm ngay (không cần Andy)
Task	Action	Kết quả
DATASET-001	python -X utf8 scripts/download_datasets.py	Tải ~6.6 GB P1 datasets
DATASET-002	Phân tích VietMed-NER 18 entity types → map MediVoice	Chuẩn bị training pipeline NER
DRUG-DB expand	Mine DRUGCHEMICAL từ VietMed-NER sau khi tải	Drug_db.json 110 → 500+ thuốc
Trả lời thẳng
Về code: Có thể tiếp tục ngay — 388 tests PASS, pipeline clean, deploy script sẵn.

Về pilot Đà Nẵng: Chưa được — cần ONBOARD-001 (ký consent BS) + LEGAL-001 (luật sư) trước khi thu audio bệnh nhân thật.

Về datasets/training: Có thể bắt đầu ngay — chạy scripts/download_datasets.py là được.

Nút thắt cổ chai thực sự là PA-008 (4 người ghi âm) — đây là thứ duy nhất Andy cần làm để dự án tiến được đến BENCH-002a → calibrate → pilot thật. Tất cả thứ khác đã sẵn sàng chờ data này.

Muốn làm gì tiếp theo?

A. Chạy download datasets P1 ngay (Claude làm — cần disk ~7 GB)
B. Đóng phiên và commit
C. Làm task khác trong BACKLOG

----------------------
1. CLAUDE ĐỦ DATA ĐI TIẾP CHƯA?
Chưa đủ. Lý do cụ thể:

Cần gì	Có gì	Gap
NER clinical outpatient VN	VietMed-NER (YouTube lecture/media)	Domain khác — "ung thư, béo phì, parkinson" ≠ "viêm họng, kê Amoxicillin 3 lần/ngày"
Drug corpus prescription VN	drug_db.json 118 thuốc	Thiếu 90% thuốc phòng khám thực tế
Vital signs extraction	Regex tự build	Không có training data số thực (38.5°C, 120/80)
Spoken outpatient transcripts	Semi-synthetic scripts (chờ PA-008)	Chưa có 1 câu thực tế nào từ phòng khám
Kết luận: Không có dataset nào PUBLIC trên thế giới từ phòng khám ngoại trú tiếng Việt thực tế. Đây là gap thật sự trong literature — pilot Đà Nẵng của Andy sẽ là novel data đầu tiên.

2. DATA REQUIREMENTS — CẦN GÌ CHÍNH XÁC
A. NER Training Data (ưu tiên cao nhất)

ENTITY TYPE    FORMAT THỰC TẾ CẦN CÓ                     VÍ DỤ
─────────────────────────────────────────────────────────────────
MEDICATION     drug_name + dose + freq + route + duration  "Amoxicillin 500mg uống 3 lần/ngày trong 7 ngày"
SYMPTOM        tên triệu chứng (spoken VN)                "đau họng, nuốt khó, sốt nhẹ 37.8"
DIAGNOSIS      bệnh danh + ICD-10 code                    "viêm họng cấp J02.9"
VITAL          số + đơn vị (cần extract số thực)          "nhiệt độ 38.5 độ, huyết áp 130/80, cân 65kg"
FOLLOWUP       ngày/tuần + trigger condition              "tái khám sau 7 ngày nếu không đỡ"
Điều kiện bắt buộc:

Spoken Vietnamese (văn nói, có ừ/thì/mà, không phải văn viết)
Outpatient prescription context (không phải lecture, không phải tin tức)
Phải có drug name + dose + frequency together (tam giác quan trọng nhất)
Đủ 3 miền accent (Bắc/Nam/Tây Nam Bộ)
B. Drug Corpus

Cần: 500-1000 thuốc (vs. 118 hiện tại) với:
  - INN name + Vietnamese brand names
  - Phonetic variants (PhoWhisper mishears)
  - Common dose forms tại VN
  - Route: uống/tiêm/bôi/nhỏ mắt

Nguồn: drugbank.vn (contact DAV) > vinmec.com scrape > ChatGPT generate
C. ASR Fine-tuning Data

Cần: 50-100h audio từ phòng khám thực tế (spontaneous, noisy OK)
Có: VietMed 16h (lecture/media) — useful nhưng domain khác
Gap: 0h real outpatient consultation audio
3. KEYWORDS TÌM THÊM
Tìm trên HuggingFace

vietnamese medical NER
vietnamese clinical NER
vietnamese prescription
vietnamese EHR
vietnamese outpatient
bệnh án tiếng việt
đơn thuốc NER
Tìm trên Google Scholar / Semantic Scholar

"Vietnamese NER" clinical
"Vietnamese medical" dataset NER 2023 2024 2025
"tiếng Việt" "nhận dạng thực thể" y tế
VLSP 2022 medical NER (check VLSP shared task results)
ViHealthBERT downstream tasks
"Vietnamese" "named entity recognition" "prescription"
Kiểm tra các nhóm NLP VN

VinAI Research GitHub → kiểm tra datasets mới sau PhoNER
UIT NLP Group (nlp.uit.edu.vn) → chỉ có ViNewsQA (healthcare QA), không có NER
HUST NLP → Hanoi Univ Science Tech
FPT AI Center → có collaborate với VietMed authors
4. VIMEDNER (CC BY 3.0) — THỰC CHẤT LÀ GÌ
Không phải từ UIT-HCM. Đây là nhầm lẫn tên viết tắt:

Field	Thực tế
Tác giả	Pham Van Duong et al. — Đại học BKHN + FPT + Hung Yên
Paper	EAI INIS 2024
License	CC BY 3.0 ✅
Entity types	5: DISEASE, SYMPTOM, CAUSE, DIAGNOSTIC, TREATMENT
Data source	4 websites y tế VN (không phải phòng khám)
Download	Chưa có — "Download not yet available"
Code	https://github.com/tdtrinh11/ViMedNer (code only)
Action	Email tác giả: tiendat.trinh@... hoặc watch GitHub repo
So với VietMed-NER: ViMedNER có 5 entity types (đơn giản hơn), text domain (không phải spoken), và data chưa có. VietMed-NER vẫn tốt hơn để dùng ngay.

5. SYNTHETIC DATA — YÊU CẦU NẾU KHÔNG CÓ REAL DATA
Nếu Andy muốn generate synthetic data để train NER ngay bây giờ, cần:

Format bắt buộc

{
  "id": "SYN-001",
  "region": "HN | SG | CT | CA",
  "scenario": "viem_hong | da_day | THA | DTD | gout | cam | xuong_khop",
  "transcript": "văn nói tự nhiên có ừ/thì, không phải văn viết",
  "entities": [
    {"text": "Amoxicillin 500mg", "type": "MEDICATION", "start": 12, "end": 29},
    {"text": "3 lần mỗi ngày", "type": "FREQUENCY", "start": 35, "end": 49},
    {"text": "7 ngày", "type": "DURATION", "start": 55, "end": 61},
    {"text": "viêm họng cấp", "type": "DIAGNOSIS", "start": 70, "end": 82},
    {"text": "38.5 độ", "type": "VITAL", "start": 100, "end": 107}
  ]
}
Yêu cầu chất lượng

100 samples minimum × 7 scenarios × 3 regions = 2,100 samples
Mỗi sample PHẢI có: ít nhất 1 MEDICATION + 1 DIAGNOSIS + 1 VITAL hoặc FOLLOWUP
Drug names: lấy từ drug_db.json 118 thuốc
Phonetic errors: thêm 20% samples có lỗi PhoWhisper ("ammos lim", "ban ngày" → test L1b)
Format số: 50% word-form ("ba viên") + 50% digit-form ("3 viên")
Công cụ generate

# Dùng ChatGPT/Claude với prompt cụ thể:
python -X utf8 scripts/generate_synthetic_ner.py  # (chưa có — cần viết)
# Hoặc dùng PA-007 corpus (41 scripts) → annotate entities → train NER
TÓM TẮT: LỘ TRÌNH ĐỦ DATA

HIỆN TẠI (đã có):
  VietMed-NER + ViMQ + VN Medical QA → seed vocabulary
  drug_db.json 118 thuốc → L1b correction

NGẮN HẠN (1-2 tuần) — Andy cần làm:
  PA-008: 4 người × 5 scripts × 2 takes → 20 audio (BENCH-002a)
  PA-007: ChatGPT 41 scripts → annotate entities → 2,100 synthetic NER samples

TRUNG HẠN (sau pilot):
  L4 Correction Capture → tự thu thập real corrections từ BS
  analyze_corrections.py sau 10+ approvals → mở rộng drug_db
  Fine-tune NER (TRAIN-002) khi có 500+ samples

DÀI HẠN (3-6 tháng):
  Pilot audio → novel outpatient VN NER dataset (đầu tiên trên thế giới)
  Contact DAV → drugbank.vn bulk data
  Fine-tune PhoWhisper (TRAIN-001) khi có 50h+ audio thực tế
  ============

  v0.7.1 | 395/395 PASS | Pushed ✅

Phiên này đã làm:

#	Việc	Kết quả
1	generate_synthetic_ner.py	2100 BIO samples, 7 scenarios × 4 vùng miền
2	test_synthetic_ner_pipeline.py	7 tests: Drug 97-100% · CD 63-80% · Vital 63-77%
3	chan_doan regex fix	10/10 patterns pass — ". filler Kê", ICD code, "bị gout cấp"
4	drug_db.json v0.2.0	110 → 118 drugs
5	VietMed datasets	NER 9K + Sum 106K + QA 9K downloaded
6	Docs	DATA_CATALOG + RECORDING_SCRIPTS + SEMI_SYNTHETIC_PLAN
Andy cần làm tiếp:

PA-008 🔴 Tìm 4 người (HN/SG/CT/CA) ghi âm 5 scripts — unblock BENCH-002a
PA-006 🟡 Điền dental ground truth labels
PA-007 🟡 ChatGPT corpus generation