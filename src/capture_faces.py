import cv2
import os

name = input("Enter Person Name: ")

folder = f"database/{name}"

os.makedirs(folder, exist_ok=True)

camera = cv2.VideoCapture(0)

count = 0

print("Press SPACE to capture images")
print("Press ESC to exit")

while True:
    ret, frame = camera.read()

    if not ret:
        break

    cv2.imshow("Capture Face", frame)

    key = cv2.waitKey(1)

    if key % 256 == 27:
        break

    elif key % 256 == 32:
        img_name = f"{folder}/{count}.jpg"
        cv2.imwrite(img_name, frame)
        print(f"Saved {img_name}")
        count += 1

camera.release()
cv2.destroyAllWindows()