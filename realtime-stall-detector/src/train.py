"""Train an interpretable decision tree; report vs a threshold baseline; save artifacts."""
import argparse
import os
import numpy as np
import pandas as pd
import joblib
from src.features import iter_windows
from src.config import CLASSES, FEATURE_NAMES

def build_dataset(csv_path):
    df = pd.read_csv(csv_path)
    t = df["t_s"].to_numpy(); x = df["current_a"].to_numpy(); labels = df["label"].to_numpy()
    X, y = [], []
    for feat, lab in iter_windows(t, x, labels):
        X.append(feat); y.append(lab)
    return np.array(X), np.array(y)

def train_model(X, y, max_depth=4, seed=0):
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import confusion_matrix, classification_report
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)
    clf = DecisionTreeClassifier(max_depth=max_depth, random_state=seed).fit(Xtr, ytr)
    pred = clf.predict(Xte)
    info = {
        "confusion": confusion_matrix(yte, pred, labels=CLASSES),
        "labels": list(CLASSES),
        "report": classification_report(yte, pred, zero_division=0),
    }
    return clf, info

def threshold_baseline(X, y, feature="mean"):
    """Naive: alarm when mean current high. Reports how often it false-alarms on startup."""
    idx = FEATURE_NAMES.index(feature)
    stall_vals = X[y == "stall"][:, idx]
    thr = float(np.percentile(stall_vals, 10)) if len(stall_vals) else 0.0
    startup_mask = y == "startup"
    false_alarm = float(np.mean(X[startup_mask][:, idx] > thr)) if startup_mask.any() else 0.0
    return {"threshold": thr, "startup_false_alarm_rate": false_alarm}

def save_model(clf, path="model/tree.joblib"):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    joblib.dump({"model": clf, "features": FEATURE_NAMES, "classes": CLASSES}, path)

def save_tree_viz(clf, path="plots/tree.txt"):
    from sklearn.tree import export_text
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w") as f:
        f.write(export_text(clf, feature_names=FEATURE_NAMES))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/labeled.csv")
    ap.add_argument("--model", default="model/tree.joblib")
    args = ap.parse_args()
    X, y = build_dataset(args.data)
    print(X,y)
    clf, info = train_model(X, y)
    print(info["report"])
    print("Confusion (rows=true", info["labels"], "):\n", info["confusion"])
    print("Threshold baseline:", threshold_baseline(X, y))
    save_model(clf, args.model)
    save_tree_viz(clf)
    print(f"Saved model -> {args.model}; tree rules -> plots/tree.txt")
