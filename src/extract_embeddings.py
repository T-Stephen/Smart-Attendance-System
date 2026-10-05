import os
import cv2
import pickle
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet

# Initialize MTCNN and FaceNet
detector = MTCNN()
embedder = FaceNet()

database_path = "database"

embeddings = []
names = []

print("=" * 50)
print("Extracting Face Embeddings...")
print("=" * 50)

for person in os.listdir(database_path):

    person_path = os.path.join(database_path, person)

    if not os.path.isdir(person_path):
        continue

    print(f"\nProcessing Person: {person}")

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        try:
            # Read image
            image = cv2.imread(image_path)

            if image is None:
                print(f"Could not read: {image_path}")
                continue

            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Detect face
            try:
                faces = detector.detect_faces(rgb)
            except Exception:
                print(f"Skipping {image_path} (Face detection failed)")
                continue

            if len(faces) == 0:
                print(f"No face detected: {image_path}")
                continue

            # Get first detected face
            x, y, w, h = faces[0]['box']

            x = max(0, x)
            y = max(0, y)

            face = rgb[y:y+h, x:x+w]

            if face.size == 0:
                print(f"Invalid face crop: {image_path}")
                continue

            # Resize face
            face = cv2.resize(face, (160, 160))

            # Generate embedding
            embedding = embedder.embeddings([face])[0]

            embeddings.append(embedding)
            names.append(person)

            print(f"Processed: {image_path}")

        except Exception as e:
            print(f"Skipped {image_path}")
            print(f"Reason: {e}")
            continue

print("\nSaving embeddings...")

os.makedirs("models", exist_ok=True)

data = {
    "embeddings": np.array(embeddings),
    "names": names
}

with open("models/embeddings.pkl", "wb") as f:
    pickle.dump(data, f)

print("\n" + "=" * 50)
print("Embedding Extraction Completed Successfully!")
print("=" * 50)
print(f"Total Images Processed : {len(names)}")
print(f"Total Embeddings Saved : {len(embeddings)}")
print("File Saved : models/embeddings.pkl")