import cv2
import joblib
import numpy as np
from mtcnn import MTCNN
from keras_facenet import FaceNet
from attendance_manager import mark_attendance
from utils.face_verifier import verify_face

# ============================================
# Load Dataset Model
# ============================================

model = joblib.load("models/student_face_model.pkl")
encoder = joblib.load("models/student_label_encoder.pkl")

# ============================================
# Initialize Face Detector & FaceNet
# ============================================

detector = MTCNN()
embedder = FaceNet()

# ============================================
# Open Webcam
# ============================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open webcam.")
    exit()

print("=" * 60)
print(" Smart Attendance System")
print(" Press ESC to Exit")
print("=" * 60)

while True:

    ret, frame = cap.read()

    if not ret:
        print("Failed to read frame.")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # -------------------------------
    # Face Detection
    # -------------------------------

    try:
        faces = detector.detect_faces(rgb)
    except Exception:
        cv2.imshow("Smart Attendance System", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        continue

    # -------------------------------
    # Process Each Face
    # -------------------------------

    for face in faces:

        try:

            x, y, w, h = face["box"]

            # Ignore very small detections
            if w < 40 or h < 40:
                continue

            x = max(0, x)
            y = max(0, y)

            if x + w > rgb.shape[1]:
                w = rgb.shape[1] - x

            if y + h > rgb.shape[0]:
                h = rgb.shape[0] - y

            crop = rgb[y:y+h, x:x+w]

            if crop.size == 0:
                continue

            crop = cv2.resize(crop, (160, 160))

            embedding = embedder.embeddings([crop])[0]

            prediction = model.predict([embedding])[0]

            probabilities = model.predict_proba([embedding])[0]

            confidence = np.max(probabilities)

            name = encoder.inverse_transform([prediction])[0]

            # -------------------------------
            # Unknown Threshold
            # -------------------------------

            if confidence < 0.80:

                name = "Unknown"
                color = (0, 0, 255)

            else:

                color = (0, 255, 0)

                mark_attendance(
                    name,
                    confidence * 100
                )

            # -------------------------------
            # Draw Face Box
            # -------------------------------

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            cv2.putText(
                frame,
                f"{name} ({confidence*100:.2f}%)",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

        except Exception:
            # Skip this face if any error occurs
            continue

    cv2.imshow("Smart Attendance System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()