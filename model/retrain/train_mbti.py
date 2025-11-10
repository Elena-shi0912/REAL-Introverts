
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MBTI Text Classifier Training Script
------------------------------------
Pipeline-friendly trainer for MBTI (16-type) prediction using TF‑IDF + MultiOutput SVM.
- Reads a CSV with text + MBTI label columns (auto-detect: ('posts','type') or ('text','label')).
- Encodes MBTI -> 4-bit binary [IE, SN, TF, JP] and back.
- Trains a MultiOutput LinearSVC wrapped in OneVsRestClassifier for each bit.
- Saves artifacts:
    - tfidf_vectorizer.pkl
    - svm_model.pkl
    - label_schema.json (bit order + mapping doc)
    - metrics.json (accuracy/F1 per bit + overall)
- Optional: reuse an existing vectorizer for consistent vocab across retrains.

Usage:
    python3 train_mbti.py \
        --train-csv mbti_1.csv \
        --output-dir out/mbti_svm_v1 \
        --text-col posts --label-col type \
        --test-size 0.15 --random-state 42 \
        --min-df 3 --max-df 0.95 --ngram-max 2

Artifacts are written atomically then moved into place for safer CI/CD retrains.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Tuple, List, Optional, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.preprocessing import FunctionTransformer
from sklearn.utils import Bunch

# ------------------------------
# MBTI <-> Binary helper mapping
# ------------------------------

BIT_ORDER = ["IE", "SN", "TF", "JP"]  # IMPORTANT: Keep stable for retrains!

def mbti_to_binary(mbti: str) -> List[int]:
    mbti = mbti.strip().upper()
    if len(mbti) != 4:
        raise ValueError(f"Invalid MBTI string: {mbti}")
    # Positions: 0=I/E, 1=S/N, 2=T/F, 3=J/P
    b0 = 0 if mbti[0] == "I" else 1  # 0=I,1=E
    b1 = 0 if mbti[1] == "S" else 1  # 0=S,1=N
    b2 = 0 if mbti[2] == "T" else 1  # 0=T,1=F
    b3 = 0 if mbti[3] == "J" else 1  # 0=J,1=P
    return [b0, b1, b2, b3]

def binary_to_mbti(bits: List[int]) -> str:
    if len(bits) != 4:
        raise ValueError(f"Expected 4 bits, got {len(bits)}")
    c0 = "I" if bits[0] == 0 else "E"
    c1 = "S" if bits[1] == 0 else "N"
    c2 = "T" if bits[2] == 0 else "F"
    c3 = "J" if bits[3] == 0 else "P"
    return c0 + c1 + c2 + c3

def encode_labels(mbtis: List[str]) -> np.ndarray:
    return np.array([mbti_to_binary(m) for m in mbtis], dtype=np.int64)

def decode_labels(Y: np.ndarray) -> List[str]:
    return [binary_to_mbti(list(row)) for row in Y]

# ------------------------------
# Data loading
# ------------------------------

def autodetect_columns(df: pd.DataFrame, text_col: Optional[str], label_col: Optional[str]) -> Tuple[str, str]:
    if text_col and label_col:
        return text_col, label_col
    candidates = [
        ("posts", "type"),
        ("text", "label"),
        ("content", "mbti"),
        ("message", "type"),
    ]
    for tcol, lcol in candidates:
        if tcol in df.columns and lcol in df.columns:
            return tcol, lcol
    raise ValueError(f"Could not autodetect text/label columns. Columns present: {list(df.columns)}")

def load_data(csv_path: Path, text_col: Optional[str], label_col: Optional[str]) -> Bunch:
    df = pd.read_csv(csv_path)
    tcol, lcol = autodetect_columns(df, text_col, label_col)
    # Drop NA & strip
    df = df[[tcol, lcol]].dropna()
    df[tcol] = df[tcol].astype(str).str.strip()
    df[lcol] = df[lcol].astype(str).str.strip().str.upper()
    # Filter valid MBTI (length==4)
    mask_valid = df[lcol].str.len() == 4
    df = df[mask_valid].copy()
    X = df[tcol].tolist()
    y_mbtis = df[lcol].tolist()
    Y = encode_labels(y_mbtis)
    return Bunch(X=X, Y=Y, y_mbtis=y_mbtis, text_col=tcol, label_col=lcol, frame=df)

# ------------------------------
# Model building
# ------------------------------

def build_model(min_df: int, max_df: float, ngram_max: int, reuse_vectorizer: Optional[Path]) -> Tuple[Pipeline, TfidfVectorizer]:
    if reuse_vectorizer and reuse_vectorizer.exists():
        vectorizer: TfidfVectorizer = joblib.load(reuse_vectorizer)
    else:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            min_df=min_df,
            max_df=max_df,
            ngram_range=(1, ngram_max),
            sublinear_tf=True,
        )
    base = LinearSVC()  # robust + fast; no predict_proba, but OK for classification
    clf = MultiOutputClassifier(base)
    pipe = Pipeline([
        ("tfidf", vectorizer),
        ("clf", clf),
    ])
    return pipe, vectorizer

# ------------------------------
# Evaluation
# ------------------------------

def evaluate(Y_true: np.ndarray, Y_pred: np.ndarray) -> Dict:
    metrics = {}
    # Per-bit metrics
    bit_metrics = {}
    for i, bit_name in enumerate(BIT_ORDER):
        acc = accuracy_score(Y_true[:, i], Y_pred[:, i])
        f1 = f1_score(Y_true[:, i], Y_pred[:, i])
        bit_metrics[bit_name] = {"accuracy": acc, "f1": f1}
    # Exact 4-bit match (all bits correct)
    exact_match = float(np.mean(np.all(Y_true == Y_pred, axis=1)))
    # Macro F1 across 4 bits
    macro_f1 = float(np.mean([m["f1"] for m in bit_metrics.values()]))
    metrics["bits"] = bit_metrics
    metrics["exact_4bit_match"] = exact_match
    metrics["macro_f1_bits"] = macro_f1
    return metrics

# ------------------------------
# IO helpers
# ------------------------------

def atomic_write_json(obj: Dict, out_path: Path):
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    tmp.replace(out_path)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

# ------------------------------
# Main
# ------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description="Train MBTI text classifier (TF‑IDF + MultiOutput LinearSVC).")
    ap.add_argument("--train-csv", type=Path, required=True, help="Path to training CSV.")
    ap.add_argument("--output-dir", type=Path, required=True, help="Directory to save artifacts.")
    ap.add_argument("--text-col", type=str, default=None, help="Name of text column (auto-detect if omitted).")
    ap.add_argument("--label-col", type=str, default=None, help="Name of label column (auto-detect if omitted).")
    ap.add_argument("--test-size", type=float, default=0.1, help="Holdout fraction for evaluation.")
    ap.add_argument("--random-state", type=int, default=42, help="Random seed for splits.")
    ap.add_argument("--min-df", type=int, default=3, help="TfidfVectorizer min_df.")
    ap.add_argument("--max-df", type=float, default=0.95, help="TfidfVectorizer max_df.")
    ap.add_argument("--ngram-max", type=int, default=2, help="Max n-gram length (1..N).")
    ap.add_argument("--reuse-vectorizer", type=Path, default=None, help="Optional path to existing tfidf_vectorizer.pkl.")
    return ap.parse_args()

def main():
    args = parse_args()
    ensure_dir(args.output_dir)

    data = load_data(args.train_csv, args.text_col, args.label_col)

    X_train, X_val, Y_train, Y_val = train_test_split(
        data.X, data.Y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=data.Y  # stratify on 4-bit labels if possible
    )

    pipe, vectorizer = build_model(
        min_df=args.min_df,
        max_df=args.max_df,
        ngram_max=args.ngram_max,
        reuse_vectorizer=args.reuse_vectorizer
    )

    # Fit
    pipe.fit(X_train, Y_train)

    # Evaluate
    Y_pred = pipe.predict(X_val)
    metrics = evaluate(Y_val, Y_pred)

    # Save artifacts
    tfidf_path = args.output_dir / "tfidf_vectorizer.pkl"
    model_path = args.output_dir / "svm_model.pkl"
    schema_path = args.output_dir / "label_schema.json"
    metrics_path = args.output_dir / "metrics.json"

    # Save vectorizer and model (pipeline persists both, but save vectorizer alone too for reuse)
    joblib.dump(pipe.named_steps["tfidf"], tfidf_path)
    joblib.dump(pipe.named_steps["clf"], model_path)

    schema = {
        "bit_order": BIT_ORDER,
        "bit_meanings": {
            "IE": {"0": "I", "1": "E"},
            "SN": {"0": "S", "1": "N"},
            "TF": {"0": "T", "1": "F"},
            "JP": {"0": "J", "1": "P"}
        },
        "encoding_examples": {
            "INTJ": mbti_to_binary("INTJ"),
            "ENFP": mbti_to_binary("ENFP")
        }
    }
    atomic_write_json(schema, schema_path)
    atomic_write_json(metrics, metrics_path)

    # Also persist a small "training_summary.json" with data columns & counts for audits
    summary = {
        "text_column": data.text_col,
        "label_column": data.label_col,
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "params": {
            "test_size": args.test_size,
            "random_state": args.random_state,
            "min_df": args.min_df,
            "max_df": args.max_df,
            "ngram_max": args.ngram_max
        }
    }
    atomic_write_json(summary, args.output_dir / "training_summary.json")

    # Emit a compact printout for CI logs
    print("=== MBTI Training Complete ===")
    print(f"Output dir: {args.output_dir}")
    print("Exact 4-bit match:", metrics["exact_4bit_match"])
    print("Macro F1 (bits):", metrics["macro_f1_bits"])
    for bit, m in metrics["bits"].items():
        print(f"  {bit}: acc={m['accuracy']:.4f} f1={m['f1']:.4f}")

if __name__ == "__main__":
    main()
