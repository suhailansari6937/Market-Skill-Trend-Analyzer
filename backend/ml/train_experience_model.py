
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from app.db.database import SessionLocal
from app.models import Job


# 1. Fetch training data from database
db = SessionLocal()

try:
    records = (
        db.query(Job.description, Job.experience_level)
        .filter(
            Job.experience_level.in_(
                ["Entry", "Mid", "Senior", "Intern"]
            ),
            Job.description.isnot(None)
        )
        .all()
    )
finally:
    db.close()


# 2. Prepare features and labels
X = [row.description.strip() for row in records]
y = [row.experience_level for row in records]

print("Total records:", len(X))

# 3. Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training records:", len(X_train))
print("Testing records:", len(X_test))


# 4. Build ML pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=30000,
            min_df=2,
            sublinear_tf=True
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        )
    )
])


# 5. Train model
print("\nTraining model...")
model.fit(X_train, y_train)

# 6. Evaluate on unseen test data
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\n========== MODEL RESULTS ==========")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

print("\nConfusion Matrix:")
print(confusion_matrix(
    y_test,
    y_pred,
    labels=["Entry", "Intern", "Mid", "Senior"]
))


# 7. Save trained model
os.makedirs("ml", exist_ok=True)

joblib.dump(
    model,
    "ml/experience_level_model.joblib"
)

print("\nModel saved successfully!")
