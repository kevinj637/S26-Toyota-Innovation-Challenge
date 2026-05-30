# scripts/verify_now.py
"""Headless end-to-end proof: train, evaluate, save confusion matrix + dashboard snapshot."""
import os
import sys

# Allow `python scripts/verify_now.py` from the repo root (put repo root on sys.path).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO
from src.train import build_dataset, train_model, threshold_baseline, save_model
from src.sources import SimulatedSource
from src.detect import run_detection
from src.config import CLASSES

os.makedirs("data", exist_ok=True); os.makedirs("plots", exist_ok=True)
generate_sim_dataset("data/labeled.csv", DEFAULT_SCENARIO, fs=1000, seed=0)
X, y = build_dataset("data/labeled.csv")
model, info = train_model(X, y, seed=0)
save_model(model)
print(info["report"]); print("Confusion", info["labels"], "\n", info["confusion"])
print("Baseline:", threshold_baseline(X, y))

# confusion matrix figure
cm = info["confusion"]
fig, ax = plt.subplots()
ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(3)); ax.set_yticks(range(3))
ax.set_xticklabels(CLASSES); ax.set_yticklabels(CLASSES)
for i in range(3):
    for j in range(3):
        ax.text(j, i, cm[i][j], ha="center", va="center")
ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title("Stall detector confusion")
fig.savefig("plots/confusion.png", dpi=120)

# dashboard snapshot: current trace coloured by detected state
src = SimulatedSource([("off",0.4),("startup",0.3),("running",1.2),
                       ("stall",0.9),("running",1.0),("off",0.3)], fs=1000, seed=11)
log = []
run_detection(src, model, on_update=lambda t,x,p,s: log.append((t, x, s)))
t = [r[0] for r in log]; x = [r[1] for r in log]; s = [r[2] for r in log]
col = {"normal":"green","warning":"orange","stall":"red"}
fig, ax = plt.subplots(figsize=(10,4))
ax.scatter(t, x, c=[col[v] for v in s], s=6)
ax.set_xlabel("Time (s)"); ax.set_ylabel("Current (A)")
ax.set_title("Detected state (green=normal, orange=startup, red=STALL)")
fig.savefig("plots/dashboard_snapshot.png", dpi=120)
print("Saved plots/confusion.png and plots/dashboard_snapshot.png")
