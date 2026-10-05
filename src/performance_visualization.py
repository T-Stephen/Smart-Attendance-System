import joblib
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay
)

# ==========================================
# Load Dataset
# ==========================================

data = joblib.load("models/student_embeddings.pkl")

X = data["embeddings"]
y = data["labels"]

print("="*60)
print("STUDENT FACE RECOGNITION MODEL PERFORMANCE")
print("="*60)

print(f"Total Samples : {len(X)}")
print(f"Total Students: {len(set(y))}")

# ==========================================
# Train Test Split
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.40,
    random_state=42,
    stratify=y
)

print(f"\nTraining Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")

# ==========================================
# Train SVM Model
# ==========================================

model = SVC(
    kernel="linear",
    C=0.5,
    probability=True
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

# ==========================================
# Metrics
# ==========================================

accuracy = accuracy_score(y_test, pred) * 100

precision = precision_score(
    y_test,
    pred,
    average="weighted"
) * 100

recall = recall_score(
    y_test,
    pred,
    average="weighted"
) * 100

f1 = f1_score(
    y_test,
    pred,
    average="weighted"
) * 100

print("\n")
print("="*60)
print("MODEL PERFORMANCE")
print("="*60)

print(f"Accuracy  : {accuracy:.2f}%")
print(f"Precision : {precision:.2f}%")
print(f"Recall    : {recall:.2f}%")
print(f"F1 Score  : {f1:.2f}%")

# ==========================================
# BAR CHART
# ==========================================

metrics = ["Accuracy","Precision","Recall","F1 Score"]

values = [
    accuracy,
    precision,
    recall,
    f1
]

plt.figure(figsize=(9,5))

colors = [
    "royalblue",
    "seagreen",
    "orange",
    "crimson"
]

bars = plt.bar(metrics, values, color=colors)

plt.ylim(0,100)

plt.ylabel("Percentage (%)")

plt.title("Student Face Recognition Model Performance")

for bar in bars:

    h = bar.get_height()

    plt.text(
        bar.get_x()+bar.get_width()/2,
        h+0.15,
        f"{h:.2f}%",
        ha="center",
        fontsize=11,
        fontweight="bold"
    )

plt.grid(axis="y",linestyle="--",alpha=0.5)

plt.tight_layout()

plt.show()

# ==========================================
# CONFUSION MATRIX
# ==========================================

cm = confusion_matrix(y_test,pred)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm
)

disp.plot(cmap="Blues")

plt.title("Confusion Matrix")

plt.show()