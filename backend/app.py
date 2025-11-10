from fastapi import FastAPI, Request
from google.cloud import storage
import pickle
import numpy as np
import os

app = FastAPI()

# Environment variables
BUCKET_NAME = os.environ.get("MODEL_BUCKET", "mbti_mode_bucket")
MODEL_PATH = os.environ.get("MODEL_PATH", "svm_model.pkl")
VECTORIZER_PATH = os.environ.get("VECTORIZER_PATH", "tfidf_vectorizer.pkl")

def load_pickle_from_gcs(bucket_name, blob_name):
    """Download and load pickle object from GCS into memory."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    return pickle.loads(data)

# Load model and vectorizer
model = load_pickle_from_gcs(BUCKET_NAME, MODEL_PATH)
vectorizer = load_pickle_from_gcs(BUCKET_NAME, VECTORIZER_PATH)

@app.post("/predict")
async def predict(request: Request):
    """Predict endpoint"""
    data = await request.json()
    text_input = data.get("text", "")
    features = vectorizer.transform([text_input])
    prediction = model.predict(features)
    return {"prediction": prediction.tolist()}

@app.get("/")
def home():
    return {"message": "Model and vectorizer API running on Cloud Run"}
