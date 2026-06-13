# Colab/Kaggle GPU Setup — PhoWhisper Fine-tune (TRAIN-001)

> **Consolidated notebook**: `notebooks/TRAIN_001_colab_kaggle.ipynb` chains all
> steps below (1-10) including step 9b (evaluate WER, output results) — upload it
> directly to Colab/Kaggle to run end-to-end. This page documents each step.

> Compliance note: `docs/records/DECISIONS.md` 2026-06-11 (PILOT PHASE EXCEPTION #2) +
> `docs/compliance/RISK_REGISTER.md` R-P03. Uploading **pilot audio with patient PII**
> to Colab/Kaggle (Google Cloud, ngoài VN) is TEMPORARY, pilot-only, with Andy's
> consent already confirmed. **Delete audio from the Colab/Kaggle runtime and any
> Drive/Dataset upload immediately after the training run.** Only download the final
> model checkpoint (no audio/PII inside .bin/.safetensors files). VietMed (MIT,
> public, no PII) has no such restriction.

## 1. Clone repo

```bash
!git clone https://github.com/vietsharescom/MediVoice_VN.git
%cd MediVoice_VN
```

## 2. Install dependencies

```bash
!pip install -q transformers datasets librosa soundfile accelerate evaluate jiwer
```

## 3. (Optional) Set HF_TOKEN — higher rate limits only

`leduckhai/VietMed` (correct dataset, verified 2026-06-12) is **NOT gated** — no
token required to download. `HF_TOKEN` is optional and only raises HuggingFace
rate limits if you hit them.

In Colab: use the "Secrets" panel (key icon) to store `HF_TOKEN`, then:

```python
from google.colab import userdata
import os
os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
```

In Kaggle: Settings → Secrets → add `HF_TOKEN`, then access via `kaggle_secrets.UserSecretsClient`.

**Never paste the token directly into a notebook cell or commit it.**

## 4. Download VietMed (always allowed, no PII)

VietMed (16h, MIT, `leduckhai/VietMed`) can also be downloaded and fine-tuned
**locally** — Colab/Kaggle is not required for VietMed itself. Use Colab/Kaggle for
(a) stronger GPU than local, or (b) pilot audio (PII) per
`docs/records/DECISIONS.md` 2026-06-11.

```bash
!python -X utf8 scripts/download_vietmed.py
```

## 5. (Optional, pilot-only) Upload pilot audio

Only if pilot audio has been recorded (`data/audio/pilot/`) **and** consent is
confirmed per `docs/records/DECISIONS.md` 2026-06-11. Upload via Colab's file
upload UI or a temporary Drive mount — do NOT leave it in a shared/public Drive
folder.

## 6. Build manifests

```bash
!python -X utf8 scripts/build_asr_manifest.py --vietmed --pilot data/audio/pilot --combined
```

## 7. Smoke test (validate pipeline before full run)

```bash
!python -X utf8 scripts/train_asr_phowhisper.py --smoke-test
```

## 8. Full fine-tune run (GPU)

```bash
!python -X utf8 scripts/train_asr_phowhisper.py \
    --manifest data/asr_manifest/combined_manifest.jsonl \
    --epochs 3 --batch 8 --fp16
```

## 9b. Evaluate — output results (WER)

`scripts/eval_asr_phowhisper.py` transcribes a manifest with a model/checkpoint
and computes WER per sample + aggregate via `jiwer`, writing a JSON results file.
Run it once with the base model (baseline) and once with the fine-tuned checkpoint:

```bash
!python -X utf8 scripts/eval_asr_phowhisper.py \
    --model vinai/PhoWhisper-medium \
    --manifest data/asr_manifest/ref_voice_manifest.jsonl \
    --out data/eval/train001_eval_baseline.json

!python -X utf8 scripts/eval_asr_phowhisper.py \
    --model models/asr_phowhisper \
    --manifest data/asr_manifest/ref_voice_manifest.jsonl \
    --out data/eval/train001_eval_results.json
```

Output JSON: `{"model", "manifest", "n", "wer_mean", "samples": [{"audio", "ref", "hyp", "wer"}, ...]}`.
Compare `wer_mean` baseline vs fine-tuned to confirm the fine-tune improved WER
(current baseline ALL=0.183, HN=0.292 — see `docs/records/PROJECT_PROGRESS.md`).

## 10. Download checkpoint, clean up

- Download `models/asr_phowhisper/` (model files only — no audio).
- Delete any uploaded pilot audio from the Colab/Kaggle session, Drive, or Dataset:
  ```bash
  !rm -rf data/audio/pilot/*
  ```
- Confirm no PII remains in the runtime before closing the session.
