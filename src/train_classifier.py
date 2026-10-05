import pickle
import joblib
import os
import time

from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

print('=' * 50)
print('Training Face Recognition Models')
print('=' * 50)

# Load embeddings
with open('models/embeddings.pkl', 'rb') as f:
    data = pickle.load(f)

embeddings = data['embeddings']
names = data['names']

print(f'Total Embeddings : {len(embeddings)}')
print(f'Total Persons    : {len(set(names))}')

# Convert names into numbers
encoder = LabelEncoder()
labels = encoder.fit_transform(names)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    embeddings,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

# ---------------- SVM ----------------
print('\nTraining SVM Classifier...')
start = time.time()

svm_model = SVC(kernel='linear', probability=True)
svm_model.fit(X_train, y_train)

svm_train_time = time.time() - start

svm_pred = svm_model.predict(X_test)
svm_acc = accuracy_score(y_test, svm_pred)

# ---------------- Random Forest ----------------
print('Training Random Forest Classifier...')
start = time.time()

rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
rf_model.fit(X_train, y_train)

rf_train_time = time.time() - start

rf_pred = rf_model.predict(X_test)
rf_acc = accuracy_score(y_test, rf_pred)

# ---------------- Results ----------------
print('\n' + '=' * 50)
print('ALGORITHM COMPARISON')
print('=' * 50)
print(f'SVM Accuracy           : {svm_acc * 100:.2f}%')
print(f'SVM Training Time      : {svm_train_time:.2f} sec')
print('-' * 50)
print(f'Random Forest Accuracy : {rf_acc * 100:.2f}%')
print(f'RF Training Time       : {rf_train_time:.2f} sec')
print('=' * 50)

# Select the better model
if svm_acc >= rf_acc:
    best_model = svm_model
    best_name = 'SVM'
    best_acc = svm_acc
else:
    best_model = rf_model
    best_name = 'Random Forest'
    best_acc = rf_acc

# Save the best model
os.makedirs('models', exist_ok=True)

joblib.dump(best_model, 'models/face_recognition_model.pkl')
joblib.dump(encoder, 'models/label_encoder.pkl')

print(f'\nBest Model Selected : {best_name}')
print(f'Best Accuracy       : {best_acc * 100:.2f}%')

print('\nSaved Files:')
print('models/face_recognition_model.pkl')
print('models/label_encoder.pkl')