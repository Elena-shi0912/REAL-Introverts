#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Predict MBTI from text using saved artifacts.
Loads:
  - tfidf_vectorizer.pkl
  - svm_model.pkl
Outputs predictions to stdout or a CSV file.

Usage examples:
  # Single text
  python predict.py --model-dir artifacts/mbti_svm_v1 --text "I enjoy deep conversations about philosophy and science."

  # Batch CSV (auto-detect text column or specify with --text-col)
  python predict.py --model-dir artifacts/mbti_svm_v1 --input-csv data/some_texts.csv --output-csv out/preds.csv --text-col posts
"""
import argparse
from pathlib import Path
import sys
import json

import joblib
import numpy as np
import pandas as pd

BIT_ORDER = ["IE", "SN", "TF", "JP"]

def binary_to_mbti(bits):
    c0 = "I" if bits[0] == 0 else "E"
    c1 = "S" if bits[1] == 0 else "N"
    c2 = "T" if bits[2] == 0 else "F"
    c3 = "J" if bits[3] == 0 else "P"
    return c0 + c1 + c2 + c3

def autodetect_text_col(df: pd.DataFrame, text_col):
    if text_col:
        if text_col not in df.columns:
            raise ValueError(f"--text-col '{text_col}' not found in CSV columns: {list(df.columns)}")
        return text_col
    candidates = ["posts", "text", "content", "message"]
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"Could not autodetect text column. Columns present: {list(df.columns)}")

def load_artifacts(model_dir: Path):
    vec_path = model_dir / "tfidf_vectorizer.pkl"
    clf_path = model_dir / "svm_model.pkl"
    if not vec_path.exists() or not clf_path.exists():
        raise FileNotFoundError(f"Missing artifacts in {model_dir}. Expected tfidf_vectorizer.pkl and svm_model.pkl")
    vectorizer = joblib.load(vec_path)
    clf = joblib.load(clf_path)
    return vectorizer, clf

def predict_texts(model_dir: Path, texts):
    vectorizer, clf = load_artifacts(model_dir)
    X = vectorizer.transform(texts)
    Y_pred = clf.predict(X)  # shape (N, 4)
    mbti = [binary_to_mbti(list(row)) for row in Y_pred]
    return Y_pred, mbti

def main():
    ap = argparse.ArgumentParser(description="MBTI inference script")
    ap.add_argument("--model-dir", type=Path, required=True, help="Directory with tfidf_vectorizer.pkl and svm_model.pkl")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Single input text")
    group.add_argument("--input-csv", type=Path, help="CSV file with a text column")
    ap.add_argument("--text-col", type=str, default=None, help="Column name for text if using --input-csv")
    ap.add_argument("--output-csv", type=Path, default=None, help="Optional path to save predictions as CSV")
    args = ap.parse_args()

    if args.text:
        _, mbti = predict_texts(args.model_dir, [args.text])
        print(mbti[0])
        return

    # CSV mode
    df = pd.read_csv(args.input_csv)
    tcol = autodetect_text_col(df, args.text_col)
    texts = df[tcol].astype(str).fillna("").tolist()
    Y_pred, mbti = predict_texts(args.model_dir, texts)

    out_df = df.copy()
    out_df["pred_IE"] = Y_pred[:, 0]
    out_df["pred_SN"] = Y_pred[:, 1]
    out_df["pred_TF"] = Y_pred[:, 2]
    out_df["pred_JP"] = Y_pred[:, 3]
    out_df["pred_mbti"] = mbti

    if args.output_csv:
        out_df.to_csv(args.output_csv, index=False)
        print(f"Wrote predictions to {args.output_csv}")
    else:
        # Print a compact sample
        print(out_df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
