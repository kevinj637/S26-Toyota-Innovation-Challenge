"""Physics-flavoured DC-motor current generator.

Current ~ (V - back_emf)/R. Back-emf scales with speed, so:
- off: ~0
- running: low, steady (+ small ripple)
- startup: inrush from stall-level decaying to running level
- stall: high, sustained
"""
from dataclasses import dataclass
import numpy as np

@dataclass
class MotorParams:
    i_off: float = 0.0
    i_run: float = 0.15
    i_stall: float = 1.2
    startup_tau_s: float = 0.12
    noise_a: float = 0.01
    ripple_a: float = 0.004
    ripple_hz: float = 60.0

STATE_TO_LABEL = {"off": "normal", "running": "normal",
                  "startup": "startup", "stall": "stall"}

def _segment_current(state, tloc, p, rng):
    n = len(tloc)
    if state == "off":
        base = np.full(n, p.i_off)
    elif state == "running":
        base = p.i_run + p.ripple_a * np.sin(2*np.pi*p.ripple_hz*tloc)
    elif state == "startup":
        base = p.i_run + (p.i_stall - p.i_run) * np.exp(-tloc / p.startup_tau_s)
    elif state == "stall":
        base = np.full(n, p.i_stall)
    else:
        raise ValueError(f"unknown state: {state}")
    return np.clip(base + rng.normal(0, p.noise_a, n), 0.0, None)

def simulate(segments, fs=1000, params=None, seed=0):
    """segments: list of (state, duration_s). Returns (times_s, currents_a, labels)."""
    p = params or MotorParams()
    rng = np.random.default_rng(seed)
    times, currents, labels = [], [], []
    t0 = 0.0
    for state, dur in segments:
        n = int(dur * fs)
        tloc = np.arange(n) / fs
        currents.append(_segment_current(state, tloc, p, rng))
        times.append(t0 + tloc)
        labels.append(np.full(n, STATE_TO_LABEL[state]))
        t0 += n / fs
    return np.concatenate(times), np.concatenate(currents), np.concatenate(labels)
