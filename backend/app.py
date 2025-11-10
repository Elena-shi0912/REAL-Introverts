from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
import joblib
import numpy as np
import os
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
BUCKET_NAME = os.environ.get("MODEL_BUCKET", "mbti_model_bucket")
MODEL_PATH = os.environ.get("MODEL_PATH", "svm_model.pkl")
VECTORIZER_PATH = os.environ.get("VECTORIZER_PATH", "tfidf_vectorizer.pkl")

def load_joblib_from_gcs(bucket_name, blob_name):
    """Download and load joblib object directly from GCS."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    print(f"✅ Loaded {blob_name} ({len(data)} bytes)")
    return joblib.load(BytesIO(data))

def binary_to_mbti(vec):
    mapping = [
        ("I", "E"),  # IE axis: 1 -> I, 0 -> E
        ("N", "S"),  # SN axis
        ("T", "F"),  # TF axis
        ("J", "P")   # JP axis
    ]
    return "".join([mapping[i][0] if val == 1 else mapping[i][1] for i, val in enumerate(vec)])

# Load model + vectorizer
try:
    model = load_joblib_from_gcs(BUCKET_NAME, MODEL_PATH)
    vectorizer = load_joblib_from_gcs(BUCKET_NAME, VECTORIZER_PATH)
    print("✅ Model and vectorizer loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model/vectorizer: {e}")
    model, vectorizer = None, None

@app.post("/predict")
async def predict(request: Request):
    data = await request.json()
    text = data.get("text", "")
    if not model or not vectorizer:
        return {"error": "Model or vectorizer not loaded."}
    if not text:
        return {"error": "Missing 'text' field."}

    features = vectorizer.transform([text])
    pred_binary = model.predict(features)[0]
    mbti = binary_to_mbti(pred_binary)
    return {"prediction": mbti}

@app.get("/")
def home():
    return {"message": "MBTI backend running on Cloud Run"}
