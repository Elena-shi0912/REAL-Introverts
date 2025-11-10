
## Files

| File | Description |
|------|-------------|
| `train.sh` | Shell script that runs the training pipeline and saves model artifacts. |
| `predict.py` | Inference script for predicting MBTI types from new text or CSV files. |

---

## 1. Training the Model

### Requirements
- Python ≥ 3.8
- Install dependencies:
```bash
pip install pandas numpy scikit-learn joblib
```

### Run Training
```bash
chmod +x train.sh
./train.sh
```
By default, the script expects:
```
data/mbti_1.csv
```

This CSV must contain:

- A text column (e.g., posts)

- A label column with MBTI types (e.g., type)

### Output Artifacts (Saved in OUT_DIR = /artifacts)

| File                    | Purpose                                      |
| ----------------------- | -------------------------------------------- |
| `tfidf_vectorizer.pkl`  | TF-IDF tokenizer and vocabulary              |
| `svm_model.pkl`         | Multi-output classification model            |
| `label_schema.json`     | Explanation of label encoding for MBTI bits  |
| `metrics.json`          | Validation metrics (per-axis + exact match)  |
| `training_summary.json` | Data + parameter summary for reproducibility |

## 2. Running Inference
### Predict a Single Text
```bash
python3 predict.py --model-dir artifacts/mbti_svm_v1 \
  --text "I enjoy deep conversations about philosophy and science."
```

### Output example:
```
INTP
```

### Predict for a CSV File
```
python3 predict.py \
  --model-dir artifacts/mbti_svm_v1 \
  --input-csv data/new_texts.csv \
  --output-csv results/predictions.csv \
  --text-col posts
```

The output CSV will include:
```
pred_IE, pred_SN, pred_TF, pred_JP, pred_mbti
```

Example:
```
"I love exploring ideas",0,1,1,1,INFP
```


