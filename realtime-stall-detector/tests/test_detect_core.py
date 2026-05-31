# tests/test_detect_core.py
from src.collect import generate_sim_dataset, DEFAULT_SCENARIO
from src.train import build_dataset, train_model
from src.sources import SimulatedSource
from src.detect import run_detection

def test_detection_alarms_on_stall_only(tmp_path):
    csv = tmp_path / "d.csv"
    generate_sim_dataset(csv, scenario=DEFAULT_SCENARIO, fs=1000, seed=0)
    X, y = build_dataset(csv); model, _ = train_model(X, y, seed=0)

    # fresh scenario with a clear stall in the middle
    src = SimulatedSource([("off",0.3),("startup",0.3),("running",1.0),
                           ("stall",0.8),("running",1.0)], fs=1000, seed=7)
    log = []
    run_detection(src, model, on_update=lambda t,x,p,s: log.append((t, s)))
    states = [s for _, s in log]
    assert "stall" in states                       # alarm fires during stall
    # no alarm in the first second (off/startup/running region)
    early = [s for t, s in log if t < 0.9]
    assert "stall" not in early
