#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MBTI Text Classifier Training Script (Vertex-ready)
---------------------------------------------------
- Reads CSV from GCS (requires gcsfs)
- Trains TF-IDF + MultiOutput(LinearSVC) MBTI predictor
- Saves artifacts locally, then uploads to GCS automatically if OUTPUT_DIR is gs://...
- Exports both:
    • tfidf_vectorizer.pkl
    • svm_model.pkl
    • model.joblib   ← complete pipeline for Vertex serving
    • metrics.json, schema.json, training_summary.json
Environment variables you can set in Vertex Custom Job:
    TRAIN_CSV=gs://<bucket>/data/training.csv
    OUTPUT_DIR=gs://<bucket>/vertex/mbti_svm_v1
    TEXT_COL=posts
    LABEL_COL=type
    TEST_SIZE=0.15
    RANDOM_STATE=42
    MIN_DF=3
    MAX_DF=0.95
    NGRAM_MAX=2
"""

import os
import json
import tempfile
from pathlib import Path
from typing import List, Optional, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import accuracy_score, f1_score
from google.cloud import storage

# ================================================================
#  Label helpers
# ================================================================
BIT_ORDER = ["IE", "SN", "TF", "JP"]

def mbti_to_binary(mbti: str) -> List[int]:
    mbti = mbti.strip().upper()
    if len(mbti) != 4:
        raise ValueError(f"Invalid MBTI string: {mbti}")
    return [
        0 if mbti[0] == "I" else 1,
        0 if mbti[1] == "S" else 1,
        0 if mbti[2] == "T" else 1,
        0 if mbti[3] == "J" else 1,
    ]

def encode_labels(mbtis: List[str]) -> np.ndarray:
    return np.array([mbti_to_binary(m) for m in mbtis], dtype=np.int64)

# ================================================================
#  Data loading
# ================================================================
CANDIDATES = [("posts","type"), ("text","label"), ("content","mbti"), ("message","type")]

def autodetect_columns(df: pd.DataFrame, text_col: Optional[str], label_col: Optional[str]):
    if text_col and label_col:
        return text_col, label_col
    for tcol, lcol in CANDIDATES:
        if tcol in df.columns and lcol in df.columns:
            return tcol, lcol
    raise ValueError(f"Cannot autodetect text/label columns; columns={list(df.columns)}")

def load_data(csv_path: str, text_col: Optional[str], label_col: Optional[str]):
    df = pd.read_csv(csv_path)
    tcol, lcol = autodetect_columns(df, text_col, label_col)
    df = df[[tcol, lcol]].dropna()
    df[tcol] = df[tcol].astype(str).str.strip()
    df[lcol] = df[lcol].astype(str).str.strip().str.upper()
    df = df[df[lcol].str.len() == 4].copy()
    X, y_mbtis = df[tcol].tolist(), df[lcol].tolist()
    Y = encode_labels(y_mbtis)
    return X, Y, tcol, lcol

# ================================================================
#  Model
# ================================================================
def build_model(min_df: int, max_df: float, ngram_max: int) -> Pipeline:
    vec = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"(?u)\b\w+\b",
        min_df=min_df,
        max_df=max_df,
        ngram_range=(1, ngram_max),
        sublinear_tf=True,
    )
    base = LinearSVC()
    clf = MultiOutputClassifier(base)
    return Pipeline([("tfidf", vec), ("clf", clf)])

# ================================================================
#  Metrics
# ================================================================
def evaluate(Y_true: np.ndarray, Y_pred: np.ndarray) -> Dict:
    bit_metrics = {}
    for i, bit in enumerate(BIT_ORDER):
        bit_metrics[bit] = {
            "accuracy": float(accuracy_score(Y_true[:, i], Y_pred[:, i])),
            "f1": float(f1_score(Y_true[:, i], Y_pred[:, i])),
        }
    exact = float(np.mean(np.all(Y_true == Y_pred, axis=1)))
    macro_f1 = float(np.mean([m["f1"] for m in bit_metrics.values()]))
    return {"bits": bit_metrics, "exact_4bit_match": exact, "macro_f1_bits": macro_f1}

# ================================================================
#  GCS helpers
# ================================================================
def is_gcs_uri(path: str) -> bool:
    return str(path).startswith("gs://")

def upload_dir_to_gcs(local_dir: Path, gcs_uri: str):
    client = storage.Client()
    no_prefix = gcs_uri.replace("gs://", "", 1)
    parts = no_prefix.split("/", 1)
    bucket_name = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    bucket = client.bucket(bucket_name)
    for file in local_dir.rglob("*"):
        if file.is_file():
            rel = file.relative_to(local_dir).as_posix()
            blob = bucket.blob(f"{prefix.rstrip('/')}/{rel}" if prefix else rel)
            blob.upload_from_filename(str(file))

def atomic_write_json(obj: Dict, out_path: Path):
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    tmp.replace(out_path)

# ================================================================
#  Main (reads from environment vars)
# ================================================================
def get_env_or_default(key: str, default):
    val = os.environ.get(key)
    if not val:
        print(f"[Config] Using default {key}={default}")
        return default
    print(f"[Config] Using {key}={val}")
    return val

def main():
    # --- Configuration from environment vars ---
    TRAIN_CSV = get_env_or_default("TRAIN_CSV", "gs://mbti_model_bucket/data/training.csv")
    OUTPUT_DIR = get_env_or_default("OUTPUT_DIR", "gs://mbti_model_bucket/vertex/mbti_svm_v1")
    TEXT_COL = os.environ.get("TEXT_COL")
    LABEL_COL = os.environ.get("LABEL_COL")
    TEST_SIZE = float(os.environ.get("TEST_SIZE", 0.1))
    RANDOM_STATE = int(os.environ.get("RANDOM_STATE", 42))
    MIN_DF = int(os.environ.get("MIN_DF", 3))
    MAX_DF = float(os.environ.get("MAX_DF", 0.95))
    NGRAM_MAX = int(os.environ.get("NGRAM_MAX", 2))

    # --- Working directory ---
    out_is_gcs = is_gcs_uri(OUTPUT_DIR)
    work_dir = Path(tempfile.mkdtemp(prefix="mbti-train-")) if out_is_gcs else Path(OUTPUT_DIR)
    work_dir.mkdir(parents=True, exist_ok=True)

    # --- Load data ---
    X, Y, tcol, lcol = load_data(TRAIN_CSV, TEXT_COL, LABEL_COL)
    X_tr, X_val, Y_tr, Y_val = train_test_split(
        X, Y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=Y
    )

    # --- Train ---
    pipe = build_model(MIN_DF, MAX_DF, NGRAM_MAX)
    pipe.fit(X_tr, Y_tr)
    Y_pred = pipe.predict(X_val)
    metrics = evaluate(Y_val, Y_pred)

    # --- Save artifacts ---
    tfidf_path = work_dir / "tfidf_vectorizer.pkl"
    model_path = work_dir / "svm_model.pkl"
    pipe_path = work_dir / "model.joblib"
    metrics_path = work_dir / "metrics.json"
    schema_path = work_dir / "label_schema.json"
    summary_path = work_dir / "training_summary.json"

    joblib.dump(pipe.named_steps["tfidf"], tfidf_path)
    joblib.dump(pipe.named_steps["clf"], model_path)
    joblib.dump(pipe, pipe_path)
    atomic_write_json(metrics, metrics_path)

    schema = {"bit_order": BIT_ORDER}
    atomic_write_json(schema, schema_path)

    summary = {
        "train_csv": TRAIN_CSV,
        "output_dir": OUTPUT_DIR,
        "n_train": len(X_tr),
        "n_val": len(X_val),
        "params": {
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "min_df": MIN_DF,
            "max_df": MAX_DF,
            "ngram_max": NGRAM_MAX,
        },
    }
    atomic_write_json(summary, summary_path)

    print("=== MBTI Training Complete ===")
    print("Metrics:", metrics)
    if out_is_gcs:
        upload_dir_to_gcs(work_dir, OUTPUT_DIR)
        print(f"Uploaded artifacts to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
