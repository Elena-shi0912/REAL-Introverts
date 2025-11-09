import joblib
import os

def binary_to_mbti(vec):
    mapping = [
        ("I", "E"),  # IE axis: 1 -> I, 0 -> E
        ("N", "S"),  # SN axis: 1 -> N, 0 -> S
        ("T", "F"),  # TF axis: 1 -> T, 0 -> F
        ("J", "P")   # JP axis: 1 -> J, 0 -> P
    ]
    return "".join([mapping[i][0] if val == 1 else mapping[i][1] for i, val in enumerate(vec)])

OUTPUT_MODEL_DIR = ""
# Reload the saved model and vectorizer
loaded_tfidf = joblib.load(os.path.join(OUTPUT_MODEL_DIR, "tfidf_vectorizer.pkl"))
loaded_svm = joblib.load(os.path.join(OUTPUT_MODEL_DIR, "svm_model.pkl")) # or log_reg_model.pkl

# Test with an example input text
sample_text = "I enjoy deep conversations about philosophy and science."
sample_vec = loaded_tfidf.transform([sample_text])

# Predict the 4 binary MBTI axis values
pred_binary = loaded_svm.predict(sample_vec)[0]

# Convert the binary prediction to an MBTI type string
pred_mbti = binary_to_mbti(pred_binary)

print("Sample:", sample_text)
print("Predicted binary:", pred_binary)
print("Predicted MBTI:", pred_mbti)