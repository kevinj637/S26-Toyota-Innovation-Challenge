import numpy as np
from src.simulator import simulate, MotorParams

def test_segments_have_expected_levels_and_labels():
    segs = [("off", 0.2), ("startup", 0.3), ("running", 0.5), ("stall", 0.4)]
    t, x, y = simulate(segs, fs=1000, seed=1)
    assert len(t) == len(x) == len(y) == int(0.2*1000)+int(0.3*1000)+int(0.5*1000)+int(0.4*1000)
    # labels mapped: off/running -> normal, startup -> startup, stall -> stall
    assert set(np.unique(y)) == {"normal", "startup", "stall"}
    # stall current sustained near i_stall; off near 0
    p = MotorParams()
    stall = x[y == "stall"]
    assert abs(np.mean(stall) - p.i_stall) < 0.1
    assert np.mean(x[:int(0.2*1000)]) < 0.05  # off segment ~ 0

def test_startup_decays_toward_running():
    t, x, y = simulate([("startup", 0.5)], fs=1000, seed=2)
    first_quarter = np.mean(x[:125]); last_quarter = np.mean(x[-125:])
    assert first_quarter > last_quarter  # inrush decays
