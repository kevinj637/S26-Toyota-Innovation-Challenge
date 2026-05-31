import numpy as np
from src.config import FEATURE_NAMES
from src.features import compute_features, iter_windows, FeatureStreamer

def test_compute_features_shape_and_values():
    t = np.arange(75) / 1000.0
    x = np.full(75, 1.2)  # flat high (stall-like)
    f = compute_features(t, x)
    assert f.shape == (len(FEATURE_NAMES),)
    mean, std, rms, peak, max_slope, half_diff = f
    assert abs(mean - 1.2) < 1e-6
    assert std < 1e-6 and abs(half_diff) < 1e-6 and max_slope < 1e-6

def test_half_diff_negative_for_decaying_window():
    t = np.arange(100) / 1000.0
    x = np.linspace(1.2, 0.2, 100)  # decaying (startup-like)
    f = compute_features(t, x)
    assert f[FEATURE_NAMES.index("half_diff")] < -0.3

def test_iter_windows_yields_labeled_vectors():
    t = np.arange(300) / 1000.0
    x = np.concatenate([np.full(150, 0.15), np.full(150, 1.2)])
    labels = np.array(["normal"]*150 + ["stall"]*150)
    out = list(iter_windows(t, x, labels, window_s=0.075, hop_s=0.025))
    assert len(out) > 0
    feats, labs = zip(*out)
    assert all(f.shape == (len(FEATURE_NAMES),) for f in feats)
    assert "normal" in labs and "stall" in labs

def test_streamer_emits_periodically():
    streamer = FeatureStreamer(window_s=0.075, hop_s=0.025)
    emitted = 0
    for i in range(300):
        f = streamer.push(i/1000.0, 1.0)
        if f is not None:
            assert f.shape == (len(FEATURE_NAMES),)
            emitted += 1
    assert emitted >= 5  # roughly (0.3s - 0.075s)/0.025s
