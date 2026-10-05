import os
import shutil

# -------------------------------
# CONFIGURATION
# -------------------------------

SOURCE_DATASET = "webface_112x112"
DESTINATION_DATASET = "training_dataset"

TARGET_IMAGES = 10000

# -------------------------------
# CREATE DESTINATION FOLDER
# -------------------------------

os.makedirs(DESTINATION_DATASET, exist_ok=True)

total_images = 0
total_people = 0

print("=" * 60)
print("Preparing Training Dataset")
print("=" * 60)

# Sort folders (id_0, id_1, ...)
person_folders = sorted(os.listdir(SOURCE_DATASET))

for person in person_folders:

    person_path = os.path.join(SOURCE_DATASET, person)

    if not os.path.isdir(person_path):
        continue

    images = [
        img for img in os.listdir(person_path)
        if img.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    if len(images) == 0:
        continue

    destination_person = os.path.join(DESTINATION_DATASET, person)
    os.makedirs(destination_person, exist_ok=True)

    copied = 0

    for image in images:

        if total_images >= TARGET_IMAGES:
            break

        src = os.path.join(person_path, image)
        dst = os.path.join(destination_person, image)

        shutil.copy2(src, dst)

        total_images += 1
        copied += 1

    if copied > 0:
        total_people += 1
        print(f"{person:10s} --> {copied:3d} images copied")

    if total_images >= TARGET_IMAGES:
        break

print("\n" + "=" * 60)
print("Dataset Preparation Completed")
print("=" * 60)

print(f"Total Persons : {total_people}")
print(f"Total Images  : {total_images}")

print("\nDataset Saved To:")
print(DESTINATION_DATASET)