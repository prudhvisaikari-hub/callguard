"""Train the TF-IDF + LogisticRegression risk prefilter with CV and validation metrics.
Run: python ml/train.py
"""
import csv
import json
import pathlib
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score, accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import make_pipeline

root = pathlib.Path(__file__).parent
data_file = root / "data" / "seed_lines.csv"

rows = list(csv.DictReader(open(data_file, encoding="utf-8")))
X = [r["text"] for r in rows]
y = np.array([int(r["label"]) for r in rows])

print(f"Loaded {len(X)} samples (Risky={sum(y == 1)}, Safe={sum(y == 0)})")

# Stratified 80/20 train/validation split
X_tr, X_val, y_tr, y_val = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# Pipeline with sublinear TF-IDF and balanced LogisticRegression
pipeline = make_pipeline(
    TfidfVectorizer(
        ngram_range=(1, 2),
        sublinear_tf=True,
        min_df=1,
    ),
    LogisticRegression(
        solver="liblinear",
        C=2.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    ),
)

# 5-fold Stratified Cross-Validation on the training set
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_results = cross_validate(
    pipeline,
    X_tr,
    y_tr,
    cv=cv,
    scoring=["accuracy", "precision", "recall", "f1"],
    return_train_score=False,
)

# Fit on training split and evaluate on hold-out validation set
pipeline.fit(X_tr, y_tr)
y_pred = pipeline.predict(X_val)
report_dict = classification_report(y_val, y_pred, output_dict=True)
report_text = classification_report(y_val, y_pred, target_names=["Safe (0)", "Risky (1)"])

print("\n--- Hold-out Validation Report (20% split) ---")
print(report_text)

val_risky_recall = report_dict["1"]["recall"]
val_risky_precision = report_dict["1"]["precision"]
val_risky_f1 = report_dict["1"]["f1-score"]

cv_metrics = {
    "cv_accuracy_mean": float(np.mean(cv_results["test_accuracy"])),
    "cv_accuracy_std": float(np.std(cv_results["test_accuracy"])),
    "cv_recall_risky_mean": float(np.mean(cv_results["test_recall"])),
    "cv_recall_risky_std": float(np.std(cv_results["test_recall"])),
    "cv_precision_risky_mean": float(np.mean(cv_results["test_precision"])),
    "cv_precision_risky_std": float(np.std(cv_results["test_precision"])),
    "cv_f1_risky_mean": float(np.mean(cv_results["test_f1"])),
    "cv_f1_risky_std": float(np.std(cv_results["test_f1"])),
}

print("--- 5-Fold Cross-Validation Metrics on Training Set ---")
print(f"CV Recall (Risky):    {cv_metrics['cv_recall_risky_mean']:.4f} ± {cv_metrics['cv_recall_risky_std']:.4f}")
print(f"CV Precision (Risky): {cv_metrics['cv_precision_risky_mean']:.4f} ± {cv_metrics['cv_precision_risky_std']:.4f}")
print(f"CV Accuracy:          {cv_metrics['cv_accuracy_mean']:.4f} ± {cv_metrics['cv_accuracy_std']:.4f}")

metrics = {
    "dataset_size": len(X),
    "classes": {"safe": int(sum(y == 0)), "risky": int(sum(y == 1))},
    "holdout_validation": {
        "accuracy": float(accuracy_score(y_val, y_pred)),
        "risky_recall": float(val_risky_recall),
        "risky_precision": float(val_risky_precision),
        "risky_f1": float(val_risky_f1),
        "per_class": report_dict,
    },
    "cross_validation": cv_metrics,
}

metrics_path = root / "metrics.json"
metrics_path.write_text(json.dumps(metrics, indent=2))
print(f"\nSaved metrics -> {metrics_path}")

# Retrain on 100% of data for deployment
pipeline.fit(X, y)
joblib.dump(pipeline, root / "risk_clf.joblib")
print(f"Saved trained classifier -> {root / 'risk_clf.joblib'}")

# Verify target recall
if val_risky_recall < 0.85:
    print(f"WARNING: Holdout risky recall {val_risky_recall:.3f} is below 0.85 target!")
else:
    print(f"SUCCESS: Holdout risky recall {val_risky_recall:.3f} meets >= 0.85 target.")
