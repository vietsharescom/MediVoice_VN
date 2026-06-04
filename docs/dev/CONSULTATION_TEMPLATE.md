# CONSULTATION_TEMPLATE.md | DS-VN-DEV-004
# MediVoice VN — Multi-AI Consultation System
# v1.0 | 2026-06-06 | Owner: Andy Phan

---

## MỤC ĐÍCH

Khi Claude confused hoặc có multiple valid options, Claude tự generate
file consultation request. Andy copy nội dung → hỏi ChatGPT/Grok →
paste response lại → Claude synthesize + khuyến nghị.

Lưu consultation records tại: `docs/records/consultations/CONS-YYYYMMDD-NNN.md`

---

## KHI NÀO CLAUDE TỰ ĐỘNG GENERATE CONSULTATION

Claude generate consultation (không cần Andy hỏi) khi:

```
TRIGGER TỰ ĐỘNG:
  T1: Có ≥ 2 valid options, không rõ option nào đúng cho bối cảnh VN pháp lý
  T2: Decision cần domain knowledge ngoài scope Claude (luật VN chi tiết, medical standard)
  T3: Architecture choice ảnh hưởng > Phase 1 scope (irreversible design)
  T4: Andy nói: "hỏi thêm AI khác" / "so sánh" / "ý kiến thứ 2"
  T5: Claude cho rằng mình < 70% confident về một decision quan trọng

KHÔNG trigger (Claude tự quyết):
  - Code implementation details
  - Bug fixes và test writing
  - Document updates
  - Tầng 3 features (< 20 LOC)
  - Decisions đã có ADR trong DECISIONS.md
```

---

## TEMPLATE REQUEST (copy sang ChatGPT/Grok)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSULTATION REQUEST [CONS-YYYYMMDD-NNN]
From: Claude Sonnet 4.6 | MediVoice VN | SES-YYYYMMDD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PROJECT CONTEXT
Product: MediVoice VN — AI voice scribe cho phòng mạch tư VN
  BS nói → PhoWhisper ASR → NER → Mẫu 15/BV-01 → BS approve → PDF
Stack: Python 3.10 / FastAPI / PhoWhisper-small / SQLite / Fernet / PWA
Constraints:
  - 100% offline (NĐ13/2023: data tại VN)
  - NOT SaMD (chỉ transcription + form fill, không chẩn đoán)
  - BS phải approve mọi record (Luật KCB 2023 Điều 62)
  - Output: Mẫu 15/BV-01 tiếng Việt (TT32/2023)
Phase: Phase 0 pilot — 5 BS phòng mạch tư Đà Nẵng + SG
ISO: ISO/IEC 42001:2023 + ISO 9001:2015

## QUESTION
[Câu hỏi cụ thể — 1-3 câu rõ ràng]

## OPTIONS EVALUATED

### Option A: [tên option]
Mô tả: [1-2 câu]
Pros:
  - [pro 1]
  - [pro 2]
Cons:
  - [con 1]
  - [con 2]
Risks: [legal/technical/business risk]
Effort: [Low/Medium/High] | Timeline: [estimate]

### Option B: [tên option]
Mô tả: [1-2 câu]
Pros: [list]
Cons: [list]
Risks: [list]
Effort: [Low/Medium/High] | Timeline: [estimate]

## HARD CONSTRAINTS (KHÔNG thể vi phạm)
- [constraint 1 với lý do]
- [constraint 2 với lý do]

## CLAUDE'S CURRENT ANALYSIS
Lean toward: Option [X]
Confidence: [X]%
Main reason: [1-2 câu]
Main uncertainty: [what I'm not sure about]

## WHAT I NEED FROM YOU
Please provide:
1. Your recommendation: A / B / C (other) — with reasoning
2. Confidence level: X%
3. Key risks or considerations I may have missed
4. Is this an owner (Andy) decision vs technical decision? Why?
5. If owner decision: what specific question should Andy answer?

Return format:
  RECOMMENDATION: [A/B/other]
  CONFIDENCE: [X%]
  KEY RISKS: [list]
  OWNER DECISION: [yes/no + why]
  OWNER QUESTION: [if yes, what to ask]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## TEMPLATE SYNTHESIS (sau khi Andy paste response)

Claude điền khi có responses từ các AI:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSULTATION SYNTHESIS [CONS-YYYYMMDD-NNN]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RESPONSES RECEIVED
| AI | Recommendation | Confidence | Key Points |
|----|---------------|------------|------------|
| Claude (original) | Option [X] | [X]% | [main reason] |
| ChatGPT | Option [X] | [X]% | [main reason] |
| Grok | Option [X] | [X]% | [main reason] |

## AGREEMENT ANALYSIS
Points ALL agree on:
  - [point 1]
  - [point 2]

Points with DISAGREEMENT:
  - Issue: [what they disagree on]
    Claude: [position]
    ChatGPT: [position]
    Grok: [position]
    Resolution: [how to resolve the disagreement]

## FINAL RECOMMENDATION
Recommendation: Option [X]
Consolidated confidence: [X]%

Because:
  1. [strongest reason — agreed by majority]
  2. [second reason]
  3. [constraint that eliminates other options]

Risk if wrong: [LOW/MEDIUM/HIGH] — [why]

## OWNER DECISION NEEDED?
[YES / NO]

IF YES:
  Decision for Andy: "[specific question]"
  
  Pro Option A (for Andy's perspective):
    - [business/risk consideration 1]
    - [business/risk consideration 2]
  
  Pro Option B:
    - [business/risk consideration 1]
    - [business/risk consideration 2]
  
  RECOMMENDATION: Option [X]
  UNLESS: [condition where other option is better]
  DEADLINE: [if any — e.g., "needed before VN-ROUTER-001 starts"]

IF NO:
  Claude will proceed with Option [X].
  [Andy can redirect if disagreed.]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## NAMING CONVENTION CHO FILES

```
docs/records/consultations/CONS-YYYYMMDD-NNN.md

Ví dụ:
  CONS-20260606-001.md  ← consultation đầu tiên phiên 2026-06-06
  CONS-20260610-001.md  ← consultation phiên 2026-06-10

NNN bắt đầu từ 001 mỗi ngày.
```

---

## VÍ DỤ THỰC TẾ

```
Tình huống: Claude không chắc về booking engine state machine
  - Option A: 5 states (simple)
  - Option B: 7 states với buffer + waitlist (complex)
  
Claude tự nhận: "Có 2 options, cả 2 valid, VN context unclear → generate consultation"

File tạo ra: CONS-20260606-001.md
Andy copy → hỏi ChatGPT → paste response → Claude synthesize
→ Kết quả: Option B (7 states) — vì chuẩn Canada clinics + no-show problem critical

Decision ghi vào: DECISIONS.md ADR 2026-06-06
```

---

*DS-VN-DEV-004 | CONSULTATION_TEMPLATE v1.0 | 2026-06-06*
