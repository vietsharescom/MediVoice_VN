# FID-VN-006 — L4 Correction Capture (Implicit Supervision)
# MediVoice VN | ISO/IEC 42001:2023 Cl.8.6 (V&V) + Cl.9.1 (Performance evaluation)
# Author: Claude (Sonnet 4.6) | Requested by: Andy Phan
# Date: 2026-06-08 | Status: DRAFT — awaiting Andy approval

---

## WHY

Real-world A-04 testing revealed that ASR noise causes consistent NER misses:
- "amosilic" → Amoxicillin not recognized
- "paracitamol" / "parasyte mode" → Paracetamol not recognized
- "huyết á" (dropped 'p') → blood pressure missed

The Canada pipeline (MarianMT) does better because translation acts as a denoiser.
For the VN direct pipeline, we need a feedback loop.

When BS reviews and edits the AI draft at L4, those edits are **implicit training labels**:
- AI wrote: `don_thuoc = []` → BS corrected to `[{name: "Amoxicillin", ...}]`
- This means ASR said something phonetically close to "amoxicillin" but NER missed it
- Logging this correction lets us: (1) build better aliases, (2) generate TRAIN-001 data

ISO 42001 Cl.9.1 requires measuring AI system performance — L4 corrections are
the highest-quality real-world signal available.

---

## WHAT

### New file: `src/core/l4_correction_capture.py`

Module with one public function:
```python
def capture(
    record_id: str,
    clinic_id: str,
    audio_hash: str,
    ai_form: dict,
    bs_form: dict,
    doctor_cchn: str,
) -> None
```

Compares `ai_form` vs `bs_form` field-by-field. For each changed field,
logs a correction entry to `data/corrections/{clinic_id}/corrections.jsonl`.

**Correction log entry format (JSONL, one JSON per line):**
```json
{
  "schema_version": "1.0",
  "session_id": "SES-20260608",
  "clinic_id": "DA_NANG_01",
  "record_id": "REC-abc123",
  "audio_hash": "sha256:...",
  "doctor_cchn": "CCHN-xxxxx",
  "timestamp": "2026-06-08T14:30:00+07:00",
  "corrections": [
    {
      "field": "don_thuoc",
      "ai_value": [],
      "bs_value": [{"name": "Amoxicillin", "dose": "500mg", "qty": 10}],
      "note": "field_added"
    },
    {
      "field": "chan_doan",
      "ai_value": "",
      "bs_value": "Viêm họng cấp",
      "note": "field_corrected"
    }
  ]
}
```

If no corrections (AI was 100% correct), log a `"corrections": []` entry — this is
positive signal too (confirms what AI did correctly).

Storage: `data/corrections/` — created automatically, excluded from git via `.gitignore`.

### Hook in `src/api/main.py`

In `approve_record()`, between "Apply BS edits" and "L4: Approve":
```python
# L4 Correction Capture — best-effort, non-blocking
import l4_correction_capture
try:
    ai_form_snapshot = original_record.form_data  # before BS edits
    bs_form_final = record.form_data              # after BS edits
    l4_correction_capture.capture(
        record_id=record_id,
        clinic_id=current_facility_id(),
        audio_hash=record.audio_hash or "",
        ai_form=ai_form_snapshot,
        bs_form=bs_form_final,
        doctor_cchn=doctor_cchn,
    )
except Exception:
    pass  # never block approve flow
```

### New script: `scripts/analyze_corrections.py`

CLI tool (run manually by Andy, not automated):
```
python scripts/analyze_corrections.py [--clinic DA_NANG_01] [--field don_thuoc] [--min-count 3]
```

Output: frequency table of correction patterns, alias suggestions for drug names.
Does NOT auto-update `drug_db.json` — human review required (ISO 42001 Cl.8.6).

### Tests: `tests/unit/test_l4_correction_capture.py`

- AC-001: correction logged when BS changes any field
- AC-002: empty corrections logged when BS changes nothing
- AC-003: capture() does not raise even if data/corrections/ is unwritable (best-effort)
- AC-004: log file is valid JSONL (each line parses as JSON)
- AC-005: analyze_corrections.py generates alias suggestions from fixture data

---

## ACCEPTANCE CRITERIA

| AC | Description | Test |
|---|---|---|
| AC-001 | When BS edits any field, correction entry written to corrections.jsonl | test_ac001 |
| AC-002 | When BS approves without edits, empty correction entry written (positive signal) | test_ac002 |
| AC-003 | capture() failure never blocks approve flow | test_ac003 |
| AC-004 | corrections.jsonl is valid JSONL format | test_ac004 |
| AC-005 | analyze_corrections.py outputs alias suggestions from fixture data | test_ac005 |
| AC-006 | All existing 352 tests still pass | CI |
| AC-007 | data/corrections/ is in .gitignore (patient data must not be committed) | manual |

---

## OUT OF SCOPE

- Auto-updating drug_db.json (Phase 2, TRAIN-001)
- Real-time alias suggestions during BS editing (Phase 2)
- PII in correction log: only field names + values (which may contain drug names + diagnoses — not names/CCCD)
- Encryption: Phase 1 correction data stored plaintext (no CCCD/SĐT — low NĐ13 risk)

---

## ESTIMATED SIZE

- `src/core/l4_correction_capture.py`: ~80 LOC
- `scripts/analyze_corrections.py`: ~60 LOC
- `tests/unit/test_l4_correction_capture.py`: ~80 LOC
- `src/api/main.py` change: ~10 LOC
- Total: ~230 LOC → **Tầng 1** ✓

---

*FID-VN-006 | MediVoice VN | Awaiting Andy approval before implementation*
