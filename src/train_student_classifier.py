import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

# ==========================================
# LOAD EMBEDDINGS
# ==========================================

print("=" * 60)
print("Training Student Recognition Model")
print("=" * 60)

data = joblib.load("models/student_embeddings.pkl")

embeddings = np.array(data["embeddings"])
labels = np.array(data["labels"])

print(f"Total Embeddings : {len(embeddings)}")
print(f"Total Students   : {len(set(labels))}")

# ==========================================
# LABEL ENCODER
# ==========================================

encoder = LabelEncoder()

encoded_labels = encoder.fit_transform(labels)

# ==========================================
# TRAIN SVM
# ==========================================

print("\nTraining SVM Classifier...")

model = SVC(
    kernel="linear",
    probability=True
)

model.fit(
    embeddings,
    encoded_labels
)

# ==========================================
# SAVE MODEL
# ==========================================

joblib.dump(
    model,
    "models/student_face_model.pkl"
)

joblib.dump(
    encoder,
    "models/student_label_encoder.pkl"
)

print("\nTraining Completed Successfully!")

print("\nSaved Files")

print("models/student_face_model.pkl")
print("models/student_label_encoder.pkl")

print("=" * 60)