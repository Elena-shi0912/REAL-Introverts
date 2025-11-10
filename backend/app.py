from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import storage
import pickle
import numpy as np
import os

app = Flask(__name__)
CORS(app)

# Get environment variables
BUCKET_NAME = os.environ.get("MODEL_BUCKET", "mbti_model_bucket")
MODEL_PATH = os.environ.get("MODEL_PATH", "svm_model.pkl")
VECTORIZER_PATH = os.environ.get("VECTORIZER_PATH", "tfidf_vectorizer.pkl")

def load_pickle_from_gcs(bucket_name, blob_name):
    """Download and load pickle object from GCS into memory."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    return pickle.loads(data)

# Load both model and vectorizer
model = load_pickle_from_gcs(BUCKET_NAME, MODEL_PATH)
vectorizer = load_pickle_from_gcs(BUCKET_NAME, VECTORIZER_PATH)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text_input = data.get("text", "")
    # transform the text using your vectorizer
    features = vectorizer.transform([text_input])
    prediction = model.predict(features)
    return jsonify({"prediction": prediction.tolist()})

@app.route("/")
def home():
    return "Model and vectorizer API running on Cloud Run"
