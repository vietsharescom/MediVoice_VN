#!/usr/bin/env python
# scripts/train_ner_phobert.py — TRAIN-002: PhoBERT+CRF NER overnight
# Input:  data/synthetic_ner/{train,val,test}.jsonl  (7994/1003/1003 samples)
# Output: models/ner_phobert/  — AutoModelForTokenClassification checkpoint
# Runtime (CPU i5-12400F): ~3-5h for 3 epochs, 7994 train samples
# Usage: python scripts/train_ner_phobert.py [--epochs 3] [--batch 8]

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    DataCollatorForTokenClassification,
    Trainer,
    TrainingArguments,
)

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT / "logs" / "train_ner_phobert.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

LABEL_LIST = [
    "O",
    "B-MEDICATION", "I-MEDICATION",
    "B-SYMPTOM",    "I-SYMPTOM",
    "B-VITAL",      "I-VITAL",
    "B-FOLLOWUP",   "I-FOLLOWUP",
    "B-DOSE",
    "B-FREQUENCY",  "I-FREQUENCY",
    "B-DURATION",   "I-DURATION",
]
LABEL2ID = {l: i for i, l in enumerate(LABEL_LIST)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

MODEL_NAME = "vinai/phobert-base-v2"
OUT_DIR = ROOT / "models" / "ner_phobert"


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def _word_ids_manual(tokenizer, words, input_ids):
    """Build word_ids list manually (for non-fast tokenizers like PhoBERT)."""
    # Tokenize each word individually to know how many subword tokens it produces
    word_ids = [None]  # [CLS]
    for wid, word in enumerate(words):
        subtokens = tokenizer.tokenize(word)
        if not subtokens:
            subtokens = [tokenizer.unk_token]
        word_ids.extend([wid] * len(subtokens))
    word_ids.append(None)  # [SEP]
    # Truncate to match actual input_ids length
    word_ids = word_ids[: len(input_ids)]
    # Pad if needed
    while len(word_ids) < len(input_ids):
        word_ids.append(None)
    return word_ids


def tokenize_and_align(examples, tokenizer, max_len=256):
    tokenized = tokenizer(
        examples["words"],
        truncation=True,
        max_length=max_len,
        is_split_into_words=True,
    )
    # Try fast-tokenizer word_ids first; fall back to manual alignment
    use_fast = hasattr(tokenized, "word_ids") and callable(
        lambda: tokenized.word_ids(batch_index=0)
    )
    all_labels = []
    for i, label_seq in enumerate(examples["labels"]):
        try:
            word_ids = tokenized.word_ids(batch_index=i)
        except (ValueError, AttributeError):
            word_ids = _word_ids_manual(
                tokenizer, examples["words"][i], tokenized["input_ids"][i]
            )
        prev_word_id = None
        label_ids = []
        for wid in word_ids:
            if wid is None:
                label_ids.append(-100)
            elif wid != prev_word_id:
                raw = label_seq[wid] if wid < len(label_seq) else "O"
                label_ids.append(LABEL2ID.get(raw, 0))
            else:
                raw = label_seq[wid] if wid < len(label_seq) else "O"
                if raw.startswith("B-"):
                    inner = "I-" + raw[2:]
                    label_ids.append(LABEL2ID.get(inner, LABEL2ID.get(raw, 0)))
                else:
                    label_ids.append(LABEL2ID.get(raw, 0))
            prev_word_id = wid
        all_labels.append(label_ids)
    tokenized["labels"] = all_labels
    return tokenized


def compute_metrics(p):
    try:
        import evaluate as hf_eval
        seqeval = hf_eval.load("seqeval")
    except Exception:
        import seqeval.metrics as sm

        def _compute(preds, refs):
            return {
                "f1": sm.f1_score(refs, preds),
                "precision": sm.precision_score(refs, preds),
                "recall": sm.recall_score(refs, preds),
            }

        predictions_raw, labels_raw = p
        preds = np.argmax(predictions_raw, axis=2)
        true_preds = [
            [ID2LABEL[pred] for pred, lab in zip(pr, la) if lab != -100]
            for pr, la in zip(preds, labels_raw)
        ]
        true_labels = [
            [ID2LABEL[lab] for lab in la if lab != -100]
            for la in labels_raw
        ]
        return _compute(true_preds, true_labels)

    predictions_raw, labels_raw = p
    preds = np.argmax(predictions_raw, axis=2)
    true_preds = [
        [ID2LABEL[pred] for pred, lab in zip(pr, la) if lab != -100]
        for pr, la in zip(preds, labels_raw)
    ]
    true_labels = [
        [ID2LABEL[lab] for lab in la if lab != -100]
        for la in labels_raw
    ]
    result = seqeval.compute(predictions=true_preds, references=true_labels)
    return {
        "f1": result["overall_f1"],
        "precision": result["overall_precision"],
        "recall": result["overall_recall"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-len", type=int, default=256)
    args = parser.parse_args()

    (ROOT / "logs").mkdir(exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log.info(f"Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
    log.info(f"Model: {MODEL_NAME}")
    log.info(f"Epochs: {args.epochs}  Batch: {args.batch}  LR: {args.lr}")

    # Load data
    log.info("Loading datasets...")
    train_raw = load_jsonl(ROOT / "data/synthetic_ner/train.jsonl")
    val_raw   = load_jsonl(ROOT / "data/synthetic_ner/val.jsonl")
    test_raw  = load_jsonl(ROOT / "data/synthetic_ner/test.jsonl")
    log.info(f"  train={len(train_raw)}  val={len(val_raw)}  test={len(test_raw)}")

    def to_hf_dict(rows):
        return {
            "words":  [r["words"]  for r in rows],
            "labels": [r["labels"] for r in rows],
        }

    ds = DatasetDict({
        "train": Dataset.from_dict(to_hf_dict(train_raw)),
        "val":   Dataset.from_dict(to_hf_dict(val_raw)),
        "test":  Dataset.from_dict(to_hf_dict(test_raw)),
    })

    # Tokenize
    log.info(f"Loading tokenizer {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    log.info("Tokenizing...")
    tokenized_ds = ds.map(
        lambda ex: tokenize_and_align(ex, tokenizer, args.max_len),
        batched=True,
        remove_columns=["words", "labels"],
    )

    # Model
    log.info("Loading model...")
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABEL_LIST),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )

    collator = DataCollatorForTokenClassification(tokenizer)

    training_args = TrainingArguments(
        output_dir=str(OUT_DIR),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch,
        per_device_eval_batch_size=args.batch * 2,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.1,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_dir=str(ROOT / "logs" / "ner_tb"),
        logging_steps=50,
        save_total_limit=2,
        fp16=False,
        dataloader_num_workers=0,
        report_to="none",
        no_cuda=not torch.cuda.is_available(),
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["val"],
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
    )

    log.info("=== Starting training ===")
    trainer.train()

    log.info("=== Evaluating on test set ===")
    test_results = trainer.evaluate(tokenized_ds["test"])
    log.info(f"Test results: {test_results}")

    log.info(f"Saving best model → {OUT_DIR}/best")
    trainer.save_model(str(OUT_DIR / "best"))
    tokenizer.save_pretrained(str(OUT_DIR / "best"))
    log.info("Done.")

    # Save label map alongside model
    label_map_path = OUT_DIR / "best" / "label_map.json"
    with open(label_map_path, "w", encoding="utf-8") as f:
        json.dump({"label2id": LABEL2ID, "id2label": {str(k): v for k, v in ID2LABEL.items()}}, f, indent=2)
    log.info(f"Label map saved → {label_map_path}")


if __name__ == "__main__":
    main()
