# src/detect.py  (state machine first; run_detection + dashboard added in Task 7)
"""Real-time detection: features -> model -> debounced state machine -> dashboard."""
from src.config import ENTER_N, EXIT_M

class StallStateMachine:
    """normal/warning/stall with debounce to reject single-window noise."""
    def __init__(self, enter_n=ENTER_N, exit_m=EXIT_M):
        self.enter_n = enter_n; self.exit_m = exit_m
        self.stall_streak = 0; self.normal_streak = 0
        self.state = "normal"

    def update(self, pred):
        if pred == "stall":
            self.stall_streak += 1; self.normal_streak = 0
        elif pred == "normal":
            self.normal_streak += 1; self.stall_streak = 0
        else:  # startup transient
            self.stall_streak = 0; self.normal_streak = 0

        if self.stall_streak >= self.enter_n:
            self.state = "stall"
        elif self.state == "stall":
            if self.normal_streak >= self.exit_m:
                self.state = "normal"
            # else hold "stall"
        elif pred == "startup":
            self.state = "warning"
        else:
            self.state = "normal"
        return self.state


import argparse
import joblib
import numpy as np
from src.features import FeatureStreamer

def run_detection(source, model, on_update=None, streamer=None, state_machine=None):
    """Drive source -> features -> model -> state machine. on_update(t,x,pred,state)."""
    streamer = streamer or FeatureStreamer()
    sm = state_machine or StallStateMachine()
    for t, x in source:
        feat = streamer.push(t, x)
        if feat is None:
            continue
        pred = model.predict(feat.reshape(1, -1))[0]
        state = sm.update(pred)
        if on_update:
            on_update(t, x, pred, state)

def _load_model(path):
    bundle = joblib.load(path)
    return bundle["model"]

def run_dashboard(source, model):
    """Live matplotlib current plot + green/red status banner (A1 demo)."""
    import matplotlib.pyplot as plt
    from collections import deque
    fig, ax = plt.subplots(figsize=(10, 4))
    ts, xs = deque(maxlen=2000), deque(maxlen=2000)
    line, = ax.plot([], [], lw=1)
    banner = ax.text(0.5, 0.92, "NORMAL", transform=ax.transAxes, ha="center",
                     fontsize=20, color="white", bbox=dict(boxstyle="round", fc="green"))
    ax.set_xlabel("Time (s)"); ax.set_ylabel("Current (A)")
    plt.ion(); plt.show()
    color = {"normal": "green", "warning": "orange", "stall": "red"}

    def on_update(t, x, pred, state):
        ts.append(t); xs.append(x)
        line.set_data(ts, xs)
        ax.relim(); ax.autoscale_view()
        banner.set_text(state.upper())
        banner.get_bbox_patch().set_facecolor(color[state])
        plt.pause(0.001)

    run_detection(source, model, on_update=on_update)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sim", "serial"], default="sim")
    ap.add_argument("--model", default="model/tree.joblib")
    ap.add_argument("--port", default=None)
    ap.add_argument("--no-dashboard", action="store_true")
    args = ap.parse_args()
    model = _load_model(args.model)
    if args.source == "sim":
        from src.sources import SimulatedSource
        src = SimulatedSource([("off",0.5),("startup",0.3),("running",1.5),
                               ("stall",0.8),("running",1.0),("off",0.3)],
                              fs=1000, seed=11, realtime=not args.no_dashboard)
    else:
        from src.sources import SerialSource
        src = SerialSource(args.port)
    if args.no_dashboard:
        run_detection(src, model, on_update=lambda t,x,p,s: print(f"{t:6.3f} {p:>7} -> {s}"))
    else:
        run_dashboard(src, model)
