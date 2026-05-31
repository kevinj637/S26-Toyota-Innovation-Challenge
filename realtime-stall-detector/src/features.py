"""Windowed feature extraction — shared by training, realtime, and (mirrored in) A2 firmware.

Features (threshold-free, transfer across motors):
  mean, std, rms, peak, max_slope, half_diff
half_diff = mean(second half) - mean(first half):
  ~0 for steady (stall/running), strongly negative for decaying (startup inrush).
"""
from collections import deque
import numpy as np
from src.config import WINDOW_S, HOP_S, FEATURE_NAMES

def compute_features(t, x):
    t = np.asarray(t, float); x = np.asarray(x, float)
    n = len(x)
    mean = float(np.mean(x))
    std = float(np.std(x))
    rms = float(np.sqrt(np.mean(x*x)))
    peak = float(np.max(x))
    dt = np.diff(t); dx = np.diff(x)
    slopes = np.divide(dx, dt, out=np.zeros_like(dx), where=dt > 0)
    max_slope = float(np.max(np.abs(slopes))) if slopes.size else 0.0
    half = n // 2
    half_diff = float(np.mean(x[half:]) - np.mean(x[:half])) if n >= 2 else 0.0
    return np.array([mean, std, rms, peak, max_slope, half_diff], float)

def iter_windows(t, x, labels=None, window_s=WINDOW_S, hop_s=HOP_S):
    """Yield (feature_vector, majority_label_or_None) over sliding windows."""
    t = np.asarray(t, float); x = np.asarray(x, float)
    if t.size == 0:
        return
    w0, end = t[0], t[-1]
    while w0 + window_s <= end + 1e-9:
        mask = (t >= w0) & (t < w0 + window_s)
        if mask.sum() >= 2:
            feat = compute_features(t[mask], x[mask])
            lab = None
            if labels is not None:
                vals, counts = np.unique(np.asarray(labels)[mask], return_counts=True)
                lab = str(vals[int(np.argmax(counts))])
            yield feat, lab
        w0 += hop_s

class FeatureStreamer:
    """Incremental feature emission for realtime streams. push(t,x) -> vector | None."""
    def __init__(self, window_s=WINDOW_S, hop_s=HOP_S):
        self.window_s = window_s; self.hop_s = hop_s
        self.t = deque(); self.x = deque(); self.next_emit = None

    def push(self, t, x):
        self.t.append(t); self.x.append(x)
        while self.t and (self.t[-1] - self.t[0]) > self.window_s:
            self.t.popleft(); self.x.popleft()
        if self.next_emit is None:
            self.next_emit = self.t[0] + self.window_s
        if t >= self.next_emit and (self.t[-1] - self.t[0]) >= self.window_s*0.8 and len(self.t) >= 2:
            self.next_emit = t + self.hop_s
            return compute_features(np.array(self.t), np.array(self.x))
        return None
