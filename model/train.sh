#!/usr/bin/env bash
set -euo pipefail

# -------- Config (adjust as needed) --------
DATA_CSV="${DATA_CSV:-mbti_1.csv}"   # path to your training CSV
OUT_DIR="${OUT_DIR:-artifacts/mbti_svm_v1}"

# Optional knobs (override via env or edit here)
TEXT_COL="${TEXT_COL:-posts}"             # or text/content/message
LABEL_COL="${LABEL_COL:-type}"            # or label/mbti/type
TEST_SIZE="${TEST_SIZE:-0.15}"
SEED="${SEED:-42}"
MIN_DF="${MIN_DF:-3}"
MAX_DF="${MAX_DF:-0.95}"
NGRAM_MAX="${NGRAM_MAX:-2}"
REUSE_VECTORIZER="${REUSE_VECTORIZER:-}"  # e.g., artifacts/prev_run/tfidf_vectorizer.pkl

# -------- Run training --------
echo "Training with:"
echo "  DATA_CSV=$DATA_CSV"
echo "  OUT_DIR=$OUT_DIR"
echo "  TEXT_COL=$TEXT_COL  LABEL_COL=$LABEL_COL"
echo "  TEST_SIZE=$TEST_SIZE  SEED=$SEED  MIN_DF=$MIN_DF  MAX_DF=$MAX_DF  NGRAM_MAX=$NGRAM_MAX"
if [[ -n "${REUSE_VECTORIZER}" ]]; then echo "  REUSE_VECTORIZER=$REUSE_VECTORIZER"; fi

mkdir -p "$(dirname "$OUT_DIR")"

python3 train_mbti.py \
  --train-csv "$DATA_CSV" \
  --output-dir "$OUT_DIR" \
  --text-col "$TEXT_COL" \
  --label-col "$LABEL_COL" \
  --test-size "$TEST_SIZE" \
  --random-state "$SEED" \
  --min-df "$MIN_DF" \
  --max-df "$MAX_DF" \
  --ngram-max "$NGRAM_MAX" \
  ${REUSE_VECTORIZER:+--reuse-vectorizer "$REUSE_VECTORIZER"}

echo "Artifacts written to: $OUT_DIR"
echo "Files:"
ls -1 "$OUT_DIR"
