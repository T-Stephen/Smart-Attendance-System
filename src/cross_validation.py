import joblib
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

data = joblib.load("models/student_embeddings.pkl")

X = data["embeddings"]
y = data["labels"]

model = SVC(kernel="linear")

scores = cross_val_score(
    model,
    X,
    y,
    cv=5
)

print("Cross Validation Scores")
print(scores)

print("Average Accuracy")
print(scores.mean()*100)