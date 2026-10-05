import pickle
import os
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

print("=" * 60)
print("Training Face Recognition Model")
print("=" * 60)

# Load embeddings
with open("models/dataset_embeddings.pkl", "rb") as f:
    data = pickle.load(f)

embeddings = data["embeddings"]
labels = data["labels"]

print(f"Total Embeddings : {len(embeddings)}")

# Encode labels
encoder = LabelEncoder()
encoded_labels = encoder.fit_transform(labels)

print(f"Total Persons    : {len(encoder.classes_)}")

print("\nTraining SVM Classifier...")

# Train classifier
model = SVC(kernel="linear", probability=True)
model.fit(embeddings, encoded_labels)

# Save model
os.makedirs("models", exist_ok=True)

with open("models/dataset_face_model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("models/dataset_label_encoder.pkl", "wb") as f:
    pickle.dump(encoder, f)

print("\nTraining Completed Successfully!")

print("\nSaved Files:")
print("models/dataset_face_model.pkl")
print("models/dataset_label_encoder.pkl")