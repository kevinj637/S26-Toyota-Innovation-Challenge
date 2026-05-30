import numpy as np
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO
from src.train import build_dataset, train_model
from src.config import CLASSES

def test_train_separates_startup_from_stall(tmp_path):
    csv = tmp_path / "d.csv"
    generate_sim_dataset(csv, scenario=DEFAULT_SCENARIO, fs=1000, seed=0)
    X, y = build_dataset(csv)
    assert X.shape[1] == 6 and len(X) == len(y)
    model, info = train_model(X, y, seed=0)
    cm = info["confusion"]; labels = info["labels"]
    si = labels.index("startup"); ti = labels.index("stall")
    # stall recall high
    stall_total = cm[ti].sum()
    assert cm[ti][ti] / max(stall_total, 1) >= 0.9
    # startup almost never predicted as stall (the key safety property)
    assert cm[si][ti] <= 1
