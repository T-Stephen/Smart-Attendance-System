import joblib
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)

print("=" * 60)
print(" STUDENT FACE RECOGNITION MODEL EVALUATION ")
print("=" * 60)

# ==========================================
# Load Embeddings
# ==========================================

data = joblib.load("models/student_embeddings.pkl")

X = data["embeddings"]
y = data["labels"]

print(f"Total Samples : {len(X)}")
print(f"Total Students: {len(set(y))}")

# ==========================================
# Train-Test Split
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.40,      # 40% Testing
    random_state=42,
    stratify=y
)

print(f"\nTraining Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")

# ==========================================
# Train SVM
# ==========================================

model = SVC(
    kernel="linear",
    C=0.5,
    probability=True
)

print("\nTraining Model...")
model.fit(X_train, y_train)

# ==========================================
# Prediction
# ==========================================

pred = model.predict(X_test)

# ==========================================
# Metrics
# ==========================================

accuracy = accuracy_score(y_test, pred)
precision = precision_score(
    y_test,
    pred,
    average="weighted"
)
recall = recall_score(
    y_test,
    pred,
    average="weighted"
)
f1 = f1_score(
    y_test,
    pred,
    average="weighted"
)

print("\n" + "=" * 60)
print("MODEL PERFORMANCE")
print("=" * 60)

print(f"Accuracy :  {accuracy*100:.2f}%")
print(f"Precision:  {precision*100:.2f}%")
print(f"Recall   :  {recall*100:.2f}%")
print(f"F1 Score :  {f1*100:.2f}%")

# ==========================================
# Classification Report
# ==========================================

print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)

print(classification_report(y_test, pred))

# ==========================================
# Confusion Matrix
# ==========================================

print("\n" + "=" * 60)
print("CONFUSION MATRIX")
print("=" * 60)

print(confusion_matrix(y_test, pred))