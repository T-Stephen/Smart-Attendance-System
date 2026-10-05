import os
import cv2
import pickle
import numpy as np

from mtcnn import MTCNN
from keras_facenet import FaceNet

print("=" * 60)
print("Extracting Embeddings from Training Dataset")
print("=" * 60)

# Initialize models
detector = MTCNN()
embedder = FaceNet()

dataset_path = "training_dataset"

embeddings = []
labels = []

total_images = 0
processed_images = 0
skipped_images = 0

# Count total images
for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)
    if os.path.isdir(person_path):
        total_images += len(os.listdir(person_path))

print(f"\nTotal Images Found : {total_images}\n")

for person in sorted(os.listdir(dataset_path)):

    person_path = os.path.join(dataset_path, person)

    if not os.path.isdir(person_path):
        continue

    print(f"\nProcessing {person}")

    for image_name in os.listdir(person_path):

        image_path = os.path.join(person_path, image_name)

        image = cv2.imread(image_path)

        if image is None:
            skipped_images += 1
            continue

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        try:
            faces = detector.detect_faces(rgb)

            if len(faces) == 0:
                skipped_images += 1
                continue

            x, y, w, h = faces[0]["box"]

            x = max(0, x)
            y = max(0, y)

            face = rgb[y:y+h, x:x+w]

            if face.size == 0:
                skipped_images += 1
                continue

            face = cv2.resize(face, (160,160))

            embedding = embedder.embeddings([face])[0]

            embeddings.append(embedding)
            labels.append(person)

            processed_images += 1

            if processed_images % 100 == 0:
                print(f"Processed {processed_images} / {total_images}")

        except Exception:
            skipped_images += 1
            continue


os.makedirs("models", exist_ok=True)

data = {
    "embeddings": np.array(embeddings),
    "labels": np.array(labels)
}

with open("models/dataset_embeddings.pkl", "wb") as f:
    pickle.dump(data, f)

print("\n")
print("=" * 60)
print("Embedding Extraction Completed")
print("=" * 60)

print(f"Processed Images : {processed_images}")
print(f"Skipped Images   : {skipped_images}")
print(f"Saved File       : models/dataset_embeddings.pkl")