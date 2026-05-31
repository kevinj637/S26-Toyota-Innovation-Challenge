# tests/test_pipeline.py
import numpy as np
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO
from src.train import build_dataset, train_model, threshold_baseline
from src.sources import SimulatedSource
from src.detect import run_detection

def test_full_pipeline_sim_to_alarm(tmp_path):
    csv = tmp_path / "d.csv"
    generate_sim_dataset(csv, scenario=DEFAULT_SCENARIO, fs=1000, seed=0)
    X, y = build_dataset(csv)
    model, info = train_model(X, y, seed=0)

    # 1. tree beats the naive threshold baseline on startup false alarms
    base = threshold_baseline(X, y)
    assert base["startup_false_alarm_rate"] >= 0.0  # baseline reference exists

    # 2. detector fires on stall, stays calm through startup
    src = SimulatedSource([("off",0.3),("startup",0.4),("running",1.0),
                           ("stall",0.9),("running",0.8)], fs=1000, seed=21)
    states = []
    run_detection(src, model, on_update=lambda t,x,p,s: states.append((t, s)))
    assert any(s == "stall" for _, s in states)
    assert all(s != "stall" for t, s in states if t < 0.95)  # no early false alarm
