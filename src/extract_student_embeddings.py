import os
import pickle
import cv2
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet

# ==========================================
# CONFIGURATION
# ==========================================

FACES_DIR = "registered_faces"
OUTPUT_FILE = "models/student_embeddings.pkl"

# ==========================================
# INITIALIZE MODELS
# ==========================================

detector = MTCNN()
embedder = FaceNet()

# ==========================================
# STORAGE
# ==========================================

embeddings = []
labels = []

# ==========================================
# PROCESS STUDENT FOLDERS
# ==========================================

if not os.path.exists(FACES_DIR):
    print("registered_faces folder not found!")
    exit()

student_folders = os.listdir(FACES_DIR)

print("=" * 60)
print("   EXTRACTING STUDENT EMBEDDINGS")
print("=" * 60)

total_processed = 0
total_skipped = 0

for student_id in student_folders:

    student_path = os.path.join(FACES_DIR, student_id)

    if not os.path.isdir(student_path):
        continue

    image_files = os.listdir(student_path)

    processed = 0

    for image_name in image_files:

        image_path = os.path.join(student_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            total_skipped += 1
            continue

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        try:
            faces = detector.detect_faces(rgb)
        except:
            total_skipped += 1
            continue

        if len(faces) == 0:
            total_skipped += 1
            continue

        # Use the largest face
        face = max(faces, key=lambda f: f["box"][2] * f["box"][3])

        x, y, w, h = face["box"]

        x = max(0, x)
        y = max(0, y)

        if w < 40 or h < 40:
            total_skipped += 1
            continue

        crop = rgb[y:y+h, x:x+w]

        if crop.size == 0:
            total_skipped += 1
            continue

        try:
            crop = cv2.resize(crop, (160, 160))
        except:
            total_skipped += 1
            continue

        try:
            embedding = embedder.embeddings([crop])[0]
        except:
            total_skipped += 1
            continue

        embeddings.append(embedding)
        labels.append(student_id)

        processed += 1
        total_processed += 1

    print(f"{student_id} --> {processed} embeddings extracted")

# ==========================================
# SAVE EMBEDDINGS
# ==========================================

os.makedirs("models", exist_ok=True)

data = {
    "embeddings": np.array(embeddings),
    "labels": np.array(labels)
}

with open(OUTPUT_FILE, "wb") as f:
    pickle.dump(data, f)

print("\n" + "=" * 60)
print("Embedding Extraction Completed")
print(f"Processed : {total_processed}")
print(f"Skipped   : {total_skipped}")
print(f"Saved To  : {OUTPUT_FILE}")
print("=" * 60)