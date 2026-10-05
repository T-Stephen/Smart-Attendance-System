import joblib

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


# ============================================================
# LOAD DATASET
# ============================================================

data = joblib.load(
    "models/student_embeddings.pkl"
)

X = data["embeddings"]
y = data["labels"]


print("=" * 70)
print("SVM HYPERPARAMETER TUNING")
print("=" * 70)

print(f"Total Samples  : {len(X)}")
print(f"Total Students : {len(set(y))}")


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.40,
    random_state=42,
    stratify=y
)


print(f"\nTraining Samples : {len(X_train)}")
print(f"Testing Samples  : {len(X_test)}")


# ============================================================
# SVM MODEL
# ============================================================

svm = SVC(
    probability=True
)


# ============================================================
# HYPERPARAMETER GRID
# ============================================================

param_grid = {

    "C": [
        0.1,
        0.5,
        1,
        2,
        5,
        10
    ],

    "kernel": [
        "linear",
        "rbf",
        "poly"
    ],

    "gamma": [
        "scale",
        "auto"
    ]

}


# ============================================================
# GRID SEARCH
# ============================================================

grid_search = GridSearchCV(
    estimator=svm,
    param_grid=param_grid,
    cv=5,
    scoring="accuracy",
    n_jobs=-1,
    verbose=1
)


print("\nStarting hyperparameter tuning...")
print("Please wait...\n")


grid_search.fit(
    X_train,
    y_train
)


# ============================================================
# BEST PARAMETERS
# ============================================================

print("\n" + "=" * 70)
print("BEST HYPERPARAMETERS")
print("=" * 70)

print(
    "Best Parameters :",
    grid_search.best_params_
)

print(
    f"Best CV Accuracy : "
    f"{grid_search.best_score_ * 100:.2f}%"
)


# ============================================================
# BEST MODEL
# ============================================================

best_model = grid_search.best_estimator_


predictions = best_model.predict(
    X_test
)


# ============================================================
# EVALUATION
# ============================================================

accuracy = accuracy_score(
    y_test,
    predictions
) * 100


precision = precision_score(
    y_test,
    predictions,
    average="weighted",
    zero_division=0
) * 100


recall = recall_score(
    y_test,
    predictions,
    average="weighted",
    zero_division=0
) * 100


f1 = f1_score(
    y_test,
    predictions,
    average="weighted",
    zero_division=0
) * 100


cm = confusion_matrix(
    y_test,
    predictions
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 70)
print("TUNED MODEL PERFORMANCE")
print("=" * 70)

print(f"Accuracy  : {accuracy:.2f}%")
print(f"Precision : {precision:.2f}%")
print(f"Recall    : {recall:.2f}%")
print(f"F1 Score  : {f1:.2f}%")


print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print(cm)


# ============================================================
# SAVE RESULTS
# ============================================================

results = {

    "best_parameters":
        grid_search.best_params_,

    "cv_accuracy":
        grid_search.best_score_ * 100,

    "accuracy":
        accuracy,

    "precision":
        precision,

    "recall":
        recall,

    "f1_score":
        f1,

    "confusion_matrix":
        cm,

    "model":
        best_model

}


joblib.dump(
    results,
    "models/tuned_svm_results.pkl"
)


print("\n" + "=" * 70)
print("TUNING COMPLETED")
print("=" * 70)

print(
    "Results saved to:"
)

print(
    "models/tuned_svm_results.pkl"
)